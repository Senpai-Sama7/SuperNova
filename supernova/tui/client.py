"""SuperNova API Client for TUI."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote, urlparse

import httpx
import websockets


class SuperNovaClient:
    """Async HTTP + WebSocket client for the SuperNova API."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self.session_id = uuid.uuid4().hex[:16]
        self.token: str | None = None
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    # ── Health ─────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        r = await self._http.get("/health")
        r.raise_for_status()
        return r.json()

    async def deep_health(self) -> dict[str, Any]:
        r = await self._http.get("/health/deep")
        r.raise_for_status()
        return r.json()

    # ── Agent ──────────────────────────────────────────────────

    async def send_message(self, message: str) -> dict[str, Any]:
        r = await self._http.post(
            "/api/v1/agent/message",
            json={"session_id": self.session_id, "message": message, "actor": "user"},
        )
        r.raise_for_status()
        return r.json()

    # ── Dashboard ──────────────────────────────────────────────

    async def get_snapshot(self) -> dict[str, Any]:
        r = await self._http.get("/api/v1/dashboard/snapshot")
        r.raise_for_status()
        return r.json()

    async def resolve_approval(self, approval_id: str, approved: bool) -> dict[str, Any]:
        safe_id = quote(approval_id, safe="")
        r = await self._http.post(
            f"/api/v1/dashboard/approvals/{safe_id}/resolve",
            json={"approved": approved},
        )
        r.raise_for_status()
        return r.json()

    # ── Memory ─────────────────────────────────────────────────

    async def get_semantic_memories(self) -> Any:
        r = await self._http.get("/memory/semantic")
        r.raise_for_status()
        return r.json()

    async def get_procedural_skills(self) -> Any:
        r = await self._http.get("/memory/procedural")
        r.raise_for_status()
        return r.json()

    async def export_memories(self) -> Any:
        r = await self._http.get("/memory/export")
        r.raise_for_status()
        return r.json()

    # ── Admin ──────────────────────────────────────────────────

    async def get_costs(self) -> Any:
        r = await self._http.get("/admin/costs")
        r.raise_for_status()
        return r.json()

    async def get_audit_logs(self) -> Any:
        r = await self._http.get("/admin/audit-logs")
        r.raise_for_status()
        return r.json()

    async def get_fleet(self) -> Any:
        r = await self._http.get("/admin/fleet")
        r.raise_for_status()
        return r.json()

    # ── Streaming ──────────────────────────────────────────────

    async def stream(self, message: str) -> AsyncIterator[dict[str, Any]]:
        """Stream agent events via WebSocket with HTTP fallback."""
        parsed = urlparse(self.base_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = f"{ws_scheme}://{parsed.netloc}/agent/stream/{self.session_id}"
        if self.token:
            ws_url += f"?token={self.token}"

        try:
            async with websockets.connect(ws_url, open_timeout=5, close_timeout=5) as ws:
                await ws.send(json.dumps({"message": message}))
                async for raw in ws:
                    event = json.loads(raw)
                    yield event
                    if event.get("type") in ("done", "error"):
                        break
        except (OSError, asyncio.TimeoutError, websockets.exceptions.WebSocketException):
            yield {"type": "error", "message": "WebSocket unavailable — using HTTP fallback"}
            try:
                result = await self.send_message(message)
                yield {"type": "message", "content": result.get("detail", str(result))}
            except Exception as e:
                yield {"type": "error", "message": f"HTTP fallback failed: {e}"}
            yield {"type": "done"}

    # ── Cleanup ────────────────────────────────────────────────

    async def close(self) -> None:
        await self._http.aclose()
