"""supernova/core/security/trusted_context.py

Immutable TrustedContext snapshot: verified caller identity, permission scope,
and session-level trust metadata.  Used by the tool execution gate and approval
interrupt to make policy decisions without ambient/mutable state.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import FrozenSet


class TrustLevel(IntEnum):
    """Ordered trust tiers from untrusted to internal system."""

    UNTRUSTED = 0
    GUEST = 1
    USER = 2
    POWER_USER = 3
    ADMIN = 4
    SYSTEM = 5


@dataclass(frozen=True)
class TrustedContext:
    """Immutable snapshot of trust state for a single agent request.

    All fields are resolved from verified sources (JWT claims, session state,
    prior approval records) at construction time.  No field is mutated after
    creation, making this safe to pass freely across async task boundaries.

    Attributes:
        session_id: Unique identifier for the active agent session.
        user_id: Authenticated user subject.  Empty string if unauthenticated.
        trust_level: Resolved TrustLevel for this request.
        approved_tool_ids: Tool IDs pre-approved via the approval flow.
        ip_address: Client IP for rate-limit and anomaly correlation.
        created_at: Unix timestamp when this context was minted.
        trace_id: Distributed trace identifier for observability correlation.
    """

    session_id: str
    user_id: str
    trust_level: TrustLevel
    approved_tool_ids: FrozenSet[str] = field(default_factory=frozenset)
    ip_address: str = ""
    created_at: float = field(default_factory=time.time)
    trace_id: str = ""

    # ── Factory methods ──────────────────────────────────────────────────────

    @classmethod
    def unauthenticated(cls, session_id: str, ip_address: str = "") -> "TrustedContext":
        """Mint a minimal GUEST-level context for unauthenticated sessions."""
        return cls(
            session_id=session_id,
            user_id="",
            trust_level=TrustLevel.GUEST,
            ip_address=ip_address,
        )

    @classmethod
    def from_jwt_claims(
        cls,
        claims: dict,
        session_id: str,
        approved_tool_ids: FrozenSet[str] = frozenset(),
        trace_id: str = "",
    ) -> "TrustedContext":
        """Construct a TrustedContext from a verified JWT payload.

        Args:
            claims: Decoded and cryptographically verified JWT payload dict.
            session_id: Current agent session identifier.
            approved_tool_ids: Tool IDs already approved by prior approval flow.
            trace_id: Distributed trace identifier from incoming request headers.

        Returns:
            TrustedContext with trust_level derived from the ``role`` claim.
        """
        _level_map = {
            "system": TrustLevel.SYSTEM,
            "admin": TrustLevel.ADMIN,
            "power_user": TrustLevel.POWER_USER,
            "user": TrustLevel.USER,
            "guest": TrustLevel.GUEST,
        }
        role = claims.get("role", "user").lower()
        return cls(
            session_id=session_id,
            user_id=claims.get("sub", ""),
            trust_level=_level_map.get(role, TrustLevel.USER),
            approved_tool_ids=approved_tool_ids,
            ip_address=claims.get("ip", ""),
            trace_id=trace_id,
        )

    @classmethod
    def system(cls, session_id: str = "system", trace_id: str = "") -> "TrustedContext":
        """Mint a SYSTEM-level context for internal background tasks."""
        return cls(
            session_id=session_id,
            user_id="system",
            trust_level=TrustLevel.SYSTEM,
            approved_tool_ids=frozenset(),
            trace_id=trace_id,
        )

    # ── Policy helpers ───────────────────────────────────────────────────────

    def can_execute_tool(self, tool_id: str, required_level: TrustLevel) -> bool:
        """Return True if this context authorises automatic tool execution.

        Args:
            tool_id: Tool identifier to check.
            required_level: Minimum TrustLevel needed to bypass the approval gate.

        Returns:
            True if trust_level >= required_level, OR if tool_id is pre-approved.
        """
        if self.trust_level >= required_level:
            return True
        return tool_id in self.approved_tool_ids

    def elevate(self, additional_tool_ids: FrozenSet[str]) -> "TrustedContext":
        """Return a new context with additional pre-approved tool IDs.

        Used by the approval flow to mint an elevated context after the user
        confirms a specific tool action.
        """
        return TrustedContext(
            session_id=self.session_id,
            user_id=self.user_id,
            trust_level=self.trust_level,
            approved_tool_ids=self.approved_tool_ids | additional_tool_ids,
            ip_address=self.ip_address,
            created_at=self.created_at,
            trace_id=self.trace_id,
        )

    # ── Utility ──────────────────────────────────────────────────────────────

    def fingerprint(self) -> str:
        """Return a stable 16-char hex hash for audit log correlation."""
        data = f"{self.session_id}:{self.user_id}:{self.trust_level}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def is_expired(self, ttl_seconds: float = 3600.0) -> bool:
        """Return True if this context has exceeded its validity window."""
        return (time.time() - self.created_at) > ttl_seconds
