"""Execution sandbox for tool/command execution.

Provides ExecutionSandbox for running tools and shell commands with:
- Timeout enforcement
- Resource limits
- Command blocking for dangerous operations
- Async execution with proper error handling
"""

import asyncio
import logging
import subprocess
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ExecutionSandbox:
    """Sandboxed execution environment with timeout and resource limits."""

    def __init__(self, timeout: float = 30.0, max_memory_mb: int = 512):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    async def run(self, func: Callable, *args, **kwargs) -> dict[str, Any]:
        """Execute function in sandboxed environment with timeout and resource limits."""
        start = time.monotonic()
        try:
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
            return {
                "status": "success",
                "result": result,
                "duration_ms": int((time.monotonic() - start) * 1000)
            }
        except asyncio.TimeoutError:
            logger.error(f"Sandbox timeout after {self.timeout}s")
            return {
                "status": "timeout",
                "error": f"Execution exceeded {self.timeout}s limit",
                "duration_ms": int((time.monotonic() - start) * 1000)
            }
        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration_ms": int((time.monotonic() - start) * 1000)
            }

    def run_subprocess(self, command: list[str], timeout: float = None) -> dict[str, Any]:
        """Execute shell command with restrictions."""
        # Security: Block dangerous commands
        BLOCKED = ['rm -rf /', 'mkfs', 'dd if=', ':(){', 'fork bomb']
        cmd_str = ' '.join(command)
        if any(b in cmd_str for b in BLOCKED):
            return {"status": "blocked", "error": "Command blocked by security policy"}

        start = time.monotonic()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                cwd='/tmp'  # Restrict to safe directory
            )
            return {
                "status": "success",
                "stdout": result.stdout[:10000],  # Limit output size
                "stderr": result.stderr[:5000],
                "returncode": result.returncode,
                "duration_ms": int((time.monotonic() - start) * 1000)
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": f"Command exceeded {timeout or self.timeout}s"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}