"""Semantic memory store using pgvector hybrid search.

Provides vector + full-text hybrid search with RRF (Reciprocal Rank Fusion),
Redis-cached embeddings via LiteLLM, and content-hash deduplication.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import litellm

from supernova.config import get_settings
from supernova.infrastructure.storage.postgres import AsyncPostgresPool
from supernova.infrastructure.storage.redis import AsyncRedisClient

logger = logging.getLogger(__name__)

RRF_K = 60


class SemanticMemoryStore:
    """pgvector-backed semantic memory with hybrid search.

    Combines vector cosine similarity and full-text BM25 ranking
    via Reciprocal Rank Fusion for robust retrieval.
    """

    def __init__(
        self,
        pool: AsyncPostgresPool,
        redis: AsyncRedisClient | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self._pool = pool
        self._redis = redis
        settings = get_settings()
        # Use local embedding model if no OpenAI key configured
        if embedding_model is None:
            if not settings.llm.openai_api_key:
                self._embedding_model = "ollama/nomic-embed-text"
            else:
                self._embedding_model = "text-embedding-3-small"
        else:
            self._embedding_model = embedding_model

    async def embed(self, text: str) -> list[float]:
        """Generate embedding with Redis caching.

        Uses LiteLLM to call text-embedding-3-small. Cached in Redis
        with key ``em:{sha256(text)[:16]}`` and TTL=3600s.
        """
        if self._redis:
            try:
                cached = await self._redis.embedding_cache_get(text)
                if cached is not None:
                    return cached
            except Exception as e:
                logger.warning(f"Embedding cache read failed: {e}")

        response = await litellm.aembedding(model=self._embedding_model, input=[text])
        embedding = response.data[0]["embedding"]

        if self._redis:
            try:
                await self._redis.embedding_cache_set(text, embedding, ttl=3600)
            except Exception as e:
                logger.warning(f"Embedding cache write failed: {e}")

        return embedding

    async def search(
        self,
        query: str,
        user_id: str,
        *,
        limit: int = 10,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid vector + full-text search with RRF.

        Returns list of memory dicts sorted by combined RRF score.
        """
        try:
            embedding = await self.embed(query)
            emb_str = "[" + ",".join(str(v) for v in embedding) + "]"

            cat_clause = "AND category = $5" if category else ""
            params: list[Any] = [emb_str, query, user_id, limit * 2]
            if category:
                params.append(category)

            sql = f"""
            WITH vec AS (
                SELECT id, content, category, confidence, importance, tags, source,
                       created_at, updated_at,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) AS rank
                FROM semantic_memories
                WHERE user_id = $3 {cat_clause}
                ORDER BY embedding <=> $1::vector
                LIMIT $4
            ),
            fts AS (
                SELECT id,
                       ROW_NUMBER() OVER (
                           ORDER BY ts_rank(to_tsvector('english', content),
                                            plainto_tsquery('english', $2)) DESC
                       ) AS rank
                FROM semantic_memories
                WHERE user_id = $3 {cat_clause}
                  AND to_tsvector('english', content) @@ plainto_tsquery('english', $2)
                LIMIT $4
            )
            SELECT v.id, v.content, v.category, v.confidence, v.importance,
                   v.tags, v.source, v.created_at, v.updated_at,
                   (1.0 / ({RRF_K} + v.rank))
                   + COALESCE(1.0 / ({RRF_K} + f.rank), 0) AS rrf_score
            FROM vec v
            LEFT JOIN fts f ON v.id = f.id
            ORDER BY rrf_score DESC
            LIMIT {limit}
            """

            rows = await self._pool.fetch(sql, *params)
            return [
                {
                    "id": str(r["id"]),
                    "content": r["content"],
                    "category": r["category"],
                    "confidence": r["confidence"],
                    "importance": r["importance"],
                    "tags": r["tags"],
                    "source": r["source"],
                    "score": float(r["rrf_score"]),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    async def upsert(
        self,
        content: str,
        user_id: str,
        *,
        category: str | None = None,
        confidence: float = 0.5,
        importance: float = 0.5,
        tags: list[str] | None = None,
        source: str | None = None,
    ) -> UUID | None:
        """Insert or update a memory by content hash.

        Uses MD5 of content for deduplication within a user scope.
        Returns UUID of the upserted memory, or None on error.
        """
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            embedding = await self.embed(content)
            emb_str = "[" + ",".join(str(v) for v in embedding) + "]"

            existing = await self._pool.fetchval(
                "SELECT id FROM semantic_memories WHERE user_id = $1 AND md5(content) = $2 LIMIT 1",
                user_id, content_hash,
            )

            if existing:
                await self._pool.execute(
                    """UPDATE semantic_memories
                       SET embedding = $1::vector, confidence = $2, importance = $3,
                           tags = $4, source = $5, updated_at = now()
                       WHERE id = $6""",
                    emb_str, confidence, importance, tags or [], source, existing,
                )
                return existing
            else:
                return await self._pool.fetchval(
                    """INSERT INTO semantic_memories
                       (user_id, content, embedding, category, confidence, importance, tags, source)
                       VALUES ($1, $2, $3::vector, $4, $5, $6, $7, $8)
                       RETURNING id""",
                    user_id, content, emb_str, category, confidence, importance, tags or [], source,
                )
        except Exception as e:
            logger.error(f"Error upserting semantic memory: {e}")
            return None

    async def update_access_time(self, memory_id: UUID) -> None:
        """Update last_accessed timestamp and increment access_count."""
        try:
            await self._pool.execute(
                """UPDATE semantic_memories
                   SET last_accessed_at = $1, access_count = access_count + 1
                   WHERE id = $2""",
                datetime.now(UTC), memory_id,
            )
        except Exception as e:
            logger.error(f"Error updating access time: {e}")

    async def get_by_category(
        self, user_id: str, category: str,
    ) -> list[dict[str, Any]]:
        """Get all memories for a user in a category, ordered by importance."""
        try:
            rows = await self._pool.fetch(
                """SELECT id, content, category, confidence, importance, tags, source,
                          created_at, updated_at
                   FROM semantic_memories
                   WHERE user_id = $1 AND category = $2
                   ORDER BY importance DESC""",
                user_id, category,
            )
            return [
                {
                    "id": str(r["id"]),
                    "content": r["content"],
                    "category": r["category"],
                    "confidence": r["confidence"],
                    "importance": r["importance"],
                    "tags": r["tags"],
                    "source": r["source"],
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Error getting memories by category: {e}")
            return []
