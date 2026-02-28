"""Tests for DynamicTrustModel (supernova/core/agent/trust_model.py).

ToT paths covered:
  A  Pre-approved tool ID bypasses scoring entirely
  B  SYSTEM trust level always produces adjusted=0.0 (never needs approval)
  C  CRITICAL + UNTRUSTED produces requires_approval=True
  D  LOW + ADMIN falls below default threshold (auto-approved)
  E  Anomaly multiplier amplifies score when velocity > 10 calls/min
  F  Approved history records reduce score; rejected records are ignored
  G  Custom approval_threshold overrides env default
  H  _confidence grows with history volume and score extremeness
"""
from __future__ import annotations

import math
import time

import pytest

from supernova.core.agent.trust_model import (
    ApprovalRecord,
    DynamicTrustModel,
    RiskTier,
)
from supernova.core.security.trusted_context import TrustedContext, TrustLevel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(
    trust_level: TrustLevel = TrustLevel.USER,
    approved_tool_ids: frozenset = frozenset(),
    session_id: str = "sess-001",
) -> TrustedContext:
    return TrustedContext(
        session_id=session_id,
        user_id="u1",
        trust_level=trust_level,
        approved_tool_ids=approved_tool_ids,
    )


def _approval(
    tool_id: str = "bash_exec",
    approved: bool = True,
    age_seconds: float = 10.0,
    session_id: str = "sess-001",
    risk_tier: RiskTier = RiskTier.HIGH,
) -> ApprovalRecord:
    return ApprovalRecord(
        tool_id=tool_id,
        approved=approved,
        timestamp=time.time() - age_seconds,
        risk_tier=risk_tier,
        session_id=session_id,
    )


MODEL = DynamicTrustModel()


# ---------------------------------------------------------------------------
# Path A: pre-approved bypass
# ---------------------------------------------------------------------------

def test_pre_approved_tool_bypasses_scoring() -> None:
    ctx = _ctx(
        trust_level=TrustLevel.UNTRUSTED,
        approved_tool_ids=frozenset({"bash_exec"}),
    )
    score = MODEL.score("bash_exec", RiskTier.CRITICAL, ctx)

    assert score.adjusted_score == 0.0
    assert score.requires_approval is False
    assert score.confidence == 1.0
    assert score.factors.get("pre_approved") == 1.0


# ---------------------------------------------------------------------------
# Path B: SYSTEM trust level → adjusted = 0.0 for all tiers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tier", list(RiskTier))
def test_system_trust_level_never_requires_approval(tier: RiskTier) -> None:
    ctx = _ctx(trust_level=TrustLevel.SYSTEM)
    score = MODEL.score("any_tool", tier, ctx)

    # discount=1.0 → raw * 0.0 * ... = 0.0
    assert score.adjusted_score == pytest.approx(0.0, abs=1e-9)
    assert score.requires_approval is False


# ---------------------------------------------------------------------------
# Path C: CRITICAL + UNTRUSTED → requires_approval=True
# ---------------------------------------------------------------------------

def test_critical_tier_untrusted_requires_approval() -> None:
    ctx = _ctx(trust_level=TrustLevel.UNTRUSTED)
    score = MODEL.score("risky_tool", RiskTier.CRITICAL, ctx)

    # base 0.90, no discounts → 0.90 ≥ default threshold 0.35
    assert score.raw_score == pytest.approx(0.90)
    assert score.requires_approval is True


# ---------------------------------------------------------------------------
# Path D: LOW + ADMIN → auto-approved (below threshold)
# ---------------------------------------------------------------------------

def test_low_tier_admin_does_not_require_approval() -> None:
    ctx = _ctx(trust_level=TrustLevel.ADMIN)
    score = MODEL.score("read_file", RiskTier.LOW, ctx)

    # 0.30 * (1 - 0.50) = 0.15 < 0.35
    assert score.adjusted_score == pytest.approx(0.15, abs=0.01)
    assert score.requires_approval is False


# ---------------------------------------------------------------------------
# Path E: anomaly multiplier fires above 10 calls/min
# ---------------------------------------------------------------------------

def test_anomaly_multiplier_above_ten_calls_per_minute() -> None:
    ctx = _ctx(trust_level=TrustLevel.USER)
    normal = MODEL.score("tool", RiskTier.MEDIUM, ctx, velocity_calls_per_minute=5.0)
    elevated = MODEL.score("tool", RiskTier.MEDIUM, ctx, velocity_calls_per_minute=20.0)

    expected_mult = 1.0 + math.log1p(20.0 - 10.0) * 0.1
    assert elevated.factors["anomaly_multiplier"] == pytest.approx(expected_mult, rel=1e-6)
    assert elevated.adjusted_score > normal.adjusted_score


def test_anomaly_multiplier_at_or_below_ten_is_one() -> None:
    ctx = _ctx(trust_level=TrustLevel.USER)
    score = MODEL.score("tool", RiskTier.MEDIUM, ctx, velocity_calls_per_minute=10.0)
    assert score.factors["anomaly_multiplier"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Path F: history discount — approved records reduce score;
#         rejected records must be ignored
# ---------------------------------------------------------------------------

def test_approved_history_reduces_adjusted_score() -> None:
    ctx = _ctx(trust_level=TrustLevel.USER)
    no_hist = MODEL.score("bash_exec", RiskTier.HIGH, ctx)
    with_hist = MODEL.score(
        "bash_exec",
        RiskTier.HIGH,
        ctx,
        approval_history=[_approval(approved=True, age_seconds=5.0)],
    )
    assert with_hist.adjusted_score < no_hist.adjusted_score
    assert with_hist.factors["history_discount"] > 0.0


def test_rejected_history_records_do_not_discount() -> None:
    ctx = _ctx(trust_level=TrustLevel.USER)
    baseline = MODEL.score("bash_exec", RiskTier.HIGH, ctx)
    with_rejected = MODEL.score(
        "bash_exec",
        RiskTier.HIGH,
        ctx,
        approval_history=[_approval(approved=False, age_seconds=5.0)],
    )
    # Rejected approvals must not reduce risk score
    assert with_rejected.factors["history_discount"] == pytest.approx(0.0)
    assert with_rejected.adjusted_score == pytest.approx(baseline.adjusted_score, rel=1e-6)


def test_history_discount_same_session_bonus_is_greater() -> None:
    """Same-session approvals carry a 1.5x recency bonus over cross-session."""
    ctx = _ctx(session_id="sess-A")
    same_session_hist = [_approval(session_id="sess-A", age_seconds=5.0)]
    diff_session_hist = [_approval(session_id="sess-B", age_seconds=5.0)]

    same = MODEL.score("bash_exec", RiskTier.HIGH, ctx, approval_history=same_session_hist)
    diff = MODEL.score("bash_exec", RiskTier.HIGH, ctx, approval_history=diff_session_hist)

    assert same.factors["history_discount"] > diff.factors["history_discount"]


# ---------------------------------------------------------------------------
# Path G: custom threshold overrides the default
# ---------------------------------------------------------------------------

def test_custom_threshold_changes_routing_decision() -> None:
    strict = DynamicTrustModel(approval_threshold=0.05)
    lenient = DynamicTrustModel(approval_threshold=0.95)

    ctx = _ctx(trust_level=TrustLevel.USER)

    # SAFE tier baseline score = 0.10 * (1-0.15) = 0.085
    strict_score = strict.score("read_db", RiskTier.SAFE, ctx)
    lenient_score = lenient.score("read_db", RiskTier.SAFE, ctx)

    assert strict_score.requires_approval is True   # 0.085 ≥ 0.05
    assert lenient_score.requires_approval is False  # 0.085 < 0.95


# ---------------------------------------------------------------------------
# Path H: _confidence grows with more history and score extremeness
# ---------------------------------------------------------------------------

def test_confidence_increases_with_history_volume() -> None:
    ctx = _ctx(trust_level=TrustLevel.USER)
    no_hist = MODEL.score("tool", RiskTier.MEDIUM, ctx)
    large_hist = MODEL.score(
        "tool",
        RiskTier.MEDIUM,
        ctx,
        approval_history=[_approval(age_seconds=float(i)) for i in range(1, 30)],
    )
    assert large_hist.confidence > no_hist.confidence
    assert 0.0 <= large_hist.confidence <= 1.0
