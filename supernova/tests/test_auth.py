"""Tests for Authentication (Task 6.1)."""

from __future__ import annotations

import time
from unittest.mock import patch, MagicMock

import jwt
import pytest
from fastapi import HTTPException


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
            user_id = await get_current_user(creds)
        assert user_id == "user-789"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid(self):
        from supernova.api.auth import get_current_user
        with patch.dict("os.environ", {"JWT_SECRET_KEY": self.SECRET}):
            creds = MagicMock()
            creds.credentials = "bad-token"
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)
        assert exc_info.value.status_code == 401
