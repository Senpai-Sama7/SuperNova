"""MCP and Skills API endpoints for SuperNova."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from supernova.api.auth import get_current_user

router = APIRouter(
    prefix="/mcp",
    tags=["mcp"],
    dependencies=[Depends(get_current_user)],
)
