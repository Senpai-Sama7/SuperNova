"""Built-in code execution tool with hardened Docker sandbox and subprocess fallback.

Security layers:
  - Network isolation (--network none)
  - Read-only root filesystem
  - Memory + CPU + PID limits
  - No new privileges (--security-opt no-new-privileges)
  - Seccomp profile restricting dangerous syscalls
  - Optional gVisor runtime (CODE_SANDBOX=gvisor)
  - tmpfs for /tmp writes
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from supernova.infrastructure.tools.registry import Capability, Tool

logger = logging.getLogger(__name__)

# Seccomp profile: block dangerous syscalls while allowing normal Python execution
_SECCOMP_POLICY = {
    "defaultAction": "SCMP_ACT_ALLOW",
    "syscalls": [
        {
            "names": [
                "clone3", "unshare", "mount", "umount2", "pivot_root",
                "reboot", "swapon", "swapoff", "kexec_load", "init_module",
                "finit_module", "delete_module", "acct", "settimeofday",
                "stime", "ptrace", "personality", "keyctl",
            ],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
        }
    ],
}


def _build_docker_args(
    script: str,
    *,
    timeout: float = 30.0,
    memory_mb: int = 128,
    cpu_quota: int = 50000,
    pids_limit: int = 64,
    sandbox_type: str = "docker",
    seccomp_path: str | None = None,
) -> list[str]:
    """Build hardened docker run arguments."""
    args = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", f"{memory_mb}m",
        "--cpu-quota", str(cpu_quota),
        "--pids-limit", str(pids_limit),
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "--security-opt", "no-new-privileges",
    ]

    if sandbox_type == "gvisor":
        args.extend(["--runtime", "runsc"])

    if seccomp_path:
        args.extend(["--security-opt", f"seccomp={seccomp_path}"])

    args.extend([
        "-v", f"{script}:/tmp/script.py:ro",
        "python:3.12-slim",
        "python", "/tmp/script.py",
    ])
    return args


async def _code_exec(
    code: str,
    language: str = "python",
    timeout: float = 30.0,
    sandbox_type: str = "docker",
) -> dict[str, Any]:
    """Execute code in hardened Docker sandbox, falling back to subprocess."""
    if language != "python":
        return {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": 1}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        script = f.name

    # Write seccomp profile to temp file
    seccomp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as sf:
            json.dump(_SECCOMP_POLICY, sf)
            seccomp_path = sf.name
    except OSError:
        pass

    # Try Docker first
    try:
        args = _build_docker_args(
            script,
            timeout=timeout,
            sandbox_type=sandbox_type,
            seccomp_path=seccomp_path,
        )
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "exit_code": proc.returncode,
            "sandbox": sandbox_type,
        }
    except (FileNotFoundError, OSError):
        logger.info("Docker unavailable, falling back to subprocess")
    except TimeoutError:
        return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1, "sandbox": sandbox_type}
    finally:
        # Clean up seccomp file
        if seccomp_path:
            Path(seccomp_path).unlink(missing_ok=True)

    # Subprocess fallback (no sandbox hardening available)
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
    """Factory returning a hardened code execution Tool."""
    return Tool(
        name="code_exec",
        description="Execute code in a hardened sandboxed environment (Docker preferred, subprocess fallback).",
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
