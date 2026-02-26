"""Tests for api/main.py health and shutdown behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from supernova.api import main as main_mod


@pytest.mark.asyncio
async def test_healthz_all_services_healthy() -> None:
    """healthz returns ok=true when postgres, redis, and neo4j checks pass."""
    mock_pool = AsyncMock()
    mock_pool.fetchval = AsyncMock(return_value=1)

    mock_redis = MagicMock()
    mock_redis.get_client.return_value = AsyncMock(ping=AsyncMock(return_value=True))

    mock_result = AsyncMock()
    mock_result.single = AsyncMock(return_value={"ok": 1})
    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)

    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = mock_session
    session_cm.__aexit__.return_value = None

    mock_driver = MagicMock()
    mock_driver.session.return_value = session_cm
    mock_driver.close = AsyncMock()

    with (
        patch("supernova.api.main.get_postgres_pool", AsyncMock(return_value=mock_pool)),
        patch("supernova.api.main.get_redis_client", AsyncMock(return_value=mock_redis)),
        patch("supernova.api.main.AsyncGraphDatabase.driver", return_value=mock_driver),
    ):
        result = await main_mod.healthz()

    assert result["ok"] is True
    assert result["services"] == {
        "postgres": True,
        "redis": True,
        "neo4j": True,
    }
    mock_driver.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_healthz_degrades_when_services_fail() -> None:
    """healthz marks each backend unhealthy when probe raises."""
    with (
        patch("supernova.api.main.get_postgres_pool", AsyncMock(side_effect=RuntimeError("pg"))),
        patch("supernova.api.main.get_redis_client", AsyncMock(side_effect=RuntimeError("redis"))),
        patch("supernova.api.main.AsyncGraphDatabase.driver", side_effect=RuntimeError("neo4j")),
    ):
        result = await main_mod.healthz()

    assert result["ok"] is False
    assert result["services"] == {
        "postgres": False,
        "redis": False,
        "neo4j": False,
    }


@pytest.mark.asyncio
async def test_lifespan_shutdown_closes_shared_clients() -> None:
    """Lifespan shutdown closes postgres and redis global clients."""
    with (
        patch("supernova.api.main.close_postgres_pool", AsyncMock()) as mock_close_pg,
        patch("supernova.api.main.close_redis_client", AsyncMock()) as mock_close_redis,
    ):
        async with main_mod._lifespan(main_mod.app):
            pass

    mock_close_pg.assert_awaited_once()
    mock_close_redis.assert_awaited_once()
