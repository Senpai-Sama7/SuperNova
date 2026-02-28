"""supernova/core/security/trusted_context.py

Immutable TrustedContext snapshot: verified caller identity, permission scope,
and session-level trust metadata. Used by tool execution gates and the approval
coordinator to make policy decisions without ambient mutable state.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import FrozenSet


class TrustLevel(IntEnum):
    """Ordered trust levels; higher value = more privilege."""

    UNTRUSTED = 0
    GUEST = 1
    USER = 2
    POWER_USER = 3
    ADMIN = 4
    SYSTEM = 5


@dataclass(frozen=True)
class TrustedContext:
    """Immutable snapshot of trust state for a single agent request.

    All fields are set at construction time from verified sources
    (JWT claims, session records, approval history). No mutable state.

    Attributes:
        session_id: Unique identifier for the current agent session.
        user_id: Authenticated user identifier; empty string if unauthenticated.
        trust_level: Resolved TrustLevel for this request.
        approved_tool_ids: Frozenset of tool IDs pre-approved this context.
        ip_address: Client IP for rate-limit and anomaly detection.
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
        """Construct TrustedContext from decoded and verified JWT claims.

        Args:
            claims: Decoded JWT payload (must already be signature-verified).
            session_id: Current agent session identifier.
            approved_tool_ids: Tool IDs pre-approved by prior approval flow.
            trace_id: Distributed trace identifier.

        Returns:
            TrustedContext with trust level derived from ``role`` claim.
        """
        role = claims.get("role", "user").lower()
        level_map = {
            "system": TrustLevel.SYSTEM,
            "admin": TrustLevel.ADMIN,
            "power_user": TrustLevel.POWER_USER,
            "user": TrustLevel.USER,
            "guest": TrustLevel.GUEST,
        }
        return cls(
            session_id=session_id,
            user_id=claims.get("sub", ""),
            trust_level=level_map.get(role, TrustLevel.USER),
            approved_tool_ids=approved_tool_ids,
            ip_address=claims.get("ip", ""),
            trace_id=trace_id,
        )

    def can_execute_tool(self, tool_id: str, required_level: TrustLevel) -> bool:
        """Return True if this context authorises automatic tool execution.

        Args:
            tool_id: The tool being invoked.
            required_level: Minimum TrustLevel for auto-execution.

        Returns:
            True if trust level is sufficient OR tool is pre-approved.
        """
        if self.trust_level >= required_level:
            return True
        return tool_id in self.approved_tool_ids

    def fingerprint(self) -> str:
        """Return a 16-char hex digest of this context for audit logging."""
        raw = f"{self.session_id}:{self.user_id}:{self.trust_level}:{self.created_at}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def is_expired(self, ttl_seconds: float = 3600.0) -> bool:
        """True if this context has exceeded its validity window."""
        return (time.time() - self.created_at) > ttl_seconds
