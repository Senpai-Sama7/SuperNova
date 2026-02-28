"""supernova/core/security/middleware.py

InputSanitizationMiddleware: Starlette ASGI middleware that intercepts all
inbound HTTP request bodies and applies ContentSanitizer before the request
reaches any FastAPI route handler.  Returns HTTP 400 on injection detection.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from supernova.core.security.sanitizer import ContentSanitizer

logger = logging.getLogger(__name__)

_JSON_CONTENT_TYPES = frozenset(
    {
        "application/json",
        "application/json; charset=utf-8",
    }
)
_TEXT_CONTENT_TYPES = frozenset(
    {
        "text/plain",
        "text/plain; charset=utf-8",
        "application/x-www-form-urlencoded",
    }
)


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that sanitises inbound request bodies.

    - JSON bodies: recursively sanitises every string field.
    - Text / form bodies: sanitises the raw string.
    - Other content types: passed through unchanged.
    - Configured skip_paths bypass sanitisation entirely (health, metrics).

    Returns HTTP 400 ``{"error": "SANITIZATION_REJECTED", "detail": "..."}``
    when prompt injection is detected in a JSON or text body.

    Args:
        app: Wrapped ASGI application.
        sanitizer: ContentSanitizer instance.  Defaults to standard config
            with ``block_on_injection=True``.
        skip_paths: URL path prefixes to skip (default: health / docs / metrics).
    """

    def __init__(
        self,
        app: ASGIApp,
        sanitizer: Optional[ContentSanitizer] = None,
        skip_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(app)
        self._sanitizer = sanitizer or ContentSanitizer(block_on_injection=True)
        self._skip_paths: List[str] = skip_paths or [
            "/health",
            "/healthz",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bypass sanitisation for excluded paths
        if any(request.url.path.startswith(p) for p in self._skip_paths):
            return await call_next(request)

        raw_ct = request.headers.get("content-type", "").split(";")[0].strip().lower()

        if raw_ct in _JSON_CONTENT_TYPES or raw_ct in _TEXT_CONTENT_TYPES:
            body = await request.body()
            if body:
                try:
                    sanitized_body = self._sanitize_body(body, raw_ct, request.url.path)
                except ValueError as exc:
                    logger.warning(
                        "Sanitization rejection",
                        path=request.url.path,
                        reason=str(exc),
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "SANITIZATION_REJECTED",
                            "detail": str(exc),
                        },
                    )

                async def receive() -> dict:
                    return {
                        "type": "http.request",
                        "body": sanitized_body,
                        "more_body": False,
                    }

                request = Request(request.scope, receive)

        return await call_next(request)

    def _sanitize_body(self, body: bytes, content_type: str, path: str) -> bytes:
        """Dispatch sanitisation by content type and return cleaned bytes."""
        if content_type in _JSON_CONTENT_TYPES:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return body  # Malformed JSON — let the route handler return 422
            cleaned = self._sanitize_json_value(data, path)
            return json.dumps(cleaned, ensure_ascii=False).encode("utf-8")
        else:
            text = body.decode("utf-8", errors="replace")
            result = self._sanitizer.sanitize(text, context_label=path)
            # block_on_injection is set on the sanitizer; ValueError propagates up
            return result.text.encode("utf-8")

    def _sanitize_json_value(self, value: Any, path: str) -> Any:
        """Recursively sanitise all string values within a JSON structure."""
        if isinstance(value, str):
            result = self._sanitizer.sanitize(value, context_label=path)
            return result.text  # ValueError already raised by sanitizer if injected
        if isinstance(value, dict):
            return {
                k: self._sanitize_json_value(v, f"{path}.{k}") for k, v in value.items()
            }
        if isinstance(value, list):
            return [self._sanitize_json_value(item, path) for item in value]
        return value
