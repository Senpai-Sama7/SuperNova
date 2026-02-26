"""Shared test fixtures for SuperNova test suite."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def db_pool():
    """Mock asyncpg pool pointing to supernova_test database."""
    pool = AsyncMock()
    pool.dsn = "postgresql://localhost:5432/supernova_test"
    pool.execute = AsyncMock(return_value="SELECT 1")
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def redis_client():
    """Mock aioredis client on db 15 for test isolation."""
    client = AsyncMock()
    client.db = 15
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.ping = AsyncMock(return_value=True)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_llm():
    """Mock LiteLLM router with predefined responses — no API calls."""
    router = AsyncMock()
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Mock LLM response"
    response.usage.prompt_tokens = 100
    response.usage.completion_tokens = 50
    router.acompletion = AsyncMock(return_value=response)
    return router


@pytest.fixture
def mock_embedder():
    """Returns deterministic 1536-dim zero vectors — no API calls."""
    embedder = AsyncMock()
    embedder.embed = AsyncMock(return_value=[0.0] * 1536)
    return embedder


@pytest.fixture
def tool_registry():
    """Registry with READ_FILES | WEB_SEARCH granted."""
    from supernova.infrastructure.tools.registry import Capability, ToolRegistry

    return ToolRegistry(granted_capabilities=Capability.READ_FILES | Capability.WEB_SEARCH)


@pytest.fixture
def interrupt_coordinator():
    """Fresh InterruptCoordinator with mock broadcaster."""
    import sys
    # interrupts.py is at project root, add to path if needed
    root = str(__import__("pathlib").Path(__file__).resolve().parents[2])
    if root not in sys.path:
        sys.path.insert(0, root)

    from interrupts import InterruptCoordinator

    broadcaster = AsyncMock()
    broadcaster.send = AsyncMock()
    return InterruptCoordinator(websocket_broadcaster=broadcaster)
