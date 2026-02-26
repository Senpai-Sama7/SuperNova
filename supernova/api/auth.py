"""JWT authentication for SuperNova API."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_bearer = HTTPBearer()


def _get_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY not set")
    return secret


def create_access_token(user_id: str, *, expires_delta_hours: float = 24.0) -> str:
    """Create a JWT access token for the given user_id."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + timedelta(hours=expires_delta_hours),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def verify_token(token: str) -> str:
    """Verify a JWT token and return the user_id.

    Raises:
        HTTPException(401): If token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no subject")
        return user_id
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}") from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """FastAPI dependency that extracts and validates JWT from Authorization header."""
    return verify_token(credentials.credentials)
