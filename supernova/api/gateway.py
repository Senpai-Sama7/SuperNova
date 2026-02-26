"""FastAPI gateway for SuperNova — main application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import litellm
from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from supernova.api.auth import create_access_token, get_current_user, verify_token
from supernova.api.routes.agent import router as agent_router
from supernova.api.routes.dashboard import router as dashboard_router
from supernova.api.routes.mcp_routes import (
    router as mcp_router,
    set_mcp_client,
    set_skill_loader,
)
from supernova.api.websockets import WebSocketBroadcaster, handle_agent_stream
from supernova.config import get_settings
from supernova.core.memory import EpisodicMemoryStore, SemanticMemoryStore, get_working_memory_store
from supernova.core.memory.procedural import ProceduralMemoryStore
from supernova.core.reasoning.dynamic_router import DynamicModelRouter
from supernova.infrastructure.llm.cost_controller import CostController
from supernova.infrastructure.storage import (
    close_postgres_pool,
    close_redis_client,
    get_postgres_pool,
    get_redis_client,
)
from supernova.infrastructure.tools.builtin import (
    create_code_exec_tool,
    create_file_read_tool,
    create_file_write_tool,
    create_web_search_tool,
)
from supernova.infrastructure.tools.registry import Capability, ToolRegistry
from supernova.mcp.client.mcp_client import MCPClient
from supernova.mcp.tools.mcp_tool_bridge import bridge_mcp_tools
from supernova.skills.loader import SkillLoader

logger = logging.getLogger(__name__)

# Shared state populated during lifespan
_state: dict[str, Any] = {}


class _LiteLLMClientAdapter:
    """Minimal adapter that satisfies DynamicModelRouter's LiteLLM interface."""

    async def acompletion(self, **kwargs: Any) -> Any:
        return await litellm.acompletion(**kwargs)


async def _initialize_runtime_state() -> None:
    """Best-effort runtime component initialization for graph execution."""
    settings = get_settings()
    _state["settings"] = settings

    # Core storage clients
    pool = None
    redis_client = None
    try:
        pool = await get_postgres_pool()
        _state["pool"] = pool
    except Exception as exc:
        logger.warning("Postgres pool unavailable during startup: %s", exc)

    try:
        redis_client = await get_redis_client()
        _state["redis"] = redis_client
    except Exception as exc:
        logger.warning("Redis client unavailable during startup: %s", exc)

    # Memory stores
    if pool:
        try:
            semantic_store = SemanticMemoryStore(pool=pool, redis=redis_client)
            _state["semantic_store"] = semantic_store
        except Exception as exc:
            logger.warning("Semantic store initialization failed: %s", exc)

        try:
            async def _embedder(text: str) -> list[float]:
                semantic = _state.get("semantic_store")
                if semantic is None:
                    return []
                return await semantic.embed(text)

            procedural_store = ProceduralMemoryStore(
                pool=pool.get_pool(),
                embedder=_embedder,
                hmac_key=settings.security.pickle_hmac_key,
            )
            await procedural_store.initialize_schema()
            _state["procedural_store"] = procedural_store
        except Exception as exc:
            logger.warning("Procedural store initialization failed: %s", exc)

    try:
        _state["working_memory_store"] = await get_working_memory_store()
    except Exception as exc:
        logger.warning("Working memory store initialization failed: %s", exc)

    try:
        episodic_store = EpisodicMemoryStore(
            neo4j_uri=settings.neo4j.uri,
            neo4j_password=settings.neo4j.password,
            neo4j_user=settings.neo4j.user,
        )
        _state["episodic_store"] = episodic_store
    except Exception as exc:
        logger.warning("Episodic store initialization failed: %s", exc)

    # Tool registry and built-ins
    all_caps = (
        Capability.READ_FILES
        | Capability.WRITE_FILES
        | Capability.EXECUTE_CODE
        | Capability.WEB_SEARCH
        | Capability.WEB_BROWSE
        | Capability.SEND_EMAIL
        | Capability.SHELL_ACCESS
        | Capability.EXTERNAL_API
    )
    registry = ToolRegistry(granted_capabilities=all_caps, pool=pool)
    for factory in (
        create_file_read_tool,
        create_file_write_tool,
        create_code_exec_tool,
        create_web_search_tool,
    ):
        try:
            registry.register(factory())
        except Exception as exc:
            logger.warning("Built-in tool registration failed for %s: %s", factory.__name__, exc)
    _state["tool_registry"] = registry

    # MCP client + bridged tools
    mcp_client = MCPClient()
    try:
        configs = mcp_client.load_config(settings.mcp.config_path)
        for cfg in configs:
            await mcp_client.start_server(cfg)
        bridged = bridge_mcp_tools(mcp_client, await mcp_client.list_tools())
        for tool in bridged:
            registry.register(tool)
        _state["mcp_client"] = mcp_client
        set_mcp_client(mcp_client)
    except Exception as exc:
        logger.warning("MCP initialization failed: %s", exc)
        await mcp_client.stop()

    # Skills loader
    try:
        skill_loader = SkillLoader(settings.paths.skills_dir)
        skill_loader.discover()
        _state["skill_loader"] = skill_loader
        set_skill_loader(skill_loader)
    except Exception as exc:
        logger.warning("Skill loader initialization failed: %s", exc)

    # Router + cost controller
    try:
        cost_controller = None
        if redis_client is not None:
            cost_controller = CostController.from_settings(redis_client.get_client())
            _state["cost_controller"] = cost_controller

        model_router = DynamicModelRouter(
            litellm_router=_LiteLLMClientAdapter(),
            cost_controller=cost_controller,
        )
        await model_router.start()
        _state["model_router"] = model_router
    except Exception as exc:
        logger.warning("Model router initialization failed: %s", exc)

    # Compile cognitive loop graph only when hard dependencies are available
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from loop import build_agent_graph
        from supernova.core.agent.interrupts import InterruptCoordinator

        if pool and _state.get("episodic_store") and _state.get("semantic_store") and _state.get("procedural_store"):
            dsn = settings.database_url.replace("postgresql+asyncpg", "postgresql")
            checkpointer_cm = AsyncPostgresSaver.from_conn_string(dsn)
            checkpointer = await checkpointer_cm.__aenter__()
            await checkpointer.setup()

            coordinator = InterruptCoordinator(websocket_broadcaster=_state.get("broadcaster"))
            _state["interrupt_coordinator"] = coordinator
            mount_interrupt_router(coordinator)

            graph = build_agent_graph(
                checkpointer=checkpointer,
                episodic_store=_state["episodic_store"],
                semantic_store=_state["semantic_store"],
                procedural_store=_state["procedural_store"],
                working_memory_store=_state["working_memory_store"],
                tool_registry=registry,
                interrupt_coordinator=coordinator,
                llm_router=_state["model_router"],
                agent_identity="SuperNova",
                enable_hitl=settings.features.hitl_interrupts,
            )
            _state["agent_graph"] = graph
            _state["checkpointer_cm"] = checkpointer_cm
    except Exception as exc:
        logger.warning("Agent graph initialization skipped: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down shared resources."""
    logger.info("SuperNova gateway starting up")
    _state["broadcaster"] = WebSocketBroadcaster()
    await _initialize_runtime_state()
    yield

    # Stop background services before tearing down clients.
    model_router = _state.get("model_router")
    if model_router:
        try:
            await model_router.stop()
        except Exception as exc:
            logger.warning("Failed stopping model router: %s", exc)

    mcp_client = _state.get("mcp_client")
    if mcp_client:
        try:
            await mcp_client.stop()
        except Exception as exc:
            logger.warning("Failed stopping MCP client: %s", exc)

    checkpointer_cm = _state.get("checkpointer_cm")
    if checkpointer_cm is not None:
        try:
            await checkpointer_cm.__aexit__(None, None, None)
        except Exception as exc:
            logger.warning("Failed closing checkpointer context: %s", exc)

    await close_postgres_pool()
    await close_redis_client()
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


@app.get("/admin/audit-logs")
async def get_audit_logs(
    user_id: str = Depends(get_current_user),
    action: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Return paginated audit log entries."""
    from supernova.infrastructure.security.audit import query_audit_logs
    pool = _state.get("db_pool")
    if not pool:
        return {"entries": [], "note": "Database not initialized"}
    entries = await query_audit_logs(pool, user_id=user_id, action=action, limit=limit, offset=offset)
    return {"entries": entries, "total_returned": len(entries)}


# ── Memory Export/Import ──────────────────────────────────────────────────────

@app.get("/memory/export")
async def export_memories(
    user_id: str = Depends(get_current_user),
    format: str = Query("json", pattern="^(json|markdown)$"),
    memory_type: str | None = Query(None, pattern="^(semantic|episodic|all)$"),
    category: str | None = None,
    since: str | None = None,
) -> Any:
    """Export user memories as JSON or Markdown."""
    from fastapi.responses import PlainTextResponse

    store = _state.get("semantic_store")
    memories = []
    if store:
        if category:
            memories = await store.get_by_category(user_id, category)
        else:
            memories = await store.search("", user_id)

    # Filter by date if provided
    if since:
        memories = [m for m in memories if m.get("created_at", "") >= since]

    if format == "markdown":
        lines = ["# SuperNova Memory Export\n"]
        for m in memories:
            lines.append(f"## {m.get('title', m.get('id', 'Memory'))}\n")
            lines.append(f"{m.get('content', '')}\n")
            if m.get("category"):
                lines.append(f"*Category: {m['category']}*\n")
            lines.append("---\n")
        return PlainTextResponse("\n".join(lines), media_type="text/markdown")

    return {"user_id": user_id, "count": len(memories), "memories": memories}


@app.post("/memory/import")
async def import_memories(
    user_id: str = Depends(get_current_user),
    body: dict[str, Any] = ...,
) -> dict[str, Any]:
    """Import memories from JSON payload."""
    store = _state.get("semantic_store")
    if not store:
        return {"imported": 0, "error": "Semantic store not initialized"}

    memories = body.get("memories", [])
    imported = 0
    for m in memories:
        content = m.get("content", "")
        if not content:
            continue
        await store.upsert(
            content=content,
            user_id=user_id,
            metadata=m.get("metadata", {}),
        )
        imported += 1

    return {"imported": imported, "total_submitted": len(memories)}


# ── HITL interrupt router ─────────────────────────────────────────────────────

def mount_interrupt_router(coordinator: Any) -> None:
    """Mount the HITL interrupt router at /hitl."""
    from supernova.core.agent.interrupts import create_interrupt_router

    router = create_interrupt_router(coordinator)
    app.include_router(router, prefix="/hitl")
    logger.info("HITL interrupt router mounted at /hitl")
