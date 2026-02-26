"""Built-in file operation tools with path jail to ./workspace/ (CC-3)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from supernova.infrastructure.tools.registry import Capability, Tool

logger = logging.getLogger(__name__)

WORKSPACE = Path("./workspace").resolve()


def _safe_path(rel: str) -> Path:
    """Resolve path within workspace jail. Rejects '..' traversal."""
    if ".." in rel:
        raise PermissionError(f"Path traversal rejected: {rel}")
    target = (WORKSPACE / rel).resolve()
    if not str(target).startswith(str(WORKSPACE)):
        raise PermissionError(f"Path escapes workspace: {rel}")
    return target


async def _file_read(path: str) -> str:
    """Read a file from the workspace."""
    return _safe_path(path).read_text(encoding="utf-8")


async def _file_write(path: str, content: str) -> str:
    """Write content to a file in the workspace."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"


def create_file_read_tool() -> Tool:
    """Factory returning a file read Tool."""
    return Tool(
        name="file_read",
        description="Read a file from the workspace directory.",
        required_capabilities=Capability.READ_FILES,
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative path within workspace"}},
            "required": ["path"],
        },
        fn=_file_read,
        is_safe_parallel=True,
    )


def create_file_write_tool() -> Tool:
    """Factory returning a file write Tool."""
    return Tool(
        name="file_write",
        description="Write content to a file in the workspace directory.",
        required_capabilities=Capability.WRITE_FILES,
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path within workspace"},
                "content": {"type": "string", "description": "File content to write"},
            },
            "required": ["path", "content"],
        },
        fn=_file_write,
        is_safe_parallel=False,
    )
