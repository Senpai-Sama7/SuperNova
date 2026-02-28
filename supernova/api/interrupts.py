"""
api/interrupts.py

Human-in-the-loop (HITL) interrupt coordinator for the agent cognitive loop.

Theoretical background:
    LangGraph's interrupt mechanism implements a form of *continuation-passing
    coroutines* at the graph level. When a node is declared in interrupt_before,
    the framework serializes the entire AgentState to the checkpoint store
    (AsyncPostgresSaver / PostgreSQL) before execution, then raises a
    GraphInterrupt exception to the top-level caller.

    The caller has two resumption paths:
      a) graph.invoke(None, config) — resume from the checkpoint (approved)
      b) graph.invoke({"tool_approved": False}, config) — inject a decision
         into the state and resume from the checkpoint (denied)

    This is structurally equivalent to call/cc (call-with-current-continuation)
    in Scheme: the checkpoint IS the reified continuation, and the
    InterruptCoordinator IS the continuation registry. The key property:
    continuations are durable (PostgreSQL-backed), not just in-memory,
    so process crashes during a pause do not lose the pending decision.

    This is architecturally superior to the traditional webhook pattern
    (where you'd store callback URLs and hope the calling process is still
    alive when the user responds) or the polling pattern (where you'd
    repeatedly check a database for the decision, burning CPU and introducing
    latency proportional to poll interval).

Synchronization primitive choice:
    asyncio.Event is the correct primitive here, not asyncio.Queue or
    asyncio.Condition.

    asyncio.Queue is designed for producer-consumer workflows where multiple
    items flow through the channel. Approvals are strictly one-shot:
    one interrupt, one decision. Queue's overhead (FIFO buffer, bounded capacity
    semantics) is unnecessary.

    asyncio.Condition supports multiple waiters on the same predicate, with
    explicit acquire/notify/release semantics. The interrupt coordinator has
    exactly one waiter per session (the suspended graph coroutine) — the
    additional complexity of Condition is not warranted.

    asyncio.Event has O(1) set() and wait() with zero memory allocation in
    the hot path (the event loop's implementation uses a deque of futures
    that are resolved directly). It naturally implements exactly the semantics
    we need: zero → one state transition, with waiting coroutines notified
    on the transition.

    The timeout semantics are critical for production safety:
    asyncio.wait_for(event.wait(), timeout=N) raises asyncio.TimeoutError
    if the event is not set within N seconds. Without this, a user who
    ignores an approval notification would permanently suspend a coroutine,
    leaking memory and eventually exhausting the event loop's coroutine pool
    in high-concurrency scenarios.

Risk-stratified auto-resolution on timeout:
    The timeout policy deliberately diverges by risk level:
      - "low" risk: auto-approve on timeout. The cost of a missed low-risk
        tool call is low, and blocking on timeout would degrade the user
        experience for tasks the user doesn't care to supervise.
      - "high" / "critical" risk: auto-deny on timeout. The cost of an
        unsupervised high-risk action (file deletion, email send, API call
        with side effects) exceeds the cost of an interrupted task.

    This asymmetric timeout policy implements a formal risk-weighted decision
    rule: E[cost of auto-approve] = P(harmful) × cost_harm vs.
    E[cost of auto-deny] = P(benign) × cost_interruption. For high-risk
    tools, cost_harm dominates; for low-risk tools, cost_interruption dominates.

IronClaw correspondence:
    IronClaw implements an analogous pattern via its "endpoint allowlisting"
    and "credential injection at host boundary" — rather than pausing for
    human approval, it applies deterministic security policies at the WASM
    host layer. The Python approach (HITL) and the Rust approach (policy
    enforcement) are complementary, not alternatives: HITL handles edge cases
    that static policy cannot anticipate; policy handles cases where HITL
    latency is unacceptable.
"""

from __future__ import annotations

import asyncio
import json
import logging
import platform
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """
    Risk classification for tool executions requiring HITL approval.

    The taxonomy is intentionally coarse (4 levels) to avoid analysis paralysis
    in classification. More granular risk taxonomies tend to produce inconsistent
    classifications and edge-case disputes; the operational goal is to distinguish
    "definitely tell the user" from "definitely don't block on this."

    Classification guidance:
        LOW      — Read-only, reversible, no external side effects
                   Examples: web_search, file_read, memory_query
        MEDIUM   — Write to local state, potentially slow/expensive
                   Examples: file_write, code_execute, API_read
        HIGH     — External side effects, hard to reverse, may affect others
                   Examples: send_email, post_to_service, file_delete
        CRITICAL — Irreversible, financial, or security-relevant
                   Examples: make_payment, delete_database, grant_permissions
    """
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


# Timeout in seconds before auto-resolution fires, per risk level.
# Lower for LOW (fast auto-approve) and higher for CRITICAL (user has time to see it).
TIMEOUT_BY_RISK: dict[str, float] = {
    RiskLevel.LOW.value:      30.0,
    RiskLevel.MEDIUM.value:   120.0,
    RiskLevel.HIGH.value:     300.0,
    RiskLevel.CRITICAL.value: 600.0,
}

# Auto-resolution policy on timeout: True = approve, False = deny
AUTO_RESOLVE_ON_TIMEOUT: dict[str, bool] = {
    RiskLevel.LOW.value:      True,    # Low risk: proceed if user doesn't respond
    RiskLevel.MEDIUM.value:   False,   # Medium: err on caution
    RiskLevel.HIGH.value:     False,
    RiskLevel.CRITICAL.value: False,
}


@dataclass
class PendingApproval:
    """
    A pending HITL approval request.

    The event field is the synchronization primitive — the suspended graph
    coroutine calls await event.wait() and blocks without consuming CPU
    (the coroutine is parked in the event loop's waiting set, not spinning).

    The decision field is initially None and set atomically by submit_decision().
    Reading decision before event.is_set() is undefined behavior — the coordinator
    enforces this ordering via the event protocol.
    """
    thread_id:   str
    tool_name:   str
    tool_args:   dict
    risk_level:  str
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event:       asyncio.Event = field(default_factory=asyncio.Event)
    decision:    bool | None = None


class ApprovalResult(NamedTuple):
    approved:    bool
    source:      str    # "user", "timeout_auto_approve", "timeout_auto_deny", "error"
    latency_ms:  float


class InterruptCoordinator:
    """
    Coordinates HITL approval requests between the agent graph and human interfaces.

    The coordinator is a singleton service (one instance per agent process).
    It maintains a registry of pending approvals keyed by thread_id (session ID).
    Each approval is a one-shot event: approved, denied, or timed out.

    The coordinator bridges three different concurrency domains:
      1. The LangGraph graph execution (async coroutine, blocked on Event)
      2. The WebSocket handler (async coroutine, receives user JSON decision)
      3. The OS notification system (subprocess call, one-shot)

    All three operate within the same asyncio event loop, so coordination
    requires no locks — asyncio's cooperative multitasking ensures that
    Event.set() and Event.wait() are sequentially consistent.

    Distributed deployment note:
        This implementation assumes a single-process deployment where the
        graph coroutine and WebSocket handler share the same event loop.
        For multi-process or multi-machine deployments (e.g., graph workers
        on separate nodes), replace asyncio.Event with a Redis pub/sub channel
        or a shared-memory IPC mechanism. The interface remains identical;
        only the synchronization primitive changes.
    """

    def __init__(
        self,
        websocket_broadcaster: Any | None = None,   # For in-app approval UI
        default_timeout_override: float | None = None,
    ) -> None:
        self._pending: dict[str, PendingApproval] = {}
        self.broadcaster    = websocket_broadcaster
        self._timeout_override = default_timeout_override

    async def request_approval(
        self,
        thread_id:  str,
        tool_name:  str,
        tool_args:  dict,
        risk_level: str | RiskLevel = RiskLevel.LOW,
    ) -> ApprovalResult:
        """
        Request human approval for a tool execution.

        This coroutine suspends the caller until one of three resolution events:
          1. Human approves via WebSocket or OS notification acknowledgment
          2. Human denies
          3. Timeout: auto-resolution per TIMEOUT_BY_RISK policy

        The suspension is cooperative (asyncio.wait_for), not preemptive.
        The event loop remains fully responsive to other sessions while this
        session waits for approval.

        Concurrent approval requests:
            If two sessions simultaneously request approval for the same thread_id
            (unusual but theoretically possible in parallel agentic workflows),
            the second request overwrites the first pending approval. This is
            intentionally simplistic — proper parallel HITL would require an
            approval queue per thread rather than a single event per thread.
            For the personal-agent use case (one user, sequential conversations),
            this is not a concern.
        """
        risk_str = risk_level.value if isinstance(risk_level, RiskLevel) else risk_level
        timeout  = self._timeout_override or TIMEOUT_BY_RISK.get(risk_str, 120.0)

        approval = PendingApproval(
            thread_id   = thread_id,
            tool_name   = tool_name,
            tool_args   = tool_args,
            risk_level  = risk_str,
        )
        self._pending[thread_id] = approval

        start_ms = _monotonic_ms()

        # Fire both notification channels concurrently (non-blocking)
        # We don't await them — notification delivery is best-effort
        asyncio.create_task(
            self._notify_os(tool_name, tool_args, risk_str)
        )
        if self.broadcaster:
            asyncio.create_task(
                self._notify_websocket(thread_id, tool_name, tool_args, risk_str, timeout)
            )

        logger.info(
            "HITL approval requested: thread=%s, tool=%s, risk=%s, timeout=%.0fs",
            thread_id, tool_name, risk_str, timeout
        )

        try:
            await asyncio.wait_for(approval.event.wait(), timeout=timeout)

            decision = approval.decision
            latency  = _monotonic_ms() - start_ms

            logger.info(
                "HITL approval %s by user: thread=%s, tool=%s, latency=%.0fms",
                "approved" if decision else "denied", thread_id, tool_name, latency
            )

            return ApprovalResult(
                approved   = bool(decision),
                source     = "user",
                latency_ms = latency,
            )

        except asyncio.TimeoutError:
            auto_approve = AUTO_RESOLVE_ON_TIMEOUT.get(risk_str, False)
            latency      = _monotonic_ms() - start_ms

            logger.warning(
                "HITL timeout after %.0fms: thread=%s, tool=%s, risk=%s, auto_resolve=%s",
                latency, thread_id, tool_name, risk_str, "APPROVE" if auto_approve else "DENY"
            )

            # Notify the UI that the timeout resolved
            if self.broadcaster:
                asyncio.create_task(
                    self.broadcaster.send(thread_id, {
                        "type":         "approval_timeout",
                        "tool":         tool_name,
                        "risk_level":   risk_str,
                        "auto_resolved": "approved" if auto_approve else "denied",
                    })
                )

            return ApprovalResult(
                approved   = auto_approve,
                source     = "timeout_auto_approve" if auto_approve else "timeout_auto_deny",
                latency_ms = latency,
            )

        finally:
            # Always clean up the pending approval entry to prevent memory leaks.
            # del is safe even if the key was already removed by a concurrent call.
            self._pending.pop(thread_id, None)

    async def submit_decision(
        self,
        thread_id: str,
        approved:  bool,
        user_id:   str | None = None,
    ) -> bool:
        """
        Resolve a pending approval. Called by the WebSocket message handler
        when the user clicks Approve or Deny in the UI.

        Returns True if the decision was recorded, False if no pending approval
        exists for thread_id (e.g., it already timed out).

        The atomicity guarantee: between setting approval.decision and calling
        approval.event.set(), no coroutine can observe a None decision with the
        event set, because asyncio is single-threaded cooperative. The event
        notifies the waiting coroutine, which then reads decision — the
        read always follows the write.
        """
        approval = self._pending.get(thread_id)
        if not approval:
            logger.warning(
                "submit_decision called for unknown/expired thread_id: %s", thread_id
            )
            return False

        approval.decision = approved
        approval.event.set()   # Unblock the waiting coroutine

        logger.debug(
            "Decision submitted: thread=%s, approved=%s, user=%s",
            thread_id, approved, user_id or "anonymous"
        )
        return True

    def get_pending_approvals(self) -> list[dict]:
        """
        Return all currently pending approvals.
        Used by admin endpoints and WebSocket initial state sync.
        """
        return [
            {
                "thread_id":    a.thread_id,
                "tool_name":    a.tool_name,
                "tool_args":    a.tool_args,
                "risk_level":   a.risk_level,
                "requested_at": a.requested_at,
                "timeout_at": (
                    TIMEOUT_BY_RISK.get(a.risk_level, 120)
                ),
            }
            for a in self._pending.values()
        ]

    async def _notify_os(
        self,
        tool_name:  str,
        tool_args:  dict,
        risk_level: str,
    ) -> None:
        """
        Send a native OS notification for the pending approval.

        Platform support:
            macOS: osascript with AppleScript display notification
                   Supports: title, body, sound name
                   Limitations: no actionable buttons in standard notifications
                   (actionable buttons require a macOS app bundle with UserNotifications
                   entitlements — out of scope for this Python service)

            Linux: notify-send (libnotify)
                   Supports: --urgency (low/normal/critical), title, body
                   Requires: libnotify-bin package, DBUS session for desktop notifications
                   Limitations: varies by notification daemon (dunst, mako, GNOME)

            Windows: winrt.windows.ui.notifications (via winsdk / pywinrt)
                     Not implemented here — left as an exercise.
                     Alternatively: win10toast or plyer for a cross-platform abstraction.

        The sound alert on macOS is critical UX: without it, the notification
        may go unnoticed if the user is in a different virtual desktop. "Ping"
        is the most neutral system sound; "Hero" or "Sosumi" convey higher urgency
        for critical risk levels.
        """
        body  = _summarize_args(tool_args)
        title = f"🤖 Agent wants to: {tool_name}"

        # Risk level to urgency/sound mapping
        if risk_level in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value):
            urgency    = "critical"
            mac_sound  = "Hero"
        elif risk_level == RiskLevel.MEDIUM.value:
            urgency    = "normal"
            mac_sound  = "Ping"
        else:
            urgency    = "low"
            mac_sound  = "Tink"

        try:
            os_name = platform.system()

            if os_name == "Darwin":
                script = (
                    f'display notification "{_escape_applescript(body)}" '
                    f'with title "{_escape_applescript(title)}" '
                    f'sound name "{mac_sound}"'
                )
                proc = await asyncio.create_subprocess_exec(
                    "osascript", "-e", script,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
                if proc.returncode != 0 and stderr:
                    logger.debug("osascript warning: %s", stderr.decode().strip())

            elif os_name == "Linux":
                proc = await asyncio.create_subprocess_exec(
                    "notify-send",
                    f"--urgency={urgency}",
                    f"--expire-time={int(TIMEOUT_BY_RISK.get(risk_level, 120) * 1000)}",
                    "--app-name=SuperNova Agent",
                    title,
                    body,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=5.0)

            else:
                # Windows or unknown: log only
                logger.info("OS notification (unsupported platform): %s — %s", title, body)

        except asyncio.TimeoutError:
            logger.warning("OS notification subprocess timed out for tool: %s", tool_name)
        except FileNotFoundError as e:
            # osascript or notify-send not found — log and continue
            logger.debug("Notification binary not found: %s", e)
        except Exception as e:
            logger.warning("OS notification failed: %s", e)

    async def _notify_websocket(
        self,
        thread_id:  str,
        tool_name:  str,
        tool_args:  dict,
        risk_level: str,
        timeout:    float,
    ) -> None:
        """
        Push an approval_request event to the WebSocket client.

        The payload includes all information needed for the frontend to render
        a meaningful approval dialog:
          - tool: the tool being requested
          - args: the arguments (may be displayed as formatted JSON)
          - risk_level: drives the UI color coding and urgency styling
          - expires_in_seconds: used to show a countdown timer in the UI,
            so the user understands the auto-resolution will fire

        The frontend should respond with a POST or WebSocket message:
            {"type": "approval_response", "thread_id": "...", "approved": true/false}
        which routes to submit_decision() via the WebSocket handler.
        """
        if not self.broadcaster:
            return
        try:
            await self.broadcaster.send(thread_id, {
                "type":             "approval_request",
                "tool":             tool_name,
                "args":             tool_args,
                "args_summary":     _summarize_args(tool_args),
                "risk_level":       risk_level,
                "expires_in_seconds": int(timeout),
                "auto_resolve":     AUTO_RESOLVE_ON_TIMEOUT.get(risk_level, False),
                "requested_at":     datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning("WebSocket notification failed for thread %s: %s", thread_id, e)


# ── FastAPI integration ────────────────────────────────────────────────────────

def create_interrupt_router(coordinator: InterruptCoordinator) -> Any:
    """
    Create a FastAPI APIRouter for HITL approval management.

    Mount this router on your main FastAPI app:
        app.include_router(create_interrupt_router(coordinator), prefix="/hitl")

    Endpoints:
        GET  /hitl/pending          — List all pending approvals (for admin UI)
        POST /hitl/{thread_id}/approve  — Approve a pending tool call
        POST /hitl/{thread_id}/deny     — Deny a pending tool call
    """
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel

    router = APIRouter(tags=["hitl"])

    class DecisionPayload(BaseModel):
        user_id: str | None = None
        reason:  str | None = None   # Optional: user-provided reason for audit log

    @router.get("/pending")
    async def list_pending_approvals() -> list[dict]:
        return coordinator.get_pending_approvals()

    @router.post("/{thread_id}/approve")
    async def approve_tool_call(thread_id: str, body: DecisionPayload) -> dict:
        recorded = await coordinator.submit_decision(thread_id, True, body.user_id)
        if not recorded:
            raise HTTPException(
                status_code=404,
                detail=f"No pending approval for thread_id={thread_id}. "
                       f"It may have already timed out."
            )
        return {"status": "approved", "thread_id": thread_id}

    @router.post("/{thread_id}/deny")
    async def deny_tool_call(thread_id: str, body: DecisionPayload) -> dict:
        recorded = await coordinator.submit_decision(thread_id, False, body.user_id)
        if not recorded:
            raise HTTPException(
                status_code=404,
                detail=f"No pending approval for thread_id={thread_id}. "
                       f"It may have already timed out."
            )
        return {"status": "denied", "thread_id": thread_id}

    return router


# ── Utility functions ──────────────────────────────────────────────────────────

def _summarize_args(args: dict, max_len: int = 120) -> str:
    """
    Generate a human-readable one-line summary of tool arguments.

    The summary is displayed in OS notifications (limited screen real estate)
    and WebSocket payloads (displayed in the approval dialog subtitle).
    """
    if not args:
        return "no arguments"
    parts = []
    for k, v in list(args.items())[:3]:
        v_str = str(v)
        if len(v_str) > 40:
            v_str = v_str[:37] + "..."
        parts.append(f"{k}={v_str!r}")
    summary = ", ".join(parts)
    if len(args) > 3:
        summary += f" (+{len(args) - 3} more)"
    return summary[:max_len]


def _escape_applescript(text: str) -> str:
    """
    Escape special characters for AppleScript string literals.

    AppleScript uses double quotes for strings with backslash as the escape
    character. Characters that must be escaped: double quote, backslash.
    Control characters are replaced with spaces to prevent shell injection
    via the osascript subprocess call.
    """
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    # Remove control characters that would break AppleScript parsing
    text = "".join(c if ord(c) >= 32 else " " for c in text)
    return text[:500]   # AppleScript display notification has a practical length limit


def _monotonic_ms() -> float:
    """Return current monotonic time in milliseconds."""
    import time
    return time.monotonic() * 1000
