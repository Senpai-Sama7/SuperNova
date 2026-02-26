"""Tests for EpisodicMemoryStore."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from supernova.core.memory.episodic import EpisodicMemoryStore


@pytest.fixture
def mock_graphiti():
    """Create a mock Graphiti client."""
    with patch("supernova.core.memory.episodic.Graphiti") as MockGraphiti:
        instance = MagicMock()
        instance.add_episode = AsyncMock()
        instance.search = AsyncMock(return_value=[])
        instance.retrieve_episodes = AsyncMock(return_value=[])
        instance.close = AsyncMock()
        MockGraphiti.return_value = instance
        yield instance


@pytest.fixture
def store(mock_graphiti):
    """Create an EpisodicMemoryStore with mocked Graphiti."""
    return EpisodicMemoryStore(
        neo4j_uri="bolt://localhost:7687",
        neo4j_password="test",
    )


class TestEpisodicMemoryStoreInit:
    """5.3.1: Class wraps graphiti_core.Graphiti."""

    def test_constructor_creates_graphiti_client(self, store, mock_graphiti):
        assert store._client is mock_graphiti


class TestRecordEpisode:
    """5.3.2: record_episode writes to Graphiti."""

    @pytest.mark.asyncio
    async def test_record_episode_calls_add_episode(self, store, mock_graphiti):
        await store.record_episode("user asked about weather", name="chat")
        mock_graphiti.add_episode.assert_called_once()
        call_kwargs = mock_graphiti.add_episode.call_args.kwargs
        assert call_kwargs["episode_body"] == "user asked about weather"
        assert call_kwargs["name"] == "chat"

    @pytest.mark.asyncio
    async def test_record_episode_handles_exception(self, store, mock_graphiti):
        mock_graphiti.add_episode.side_effect = RuntimeError("Neo4j down")
        # Should not raise
        await store.record_episode("test content")


class TestRecall:
    """5.3.3: recall returns list[dict] with fact, valid_from, valid_until, score."""

    @pytest.mark.asyncio
    async def test_recall_returns_formatted_results(self, store, mock_graphiti):
        edge = MagicMock()
        edge.fact = "The sky is blue"
        edge.valid_at = datetime(2025, 1, 1, tzinfo=UTC)
        edge.invalid_at = None
        mock_graphiti.search.return_value = [edge]

        results = await store.recall("sky color")
        assert len(results) == 1
        assert results[0]["fact"] == "The sky is blue"
        assert results[0]["valid_from"] == "2025-01-01T00:00:00+00:00"
        assert results[0]["valid_until"] is None
        assert results[0]["score"] == 1.0

    @pytest.mark.asyncio
    async def test_recall_respects_limit(self, store, mock_graphiti):
        await store.recall("test", limit=5)
        assert mock_graphiti.search.call_args.kwargs["num_results"] == 5

    @pytest.mark.asyncio
    async def test_recall_handles_exception(self, store, mock_graphiti):
        mock_graphiti.search.side_effect = RuntimeError("fail")
        result = await store.recall("test")
        assert result == []


class TestGetRecent:
    """5.3.4: get_recent fetches raw episodes from last N hours."""

    @pytest.mark.asyncio
    async def test_get_recent_returns_episodes(self, store, mock_graphiti):
        ep = MagicMock()
        ep.uuid = "abc-123"
        ep.name = "chat_episode"
        ep.content = "Hello world"
        ep.created_at = datetime.now(UTC)
        ep.source = "agent"
        mock_graphiti.retrieve_episodes.return_value = [ep]

        results = await store.get_recent(hours=24)
        assert len(results) == 1
        assert results[0]["content"] == "Hello world"
        assert results[0]["uuid"] == "abc-123"

    @pytest.mark.asyncio
    async def test_get_recent_filters_old_episodes(self, store, mock_graphiti):
        old_ep = MagicMock()
        old_ep.uuid = "old"
        old_ep.name = "old"
        old_ep.content = "old"
        old_ep.created_at = datetime(2020, 1, 1, tzinfo=UTC)
        old_ep.source = "agent"
        mock_graphiti.retrieve_episodes.return_value = [old_ep]

        results = await store.get_recent(hours=1)
        assert results == []

    @pytest.mark.asyncio
    async def test_get_recent_handles_exception(self, store, mock_graphiti):
        mock_graphiti.retrieve_episodes.side_effect = RuntimeError("fail")
        result = await store.get_recent()
        assert result == []


class TestErrorHandling:
    """5.3.5: All methods catch exceptions and return empty/None."""

    @pytest.mark.asyncio
    async def test_close_handles_exception(self, store, mock_graphiti):
        mock_graphiti.close.side_effect = RuntimeError("fail")
        await store.close()  # Should not raise
