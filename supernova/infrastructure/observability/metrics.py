"""Prometheus-compatible metrics collection (zero external dependencies)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class _Histogram:
    """Minimal histogram with fixed buckets."""

    buckets: tuple[float, ...] = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    _counts: list[int] = field(default_factory=list)
    _sum: float = 0.0
    _total: int = 0

    def __post_init__(self) -> None:
        self._counts = [0] * len(self.buckets)

    def observe(self, value: float) -> None:
        self._sum += value
        self._total += 1
        for i, b in enumerate(self.buckets):
            if value <= b:
                self._counts[i] += 1


class MetricsCollector:
    """Thread-safe metrics collector with Prometheus text output."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, _Histogram] = {}

    def inc(self, name: str, value: float = 1.0, labels: str = "") -> None:
        key = f"{name}{{{labels}}}" if labels else name
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, labels: str = "") -> None:
        key = f"{name}{{{labels}}}" if labels else name
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = _Histogram()
            self._histograms[name].observe(value)

    def render_prometheus(self) -> str:
        """Render all metrics in Prometheus exposition format."""
        lines: list[str] = []
        with self._lock:
            for k, v in sorted(self._counters.items()):
                lines.append(f"# TYPE {k.split('{')[0]} counter")
                lines.append(f"{k} {v}")
            for k, v in sorted(self._gauges.items()):
                lines.append(f"# TYPE {k.split('{')[0]} gauge")
                lines.append(f"{k} {v}")
            for name, h in sorted(self._histograms.items()):
                lines.append(f"# TYPE {name} histogram")
                cumulative = 0
                for i, b in enumerate(h.buckets):
                    cumulative += h._counts[i]
                    lines.append(f'{name}_bucket{{le="{b}"}} {cumulative}')
                lines.append(f'{name}_bucket{{le="+Inf"}} {h._total}')
                lines.append(f"{name}_sum {h._sum}")
                lines.append(f"{name}_count {h._total}")
        return "\n".join(lines) + "\n"


# Singleton
metrics = MetricsCollector()


class RequestTimer:
    """Context manager for timing requests."""

    def __init__(self, method: str = "", path: str = "") -> None:
        self.method = method
        self.path = path
        self._start = 0.0

    def __enter__(self) -> "RequestTimer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: object) -> None:
        elapsed = time.monotonic() - self._start
        metrics.observe("http_request_duration_seconds", elapsed)
        metrics.inc("http_requests_total", labels=f'method="{self.method}",path="{self.path}"')
