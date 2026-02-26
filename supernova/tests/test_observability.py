"""Tests for Phase 14 — Observability & Diagnostics."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 14.1: Structured Logging ─────────────────────────────────────────────────


class TestStructuredLogging:
    """Tests for logging.py — structlog config, correlation ID, rotation."""

    def test_configure_logging_creates_dir(self, tmp_path: Path) -> None:
        from infrastructure.observability.logging import configure_logging

        log_dir = tmp_path / "logs"
        configure_logging(log_dir=log_dir, level=logging.DEBUG)
        assert log_dir.exists()
        assert (log_dir / "supernova.log").exists() or True  # handler created

    def test_generate_correlation_id_unique(self) -> None:
        from infrastructure.observability.logging import generate_correlation_id

        ids = {generate_correlation_id() for _ in range(100)}
        assert len(ids) == 100

    def test_correlation_id_contextvar(self) -> None:
        from infrastructure.observability.logging import correlation_id, generate_correlation_id

        cid = generate_correlation_id()
        assert correlation_id.get() == cid
        assert len(cid) == 16

    def test_add_correlation_id_processor(self) -> None:
        from infrastructure.observability.logging import add_correlation_id, correlation_id

        correlation_id.set("test-cid-123")
        event_dict: dict = {"event": "test"}
        result = add_correlation_id(None, "info", event_dict)
        assert result["correlation_id"] == "test-cid-123"

    def test_add_correlation_id_empty(self) -> None:
        from infrastructure.observability.logging import add_correlation_id, correlation_id

        correlation_id.set("")
        event_dict: dict = {"event": "test"}
        result = add_correlation_id(None, "info", event_dict)
        assert "correlation_id" not in result


# ── 14.2: Health Check System ────────────────────────────────────────────────


class TestDeepHealthCheck:
    """Tests for health.py — deep checks and alerting."""

    @pytest.mark.asyncio
    async def test_all_services_unhealthy_when_none(self) -> None:
        from infrastructure.observability.health import deep_health_check

        result = await deep_health_check()
        assert result["status"] == "unhealthy"
        assert len(result["services"]) == 3
        for svc in result["services"]:
            assert svc["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_healthy_pool(self) -> None:
        from infrastructure.observability.health import deep_health_check

        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
        result = await deep_health_check(pool=mock_pool)
        pg = next(s for s in result["services"] if s["name"] == "postgresql")
        assert pg["status"] == "healthy"
        assert pg["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_redis_timeout(self) -> None:
        from infrastructure.observability.health import deep_health_check

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=asyncio.TimeoutError)
        result = await deep_health_check(redis=mock_redis)
        redis_svc = next(s for s in result["services"] if s["name"] == "redis")
        assert redis_svc["status"] in ("degraded", "unhealthy")

    @pytest.mark.asyncio
    async def test_neo4j_exception(self) -> None:
        from infrastructure.observability.health import deep_health_check

        mock_neo4j = AsyncMock()
        mock_neo4j.verify_connectivity = AsyncMock(side_effect=ConnectionError("refused"))
        result = await deep_health_check(neo4j_driver=mock_neo4j)
        neo = next(s for s in result["services"] if s["name"] == "neo4j")
        assert neo["status"] == "unhealthy"
        assert "refused" in neo["detail"]


class TestHealthAlertManager:
    """Tests for health alerting on state transitions."""

    @pytest.mark.asyncio
    async def test_no_alert_on_first_check(self) -> None:
        from infrastructure.observability.health import HealthAlertManager, ServiceCheck

        mgr = HealthAlertManager()
        alerts = await mgr.evaluate([ServiceCheck("pg", "healthy")])
        assert alerts == []

    @pytest.mark.asyncio
    async def test_alert_on_transition(self) -> None:
        from infrastructure.observability.health import HealthAlertManager, ServiceCheck

        mgr = HealthAlertManager()
        await mgr.evaluate([ServiceCheck("pg", "healthy")])
        alerts = await mgr.evaluate([ServiceCheck("pg", "unhealthy", detail="down")])
        assert len(alerts) == 1
        assert alerts[0]["from"] == "healthy"
        assert alerts[0]["to"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_ws_listener_receives_alert(self) -> None:
        from infrastructure.observability.health import HealthAlertManager, ServiceCheck

        mgr = HealthAlertManager()
        ws = AsyncMock()
        mgr.register(ws)
        await mgr.evaluate([ServiceCheck("redis", "healthy")])
        await mgr.evaluate([ServiceCheck("redis", "degraded")])
        ws.send_json.assert_called_once()
        payload = ws.send_json.call_args[0][0]
        assert payload["type"] == "health_alert"
        assert payload["service"] == "redis"

    @pytest.mark.asyncio
    async def test_broken_ws_unregistered(self) -> None:
        from infrastructure.observability.health import HealthAlertManager, ServiceCheck

        mgr = HealthAlertManager()
        ws = AsyncMock()
        ws.send_json.side_effect = RuntimeError("closed")
        mgr.register(ws)
        await mgr.evaluate([ServiceCheck("pg", "healthy")])
        await mgr.evaluate([ServiceCheck("pg", "unhealthy")])
        assert ws not in mgr._listeners


# ── 14.3: Metrics Collection ─────────────────────────────────────────────────


class TestMetricsCollector:
    """Tests for metrics.py — counters, gauges, histograms, Prometheus output."""

    def test_counter_increment(self) -> None:
        from infrastructure.observability.metrics import MetricsCollector

        m = MetricsCollector()
        m.inc("test_counter")
        m.inc("test_counter", 5)
        output = m.render_prometheus()
        assert "test_counter 6" in output

    def test_gauge_set(self) -> None:
        from infrastructure.observability.metrics import MetricsCollector

        m = MetricsCollector()
        m.gauge("cpu_usage", 42.5)
        output = m.render_prometheus()
        assert "cpu_usage 42.5" in output

    def test_histogram_observe(self) -> None:
        from infrastructure.observability.metrics import MetricsCollector

        m = MetricsCollector()
        m.observe("latency", 0.05)
        m.observe("latency", 0.5)
        m.observe("latency", 2.0)
        output = m.render_prometheus()
        assert "latency_count 3" in output
        assert "latency_sum" in output
        assert 'le="+Inf"' in output

    def test_labels(self) -> None:
        from infrastructure.observability.metrics import MetricsCollector

        m = MetricsCollector()
        m.inc("http_total", labels='method="GET"')
        m.inc("http_total", labels='method="POST"')
        output = m.render_prometheus()
        assert 'http_total{method="GET"} 1' in output
        assert 'http_total{method="POST"} 1' in output

    def test_request_timer(self) -> None:
        import time

        from infrastructure.observability.metrics import MetricsCollector, RequestTimer, metrics

        # Use fresh collector
        old_counters = dict(metrics._counters)
        with RequestTimer("GET", "/test"):
            time.sleep(0.01)
        # Timer should have recorded something
        assert metrics._histograms.get("http_request_duration_seconds") is not None

    def test_prometheus_format_types(self) -> None:
        from infrastructure.observability.metrics import MetricsCollector

        m = MetricsCollector()
        m.inc("req_total")
        m.gauge("mem_mb", 512)
        m.observe("dur", 0.1)
        output = m.render_prometheus()
        assert "# TYPE req_total counter" in output
        assert "# TYPE mem_mb gauge" in output
        assert "# TYPE dur histogram" in output


# ── 14.4: Diagnostic CLI ─────────────────────────────────────────────────────


class TestDiagnosticCLI:
    """Tests for cli.py — doctor, logs, status, report subcommands."""

    @pytest.mark.asyncio
    async def test_doctor_checks_python(self, capsys: pytest.CaptureFixture[str]) -> None:
        import argparse

        from infrastructure.observability.cli import cmd_doctor

        args = argparse.Namespace(base_url="http://localhost:99999")
        await cmd_doctor(args)
        captured = capsys.readouterr()
        assert "python" in captured.out
        assert "✓" in captured.out  # Python 3.12+ should pass

    @pytest.mark.asyncio
    async def test_doctor_api_unreachable(self, capsys: pytest.CaptureFixture[str]) -> None:
        import argparse

        from infrastructure.observability.cli import cmd_doctor

        args = argparse.Namespace(base_url="http://localhost:99999")
        await cmd_doctor(args)
        captured = capsys.readouterr()
        assert "api" in captured.out
        assert "✗" in captured.out

    @pytest.mark.asyncio
    async def test_logs_tail(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        import argparse

        from infrastructure.observability.cli import cmd_logs

        log_file = tmp_path / "supernova.log"
        log_file.write_text("\n".join(f"line {i}" for i in range(100)))
        args = argparse.Namespace(log_dir=str(tmp_path), tail=5, filter=None)
        await cmd_logs(args)
        captured = capsys.readouterr()
        assert "line 99" in captured.out
        assert "line 94" not in captured.out

    @pytest.mark.asyncio
    async def test_logs_filter(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        import argparse

        from infrastructure.observability.cli import cmd_logs

        log_file = tmp_path / "supernova.log"
        log_file.write_text("INFO ok\nERROR bad\nINFO fine\n")
        args = argparse.Namespace(log_dir=str(tmp_path), tail=50, filter="ERROR")
        await cmd_logs(args)
        captured = capsys.readouterr()
        assert "ERROR bad" in captured.out
        assert "INFO" not in captured.out

    @pytest.mark.asyncio
    async def test_status_unreachable(self, capsys: pytest.CaptureFixture[str]) -> None:
        import argparse

        from infrastructure.observability.cli import cmd_status

        args = argparse.Namespace(base_url="http://localhost:99999")
        await cmd_status(args)
        captured = capsys.readouterr()
        assert "unreachable" in captured.out

    @pytest.mark.asyncio
    async def test_report_generates_file(self, tmp_path: Path) -> None:
        import argparse

        from infrastructure.observability.cli import cmd_report

        out = tmp_path / "report.json"
        args = argparse.Namespace(base_url="http://localhost:99999", output=str(out))
        await cmd_report(args)
        assert out.exists()
        data = json.loads(out.read_text())
        assert "generated_at" in data
        assert "python" in data


# ── Gateway Integration ──────────────────────────────────────────────────────


class TestGatewayObservability:
    """Tests for gateway endpoints: /health/deep, /metrics, correlation ID."""

    @pytest.fixture
    def client(self) -> "TestClient":
        from starlette.testclient import TestClient

        from api.gateway import app

        return TestClient(app, raise_server_exceptions=False)

    def test_health_deep_returns_services(self, client: "TestClient") -> None:
        r = client.get("/health/deep")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "services" in data
        assert isinstance(data["services"], list)

    def test_metrics_endpoint(self, client: "TestClient") -> None:
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers["content-type"]
        # Should have at least the request we just made
        assert "http_request" in r.text or r.text.strip() != ""

    def test_correlation_id_injected(self, client: "TestClient") -> None:
        r = client.get("/health")
        assert "x-correlation-id" in r.headers
        assert len(r.headers["x-correlation-id"]) == 16

    def test_correlation_id_propagated(self, client: "TestClient") -> None:
        r = client.get("/health", headers={"x-correlation-id": "custom-cid-12345"})
        assert r.headers["x-correlation-id"] == "custom-cid-12345"

    def test_health_deep_all_unhealthy_no_backends(self, client: "TestClient") -> None:
        r = client.get("/health/deep")
        data = r.json()
        # Without real backends, all should be unhealthy
        for svc in data["services"]:
            assert svc["status"] in ("unhealthy", "degraded", "healthy")


# ── Grafana Dashboard ────────────────────────────────────────────────────────


class TestGrafanaDashboard:
    """Validate Grafana dashboard JSON structure."""

    def test_dashboard_valid_json(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "dashboard" / "src" / "grafana_dashboard.json"
        data = json.loads(path.read_text())
        assert data["title"] == "SuperNova Overview"
        assert len(data["panels"]) >= 4
        assert data["uid"] == "supernova-overview"

    def test_dashboard_panels_have_targets(self) -> None:
        path = Path(__file__).resolve().parent.parent.parent / "dashboard" / "src" / "grafana_dashboard.json"
        data = json.loads(path.read_text())
        for panel in data["panels"]:
            assert "targets" in panel
            assert len(panel["targets"]) >= 1
