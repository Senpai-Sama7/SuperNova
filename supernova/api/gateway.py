"""FastAPI gateway for SuperNova — main application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from starlette.responses import Response

from supernova.api.auth import create_access_token, get_current_user, verify_token
from supernova.api.routes.agent import router as agent_router
from supernova.api.routes.dashboard import router as dashboard_router
from supernova.config import get_settings
from supernova.infrastructure.storage import (
    close_postgres_pool,
    close_redis_client,
    get_postgres_pool,
    get_redis_client,
)
from supernova.runtime_config_guardrails import validate_runtime_configuration
from supernova.api.websockets import WebSocketBroadcaster, handle_agent_stream

logger = logging.getLogger(__name__)
settings = get_settings()
validate_runtime_configuration()

_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application startup and shutdown resources."""
    _state["broadcaster"] = WebSocketBroadcaster()
    try:
        yield
    finally:
        await close_postgres_pool()
        await close_redis_client()
        episodic_store = _state.get("episodic_store")
        if episodic_store is not None:
            await episodic_store.close()


app = FastAPI(
    title="SuperNova Gateway",
    version="2.0.0",
    description="Main API gateway for SuperNova.",
    lifespan=lifespan,
)

cors_origins = set(settings.security.cors_origins_list)
if settings.is_development:
    cors_origins.update(
        {
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, dependencies=[Depends(get_current_user)])
app.include_router(agent_router)


@app.get("/metrics")
async def prometheus_metrics(user_id: str = Depends(get_current_user)) -> Any:
    registry = CollectorRegistry()
    payload = generate_latest(registry)
    return Response(payload, media_type=CONTENT_TYPE_LATEST)


@app.websocket("/health/ws")
async def health_ws(ws: WebSocket, token: str = Query(...)) -> None:
    """WebSocket for real-time health alerts. Requires JWT in query param."""
    if not verify_token(token):
        await ws.close(code=4001, reason="Invalid token")
        return

    await ws.accept()
    try:
        while True:
            await ws.send_json({"type": "health", "ok": True, "timestamp": datetime.now(UTC).isoformat()})
            await ws.receive_text()
    except WebSocketDisconnect:
        logger.info("Health websocket disconnected")


@app.websocket("/agent/stream/{session_id}")
async def agent_stream(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """WebSocket endpoint for streaming agent events. Requires JWT in query param."""
    if not verify_token(token):
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    broadcaster = _state.get("broadcaster")
    agent_graph = _state.get("agent_graph")

    if broadcaster is None or agent_graph is None:
        await websocket.send_json({"type": "error", "message": "Agent graph not initialized"})
        await websocket.close()
        return

    try:
        data = await websocket.receive_json()
        await handle_agent_stream(websocket, session_id, broadcaster, agent_graph, data)
    except WebSocketDisconnect:
        logger.info("Agent websocket disconnected: %s", session_id)


@app.get("/fleet/summary")
async def get_fleet_summary(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    return {"ok": True, "user_id": user_id}


@app.get("/costs/summary")
async def get_cost_summary(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    return {"ok": True, "user_id": user_id}
