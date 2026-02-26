"""MCP and Skills API endpoints for SuperNova."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from supernova.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp"])

# These are populated by the gateway lifespan
_mcp_client: Any = None
_skill_loader: Any = None


def set_mcp_client(client: Any) -> None:
    global _mcp_client
    _mcp_client = client


def set_skill_loader(loader: Any) -> None:
    global _skill_loader
    _skill_loader = loader


# ── MCP Server endpoints ─────────────────────────────────────────────────────

@router.get("/mcp/servers")
async def list_mcp_servers() -> list[dict[str, Any]]:
    """Return list of configured MCP servers with health status."""
    if not _mcp_client:
        return []
    return _mcp_client.get_server_status()


@router.get("/mcp/tools")
async def list_mcp_tools() -> list[dict[str, Any]]:
    """Return aggregated tools from all healthy MCP servers."""
    if not _mcp_client:
        return []
    return await _mcp_client.list_tools()


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = {}


@router.post("/mcp/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    body: ToolCallRequest,
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    """Execute an MCP tool with provided arguments."""
    if not _mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")

    # Parse "server__tool" format
    parts = tool_name.split("__", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Tool name must be in 'server__tool' format")

    server_name, actual_tool = parts
    try:
        return await _mcp_client.call_tool(server_name, actual_tool, body.arguments)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Skills endpoints ──────────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills() -> list[dict[str, Any]]:
    """Return list of available skills."""
    if not _skill_loader:
        return []
    return _skill_loader.list_skills()


@router.post("/skills/{skill_name}/activate")
async def activate_skill(
    skill_name: str,
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    """Activate a skill for the current session."""
    if not _skill_loader:
        raise HTTPException(status_code=503, detail="Skill loader not initialized")
    if _skill_loader.activate(skill_name):
        return {"status": "activated", "skill": skill_name}
    raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")


@router.post("/skills/{skill_name}/deactivate")
async def deactivate_skill(
    skill_name: str,
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    """Deactivate a skill."""
    if not _skill_loader:
        raise HTTPException(status_code=503, detail="Skill loader not initialized")
    _skill_loader.deactivate(skill_name)
    return {"status": "deactivated", "skill": skill_name}
