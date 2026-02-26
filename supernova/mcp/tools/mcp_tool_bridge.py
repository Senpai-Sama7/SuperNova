"""Bridge MCP tools to SuperNova's ToolRegistry."""

from __future__ import annotations

import logging
from typing import Any

from supernova.infrastructure.tools.registry import Capability, Tool
from supernova.mcp.client.mcp_client import MCPClient

logger = logging.getLogger(__name__)


def bridge_mcp_tools(
    mcp_client: MCPClient,
    mcp_tools: list[dict[str, Any]],
    capability: Capability = Capability.EXTERNAL_API,
) -> list[Tool]:
    """Convert MCP tools to SuperNova Tool dataclasses for ToolRegistry."""
    tools: list[Tool] = []
    for mcp_tool in mcp_tools:
        func_def = mcp_tool.get("function", {})
        full_name = func_def.get("name", "")
        server_name = mcp_tool.get("_mcp_server", "")

        # Parse "server__tool_name" format
        parts = full_name.split("__", 1)
        if len(parts) == 2:
            srv, tool_name = parts
        else:
            srv, tool_name = server_name, full_name

        async def _call(
            _srv=srv, _tool=tool_name, **kwargs: Any,
        ) -> dict[str, Any]:
            return await mcp_client.call_tool(_srv, _tool, kwargs)

        tools.append(Tool(
            name=full_name,
            description=func_def.get("description", ""),
            required_capabilities=capability,
            parameters=func_def.get("parameters", {}),
            fn=_call,
            is_safe_parallel=True,
        ))
    return tools
