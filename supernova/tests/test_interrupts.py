"""Tests for interrupts.py — HITL interrupt coordinator."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

_root = str(Path(__file__).resolve().parents[2])
if _root not in sys.path:
    sys.path.insert(0, _root)

from interrupts import InterruptCoordinator, RiskLevel


def _make_coordinator(timeout_override=None):
    broadcaster = AsyncMock()
    broadcaster.send = AsyncMock()
    return InterruptCoordinator(
        websocket_broadcaster=broadcaster,
        default_timeout_override=timeout_override,
    )


class TestApprovalFlow:
    @pytest.mark.asyncio
    async def test_approval_resolves_when_decision_submitted(self):
        """submit_decision() unblocks request_approval()."""
        coord = _make_coordinator(timeout_override=5.0)

        async def approve_after_delay():
            await asyncio.sleep(0.05)
            await coord.submit_decision("t1", True)

        asyncio.create_task(approve_after_delay())
        result = await coord.request_approval("t1", "web_search", {}, RiskLevel.LOW)
        assert result.approved is True
        assert result.source == "user"

    @pytest.mark.asyncio
    async def test_timeout_auto_approves_low_risk(self):
        """Low risk auto-approves after timeout."""
        coord = _make_coordinator(timeout_override=0.05)
        result = await coord.request_approval("t2", "web_search", {}, RiskLevel.LOW)
        assert result.approved is True
        assert result.source == "timeout_auto_approve"

    @pytest.mark.asyncio
    async def test_timeout_auto_denies_high_risk(self):
        """High risk auto-denies after timeout."""
        coord = _make_coordinator(timeout_override=0.05)
        result = await coord.request_approval("t3", "send_email", {}, RiskLevel.HIGH)
        assert result.approved is False
        assert result.source == "timeout_auto_deny"


class TestSubmitDecision:
    @pytest.mark.asyncio
    async def test_unknown_thread_id_returns_false(self):
        """submit_decision returns False for unknown thread_id."""
        coord = _make_coordinator()
        result = await coord.submit_decision("nonexistent", True)
        assert result is False


class TestOSNotification:
    @pytest.mark.asyncio
    async def test_os_notification_does_not_raise_if_binary_missing(self):
        """FileNotFoundError suppressed for missing notify binary."""
        coord = _make_coordinator(timeout_override=0.05)
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("no binary")):
            # Should not raise — notification failure is non-fatal
            result = await coord.request_approval("t5", "file_read", {}, RiskLevel.LOW)
            assert result.approved is True  # low risk auto-approves on timeout

    @pytest.mark.asyncio
    async def test_pending_approvals_list(self):
        """get_pending_approvals returns current pending items."""
        coord = _make_coordinator(timeout_override=2.0)

        async def check_pending():
            await asyncio.sleep(0.02)
            pending = coord.get_pending_approvals()
            assert len(pending) == 1
            assert pending[0]["tool_name"] == "code_exec"
            await coord.submit_decision("t6", False)

        asyncio.create_task(check_pending())
        result = await coord.request_approval("t6", "code_exec", {"code": "print(1)"}, RiskLevel.MEDIUM)
        assert result.approved is False
