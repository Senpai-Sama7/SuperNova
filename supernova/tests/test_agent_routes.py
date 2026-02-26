"""Tests for api/routes/agent.py — agent message endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


def _make_app():
    from fastapi import FastAPI

    from supernova.api.routes.agent import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_post_agent_message():
    mock_store = AsyncMock()
    mock_store.get.return_value = None  # new session
    mock_pool = AsyncMock()

    with (
        patch("supernova.api.routes.agent.get_working_memory_store", return_value=mock_store),
        patch("supernova.api.routes.agent.get_postgres_pool", return_value=mock_pool),
    ):
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/message",
                json={"session_id": "s1", "message": "hello"},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert data["session_id"] == "s1"
    mock_store.set.assert_awaited_once()
    mock_pool.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_agent_message_existing_session():
    from supernova.core.memory.working import WorkingMemory

    existing = WorkingMemory(session_id="s2", scratchpad="prior note")
    mock_store = AsyncMock()
    mock_store.get.return_value = existing
    mock_pool = AsyncMock()

    with (
        patch("supernova.api.routes.agent.get_working_memory_store", return_value=mock_store),
        patch("supernova.api.routes.agent.get_postgres_pool", return_value=mock_pool),
    ):
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/agent/message",
                json={"session_id": "s2", "message": "follow-up"},
            )
    assert resp.status_code == 200
    saved = mock_store.set.call_args[0][0]
    assert "prior note" in saved.scratchpad
    assert "follow-up" in saved.scratchpad
