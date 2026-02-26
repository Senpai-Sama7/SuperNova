"""Tests for api/routes/dashboard.py — helpers and endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from supernova.api.routes.dashboard import (
    _age_label,
    _clamp,
    _compute_conformal_metrics,
    _derive_status,
    _details_as_dict,
    _hash_position,
    _parse_iso_datetime,
    _safe_float,
)

# ── Pure helper tests ──────────────────────────────────────────────


class TestSafeFloat:
    def test_valid(self):
        assert _safe_float("3.14") == 3.14

    def test_none(self):
        assert _safe_float(None) is None

    def test_nan(self):
        assert _safe_float(float("nan")) is None

    def test_inf(self):
        assert _safe_float(float("inf")) is None


class TestClamp:
    def test_within(self):
        assert _clamp(0.5, 0.0, 1.0) == 0.5

    def test_below(self):
        assert _clamp(-1.0, 0.0, 1.0) == 0.0

    def test_above(self):
        assert _clamp(2.0, 0.0, 1.0) == 1.0


class TestParseIsoDatetime:
    def test_valid_naive(self):
        result = _parse_iso_datetime("2024-01-15T10:30:00")
        assert result is not None and result.tzinfo is not None

    def test_valid_aware(self):
        result = _parse_iso_datetime("2024-01-15T10:30:00+00:00")
        assert result is not None

    def test_invalid(self):
        assert _parse_iso_datetime("not-a-date") is None

    def test_non_string(self):
        assert _parse_iso_datetime(12345) is None


class TestAgeLabel:
    def test_none(self):
        assert _age_label(None) == "unknown"

    def test_seconds(self):
        assert _age_label(datetime.now(UTC) - timedelta(seconds=30)).endswith("s")

    def test_minutes(self):
        assert _age_label(datetime.now(UTC) - timedelta(minutes=5)).endswith("m")

    def test_hours(self):
        assert _age_label(datetime.now(UTC) - timedelta(hours=2)).endswith("h")

    def test_days(self):
        assert _age_label(datetime.now(UTC) - timedelta(days=3)).endswith("d")


class TestHashPosition:
    def test_deterministic(self):
        a = _hash_position("test-id")
        b = _hash_position("test-id")
        assert a == b

    def test_range(self):
        x, y = _hash_position("anything")
        assert 10 <= x <= 90 and 10 <= y <= 90


class TestDetailsAsDict:
    def test_dict_passthrough(self):
        assert _details_as_dict({"a": 1}) == {"a": 1}

    def test_json_string(self):
        assert _details_as_dict('{"b": 2}') == {"b": 2}

    def test_invalid_string(self):
        assert _details_as_dict("not json") == {}

    def test_non_dict_json(self):
        assert _details_as_dict("[1,2]") == {}

    def test_other_type(self):
        assert _details_as_dict(42) == {}


class TestDeriveStatus:
    def test_none(self):
        assert _derive_status(None) == "unknown"

    def test_active(self):
        assert _derive_status(datetime.now(UTC)) == "active"

    def test_reasoning(self):
        assert _derive_status(datetime.now(UTC) - timedelta(seconds=120)) == "reasoning"

    def test_waiting(self):
        assert _derive_status(datetime.now(UTC) - timedelta(minutes=10)) == "waiting"

    def test_idle(self):
        assert _derive_status(datetime.now(UTC) - timedelta(hours=2)) == "idle"


class TestConformalMetrics:
    def test_too_few_points(self):
        result = _compute_conformal_metrics([{"actual": 0.5, "predicted": 0.5}])
        assert result["coverage"] is None

    def test_with_stream(self):
        stream = [
            {"actual": 0.5, "predicted": 0.5},
            {"actual": 0.6, "predicted": 0.55},
            {"actual": 0.7, "predicted": 0.65},
            {"actual": 0.8, "predicted": 0.75},
            {"actual": 0.9, "predicted": 0.85},
        ]
        result = _compute_conformal_metrics(stream)
        assert result["interval_lower"] is not None
        assert result["interval_upper"] is not None

    def test_no_valid_data(self):
        stream = [
            {"actual": "bad", "predicted": "bad"},
            {"actual": "bad", "predicted": "bad"},
            {"actual": "bad", "predicted": "bad"},
            {"actual": "bad", "predicted": "bad"},
        ]
        result = _compute_conformal_metrics(stream)
        assert result["coverage"] is None


# ── Endpoint tests ─────────────────────────────────────────────────


def _make_mock_pool():
    """Build a mock pool that returns plausible dashboard data."""
    pool = AsyncMock()

    # metrics_row
    pool.fetchrow.side_effect = [
        # First call: metrics_row
        {
            "total_calls": 100,
            "success_count": 80,
            "failure_count": 20,
            "avg_latency_sec": 1.5,
            "cost_usd": 0.42,
            "skills_compiled": 3,
            "semantic_memories": 50,
        },
        # Second call: checkpoint_row
        {
            "checkpoint": json.dumps({"phase": "reason", "step": 4, "phase_progress": 0.6}),
            "metadata": "{}",
            "type": "agent",
        },
    ]

    now = datetime.now(UTC)
    # stream_rows, memory_rows, cluster_rows, approval_rows, model_rows
    pool.fetch.side_effect = [
        # stream_rows
        [
            {"timestamp": now, "regime": "normal", "actual": 0.8, "predicted": 0.75},
        ],
        # memory_rows
        [
            {
                "id": "abc-123",
                "content": "test memory",
                "category": "fact",
                "confidence": 0.9,
                "importance": 0.8,
                "created_at": now,
            }
        ],
        # cluster_rows
        [{"cluster": "fact", "count": 10}],
        # approval_rows
        [],
        # model_rows
        [
            {
                "model": "gpt-4",
                "invocations": 50,
                "success_rate": 0.95,
                "avg_latency_sec": 1.2,
                "avg_cost_usd": 0.01,
            }
        ],
    ]
    return pool


def _make_app():
    """Build a minimal FastAPI app with the dashboard router mounted."""
    from fastapi import FastAPI

    from supernova.api.routes.dashboard import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.mark.asyncio
async def test_dashboard_snapshot():
    mock_pool = _make_mock_pool()
    mock_redis = AsyncMock()
    mock_redis.working_memory_list = AsyncMock(return_value=[])

    with (
        patch("supernova.api.routes.dashboard.get_postgres_pool", return_value=mock_pool),
        patch("supernova.api.routes.dashboard.get_redis_client", return_value=mock_redis),
        patch("supernova.api.routes.dashboard._neo4j_node_count", return_value=42),
    ):
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/dashboard/snapshot")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"]["total_calls"] == 100
    assert data["metrics"]["episodic_nodes"] == 42
    assert data["cognitive_loop"]["phase"] == "reason"
    assert len(data["memory_nodes"]) == 1
    assert len(data["model_fleet"]) == 1


@pytest.mark.asyncio
async def test_resolve_approval_not_found():
    mock_pool = AsyncMock()
    mock_pool.fetchrow.return_value = None

    with patch("supernova.api.routes.dashboard.get_postgres_pool", return_value=mock_pool):
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/dashboard/approvals/fake-id/resolve",
                json={"approved": True, "actor": "tester"},
            )
    assert resp.status_code == 404
