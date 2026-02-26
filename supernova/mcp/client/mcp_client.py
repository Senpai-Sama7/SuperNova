"""MCP client for managing external MCP server connections."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _import_mcp():
    """Import the external mcp package, bypassing local supernova.mcp shadow."""
    # Temporarily remove our local mcp from sys.modules if it shadows
    saved = {}
    to_remove = [k for k in sys.modules if k == "mcp" or k.startswith("mcp.")]
    # Check if the loaded 'mcp' is our local one (has no ClientSession)
    mcp_mod = sys.modules.get("mcp")
    if mcp_mod and not hasattr(mcp_mod, "ClientSession"):
        for k in to_remove:
            saved[k] = sys.modules.pop(k)
    import mcp as _mcp
    from mcp.client.stdio import stdio_client as _stdio_client
    # Restore saved modules
    for k, v in saved.items():
        sys.modules.setdefault(k, v)
    return _mcp.ClientSession, _mcp.StdioServerParameters, _stdio_client


@dataclass
class ServerConfig:
    """Configuration for a single MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None
    enabled: bool = True


@dataclass
class ServerConnection:
    """Active connection to an MCP server."""
    config: ServerConfig
    session: Any  # ClientSession
    healthy: bool = True


class MCPClient:
    """Manages MCP server connections via stdio transport."""

    def __init__(self) -> None:
        self._connections: dict[str, ServerConnection] = {}
        self._exit_stack = AsyncExitStack()

    async def start_server(self, config: ServerConfig) -> bool:
        """Start and connect to an MCP server. Returns True on success."""
        if not config.enabled:
            return False
        try:
            ClientSession, StdioServerParameters, stdio_client = _import_mcp()
            params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env,
            )
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(params)
            )
            read_stream, write_stream = stdio_transport
            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            self._connections[config.name] = ServerConnection(config=config, session=session)
            logger.info("MCP server started: %s", config.name)
            return True
        except Exception as e:
            logger.error("Failed to start MCP server %s: %s", config.name, e)
            return False

    async def stop(self) -> None:
        """Stop all MCP server connections."""
        try:
            await self._exit_stack.aclose()
        except Exception as e:
            logger.warning("Error closing MCP connections: %s", e)
        self._connections.clear()

    def load_config(self, config_path: str | Path) -> list[ServerConfig]:
        """Load MCP server configs from a Claude-format JSON file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning("MCP config not found: %s", path)
            return []
        try:
            data = json.loads(path.read_text())
            servers = data.get("mcpServers", {})
            return [
                ServerConfig(
                    name=name,
                    command=cfg["command"],
                    args=cfg.get("args", []),
                    env=cfg.get("env"),
                    cwd=cfg.get("cwd"),
                    enabled=not cfg.get("disabled", False),
                )
                for name, cfg in servers.items()
            ]
        except Exception as e:
            logger.error("Failed to load MCP config: %s", e)
            return []

    async def list_tools(self) -> list[dict[str, Any]]:
        """Aggregate tools from all connected MCP servers in OpenAI format."""
        tools: list[dict[str, Any]] = []
        for name, conn in self._connections.items():
            if not conn.healthy:
                continue
            try:
                result = await conn.session.list_tools()
                for t in result.tools:
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": f"{name}__{t.name}",
                            "description": t.description or "",
                            "parameters": t.inputSchema,
                        },
                        "_mcp_server": name,
                    })
            except Exception as e:
                logger.warning("Failed to list tools from %s: %s", name, e)
                conn.healthy = False
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None,
        *, timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Call a tool on a specific MCP server."""
        conn = self._connections.get(server_name)
        if not conn:
            raise KeyError(f"MCP server not connected: {server_name}")
        if not conn.healthy:
            raise RuntimeError(f"MCP server unhealthy: {server_name}")

        result = await asyncio.wait_for(
            conn.session.call_tool(tool_name, arguments),
            timeout=timeout,
        )
        content_text = ""
        for c in result.content:
            if hasattr(c, "text"):
                content_text += c.text
        return {"content": content_text, "is_error": result.isError}

    async def health_check(self) -> dict[str, bool]:
        """Ping all servers and update health status."""
        results: dict[str, bool] = {}
        for name, conn in self._connections.items():
            try:
                await asyncio.wait_for(conn.session.send_ping(), timeout=5.0)
                conn.healthy = True
                results[name] = True
            except Exception:
                conn.healthy = False
                results[name] = False
        return results

    def get_server_status(self) -> list[dict[str, Any]]:
        """Return status of all connected servers."""
        return [
            {"name": name, "healthy": conn.healthy, "command": conn.config.command}
            for name, conn in self._connections.items()
        ]
