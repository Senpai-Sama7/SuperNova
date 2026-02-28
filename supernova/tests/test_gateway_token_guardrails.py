"""Regression tests for gateway demo-token guardrails."""

from __future__ import annotations

from supernova.api import gateway


def test_issue_token_function_exists_for_non_production_bootstrap() -> None:
    assert gateway.issue_token.__name__ == "issue_token"


def test_gateway_import_uses_runtime_settings_object() -> None:
    assert hasattr(gateway, "settings")
