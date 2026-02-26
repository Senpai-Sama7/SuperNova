"""Cost tracking and budget enforcement with Redis-backed atomic counters.

Provides CostController for per-day/month spending limits, cost recording,
estimation, and alert thresholds. All counter updates use Redis INCRBYFLOAT
for atomicity across concurrent agent calls.

Redis key schema:
    cost:daily:{YYYY-MM-DD}   → float (USD spent today)
    cost:monthly:{YYYY-MM}    → float (USD spent this month)
    cost:last_alert:{level}   → timestamp of last alert at that level
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from redis.asyncio import Redis

from supernova.config import get_settings

logger = logging.getLogger(__name__)

# Redis key prefixes
_DAILY_KEY = "cost:daily"
_MONTHLY_KEY = "cost:monthly"
_ALERT_KEY = "cost:last_alert"

# TTLs
_DAILY_TTL = 86400 * 2      # 2 days (covers timezone edge)
_MONTHLY_TTL = 86400 * 35   # 35 days

# Per-million-token pricing lookup (USD). Used for estimation.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input $/MTok, output $/MTok)
    "anthropic/claude-sonnet-4-5": (3.00, 15.00),
    "openai/gpt-4o": (2.50, 10.00),
    "google/gemini-2.0-flash": (0.10, 0.40),
    "groq/llama-3.3-70b-versatile": (0.59, 0.79),
    "ollama/qwen2.5:32b": (0.0, 0.0),
}

# Alert thresholds (percent of daily budget)
ALERT_LEVELS: list[int] = [50, 80, 100]


class BudgetExceeded(Exception):
    """Raised when a call would exceed the configured budget."""

    def __init__(self, current: float, limit: float, period: str) -> None:
        self.current = current
        self.limit = limit
        self.period = period
        super().__init__(f"{period} budget exceeded: ${current:.4f} / ${limit:.2f}")


class CostController:
    """Redis-backed cost tracking with budget enforcement.

    Args:
        redis: Async Redis client instance.
        daily_limit: Max USD per day. None = unlimited.
        monthly_limit: Max USD per month. None = unlimited.
        confirmation_threshold: Cost above which user confirmation is required.
        alert_threshold_pct: Percentage of daily budget that triggers alerts.
        enabled: Master switch for cost tracking.
    """

    def __init__(
        self,
        redis: Redis,
        daily_limit: float | None = None,
        monthly_limit: float | None = None,
        confirmation_threshold: float = 0.50,
        alert_threshold_pct: float = 80.0,
        enabled: bool = True,
    ) -> None:
        self._redis = redis
        self._daily_limit = daily_limit
        self._monthly_limit = monthly_limit
        self._confirmation_threshold = confirmation_threshold
        self._alert_threshold_pct = alert_threshold_pct
        self._enabled = enabled

    @classmethod
    def from_settings(cls, redis: Redis) -> CostController:
        """Create from application settings."""
        s = get_settings().cost
        return cls(
            redis=redis,
            daily_limit=s.daily_spending_limit,
            monthly_limit=None,  # monthly not in current config; use daily × 30
            confirmation_threshold=s.confirmation_threshold,
            alert_threshold_pct=s.alert_threshold_percent,
            enabled=s.tracking_enabled,
        )

    # ── Keys ──────────────────────────────────────────────────────────────

    @staticmethod
    def _daily_key(dt: datetime | None = None) -> str:
        d = dt or datetime.now(timezone.utc)
        return f"{_DAILY_KEY}:{d.strftime('%Y-%m-%d')}"

    @staticmethod
    def _monthly_key(dt: datetime | None = None) -> str:
        d = dt or datetime.now(timezone.utc)
        return f"{_MONTHLY_KEY}:{d.strftime('%Y-%m')}"

    # ── Core API ──────────────────────────────────────────────────────────

    async def check_budget(self, estimated_cost: float = 0.0) -> bool:
        """Return True if the estimated cost fits within remaining budget.

        Does NOT raise — returns False if budget would be exceeded.
        """
        if not self._enabled:
            return True

        now = datetime.now(timezone.utc)
        daily_spend = await self._get_counter(self._daily_key(now))
        if self._daily_limit is not None:
            if daily_spend + estimated_cost > self._daily_limit:
                return False

        if self._monthly_limit is not None:
            monthly_spend = await self._get_counter(self._monthly_key(now))
            if monthly_spend + estimated_cost > self._monthly_limit:
                return False

        return True

    async def record_cost(self, amount: float, model_id: str = "") -> dict[str, float]:
        """Record actual spend after an LLM call. Returns updated totals.

        Uses INCRBYFLOAT for atomic increment — safe under concurrency.
        """
        if not self._enabled or amount <= 0:
            return {"daily": 0.0, "monthly": 0.0}

        now = datetime.now(timezone.utc)
        dk = self._daily_key(now)
        mk = self._monthly_key(now)

        pipe = self._redis.pipeline()
        pipe.incrbyfloat(dk, amount)
        pipe.expire(dk, _DAILY_TTL)
        pipe.incrbyfloat(mk, amount)
        pipe.expire(mk, _MONTHLY_TTL)
        results = await pipe.execute()

        daily_total = float(results[0])
        monthly_total = float(results[2])

        logger.debug(
            "Recorded $%.6f for %s (daily=$%.4f, monthly=$%.4f)",
            amount, model_id, daily_total, monthly_total,
        )

        # Check alert thresholds
        alerts = await self._check_alerts(daily_total)

        return {"daily": daily_total, "monthly": monthly_total, "alerts": alerts}

    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a call based on model pricing and token counts."""
        pricing = MODEL_PRICING.get(model_id, (5.0, 15.0))  # default to expensive
        return (pricing[0] * input_tokens + pricing[1] * output_tokens) / 1_000_000

    def needs_confirmation(self, estimated_cost: float) -> bool:
        """Return True if the estimated cost exceeds the confirmation threshold."""
        return self._enabled and estimated_cost > self._confirmation_threshold

    async def get_spend_summary(self) -> dict:
        """Return current spend, limits, and projections for the API."""
        now = datetime.now(timezone.utc)
        daily = await self._get_counter(self._daily_key(now))
        monthly = await self._get_counter(self._monthly_key(now))

        hours_elapsed = now.hour + now.minute / 60.0
        daily_projection = (daily / max(hours_elapsed, 0.5)) * 24 if daily > 0 else 0.0

        return {
            "daily_spend": round(daily, 6),
            "monthly_spend": round(monthly, 6),
            "daily_limit": self._daily_limit,
            "monthly_limit": self._monthly_limit,
            "daily_projection": round(daily_projection, 4),
            "daily_pct": round((daily / self._daily_limit * 100) if self._daily_limit else 0, 1),
            "confirmation_threshold": self._confirmation_threshold,
            "tracking_enabled": self._enabled,
        }

    # ── Internals ─────────────────────────────────────────────────────────

    async def _get_counter(self, key: str) -> float:
        val = await self._redis.get(key)
        if val is None:
            return 0.0
        return float(val)

    async def _check_alerts(self, daily_total: float) -> list[int]:
        """Return list of alert levels that were newly crossed."""
        if self._daily_limit is None or self._daily_limit <= 0:
            return []

        pct = (daily_total / self._daily_limit) * 100
        triggered: list[int] = []

        for level in ALERT_LEVELS:
            if pct >= level:
                alert_key = f"{_ALERT_KEY}:{level}"
                last = await self._redis.get(alert_key)
                if last is None:
                    await self._redis.set(alert_key, str(time.time()), ex=_DAILY_TTL)
                    triggered.append(level)

        return triggered
