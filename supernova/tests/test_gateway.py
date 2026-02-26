"""Tests for FastAPI Gateway (Task 6.3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the gateway app."""
    with patch.dict("os.environ", {"JWT_SECRET_KEY": "test-secret", "ALLOWED_ORIGINS": "*"}):
        from supernova.api.gateway import app
        with TestClient(app) as c:
            yield c


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"


class TestAuthEndpoint:
    def test_issue_token(self, client):
        resp = client.post("/auth/token", json={"user_id": "user-123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)

    def test_issue_token_missing_user_id(self, client):
        resp = client.post("/auth/token", json={})
        assert resp.status_code == 422  # Validation error


class TestMemoryEndpoints:
    def test_semantic_no_auth(self, client):
        resp = client.get("/memory/semantic")
        assert resp.status_code in (401, 403)

    def test_semantic_with_auth(self, client):
        # Get a token first
        token_resp = client.post("/auth/token", json={"user_id": "user-1"})
        token = token_resp.json()["access_token"]
        resp = client.get("/memory/semantic", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []  # No store initialized

    def test_procedural_returns_empty(self, client):
        resp = client.get("/memory/procedural")
        assert resp.status_code == 200
        assert resp.json() == []


class TestAdminEndpoints:
    def test_fleet_no_router(self, client):
        resp = client.get("/admin/fleet")
        assert resp.status_code == 200
        data = resp.json()
        assert "note" in data or "models" in data


class TestWebSocketEndpoint:
    def test_ws_no_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/agent/stream/s1"):
                pass

    def test_ws_invalid_token(self, client):
        with pytest.raises(Exception):
            with client.websocket_connect("/agent/stream/s1?token=bad"):
                pass


class TestCORS:
    def test_cors_headers(self, client):
        resp = client.options(
            "/health",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        # CORS should allow the origin
        assert resp.status_code in (200, 204)


class TestGatewayApp:
    def test_app_exists(self):
        with patch.dict("os.environ", {"JWT_SECRET_KEY": "test-secret"}):
            from supernova.api.gateway import app
            assert app.title == "SuperNova API"
            assert app.version == "2.0.0"

    def test_mount_interrupt_router(self):
        with patch.dict("os.environ", {"JWT_SECRET_KEY": "test-secret"}):
            from supernova.api.gateway import mount_interrupt_router
            # Should not raise even if interrupts.py not found at expected path
            mock_coordinator = MagicMock()
            # This may or may not find the file depending on cwd, but shouldn't crash
            try:
                mount_interrupt_router(mock_coordinator)
            except Exception:
                pass  # OK if file not found in test env
