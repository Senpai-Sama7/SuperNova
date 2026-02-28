"""Regression tests for gateway route authentication guardrails."""

from __future__ import annotations

import inspect

from supernova.api import gateway


def test_deep_health_requires_authenticated_user_dependency() -> None:
    signature = inspect.signature(gateway.deep_health)
    parameter = signature.parameters["user_id"]
    assert parameter.default is not inspect._empty


def test_public_health_remains_unauthenticated() -> None:
    signature = inspect.signature(gateway.health)
    assert "user_id" not in signature.parameters
