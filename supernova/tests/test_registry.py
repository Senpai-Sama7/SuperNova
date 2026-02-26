"""Tests for ToolRegistry."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from supernova.infrastructure.tools.registry import Capability, Tool, ToolRegistry


async def dummy_tool(**kwargs):
    return {"result": "ok"}


async def slow_tool(**kwargs):
    await asyncio.sleep(10)
    return {"result": "slow"}


def make_tool(
    name: str = "test_tool",
    caps: Capability = Capability.READ_FILES,
    fn=None,
) -> Tool:
    return Tool(
        name=name,
        description=f"A {name}",
        required_capabilities=caps,
        parameters={"type": "object", "properties": {"q": {"type": "string"}}},
        fn=fn or dummy_tool,
    )


class TestCapability:
    """5.5.1: Capability Flag enum."""

    def test_all_flags_defined(self):
        expected = {
            "READ_FILES", "WRITE_FILES", "EXECUTE_CODE", "WEB_SEARCH",
            "WEB_BROWSE", "SEND_EMAIL", "SHELL_ACCESS", "EXTERNAL_API",
        }
        actual = {c.name for c in Capability}
        assert actual == expected

    def test_flags_combinable(self):
        combined = Capability.READ_FILES | Capability.WEB_SEARCH
        assert Capability.READ_FILES in combined
        assert Capability.WRITE_FILES not in combined


class TestToolRegistryInit:
    """5.5.2: ToolRegistry initialized with granted_capabilities."""

    def test_constructor(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        assert reg._granted == Capability.READ_FILES


class TestRegister:
    """5.5.3: register() validates capabilities."""

    def test_register_permitted_tool(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES | Capability.WEB_SEARCH)
        tool = make_tool(caps=Capability.READ_FILES)
        reg.register(tool)
        assert reg.get_tool("test_tool") is tool

    def test_register_rejects_unpermitted_tool(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        tool = make_tool(caps=Capability.SHELL_ACCESS)
        with pytest.raises(PermissionError, match="not granted"):
            reg.register(tool)


class TestExecute:
    """5.5.4: execute() with runtime check, timeout, logging."""

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        reg.register(make_tool())
        result = await reg.execute("test_tool", {"q": "hello"})
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_execute_raises_on_unknown_tool(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        with pytest.raises(KeyError, match="not registered"):
            await reg.execute("nonexistent", {})

    @pytest.mark.asyncio
    async def test_execute_runtime_capability_check(self):
        # Register with full caps, then reduce granted caps
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES | Capability.SHELL_ACCESS)
        tool = make_tool(caps=Capability.SHELL_ACCESS)
        reg.register(tool)
        # Simulate capability revocation
        reg._granted = Capability.READ_FILES
        with pytest.raises(PermissionError):
            await reg.execute("test_tool", {})

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        reg.register(make_tool(fn=slow_tool))
        with pytest.raises(asyncio.TimeoutError):
            await reg.execute("test_tool", {}, timeout=0.1)

    @pytest.mark.asyncio
    async def test_execute_logs_to_audit(self):
        mock_pool = MagicMock()
        mock_pool.execute = AsyncMock()
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES, pool=mock_pool)
        reg.register(make_tool())
        await reg.execute("test_tool", {"q": "hi"})
        mock_pool.execute.assert_called_once()
        sql = mock_pool.execute.call_args[0][0]
        assert "audit_log" in sql


class TestGetToolSchemas:
    """5.5.5: get_tool_schemas() returns OpenAI-format schemas."""

    def test_returns_openai_format(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        reg.register(make_tool(name="reader"))
        schemas = reg.get_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["type"] == "function"
        assert schemas[0]["function"]["name"] == "reader"
        assert "parameters" in schemas[0]["function"]

    def test_only_registered_tools(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        assert reg.get_tool_schemas() == []


class TestGetTool:
    """5.5.6: get_tool() returns Tool | None."""

    def test_returns_tool(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        tool = make_tool()
        reg.register(tool)
        assert reg.get_tool("test_tool") is tool

    def test_returns_none_for_missing(self):
        reg = ToolRegistry(granted_capabilities=Capability.READ_FILES)
        assert reg.get_tool("nope") is None
