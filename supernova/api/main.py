"""FastAPI application entrypoint for SuperNova APIs."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import AsyncGraphDatabase

from supernova.api.routes.agent import router as agent_router
from supernova.api.routes.dashboard import router as dashboard_router
from supernova.config import get_settings
from supernova.infrastructure.storage import (
    close_postgres_pool,
    close_redis_client,
    get_postgres_pool,
    get_redis_client,
)
from supernova.runtime_config_guardrails import validate_runtime_configuration

settings = get_settings()
validate_runtime_configuration()


@asynccontextmanager
async def _lifespan(_: FastAPI):
    """Manage application startup and shutdown resources."""
    yield
    await close_postgres_pool()
    await close_redis_client()


app = FastAPI(
    title="SuperNova API",
    version="2.0.0",
    description="Live operational APIs for SuperNova agent platform.",
    lifespan=_lifespan,
)

cors_origins = set(settings.security.cors_origins_list)
if settings.is_development:
    cors_origins.update(
        {
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(agent_router)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness/readiness endpoint with real backend checks."""
    status: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {
            "postgres": False,
            "redis": False,
            "neo4j": False,
        },
    }

    try:
        pool = await get_postgres_pool()
        value = await pool.fetchval("SELECT 1")
        status["services"]["postgres"] = value == 1
    except Exception:
        status["services"]["postgres"] = False

    try:
        redis_client = await get_redis_client()
        pong = await redis_client.get_client().ping()
        status["services"]["redis"] = bool(pong)
    except Exception:
        status["services"]["redis"] = False

    try:
        driver = AsyncGraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.user, settings.neo4j.password),
        )
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            status["services"]["neo4j"] = bool(record and record["ok"] == 1)
        await driver.close()
    except Exception:
        status["services"]["neo4j"] = False

    status["ok"] = all(status["services"].values())
    return status
