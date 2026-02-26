"""Celery tasks for automated backup scheduling."""

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


async def _do_backup() -> dict:
    """Run full backup with rotation and verification."""
    from supernova.config import get_settings
    from supernova.core.backup.manager import BackupManager

    settings = get_settings()
    if not settings.backup.enabled:
        return {"status": "skipped", "reason": "backups disabled"}

    mgr = BackupManager.from_settings(settings)

    # Create backup
    archive = await mgr.create_backup()

    # Verify integrity
    verified = await mgr.verify_backup(archive)

    # Rotate old backups
    deleted = mgr.rotate_backups()

    return {
        "status": "ok",
        "archive": str(archive),
        "verified": verified,
        "rotated": deleted,
    }


@app.task(name="supernova.workers.backup.daily_backup")
def daily_backup() -> dict:
    """Celery task: run daily automated backup."""
    logger.info("Starting daily backup")
    result = _run_async(_do_backup())
    logger.info("Backup result: %s", result)
    return result
