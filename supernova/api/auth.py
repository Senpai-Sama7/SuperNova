"""JWT authentication for SuperNova API."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def _get_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY not set")
    return secret



def _request_id_from_headers(headers: object) -> str:
    """Return a stable request id for auth audit events."""
    if headers is not None and hasattr(headers, "get"):
        request_id = headers.get("x-request-id") or headers.get("x-correlation-id")
        if request_id:
            return str(request_id)
    return f"req-{uuid4().hex}"



def _client_host(request: Request | None) -> str:
    if request is None or request.client is None:
        return "unknown"
    return getattr(request.client, "host", None) or "unknown"



def _emit_auth_failure(
    *,
    request: Request | None,
    route: str,
    reason: str,
    auth_method: str,
) -> None:
    payload = {
        "event_type": "auth_failure",
        "event_category": "authentication",
        "audit_layer": "dependency",
        "route_intent": "auth",
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": _request_id_from_headers(request.headers if request is not None else None),
        "route": route,
        "outcome": "denied",
        "disposition": "blocked",
        "severity": "warning",
        "reason": reason,
        "user_id": "anonymous",
        "actor_type": "anonymous",
        "auth_method": auth_method,
        "client_host": _client_host(request),
        "details": {},
    }
    logger.info("auth_failure %s", payload)



def _emit_auth_success(
    *,
    request: Request,
    route: str,
    user_id: str,
    auth_method: str,
) -> None:
    payload = {
        "event_type": "auth_success",
        "event_category": "authentication",
        "audit_layer": "dependency",
        "route_intent": "auth",
        "timestamp": datetime.now(UTC).isoformat(),
        "request_id": _request_id_from_headers(request.headers),
        "route": route,
        "outcome": "granted",
        "disposition": "granted",
        "severity": "info",
        "reason": "validated_bearer_token",
        "user_id": user_id,
        "actor_type": "user",
        "auth_method": auth_method,
        "client_host": _client_host(request),
        "details": {},
    }
    logger.info("auth_success %s", payload)



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
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """FastAPI dependency that extracts and validates JWT from Authorization header."""
    route = request.url.path
    if credentials is None:
        _emit_auth_failure(
            request=request,
            route=route,
            reason="missing_bearer_token",
            auth_method="bearer",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        user_id = verify_token(credentials.credentials)
    except HTTPException as exc:
        _emit_auth_failure(
            request=request,
            route=route,
            reason=str(exc.detail),
            auth_method="bearer",
        )
        raise

    _emit_auth_success(
        request=request,
        route=route,
        user_id=user_id,
        auth_method="bearer",
    )
    return user_id
