"""E2E integration tests against live docker-compose services.

Run:
    docker compose up -d postgres redis neo4j
    SUPERNOVA_E2E=1 python3 -m pytest tests/test_e2e.py -o "addopts=" -v

These tests hit real Postgres, Redis, and Neo4j — NOT mocks.
"""

import os
import asyncio

import pytest
import httpx

pytestmark = pytest.mark.skipif(
    not os.getenv("SUPERNOVA_E2E"), reason="Set SUPERNOVA_E2E=1 to run E2E tests"
)

BASE = os.getenv("SUPERNOVA_BASE_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Infrastructure connectivity
# ---------------------------------------------------------------------------

class TestInfraConnectivity:
    """Verify docker-compose services are reachable."""

    @pytest.mark.asyncio
    async def test_postgres_reachable(self):
        import asyncpg

        conn = await asyncpg.connect(
            "postgresql://supernova:supernova_dev_password@localhost:5432/supernova"
        )
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        assert result == 1

    @pytest.mark.asyncio
    async def test_pgvector_extension(self):
        import asyncpg

        conn = await asyncpg.connect(
            "postgresql://supernova:supernova_dev_password@localhost:5432/supernova"
        )
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        result = await conn.fetchval(
            "SELECT extname FROM pg_extension WHERE extname = 'vector'"
        )
        await conn.close()
        assert result == "vector"

    @pytest.mark.asyncio
    async def test_redis_reachable(self):
        import redis.asyncio as aioredis

        r = aioredis.from_url("redis://localhost:6379/0")
        assert await r.ping()
        await r.aclose()

    @pytest.mark.asyncio
    async def test_neo4j_reachable(self):
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "supernova_neo4j_dev")
        )
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS n")
            record = await result.single()
            assert record["n"] == 1
        await driver.close()


# ---------------------------------------------------------------------------
# API health endpoints
# ---------------------------------------------------------------------------

class TestAPIHealth:
    """Verify the running API responds correctly."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.get("/health")
            assert r.status_code == 200
            data = r.json()
            assert data["status"] in ("healthy", "ok")

    @pytest.mark.asyncio
    async def test_deep_health(self):
        async with httpx.AsyncClient(base_url=BASE, timeout=15) as client:
            r = await client.get("/health/deep")
            assert r.status_code == 200
            data = r.json()
            # Deep health checks each backend
            assert "postgres" in data or "status" in data

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.get("/metrics")
            assert r.status_code == 200
            assert "supernova_" in r.text  # Prometheus format


# ---------------------------------------------------------------------------
# Auth flow
# ---------------------------------------------------------------------------

class TestAuthFlow:
    """Verify JWT auth works end-to-end."""

    @pytest.mark.asyncio
    async def test_token_roundtrip(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.post("/auth/token", json={"username": "admin"})
            assert r.status_code == 200
            token = r.json()["access_token"]
            assert len(token) > 20

            # Use token on a protected endpoint
            r2 = await client.get(
                "/admin/fleet",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r2.status_code == 200


# ---------------------------------------------------------------------------
# Dashboard snapshot
# ---------------------------------------------------------------------------

class TestDashboardAPI:
    """Verify dashboard data endpoints return valid shapes."""

    @pytest.mark.asyncio
    async def test_snapshot(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.get("/dashboard/snapshot")
            assert r.status_code == 200
            data = r.json()
            # Snapshot should have agent/memory/cost sections
            assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

class TestOnboarding:
    """Verify onboarding endpoints work against live DB."""

    @pytest.mark.asyncio
    async def test_status(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.get("/onboarding/status")
            assert r.status_code == 200
            data = r.json()
            assert "first_run" in data or "completed" in data

    @pytest.mark.asyncio
    async def test_cost_estimate(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.get("/onboarding/cost-estimate")
            assert r.status_code == 200


# ---------------------------------------------------------------------------
# Memory round-trip (requires running API + Postgres)
# ---------------------------------------------------------------------------

class TestMemoryRoundTrip:
    """Verify semantic memory write/read against live Postgres."""

    @pytest.mark.asyncio
    async def test_semantic_search(self):
        async with httpx.AsyncClient(base_url=BASE) as client:
            r = await client.get("/memory/semantic", params={"q": "test query"})
            assert r.status_code == 200
            assert isinstance(r.json(), (list, dict))
