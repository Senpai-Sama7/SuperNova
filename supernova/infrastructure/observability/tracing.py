"""supernova/infrastructure/observability/tracing.py

Lightweight trace-context propagation for SuperNova.  Binds a ``trace_id``
to the current async task via :mod:`contextvars` so that every LLM call,
memory retrieval, and tool execution emits correlated log records and
Langfuse spans without passing the ID through every function signature.

Usage::

    # At request boundary (middleware or gateway):
    ctx = TraceContext.from_request_headers(request.headers)
    token = ctx.bind()          # sets contextvars for this async task
    try:
        response = await handler(request)
    finally:
        ctx.unbind(token)       # restore previous context

    # Inside any coroutine:
    trace_id = current_trace_id()   # returns bound ID or empty string

    # Langfuse span helper:
    async with trace_span("memory.retrieve", input={"query": q}) as span:
        items = await retriever.retrieve(q)
        span.update(output={"count": len(items)})
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Mapping, Optional

import structlog

logger = structlog.get_logger(__name__)

# Module-level ContextVar — one per async task / request
_TRACE_ID_VAR: ContextVar[str] = ContextVar("trace_id", default="")
_SPAN_STACK_VAR: ContextVar[list] = ContextVar("span_stack", default=[])

_TRACE_HEADER = "X-Trace-Id"
_ALT_HEADERS = ("X-Request-Id", "X-Correlation-Id", "Traceparent")


# ── TraceContext ──────────────────────────────────────────────────────────────


@dataclass
class TraceContext:
    """Holds a single trace identifier for the lifetime of one agent request.

    Attributes:
        trace_id: UUID4 string identifying this trace.
        parent_id: Optional parent span ID for W3C Traceparent compatibility.
        baggage: Arbitrary key-value pairs forwarded across service calls.
    """

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str = ""
    baggage: Dict[str, str] = field(default_factory=dict)

    # ── Factories ───────────────────────────────────────────────────────

    @classmethod
    def new(cls) -> "TraceContext":
        """Create a fresh trace context with a generated UUID4 trace_id."""
        return cls()

    @classmethod
    def from_request_headers(cls, headers: Mapping[str, str]) -> "TraceContext":
        """Extract or generate a trace ID from HTTP request headers.

        Checks ``X-Trace-Id`` first, then ``X-Request-Id``,
        ``X-Correlation-Id``, and ``Traceparent`` (W3C) in that order.
        Generates a fresh UUID4 if no header is present.

        Args:
            headers: Mapping of HTTP header names to values (case-insensitive
                lookup is performed internally).

        Returns:
            :class:`TraceContext` with resolved or generated ``trace_id``.
        """
        lower = {k.lower(): v for k, v in headers.items()}
        trace_id = lower.get(_TRACE_HEADER.lower(), "")
        if not trace_id:
            for alt in _ALT_HEADERS:
                trace_id = lower.get(alt.lower(), "")
                if trace_id:
                    break
        if not trace_id:
            trace_id = str(uuid.uuid4())
        return cls(trace_id=trace_id)

    # ── ContextVar binding ───────────────────────────────────────────────

    def bind(self) -> Token:
        """Bind this trace_id to the current async task's ContextVar.

        Returns:
            A :class:`~contextvars.Token` that must be passed to :meth:`unbind`
            to restore the previous context cleanly.
        """
        token = _TRACE_ID_VAR.set(self.trace_id)
        structlog.contextvars.bind_contextvars(trace_id=self.trace_id)
        return token

    def unbind(self, token: Token) -> None:
        """Restore the previous trace_id after request processing completes."""
        _TRACE_ID_VAR.reset(token)
        structlog.contextvars.unbind_contextvars("trace_id")

    # ── Utility ──────────────────────────────────────────────────────────────

    def to_headers(self) -> Dict[str, str]:
        """Return HTTP headers dict to propagate this trace downstream."""
        headers = {_TRACE_HEADER: self.trace_id}
        headers.update({f"Baggage-{k}": v for k, v in self.baggage.items()})
        return headers


# ── Module-level accessors ────────────────────────────────────────────────────


def current_trace_id() -> str:
    """Return the trace_id bound to the current async task, or empty string."""
    return _TRACE_ID_VAR.get()


# ── Langfuse span context manager ───────────────────────────────────────────


class _NullSpan:
    """No-op span used when Langfuse is unavailable or disabled."""

    def update(self, **kwargs: Any) -> None:  # noqa: ANN401
        pass

    def end(self, **kwargs: Any) -> None:  # noqa: ANN401
        pass


@asynccontextmanager
async def trace_span(
    name: str,
    input: Optional[Dict[str, Any]] = None,  # noqa: A002
    metadata: Optional[Dict[str, Any]] = None,
    langfuse_client: Optional[Any] = None,
) -> AsyncIterator[Any]:
    """Async context manager that creates a Langfuse span for the block.

    Falls back to a no-op span when *langfuse_client* is ``None`` or
    when Langfuse is not importable (avoids hard dependency at import time).

    Args:
        name: Span name, shown in the Langfuse trace waterfall.
        input: Optional input payload to record on the span.
        metadata: Optional metadata dict attached to the span.
        langfuse_client: A ``Langfuse`` instance.  If ``None``, the span
            is silently no-opped.

    Yields:
        The Langfuse span (or ``_NullSpan``) so callers can call
        ``span.update(output=...)`` before the block exits.
    """
    trace_id = current_trace_id()
    span: Any = _NullSpan()

    if langfuse_client is not None:
        try:
            span = langfuse_client.span(
                name=name,
                trace_id=trace_id or None,
                input=input,
                metadata=metadata,
            )
        except Exception as exc:
            logger.warning("Failed to create Langfuse span", name=name, error=str(exc))

    logger.debug("span.start", span_name=name, trace_id=trace_id)
    try:
        yield span
    except Exception:
        try:
            span.end(level="ERROR")
        except Exception:
            pass
        raise
    else:
        try:
            span.end()
        except Exception:
            pass
        logger.debug("span.end", span_name=name, trace_id=trace_id)


# ── ASGI middleware ───────────────────────────────────────────────────────────────


class TraceContextMiddleware:
    """Starlette pure-ASGI middleware that binds a trace ID per request.

    Reads ``X-Trace-Id`` (or fallback headers) from inbound requests,
    binds the ID to the async task's :class:`~contextvars.ContextVar`,
    and injects it into outbound response headers so clients can correlate
    logs with the originating request.

    Unlike :class:`~starlette.middleware.base.BaseHTTPMiddleware`, this
    is a pure ASGI middleware to avoid double-body-read issues with
    streaming responses.

    Args:
        app: The wrapped ASGI application.
    """

    def __init__(self, app: Any) -> None:
        self._app = app

    async def __call__(
        self, scope: dict, receive: Any, send: Any
    ) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        decoded = {
            k.decode("latin-1"): v.decode("latin-1") for k, v in headers.items()
        }
        ctx = TraceContext.from_request_headers(decoded)
        token = ctx.bind()

        async def send_with_trace_header(message: dict) -> None:
            if message["type"] == "http.response.start":
                existing = list(message.get("headers", []))
                existing.append(
                    (
                        _TRACE_HEADER.lower().encode(),
                        ctx.trace_id.encode(),
                    )
                )
                message = {**message, "headers": existing}
            await send(message)

        try:
            await self._app(scope, receive, send_with_trace_header)
        finally:
            ctx.unbind(token)
