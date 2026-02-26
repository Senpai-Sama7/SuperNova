"""WebSocket handler for streaming agent events to clients."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# LangGraph event type → client event type mapping
EVENT_MAP: dict[str, str] = {
    "on_chat_model_stream": "token",
    "on_tool_start": "tool_start",
    "on_tool_end": "tool_result",
    "on_chain_end": "done",
}


class WebSocketBroadcaster:
    """Manages WebSocket connections keyed by thread_id."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    def register(self, thread_id: str, ws: WebSocket) -> None:
        """Register a WebSocket connection for a thread."""
        self._connections[thread_id] = ws

    def unregister(self, thread_id: str) -> None:
        """Remove a WebSocket connection."""
        self._connections.pop(thread_id, None)

    async def send(self, thread_id: str, data: dict[str, Any]) -> None:
        """Send JSON data to the WebSocket for a thread."""
        ws = self._connections.get(thread_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning("Failed to send to %s: %s", thread_id, e)
                self.unregister(thread_id)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


def map_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Map a LangGraph stream event to a client-facing event."""
    event_type = event.get("event", "")

    # GraphInterrupt → approval_request
    if event_type == "on_chain_end":
        output = event.get("data", {}).get("output", {})
        if isinstance(output, dict) and output.get("__interrupt__"):
            return {"type": "approval_request", "data": output["__interrupt__"]}

    mapped_type = EVENT_MAP.get(event_type)
    if not mapped_type:
        return None

    result: dict[str, Any] = {"type": mapped_type}

    if mapped_type == "token":
        chunk = event.get("data", {}).get("chunk", "")
        content = getattr(chunk, "content", chunk) if not isinstance(chunk, str) else chunk
        if content:
            result["content"] = content
        else:
            return None
    elif mapped_type == "tool_start":
        result["tool"] = event.get("name", "")
        result["input"] = event.get("data", {}).get("input", {})
    elif mapped_type == "tool_result":
        result["tool"] = event.get("name", "")
        result["output"] = event.get("data", {}).get("output", "")
    elif mapped_type == "done":
        result["data"] = event.get("data", {})

    return result


async def handle_agent_stream(
    ws: WebSocket,
    thread_id: str,
    broadcaster: WebSocketBroadcaster,
    agent_graph: Any,
    user_input: dict[str, Any],
) -> None:
    """Stream agent graph events to a WebSocket client."""
    broadcaster.register(thread_id, ws)
    config = {"configurable": {"thread_id": thread_id}}
    try:
        async for event in agent_graph.astream_events(user_input, config, version="v2"):
            mapped = map_event(event)
            if mapped:
                await broadcaster.send(thread_id, mapped)
        await broadcaster.send(thread_id, {"type": "done"})
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", thread_id)
    except Exception as e:
        logger.error("Stream error for %s: %s", thread_id, e)
        await broadcaster.send(thread_id, {"type": "error", "message": str(e)})
    finally:
        broadcaster.unregister(thread_id)
