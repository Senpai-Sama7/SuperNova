"""Agent interaction routes backed by working memory and audit log."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from supernova.core.memory import WorkingMemory, get_working_memory_store
from supernova.infrastructure.storage import get_postgres_pool

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


class AgentMessageRequest(BaseModel):
    """Inbound user message payload."""

    session_id: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=10_000)
    actor: str = Field(default="user", min_length=1, max_length=255)


@router.post("/message")
async def post_agent_message(payload: AgentMessageRequest) -> dict[str, Any]:
    """Persist an inbound message to working memory and audit log."""
    try:
        store = await get_working_memory_store()
        memory = await store.get(payload.session_id)
        if memory is None:
            memory = WorkingMemory(session_id=payload.session_id)

        timestamp = datetime.now(UTC).isoformat()
        message_line = f"[{timestamp}] {payload.actor}: {payload.message}"
        if memory.scratchpad:
            memory.scratchpad = f"{memory.scratchpad}\n{message_line}"
        else:
            memory.scratchpad = message_line
        memory.current_goal = payload.message

        await store.set(memory)
    except Exception as exc:  # pragma: no cover - integration failure path
        raise HTTPException(status_code=503, detail=f"Working memory unavailable: {exc}") from exc

    try:
        pool = await get_postgres_pool()
        await pool.execute(
            """
            INSERT INTO audit_log (action, actor, resource_type, resource_id, details)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            """,
            "user_message_received",
            payload.actor,
            "session",
            payload.session_id,
            json.dumps(
                {
                    "message": payload.message,
                    "session_id": payload.session_id,
                    "received_at": timestamp,
                }
            ),
        )
    except Exception as exc:  # pragma: no cover - integration failure path
        raise HTTPException(status_code=503, detail=f"PostgreSQL unavailable: {exc}") from exc

    return {
        "status": "accepted",
        "session_id": payload.session_id,
        "received_at": timestamp,
    }
