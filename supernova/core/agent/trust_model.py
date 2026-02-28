"""
supernova/core/agent/trust_model.py

Dynamic trust model — autonomy earned through behavioral history.

From PROGRESS_TRACKER_v3 (Autonomy section):
  'Replace your binary approval/deny system with a dynamic trust model
   that learns from your behavior. Start fully supervised, build a trust
   history, and expand autonomy only where that history justifies it.'

The trust model answers one question per tool call:
  "Given this user's history with this type of action, should I auto-approve
   or ask for confirmation?"

Autonomy score factors (weighted sum, 0.0 to 1.0):
  approved_ratio   (+0.40) — fraction of similar past actions the user approved
  reversibility    (+0.20) — can this action be undone if wrong?
  novelty_penalty  (-0.25) — new action types start with low trust
  recency_decay    (-0.10) — unused trust degrades over time (90-day window)
  preference_match (+0.05) — explicitly stated user preferences boost score

Score thresholds (user-configurable via settings):
  >= AUTONOMY_THRESHOLD (default 0.75) — auto-approve
  >= 0.40              — approve with brief notification (no blocking prompt)
  <  0.40              — full blocking approval request

Persistence:
  Trust records are stored in Redis as JSON-serialized TrustRecord objects,
  keyed by (user_id, action_fingerprint). They survive restarts and accumulate
  across sessions, which is the entire point — trust is a long-lived asset.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Default threshold above which actions auto-approve.
# 0.75 = meaningful approval history required before autonomy is granted.
DEFAULT_AUTONOMY_THRESHOLD: float = 0.75

# Trust decays after this many days of non-use for a given action type.
TRUST_DECAY_DAYS: int = 90

# Minimum decisions required before trust score is considered meaningful.
MIN_DECISIONS_FOR_TRUST: int = 3


@dataclass
class TrustRecord:
    """
    Persisted trust history for a specific (user, action_type, tool_name) triple.

    This is the raw data that autonomy_score() uses to compute its weighted estimate.
    It is JSON-serializable so it can be stored in Redis without a schema migration.
    """
    user_id: str
    action_fingerprint: str         # hash(action_type + tool_name + param_pattern)
    tool_name: str
    action_type: str                # e.g. "file_read", "file_write", "api_call"
    is_reversible: bool             # Can this action be undone?
    approvals: int = 0
    denials: int = 0
    total: int = 0
    last_approved_at: str | None = None   # ISO-8601 UTC
    last_denied_at: str | None = None     # ISO-8601 UTC
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    explicit_preferences: list[str] = field(default_factory=list)  # user-stated rules

    @property
    def approval_ratio(self) -> float:
        """Fraction of interactions that resulted in approval. 0 if no history."""
        return self.approvals / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> TrustRecord:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TrustModel:
    """
    Dynamic trust model: learns autonomy thresholds from user approval history.

    Usage:
        model = TrustModel(redis_client, autonomy_threshold=0.75)
        should_auto = await model.should_auto_approve(user_id, tool_call)
        await model.record_decision(user_id, tool_call, approved=True)
    """

    def __init__(
        self,
        redis_client: Any,
        autonomy_threshold: float = DEFAULT_AUTONOMY_THRESHOLD,
    ) -> None:
        self._redis = redis_client
        self._threshold = autonomy_threshold

    # ── Public API ───────────────────────────────────────────────────────────

    async def should_auto_approve(
        self,
        user_id: str,
        tool_call: dict,
    ) -> bool:
        """
        Return True if this tool call can auto-approve based on trust history.

        A tool call with no history always returns False (start supervised).
        A tool call with < MIN_DECISIONS_FOR_TRUST history always returns False.
        """
        score = await self.autonomy_score(user_id, tool_call)
        return score >= self._threshold

    async def autonomy_score(
        self,
        user_id: str,
        tool_call: dict,
    ) -> float:
        """
        Compute autonomy score (0.0 to 1.0) for this tool call.

        Score components:
          approved_ratio_score  (weight 0.40) — primary signal
          reversibility_score   (weight 0.20) — undo-ability bonus
          novelty_penalty       (weight 0.25) — penalize unknown action types
          recency_decay         (weight 0.10) — penalize stale trust records
          preference_match      (weight 0.05) — explicit user pref bonus
        """
        record = await self._load_record(user_id, tool_call)

        if record is None or record.total < MIN_DECISIONS_FOR_TRUST:
            return 0.0

        approved_ratio_score = record.approval_ratio * 0.40

        reversibility_score = 0.20 if record.is_reversible else 0.0

        novelty_penalty = 0.0 if record.total >= 10 else (
            0.25 * (1.0 - record.total / 10.0)
        )

        recency_decay = self._compute_recency_decay(record) * 0.10

        preference_match = self._compute_preference_match(
            record, tool_call
        ) * 0.05

        raw = (
            approved_ratio_score
            + reversibility_score
            - novelty_penalty
            - recency_decay
            + preference_match
        )
        score = max(0.0, min(1.0, raw))

        logger.debug(
            "TrustModel score: tool=%s score=%.3f "
            "(ratio=%.2f rev=%.2f novelty=-%.2f recency=-%.2f pref=+%.2f)",
            tool_call.get("name", "?"),
            score,
            approved_ratio_score,
            reversibility_score,
            novelty_penalty,
            recency_decay,
            preference_match,
        )
        return score

    async def record_decision(
        self,
        user_id: str,
        tool_call: dict,
        approved: bool,
        is_reversible: bool = True,
    ) -> None:
        """
        Record the user's approval or denial decision for future learning.

        This is the write side of the trust model — every decision the user
        makes (approve/deny in the HITL UI) feeds back into the trust record,
        continuously improving future autonomous behavior.
        """
        record = await self._load_record(user_id, tool_call)
        fingerprint = self._fingerprint(tool_call)
        now_iso = datetime.now(timezone.utc).isoformat()

        if record is None:
            record = TrustRecord(
                user_id=user_id,
                action_fingerprint=fingerprint,
                tool_name=tool_call.get("name", "unknown"),
                action_type=self._classify_action(tool_call),
                is_reversible=is_reversible,
            )

        record.total += 1
        if approved:
            record.approvals += 1
            record.last_approved_at = now_iso
        else:
            record.denials += 1
            record.last_denied_at = now_iso

        await self._save_record(user_id, record)
        logger.info(
            "Trust record updated: user=%s tool=%s approved=%s ratio=%.2f total=%d",
            user_id, record.tool_name, approved, record.approval_ratio, record.total,
        )

    async def explain(
        self,
        user_id: str,
        tool_call: dict,
    ) -> str:
        """
        Return a human-readable explanation of the current trust decision.

        This is surfaced in the approval UI so users understand *why* they
        are being asked to approve or why the action auto-approved.
        Transparency builds trust in the trust model itself.
        """
        record = await self._load_record(user_id, tool_call)
        score = await self.autonomy_score(user_id, tool_call)
        tool_name = tool_call.get("name", "unknown")

        if record is None or record.total == 0:
            return (
                f"**{tool_name}**: No history — first time I've seen this action. "
                f"Asking for your confirmation to start building trust."
            )

        if record.total < MIN_DECISIONS_FOR_TRUST:
            return (
                f"**{tool_name}**: Only {record.total} decision(s) recorded. "
                f"I need at least {MIN_DECISIONS_FOR_TRUST} before auto-approving. "
                f"You've approved {record.approvals} and denied {record.denials} so far."
            )

        if score >= self._threshold:
            return (
                f"**{tool_name}**: Auto-approved (score {score:.0%}). "
                f"You've approved this type of action {record.approvals}/{record.total} times."
            )

        return (
            f"**{tool_name}**: Asking for confirmation (score {score:.0%}, "
            f"threshold {self._threshold:.0%}). "
            f"Approval history: {record.approvals} approved, {record.denials} denied "
            f"out of {record.total} total."
        )

    # ── Internal helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _fingerprint(tool_call: dict) -> str:
        """Stable hash of (tool_name, action_type) for Redis key."""
        key = f"{tool_call.get('name', '')}:{tool_call.get('type', '')}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    @staticmethod
    def _classify_action(tool_call: dict) -> str:
        """Heuristic classification of action type from tool name."""
        name = tool_call.get("name", "").lower()
        if any(kw in name for kw in ("read", "get", "fetch", "list", "search")):
            return "read"
        if any(kw in name for kw in ("write", "create", "update", "delete", "post")):
            return "write"
        if any(kw in name for kw in ("exec", "run", "execute", "shell", "code")):
            return "execute"
        if any(kw in name for kw in ("send", "email", "message", "notify")):
            return "communicate"
        return "other"

    @staticmethod
    def _compute_recency_decay(record: TrustRecord) -> float:
        """
        Returns 0.0 (no decay) to 1.0 (full decay) based on days since last use.

        Trust that hasn't been exercised in TRUST_DECAY_DAYS is fully decayed.
        This prevents old approvals from indefinitely granting autonomy.
        """
        last_use_iso = record.last_approved_at or record.last_denied_at
        if last_use_iso is None:
            return 1.0  # No history — treat as fully decayed
        try:
            last_use = datetime.fromisoformat(last_use_iso)
            days_since = (datetime.now(timezone.utc) - last_use).days
            decay = min(1.0, days_since / TRUST_DECAY_DAYS)
            return decay
        except ValueError:
            return 0.5  # Unknown timestamp — partial decay

    @staticmethod
    def _compute_preference_match(
        record: TrustRecord,
        tool_call: dict,
    ) -> float:
        """
        Returns 1.0 if any of the user's explicit preferences match this action.
        Returns 0.0 otherwise. Preferences are simple string rules stored by
        the user in settings, e.g. 'auto-approve calendar invites'.
        """
        if not record.explicit_preferences:
            return 0.0
        tool_name = tool_call.get("name", "").lower()
        for pref in record.explicit_preferences:
            if any(kw in tool_name for kw in pref.lower().split()):
                return 1.0
        return 0.0

    def _redis_key(self, user_id: str, fingerprint: str) -> str:
        return f"trust:{user_id}:{fingerprint}"

    async def _load_record(
        self,
        user_id: str,
        tool_call: dict,
    ) -> TrustRecord | None:
        fingerprint = self._fingerprint(tool_call)
        key = self._redis_key(user_id, fingerprint)
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return TrustRecord.from_dict(json.loads(raw))
        except Exception as exc:
            logger.warning("TrustModel: failed to load record for %s: %s", key, exc)
            return None

    async def _save_record(self, user_id: str, record: TrustRecord) -> None:
        key = self._redis_key(user_id, record.action_fingerprint)
        try:
            # No expiry — trust records are long-lived assets
            await self._redis.set(key, json.dumps(record.to_dict()))
        except Exception as exc:
            logger.warning("TrustModel: failed to save record for %s: %s", key, exc)
