"""Audit logging decorator and writer for security-critical operations."""

from __future__ import annotations

import functools
import logging
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

# In-memory buffer flushed by the writer; avoids import-time DB dependency
_audit_buffer: list[dict[str, Any]] = []


def audit_log(action: str, resource: str | None = None) -> Callable:
    """Decorator that records an audit entry for the wrapped function.

    Usage:
        @audit_log("config.update", resource="settings")
        async def update_settings(user_id: str, ...):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_id = kwargs.get("user_id", "system")
            ip_address = kwargs.get("ip_address")
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": str(user_id),
                "action": action,
                "resource": resource or fn.__name__,
                "details": {"args_keys": list(kwargs.keys())},
                "ip_address": ip_address,
            }
            _audit_buffer.append(entry)
            logger.info("AUDIT: %s by %s on %s", action, user_id, resource or fn.__name__)
            return await fn(*args, **kwargs)

        return wrapper

    return decorator


async def write_audit_entry(pool: Any, entry: dict[str, Any]) -> None:
    """Write a single audit entry to the database."""
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO audit_logs (user_id, action, resource, details, ip_address)
               VALUES ($1, $2, $3, $4::json, $5)""",
            entry["user_id"],
            entry["action"],
            entry.get("resource"),
            __import__("json").dumps(entry.get("details")),
            entry.get("ip_address"),
        )


async def flush_audit_buffer(pool: Any) -> int:
    """Flush buffered audit entries to the database. Returns count written."""
    entries = _audit_buffer.copy()
    _audit_buffer.clear()
    for entry in entries:
        await write_audit_entry(pool, entry)
    return len(entries)


async def query_audit_logs(
    pool: Any,
    *,
    user_id: str | None = None,
    action: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Query audit logs with optional filters."""
    conditions = []
    params: list[Any] = []
    idx = 1

    if user_id:
        conditions.append(f"user_id = ${idx}")
        params.append(user_id)
        idx += 1
    if action:
        conditions.append(f"action = ${idx}")
        params.append(action)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""SELECT id, timestamp, user_id, action, resource, details, ip_address
                FROM audit_logs {where}
                ORDER BY timestamp DESC
                LIMIT ${idx} OFFSET ${idx + 1}""",
            *params,
        )
    return [dict(r) for r in rows]
