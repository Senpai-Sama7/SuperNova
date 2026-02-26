"""Structured JSON logging with correlation IDs and log rotation."""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

import structlog

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def add_correlation_id(
    logger: Any, method_name: str, event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Inject correlation_id from contextvars into every log entry."""
    cid = correlation_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    return event_dict


def configure_logging(
    log_dir: str | Path = "logs",
    level: int = logging.INFO,
    retention_days: int = 30,
) -> None:
    """Set up structlog JSON logging with daily rotation."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    handler = TimedRotatingFileHandler(
        log_path / "supernova.log", when="midnight", backupCount=retention_days, utc=True,
    )
    handler.setLevel(level)

    console = logging.StreamHandler()
    console.setLevel(level)

    logging.basicConfig(level=level, handlers=[handler, console], format="%(message)s")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_correlation_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def generate_correlation_id() -> str:
    """Generate and set a new correlation ID, returning it."""
    cid = uuid.uuid4().hex[:16]
    correlation_id.set(cid)
    return cid
