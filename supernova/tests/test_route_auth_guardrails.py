"""Tests for API route authentication guardrails."""

from __future__ import annotations

from supernova.api.routes import mcp_routes, preferences


def test_preferences_router_requires_auth_dependency() -> None:
    dependency_calls = [getattr(dep.dependency, "__name__", "") for dep in preferences.router.dependencies]
    assert "get_current_user" in dependency_calls


def test_mcp_router_requires_auth_dependency() -> None:
    dependency_calls = [getattr(dep.dependency, "__name__", "") for dep in mcp_routes.router.dependencies]
    assert "get_current_user" in dependency_calls
