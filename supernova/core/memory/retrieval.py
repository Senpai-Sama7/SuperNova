"""supernova/core/memory/retrieval.py

Provides three complementary memory pipeline components:

* :class:`WeightedMemoryRetriever` — fan-out retrieval across multiple stores
  with composite scoring: ``α·relevance + β·recency + γ·type_weight``.

* :class:`MemoryConsolidator` — periodic merging of redundant episodic/semantic
  entries via cluster-then-summarise to reduce noise and store bloat.

* :class:`MemoryPrefetcher` — background async prefetch with TTL cache so
  the reasoning loop never waits on cold memory lookups.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Timing metrics storage
_retrieval_times: List[float] = []
_MAX_METRICS = 1000  # Keep last 1000 measurements


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class MemoryItem:
    """A single retrieved memory artefact with scoring metadata.

    Attributes:
        id: Unique identifier in the backing store.
        content: Raw text content of the memory.
        memory_type: One of ``episodic``, ``semantic``, ``procedural``, ``working``.
        relevance_score: Raw cosine / BM25 similarity from the store (0–1).
        recency_score: Time-decay weight (1.0 = just created, 0.0 = ancient).
        composite_score: Final weighted rank used for selection.
        salience_score: Emotional salience (-1.0 to 1.0).
        metadata: Store-specific payload (timestamps, source, tags, …).
        retrieved_at: Unix timestamp of retrieval.
    """

    id: str
    content: str
    memory_type: str
    relevance_score: float
    recency_score: float
    composite_score: float
    salience_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: float = field(default_factory=time.time)


class MemoryStore(Protocol):
    """Structural protocol that all memory store adapters must satisfy."""

    async def search(
        self, query: str, top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]: ...

    async def upsert(self, item: MemoryItem) -> None: ...

    async def delete(self, item_id: str) -> None: ...


# ---------------------------------------------------------------------------
# WeightedMemoryRetriever
# ---------------------------------------------------------------------------


class WeightedMemoryRetriever:
    """Fan-out retrieval from multiple memory stores with composite ranking.

    Composite score formula::

        composite = α × relevance_score
                  + β × recency_score
                  + γ × type_weight
                  + δ × access_frequency

    where ``α + β + γ + δ == 1.0`` and ``type_weight`` is the per-store priority
    declared when the store is registered.

    Args:
        stores: ``{name: (MemoryStore, type_weight)}`` mapping.
        alpha: Relevance weight. Default 0.5.
        beta: Recency weight. Default 0.25.
        gamma: Type-priority weight. Default 0.15.
        delta: Access frequency weight. Default 0.1.
        recency_half_life_hours: Hours until recency score halves.
        dedup_threshold: Items with identical content fingerprints (first 200
            chars, lowercased) are deduplicated; highest-scoring copy is kept.
    """

    def __init__(
        self,
        stores: Dict[str, Tuple[MemoryStore, float]],
        alpha: float = 0.5,
        beta: float = 0.25,
        gamma: float = 0.15,
        delta: float = 0.1,
        recency_half_life_hours: float = 24.0,
        dedup_threshold: float = 0.95,
    ) -> None:
        if abs(alpha + beta + gamma + delta - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {alpha + beta + gamma + delta}")
        self._stores = stores
        self._alpha = alpha
        self._beta = beta
        self._gamma = gamma
        self._delta = delta
        self._half_life_s = recency_half_life_hours * 3600.0
        self._dedup_threshold = dedup_threshold
        self._access_counts: Dict[str, int] = {}
        self._total_retrievals = 0
        self._cache_hits = 0

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        store_names: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """Retrieve and rank memories from all (or specified) stores.

        Args:
            query: Natural language query for similarity search.
            top_k: Maximum items to return after merging and ranking.
            store_names: If provided, restrict to these stores.
            filters: Passed through to each store’s ``search`` method.

        Returns:
            Ranked :class:`MemoryItem` list, length ≤ *top_k*.
        """
        start_time = time.monotonic()
        self._total_retrievals += 1
        
        target = {
            k: v for k, v in self._stores.items()
            if store_names is None or k in store_names
        }
        results = await asyncio.gather(
            *[
                self._fetch(name, store, weight, query, top_k, filters)
                for name, (store, weight) in target.items()
            ]
        )
        merged: List[MemoryItem] = [item for batch in results for item in batch]
        
        # Track access frequency for retrieved items
        for item in merged:
            self._access_counts[item.id] = self._access_counts.get(item.id, 0) + 1
        
        merged = self._apply_weights(merged)
        merged = self._deduplicate(merged)
        merged.sort(key=lambda x: x.composite_score, reverse=True)
        
        # Record timing metrics
        elapsed = time.monotonic() - start_time
        _retrieval_times.append(elapsed)
        if len(_retrieval_times) > _MAX_METRICS:
            _retrieval_times.pop(0)
        
        # Log p50/p95 every 10 retrievals
        if len(_retrieval_times) % 10 == 0:
            self._log_latency_metrics()
        
        # Log prefetch stats every 50 retrievals
        if self._total_retrievals % 50 == 0:
            self._log_prefetch_stats()
        
        logger.debug("memory_retrieval", elapsed_ms=elapsed*1000, items=len(merged[:top_k]))
        return merged[:top_k]

    async def _fetch(
        self,
        name: str,
        store: MemoryStore,
        weight: float,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[MemoryItem]:
        try:
            items = await store.search(query, top_k=top_k * 2, filters=filters)
            now = time.time()
            for item in items:
                age = now - item.metadata.get("created_at", now)
                item.recency_score = 2.0 ** (-age / self._half_life_s)
                item.metadata["_store"] = name
                item.metadata["_type_weight"] = weight
            return items
        except Exception as exc:
            logger.warning("store_fetch_failed", store=name, error=str(exc))
            return []

    def _apply_weights(self, items: List[MemoryItem]) -> List[MemoryItem]:
        max_access = max(self._access_counts.values()) if self._access_counts else 1
        for item in items:
            tw = item.metadata.get("_type_weight", 0.5)
            access_freq = self._access_counts.get(item.id, 0) / max_access
            item.composite_score = (
                self._alpha * item.relevance_score
                + self._beta * item.recency_score
                + self._gamma * tw
                + self._delta * access_freq
            )
        return items

    def get_access_frequency(self, memory_id: str) -> int:
        """Get access count for a specific memory."""
        return self._access_counts.get(memory_id, 0)
    
    def get_prefetch_stats(self) -> Dict[str, float]:
        """Get prefetch hit rate statistics."""
        hit_rate = self._cache_hits / self._total_retrievals if self._total_retrievals > 0 else 0.0
        return {
            "total_retrievals": self._total_retrievals,
            "cache_hits": self._cache_hits,
            "hit_rate": hit_rate
        }
    
    def _log_prefetch_stats(self) -> None:
        """Log prefetch statistics every 50 retrievals."""
        stats = self.get_prefetch_stats()
        logger.info("prefetch_stats", **stats)

    def _deduplicate(self, items: List[MemoryItem]) -> List[MemoryItem]:
        seen: Dict[str, float] = {}
        unique: List[MemoryItem] = []
        for item in sorted(items, key=lambda x: x.composite_score, reverse=True):
            fp = _fingerprint(item.content)
            if fp not in seen:
                seen[fp] = item.composite_score
                unique.append(item)
        return unique
    
    def _log_latency_metrics(self) -> None:
        """Log p50/p95 latency metrics."""
        if not _retrieval_times:
            return
        
        sorted_times = sorted(_retrieval_times)
        n = len(sorted_times)
        p50 = sorted_times[int(n * 0.5)] * 1000  # ms
        p95 = sorted_times[int(n * 0.95)] * 1000  # ms
        
        logger.info("retrieval_latency", p50_ms=p50, p95_ms=p95, samples=n)


# ---------------------------------------------------------------------------
# MemoryConsolidator
# ---------------------------------------------------------------------------


@dataclass
class ConsolidationRecord:
    """Metadata for a completed consolidation operation."""

    source_ids: List[str]
    result_id: str
    store_name: str
    consolidated_at: float = field(default_factory=time.time)
    summary: str = ""


class MemoryConsolidator:
    """Merge redundant memories to reduce store noise and retrieval latency.

    Consolidation procedure:

    1. Fetch recent candidates within the lookback window.
    2. Cluster by content-fingerprint prefix (first 8 hex chars of MD5).
    3. For each cluster ≥ *min_cluster_size*: synthesise a summary via the
       optional *summariser* callable, upsert as a new item, delete sources.

    Args:
        store: Target :class:`MemoryStore` to consolidate.
        store_name: Label for logging and record-keeping.
        window_hours: Lookback window for candidate selection.
        min_cluster_size: Minimum cluster size to trigger consolidation.
        summariser: Optional ``async (text: str) -> str`` callable.
    """

    def __init__(
        self,
        store: MemoryStore,
        store_name: str,
        window_hours: float = 48.0,
        min_cluster_size: int = 3,
        summariser: Any = None,
    ) -> None:
        self._store = store
        self._store_name = store_name
        self._window_s = window_hours * 3600.0
        self._min_cluster = min_cluster_size
        self._summariser = summariser
        self._history: List[ConsolidationRecord] = []

    async def consolidate(self, seed_query: str = "recent events") -> List[ConsolidationRecord]:
        """Run a full consolidation pass.

        Args:
            seed_query: Used to seed candidate retrieval.

        Returns:
            :class:`ConsolidationRecord` list for each merged cluster.
        """
        candidates = await self._store.search(seed_query, top_k=200)
        cutoff = time.time() - self._window_s
        recent = [c for c in candidates if c.metadata.get("created_at", time.time()) >= cutoff]

        clusters = self._cluster(recent)
        records: List[ConsolidationRecord] = []
        memories_merged = 0
        memories_generalized = 0
        
        for cluster in clusters.values():
            if len(cluster) >= self._min_cluster:
                rec = await self._merge(cluster)
                if rec:
                    records.append(rec)
                    memories_merged += len(cluster)
                    memories_generalized += 1

        # Get archived count from pruning if available
        memories_archived = 0
        try:
            from .retrieval import prune_stale_memories
            memories_archived = await prune_stale_memories(self._store)
        except Exception:
            pass
            
        # Get total memory count
        total_memory_count = len(await self._store.search("*", top_k=10000))

        self._history.extend(records)
        
        # Log consolidation metrics
        logger.info(
            "consolidation_metrics",
            store=self._store_name,
            memories_merged=memories_merged,
            memories_generalized=memories_generalized, 
            memories_archived=memories_archived,
            total_memory_count=total_memory_count,
            merged_clusters=len(records),
            candidates=len(recent),
        )
        return records

    def _cluster(self, items: List[MemoryItem]) -> Dict[str, List[MemoryItem]]:
        clusters: Dict[str, List[MemoryItem]] = {}
        for item in items:
            prefix = _fingerprint(item.content)[:8]
            clusters.setdefault(prefix, []).append(item)
        return clusters

    async def _merge(self, cluster: List[MemoryItem]) -> Optional[ConsolidationRecord]:
        combined = "\n\n".join(i.content for i in cluster)
        source_ids = [i.id for i in cluster]

        if self._summariser is not None:
            try:
                summary: str = await self._summariser(combined)
            except Exception as exc:
                logger.warning("summariser_failed", error=str(exc))
                summary = combined[:1000]
        else:
            summary = combined[:1000]

        result_id = "consolidated_" + hashlib.sha256(summary.encode()).hexdigest()[:12]
        merged = MemoryItem(
            id=result_id,
            content=summary,
            memory_type=cluster[0].memory_type,
            relevance_score=max(i.relevance_score for i in cluster),
            recency_score=max(i.recency_score for i in cluster),
            composite_score=0.0,
            metadata={
                "source_ids": source_ids,
                "consolidation_count": len(cluster),
                "created_at": time.time(),
            },
        )
        await self._store.upsert(merged)
        for sid in source_ids:
            await self._store.delete(sid)

        return ConsolidationRecord(
            source_ids=source_ids,
            result_id=result_id,
            store_name=self._store_name,
            summary=summary[:200],
        )

    @property
    def history(self) -> List[ConsolidationRecord]:
        """Read-only view of this session’s consolidation records."""
        return list(self._history)


# ---------------------------------------------------------------------------
# MemoryPrefetcher
# ---------------------------------------------------------------------------


class MemoryPrefetcher:
    """Proactively prefetch memories before the agent’s reasoning phase.

    Spawns background :mod:`asyncio` tasks that populate a TTL cache keyed
    by normalised query strings. Subsequent ``get()`` calls are satisfied
    from cache, eliminating retrieval latency on the hot path.

    Args:
        retriever: :class:`WeightedMemoryRetriever` used for background fetches.
        cache_ttl_seconds: Cache entry lifetime. Default 30 s.
        max_cache_size: LRU eviction cap. Default 10 queries.
        top_k: Items prefetched per query.
    """

    def __init__(
        self,
        retriever: WeightedMemoryRetriever,
        cache_ttl_seconds: float = 30.0,
        max_cache_size: int = 10,
        top_k: int = 8,
    ) -> None:
        self._retriever = retriever
        self._ttl = cache_ttl_seconds
        self._max_size = max_cache_size
        self._top_k = top_k
        self._cache: Dict[str, Tuple[float, List[MemoryItem]]] = {}
        self._pending: Dict[str, asyncio.Task] = {}

    async def prefetch(self, anticipated_query: str) -> None:
        """Initiate a non-blocking background prefetch.

        If a live cache entry exists the call is a no-op.

        Args:
            anticipated_query: Query expected to be needed shortly.
        """
        key = _norm_key(anticipated_query)
        if key in self._cache and (time.time() - self._cache[key][0]) < self._ttl:
            return
        if key not in self._pending:
            self._pending[key] = asyncio.create_task(self._background_fetch(key, anticipated_query))

    async def get(self, query: str, fallback: bool = True) -> List[MemoryItem]:
        """Return cached results, waiting briefly for in-flight prefetch.

        Args:
            query: The actual retrieval query.
            fallback: Fetch synchronously if no cache hit after waiting.

        Returns:
            List of :class:`MemoryItem`, possibly empty if no fallback.
        """
        key = _norm_key(query)

        # Await any in-flight prefetch (max 2 s)
        if key in self._pending:
            try:
                await asyncio.wait_for(asyncio.shield(self._pending[key]), timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            self._pending.pop(key, None)

        # Cache hit
        if key in self._cache:
            ts, items = self._cache[key]
            if (time.time() - ts) < self._ttl:
                logger.debug("prefetch_cache_hit", query=query[:60])
                self._retriever._cache_hits += 1
                return items

        # Cache miss — synchronous fallback
        if fallback:
            items = await self._retriever.retrieve(query, top_k=self._top_k)
            self._put(key, items)
            return items

        return []

    def invalidate(self, pattern: Optional[str] = None) -> None:
        """Evict all or pattern-matching entries from the cache."""
        if pattern is None:
            self._cache.clear()
        else:
            for k in [k for k in self._cache if pattern.lower() in k]:
                del self._cache[k]

    async def _background_fetch(self, key: str, query: str) -> None:
        try:
            items = await self._retriever.retrieve(query, top_k=self._top_k)
            self._put(key, items)
        except Exception as exc:
            logger.warning("prefetch_failed", query=query[:60], error=str(exc))
        finally:
            self._pending.pop(key, None)

    def _put(self, key: str, items: List[MemoryItem]) -> None:
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), items)


# ---------------------------------------------------------------------------
# Memory Pruning
# ---------------------------------------------------------------------------


async def prune_stale_memories(store: MemoryStore, stale_days: int = 90) -> int:
    """Archive memories with low importance and old access times.
    
    Args:
        store: Memory store to prune
        stale_days: Days since last access to consider stale
        
    Returns:
        Number of memories archived
    """
    cutoff_time = time.time() - (stale_days * 24 * 3600)
    archived_count = 0
    
    try:
        # Get candidates for archiving
        candidates = await store.search("*", top_k=1000)
        
        for item in candidates:
            importance = item.metadata.get("importance", 0.5)
            last_accessed = item.metadata.get("last_accessed", item.metadata.get("created_at", time.time()))
            
            if importance < 0.1 and last_accessed < cutoff_time:
                # Archive instead of delete
                item.metadata["status"] = "archived"
                item.metadata["archived_at"] = time.time()
                await store.upsert(item)
                archived_count += 1
                
        logger.info("memory_pruning_complete", archived=archived_count, cutoff_days=stale_days)
        return archived_count
        
    except Exception as exc:
        logger.error("memory_pruning_failed", error=str(exc))
        return 0


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _fingerprint(content: str) -> str:
    """Stable MD5 fingerprint of normalised content (first 200 chars)."""
    normalised = " ".join(content[:200].lower().split())
    return hashlib.md5(normalised.encode()).hexdigest()


def _norm_key(query: str) -> str:
    """Normalised cache key for a query string."""
    return hashlib.md5(" ".join(query.lower().split()).encode()).hexdigest()
