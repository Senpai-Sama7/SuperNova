"""Tests for MCP API Endpoints (Task 6.4)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch.dict("os.environ", {"JWT_SECRET_KEY": "test-secret", "ALLOWED_ORIGINS": "*"}):
        from supernova.api.gateway import app
        with TestClient(app) as c:
            yield c


@pytest.fixture
def auth_header(client):
    resp = client.post("/auth/token", json={"user_id": "user-1"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestMCPServers:
    def test_list_servers_no_client(self, client):
        from supernova.api.routes import mcp_routes
        mcp_routes._mcp_client = None
        resp = client.get("/mcp/servers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_servers_with_client(self, client):
        from supernova.api.routes import mcp_routes
        mock_client = MagicMock()
        mock_client.get_server_status.return_value = [
            {"name": "srv1", "healthy": True, "command": "node"}
        ]
        mcp_routes._mcp_client = mock_client
        try:
            resp = client.get("/mcp/servers")
            assert resp.status_code == 200
            assert len(resp.json()) == 1
            assert resp.json()[0]["name"] == "srv1"
        finally:
            mcp_routes._mcp_client = None


class TestMCPTools:
    def test_list_tools_no_client(self, client):
        from supernova.api.routes import mcp_routes
        mcp_routes._mcp_client = None
        resp = client.get("/mcp/tools")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_tools_with_client(self, client):
        from supernova.api.routes import mcp_routes
        mock_client = MagicMock()
        mock_client.list_tools = AsyncMock(return_value=[
            {"type": "function", "function": {"name": "srv__search"}}
        ])
        mcp_routes._mcp_client = mock_client
        try:
            resp = client.get("/mcp/tools")
            assert resp.status_code == 200
            assert len(resp.json()) == 1
        finally:
            mcp_routes._mcp_client = None

    def test_call_tool_bad_format(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mock_client = MagicMock()
        mcp_routes._mcp_client = mock_client
        try:
            resp = client.post("/mcp/tools/badname", json={"arguments": {}}, headers=auth_header)
            assert resp.status_code == 400
        finally:
            mcp_routes._mcp_client = None

    def test_call_tool_success(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value={"content": "ok", "is_error": False})
        mcp_routes._mcp_client = mock_client
        try:
            resp = client.post(
                "/mcp/tools/srv__search",
                json={"arguments": {"q": "test"}},
                headers=auth_header,
            )
            assert resp.status_code == 200
            assert resp.json()["content"] == "ok"
        finally:
            mcp_routes._mcp_client = None

    def test_call_tool_no_client(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mcp_routes._mcp_client = None
        resp = client.post("/mcp/tools/srv__search", json={"arguments": {}}, headers=auth_header)
        assert resp.status_code == 503


class TestSkillsEndpoints:
    def test_list_skills_no_loader(self, client):
        from supernova.api.routes import mcp_routes
        mcp_routes._skill_loader = None
        resp = client.get("/skills")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_skills_with_loader(self, client):
        from supernova.api.routes import mcp_routes
        mock_loader = MagicMock()
        mock_loader.list_skills.return_value = [
            {"name": "mcp-builder", "description": "Build MCP", "active": False}
        ]
        mcp_routes._skill_loader = mock_loader
        try:
            resp = client.get("/skills")
            assert resp.status_code == 200
            assert len(resp.json()) == 1
        finally:
            mcp_routes._skill_loader = None

    def test_activate_skill(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mock_loader = MagicMock()
        mock_loader.activate.return_value = True
        mcp_routes._skill_loader = mock_loader
        try:
            resp = client.post("/skills/mcp-builder/activate", headers=auth_header)
            assert resp.status_code == 200
            assert resp.json()["status"] == "activated"
        finally:
            mcp_routes._skill_loader = None

    def test_activate_skill_not_found(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mock_loader = MagicMock()
        mock_loader.activate.return_value = False
        mcp_routes._skill_loader = mock_loader
        try:
            resp = client.post("/skills/nonexistent/activate", headers=auth_header)
            assert resp.status_code == 404
        finally:
            mcp_routes._skill_loader = None

    def test_deactivate_skill(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mock_loader = MagicMock()
        mcp_routes._skill_loader = mock_loader
        try:
            resp = client.post("/skills/mcp-builder/deactivate", headers=auth_header)
            assert resp.status_code == 200
            assert resp.json()["status"] == "deactivated"
        finally:
            mcp_routes._skill_loader = None

    def test_activate_no_loader(self, client, auth_header):
        from supernova.api.routes import mcp_routes
        mcp_routes._skill_loader = None
        resp = client.post("/skills/test/activate", headers=auth_header)
        assert resp.status_code == 503
