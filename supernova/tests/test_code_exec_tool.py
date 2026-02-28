from __future__ import annotations

import textwrap

import pytest

from supernova.infrastructure.tools.builtin.code_exec import _code_exec


@pytest.mark.asyncio
async def test_code_exec_rejects_unsupported_language() -> None:
    """Non-Python languages should be rejected with exit_code=1."""
    result = await _code_exec("print('hi')", language="javascript", timeout=1.0)

    assert result["exit_code"] == 1
    assert "Unsupported language" in result["stderr"]
    # stdout should be empty on this fast-fail path
    assert result["stdout"] == ""


@pytest.mark.asyncio
async def test_code_exec_runs_simple_python_successfully() -> None:
    """Simple Python code should run and produce expected stdout."""
    code = "print('hello from sandbox')"
    result = await _code_exec(code, language="python", timeout=5.0)

    assert result["exit_code"] == 0
    assert "hello from sandbox" in result["stdout"]
    # stderr should normally be empty
    assert result["stderr"] == ""


@pytest.mark.asyncio
async def test_code_exec_enforces_timeout() -> None:
    """Long-running code should be terminated after the timeout with exit_code=-1."""
    code = textwrap.dedent(
        """
        import time

        time.sleep(10)
        """
    )

    result = await _code_exec(code, language="python", timeout=0.5)

    assert result["exit_code"] == -1
    assert "timed out" in result["stderr"].lower()
    assert result["stdout"] == ""
