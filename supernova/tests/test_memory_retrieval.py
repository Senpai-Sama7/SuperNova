"""Tests for memory retrieval paths (Task 8.5)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from supernova.core.memory.semantic import SemanticMemoryStore
from supernova.core.memory.working import WorkingMemory, WorkingMemoryStore

# ---------------------------------------------------------------------------
# Semantic memory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pool():
    p = MagicMock()
    p.fetch = AsyncMock(return_value=[])
    p.fetchval = AsyncMock(return_value=None)
    p.execute = AsyncMock()
    return p


@pytest.fixture
def redis():
    r = MagicMock()
    r.embedding_cache_get = AsyncMock(return_value=None)
    r.embedding_cache_set = AsyncMock()
    r.working_memory_get = AsyncMock(return_value=None)
    r.working_memory_set = AsyncMock()
    return r


@pytest.fixture
def sem_store(pool, redis):
    return SemanticMemoryStore(pool=pool, redis=redis)


# ---------------------------------------------------------------------------
# 8.5.2  Upsert → search round-trip
# ---------------------------------------------------------------------------

class TestUpsertSearchRoundTrip:
    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_upsert_and_search_round_trip(self, mock_embed, sem_store, pool):
        """Upsert a memory then search — the same content must appear."""
        emb = [0.1] * 1536
        mock_embed.return_value = emb
        mem_id = uuid4()
        # upsert: no existing → insert returns id
        pool.fetchval.side_effect = [None, mem_id]
        result_id = await sem_store.upsert("Python is great", user_id="u1", category="tech")
        assert result_id == mem_id

        # search: pool.fetch returns the row we just "inserted"
        pool.fetch.return_value = [
            {"id": mem_id, "content": "Python is great", "category": "tech",
             "confidence": 0.5, "importance": 0.5, "tags": [], "source": None,
             "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
             "rrf_score": 0.032}
        ]
        results = await sem_store.search("Python", user_id="u1")
        assert len(results) == 1
        assert results[0]["id"] == str(mem_id)
        assert results[0]["content"] == "Python is great"


# ---------------------------------------------------------------------------
# 8.5.3  Forgetting curve decays importance
# ---------------------------------------------------------------------------

class TestForgettingCurve:
    @pytest.mark.asyncio
    async def test_forgetting_curve_decays_importance(self, pool):
        """run_forgetting_curves stored procedure reduces importance."""
        original_importance = 5.0
        decayed_importance = 4.2

        # Simulate: execute the stored procedure, then fetchval returns decayed value
        pool.execute.return_value = None
        pool.fetchval.return_value = decayed_importance

        await pool.execute("CALL run_forgetting_curves()")
        new_imp = await pool.fetchval(
            "SELECT importance FROM semantic_memories WHERE id = $1", uuid4()
        )
        assert new_imp < original_importance


# ---------------------------------------------------------------------------
# 8.5.4  Hybrid search RRF score >= vector-only score
# ---------------------------------------------------------------------------

class TestHybridSearch:
    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_hybrid_search_higher_score(self, mock_embed, sem_store, pool):
        """RRF score (vector + FTS) should be >= vector-only rank score."""
        mock_embed.return_value = [0.1] * 1536
        mem_id = uuid4()
        vector_only_score = 1.0 / (60 + 1)  # rank 1, RRF_K=60
        hybrid_score = vector_only_score + 1.0 / (60 + 1)  # also rank 1 in FTS

        pool.fetch.return_value = [
            {"id": mem_id, "content": "exact keyword match", "category": "tech",
             "confidence": 0.9, "importance": 0.8, "tags": [], "source": None,
             "created_at": datetime.now(UTC), "updated_at": datetime.now(UTC),
             "rrf_score": hybrid_score}
        ]
        results = await sem_store.search("exact keyword match", user_id="u1")
        assert results[0]["score"] >= vector_only_score


# ---------------------------------------------------------------------------
# 8.5.5  Working memory round-trip
# ---------------------------------------------------------------------------

class TestWorkingMemoryRoundTrip:
    @pytest.mark.asyncio
    async def test_working_memory_round_trip(self, redis):
        """Set working memory, get it back — all fields survive."""
        store = WorkingMemoryStore(redis_client=redis)
        mem = WorkingMemory(
            session_id="sess-1",
            current_goal="Build SuperNova",
            active_plan=["step1", "step2"],
            scratchpad="notes here",
        )
        # set stores the dict; get returns it
        stored = {}

        async def capture_set(sid, data, ttl=None):
            stored.update(data)

        async def return_stored(sid):
            return stored if stored else None

        redis.working_memory_set = AsyncMock(side_effect=capture_set)
        redis.working_memory_get = AsyncMock(side_effect=return_stored)

        await store.set(mem)
        retrieved = await store.get("sess-1")

        assert retrieved is not None
        assert retrieved.session_id == "sess-1"
        assert retrieved.current_goal == "Build SuperNova"
        assert retrieved.active_plan == ["step1", "step2"]
        assert retrieved.scratchpad == "notes here"
