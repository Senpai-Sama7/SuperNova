"""Dashboard API routes backed by live system state.

This module exposes read/write endpoints for the monitoring dashboard.
All values are derived from real stores (PostgreSQL, Redis, Neo4j) and
never synthesized with simulated/random data.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel, Field

from supernova.config import get_settings
from supernova.infrastructure.storage import get_postgres_pool, get_redis_client

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)


class ApprovalResolutionRequest(BaseModel):
    """Payload for resolving a pending approval."""

    approved: bool
    actor: str = Field(default="operator", min_length=1, max_length=255)


def _safe_float(value: Any) -> float | None:
    """Convert value to finite float, returning None for invalid inputs."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def _clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp float into an inclusive range."""
    return max(min_value, min(max_value, value))


def _parse_iso_datetime(value: Any) -> datetime | None:
    """Parse an ISO timestamp into timezone-aware UTC datetime."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _age_label(ts: datetime | None) -> str:
    """Convert timestamp to compact age label."""
    if ts is None:
        return "unknown"
    now = datetime.now(UTC)
    delta_seconds = max(0, int((now - ts).total_seconds()))
    if delta_seconds < 60:
        return f"{delta_seconds}s"
    if delta_seconds < 3600:
        return f"{delta_seconds // 60}m"
    if delta_seconds < 86400:
        return f"{delta_seconds // 3600}h"
    return f"{delta_seconds // 86400}d"


def _hash_position(identifier: str) -> tuple[int, int]:
    """Generate deterministic x/y graph coordinates from an identifier."""
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    x_seed = int(digest[:8], 16)
    y_seed = int(digest[8:16], 16)
    x = 10 + (x_seed % 81)  # 10..90
    y = 10 + (y_seed % 81)  # 10..90
    return x, y


def _details_as_dict(details: Any) -> dict[str, Any]:
    """Normalize JSON/JSONB payloads into a dictionary."""
    if isinstance(details, dict):
        return details
    if isinstance(details, str):
        try:
            parsed = json.loads(details)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _derive_status(last_updated: datetime | None) -> str:
    """Map recency to a simple agent status label."""
    if last_updated is None:
        return "unknown"
    age_seconds = max(0, int((datetime.now(UTC) - last_updated).total_seconds()))
    if age_seconds <= 60:
        return "active"
    if age_seconds <= 300:
        return "reasoning"
    if age_seconds <= 1800:
        return "waiting"
    return "idle"


def _compute_conformal_metrics(
    stream: list[dict[str, Any]],
) -> dict[str, float | None]:
    """Compute conformal-style interval and empirical coverage from stream."""
    if len(stream) < 4:
        return {
            "interval_lower": None,
            "interval_upper": None,
            "coverage": None,
        }

    rolling_residuals: list[float] = []
    hits = 0
    trials = 0
    latest_q = 0.0

    for point in stream:
        actual = _safe_float(point.get("actual"))
        predicted = _safe_float(point.get("predicted"))
        if actual is None or predicted is None:
            continue

        residual = abs(actual - predicted)
        if len(rolling_residuals) >= 3:
            sorted_residuals = sorted(rolling_residuals)
            q_index = int(0.9 * (len(sorted_residuals) - 1))
            latest_q = sorted_residuals[q_index]
            within_interval = residual <= latest_q
            hits += 1 if within_interval else 0
            trials += 1
        rolling_residuals.append(residual)

    if not rolling_residuals:
        return {
            "interval_lower": None,
            "interval_upper": None,
            "coverage": None,
        }

    latest = stream[-1]
    latest_predicted = _safe_float(latest.get("predicted"))
    if latest_predicted is None:
        return {
            "interval_lower": None,
            "interval_upper": None,
            "coverage": None,
        }

    interval_lower = _clamp(latest_predicted - latest_q, 0.0, 1.0)
    interval_upper = _clamp(latest_predicted + latest_q, 0.0, 1.0)
    coverage = (hits / trials) if trials > 0 else None

    return {
        "interval_lower": interval_lower,
        "interval_upper": interval_upper,
        "coverage": coverage,
    }


async def _neo4j_node_count() -> int:
    """Count nodes in Neo4j to expose live episodic graph size."""
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.user, settings.neo4j.password),
    )
    try:
        async with driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) AS count")
            record = await result.single()
            if record is None:
                return 0
            return int(record["count"])
    finally:
        await driver.close()


@router.get("/snapshot")
async def get_dashboard_snapshot() -> dict[str, Any]:
    """Return a live dashboard snapshot from real storage backends."""
    source_errors: list[str] = []
    pool = None

    try:
        pool = await get_postgres_pool()
    except Exception as exc:  # pragma: no cover - integration failure path
        logger.exception("PostgreSQL unavailable for dashboard snapshot")
        raise HTTPException(
            status_code=503,
            detail=f"PostgreSQL unavailable: {exc}",
        ) from exc

    metrics_row = await pool.fetchrow(
        """
        SELECT
            (SELECT COUNT(*)::bigint FROM audit_log) AS total_calls,
            (SELECT COALESCE(SUM(success_count), 0)::bigint FROM procedural_memories) AS success_count,
            (SELECT COALESCE(SUM(failure_count), 0)::bigint FROM procedural_memories) AS failure_count,
            (SELECT AVG((details->>'latency_sec')::double precision)
             FROM audit_log
             WHERE details ? 'latency_sec'
               AND (details->>'latency_sec') ~ '^-?[0-9]+(\\.[0-9]+)?$') AS avg_latency_sec,
            (SELECT COALESCE(SUM((details->>'cost_usd')::double precision), 0.0)
             FROM audit_log
             WHERE details ? 'cost_usd'
               AND (details->>'cost_usd') ~ '^-?[0-9]+(\\.[0-9]+)?$') AS cost_usd,
            (SELECT COUNT(*)::bigint FROM procedural_memories WHERE is_active = true) AS skills_compiled,
            (SELECT COUNT(*)::bigint FROM semantic_memories) AS semantic_memories
        """
    )
    if metrics_row is None:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=500, detail="Unable to load dashboard metrics")

    total_calls = int(metrics_row["total_calls"] or 0)
    success_count = int(metrics_row["success_count"] or 0)
    failure_count = int(metrics_row["failure_count"] or 0)
    avg_latency_sec = _safe_float(metrics_row["avg_latency_sec"])
    cost_usd = _safe_float(metrics_row["cost_usd"]) or 0.0
    skills_compiled = int(metrics_row["skills_compiled"] or 0)
    semantic_memories = int(metrics_row["semantic_memories"] or 0)
    trial_count = success_count + failure_count
    success_rate = (success_count / trial_count) if trial_count > 0 else 0.0

    stream_rows = await pool.fetch(
        """
        SELECT
            timestamp,
            COALESCE(details->>'regime', 'unknown') AS regime,
            (details->>'actual')::double precision AS actual,
            (details->>'predicted')::double precision AS predicted
        FROM audit_log
        WHERE details ? 'actual'
          AND details ? 'predicted'
          AND (details->>'actual') ~ '^-?[0-9]+(\\.[0-9]+)?$'
          AND (details->>'predicted') ~ '^-?[0-9]+(\\.[0-9]+)?$'
        ORDER BY timestamp DESC
        LIMIT 120
        """
    )
    stream = [
        {
            "timestamp": row["timestamp"].astimezone(UTC).isoformat(),
            "actual": float(row["actual"]),
            "predicted": float(row["predicted"]),
            "regime": str(row["regime"]),
        }
        for row in reversed(stream_rows)
    ]

    latest_decision = stream[-1] if stream else None
    decision = {
        "actual": latest_decision["actual"] if latest_decision else None,
        "predicted": latest_decision["predicted"] if latest_decision else None,
        "regime": latest_decision["regime"] if latest_decision else None,
    }

    checkpoint_row = await pool.fetchrow(
        """
        SELECT checkpoint, metadata, type
        FROM checkpoints
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    cognitive_loop = {
        "phase": None,
        "step": None,
        "phase_progress": None,
    }
    if checkpoint_row:
        checkpoint = _details_as_dict(checkpoint_row["checkpoint"])
        metadata = _details_as_dict(checkpoint_row["metadata"])
        channel_values = _details_as_dict(checkpoint.get("channel_values"))

        phase = (
            checkpoint.get("phase")
            or channel_values.get("phase")
            or metadata.get("phase")
            or checkpoint_row["type"]
        )
        step = checkpoint.get("step") or channel_values.get("step") or metadata.get("step")
        progress = (
            checkpoint.get("phase_progress")
            or channel_values.get("phase_progress")
            or metadata.get("phase_progress")
        )
        cognitive_loop = {
            "phase": str(phase) if phase is not None else None,
            "step": int(step) if step is not None else None,
            "phase_progress": _safe_float(progress),
        }

    memory_rows = await pool.fetch(
        """
        SELECT
            id::text AS id,
            content,
            category,
            confidence,
            importance,
            created_at
        FROM semantic_memories
        ORDER BY created_at DESC
        LIMIT 60
        """
    )
    memory_nodes: list[dict[str, Any]] = []
    for row in memory_rows:
        node_id = str(row["id"])
        label_source = str(row["content"] or "").strip()
        label = label_source[:48] if label_source else node_id
        strength = _safe_float(row["confidence"])
        if strength is None:
            strength = _safe_float(row["importance"])
        if strength is None:
            strength = 0.0
        strength = _clamp(strength, 0.0, 1.0)
        x, y = _hash_position(node_id)
        created_at = row["created_at"]
        if isinstance(created_at, datetime):
            created_at = created_at.astimezone(UTC)
        else:
            created_at = None

        memory_nodes.append(
            {
                "id": node_id,
                "label": label,
                "type": str(row["category"] or "uncategorized"),
                "strength": strength,
                "age": _age_label(created_at),
                "x": x,
                "y": y,
            }
        )

    cluster_rows = await pool.fetch(
        """
        SELECT
            COALESCE(NULLIF(category, ''), 'uncategorized') AS cluster,
            COUNT(*)::bigint AS count
        FROM semantic_memories
        GROUP BY COALESCE(NULLIF(category, ''), 'uncategorized')
        ORDER BY count DESC
        LIMIT 12
        """
    )
    cluster_total = sum(int(row["count"]) for row in cluster_rows)
    semantic_clusters = [
        {
            "name": str(row["cluster"]),
            "count": int(row["count"]),
            "probability": (int(row["count"]) / cluster_total) if cluster_total > 0 else 0.0,
        }
        for row in cluster_rows
    ]

    approval_rows = await pool.fetch(
        """
        SELECT id::text AS id, timestamp, details
        FROM audit_log
        WHERE action = 'tool_approval_requested'
          AND COALESCE(details->>'status', 'pending') = 'pending'
        ORDER BY timestamp DESC
        LIMIT 100
        """
    )
    now = datetime.now(UTC)
    pending_approvals: list[dict[str, Any]] = []
    for row in approval_rows:
        details = _details_as_dict(row["details"])
        timeout_seconds = int(details.get("timeout_seconds") or 0)
        created_at = row["timestamp"].astimezone(UTC)
        elapsed = int((now - created_at).total_seconds())
        expires_seconds = max(0, timeout_seconds - elapsed) if timeout_seconds > 0 else None

        pending_approvals.append(
            {
                "id": str(row["id"]),
                "tool": str(details.get("tool") or "unknown"),
                "risk": str(details.get("risk") or "unknown"),
                "agent": str(details.get("agent") or "unknown"),
                "args": details.get("args") if isinstance(details.get("args"), dict) else {},
                "expires_seconds": expires_seconds,
                "created_at": created_at.isoformat(),
            }
        )

    model_rows = await pool.fetch(
        """
        SELECT
            COALESCE(NULLIF(details->>'model', ''), 'unknown') AS model,
            COUNT(*)::bigint AS invocations,
            AVG(
                CASE
                    WHEN lower(COALESCE(details->>'success', '')) IN ('1', 'true', 't', 'yes') THEN 1.0
                    WHEN lower(COALESCE(details->>'success', '')) IN ('0', 'false', 'f', 'no') THEN 0.0
                    ELSE NULL
                END
            ) AS success_rate,
            AVG(
                CASE
                    WHEN details ? 'latency_sec'
                     AND (details->>'latency_sec') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                    THEN (details->>'latency_sec')::double precision
                    ELSE NULL
                END
            ) AS avg_latency_sec,
            AVG(
                CASE
                    WHEN details ? 'cost_usd'
                     AND (details->>'cost_usd') ~ '^-?[0-9]+(\\.[0-9]+)?$'
                    THEN (details->>'cost_usd')::double precision
                    ELSE NULL
                END
            ) AS avg_cost_usd
        FROM audit_log
        WHERE details ? 'model'
        GROUP BY COALESCE(NULLIF(details->>'model', ''), 'unknown')
        ORDER BY invocations DESC
        LIMIT 25
        """
    )
    model_fleet = [
        {
            "model": str(row["model"]),
            "invocations": int(row["invocations"]),
            "success_rate": _safe_float(row["success_rate"]),
            "avg_latency_sec": _safe_float(row["avg_latency_sec"]),
            "avg_cost_usd": _safe_float(row["avg_cost_usd"]),
        }
        for row in model_rows
    ]

    agents: list[dict[str, Any]] = []
    active_sessions = 0
    try:
        redis_client = await get_redis_client()
        sessions = await redis_client.working_memory_list(limit=200)
        active_sessions = len(sessions)
        for session in sessions:
            session_id = str(session["session_id"])
            memory = session["memory"] if isinstance(session["memory"], dict) else {}
            active_plan = memory.get("active_plan") if isinstance(memory.get("active_plan"), list) else []
            tool_results = (
                memory.get("tool_results_buffer")
                if isinstance(memory.get("tool_results_buffer"), list)
                else []
            )
            attention_stack = (
                memory.get("attention_stack")
                if isinstance(memory.get("attention_stack"), list)
                else []
            )
            latencies = [
                _safe_float(item.get("latency_sec"))
                for item in tool_results
                if isinstance(item, dict)
            ]
            valid_latencies = [value for value in latencies if value is not None]
            success_values = [
                _safe_float(item.get("success"))
                for item in tool_results
                if isinstance(item, dict)
            ]
            valid_success = [value for value in success_values if value is not None]
            model = None
            for item in reversed(tool_results):
                if isinstance(item, dict) and item.get("model"):
                    model = str(item["model"])
                    break

            last_updated = _parse_iso_datetime(memory.get("last_updated"))
            agents.append(
                {
                    "id": session_id,
                    "name": session_id,
                    "role": "session",
                    "status": _derive_status(last_updated),
                    "task": str(memory.get("current_goal") or ""),
                    "load": len(active_plan),
                    "max": max(1, len(active_plan)),
                    "success_rate": (
                        sum(_clamp(value, 0.0, 1.0) for value in valid_success) / len(valid_success)
                        if valid_success
                        else None
                    ),
                    "latency_sec": (
                        sum(valid_latencies) / len(valid_latencies) if valid_latencies else None
                    ),
                    "memory_hits": len(attention_stack),
                    "tools_called": len(tool_results),
                    "model": model,
                    "last_updated": last_updated.isoformat() if last_updated else None,
                }
            )
    except Exception as exc:  # pragma: no cover - integration failure path
        source_errors.append(f"redis_unavailable: {exc}")

    episodic_nodes = None
    try:
        episodic_nodes = await _neo4j_node_count()
    except Exception as exc:  # pragma: no cover - integration failure path
        source_errors.append(f"neo4j_unavailable: {exc}")

    alpha = 1 + success_count
    beta = 1 + failure_count
    denom = alpha + beta
    bayesian_mean = (alpha / denom) if denom > 0 else 0.5
    bayesian_variance = (
        (alpha * beta) / (denom * denom * (denom + 1))
        if denom > 1
        else None
    )

    conformal = _compute_conformal_metrics(stream)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_errors": source_errors,
        "metrics": {
            "total_calls": total_calls,
            "success_rate": success_rate,
            "avg_latency_sec": avg_latency_sec,
            "cost_usd": cost_usd,
            "skills_compiled": skills_compiled,
            "memories_consolidated": semantic_memories,
            "active_sessions": active_sessions,
            "episodic_nodes": episodic_nodes,
        },
        "cognitive_loop": cognitive_loop,
        "decision": decision,
        "bayesian": {
            "alpha": alpha,
            "beta": beta,
            "mean": bayesian_mean,
            "variance": bayesian_variance,
        },
        "conformal": conformal,
        "stream": stream[-40:],
        "agents": agents,
        "pending_approvals": pending_approvals,
        "memory_nodes": memory_nodes,
        "memory_stats": {
            "episodic_nodes": episodic_nodes,
            "semantic_facts": semantic_memories,
            "compiled_skills": skills_compiled,
            "active_sessions": active_sessions,
        },
        "model_fleet": model_fleet,
        "semantic_clusters": semantic_clusters,
        "policy": {
            "proceed_threshold": 0.8,
            "monitor_threshold": 0.55,
        },
    }


@router.post("/approvals/{approval_id}/resolve")
async def resolve_pending_approval(
    approval_id: str,
    payload: ApprovalResolutionRequest,
) -> dict[str, Any]:
    """Resolve a pending approval request in the audit log."""
    try:
        pool = await get_postgres_pool()
    except Exception as exc:  # pragma: no cover - integration failure path
        raise HTTPException(status_code=503, detail=f"PostgreSQL unavailable: {exc}") from exc

    updated = await pool.fetchrow(
        """
        UPDATE audit_log
        SET details = COALESCE(details, '{}'::jsonb) || jsonb_build_object(
            'status', 'resolved',
            'approved', $2::boolean,
            'resolved_by', $3::text,
            'resolved_at', now()
        )
        WHERE id = $1::uuid
          AND action = 'tool_approval_requested'
          AND COALESCE(details->>'status', 'pending') = 'pending'
        RETURNING id::text AS id, details
        """,
        approval_id,
        payload.approved,
        payload.actor,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Pending approval not found")

    resolution_details = {
        "approval_id": approval_id,
        "approved": payload.approved,
        "actor": payload.actor,
    }
    await pool.execute(
        """
        INSERT INTO audit_log (action, actor, resource_type, resource_id, details)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        """,
        "tool_approval_resolved",
        payload.actor,
        "approval",
        approval_id,
        json.dumps(resolution_details),
    )

    return {
        "status": "resolved",
        "approval_id": approval_id,
        "approved": payload.approved,
        "resolved_by": payload.actor,
    }
