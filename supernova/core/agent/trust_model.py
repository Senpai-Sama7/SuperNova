"""supernova/core/agent/trust_model.py

Dynamic trust scoring for tool execution decisions. Computes a composite
trust score from tool risk metadata, caller trust level, session approval
history, and call-velocity anomaly signals. Used by the interrupt gate and
tool router to determine whether execution proceeds automatically or requires
human approval.

Scoring formula::

    adjusted = base_risk
               × (1 − trust_level_discount)
               × (1 − history_discount)
               × anomaly_multiplier

Auto-approved when adjusted < approval_threshold (default 0.35).
"""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from supernova.core.security.trusted_context import TrustLevel, TrustedContext


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------


class RiskTier(Enum):
    """Tool risk classification.

    Tiers map to base risk scores in ``_TIER_BASE_SCORES``.
    """

    SAFE = "safe"         # Read-only, no external effects
    LOW = "low"           # Local state writes only
    MEDIUM = "medium"     # External API calls, reversible writes
    HIGH = "high"         # Filesystem writes, subprocess / code execution
    CRITICAL = "critical" # Network egress, secrets access, irreversible ops


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
    TrustLevel.SYSTEM: 1.00,  # System callers never need approval
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class ApprovalRecord:
    """Single human-approval event recorded for trust-history scoring.

    Attributes:
        tool_id: The tool that was approved or rejected.
        approved: True if the human approved execution.
        timestamp: Unix timestamp of the decision.
        risk_tier: Risk tier of the tool at decision time.
        session_id: Session in which the decision was made.
    """

    tool_id: str
    approved: bool
    timestamp: float
    risk_tier: RiskTier
    session_id: str


@dataclass
class TrustScore:
    """Composite trust score and routing decision for a tool execution.

    Attributes:
        raw_score: Base risk score before discounts (0.0–1.0).
        adjusted_score: Score after trust and history discounts.
        requires_approval: True if adjusted_score ≥ approval_threshold.
        confidence: Model’s self-assessed confidence in this decision (0–1).
        factors: Breakdown of score components for audit logging.
    """

    raw_score: float
    adjusted_score: float
    requires_approval: bool
    confidence: float
    factors: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class DynamicTrustModel:
    """Computes dynamic trust scores for tool execution routing decisions.

    Usage::

        model = DynamicTrustModel()
        score = model.score(
            tool_id="bash_exec",
            risk_tier=RiskTier.HIGH,
            context=trusted_ctx,
            approval_history=recent_records,
        )
        if score.requires_approval:
            await interrupt_gate.request_approval(...)

    Args:
        approval_threshold: Score at or above which human approval is required.
            Default 0.35 (equivalent to a POWER_USER executing a HIGH-risk tool
            with no prior approval history).
        history_window_seconds: Approval records older than this are ignored.
        max_history_discount: Maximum fractional score reduction from history.
    """

    def __init__(
        self,
        approval_threshold: Optional[float] = None,
        history_window_seconds: float = 86_400.0,
        max_history_discount: float = 0.25,
    ) -> None:
        self._threshold = approval_threshold or float(os.environ.get('AUTONOMY_THRESHOLD', '0.35'))
        self._history_window = history_window_seconds
        self._max_history_discount = max_history_discount

    def score(
        self,
        tool_id: str,
        risk_tier: RiskTier,
        context: TrustedContext,
        approval_history: Optional[List[ApprovalRecord]] = None,
        velocity_calls_per_minute: float = 0.0,
    ) -> TrustScore:
        """Compute a trust score for a proposed tool execution.

        Args:
            tool_id: Identifier of the tool to execute.
            risk_tier: Declared risk classification of the tool.
            context: :class:`TrustedContext` for the current request.
            approval_history: Recent approval records for this tool/user pair.
            velocity_calls_per_minute: Current call rate for anomaly detection.

        Returns:
            :class:`TrustScore` with routing decision and audit factors.
        """
        history = approval_history or []
        raw = _TIER_BASE_SCORES[risk_tier]
        factors: Dict[str, float] = {"base_risk": raw}

        # Pre-approved tools skip scoring entirely
        if tool_id in context.approved_tool_ids:
            return TrustScore(
                raw_score=raw,
                adjusted_score=0.0,
                requires_approval=False,
                confidence=1.0,
                factors={"pre_approved": 1.0},
            )

        trust_discount = _TRUST_DISCOUNTS.get(context.trust_level, 0.0)
        factors["trust_discount"] = trust_discount

        history_discount = self._history_discount(tool_id, history, context.session_id)
        factors["history_discount"] = history_discount

        anomaly_mult = self._anomaly_multiplier(velocity_calls_per_minute)
        factors["anomaly_multiplier"] = anomaly_mult

        adjusted = raw * (1.0 - trust_discount) * (1.0 - history_discount) * anomaly_mult
        adjusted = min(max(adjusted, 0.0), 1.0)
        factors["adjusted_score"] = adjusted

        confidence = self._confidence(history, raw)

        return TrustScore(
            raw_score=raw,
            adjusted_score=adjusted,
            requires_approval=adjusted >= self._threshold,
            confidence=confidence,
            factors=factors,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _history_discount(self, tool_id: str, history: List[ApprovalRecord], session_id: str) -> float:
        """Recency-weighted discount from prior approvals for *tool_id*."""
        now = time.time()
        cutoff = now - self._history_window
        relevant = [
            r for r in history
            if r.tool_id == tool_id and r.approved and r.timestamp >= cutoff
        ]
        if not relevant:
            return 0.0

        weighted = 0.0
        for rec in relevant:
            age = now - rec.timestamp
            recency = math.exp(-age / (self._history_window / 4.0))
            same_session_bonus = 1.5 if rec.session_id == session_id else 1.0
            weighted += recency * same_session_bonus

        return min(math.tanh(weighted) * self._max_history_discount, self._max_history_discount)

    def _anomaly_multiplier(self, velocity: float) -> float:
        """Soft anomaly amplifier when call velocity exceeds 10 calls/min."""
        if velocity <= 10.0:
            return 1.0
        return 1.0 + math.log1p(velocity - 10.0) * 0.1

    def _confidence(self, history: List[ApprovalRecord], raw_score: float) -> float:
        """Estimate scoring confidence from history volume and score extremeness."""
        history_conf = math.tanh(len(history) / 25.0)
        extremeness = abs(raw_score - 0.5) * 2.0
        return min(0.5 + history_conf * 0.3 + extremeness * 0.2, 1.0)
