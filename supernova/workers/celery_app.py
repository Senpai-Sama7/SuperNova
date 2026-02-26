"""Celery application with RedBeat scheduler for background workers."""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

REDIS_BROKER = os.getenv("REDIS_CELERY_URL", "redis://localhost:6379/1")
REDIS_BACKEND = REDIS_BROKER

app = Celery("supernova", broker=REDIS_BROKER, backend=REDIS_BACKEND)

app.conf.update(
    beat_scheduler="redbeat.RedBeatScheduler",
    redbeat_redis_url=REDIS_BROKER,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "consolidation-hourly": {
            "task": "supernova.workers.consolidation.consolidate_episodic_memories",
            "schedule": crontab(minute=0),  # every hour
        },
        "heartbeat-15min": {
            "task": "supernova.workers.heartbeat.run_heartbeat_cycle",
            "schedule": 900.0,  # 15 minutes
        },
        "forgetting-weekly": {
            "task": "supernova.workers.maintenance.run_forgetting_curves",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3am
        },
        "skill-crystallization-daily": {
            "task": "supernova.workers.consolidation.crystallize_skills",
            "schedule": crontab(hour=2, minute=0),  # daily 2am
        },
        "mcp-health-5min": {
            "task": "supernova.workers.mcp_monitor.check_mcp_health",
            "schedule": 300.0,  # 5 minutes
        },
    },
)

app.autodiscover_tasks([
    "supernova.workers.consolidation",
    "supernova.workers.heartbeat",
    "supernova.workers.maintenance",
    "supernova.workers.mcp_monitor",
])
