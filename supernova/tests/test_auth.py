"""Tests for Authentication (Task 6.1)."""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException


class _FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key.lower(), default)


class TestAuth:
    SECRET = "test-secret-key-for-jwt"

    def test_create_access_token(self):
        from supernova.api.auth import create_access_token
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            token = create_access_token("user-123")
        assert isinstance(token, str)
        payload = jwt.decode(token, self.SECRET, algorithms=["HS256"])
        assert payload["sub"] == "user-123"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_custom_expiry(self):
        from supernova.api.auth import create_access_token
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            token = create_access_token("user-1", expires_delta_hours=1.0)
        payload = jwt.decode(token, self.SECRET, algorithms=["HS256"])
        # Expiry should be ~1 hour from now
        assert payload["exp"] - payload["iat"] == pytest.approx(3600, abs=5)

    def test_verify_token_valid(self):
        from supernova.api.auth import create_access_token, verify_token
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            token = create_access_token("user-456")
            user_id = verify_token(token)
        assert user_id == "user-456"

    def test_verify_token_expired(self):
        from supernova.api.auth import verify_token
        payload = {"sub": "user-1", "exp": time.time() - 100}
        token = jwt.encode(payload, self.SECRET, algorithm="HS256")
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_invalid(self):
        from supernova.api.auth import verify_token
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            with pytest.raises(HTTPException) as exc_info:
                verify_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_verify_token_no_subject(self):
        from supernova.api.auth import verify_token
        payload = {"exp": time.time() + 3600}  # No "sub" field
        token = jwt.encode(payload, self.SECRET, algorithm="HS256")
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
        assert exc_info.value.status_code == 401

    def test_no_secret_raises(self):
        from supernova.api.auth import create_access_token
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
                create_access_token("user-1")

    @pytest.mark.asyncio
    async def test_get_current_user(self):
        from supernova.api.auth import create_access_token, get_current_user
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            token = create_access_token("user-789")
            creds = MagicMock()
            creds.credentials = token
            request = SimpleNamespace(
                url=SimpleNamespace(path="/metrics"),
                headers=_FakeHeaders({"x-request-id": "req-123"}),
                client=SimpleNamespace(host="127.0.0.1"),
            )
            user_id = await get_current_user(request, creds)
        assert user_id == "user-789"

    @pytest.mark.asyncio
    async def test_get_current_user_success_is_audited(self, monkeypatch: pytest.MonkeyPatch):
        from supernova.api.auth import create_access_token, get_current_user

        calls: list[tuple] = []

        def fake_info(*args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr("supernova.api.auth.logger.info", fake_info)
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            token = create_access_token("user-789")
            creds = MagicMock()
            creds.credentials = token
            request = SimpleNamespace(
                url=SimpleNamespace(path="/metrics"),
                headers=_FakeHeaders({"x-request-id": "req-123"}),
                client=SimpleNamespace(host="127.0.0.1"),
            )
            user_id = await get_current_user(request, creds)

        assert user_id == "user-789"
        payload = calls[0][0][1]
        assert payload["event_type"] == "auth_success"
        assert payload["event_category"] == "authentication"
        assert payload["audit_layer"] == "dependency"
        assert payload["route_intent"] == "auth"
        assert payload["route"] == "/metrics"
        assert payload["request_id"] == "req-123"
        assert payload["outcome"] == "granted"
        assert payload["user_id"] == "user-789"
        assert payload["auth_method"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid(self):
        from supernova.api.auth import get_current_user
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            creds = MagicMock()
            creds.credentials = "bad-token"
            request = SimpleNamespace(
                url=SimpleNamespace(path="/metrics"),
                headers=_FakeHeaders({"x-request-id": "req-123"}),
                client=SimpleNamespace(host="127.0.0.1"),
            )
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, creds)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_bearer_token_is_audited(self, monkeypatch: pytest.MonkeyPatch):
        from supernova.api.auth import get_current_user

        calls: list[tuple] = []

        def fake_info(*args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr("supernova.api.auth.logger.info", fake_info)
        request = SimpleNamespace(
            url=SimpleNamespace(path="/admin/fleet"),
            headers=_FakeHeaders({"x-request-id": "req-123"}),
            client=SimpleNamespace(host="127.0.0.1"),
        )

        with pytest.raises(HTTPException, match="Missing bearer token"):
            await get_current_user(request, None)

        payload = calls[0][0][1]
        assert payload["event_type"] == "auth_failure"
        assert payload["event_category"] == "authentication"
        assert payload["audit_layer"] == "dependency"
        assert payload["route_intent"] == "auth"
        assert payload["route"] == "/admin/fleet"
        assert payload["request_id"] == "req-123"
        assert payload["reason"] == "missing_bearer_token"
        assert payload["auth_method"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_is_audited(self, monkeypatch: pytest.MonkeyPatch):
        from supernova.api.auth import get_current_user

        calls: list[tuple] = []

        def fake_info(*args, **kwargs):
            calls.append((args, kwargs))

        monkeypatch.setattr("supernova.api.auth.logger.info", fake_info)
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            creds = MagicMock()
            creds.credentials = "bad-token"
            request = SimpleNamespace(
                url=SimpleNamespace(path="/admin/costs"),
                headers=_FakeHeaders({"x-correlation-id": "corr-123"}),
                client=SimpleNamespace(host="127.0.0.1"),
            )
            with pytest.raises(HTTPException):
                await get_current_user(request, creds)

        payload = calls[0][0][1]
        assert payload["event_type"] == "auth_failure"
        assert payload["event_category"] == "authentication"
        assert payload["audit_layer"] == "dependency"
        assert payload["route_intent"] == "auth"
        assert payload["route"] == "/admin/costs"
        assert payload["request_id"] == "corr-123"
        assert payload["outcome"] == "denied"
        assert payload["auth_method"] == "bearer"
