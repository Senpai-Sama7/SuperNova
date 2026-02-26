"""FastAPI gateway for SuperNova — main application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from supernova.api.auth import create_access_token, get_current_user, verify_token
from supernova.api.routes.agent import router as agent_router
from supernova.api.routes.dashboard import router as dashboard_router
from supernova.api.routes.mcp_routes import router as mcp_router
from supernova.api.websockets import WebSocketBroadcaster, handle_agent_stream

logger = logging.getLogger(__name__)

# Shared state populated during lifespan
_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down shared resources."""
    logger.info("SuperNova gateway starting up")
    _state["broadcaster"] = WebSocketBroadcaster()
    # These will be initialized when infrastructure is available:
    # _state["pool"] = await get_postgres_pool()
    # _state["redis"] = await get_redis_client()
    # _state["agent_graph"] = compiled_graph
    yield
    logger.info("SuperNova gateway shutting down")
    _state.clear()


app = FastAPI(
    title="SuperNova API",
    version="2.0.0",
    description="AI agent platform with persistent memory and autonomous cognition.",
    lifespan=lifespan,
)

# CORS middleware
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP and Skills routes
app.include_router(mcp_router)
app.include_router(dashboard_router)
app.include_router(agent_router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    user_id: str


class TokenResponse(BaseModel):
    access_token: str


@app.post("/auth/token", response_model=TokenResponse)
async def issue_token(body: TokenRequest) -> TokenResponse:
    token = create_access_token(body.user_id)
    return TokenResponse(access_token=token)


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/agent/stream/{session_id}")
async def agent_stream(websocket: WebSocket, session_id: str, token: str = Query(...)):
    """WebSocket endpoint for streaming agent events. Requires JWT in query param."""
    try:
        user_id = verify_token(token)  # noqa: F841
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    broadcaster = _state.get("broadcaster")
    agent_graph = _state.get("agent_graph")

    if not agent_graph:
        await websocket.send_json({"type": "error", "message": "Agent graph not initialized"})
        await websocket.close()
        return

    try:
        data = await websocket.receive_json()
        await handle_agent_stream(websocket, session_id, broadcaster, agent_graph, data)
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", session_id)
    finally:
        if broadcaster:
            broadcaster.unregister(session_id)


# ── Memory endpoints ──────────────────────────────────────────────────────────

@app.get("/memory/semantic")
async def get_semantic_memories(
    user_id: str = Depends(get_current_user),
    category: str | None = None,
) -> list[dict[str, Any]]:
    """Return user's semantic memories."""
    store = _state.get("semantic_store")
    if not store:
        return []
    if category:
        return await store.get_by_category(user_id, category)
    return await store.search("", user_id)


@app.get("/memory/procedural")
async def get_procedural_skills() -> list[dict[str, Any]]:
    """Return list of compiled procedural skills."""
    proc_store = _state.get("procedural_store")
    if not proc_store:
        return []
    return await proc_store.list_skills()


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.get("/admin/fleet")
async def get_fleet_summary() -> dict[str, Any]:
    """Return model fleet summary from DynamicModelRouter."""
    router = _state.get("model_router")
    if not router:
        return {"models": [], "note": "Router not initialized"}
    return router.get_fleet_summary()


@app.get("/admin/costs")
async def get_cost_summary() -> dict[str, Any]:
    """Return current spend, limits, and projections."""
    cc = _state.get("cost_controller")
    if not cc:
        return {"tracking_enabled": False, "note": "Cost controller not initialized"}
    return await cc.get_spend_summary()


# ── HITL interrupt router ─────────────────────────────────────────────────────

def mount_interrupt_router(coordinator: Any) -> None:
    """Mount the HITL interrupt router at /hitl."""
    import importlib.util
    # Import from root-level interrupts.py spec
    spec_path = os.path.join(os.path.dirname(__file__), "..", "..", "interrupts.py")
    if os.path.exists(spec_path):
        spec = importlib.util.spec_from_file_location("interrupts", spec_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        router = mod.create_interrupt_router(coordinator)
        app.include_router(router, prefix="/hitl")
        logger.info("HITL interrupt router mounted at /hitl")
