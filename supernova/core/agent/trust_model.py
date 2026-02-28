"""supernova/core/agent/trust_model.py

Dynamic trust scoring for tool execution decisions.  Computes a composite
trust score from tool risk metadata, caller trust level, approval history,
and real-time velocity signals.  Used by the interrupt gate and tool router
to decide whether a tool call proceeds automatically or requires approval.

Score formula::

    adjusted = base_risk
               × (1 − trust_level_discount)
               × (1 − history_discount)
               × anomaly_multiplier

Execution is auto-approved when ``adjusted_score < approval_threshold``.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from supernova.core.security.trusted_context import TrustLevel, TrustedContext


# ── Risk tier classification ─────────────────────────────────────────────────────


class RiskTier(Enum):
    """Tool risk classification tiers used to anchor the base trust score."""

    SAFE = "safe"  # Read-only, no external effects (e.g. get_time, read_file)
    LOW = "low"  # Writes to local state only (e.g. create_note)
    MEDIUM = "medium"  # External API calls, reversible writes (e.g. web_search)
    HIGH = "high"  # FS writes, sub-process execution (e.g. bash, write_file)
    CRITICAL = "critical"  # Network egress, secrets access, irreversible ops


_TIER_BASE_SCORES: Dict[RiskTier, float] = {
    RiskTier.SAFE: 0.10,
    RiskTier.LOW: 0.30,
    RiskTier.MEDIUM: 0.50,
    RiskTier.HIGH: 0.70,
    RiskTier.CRITICAL: 0.90,
}

_TRUST_DISCOUNTS: Dict[TrustLevel, float] = {
    TrustLevel.UNTRUSTED: 0.00,
    TrustLevel.GUEST: 0.05,
    TrustLevel.USER: 0.15,
    TrustLevel.POWER_USER: 0.30,
    TrustLevel.ADMIN: 0.50,
    TrustLevel.SYSTEM: 1.00,  # System contexts always auto-approve
}


# ── Data types ───────────────────────────────────────────────────────────────


@dataclass
class ApprovalRecord:
    """A single tool-approval event persisted in the approval history store."""

    tool_id: str
    approved: bool
    timestamp: float
    risk_tier: RiskTier
    session_id: str


@dataclass
class TrustScore:
    """Composite trust score for a single tool execution decision.

    Attributes:
        raw_score: Base risk before discounts (0.0 = no risk, 1.0 = maximum risk).
        adjusted_score: Final score after trust, history, and anomaly factors.
        requires_approval: True when adjusted_score >= threshold.
        confidence: Model confidence in this score (0.0 – 1.0).
        factors: Per-component breakdown for audit logging / explainability.
    """

    raw_score: float
    adjusted_score: float
    requires_approval: bool
    confidence: float
    factors: Dict[str, float] = field(default_factory=dict)


# ── Trust model ──────────────────────────────────────────────────────────────


class DynamicTrustModel:
    """Compute dynamic trust scores for tool execution decisions.

    Combines four signals:

    1. **Static base risk** — anchored to :class:`RiskTier`.
    2. **Caller trust discount** — from :class:`~supernova.core.security.trusted_context.TrustLevel`.
    3. **History discount** — recency-weighted prior approvals for the same tool.
    4. **Anomaly multiplier** — amplifies score when call velocity is abnormal.

    Args:
        approval_threshold: Score at or above which human approval is required.
            Default 0.35 (a POWER_USER calling a HIGH-risk tool scores ~0.28,
            a plain USER calling the same tool scores ~0.595 → approval required).
        history_window_seconds: Lookback window for approval history.
        max_history_discount: Cap on the history-driven score reduction.
        velocity_soft_threshold: Calls-per-minute above which anomaly scaling starts.
    """

    def __init__(
        self,
        approval_threshold: float = 0.35,
        history_window_seconds: float = 86_400.0,
        max_history_discount: float = 0.25,
        velocity_soft_threshold: float = 10.0,
    ) -> None:
        self._threshold = approval_threshold
        self._history_window = history_window_seconds
        self._max_history_discount = max_history_discount
        self._velocity_threshold = velocity_soft_threshold

    def score(
        self,
        tool_id: str,
        risk_tier: RiskTier,
        context: TrustedContext,
        approval_history: Optional[List[ApprovalRecord]] = None,
        velocity_calls_per_minute: float = 0.0,
    ) -> TrustScore:
        """Compute a TrustScore for the proposed tool execution.

        Args:
            tool_id: Identifier of the tool being called.
            risk_tier: Declared :class:`RiskTier` for this tool.
            context: :class:`~supernova.core.security.trusted_context.TrustedContext`
                for the current request.
            approval_history: Recent :class:`ApprovalRecord` list for this
                tool / user pair.  Pass an empty list when unavailable.
            velocity_calls_per_minute: Current call rate, used for anomaly
                detection.  Pass ``0.0`` when not tracked.

        Returns:
            :class:`TrustScore` with the adjusted score and approval decision.
        """
        history = approval_history or []
        raw = _TIER_BASE_SCORES[risk_tier]
        factors: Dict[str, float] = {"base_risk": raw}

        # — Fast path: pre-approved in context OR SYSTEM level —
        if tool_id in context.approved_tool_ids or context.trust_level == TrustLevel.SYSTEM:
            return TrustScore(
                raw_score=raw,
                adjusted_score=0.0,
                requires_approval=False,
                confidence=1.0,
                factors={"pre_approved_or_system": 1.0},
            )

        # — Trust level discount —
        trust_discount = _TRUST_DISCOUNTS.get(context.trust_level, 0.0)
        factors["trust_discount"] = trust_discount

        # — History discount —
        history_discount = self._history_discount(
            tool_id, history, context.session_id
        )
        factors["history_discount"] = history_discount

        # — Anomaly multiplier —
        anomaly = self._anomaly_multiplier(velocity_calls_per_minute)
        factors["anomaly_multiplier"] = anomaly

        adjusted = raw * (1.0 - trust_discount) * (1.0 - history_discount) * anomaly
        adjusted = max(0.0, min(adjusted, 1.0))
        factors["adjusted_score"] = adjusted

        confidence = self._confidence(history, raw)

        return TrustScore(
            raw_score=raw,
            adjusted_score=adjusted,
            requires_approval=adjusted >= self._threshold,
            confidence=confidence,
            factors=factors,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _history_discount(
        self,
        tool_id: str,
        history: List[ApprovalRecord],
        session_id: str,
    ) -> float:
        """Recency-weighted discount from positive prior approvals."""
        now = time.time()
        cutoff = now - self._history_window
        relevant = [
            r
            for r in history
            if r.tool_id == tool_id and r.approved and r.timestamp >= cutoff
        ]
        if not relevant:
            return 0.0

        weighted = 0.0
        quarter_window = self._history_window / 4.0
        for rec in relevant:
            age = now - rec.timestamp
            recency = math.exp(-age / quarter_window)
            session_bonus = 1.5 if rec.session_id == session_id else 1.0
            weighted += recency * session_bonus

        return min(math.tanh(weighted) * self._max_history_discount, self._max_history_discount)

    def _anomaly_multiplier(self, velocity: float) -> float:
        """Return a multiplier > 1.0 when call velocity exceeds soft threshold."""
        if velocity <= self._velocity_threshold:
            return 1.0
        excess = velocity - self._velocity_threshold
        return 1.0 + math.log1p(excess) * 0.1

    def _confidence(self, history: List[ApprovalRecord], raw_score: float) -> float:
        """Estimate scoring confidence from history volume and score extremeness."""
        history_conf = math.tanh(len(history) / 25.0)
        extremeness = abs(raw_score - 0.5) * 2.0
        return min(0.5 + history_conf * 0.3 + extremeness * 0.2, 1.0)
