"""Tests for MCP Client Infrastructure (Task 5.7)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from supernova.mcp.client.mcp_client import MCPClient, ServerConfig, ServerConnection


class TestServerConfig:
    def test_defaults(self):
        cfg = ServerConfig(name="test", command="node")
        assert cfg.args == []
        assert cfg.env is None
        assert cfg.enabled is True


class TestMCPClient:
    def test_init(self):
        client = MCPClient()
        assert client._connections == {}

    def test_load_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "mcpServers": {
                "server1": {"command": "node", "args": ["index.js"]},
                "server2": {"command": "python", "disabled": True},
            }
        }))
        client = MCPClient()
        configs = client.load_config(config_file)
        assert len(configs) == 2
        assert configs[0].name == "server1"
        assert configs[0].command == "node"
        assert configs[0].args == ["index.js"]
        assert configs[0].enabled is True
        assert configs[1].name == "server2"
        assert configs[1].enabled is False

    def test_load_config_missing_file(self, tmp_path):
        client = MCPClient()
        configs = client.load_config(tmp_path / "nonexistent.json")
        assert configs == []

    def test_load_config_invalid_json(self, tmp_path):
        config_file = tmp_path / "bad.json"
        config_file.write_text("not json")
        client = MCPClient()
        configs = client.load_config(config_file)
        assert configs == []

    def test_get_server_status_empty(self):
        client = MCPClient()
        assert client.get_server_status() == []

    def test_get_server_status_with_connections(self):
        client = MCPClient()
        cfg = ServerConfig(name="test", command="node")
        client._connections["test"] = ServerConnection(
            config=cfg, session=MagicMock(), healthy=True
        )
        status = client.get_server_status()
        assert len(status) == 1
        assert status[0]["name"] == "test"
        assert status[0]["healthy"] is True

    @pytest.mark.asyncio
    async def test_list_tools_empty(self):
        client = MCPClient()
        tools = await client.list_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_from_server(self):
        client = MCPClient()
        mock_session = AsyncMock()
        mock_tool = MagicMock()
        mock_tool.name = "search"
        mock_tool.description = "Search things"
        mock_tool.inputSchema = {"type": "object", "properties": {"q": {"type": "string"}}}
        mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

        cfg = ServerConfig(name="srv", command="node")
        client._connections["srv"] = ServerConnection(config=cfg, session=mock_session)

        tools = await client.list_tools()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "srv__search"
        assert tools[0]["_mcp_server"] == "srv"

    @pytest.mark.asyncio
    async def test_list_tools_skips_unhealthy(self):
        client = MCPClient()
        cfg = ServerConfig(name="bad", command="node")
        client._connections["bad"] = ServerConnection(
            config=cfg, session=AsyncMock(), healthy=False
        )
        tools = await client.list_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        client = MCPClient()
        mock_session = AsyncMock()
        mock_content = MagicMock()
        mock_content.text = "result text"
        mock_session.call_tool.return_value = MagicMock(
            content=[mock_content], isError=False
        )
        cfg = ServerConfig(name="srv", command="node")
        client._connections["srv"] = ServerConnection(config=cfg, session=mock_session)

        result = await client.call_tool("srv", "search", {"q": "test"})
        assert result["content"] == "result text"
        assert result["is_error"] is False

    @pytest.mark.asyncio
    async def test_call_tool_unknown_server(self):
        client = MCPClient()
        with pytest.raises(KeyError, match="not connected"):
            await client.call_tool("missing", "tool")

    @pytest.mark.asyncio
    async def test_call_tool_unhealthy_server(self):
        client = MCPClient()
        cfg = ServerConfig(name="bad", command="node")
        client._connections["bad"] = ServerConnection(
            config=cfg, session=AsyncMock(), healthy=False
        )
        with pytest.raises(RuntimeError, match="unhealthy"):
            await client.call_tool("bad", "tool")

    @pytest.mark.asyncio
    async def test_health_check(self):
        client = MCPClient()
        mock_session_ok = AsyncMock()
        mock_session_ok.send_ping.return_value = MagicMock()
        mock_session_bad = AsyncMock()
        mock_session_bad.send_ping.side_effect = Exception("timeout")

        cfg1 = ServerConfig(name="ok", command="node")
        cfg2 = ServerConfig(name="bad", command="node")
        client._connections["ok"] = ServerConnection(config=cfg1, session=mock_session_ok)
        client._connections["bad"] = ServerConnection(config=cfg2, session=mock_session_bad)

        results = await client.health_check()
        assert results["ok"] is True
        assert results["bad"] is False
        assert client._connections["ok"].healthy is True
        assert client._connections["bad"].healthy is False

    @pytest.mark.asyncio
    async def test_call_tool_timeout(self):
        """8.6.4: Tool exceeding timeout returns error, doesn't hang."""
        client = MCPClient()
        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = TimeoutError()
        cfg = ServerConfig(name="slow", command="node")
        client._connections["slow"] = ServerConnection(config=cfg, session=mock_session)

        with pytest.raises(asyncio.TimeoutError):
            await client.call_tool("slow", "heavy_tool", {"x": 1})

    @pytest.mark.asyncio
    async def test_start_server_disabled(self):
        client = MCPClient()
        cfg = ServerConfig(name="disabled", command="node", enabled=False)
        result = await client.start_server(cfg)
        assert result is False


class TestMCPToolBridge:
    def test_bridge_creates_tools(self):
        from supernova.infrastructure.tools.registry import Capability
        from supernova.mcp.tools.mcp_tool_bridge import bridge_mcp_tools

        mock_client = MagicMock()
        mcp_tools = [{
            "type": "function",
            "function": {
                "name": "srv__search",
                "description": "Search",
                "parameters": {"type": "object"},
            },
            "_mcp_server": "srv",
        }]
        tools = bridge_mcp_tools(mock_client, mcp_tools)
        assert len(tools) == 1
        assert tools[0].name == "srv__search"
        assert tools[0].required_capabilities == Capability.EXTERNAL_API

    @pytest.mark.asyncio
    async def test_bridge_tool_calls_mcp_client(self):
        from supernova.mcp.tools.mcp_tool_bridge import bridge_mcp_tools

        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value={"content": "ok", "is_error": False})
        mcp_tools = [{
            "type": "function",
            "function": {"name": "srv__search", "description": "", "parameters": {}},
            "_mcp_server": "srv",
        }]
        tools = bridge_mcp_tools(mock_client, mcp_tools)
        await tools[0].fn(q="test")
        mock_client.call_tool.assert_called_once_with("srv", "search", {"q": "test"})
