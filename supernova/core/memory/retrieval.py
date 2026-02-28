"""supernova/core/memory/retrieval.py

WeightedMemoryRetriever, MemoryConsolidator, and MemoryPrefetcher —
the three-layer memory pipeline for SuperNova.

Retrieval::

    composite = α·relevance + β·recency + γ·type_weight

Where α + β + γ == 1.0. Recency is an exponential decay keyed on
half-life. Type weight is a per-store priority set at registration time.

Consolidation periodically merges near-duplicate episodic memories into
a single canonical entry, reducing context-window noise over long sessions.

Prefetching uses background asyncio Tasks to warm a short-lived cache
before the agent's reasoning phase begins, hiding retrieval latency.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

import structlog

logger = structlog.get_logger(__name__)


# ── Domain types ─────────────────────────────────────────────────────────────


@dataclass
class MemoryItem:
    """A single retrieved memory artifact with relevance metadata."""

    id: str
    content: str
    memory_type: str  # 'episodic' | 'semantic' | 'procedural' | 'working'
    relevance_score: float  # Raw similarity score from the backing store (0–1)
    recency_score: float  # Time-decay weight (1.0 = now, 0.0 = ancient)
    composite_score: float  # Final weighted rank used for selection
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieved_at: float = field(default_factory=time.time)


class MemoryStore(Protocol):
    """Protocol that all memory store implementations must satisfy."""

    async def search(
        self, query: str, top_k: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """Return the *top_k* items most relevant to *query*."""
        ...

    async def upsert(self, item: MemoryItem) -> None:
        """Insert or update a memory item."""
        ...

    async def delete(self, item_id: str) -> None:
        """Remove a memory item by ID."""
        ...


# ── Weighted retriever ─────────────────────────────────────────────────────────


class WeightedMemoryRetriever:
    """Retrieve memories from multiple stores and merge with composite scoring.

    Scoring formula::

        composite = α·relevance + β·recency + γ·type_weight

    where α + β + γ == 1.0.  Recency uses exponential decay keyed on
    ``recency_half_life_hours``.  Near-duplicates are collapsed via a
    content fingerprint before the final top-k cut.

    Args:
        stores: ``{store_name: (MemoryStore, type_weight)}`` mapping.
            ``type_weight`` is the per-store priority (0.0 – 1.0); values
            are used as-is in the gamma term of the composite formula.
        alpha: Relevance weight.  Default 0.6.
        beta: Recency weight.  Default 0.3.
        gamma: Type-priority weight.  Default 0.1.  Must satisfy
            ``alpha + beta + gamma == 1.0``.
        recency_half_life_hours: Half-life for the exponential decay.
            Default 24 h (recency halves every day).
        dedup_threshold: Items whose content fingerprints collide are
            deduplicated; the highest-scoring copy is kept.
    """

    def __init__(
        self,
        stores: Dict[str, Tuple[MemoryStore, float]],
        alpha: float = 0.6,
        beta: float = 0.3,
        gamma: float = 0.1,
        recency_half_life_hours: float = 24.0,
        dedup_threshold: float = 0.95,
    ) -> None:
        if abs(alpha + beta + gamma - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {alpha + beta + gamma}")
        self._stores = stores
        self._alpha = alpha
        self._beta = beta
        self._gamma = gamma
        self._half_life_seconds = recency_half_life_hours * 3600.0
        self._dedup_threshold = dedup_threshold

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        store_names: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """Retrieve and rank memories from all (or named) stores.

        Args:
            query: Natural-language query for similarity search.
            top_k: Maximum items to return after merging and ranking.
            store_names: If provided, only query these stores by name.
            filters: Store-specific filter dict passed through to each store.

        Returns:
            Ranked list of :class:`MemoryItem`, length ≤ ``top_k``.
        """
        targets = {
            k: v
            for k, v in self._stores.items()
            if store_names is None or k in store_names
        }
        tasks = [
            self._fetch(name, store, weight, query, top_k, filters)
            for name, (store, weight) in targets.items()
        ]
        nested: List[List[MemoryItem]] = await asyncio.gather(*tasks)
        all_items = [item for sublist in nested for item in sublist]

        self._score(all_items)
        unique = self._deduplicate(all_items)
        unique.sort(key=lambda x: x.composite_score, reverse=True)
        return unique[:top_k]

    async def _fetch(
        self,
        name: str,
        store: MemoryStore,
        type_weight: float,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[MemoryItem]:
        """Fetch from one store and annotate items with recency + type_weight."""
        try:
            items = await store.search(query, top_k=top_k * 2, filters=filters)
        except Exception as exc:
            logger.warning("Memory store fetch failed", store=name, error=str(exc))
            return []

        now = time.time()
        for item in items:
            age = now - item.metadata.get("created_at", now)
            item.recency_score = 2.0 ** (-age / self._half_life_seconds)
            item.metadata["_store"] = name
            item.metadata["_type_weight"] = type_weight
        return items

    def _score(self, items: List[MemoryItem]) -> None:
        """Apply composite scoring in-place."""
        for item in items:
            tw = item.metadata.get("_type_weight", 0.5)
            item.composite_score = (
                self._alpha * item.relevance_score
                + self._beta * item.recency_score
                + self._gamma * tw
            )

    def _deduplicate(self, items: List[MemoryItem]) -> List[MemoryItem]:
        """Collapse near-duplicates, keeping the highest-scoring copy."""
        best: Dict[str, MemoryItem] = {}
        for item in items:
            fp = _fingerprint(item.content)
            if fp not in best or item.composite_score > best[fp].composite_score:
                best[fp] = item
        return list(best.values())


# ── Consolidator ────────────────────────────────────────────────────────────────


@dataclass
class ConsolidationRecord:
    """Metadata for a single consolidation operation."""

    source_ids: List[str]
    result_id: str
    store_name: str
    summary: str = ""
    consolidated_at: float = field(default_factory=time.time)


class MemoryConsolidator:
    """Merge redundant or near-duplicate memories to reduce context noise.

    Consolidation strategy:

    1. Fetch candidate memories within the rolling time window.
    2. Cluster by content-fingerprint prefix (first 8 hex chars of MD5).
    3. For each cluster ≥ ``min_cluster_size``: call ``summarizer`` (if any)
       to synthesise a canonical entry, upsert it, then delete the sources.

    Args:
        store: Target :class:`MemoryStore` to consolidate.
        store_name: Human-readable label used in log messages.
        window_hours: Rolling window for candidate selection.  Default 48 h.
        min_cluster_size: Minimum cluster size to trigger consolidation.
        summarizer: Optional ``async (combined_text: str) -> str`` callable.
            When omitted, the first 1 000 chars of combined text are used.
    """

    def __init__(
        self,
        store: MemoryStore,
        store_name: str,
        window_hours: float = 48.0,
        min_cluster_size: int = 3,
        summarizer: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self._store = store
        self._store_name = store_name
        self._window_seconds = window_hours * 3600.0
        self._min_cluster_size = min_cluster_size
        self._summarizer = summarizer
        self._records: List[ConsolidationRecord] = []

    async def consolidate(
        self, trigger_query: str = "recent events"
    ) -> List[ConsolidationRecord]:
        """Run one consolidation pass.

        Args:
            trigger_query: Query used to fetch the candidate item pool.

        Returns:
            :class:`ConsolidationRecord` list, one per merged cluster.
        """
        candidates = await self._store.search(trigger_query, top_k=200)
        now = time.time()
        cutoff = now - self._window_seconds
        recent = [
            c
            for c in candidates
            if c.metadata.get("created_at", now) >= cutoff
        ]
        clusters = _cluster_by_fingerprint(recent)
        new_records: List[ConsolidationRecord] = []
        for cluster in clusters.values():
            if len(cluster) < self._min_cluster_size:
                continue
            record = await self._merge_cluster(cluster)
            if record:
                new_records.append(record)

        self._records.extend(new_records)
        logger.info(
            "Memory consolidation complete",
            store=self._store_name,
            merged_clusters=len(new_records),
            candidates_examined=len(recent),
        )
        return new_records

    async def _merge_cluster(self, cluster: List[MemoryItem]) -> Optional[ConsolidationRecord]:
        combined = "\n\n".join(item.content for item in cluster)
        source_ids = [item.id for item in cluster]

        if self._summarizer is not None:
            try:
                summary: str = await self._summarizer(combined)
            except Exception as exc:
                logger.warning("Summarizer failed", error=str(exc))
                summary = combined[:1_000]
        else:
            summary = combined[:1_000]

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
        """Session-scoped consolidation records (read-only)."""
        return list(self._records)


# ── Prefetcher ──────────────────────────────────────────────────────────────────


class MemoryPrefetcher:
    """Proactively warm a short-lived cache before the agent reasoning phase.

    Fires background :func:`asyncio.create_task` fetches for anticipated
    queries.  When the agent later calls :meth:`get`, results are returned
    from cache with no added latency.

    Args:
        retriever: :class:`WeightedMemoryRetriever` used for background fetches.
        cache_ttl_seconds: TTL for cached results.  Default 30 s.
        max_cache_size: LRU cap on number of cached queries.  Default 10.
        top_k: Items to prefetch per query.  Default 8.
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
        """Start a background fetch for *anticipated_query*.

        No-ops if a fresh cache entry already exists or a fetch is in-flight.
        """
        key = _cache_key(anticipated_query)
        if key in self._cache:
            ts, _ = self._cache[key]
            if time.time() - ts < self._ttl:
                return
        if key not in self._pending:
            self._pending[key] = asyncio.create_task(
                self._fetch_and_cache(key, anticipated_query)
            )

    async def get(
        self, query: str, fallback: bool = True
    ) -> List[MemoryItem]:
        """Return cached results, or fetch synchronously if needed.

        Args:
            query: The actual query being executed by the agent.
            fallback: Perform a synchronous fetch on cache miss when True.

        Returns:
            List of :class:`MemoryItem` for *query*.
        """
        key = _cache_key(query)

        # Wait up to 2 s for an in-flight prefetch to complete
        if key in self._pending:
            try:
                await asyncio.wait_for(asyncio.shield(self._pending[key]), timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            self._pending.pop(key, None)

        if key in self._cache:
            ts, items = self._cache[key]
            if time.time() - ts < self._ttl:
                logger.debug("Prefetch cache hit", query=query[:60])
                return items

        if fallback:
            items = await self._retriever.retrieve(query, top_k=self._top_k)
            self._cache_store(key, items)
            return items

        return []

    async def _fetch_and_cache(self, key: str, query: str) -> None:
        try:
            items = await self._retriever.retrieve(query, top_k=self._top_k)
            self._cache_store(key, items)
        except Exception as exc:
            logger.warning("Prefetch task failed", query=query[:60], error=str(exc))
        finally:
            self._pending.pop(key, None)

    def _cache_store(self, key: str, items: List[MemoryItem]) -> None:
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), items)

    def invalidate(self, pattern: Optional[str] = None) -> None:
        """Evict all cache entries, or only those whose key contains *pattern*."""
        if pattern is None:
            self._cache.clear()
        else:
            for k in [k for k in self._cache if pattern in k]:
                del self._cache[k]


# ── Module-level helpers ─────────────────────────────────────────────────────────


def _fingerprint(content: str) -> str:
    """MD5 of the first 200 normalised characters — fast dedup key."""
    normalised = " ".join(content[:200].lower().split())
    return hashlib.md5(normalised.encode()).hexdigest()


def _cache_key(query: str) -> str:
    """Stable cache key from a normalised query string."""
    return hashlib.md5(" ".join(query.lower().split()).encode()).hexdigest()


def _cluster_by_fingerprint(
    items: List[MemoryItem],
) -> Dict[str, List[MemoryItem]]:
    """Bucket items by the first 8 chars of their content fingerprint."""
    clusters: Dict[str, List[MemoryItem]] = {}
    for item in items:
        fp = _fingerprint(item.content)[:8]
        clusters.setdefault(fp, []).append(item)
    return clusters
