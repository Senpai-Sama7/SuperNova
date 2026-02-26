"""Heartbeat worker: periodic status checks and Langfuse background traces."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from supernova.workers.celery_app import app

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _do_heartbeat() -> dict:
    """Check system health and log to Langfuse."""
    status = {
        "timestamp": time.time(),
        "redis": "unknown",
        "postgres": "unknown",
        "neo4j": "unknown",
    }

    # Check Redis
    try:
        from supernova.infrastructure.storage.redis import AsyncRedisClient
        rc = AsyncRedisClient()
        await rc.connect()
        await rc.client.ping()
        status["redis"] = "healthy"
        await rc.disconnect()
    except Exception as e:
        status["redis"] = f"unhealthy: {e}"

    # Check Postgres
    try:
        from supernova.infrastructure.storage.postgres import AsyncPostgresPool
        pg = AsyncPostgresPool()
        await pg.connect()
        async with pg.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        status["postgres"] = "healthy"
        await pg.disconnect()
    except Exception as e:
        status["postgres"] = f"unhealthy: {e}"

    # Check Neo4j
    try:
        from supernova.core.memory.episodic import EpisodicMemoryStore
        ep = EpisodicMemoryStore()
        await ep.initialize()
        status["neo4j"] = "healthy"
    except Exception as e:
        status["neo4j"] = f"unhealthy: {e}"

    # Log to Langfuse if available
    try:
        from langfuse import Langfuse
        lf = Langfuse()
        trace = lf.trace(name="heartbeat", metadata=status)
        trace.update(output=status)
        lf.flush()
    except Exception:
        logger.debug("Langfuse not available for heartbeat trace")

    return status


@app.task(name="supernova.workers.heartbeat.run_heartbeat_cycle")
def run_heartbeat_cycle() -> dict:
    """Celery task: run heartbeat checks on all infrastructure."""
    logger.info("Starting heartbeat cycle")
    result = _run_async(_do_heartbeat())
    logger.info("Heartbeat: %s", result)
    return result
