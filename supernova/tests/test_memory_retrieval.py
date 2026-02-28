"""Tests for WeightedMemoryRetriever, MemoryConsolidator, MemoryPrefetcher,
and prune_stale_memories in supernova/core/memory/retrieval.py.

structlog is stubbed before import; all async store calls use AsyncMock.

ToT paths covered:
  WeightedMemoryRetriever
    R1  Weights not summing to 1.0 raise ValueError
    R2  _apply_weights computes composite = alpha*rel + beta*rec + gamma*tw + delta*freq
    R3  _deduplicate keeps highest-scoring copy of identical-content items
    R4  retrieve fans out to all registered stores and returns sorted items
    R5  One failing store does not crash retrieve (graceful degradation)
    R6  get_prefetch_stats returns correct hit-rate dict

  MemoryConsolidator
    C1  _cluster groups items by content-fingerprint prefix
    C2  consolidate only merges clusters >= min_cluster_size
    C3  _merge upserts summary + deletes all source IDs
    C4  summariser exception falls back to truncated content

  MemoryPrefetcher
    P1  get() returns cached items on cache hit
    P2  get() falls back to synchronous retrieve on cache miss
    P3  invalidate(None) clears entire cache
    P4  invalidate(pattern) evicts only matching entries

  prune_stale_memories
    M1  Low-importance stale items are archived (metadata status set)
    M2  High-importance or recent items are not archived
    M3  Store exception returns 0 without raising
"""
from __future__ import annotations

import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

# Stub structlog before retrieval.py is imported
if "structlog" not in sys.modules:
    sys.modules["structlog"] = MagicMock()

from supernova.core.memory.retrieval import (  # noqa: E402
    MemoryConsolidator,
    MemoryItem,
    MemoryPrefetcher,
    WeightedMemoryRetriever,
    prune_stale_memories,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item(
    id: str = "m1",
    content: str = "test content",
    relevance: float = 0.8,
    recency: float = 0.9,
    composite: float = 0.0,
    importance: float = 0.5,
    age_seconds: float = 0.0,
) -> MemoryItem:
    return MemoryItem(
        id=id,
        content=content,
        memory_type="episodic",
        relevance_score=relevance,
        recency_score=recency,
        composite_score=composite,
        metadata={
            "created_at": time.time() - age_seconds,
            "importance": importance,
            "last_accessed": time.time() - age_seconds,
        },
    )


def _retriever(**kwargs) -> WeightedMemoryRetriever:
    """Build a retriever with a single mock store."""
    store = AsyncMock()
    store.search = AsyncMock(return_value=[])
    return WeightedMemoryRetriever(
        stores={"default": (store, 0.5)},
        **kwargs,
    )


# ===========================================================================
# WeightedMemoryRetriever
# ===========================================================================

# R1 ─ weight validation
def test_weights_not_summing_to_one_raises() -> None:
    with pytest.raises(ValueError, match="Weights must sum to 1.0"):
        WeightedMemoryRetriever(
            stores={},
            alpha=0.5, beta=0.5, gamma=0.5, delta=0.5,
        )


# R2 ─ composite formula
def test_apply_weights_composite_formula() -> None:
    retriever = WeightedMemoryRetriever(
        stores={},
        alpha=0.5, beta=0.25, gamma=0.15, delta=0.1,
    )
    item = _item(relevance=1.0, recency=0.8)
    item.metadata["_type_weight"] = 0.6
    retriever._apply_weights([item])
    # delta * access_freq = 0.1 * 0 / 1 = 0.0 (no prior access)
    expected = 0.5 * 1.0 + 0.25 * 0.8 + 0.15 * 0.6 + 0.1 * 0.0
    assert item.composite_score == pytest.approx(expected, rel=1e-5)


# R3 ─ deduplication
def test_deduplicate_keeps_highest_scoring_copy() -> None:
    retriever = _retriever()
    # Two items with identical content but different scores
    high = _item(id="h", content="same content", composite=0.9)
    low  = _item(id="l", content="same content", composite=0.2)
    result = retriever._deduplicate([low, high])
    assert len(result) == 1
    assert result[0].id == "h"


# R4 ─ retrieve fans out and returns sorted results
@pytest.mark.asyncio
async def test_retrieve_returns_sorted_items() -> None:
    store_a = AsyncMock()
    store_b = AsyncMock()

    item_a = _item(id="a", relevance=0.9, recency=0.8)
    item_b = _item(id="b", relevance=0.4, recency=0.5)

    store_a.search = AsyncMock(return_value=[item_a])
    store_b.search = AsyncMock(return_value=[item_b])

    retriever = WeightedMemoryRetriever(
        stores={"s_a": (store_a, 0.5), "s_b": (store_b, 0.5)},
        alpha=0.5, beta=0.25, gamma=0.15, delta=0.1,
    )
    results = await retriever.retrieve("test query", top_k=10)

    # Both stores were queried
    store_a.search.assert_called_once()
    store_b.search.assert_called_once()
    # Results are sorted descending by composite_score
    assert results[0].composite_score >= results[-1].composite_score


# R5 ─ one failing store does not crash retrieve
@pytest.mark.asyncio
async def test_retrieve_graceful_store_failure() -> None:
    good_store = AsyncMock()
    bad_store  = AsyncMock()

    good_store.search = AsyncMock(return_value=[_item(id="ok")])
    bad_store.search  = AsyncMock(side_effect=Exception("DB down"))

    retriever = WeightedMemoryRetriever(
        stores={"good": (good_store, 0.5), "bad": (bad_store, 0.5)},
        alpha=0.5, beta=0.25, gamma=0.15, delta=0.1,
    )
    results = await retriever.retrieve("query", top_k=5)
    assert len(results) == 1
    assert results[0].id == "ok"


# R6 ─ prefetch stats
def test_get_prefetch_stats_initial_state() -> None:
    r = _retriever()
    stats = r.get_prefetch_stats()
    assert stats["total_retrievals"] == 0
    assert stats["cache_hits"] == 0
    assert stats["hit_rate"] == 0.0


# ===========================================================================
# MemoryConsolidator
# ===========================================================================

# C1 ─ _cluster groups by content fingerprint prefix
def test_cluster_groups_identical_content() -> None:
    store = AsyncMock()
    consolidator = MemoryConsolidator(store=store, store_name="test", min_cluster_size=2)
    items = [
        _item(id="x1", content="same content here"),
        _item(id="x2", content="same content here"),
        _item(id="y1", content="completely different text"),
    ]
    clusters = consolidator._cluster(items)
    # At least two distinct clusters
    assert len(clusters) >= 2
    # The two identical items share a cluster
    matching = [c for c in clusters.values() if len(c) == 2]
    assert len(matching) == 1


# C2 ─ consolidate skips clusters below min_cluster_size
@pytest.mark.asyncio
async def test_consolidate_skips_small_clusters() -> None:
    store = AsyncMock()
    store.search = AsyncMock(side_effect=[
        [_item(id="a", content="lone item")],  # candidates
        [],                                     # total count
    ])
    consolidator = MemoryConsolidator(store=store, store_name="t", min_cluster_size=3)
    records = await consolidator.consolidate()
    assert records == []
    store.upsert.assert_not_called()


# C3 ─ _merge upserts consolidated item and deletes sources
@pytest.mark.asyncio
async def test_consolidate_merges_and_deletes_sources() -> None:
    store = AsyncMock()
    items = [
        _item(id=f"src{i}", content="repeated fact to consolidate")
        for i in range(3)
    ]
    store.search = AsyncMock(side_effect=[items, []])
    store.upsert = AsyncMock()
    store.delete = AsyncMock()

    consolidator = MemoryConsolidator(store=store, store_name="t", min_cluster_size=3)
    records = await consolidator.consolidate()

    assert len(records) == 1
    assert set(records[0].source_ids) == {"src0", "src1", "src2"}
    store.upsert.assert_called_once()
    assert store.delete.call_count == 3


# C4 ─ summariser exception falls back to truncated content
@pytest.mark.asyncio
async def test_merge_summariser_exception_uses_fallback() -> None:
    store = AsyncMock()
    store.upsert = AsyncMock()
    store.delete = AsyncMock()

    async def bad_summariser(text: str) -> str:
        raise RuntimeError("summariser unavailable")

    consolidator = MemoryConsolidator(
        store=store, store_name="t",
        min_cluster_size=2,
        summariser=bad_summariser,
    )
    items = [_item(id=f"s{i}", content="content") for i in range(2)]
    record = await consolidator._merge(items)

    assert record is not None
    assert record.summary != ""
    store.upsert.assert_called_once()


# ===========================================================================
# MemoryPrefetcher
# ===========================================================================

# P1 ─ cache hit returns stored items without calling retriever
@pytest.mark.asyncio
async def test_prefetcher_cache_hit() -> None:
    r = _retriever()
    prefetcher = MemoryPrefetcher(retriever=r, cache_ttl_seconds=60)

    cached_items = [_item(id="cached")]
    prefetcher._put("abc123", cached_items)
    # Inject into cache with matching normalised key
    import hashlib
    key = hashlib.md5("test query".encode()).hexdigest()
    prefetcher._cache[key] = (time.time(), cached_items)

    results = await prefetcher.get("test query", fallback=True)
    assert results == cached_items


# P2 ─ cache miss falls back to synchronous retrieve
@pytest.mark.asyncio
async def test_prefetcher_cache_miss_fallback() -> None:
    store = AsyncMock()
    store.search = AsyncMock(return_value=[_item(id="fresh")])
    retriever = WeightedMemoryRetriever(
        stores={"s": (store, 0.5)},
        alpha=0.5, beta=0.25, gamma=0.15, delta=0.1,
    )
    prefetcher = MemoryPrefetcher(retriever=retriever, cache_ttl_seconds=30, top_k=5)
    results = await prefetcher.get("new query", fallback=True)
    assert len(results) >= 0   # fallback called; no crash
    store.search.assert_called()


# P3 ─ invalidate(None) clears all cache entries
def test_prefetcher_invalidate_all() -> None:
    r = _retriever()
    prefetcher = MemoryPrefetcher(retriever=r)
    prefetcher._cache["key1"] = (time.time(), [])
    prefetcher._cache["key2"] = (time.time(), [])
    prefetcher.invalidate(None)
    assert len(prefetcher._cache) == 0


# P4 ─ invalidate(pattern) evicts only matching entries
def test_prefetcher_invalidate_pattern() -> None:
    r = _retriever()
    prefetcher = MemoryPrefetcher(retriever=r)
    prefetcher._cache["aboutpython"] = (time.time(), [])
    prefetcher._cache["aboutrust"] = (time.time(), [])
    prefetcher._cache["randomkey"] = (time.time(), [])
    prefetcher.invalidate("about")
    assert "aboutpython" not in prefetcher._cache
    assert "aboutrust" not in prefetcher._cache
    assert "randomkey" in prefetcher._cache


# ===========================================================================
# prune_stale_memories
# ===========================================================================

# M1 ─ stale low-importance items are archived
@pytest.mark.asyncio
async def test_prune_archives_stale_low_importance_items() -> None:
    stale_old = _item(
        id="stale",
        importance=0.05,
        age_seconds=100 * 24 * 3600,  # 100 days old
    )
    store = AsyncMock()
    store.search = AsyncMock(return_value=[stale_old])
    store.upsert = AsyncMock()

    count = await prune_stale_memories(store, stale_days=90)

    assert count == 1
    store.upsert.assert_called_once()
    upserted = store.upsert.call_args[0][0]
    assert upserted.metadata["status"] == "archived"


# M2 ─ high-importance or recent items are NOT archived
@pytest.mark.asyncio
async def test_prune_does_not_archive_important_or_recent_items() -> None:
    important  = _item(id="imp",    importance=0.8, age_seconds=200 * 24 * 3600)
    recent     = _item(id="recent", importance=0.05, age_seconds=10)  # 10 seconds old
    store = AsyncMock()
    store.search = AsyncMock(return_value=[important, recent])
    store.upsert = AsyncMock()

    count = await prune_stale_memories(store, stale_days=90)

    assert count == 0
    store.upsert.assert_not_called()


# M3 ─ store exception returns 0 without raising
@pytest.mark.asyncio
async def test_prune_store_exception_returns_zero() -> None:
    store = AsyncMock()
    store.search = AsyncMock(side_effect=Exception("store down"))

    count = await prune_stale_memories(store, stale_days=90)
    assert count == 0
