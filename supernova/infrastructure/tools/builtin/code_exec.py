"""Built-in code execution tool with Docker sandbox and subprocess fallback."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from typing import Any

from supernova.infrastructure.tools.registry import Capability, Tool

logger = logging.getLogger(__name__)


async def _code_exec(code: str, language: str = "python", timeout: float = 30.0) -> dict[str, Any]:
    """Execute code in Docker sandbox, falling back to subprocess."""
    if language != "python":
        return {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": 1}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        script = f.name

    # Try Docker first
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "128m",
            "--cpu-quota", "50000",
            "--read-only",
            "-v", f"{script}:/tmp/script.py:ro",
            "python:3.12-slim",
            "python", "/tmp/script.py",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
            "sandbox": "docker",
        }
    except (FileNotFoundError, OSError):
        logger.info("Docker unavailable, falling back to subprocess")
    except TimeoutError:
        return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1, "sandbox": "docker"}

    # Subprocess fallback
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
            "sandbox": "subprocess",
        }
    except TimeoutError:
        return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1, "sandbox": "subprocess"}


def create_code_exec_tool() -> Tool:
    """Factory returning a code execution Tool."""
    return Tool(
        name="code_exec",
        description="Execute code in a sandboxed environment (Docker preferred, subprocess fallback).",
        required_capabilities=Capability.EXECUTE_CODE,
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to execute"},
                "language": {"type": "string", "description": "Programming language", "default": "python"},
                "timeout": {"type": "number", "description": "Timeout in seconds", "default": 30.0},
            },
            "required": ["code"],
        },
        fn=_code_exec,
        is_safe_parallel=False,
    )
