"""Maintenance worker: forgetting curves and memory decay."""

from __future__ import annotations

import asyncio
import logging
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


async def _do_forgetting() -> dict:
    """Execute forgetting curves stored procedure via asyncpg."""
    summary = {"rows_affected": 0, "errors": 0}

    try:
        from supernova.infrastructure.storage.postgres import AsyncPostgresPool
        pg = AsyncPostgresPool()
        await pg.connect()
        async with pg.pool.acquire() as conn:
            result = await conn.execute("CALL run_forgetting_curves()")
            # Extract row count if available
            if result:
                parts = result.split()
                for p in parts:
                    if p.isdigit():
                        summary["rows_affected"] = int(p)
                        break
        await pg.disconnect()
    except Exception as e:
        logger.error("Forgetting curves failed: %s", e)
        summary["errors"] += 1

    return summary


@app.task(name="supernova.workers.maintenance.run_forgetting_curves")
def run_forgetting_curves() -> dict:
    """Celery task: apply forgetting curves to decay stale memories."""
    logger.info("Starting forgetting curves maintenance")
    result = _run_async(_do_forgetting())
    logger.info("Forgetting curves complete: %s", result)
    return result
