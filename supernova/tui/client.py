"""SuperNova API Client for TUI."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import websockets


class SuperNovaClient:
    """HTTP client for the SuperNova API."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.session_id = uuid.uuid4().hex[:16]
        self.token: str | None = None
        self._http = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def health(self) -> dict[str, Any]:
        r = await self._http.get("/health")
        r.raise_for_status()
        return r.json()

    async def deep_health(self) -> dict[str, Any]:
        r = await self._http.get("/health/deep")
        r.raise_for_status()
        return r.json()

    async def send_message(self, message: str) -> dict[str, Any]:
        r = await self._http.post(
            "/api/v1/agent/message",
            json={"session_id": self.session_id, "message": message, "actor": "user"},
        )
        r.raise_for_status()
        return r.json()

    async def get_snapshot(self) -> dict[str, Any]:
        r = await self._http.get("/api/v1/dashboard/snapshot")
        r.raise_for_status()
        return r.json()

    async def resolve_approval(self, approval_id: str, approved: bool) -> dict[str, Any]:
        r = await self._http.post(
            f"/api/v1/dashboard/approvals/{approval_id}/resolve",
            json={"approved": approved},
        )
        r.raise_for_status()
        return r.json()

    async def get_semantic_memories(self) -> dict[str, Any]:
        r = await self._http.get("/memory/semantic")
        r.raise_for_status()
        return r.json()

    async def get_procedural_skills(self) -> dict[str, Any]:
        r = await self._http.get("/memory/procedural")
        r.raise_for_status()
        return r.json()

    async def get_costs(self) -> dict[str, Any]:
        r = await self._http.get("/admin/costs")
        r.raise_for_status()
        return r.json()

    async def get_audit_logs(self) -> dict[str, Any]:
        r = await self._http.get("/admin/audit-logs")
        r.raise_for_status()
        return r.json()

    async def get_fleet(self) -> dict[str, Any]:
        r = await self._http.get("/admin/fleet")
        r.raise_for_status()
        return r.json()

    async def stream(self, message: str) -> AsyncIterator[dict[str, Any]]:
        """Connect to WebSocket and stream agent events."""
        ws_url = self.base_url.replace("http", "ws")
        url = f"{ws_url}/agent/stream/{self.session_id}?token={self.token or 'dev'}"
        try:
            async with websockets.connect(url, open_timeout=5) as ws:
                await ws.send(json.dumps({"message": message}))
                async for raw in ws:
                    event = json.loads(raw)
                    yield event
                    if event.get("type") in ("done", "error"):
                        break
        except (OSError, asyncio.TimeoutError, websockets.exceptions.WebSocketException):
            # Fallback: yield a single error event
            yield {"type": "error", "message": "WebSocket connection failed — using HTTP fallback"}
            try:
                result = await self.send_message(message)
                yield {"type": "message", "content": result.get("detail", str(result))}
            except Exception as e:
                yield {"type": "error", "message": f"HTTP fallback also failed: {e}"}
            yield {"type": "done"}

    async def close(self) -> None:
        await self._http.aclose()
