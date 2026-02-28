"""Regression tests for gateway abuse controls and audit hooks."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from supernova.api import gateway


class _FakeWebSocket:
    def __init__(self, host: str = "127.0.0.1") -> None:
        self.client = SimpleNamespace(host=host)
        self.close_calls: list[dict[str, object]] = []

    async def close(self, code: int | None = None, reason: str | None = None) -> None:
        self.close_calls.append({"code": code, "reason": reason})

    async def accept(self) -> None:
        raise AssertionError("accept should not be called in invalid-token tests")

    async def send_json(self, payload: object) -> None:
        raise AssertionError(f"send_json should not be called: {payload}")

    async def receive_text(self) -> str:
        raise AssertionError("receive_text should not be called")


@pytest.fixture(autouse=True)
def clear_rate_limit_state() -> None:
    gateway._rate_limit_state.clear()
    yield
    gateway._rate_limit_state.clear()



def test_rate_limit_blocks_after_max_calls() -> None:
    bucket = "issue_token:test"
    for i in range(gateway._RATE_LIMIT_MAX_CALLS):
        gateway._enforce_rate_limit(bucket, now_ts=100.0 + i)

    with pytest.raises(HTTPException, match="Rate limit exceeded"):
        gateway._enforce_rate_limit(bucket, now_ts=100.0 + gateway._RATE_LIMIT_MAX_CALLS)



def test_rate_limit_resets_after_window() -> None:
    bucket = "issue_token:test"
    for i in range(gateway._RATE_LIMIT_MAX_CALLS):
        gateway._enforce_rate_limit(bucket, now_ts=100.0 + i)

    gateway._enforce_rate_limit(bucket, now_ts=100.0 + gateway._RATE_LIMIT_WINDOW_SECONDS + 1.0)



def test_audit_helper_emits_log(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    def fake_info(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(gateway.logger, "info", fake_info)
    gateway._audit_privileged_action("gateway.memory.export", "user-123", {"format": "json"})

    assert calls
    assert "gateway.memory.export" in str(calls[0][0])


@pytest.mark.asyncio
async def test_health_ws_invalid_token_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "verify_token", lambda token: False)
    ws = _FakeWebSocket()

    await gateway.health_ws(ws, token="bad-token")

    assert ws.close_calls[0]["code"] == 4001


@pytest.mark.asyncio
async def test_health_ws_invalid_token_is_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "verify_token", lambda token: False)
    ws = _FakeWebSocket()
    bucket = f"invalid_token:{ws.client.host}"
    for _ in range(gateway._RATE_LIMIT_MAX_CALLS):
        gateway._enforce_rate_limit(bucket)

    await gateway.health_ws(ws, token="bad-token")

    assert ws.close_calls[0]["code"] == 4008


@pytest.mark.asyncio
async def test_issue_token_blocked_in_production_is_audited(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    def fake_info(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(gateway.logger, "info", fake_info)
    monkeypatch.setattr(gateway, "settings", SimpleNamespace(is_production=True))
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    with pytest.raises(HTTPException, match="disabled in production"):
        await gateway.issue_token(request)

    assert any("gateway.issue_token.blocked_production" in str(args) for args, _ in calls)
