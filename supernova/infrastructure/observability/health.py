"""Deep health checks with alerting for all backend services."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServiceCheck:
    name: str
    status: str = "unknown"  # healthy | degraded | unhealthy
    latency_ms: float = 0.0
    detail: str = ""


@dataclass
class HealthAlertManager:
    """Tracks health state and pushes alerts on transitions."""

    _prev: dict[str, str] = field(default_factory=dict)
    _listeners: list[Any] = field(default_factory=list)

    def register(self, ws: Any) -> None:
        self._listeners.append(ws)

    def unregister(self, ws: Any) -> None:
        self._listeners = [w for w in self._listeners if w is not ws]

    async def evaluate(self, checks: list[ServiceCheck]) -> list[dict[str, str]]:
        """Compare with previous state, emit alerts on transitions."""
        alerts: list[dict[str, str]] = []
        for c in checks:
            prev = self._prev.get(c.name)
            if prev and prev != c.status:
                alert = {"service": c.name, "from": prev, "to": c.status, "detail": c.detail}
                alerts.append(alert)
                for ws in list(self._listeners):
                    try:
                        await ws.send_json({"type": "health_alert", **alert})
                    except Exception:
                        self.unregister(ws)
            self._prev[c.name] = c.status
        return alerts


async def _check_service(name: str, coro: Any) -> ServiceCheck:
    """Run a single health check with timeout."""
    t0 = time.monotonic()
    try:
        await asyncio.wait_for(coro, timeout=5.0)
        return ServiceCheck(name, "healthy", (time.monotonic() - t0) * 1000)
    except asyncio.TimeoutError:
        return ServiceCheck(name, "degraded", 5000.0, "timeout")
    except Exception as exc:
        return ServiceCheck(name, "unhealthy", (time.monotonic() - t0) * 1000, str(exc)[:200])


async def deep_health_check(
    pool: Any = None,
    redis: Any = None,
    neo4j_driver: Any = None,
) -> dict[str, Any]:
    """Run parallel health checks against all backends."""
    checks: list[Any] = []

    async def _noop(name: str, detail: str) -> ServiceCheck:
        return ServiceCheck(name, "unhealthy", 0, detail)

    if pool:
        async def _pg() -> None:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        checks.append(_check_service("postgresql", _pg()))
    else:
        checks.append(_noop("postgresql", "no pool"))

    if redis:
        checks.append(_check_service("redis", redis.ping()))
    else:
        checks.append(_noop("redis", "no client"))

    if neo4j_driver:
        async def _neo4j() -> None:
            await neo4j_driver.verify_connectivity()
        checks.append(_check_service("neo4j", _neo4j()))
    else:
        checks.append(_noop("neo4j", "no driver"))

    results = await asyncio.gather(*checks, return_exceptions=True)
    services = []
    for r in results:
        if isinstance(r, ServiceCheck):
            services.append(r)
        elif isinstance(r, Exception):
            services.append(ServiceCheck("unknown", "unhealthy", 0, str(r)[:200]))

    overall = "healthy"
    for s in services:
        if s.status == "unhealthy":
            overall = "unhealthy"
            break
        if s.status == "degraded":
            overall = "degraded"

    return {
        "status": overall,
        "services": [
            {"name": s.name, "status": s.status, "latency_ms": round(s.latency_ms, 1), "detail": s.detail}
            for s in services
        ],
    }
