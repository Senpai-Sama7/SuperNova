"""supernova/core/security/middleware.py

ASGI middleware that applies ContentSanitizer to every inbound request body
and query parameter before reaching FastAPI route handlers. JSON string
fields are sanitised recursively; binary and non-text payloads are passed
through unchanged.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from supernova.core.security.sanitizer import ContentSanitizer

logger = logging.getLogger(__name__)

_TEXT_CONTENT_TYPES = frozenset({
    "application/json",
    "text/plain",
    "application/x-www-form-urlencoded",
})

# Paths exempt from sanitisation (health probes, static OpenAPI docs)
_DEFAULT_SKIP_PATHS = ["/healthz", "/health", "/metrics", "/docs", "/openapi.json", "/redoc"]


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """ASGI middleware: sanitise inbound text payloads, reject prompt injection.

    Wraps the application so that every request with a text content-type is
    passed through :class:`ContentSanitizer` before route handlers execute.
    Requests flagged as injections receive an HTTP 400 response immediately.

    Args:
        app: Wrapped ASGI application.
        sanitizer: Pre-configured :class:`ContentSanitizer`. If omitted a
            default instance is created with ``block_on_injection=True``.
        skip_paths: Path prefixes to bypass sanitisation entirely.
    """

    def __init__(
        self,
        app: ASGIApp,
        sanitizer: ContentSanitizer | None = None,
        skip_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._sanitizer = sanitizer or ContentSanitizer(block_on_injection=True)
        self._skip_paths: list[str] = skip_paths if skip_paths is not None else _DEFAULT_SKIP_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercept, sanitise, and forward the request."""
        if any(request.url.path.startswith(p) for p in self._skip_paths):
            return await call_next(request)

        content_type = request.headers.get("content-type", "").split(";")[0].strip()
        if content_type not in _TEXT_CONTENT_TYPES:
            return await call_next(request)

        raw_body = await request.body()
        if not raw_body:
            return await call_next(request)

        try:
            sanitised_body = self._sanitise_body(raw_body, content_type, request.url.path)
        except ValueError as exc:
            logger.warning("Sanitisation rejection path=%s reason=%s", request.url.path, exc)
            return JSONResponse(
                status_code=400,
                content={"detail": str(exc), "error": "INPUT_REJECTED"},
            )

        async def _receive() -> dict:
            return {"type": "http.request", "body": sanitised_body, "more_body": False}

        patched_request = Request(request.scope, _receive)
        return await call_next(patched_request)

    def _sanitise_body(self, body: bytes, content_type: str, path: str) -> bytes:
        """Sanitise *body* bytes according to their content type.

        Raises:
            ValueError: When prompt injection is detected and blocking is enabled.
        """
        if content_type == "application/json":
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return body
            sanitised_data = self._sanitise_json(data, path)
            return json.dumps(sanitised_data).encode()

        text = body.decode("utf-8", errors="replace")
        result = self._sanitizer.sanitize(text, context_label=path)
        if result.injection_detected:
            raise ValueError(f"Prompt injection detected in request to {path}")
        return result.text.encode("utf-8")

    def _sanitise_json(self, value: Any, path: str) -> Any:
        """Recursively sanitise string fields within a JSON structure."""
        if isinstance(value, str):
            result = self._sanitizer.sanitize(value, context_label=path)
            if result.injection_detected:
                raise ValueError(f"Prompt injection in JSON field at {path}")
            return result.text
        if isinstance(value, dict):
            return {k: self._sanitise_json(v, f"{path}.{k}") for k, v in value.items()}
        if isinstance(value, list):
            return [self._sanitise_json(item, path) for item in value]
        return value
