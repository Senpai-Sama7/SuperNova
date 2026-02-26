"""Tests for infrastructure/security/audit.py — write, flush, query paths."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.security.audit import (
    _audit_buffer,
    flush_audit_buffer,
    query_audit_logs,
    write_audit_entry,
)


@pytest.fixture(autouse=True)
def clear_buffer():
    _audit_buffer.clear()
    yield
    _audit_buffer.clear()


def _make_pool():
    """Create a mock pool with acquire() context manager."""
    conn = AsyncMock()
    pool = MagicMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


class TestWriteAuditEntry:
    @pytest.mark.asyncio
    async def test_inserts_entry(self):
        pool, conn = _make_pool()
        entry = {
            "user_id": "u1",
            "action": "config.update",
            "resource": "settings",
            "details": {"key": "val"},
            "ip_address": "127.0.0.1",
        }
        await write_audit_entry(pool, entry)
        conn.execute.assert_awaited_once()
        sql = conn.execute.call_args[0][0]
        assert "INSERT INTO supernova_audit_logs" in sql


class TestFlushAuditBuffer:
    @pytest.mark.asyncio
    async def test_flushes_all_entries(self):
        pool, conn = _make_pool()
        _audit_buffer.extend([
            {"user_id": "u1", "action": "a1", "resource": "r1", "details": {}, "ip_address": None},
            {"user_id": "u2", "action": "a2", "resource": "r2", "details": {}, "ip_address": None},
        ])
        count = await flush_audit_buffer(pool)
        assert count == 2
        assert len(_audit_buffer) == 0
        assert conn.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_flush_empty_buffer(self):
        pool, _ = _make_pool()
        count = await flush_audit_buffer(pool)
        assert count == 0


class TestQueryAuditLogs:
    @pytest.mark.asyncio
    async def test_query_no_filters(self):
        pool, conn = _make_pool()
        conn.fetch.return_value = [{"id": 1, "action": "login"}]
        rows = await query_audit_logs(pool)
        assert len(rows) == 1
        sql = conn.fetch.call_args[0][0]
        assert "WHERE" not in sql

    @pytest.mark.asyncio
    async def test_query_with_user_filter(self):
        pool, conn = _make_pool()
        conn.fetch.return_value = []
        await query_audit_logs(pool, user_id="u1")
        sql = conn.fetch.call_args[0][0]
        assert "user_id = $1" in sql

    @pytest.mark.asyncio
    async def test_query_with_both_filters(self):
        pool, conn = _make_pool()
        conn.fetch.return_value = []
        await query_audit_logs(pool, user_id="u1", action="login", limit=10, offset=5)
        sql = conn.fetch.call_args[0][0]
        assert "user_id = $1" in sql
        assert "action = $2" in sql
