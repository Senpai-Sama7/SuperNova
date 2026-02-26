"""Capability-gated tool registry for SuperNova.

Provides a Capability flag enum for permission control and a ToolRegistry
that validates capabilities at both registration and execution time.
Tools are exposed as OpenAI-compatible function calling schemas.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Any, Callable, Awaitable

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


@dataclass
class Tool:
    """A registered tool with capability requirements and OpenAI schema."""

    name: str
    description: str
    required_capabilities: Capability
    parameters: dict[str, Any]  # JSON Schema for parameters
    fn: Callable[..., Awaitable[Any]]
    is_safe_parallel: bool = True


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
    ) -> None:
        self._granted = granted_capabilities
        self._pool = pool
        self._tools: dict[str, Tool] = {}

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

        # Runtime re-validation
        missing = tool.required_capabilities & ~self._granted
        if missing:
            raise PermissionError(
                f"Tool '{name}' requires capabilities not granted: {missing}"
            )

        start = time.monotonic()
        error_msg = None
        try:
            result = await asyncio.wait_for(tool.fn(**arguments), timeout=timeout)
            return result
        except Exception as e:
            error_msg = str(e)
            raise
        finally:
            elapsed = time.monotonic() - start
            await self._log_execution(name, elapsed, error_msg)

    async def _log_execution(
        self, tool_name: str, elapsed: float, error: str | None,
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

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Return OpenAI-format function schemas for all permitted tools."""
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
        ]

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name, or None if not found."""
        return self._tools.get(name)
