"""Tests for dashboard auth include-point guardrails."""

from __future__ import annotations

from supernova.api.main import app


def test_dashboard_routes_are_mounted_with_auth_dependency() -> None:
    dashboard_routes = [route for route in app.routes if str(getattr(route, "path", "")).startswith("/api/v1/dashboard")]
    assert dashboard_routes, "expected dashboard routes to be mounted"

    dependency_names = {
        getattr(getattr(dep, "dependency", None), "__name__", "")
        for route in dashboard_routes
        for dep in getattr(route, "dependencies", [])
    }
    assert "get_current_user" in dependency_names
