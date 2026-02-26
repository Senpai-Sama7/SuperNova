"""Tests for SemanticMemoryStore."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from supernova.core.memory.semantic import SemanticMemoryStore


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchval = AsyncMock(return_value=None)
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def mock_redis():
    redis = MagicMock()
    redis.embedding_cache_get = AsyncMock(return_value=None)
    redis.embedding_cache_set = AsyncMock()
    return redis


@pytest.fixture
def fake_embedding():
    return [0.1] * 1536


@pytest.fixture
def store(mock_pool, mock_redis):
    return SemanticMemoryStore(pool=mock_pool, redis=mock_redis)


class TestInit:
    """5.4.1: Class initialized with Postgres pool + embedder client."""

    def test_constructor(self, store, mock_pool, mock_redis):
        assert store._pool is mock_pool
        assert store._redis is mock_redis
        assert store._embedding_model == "text-embedding-3-small"


class TestEmbed:
    """5.4.2: embed() with Redis caching."""

    @pytest.mark.asyncio
    async def test_embed_returns_from_cache(self, store, mock_redis, fake_embedding):
        mock_redis.embedding_cache_get.return_value = fake_embedding
        result = await store.embed("test text")
        assert result == fake_embedding
        mock_redis.embedding_cache_get.assert_called_once_with("test text")

    @pytest.mark.asyncio
    @patch("supernova.core.memory.semantic.litellm")
    async def test_embed_calls_litellm_on_cache_miss(self, mock_litellm, store, mock_redis, fake_embedding):
        mock_redis.embedding_cache_get.return_value = None
        mock_response = MagicMock()
        mock_response.data = [{"embedding": fake_embedding}]
        mock_litellm.aembedding = AsyncMock(return_value=mock_response)

        result = await store.embed("test text")
        assert result == fake_embedding
        mock_litellm.aembedding.assert_called_once_with(model="text-embedding-3-small", input=["test text"])
        mock_redis.embedding_cache_set.assert_called_once_with("test text", fake_embedding, ttl=3600)

    @pytest.mark.asyncio
    @patch("supernova.core.memory.semantic.litellm")
    async def test_embed_works_without_redis(self, mock_litellm, mock_pool, fake_embedding):
        store = SemanticMemoryStore(pool=mock_pool, redis=None)
        mock_response = MagicMock()
        mock_response.data = [{"embedding": fake_embedding}]
        mock_litellm.aembedding = AsyncMock(return_value=mock_response)

        result = await store.embed("test")
        assert result == fake_embedding


class TestSearch:
    """5.4.3: search() using hybrid SQL with RRF."""

    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_search_returns_results(self, mock_embed, store, mock_pool, fake_embedding):
        mock_embed.return_value = fake_embedding
        test_id = uuid4()
        mock_pool.fetch.return_value = [
            {
                "id": test_id, "content": "Python is great", "category": "tech",
                "confidence": 0.9, "importance": 0.8, "tags": ["python"],
                "source": "chat", "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc), "rrf_score": 0.032,
            }
        ]

        results = await store.search("python", user_id="user1")
        assert len(results) == 1
        assert results[0]["content"] == "Python is great"
        assert results[0]["score"] == 0.032

    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_search_with_category_filter(self, mock_embed, store, mock_pool, fake_embedding):
        mock_embed.return_value = fake_embedding
        mock_pool.fetch.return_value = []

        await store.search("test", user_id="user1", category="tech")
        call_args = mock_pool.fetch.call_args
        assert "category" in call_args[0][0]  # SQL contains category filter
        assert "tech" in call_args[0]  # category value passed as param

    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_search_handles_error(self, mock_embed, store, mock_pool, fake_embedding):
        mock_embed.return_value = fake_embedding
        mock_pool.fetch.side_effect = RuntimeError("db down")
        result = await store.search("test", user_id="user1")
        assert result == []


class TestUpsert:
    """5.4.4: upsert() with content hash deduplication."""

    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_upsert_inserts_new(self, mock_embed, store, mock_pool, fake_embedding):
        mock_embed.return_value = fake_embedding
        new_id = uuid4()
        mock_pool.fetchval.side_effect = [None, new_id]  # no existing, then INSERT returns id

        result = await store.upsert("new fact", user_id="user1", category="general")
        assert result == new_id

    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_upsert_updates_existing(self, mock_embed, store, mock_pool, fake_embedding):
        mock_embed.return_value = fake_embedding
        existing_id = uuid4()
        mock_pool.fetchval.return_value = existing_id  # found existing

        result = await store.upsert("existing fact", user_id="user1")
        assert result == existing_id
        mock_pool.execute.assert_called_once()  # UPDATE was called

    @pytest.mark.asyncio
    @patch.object(SemanticMemoryStore, "embed", new_callable=AsyncMock)
    async def test_upsert_handles_error(self, mock_embed, store, mock_pool, fake_embedding):
        mock_embed.side_effect = RuntimeError("embed fail")
        result = await store.upsert("test", user_id="user1")
        assert result is None


class TestUpdateAccessTime:
    """5.4.5: update_access_time() updates last_accessed."""

    @pytest.mark.asyncio
    async def test_update_access_time(self, store, mock_pool):
        mid = uuid4()
        await store.update_access_time(mid)
        mock_pool.execute.assert_called_once()
        sql = mock_pool.execute.call_args[0][0]
        assert "last_accessed_at" in sql
        assert "access_count" in sql

    @pytest.mark.asyncio
    async def test_update_access_time_handles_error(self, store, mock_pool):
        mock_pool.execute.side_effect = RuntimeError("fail")
        await store.update_access_time(uuid4())  # Should not raise


class TestGetByCategory:
    """5.4.6: get_by_category() returns memories for user_id + category."""

    @pytest.mark.asyncio
    async def test_get_by_category_returns_results(self, store, mock_pool):
        mock_pool.fetch.return_value = [
            {
                "id": uuid4(), "content": "fact1", "category": "tech",
                "confidence": 0.9, "importance": 0.8, "tags": [],
                "source": None, "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        ]
        results = await store.get_by_category("user1", "tech")
        assert len(results) == 1
        assert results[0]["content"] == "fact1"

    @pytest.mark.asyncio
    async def test_get_by_category_handles_error(self, store, mock_pool):
        mock_pool.fetch.side_effect = RuntimeError("fail")
        result = await store.get_by_category("user1", "tech")
        assert result == []
