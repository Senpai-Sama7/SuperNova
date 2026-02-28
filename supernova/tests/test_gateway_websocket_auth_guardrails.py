"""Regression tests for websocket auth guardrails in the gateway."""

from __future__ import annotations

import inspect

from supernova.api import gateway


def test_health_websocket_requires_token_query_param() -> None:
    signature = inspect.signature(gateway.health_ws)
    assert "token" in signature.parameters


def test_agent_stream_requires_token_query_param() -> None:
    signature = inspect.signature(gateway.agent_stream)
    assert "token" in signature.parameters
