"""Tests for interrupts.py — HITL interrupt coordinator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from supernova.api.interrupts import (
    AUTO_RESOLVE_ON_TIMEOUT,
    TIMEOUT_BY_RISK,
    InterruptCoordinator,
    RiskLevel,
    _escape_applescript,
    _summarize_args,
)


def _make_coordinator(timeout_override=None):
    broadcaster = AsyncMock()
    broadcaster.send = AsyncMock()
    return InterruptCoordinator(
        websocket_broadcaster=broadcaster,
        default_timeout_override=timeout_override,
    )


class TestPolicies:
    def test_timeout_by_risk_has_all_levels(self) -> None:
        for rl in RiskLevel:
            assert rl.value in TIMEOUT_BY_RISK
            assert TIMEOUT_BY_RISK[rl.value] > 0

    def test_auto_resolve_policy_is_asymmetric(self) -> None:
        assert AUTO_RESOLVE_ON_TIMEOUT[RiskLevel.LOW.value] is True
        for rl in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL):
            assert AUTO_RESOLVE_ON_TIMEOUT[rl.value] is False


class TestUtilities:
    def test_summarize_args_empty(self) -> None:
        assert _summarize_args({}) == "no arguments"

    def test_summarize_args_truncates_values_and_counts_more(self) -> None:
        args = {
            "a": "x" * 200,
            "b": 123,
            "c": "ok",
            "d": "extra",
        }
        s = _summarize_args(args)
        assert "a=" in s and "..." in s
        assert "(+1 more)" in s

    def test_escape_applescript_escapes_quotes_and_backslashes(self) -> None:
        text = 'a"b\\c'
        out = _escape_applescript(text)
        assert '\\"' in out
        assert "\\\\" in out

    def test_escape_applescript_strips_control_chars_and_limits_length(self) -> None:
        text = "a\x00b\x1fc" + ("x" * 1000)
        out = _escape_applescript(text)
        assert "\x00" not in out
        assert "\x1f" not in out
        assert len(out) <= 500


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
        assert coord.get_pending_approvals() == []  # cleaned up

    @pytest.mark.asyncio
    async def test_timeout_auto_approves_low_risk(self):
        """Low risk auto-approves after timeout."""
        coord = _make_coordinator(timeout_override=0.05)
        result = await coord.request_approval("t2", "web_search", {}, RiskLevel.LOW)
        assert result.approved is True
        assert result.source == "timeout_auto_approve"
        assert coord.get_pending_approvals() == []

    @pytest.mark.asyncio
    async def test_timeout_auto_denies_high_risk(self):
        """High risk auto-denies after timeout."""
        coord = _make_coordinator(timeout_override=0.05)
        result = await coord.request_approval("t3", "send_email", {}, RiskLevel.HIGH)
        assert result.approved is False
        assert result.source == "timeout_auto_deny"
        assert coord.get_pending_approvals() == []

    @pytest.mark.asyncio
    async def test_websocket_notification_payload_sent(self) -> None:
        coord = _make_coordinator(timeout_override=5.0)

        with patch.object(coord, "_notify_os", new=AsyncMock()):
            task = asyncio.create_task(
                coord.request_approval("t_ws", "file_write", {"path": "a.txt"}, RiskLevel.MEDIUM)
            )
            await asyncio.sleep(0.02)  # allow notify task to run

            assert coord.broadcaster.send.await_count >= 1
            args, kwargs = coord.broadcaster.send.await_args
            assert args[0] == "t_ws"
            payload = args[1]
            assert payload["type"] == "approval_request"
            assert payload["tool"] == "file_write"
            assert payload["risk_level"] == RiskLevel.MEDIUM.value
            assert payload["auto_resolve"] is False
            assert "expires_in_seconds" in payload

            await coord.submit_decision("t_ws", True)
            result = await task

        assert result.approved is True
        assert result.source == "user"

    @pytest.mark.asyncio
    async def test_timeout_sends_timeout_event_to_websocket(self) -> None:
        coord = _make_coordinator(timeout_override=0.05)
        with patch.object(coord, "_notify_os", new=AsyncMock()):
            result = await coord.request_approval("t_to", "file_read", {}, RiskLevel.MEDIUM)
        assert result.source == "timeout_auto_deny"
        # A timeout notification should also be sent
        sent_payloads = [call.args[1] for call in coord.broadcaster.send.await_args_list]
        assert any(p.get("type") == "approval_timeout" for p in sent_payloads)

    @pytest.mark.asyncio
    async def test_same_thread_id_second_request_overwrites_first(self) -> None:
        """As documented: concurrent approvals with same thread_id overwrite.

        The second approval becomes the one that submit_decision resolves; the
        first will fall through to its timeout policy.
        """
        coord = _make_coordinator(timeout_override=0.05)
        with patch.object(coord, "_notify_os", new=AsyncMock()):
            t1 = asyncio.create_task(
                coord.request_approval("same", "web_search", {}, RiskLevel.LOW)
            )
            await asyncio.sleep(0.01)
            t2 = asyncio.create_task(
                coord.request_approval("same", "code_exec", {}, RiskLevel.MEDIUM)
            )
            await asyncio.sleep(0.01)
            await coord.submit_decision("same", True)
            r2 = await t2
            r1 = await t1

        assert r2.source == "user"
        assert r2.approved is True
        assert r1.source == "timeout_auto_approve"  # LOW policy


class TestSubmitDecision:
    @pytest.mark.asyncio
    async def test_unknown_thread_id_returns_false(self):
        """submit_decision returns False for unknown thread_id."""
        coord = _make_coordinator()
        result = await coord.submit_decision("nonexistent", True)
        assert result is False

    @pytest.mark.asyncio
    async def test_submit_decision_after_timeout_returns_false(self) -> None:
        coord = _make_coordinator(timeout_override=0.01)
        with patch.object(coord, "_notify_os", new=AsyncMock()):
            await coord.request_approval("expired", "web_search", {}, RiskLevel.MEDIUM)
        assert await coord.submit_decision("expired", True) is False


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
        result = await coord.request_approval(
            "t6", "code_exec", {"code": "print(1)"}, RiskLevel.MEDIUM
        )
        assert result.approved is False
