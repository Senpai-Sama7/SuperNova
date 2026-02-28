"""FastAPI gateway for SuperNova — main application entry point."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from starlette.responses import Response

from supernova.api.auth import TokenResponse, create_access_token, get_current_user, verify_token
from supernova.api.routes.agent import router as agent_router
from supernova.api.routes.dashboard import router as dashboard_router
from supernova.api.websockets import WebSocketBroadcaster, handle_agent_stream
from supernova.config import get_settings
from supernova.infrastructure.storage import (
    close_postgres_pool,
    close_redis_client,
    get_postgres_pool,
    get_redis_client,
)
from supernova.runtime_config_guardrails import validate_runtime_configuration

logger = logging.getLogger(__name__)
settings = get_settings()
validate_runtime_configuration()

_state: dict[str, Any] = {}
_RATE_LIMIT_WINDOW_SECONDS = 60.0
_RATE_LIMIT_MAX_CALLS = 5
_rate_limit_state: dict[str, list[float]] = {}


def _audit_privileged_action(action: str, user_id: str | None, details: dict[str, Any] | None = None) -> None:
    """Emit a structured audit-style log for privileged gateway actions."""
    logger.info(
        "audit_event action=%s user_id=%s details=%s",
        action,
        user_id or "anonymous",
        details or {},
    )



def _enforce_rate_limit(bucket: str, *, now_ts: float | None = None) -> None:
    """Apply a simple in-memory fixed-window rate limit."""
    current = now_ts if now_ts is not None else time.monotonic()
    window_start = current - _RATE_LIMIT_WINDOW_SECONDS
    entries = [ts for ts in _rate_limit_state.get(bucket, []) if ts >= window_start]
    if len(entries) >= _RATE_LIMIT_MAX_CALLS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    entries.append(current)
    _rate_limit_state[bucket] = entries



def _client_host(client: Any) -> str:
    """Return a normalized client host string for audit and abuse-control buckets."""
    if client is None:
        return "unknown"
    host = getattr(client, "host", None)
    return host or "unknown"


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


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "timestamp": datetime.now(UTC).isoformat()}


@app.get("/health/deep")
async def deep_health(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    status: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {
            "postgres": False,
            "redis": False,
        },
        "user_id": user_id,
    }

    try:
        pool = await get_postgres_pool()
        value = await pool.fetchval("SELECT 1")
        status["services"]["postgres"] = value == 1
    except Exception:
        status["services"]["postgres"] = False

    try:
        redis_client = await get_redis_client()
        pong = await redis_client.get_client().ping()
        status["services"]["redis"] = bool(pong)
    except Exception:
        status["services"]["redis"] = False

    status["ok"] = all(status["services"].values())
    _audit_privileged_action("gateway.deep_health", user_id, {"services": status["services"]})
    return status


@app.get("/metrics")
async def prometheus_metrics(user_id: str = Depends(get_current_user)) -> Any:
    _audit_privileged_action("gateway.metrics", user_id)
    registry = CollectorRegistry()
    payload = generate_latest(registry)
    return Response(payload, media_type=CONTENT_TYPE_LATEST)


@app.websocket("/health/ws")
async def health_ws(ws: WebSocket, token: str = Query(...)) -> None:
    """WebSocket for real-time health alerts. Requires JWT in query param."""
    client_host = _client_host(ws.client)
    if not verify_token(token):
        try:
            _enforce_rate_limit(f"invalid_token:{client_host}")
        except HTTPException:
            _audit_privileged_action(
                "gateway.health_ws.rate_limited",
                None,
                {"client_host": client_host},
            )
            await ws.close(code=4008, reason="Rate limit exceeded")
            return

        _audit_privileged_action(
            "gateway.health_ws.invalid_token",
            None,
            {"client_host": client_host},
        )
        await ws.close(code=4001, reason="Invalid token")
        return

    await ws.accept()
    try:
        while True:
            await ws.send_json({"type": "health", "ok": True, "timestamp": datetime.now(UTC).isoformat()})
            await ws.receive_text()
    except WebSocketDisconnect:
        logger.info("Health websocket disconnected")


@app.post("/auth/token", response_model=TokenResponse)
async def issue_token(request: Request) -> TokenResponse:
    client_host = _client_host(request.client)
    if settings.is_production:
        _audit_privileged_action(
            "gateway.issue_token.blocked_production",
            None,
            {"client_host": client_host},
        )
        raise HTTPException(status_code=403, detail="Demo token issuance is disabled in production")

    try:
        _enforce_rate_limit(f"issue_token:{client_host}")
    except HTTPException:
        _audit_privileged_action(
            "gateway.issue_token.rate_limited",
            None,
            {"client_host": client_host},
        )
        raise

    _audit_privileged_action("gateway.issue_token", None, {"client_host": client_host})

    token = create_access_token({"sub": "demo-user"})
    return TokenResponse(access_token=token, token_type="bearer")


@app.websocket("/agent/stream/{session_id}")
async def agent_stream(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """WebSocket endpoint for streaming agent events. Requires JWT in query param."""
    client_host = _client_host(websocket.client)
    if not verify_token(token):
        try:
            _enforce_rate_limit(f"invalid_token:{client_host}")
        except HTTPException:
            _audit_privileged_action(
                "gateway.agent_stream.rate_limited",
                None,
                {"client_host": client_host, "session_id": session_id},
            )
            await websocket.close(code=4008, reason="Rate limit exceeded")
            return

        _audit_privileged_action(
            "gateway.agent_stream.invalid_token",
            None,
            {"client_host": client_host, "session_id": session_id},
        )
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


@app.get("/memory/semantic")
async def get_semantic_memory(
    user_id: str = Depends(get_current_user),
) -> list[dict[str, Any]]:
    _audit_privileged_action("gateway.memory.semantic", user_id)
    return []


@app.get("/memory/procedural")
async def get_procedural_skills(user_id: str = Depends(get_current_user)) -> list[dict[str, Any]]:
    _audit_privileged_action("gateway.memory.procedural", user_id)
    return []


@app.get("/admin/fleet")
async def get_fleet_summary(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    _audit_privileged_action("gateway.admin.fleet", user_id)
    return {"ok": True, "user_id": user_id}


@app.get("/admin/costs")
async def get_cost_summary(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    _audit_privileged_action("gateway.admin.costs", user_id)
    return {"ok": True, "user_id": user_id}


@app.get("/admin/audit-logs")
async def get_audit_logs(
    user_id: str = Depends(get_current_user),
    action: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    _audit_privileged_action(
        "gateway.admin.audit_logs",
        user_id,
        {"action": action, "limit": limit, "offset": offset},
    )
    return {"items": [], "action": action, "limit": limit, "offset": offset, "user_id": user_id}


@app.get("/memory/export")
async def export_memory(
    user_id: str = Depends(get_current_user),
    format: str = Query("json", pattern="^(json|markdown)$"),
    memory_type: str | None = Query(None, pattern="^(semantic|episodic|all)$"),
) -> dict[str, Any]:
    _audit_privileged_action(
        "gateway.memory.export",
        user_id,
        {"format": format, "memory_type": memory_type},
    )
    return {"format": format, "memory_type": memory_type, "user_id": user_id}


@app.post("/memory/import")
async def import_memory(
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    _audit_privileged_action("gateway.memory.import", user_id)
    return {"ok": True, "user_id": user_id}
