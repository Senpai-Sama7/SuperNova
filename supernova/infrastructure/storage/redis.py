"""Redis async client for working memory and caching.

Provides AsyncRedisClient with working memory operations
using msgpack serialization.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import msgpack
from redis.asyncio import Redis

from supernova.config import get_settings

logger = logging.getLogger(__name__)

# Default TTL for working memory (24 hours)
DEFAULT_WORKING_MEMORY_TTL = 86400

# Key prefixes
WORKING_MEMORY_PREFIX = "wm"
EMBEDDING_CACHE_PREFIX = "em"


class AsyncRedisClient:
    """Async Redis client for SuperNova.

    Manages connections to Redis and provides methods for
    working memory storage and embedding caching.

    Example:
        >>> client = AsyncRedisClient()
        >>> await client.connect()
        >>> await client.working_memory_set("session_123", {"goal": "test"})
        >>> data = await client.working_memory_get("session_123")
        >>> await client.disconnect()
    """

    def __init__(
        self,
        url: str | None = None,
        working_memory_ttl: int = DEFAULT_WORKING_MEMORY_TTL,
    ) -> None:
        """Initialize the Redis client.

        Args:
            url: Redis connection URL. If None, uses config.
            working_memory_ttl: TTL for working memory in seconds. Default 86400.
        """
        self._client: Redis | None = None
        self._url = url or get_settings().redis.url
        self._working_memory_ttl = working_memory_ttl

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._client is not None:
            logger.warning("Redis client already connected")
            return

        logger.info("Connecting to Redis")
        self._client = Redis.from_url(
            self._url,
            decode_responses=False,  # We use bytes for msgpack
        )

        # Test connection
        await self._client.ping()
        logger.info("Redis connected successfully")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client is None:
            logger.warning("Redis client not connected")
            return

        logger.info("Disconnecting from Redis")
        await self._client.close()
        self._client = None
        logger.info("Redis disconnected")

    def get_client(self) -> Redis:
        """Get the Redis client.

        Returns:
            Redis client instance.

        Raises:
            RuntimeError: If not connected.
        """
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    def _serialize(self, data: Any) -> bytes:
        """Serialize data to bytes using msgpack.

        Args:
            data: Data to serialize.

        Returns:
            Serialized bytes.
        """
        return msgpack.packb(data, use_bin_type=True)

    def _deserialize(self, data: bytes | None) -> Any:
        """Deserialize bytes to data using msgpack.

        Args:
            data: Bytes to deserialize.

        Returns:
            Deserialized data or None if input is None.
        """
        if data is None:
            return None
        return msgpack.unpackb(data, raw=False)

    def _working_memory_key(self, session_id: str) -> str:
        """Generate working memory key.

        Args:
            session_id: Session identifier.

        Returns:
            Redis key string.
        """
        return f"{WORKING_MEMORY_PREFIX}:{session_id}"

    async def working_memory_get(
        self,
        session_id: str
    ) -> dict[str, Any] | None:
        """Get working memory for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Working memory dict or None if not found.
        """
        client = self.get_client()
        key = self._working_memory_key(session_id)

        data = await client.get(key)
        if data is None:
            return None

        return self._deserialize(data)

    async def working_memory_set(
        self,
        session_id: str,
        data: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set working memory for a session.

        Args:
            session_id: Session identifier.
            data: Working memory data.
            ttl: TTL in seconds. Uses default if not specified.
        """
        client = self.get_client()
        key = self._working_memory_key(session_id)

        serialized = self._serialize(data)
        await client.set(
            key,
            serialized,
            ex=ttl or self._working_memory_ttl
        )

    async def working_memory_delete(self, session_id: str) -> None:
        """Delete working memory for a session.

        Args:
            session_id: Session identifier.
        """
        client = self.get_client()
        key = self._working_memory_key(session_id)
        await client.delete(key)

    async def working_memory_exists(self, session_id: str) -> bool:
        """Check if working memory exists.

        Args:
            session_id: Session identifier.

        Returns:
            True if exists, False otherwise.
        """
        client = self.get_client()
        key = self._working_memory_key(session_id)
        return await client.exists(key) > 0

    async def working_memory_list(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List working memory entries.

        Scans keys with the working memory prefix and returns decoded payloads.

        Args:
            limit: Maximum entries to return.

        Returns:
            List of objects with keys:
                - session_id: Redis session identifier.
                - memory: Decoded working memory payload.
        """
        client = self.get_client()
        entries: list[dict[str, Any]] = []
        cursor = 0
        match_pattern = f"{WORKING_MEMORY_PREFIX}:*"

        while True:
            cursor, keys = await client.scan(
                cursor=cursor,
                match=match_pattern,
                count=min(limit, 200),
            )

            for raw_key in keys:
                if len(entries) >= limit:
                    break

                key = (
                    raw_key.decode("utf-8")
                    if isinstance(raw_key, (bytes, bytearray))
                    else str(raw_key)
                )
                if ":" not in key:
                    continue

                session_id = key.split(":", 1)[1]
                data = await self.working_memory_get(session_id)
                if data is None:
                    continue

                entries.append(
                    {
                        "session_id": session_id,
                        "memory": data,
                    }
                )

            if cursor == 0 or len(entries) >= limit:
                break

        return entries

    def _embedding_cache_key(self, text: str) -> str:
        """Generate embedding cache key.

        Uses SHA-256 hash of text truncated to 16 chars.

        Args:
            text: Text to embed.

        Returns:
            Redis key string.
        """
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"{EMBEDDING_CACHE_PREFIX}:{text_hash}"

    async def embedding_cache_get(
        self,
        text: str
    ) -> list[float] | None:
        """Get cached embedding for text.

        Args:
            text: Text that was embedded.

        Returns:
            Cached embedding vector or None.
        """
        client = self.get_client()
        key = self._embedding_cache_key(text)

        data = await client.get(key)
        if data is None:
            return None

        return self._deserialize(data)

    async def embedding_cache_set(
        self,
        text: str,
        embedding: list[float],
        ttl: int = 3600,
    ) -> None:
        """Cache embedding for text.

        Args:
            text: Text that was embedded.
            embedding: Embedding vector.
            ttl: TTL in seconds. Default 3600 (1 hour).
        """
        client = self.get_client()
        key = self._embedding_cache_key(text)

        serialized = self._serialize(embedding)
        await client.set(key, serialized, ex=ttl)


# Global client instance
_client_instance: AsyncRedisClient | None = None


async def get_redis_client() -> AsyncRedisClient:
    """Get or create the global Redis client.

    Returns:
        AsyncRedisClient instance.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = AsyncRedisClient()
        await _client_instance.connect()
    return _client_instance


async def close_redis_client() -> None:
    """Close the global Redis client."""
    global _client_instance
    if _client_instance is not None:
        await _client_instance.disconnect()
        _client_instance = None
