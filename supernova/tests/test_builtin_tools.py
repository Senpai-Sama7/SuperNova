"""Tests for built-in tools (Task 5.6)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from supernova.infrastructure.tools.registry import Capability, Tool

# ── web_search tests ──────────────────────────────────────────────────────────

class TestWebSearch:
    def test_factory_returns_tool(self):
        from supernova.infrastructure.tools.builtin.web_search import create_web_search_tool
        tool = create_web_search_tool()
        assert isinstance(tool, Tool)
        assert tool.name == "web_search"
        assert tool.required_capabilities == Capability.WEB_SEARCH
        assert tool.is_safe_parallel is True

    @pytest.mark.asyncio
    async def test_tavily_search(self):
        from supernova.infrastructure.tools.builtin.web_search import _web_search
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"title": "T", "url": "http://x", "content": "S"}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
                results = await _web_search("test query")
        assert len(results) == 1
        assert results[0]["title"] == "T"
        assert results[0]["snippet"] == "S"

    @pytest.mark.asyncio
    async def test_serpapi_fallback(self):
        from supernova.infrastructure.tools.builtin.web_search import _web_search
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "organic_results": [{"title": "T", "link": "http://x", "snippet": "S"}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch.dict("os.environ", {"SERPAPI_KEY": "test-key"}, clear=False):
            # Ensure TAVILY_API_KEY is not set
            import os
            os.environ.pop("TAVILY_API_KEY", None)
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
                results = await _web_search("test query")
        assert len(results) == 1
        assert results[0]["url"] == "http://x"

    @pytest.mark.asyncio
    async def test_no_api_key_raises(self):
        from supernova.infrastructure.tools.builtin.web_search import _web_search
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="No search API key"):
                await _web_search("test")


# ── file_ops tests ────────────────────────────────────────────────────────────

class TestFileOps:
    def test_read_factory_returns_tool(self):
        from supernova.infrastructure.tools.builtin.file_ops import create_file_read_tool
        tool = create_file_read_tool()
        assert tool.name == "file_read"
        assert tool.required_capabilities == Capability.READ_FILES
        assert tool.is_safe_parallel is True

    def test_write_factory_returns_tool(self):
        from supernova.infrastructure.tools.builtin.file_ops import create_file_write_tool
        tool = create_file_write_tool()
        assert tool.name == "file_write"
        assert tool.required_capabilities == Capability.WRITE_FILES
        assert tool.is_safe_parallel is False

    def test_safe_path_rejects_dotdot(self):
        from supernova.infrastructure.tools.builtin.file_ops import _safe_path
        with pytest.raises(PermissionError, match="traversal rejected"):
            _safe_path("../etc/passwd")

    def test_safe_path_rejects_escape(self):
        from supernova.infrastructure.tools.builtin.file_ops import _safe_path
        # Absolute path outside workspace
        with pytest.raises(PermissionError):
            _safe_path("/etc/passwd")

    def test_safe_path_allows_valid(self):
        from supernova.infrastructure.tools.builtin.file_ops import WORKSPACE, _safe_path
        p = _safe_path("subdir/file.txt")
        assert str(p).startswith(str(WORKSPACE))

    @pytest.mark.asyncio
    async def test_file_write_and_read(self, tmp_path):
        from supernova.infrastructure.tools.builtin import file_ops
        # Temporarily override WORKSPACE
        original = file_ops.WORKSPACE
        file_ops.WORKSPACE = tmp_path
        try:
            result = await file_ops._file_write("test.txt", "hello world")
            assert "11 bytes" in result
            content = await file_ops._file_read("test.txt")
            assert content == "hello world"
        finally:
            file_ops.WORKSPACE = original

    @pytest.mark.asyncio
    async def test_file_write_creates_subdirs(self, tmp_path):
        from supernova.infrastructure.tools.builtin import file_ops
        original = file_ops.WORKSPACE
        file_ops.WORKSPACE = tmp_path
        try:
            await file_ops._file_write("a/b/c.txt", "nested")
            assert (tmp_path / "a" / "b" / "c.txt").read_text() == "nested"
        finally:
            file_ops.WORKSPACE = original


# ── code_exec tests ───────────────────────────────────────────────────────────

class TestCodeExec:
    def test_factory_returns_tool(self):
        from supernova.infrastructure.tools.builtin.code_exec import create_code_exec_tool
        tool = create_code_exec_tool()
        assert tool.name == "code_exec"
        assert tool.required_capabilities == Capability.EXECUTE_CODE
        assert tool.is_safe_parallel is False

    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        from supernova.infrastructure.tools.builtin.code_exec import _code_exec
        result = await _code_exec("console.log('hi')", language="javascript")
        assert result["exit_code"] == 1
        assert "Unsupported" in result["stderr"]

    @pytest.mark.asyncio
    async def test_subprocess_fallback(self):
        from supernova.infrastructure.tools.builtin.code_exec import _code_exec
        # Mock Docker as unavailable, subprocess succeeds
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"42\n", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # First call (docker) raises FileNotFoundError, second call (python3) succeeds
            mock_exec.side_effect = [FileNotFoundError("docker not found"), mock_proc]
            result = await _code_exec("print(42)")

        assert result["stdout"] == "42\n"
        assert result["exit_code"] == 0
        assert result["sandbox"] == "subprocess"

    @pytest.mark.asyncio
    async def test_docker_execution(self):
        from supernova.infrastructure.tools.builtin.code_exec import _code_exec
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await _code_exec("print('hello')")

        assert result["stdout"] == "hello\n"
        assert result["sandbox"] == "docker"

    @pytest.mark.asyncio
    async def test_docker_timeout(self):
        from supernova.infrastructure.tools.builtin.code_exec import _code_exec
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
                result = await _code_exec("while True: pass", timeout=1.0)

        assert result["exit_code"] == -1
        assert "timed out" in result["stderr"]
