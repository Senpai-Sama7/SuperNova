"""Tests for WebSocket Handler (Task 6.2)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from supernova.api.websockets import WebSocketBroadcaster, handle_agent_stream, map_event


class TestWebSocketBroadcaster:
    def test_register_unregister(self):
        b = WebSocketBroadcaster()
        ws = MagicMock()
        b.register("t1", ws)
        assert b.active_connections == 1
        b.unregister("t1")
        assert b.active_connections == 0

    def test_unregister_nonexistent(self):
        b = WebSocketBroadcaster()
        b.unregister("missing")  # Should not raise

    @pytest.mark.asyncio
    async def test_send_to_registered(self):
        b = WebSocketBroadcaster()
        ws = AsyncMock()
        b.register("t1", ws)
        await b.send("t1", {"type": "token", "content": "hi"})
        ws.send_json.assert_called_once_with({"type": "token", "content": "hi"})

    @pytest.mark.asyncio
    async def test_send_to_unregistered(self):
        b = WebSocketBroadcaster()
        await b.send("missing", {"type": "test"})  # Should not raise

    @pytest.mark.asyncio
    async def test_send_failure_unregisters(self):
        b = WebSocketBroadcaster()
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("broken")
        b.register("t1", ws)
        await b.send("t1", {"type": "test"})
        assert b.active_connections == 0


class TestMapEvent:
    def test_token_event(self):
        event = {"event": "on_chat_model_stream", "data": {"chunk": "hello"}}
        result = map_event(event)
        assert result == {"type": "token", "content": "hello"}

    def test_token_event_empty_content(self):
        event = {"event": "on_chat_model_stream", "data": {"chunk": ""}}
        assert map_event(event) is None

    def test_tool_start_event(self):
        event = {"event": "on_tool_start", "name": "web_search", "data": {"input": {"q": "test"}}}
        result = map_event(event)
        assert result["type"] == "tool_start"
        assert result["tool"] == "web_search"

    def test_tool_end_event(self):
        event = {"event": "on_tool_end", "name": "web_search", "data": {"output": "results"}}
        result = map_event(event)
        assert result["type"] == "tool_result"
        assert result["output"] == "results"

    def test_chain_end_event(self):
        event = {"event": "on_chain_end", "data": {"output": {"final": True}}}
        result = map_event(event)
        assert result["type"] == "done"

    def test_interrupt_event(self):
        event = {"event": "on_chain_end", "data": {"output": {"__interrupt__": {"tool": "send_email"}}}}
        result = map_event(event)
        assert result["type"] == "approval_request"

    def test_unknown_event(self):
        event = {"event": "on_something_else", "data": {}}
        assert map_event(event) is None


class TestHandleAgentStream:
    @pytest.mark.asyncio
    async def test_streams_events(self):
        broadcaster = WebSocketBroadcaster()
        ws = AsyncMock()
        broadcaster.register("t1", ws)

        mock_graph = AsyncMock()
        events = [
            {"event": "on_chat_model_stream", "data": {"chunk": "hi"}},
            {"event": "on_chain_end", "data": {"output": {}}},
        ]
        mock_graph.astream_events = MagicMock(return_value=_async_iter(events))

        await handle_agent_stream(ws, "t1", broadcaster, mock_graph, {"messages": [{"role": "user", "content": "hello"}]})

        # Should have sent token + done + final done
        calls = ws.send_json.call_args_list
        assert any(c.args[0].get("type") == "token" for c in calls)

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self):
        broadcaster = WebSocketBroadcaster()
        ws = AsyncMock()

        mock_graph = AsyncMock()
        mock_graph.astream_events = MagicMock(return_value=_async_iter([]))

        await handle_agent_stream(ws, "t1", broadcaster, mock_graph, {})
        # After completion, connection should be unregistered
        assert broadcaster.active_connections == 0


async def _async_iter(items):
    """Helper to create an async iterator from a list."""
    for item in items:
        yield item
