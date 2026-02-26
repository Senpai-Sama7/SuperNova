"""Consolidation worker: episodic→semantic transfer and skill crystallization."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from supernova.workers.celery_app import app

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    """Run async coroutine from sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _do_consolidation() -> dict:
    """Fetch recent episodes and extract facts into semantic memory."""
    from supernova.core.memory.episodic import EpisodicMemoryStore
    from supernova.core.memory.semantic import SemanticMemoryStore

    summary = {"episodes_fetched": 0, "facts_extracted": 0, "errors": 0}

    try:
        episodic = EpisodicMemoryStore()
        semantic = SemanticMemoryStore()

        episodes = await episodic.search("*", num_results=100)
        summary["episodes_fetched"] = len(episodes)

        for ep in episodes:
            try:
                content = ep.get("fact", "") or ep.get("content", "")
                if not content:
                    continue
                await semantic.store(
                    content=content,
                    metadata={"source": "consolidation", "episode_id": ep.get("uuid", "")},
                )
                summary["facts_extracted"] += 1
            except Exception as e:
                logger.error("Failed to consolidate episode: %s", e)
                summary["errors"] += 1

    except Exception as e:
        logger.error("Consolidation failed: %s", e)
        summary["errors"] += 1

    return summary


async def _do_crystallization() -> dict:
    """Run skill crystallization cycle via procedural memory."""
    summary = {"crystallized": 0, "errors": 0}

    try:
        # Late import to avoid circular deps and missing infra
        import importlib
        proc_mod = importlib.import_module("procedural")
        worker_cls = getattr(proc_mod, "SkillCrystallizationWorker")

        # These would be injected from app state in production
        worker = worker_cls.__new__(worker_cls)
        result = await worker.run_crystallization_cycle()
        summary.update(result)
    except Exception as e:
        logger.error("Crystallization failed: %s", e)
        summary["errors"] += 1

    return summary


@app.task(name="supernova.workers.consolidation.consolidate_episodic_memories")
def consolidate_episodic_memories() -> dict:
    """Celery task: consolidate episodic memories into semantic store."""
    logger.info("Starting episodic→semantic consolidation")
    result = _run_async(_do_consolidation())
    logger.info("Consolidation complete: %s", result)
    return result


@app.task(name="supernova.workers.consolidation.crystallize_skills")
def crystallize_skills() -> dict:
    """Celery task: crystallize high-performing traces into compiled skills."""
    logger.info("Starting skill crystallization")
    result = _run_async(_do_crystallization())
    logger.info("Crystallization complete: %s", result)
    return result
