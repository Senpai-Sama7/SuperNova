"""Capability-gated tool registry for SuperNova.

Provides a Capability flag enum for permission control and a ToolRegistry
that validates capabilities at both registration and execution time.
Tools are exposed as OpenAI-compatible function calling schemas.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Any

from supernova.core.security.sandbox import ExecutionSandbox
from supernova.core.security.sanitizer import ContentSanitizer
from supernova.infrastructure.storage.postgres import AsyncPostgresPool

logger = logging.getLogger(__name__)


class Capability(Flag):
    """Capability flags for tool permission control."""

    READ_FILES = auto()
    WRITE_FILES = auto()
    EXECUTE_CODE = auto()
    WEB_SEARCH = auto()
    WEB_BROWSE = auto()
    SEND_EMAIL = auto()
    SHELL_ACCESS = auto()
    EXTERNAL_API = auto()


TOOL_RISK_LEVELS: dict[str, str] = {
    "web_search": "low",
    "file_read": "low",
    "file_write": "medium",
    "code_exec": "high",
    "web_browse": "low",
    "send_email": "high",
    "external_api": "medium",
    "shell_access": "critical",
}


@dataclass
class Tool:
    """A registered tool with capability requirements and OpenAI schema."""

    name: str
    description: str
    required_capabilities: Capability
    parameters: dict[str, Any]  # JSON Schema for parameters
    fn: Callable[..., Awaitable[Any]]
    is_safe_parallel: bool = True
    risk_level: str = "low"


class ToolRegistry:
    """Capability-gated tool registry.

    Validates that tools' required capabilities are a subset of the
    granted capabilities at both registration and execution time.
    Execution has a 30-second timeout and logs to audit_log.
    """

    def __init__(
        self,
        granted_capabilities: Capability,
        pool: AsyncPostgresPool | None = None,
        enabled_tools: list[str] | None = None,
        sandbox: ExecutionSandbox | None = None,
    ) -> None:
        self._granted = granted_capabilities
        self._pool = pool
        self._tools: dict[str, Tool] = {}
        self._enabled_tools: set[str] = set(enabled_tools) if enabled_tools else set()
        self._sandbox = sandbox or ExecutionSandbox()
        self._sanitizer = ContentSanitizer()

    @staticmethod
    def _coerce_capabilities(value: Capability | int | None) -> Capability:
        """Normalize runtime capability input into a Capability flag set."""
        if value is None:
            return Capability(0)
        if isinstance(value, Capability):
            return value
        return Capability(value)

    def set_enabled_tools(self, enabled_tools: list[str]) -> None:
        """Set the list of enabled tools for this registry.

        If empty, all registered tools are allowed.
        If non-empty, only tools in this list are allowed.

        Args:
            enabled_tools: List of tool names to enable
        """
        self._enabled_tools = set(enabled_tools)
        logger.info(f"Tool registry updated: {len(self._enabled_tools)} tools enabled")

    def is_tool_enabled(self, tool_name: str) -> bool:
        """Check if a tool is enabled for this user.

        Args:
            tool_name: Name of the tool to check

        Returns:
            bool: True if tool is enabled (or no restrictions configured)
        """
        if not self._enabled_tools:
            return True
        return tool_name in self._enabled_tools

    def register(self, tool: Tool) -> None:
        """Register a tool, validating its capabilities are permitted.

        Raises:
            PermissionError: If tool requires capabilities not granted.
        """
        missing = tool.required_capabilities & ~self._granted
        if missing:
            raise PermissionError(
                f"Tool '{tool.name}' requires capabilities not granted: {missing}"
            )
        self._tools[tool.name] = tool

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        timeout: float = 30.0,
        granted_capabilities: Capability | int | None = None,
    ) -> Any:
        """Execute a tool with runtime capability check and timeout.

        Args:
            name: Tool name.
            arguments: Tool arguments.
            timeout: Execution timeout in seconds (default 30).

        Raises:
            KeyError: If tool not found.
            PermissionError: If capabilities no longer sufficient.
            asyncio.TimeoutError: If execution exceeds timeout.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not registered")

        if not self.is_tool_enabled(name):
            raise PermissionError(f"Tool '{name}' is not enabled for this user")

        # Runtime re-validation
        effective_caps = (
            self._coerce_capabilities(granted_capabilities)
            if granted_capabilities is not None
            else self._granted
        )
        missing = tool.required_capabilities & ~effective_caps
        if missing:
            raise PermissionError(f"Tool '{name}' requires capabilities not granted: {missing}")

        # Validate tool arguments
        for key, value in arguments.items():
            if isinstance(value, str):
                result = self._sanitizer.sanitize(value)
                if not result.is_clean:
                    raise ValueError(f"Unsafe input in argument {key}: {result.warnings}")
                arguments[key] = result.text

        # Execute tool in sandbox with timeout
        try:
            sandbox_result = await asyncio.wait_for(
                self._sandbox.run(tool.fn, **arguments), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Tool execution exceeded {timeout}s timeout")
        
        # Log execution
        await self._log_execution(
            name, 
            sandbox_result["duration_ms"] / 1000, 
            sandbox_result.get("error")
        )
        
        # Handle sandbox results
        if sandbox_result["status"] == "success":
            return sandbox_result["result"]
        elif sandbox_result["status"] == "timeout":
            raise asyncio.TimeoutError(sandbox_result["error"])
        else:
            raise RuntimeError(sandbox_result["error"])

    async def _log_execution(
        self,
        tool_name: str,
        elapsed: float,
        error: str | None,
    ) -> None:
        """Log tool execution to audit_log."""
        if self._pool is None:
            return
        try:
            import json

            details = json.dumps({"elapsed_ms": round(elapsed * 1000, 1), "error": error})
            await self._pool.execute(
                """INSERT INTO audit_log (action, resource_type, resource_id, details)
                   VALUES ('tool_execution', 'tool', $1, $2::jsonb)""",
                tool_name,
                details,
            )
        except Exception as e:
            logger.warning(f"Failed to log tool execution: {e}")

    def get_tool_schemas(
        self,
        *,
        granted_capabilities: Capability | int | None = None,
    ) -> list[dict[str, Any]]:
        """Return OpenAI-format function schemas for permitted tools."""
        effective_caps = (
            self._coerce_capabilities(granted_capabilities)
            if granted_capabilities is not None
            else self._granted
        )
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
            if not (tool.required_capabilities & ~effective_caps)
            and self.is_tool_enabled(tool.name)
        ]

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name, or None if not found."""
        return self._tools.get(name)
