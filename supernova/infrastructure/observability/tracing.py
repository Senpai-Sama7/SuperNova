"""supernova/infrastructure/observability/tracing.py

Trace context propagation for SuperNova agent calls.

Provides :class:`TraceContext` — a lightweight, immutable span descriptor —
and :class:`LangfuseTracer`, which wraps Langfuse generation / span calls and
auto-propagates the trace_id from :class:`~supernova.core.security.trusted_context.TrustedContext`
across LLM calls, memory retrievals, and tool executions.

Usage::

    tracer = LangfuseTracer.from_env()   # reads LANGFUSE_* env vars
    async with tracer.span(ctx, name="memory_retrieve") as span:
        items = await retriever.retrieve(query)
        span.set_output({"count": len(items)})

"""
from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TraceContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TraceContext:
    """Immutable descriptor for a single distributed trace span.

    Attributes:
        trace_id: Root trace identifier, propagated from TrustedContext.
        span_id: Unique identifier for this span.
        parent_span_id: Parent span’s ID, or empty string for root spans.
        name: Human-readable operation name.
        session_id: Agent session identifier for Langfuse grouping.
        user_id: Authenticated user identifier (may be empty).
        started_at: Unix timestamp when the span was opened.
        metadata: Arbitrary key–value pairs attached at creation time.
    """

    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    parent_span_id: str = ""
    name: str = "unnamed_span"
    session_id: str = ""
    user_id: str = ""
    started_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def child(self, name: str, **metadata: Any) -> "TraceContext":
        """Create a child span inheriting this span’s trace_id and session."""
        return TraceContext(
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
            name=name,
            session_id=self.session_id,
            user_id=self.user_id,
            metadata=metadata,
        )


# ---------------------------------------------------------------------------
# ActiveSpan — mutable result collector for use inside `async with` blocks
# ---------------------------------------------------------------------------


class ActiveSpan:
    """Mutable span handle available inside a ``tracer.span(...)`` context.

    Callers attach input/output/error metadata before the context exits so
    that :class:`LangfuseTracer` can flush a complete span record.

    Args:
        ctx: Immutable :class:`TraceContext` for this span.
    """

    def __init__(self, ctx: TraceContext) -> None:
        self._ctx = ctx
        self._input: Any = None
        self._output: Any = None
        self._error: Optional[str] = None
        self._extra: Dict[str, Any] = {}

    @property
    def context(self) -> TraceContext:
        return self._ctx

    def set_input(self, data: Any) -> None:
        """Attach input data to this span (will be sent to Langfuse)."""
        self._input = data

    def set_output(self, data: Any) -> None:
        """Attach output data to this span."""
        self._output = data

    def set_error(self, message: str) -> None:
        """Mark this span as failed with an error message."""
        self._error = message

    def annotate(self, **kwargs: Any) -> None:
        """Attach arbitrary key–value annotations."""
        self._extra.update(kwargs)


# ---------------------------------------------------------------------------
# LangfuseTracer
# ---------------------------------------------------------------------------


class LangfuseTracer:
    """Wraps Langfuse SDK calls with automatic trace-context propagation.

    Gracefully degrades to no-op logging when the Langfuse SDK is not
    installed or ``LANGFUSE_PUBLIC_KEY`` / ``LANGFUSE_SECRET_KEY`` are unset.

    Args:
        public_key: Langfuse project public key.
        secret_key: Langfuse project secret key.
        host: Langfuse API host. Defaults to ``https://cloud.langfuse.com``.
        enabled: Master on/off switch. Default True.
    """

    def __init__(
        self,
        public_key: str = "",
        secret_key: str = "",
        host: str = "https://cloud.langfuse.com",
        enabled: bool = True,
    ) -> None:
        self._enabled = enabled and bool(public_key) and bool(secret_key)
        self._client: Any = None

        if self._enabled:
            try:
                from langfuse import Langfuse  # type: ignore[import]

                self._client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host,
                )
                logger.info("LangfuseTracer initialised", extra={"host": host})
            except ImportError:
                logger.warning(
                    "langfuse package not installed — tracing disabled; "
                    "run `pip install langfuse` to enable"
                )
                self._enabled = False

    @classmethod
    def from_env(cls) -> "LangfuseTracer":
        """Construct a tracer from environment variables.

        Reads:
            ``LANGFUSE_PUBLIC_KEY``, ``LANGFUSE_SECRET_KEY``,
            ``LANGFUSE_HOST`` (optional), ``LANGFUSE_ENABLED`` (``"true"``/``"false"``)
        """
        return cls(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            enabled=os.getenv("LANGFUSE_ENABLED", "true").lower() == "true",
        )

    @asynccontextmanager
    async def span(
        self,
        parent: TraceContext,
        name: str,
        **metadata: Any,
    ) -> AsyncIterator[ActiveSpan]:
        """Async context manager that opens, yields, and flushes a child span.

        Usage::

            async with tracer.span(root_ctx, "tool_execution", tool_id="bash") as s:
                result = await execute_tool(...)
                s.set_output(result)

        Args:
            parent: Parent :class:`TraceContext` (span becomes a child).
            name: Human-readable span name.
            **metadata: Additional key–value metadata attached to the span.

        Yields:
            :class:`ActiveSpan` for attaching input/output/error data.
        """
        child_ctx = parent.child(name, **metadata)
        active = ActiveSpan(child_ctx)
        lf_span: Any = None

        if self._enabled and self._client is not None:
            try:
                lf_span = self._client.span(
                    trace_id=child_ctx.trace_id,
                    parent_observation_id=child_ctx.parent_span_id or None,
                    name=name,
                    session_id=child_ctx.session_id or None,
                    user_id=child_ctx.user_id or None,
                    metadata={**child_ctx.metadata, **metadata},
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("langfuse span open failed: %s", exc)

        try:
            yield active
        except Exception as exc:
            active.set_error(str(exc))
            raise
        finally:
            duration_ms = (time.time() - child_ctx.started_at) * 1000.0
            if lf_span is not None:
                try:
                    lf_span.end(
                        input=active._input,
                        output=active._output,
                        level="ERROR" if active._error else "DEFAULT",
                        status_message=active._error,
                        metadata={**active._extra, "duration_ms": duration_ms},
                    )
                except Exception as exc:  # pragma: no cover
                    logger.warning("langfuse span close failed: %s", exc)
            else:
                logger.debug(
                    "span",
                    name=name,
                    trace_id=child_ctx.trace_id,
                    duration_ms=round(duration_ms, 2),
                    error=active._error,
                )

    def trace_context_for(
        self,
        session_id: str,
        user_id: str = "",
        trace_id: Optional[str] = None,
        name: str = "agent_turn",
        **metadata: Any,
    ) -> TraceContext:
        """Create a root TraceContext for a new agent turn.

        Args:
            session_id: Agent session identifier.
            user_id: Authenticated user identifier.
            trace_id: Reuse an existing trace ID (e.g. from TrustedContext).
                Generates a new UUID if omitted.
            name: Top-level span name.
            **metadata: Extra metadata attached to the root span.

        Returns:
            A root :class:`TraceContext` suitable for passing to :meth:`span`.
        """
        return TraceContext(
            trace_id=trace_id or uuid.uuid4().hex,
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )

    @property
    def enabled(self) -> bool:
        """True if Langfuse is configured and the SDK is available."""
        return self._enabled

    def flush(self) -> None:
        """Flush all buffered Langfuse events synchronously (use at shutdown)."""
        if self._enabled and self._client is not None:
            try:
                self._client.flush()
            except Exception as exc:  # pragma: no cover
                logger.warning("langfuse flush failed: %s", exc)
