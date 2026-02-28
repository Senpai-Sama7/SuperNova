"""Regression tests for gateway abuse controls and audit hooks."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from supernova.api import gateway


class _FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key.lower(), default)


class _FakeWebSocket:
    def __init__(self, host: str = "127.0.0.1", headers: dict[str, str] | None = None) -> None:
        self.client = SimpleNamespace(host=host)
        self.headers = _FakeHeaders({k.lower(): v for k, v in (headers or {}).items()})
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



def test_request_id_prefers_forwarded_header() -> None:
    headers = _FakeHeaders({"x-request-id": "req-123"})

    assert gateway._request_id_from_headers(headers) == "req-123"



def test_build_audit_payload_has_standard_shape() -> None:
    payload = gateway._build_audit_payload(
        action="gateway.memory.export",
        route="/memory/export",
        outcome="success",
        user_id="user-123",
        client_host="127.0.0.1",
        request_id="req-123",
        actor_type="user",
        auth_method="jwt",
        details={"format": "json"},
    )

    assert payload["event_type"] == "gateway_audit"
    assert payload["event_category"] == "privileged_action"
    assert payload["audit_layer"] == "route"
    assert payload["request_id"] == "req-123"
    assert payload["action"] == "gateway.memory.export"
    assert payload["route"] == "/memory/export"
    assert payload["outcome"] == "success"
    assert payload["user_id"] == "user-123"
    assert payload["actor_type"] == "user"
    assert payload["auth_method"] == "jwt"
    assert payload["client_host"] == "127.0.0.1"
    assert payload["details"] == {"format": "json"}
    assert "timestamp" in payload



def test_audit_helper_emits_standard_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    def fake_info(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(gateway.logger, "info", fake_info)
    gateway._audit_privileged_action(
        action="gateway.memory.export",
        route="/memory/export",
        outcome="success",
        user_id="user-123",
        client_host="127.0.0.1",
        request_id="req-123",
        actor_type="user",
        auth_method="jwt",
        details={"format": "json"},
    )

    assert calls
    payload = calls[0][0][1]
    assert payload["event_type"] == "gateway_audit"
    assert payload["event_category"] == "privileged_action"
    assert payload["audit_layer"] == "route"
    assert payload["request_id"] == "req-123"
    assert payload["action"] == "gateway.memory.export"
    assert payload["route"] == "/memory/export"
    assert payload["outcome"] == "success"
    assert payload["actor_type"] == "user"
    assert payload["auth_method"] == "jwt"


@pytest.mark.asyncio
async def test_health_ws_invalid_token_is_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "verify_token", lambda token: False)
    ws = _FakeWebSocket(headers={"x-request-id": "req-123"})

    await gateway.health_ws(ws, token="bad-token")

    assert ws.close_calls[0]["code"] == 4001


@pytest.mark.asyncio
async def test_health_ws_invalid_token_is_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway, "verify_token", lambda token: False)
    ws = _FakeWebSocket(headers={"x-request-id": "req-123"})
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
    request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers=_FakeHeaders({"x-request-id": "req-123"}),
    )

    with pytest.raises(HTTPException, match="disabled in production"):
        await gateway.issue_token(request)

    payload = calls[0][0][1]
    assert payload["event_category"] == "privileged_action"
    assert payload["audit_layer"] == "route"
    assert payload["request_id"] == "req-123"
    assert payload["action"] == "gateway.issue_token.blocked_production"
    assert payload["route"] == "/auth/token"
    assert payload["outcome"] == "blocked"
    assert payload["actor_type"] == "anonymous"
    assert payload["auth_method"] == "none"
