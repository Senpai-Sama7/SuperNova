"""Regression tests for gateway abuse controls and audit hooks."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from supernova.api import gateway


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
