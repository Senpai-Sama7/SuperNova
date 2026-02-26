"""Episodic memory store using Graphiti temporal knowledge graph.

Wraps graphiti_core.Graphiti for recording and retrieving temporal
episodes from Neo4j. All methods are exception-safe — errors are
logged but never raised to callers.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class EpisodicMemoryStore:
    """Temporal knowledge graph store backed by Graphiti/Neo4j.

    Provides episode recording, semantic recall, and recent episode
    retrieval for the cognitive loop's REMEMBER and CONSOLIDATE phases.
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_password: str,
        llm_client: LLMClient | None = None,
        embedder: EmbedderClient | None = None,
        neo4j_user: str = "neo4j",
    ) -> None:
        self._client = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password,
            llm_client=llm_client,
            embedder=embedder,
        )

    async def close(self) -> None:
        """Close the Graphiti client connection."""
        try:
            await self._client.close()
        except Exception as e:
            logger.error(f"Error closing episodic store: {e}")

    async def record_episode(
        self,
        content: str,
        *,
        name: str = "episode",
        source: str = "agent",
        group_id: str | None = None,
        reference_time: datetime | None = None,
    ) -> None:
        """Record an episode to the temporal knowledge graph.

        Args:
            content: Episode text content.
            name: Episode name/label.
            source: Source description.
            group_id: Optional group for scoping.
            reference_time: When the episode occurred. Defaults to now.
        """
        try:
            await self._client.add_episode(
                name=name,
                episode_body=content,
                source_description=source,
                reference_time=reference_time or datetime.now(UTC),
                group_id=group_id,
            )
        except Exception as e:
            logger.error(f"Error recording episode: {e}")

    async def recall(
        self,
        query: str,
        *,
        limit: int = 10,
        group_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve episodes by semantic similarity.

        Args:
            query: Search query text.
            limit: Maximum results to return.
            group_ids: Optional group filter.

        Returns:
            List of dicts with keys: fact, valid_from, valid_until, score.
        """
        try:
            edges = await self._client.search(
                query=query,
                num_results=limit,
                group_ids=group_ids,
            )
            return [
                {
                    "fact": edge.fact,
                    "valid_from": edge.valid_at.isoformat() if edge.valid_at else None,
                    "valid_until": edge.invalid_at.isoformat() if edge.invalid_at else None,
                    "score": round(1.0 - i / max(len(edges), 1), 3),
                }
                for i, edge in enumerate(edges)
            ]
        except Exception as e:
            logger.error(f"Error recalling episodes: {e}")
            return []

    async def get_recent(
        self,
        hours: int = 24,
        *,
        last_n: int = 50,
        group_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch recent raw episodes for consolidation.

        Args:
            hours: Look-back window in hours.
            last_n: Maximum episodes to retrieve.
            group_ids: Optional group filter.

        Returns:
            List of dicts with episode data.
        """
        try:
            episodes = await self._client.retrieve_episodes(
                reference_time=datetime.now(UTC),
                last_n=last_n,
                group_ids=group_ids,
            )
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            return [
                {
                    "uuid": str(ep.uuid),
                    "name": ep.name,
                    "content": ep.content,
                    "created_at": ep.created_at.isoformat() if ep.created_at else None,
                    "source": str(ep.source) if ep.source else None,
                }
                for ep in episodes
                if ep.created_at and ep.created_at >= cutoff
            ]
        except Exception as e:
            logger.error(f"Error getting recent episodes: {e}")
            return []
