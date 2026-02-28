"""Tests for infrastructure/storage — AsyncRedisClient and AsyncPostgresPool."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import msgpack
import pytest

from supernova.infrastructure.storage.postgres import AsyncPostgresPool
from supernova.infrastructure.storage.redis import AsyncRedisClient

# ── AsyncRedisClient ───────────────────────────────────────────────


class TestRedisClient:
    """Cover connect, disconnect, get_client, serialize, deserialize, and CRUD."""

    def _make_client(self) -> AsyncRedisClient:
        with patch("supernova.infrastructure.storage.redis.get_settings") as m:
            m.return_value.redis.url = "redis://localhost:6379"
            return AsyncRedisClient(url="redis://fake:6379")

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        client = self._make_client()
        mock_redis = AsyncMock()
        with patch("supernova.infrastructure.storage.redis.Redis") as cls:
            cls.from_url.return_value = mock_redis
            await client.connect()
            assert client._client is mock_redis
            mock_redis.ping.assert_awaited_once()

            await client.disconnect()
            assert client._client is None
            mock_redis.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        client = self._make_client()
        client._client = MagicMock()  # pretend connected
        await client.connect()  # should warn, not crash

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self):
        client = self._make_client()
        await client.disconnect()  # should warn, not crash

    def test_get_client_not_connected(self):
        client = self._make_client()
        with pytest.raises(RuntimeError, match="not connected"):
            client.get_client()

    def test_serialize_deserialize(self):
        client = self._make_client()
        data = {"key": "value", "num": 42}
        packed = client._serialize(data)
        assert isinstance(packed, bytes)
        assert client._deserialize(packed) == data
        assert client._deserialize(None) is None

    def test_working_memory_key(self):
        client = self._make_client()
        key = client._working_memory_key("sess-1")
        assert "sess-1" in key

    @pytest.mark.asyncio
    async def test_working_memory_crud(self):
        client = self._make_client()
        mock_redis = AsyncMock()
        client._client = mock_redis

        # set
        await client.working_memory_set("s1", {"goal": "test"})
        mock_redis.set.assert_awaited_once()

        # get — found
        mock_redis.get.return_value = msgpack.packb({"goal": "test"}, use_bin_type=True)
        result = await client.working_memory_get("s1")
        assert result == {"goal": "test"}

        # get — not found
        mock_redis.get.return_value = None
        assert await client.working_memory_get("s1") is None

        # exists
        mock_redis.exists.return_value = 1
        assert await client.working_memory_exists("s1") is True

        # delete
        await client.working_memory_delete("s1")
        mock_redis.delete.assert_awaited()

    @pytest.mark.asyncio
    async def test_working_memory_list(self):
        client = self._make_client()
        mock_redis = AsyncMock()
        client._client = mock_redis

        mock_redis.scan.return_value = (0, [b"wm:sess-1"])
        mock_redis.get.return_value = msgpack.packb({"goal": "x"}, use_bin_type=True)

        entries = await client.working_memory_list(limit=10)
        assert len(entries) == 1
        assert entries[0]["session_id"] == "sess-1"

    @pytest.mark.asyncio
    async def test_embedding_cache_crud(self):
        client = self._make_client()
        mock_redis = AsyncMock()
        client._client = mock_redis

        vec = [0.1, 0.2, 0.3]
        await client.embedding_cache_set("hello", vec)
        mock_redis.set.assert_awaited()

        mock_redis.get.return_value = msgpack.packb(vec, use_bin_type=True)
        result = await client.embedding_cache_get("hello")
        assert result == vec

        mock_redis.get.return_value = None
        assert await client.embedding_cache_get("miss") is None

    def test_embedding_cache_key(self):
        client = self._make_client()
        key = client._embedding_cache_key("test text")
        assert "em:" in key


# ── AsyncPostgresPool ──────────────────────────────────────────────


class TestPostgresPool:
    """Cover connect, disconnect, get_pool, query helpers."""

    def _make_pool(self) -> AsyncPostgresPool:
        with patch("supernova.infrastructure.storage.postgres.get_settings") as m:
            m.return_value.database_url = "postgresql://localhost/test"
            return AsyncPostgresPool(dsn="postgresql://localhost/test")

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        pool = self._make_pool()
        mock_pg_pool = AsyncMock()
        with patch("supernova.infrastructure.storage.postgres.asyncpg") as apg:
            apg.create_pool = AsyncMock(return_value=mock_pg_pool)
            await pool.connect()
            assert pool._pool is mock_pg_pool

            await pool.disconnect()
            assert pool._pool is None
            mock_pg_pool.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        pool = self._make_pool()
        pool._pool = MagicMock()
        await pool.connect()  # should warn, not crash

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self):
        pool = self._make_pool()
        await pool.disconnect()  # should warn, not crash

    def test_get_pool_not_connected(self):
        pool = self._make_pool()
        with pytest.raises(RuntimeError, match="not initialized"):
            pool.get_pool()

    @pytest.mark.asyncio
    async def test_execute(self):
        pool = self._make_pool()
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "INSERT 1"
        mock_pg_pool = MagicMock()

        @asynccontextmanager
        async def fake_acquire():
            yield mock_conn

        mock_pg_pool.acquire = fake_acquire
        pool._pool = mock_pg_pool

        result = await pool.execute("INSERT INTO t VALUES ($1)", 1)
        assert result == "INSERT 1"

    @pytest.mark.asyncio
    async def test_fetch(self):
        pool = self._make_pool()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [{"id": 1}]
        mock_pg_pool = MagicMock()

        @asynccontextmanager
        async def fake_acquire():
            yield mock_conn

        mock_pg_pool.acquire = fake_acquire
        pool._pool = mock_pg_pool

        rows = await pool.fetch("SELECT * FROM t")
        assert rows == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_fetchrow(self):
        pool = self._make_pool()
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {"id": 1}
        mock_pg_pool = MagicMock()

        @asynccontextmanager
        async def fake_acquire():
            yield mock_conn

        mock_pg_pool.acquire = fake_acquire
        pool._pool = mock_pg_pool

        row = await pool.fetchrow("SELECT * FROM t LIMIT 1")
        assert row == {"id": 1}

    @pytest.mark.asyncio
    async def test_fetchval(self):
        pool = self._make_pool()
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = 42
        mock_pg_pool = MagicMock()

        @asynccontextmanager
        async def fake_acquire():
            yield mock_conn

        mock_pg_pool.acquire = fake_acquire
        pool._pool = mock_pg_pool

        val = await pool.fetchval("SELECT COUNT(*) FROM t")
        assert val == 42

    @pytest.mark.asyncio
    async def test_executemany(self):
        pool = self._make_pool()
        mock_conn = AsyncMock()
        mock_pg_pool = MagicMock()

        @asynccontextmanager
        async def fake_acquire():
            yield mock_conn

        mock_pg_pool.acquire = fake_acquire
        pool._pool = mock_pg_pool

        await pool.executemany("INSERT INTO t VALUES ($1)", [(1,), (2,)])
        mock_conn.executemany.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_init_connection(self):
        pool = self._make_pool()
        mock_conn = AsyncMock()
        await pool._init_connection(mock_conn)
        mock_conn.execute.assert_awaited_with("SET timezone='UTC'")
