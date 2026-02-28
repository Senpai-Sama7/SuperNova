"""Tests for tool registry with capability gating and tool enable/disable."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from supernova.infrastructure.tools.registry import (
    Capability,
    Tool,
    ToolRegistry,
    TOOL_RISK_LEVELS,
)


class MockTool:
    """Mock async tool function for testing."""

    async def __call__(self, **kwargs):
        return {"result": "success", "args": kwargs}


@pytest.fixture
def mock_tool():
    """Return a mock async tool function."""
    return MockTool()


@pytest.fixture
def registry(mock_tool):
    """Create a registry with limited capabilities."""
    return ToolRegistry(
        granted_capabilities=Capability.READ_FILES | Capability.WEB_SEARCH,
        enabled_tools=[],
    )


class TestCapabilityGating:
    """Test capability-based tool access control."""

    def test_register_allowed_tool(self, registry, mock_tool):
        """Test registering a tool with granted capability."""
        tool = Tool(
            name="web_search",
            description="Search the web",
            required_capabilities=Capability.WEB_SEARCH,
            parameters={"type": "object", "properties": {}},
            fn=mock_tool,
        )
        registry.register(tool)
        assert registry.get_tool("web_search") is not None

    def test_register_denied_tool(self, registry, mock_tool):
        """Test registering a tool without granted capability raises."""
        tool = Tool(
            name="shell_access",
            description="Run shell commands",
            required_capabilities=Capability.SHELL_ACCESS,
            parameters={"type": "object", "properties": {}},
            fn=mock_tool,
        )
        with pytest.raises(PermissionError, match="requires capabilities not granted"):
            registry.register(tool)


class TestToolExecution:
    """Test tool execution with capability checks."""

    @pytest.fixture
    def registry_with_tools(self, mock_tool):
        """Create a registry with some tools registered."""
        registry = ToolRegistry(
            granted_capabilities=Capability.READ_FILES | Capability.WEB_SEARCH,
            enabled_tools=[],
        )
        registry.register(
            Tool(
                name="web_search",
                description="Search the web",
                required_capabilities=Capability.WEB_SEARCH,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )
        registry.register(
            Tool(
                name="file_read",
                description="Read files",
                required_capabilities=Capability.READ_FILES,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )
        return registry

    @pytest.mark.asyncio
    async def test_execute_allowed_tool(self, registry_with_tools):
        """Test executing a tool with granted capability."""
        result = await registry_with_tools.execute("web_search", {"query": "test"})
        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_execute_denied_tool(self):
        """Test executing a tool without capability raises."""
        # Create a new registry with more capabilities
        registry = ToolRegistry(
            granted_capabilities=Capability.READ_FILES
            | Capability.WEB_SEARCH
            | Capability.SHELL_ACCESS,
            enabled_tools=[],
        )
        mock_tool = MockTool()

        # First register web_search
        registry.register(
            Tool(
                name="web_search",
                description="Search the web",
                required_capabilities=Capability.WEB_SEARCH,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )

        # Now try to execute with reduced capabilities - this should fail
        with pytest.raises(PermissionError):
            await registry.execute(
                "web_search",
                {"query": "test"},
                granted_capabilities=Capability.READ_FILES,  # Remove WEB_SEARCH
            )

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, registry_with_tools):
        """Test executing unknown tool raises KeyError."""
        with pytest.raises(KeyError):
            await registry_with_tools.execute("nonexistent", {})


class TestToolEnableDisable:
    """Test tool enable/disable functionality."""

    @pytest.fixture
    def registry_with_enabled_tools(self, mock_tool):
        """Create a registry with limited enabled tools."""
        registry = ToolRegistry(
            granted_capabilities=Capability.READ_FILES
            | Capability.WEB_SEARCH
            | Capability.SHELL_ACCESS,
            enabled_tools=["web_search", "file_read"],
        )
        registry.register(
            Tool(
                name="web_search",
                description="Search the web",
                required_capabilities=Capability.WEB_SEARCH,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )
        registry.register(
            Tool(
                name="file_read",
                description="Read files",
                required_capabilities=Capability.READ_FILES,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )
        registry.register(
            Tool(
                name="shell_access",
                description="Run shell commands",
                required_capabilities=Capability.SHELL_ACCESS,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )
        return registry

    def test_enabled_tools_filter(self, registry_with_enabled_tools):
        """Test that only enabled tools are available."""
        schemas = registry_with_enabled_tools.get_tool_schemas()
        tool_names = [s["function"]["name"] for s in schemas]
        assert "web_search" in tool_names
        assert "file_read" in tool_names
        assert "shell_access" not in tool_names

    @pytest.mark.asyncio
    async def test_execute_disabled_tool(self, registry_with_enabled_tools):
        """Test executing a disabled tool raises PermissionError."""
        with pytest.raises(PermissionError, match="is not enabled"):
            await registry_with_enabled_tools.execute("shell_access", {"cmd": "ls"})

    def test_empty_enabled_tools_allows_all(self, mock_tool):
        """Test empty enabled_tools list allows all registered tools."""
        registry = ToolRegistry(
            granted_capabilities=Capability.READ_FILES
            | Capability.WEB_SEARCH
            | Capability.SHELL_ACCESS,
            enabled_tools=[],
        )
        registry.register(
            Tool(
                name="web_search",
                description="Search the web",
                required_capabilities=Capability.WEB_SEARCH,
                parameters={"type": "object", "properties": {}},
                fn=mock_tool,
            )
        )
        schemas = registry.get_tool_schemas()
        assert len(schemas) == 1

    def test_set_enabled_tools(self, registry_with_enabled_tools):
        """Test dynamically updating enabled tools."""
        registry_with_enabled_tools.set_enabled_tools(["shell_access"])
        schemas = registry_with_enabled_tools.get_tool_schemas()
        tool_names = [s["function"]["name"] for s in schemas]
        assert "shell_access" in tool_names
        assert "web_search" not in tool_names
        assert "file_read" not in tool_names


class TestToolRiskLevels:
    """Test tool risk level definitions."""

    def test_all_tools_have_risk_levels(self):
        """Test all known tools have risk levels defined."""
        for tool_name in TOOL_RISK_LEVELS:
            assert TOOL_RISK_LEVELS[tool_name] in ("low", "medium", "high", "critical")

    def test_risk_levels_exist(self):
        """Test expected risk levels are present."""
        assert "web_search" in TOOL_RISK_LEVELS
        assert "file_read" in TOOL_RISK_LEVELS
        assert "file_write" in TOOL_RISK_LEVELS
        assert "code_exec" in TOOL_RISK_LEVELS
        assert "shell_access" in TOOL_RISK_LEVELS
