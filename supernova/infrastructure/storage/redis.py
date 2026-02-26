"""Redis async client for working memory and caching.

Provides AsyncRedisClient with working memory operations
using msgpack serialization.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

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
        url: Optional[str] = None,
        working_memory_ttl: int = DEFAULT_WORKING_MEMORY_TTL,
    ) -> None:
        """Initialize the Redis client.
        
        Args:
            url: Redis connection URL. If None, uses config.
            working_memory_ttl: TTL for working memory in seconds. Default 86400.
        """
        self._client: Optional[Redis] = None
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
    ) -> Optional[dict[str, Any]]:
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
        ttl: Optional[int] = None,
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
    ) -> Optional[list[float]]:
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
_client_instance: Optional[AsyncRedisClient] = None


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
