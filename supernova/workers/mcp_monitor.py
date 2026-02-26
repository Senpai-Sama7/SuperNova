"""MCP health monitoring worker: ping servers, auto-restart with backoff."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from supernova.workers.celery_app import app

logger = logging.getLogger(__name__)

# Track consecutive failures per server for exponential backoff
_failure_counts: dict[str, int] = {}
_last_restart: dict[str, float] = {}
MAX_FAILURES_BEFORE_ALERT = 3
BASE_BACKOFF_SECONDS = 30.0


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


def _backoff_seconds(failures: int) -> float:
    """Exponential backoff: 30s, 60s, 120s, ..."""
    return BASE_BACKOFF_SECONDS * (2 ** min(failures - 1, 5))


async def _do_health_check() -> dict:
    """Ping all MCP servers and restart unhealthy ones."""
    from supernova.mcp.client.mcp_client import MCPClient

    summary = {"checked": 0, "healthy": 0, "restarted": 0, "alerts": []}

    try:
        client = MCPClient()
        statuses = client.get_server_status()
        summary["checked"] = len(statuses)

        await client.health_check()

        for s in client.get_server_status():
            name = s["name"]
            if s["healthy"]:
                _failure_counts.pop(name, None)
                summary["healthy"] += 1
                continue

            # Track failure
            _failure_counts[name] = _failure_counts.get(name, 0) + 1
            failures = _failure_counts[name]

            # Alert after threshold
            if failures >= MAX_FAILURES_BEFORE_ALERT:
                msg = f"MCP server '{name}' failed {failures} consecutive health checks"
                summary["alerts"].append(msg)
                logger.warning(msg)

            # Exponential backoff for restart
            backoff = _backoff_seconds(failures)
            last = _last_restart.get(name, 0)
            if time.time() - last < backoff:
                logger.info("Skipping restart of '%s' (backoff %.0fs)", name, backoff)
                continue

            # Attempt restart
            try:
                config = s.get("config")
                if config:
                    await client.stop_server(name) if hasattr(client, "stop_server") else None
                    await client.start_server(config)
                    _last_restart[name] = time.time()
                    summary["restarted"] += 1
                    logger.info("Restarted MCP server '%s'", name)
            except Exception as e:
                logger.error("Failed to restart MCP server '%s': %s", name, e)

    except Exception as e:
        logger.error("MCP health check failed: %s", e)

    # Log to Langfuse
    try:
        from langfuse import Langfuse
        lf = Langfuse()
        lf.trace(name="mcp-health-check", metadata=summary)
        lf.flush()
    except Exception:
        pass

    return summary


@app.task(name="supernova.workers.mcp_monitor.check_mcp_health")
def check_mcp_health() -> dict:
    """Celery task: check MCP server health and restart unhealthy servers."""
    logger.info("Starting MCP health check")
    result = _run_async(_do_health_check())
    logger.info("MCP health check complete: %s", result)
    return result
