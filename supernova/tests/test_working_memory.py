"""Tests for core/memory/working.py — WorkingMemory + WorkingMemoryStore."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.memory.working import WorkingMemory, WorkingMemoryStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def redis():
    r = MagicMock()
    r.working_memory_get = AsyncMock(return_value=None)
    r.working_memory_set = AsyncMock()
    r.working_memory_delete = AsyncMock()
    r.working_memory_exists = AsyncMock(return_value=False)
    return r


@pytest.fixture
def store(redis):
    return WorkingMemoryStore(redis_client=redis)


# ---------------------------------------------------------------------------
# WorkingMemory dataclass
# ---------------------------------------------------------------------------

class TestWorkingMemory:
    def test_to_dict_and_from_dict_roundtrip(self):
        mem = WorkingMemory(session_id="s1", current_goal="test", active_plan=["a"])
        d = mem.to_dict()
        restored = WorkingMemory.from_dict(d)
        assert restored.session_id == "s1"
        assert restored.current_goal == "test"
        assert restored.active_plan == ["a"]

    def test_from_dict_bad_timestamp(self):
        mem = WorkingMemory.from_dict({"session_id": "s1", "last_updated": "not-a-date"})
        assert mem.session_id == "s1"
        # Should fall back to now() without raising
        assert mem.last_updated is not None

    def test_from_dict_missing_fields(self):
        mem = WorkingMemory.from_dict({})
        assert mem.session_id == ""
        assert mem.active_plan == []


# ---------------------------------------------------------------------------
# WorkingMemoryStore
# ---------------------------------------------------------------------------

class TestWorkingMemoryStore:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self, store, redis):
        result = await store.get("nonexistent")
        assert result is None
        redis.working_memory_get.assert_awaited_once_with("nonexistent")

    @pytest.mark.asyncio
    async def test_get_returns_memory(self, store, redis):
        redis.working_memory_get.return_value = {"session_id": "s1", "current_goal": "g"}
        result = await store.get("s1")
        assert result is not None
        assert result.current_goal == "g"

    @pytest.mark.asyncio
    async def test_get_handles_exception(self, store, redis):
        redis.working_memory_get.side_effect = RuntimeError("boom")
        result = await store.get("s1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_stores_memory(self, store, redis):
        mem = WorkingMemory(session_id="s1", current_goal="goal")
        await store.set(mem, ttl=300)
        redis.working_memory_set.assert_awaited_once()
        call_args = redis.working_memory_set.call_args
        assert call_args[0][0] == "s1"
        assert call_args[1]["ttl"] == 300

    @pytest.mark.asyncio
    async def test_set_raises_on_error(self, store, redis):
        redis.working_memory_set.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            await store.set(WorkingMemory(session_id="s1"))

    @pytest.mark.asyncio
    async def test_delete(self, store, redis):
        await store.delete("s1")
        redis.working_memory_delete.assert_awaited_once_with("s1")

    @pytest.mark.asyncio
    async def test_delete_raises_on_error(self, store, redis):
        redis.working_memory_delete.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            await store.delete("s1")

    @pytest.mark.asyncio
    async def test_exists_true(self, store, redis):
        redis.working_memory_exists.return_value = True
        assert await store.exists("s1") is True

    @pytest.mark.asyncio
    async def test_exists_false_on_error(self, store, redis):
        redis.working_memory_exists.side_effect = RuntimeError("boom")
        assert await store.exists("s1") is False

    @pytest.mark.asyncio
    async def test_update_field(self, store, redis):
        redis.working_memory_get.return_value = {"session_id": "s1", "current_goal": "old"}
        await store.update_field("s1", "current_goal", "new")
        redis.working_memory_set.assert_awaited_once()
        stored = redis.working_memory_set.call_args[0][1]
        assert stored["current_goal"] == "new"

    @pytest.mark.asyncio
    async def test_update_field_creates_new_if_missing(self, store, redis):
        redis.working_memory_get.return_value = None
        await store.update_field("s1", "current_goal", "fresh")
        redis.working_memory_set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_field_invalid_raises(self, store, redis):
        redis.working_memory_get.return_value = {"session_id": "s1"}
        with pytest.raises(ValueError, match="Invalid field"):
            await store.update_field("s1", "nonexistent_field", "val")

    @pytest.mark.asyncio
    async def test_append_to_field(self, store, redis):
        redis.working_memory_get.return_value = {"session_id": "s1", "active_plan": ["a"]}
        await store.append_to_field("s1", "active_plan", "b")
        stored = redis.working_memory_set.call_args[0][1]
        assert "b" in stored["active_plan"]

    @pytest.mark.asyncio
    async def test_append_to_field_creates_new_if_missing(self, store, redis):
        redis.working_memory_get.return_value = None
        await store.append_to_field("s1", "active_plan", "first")
        stored = redis.working_memory_set.call_args[0][1]
        assert "first" in stored["active_plan"]

    @pytest.mark.asyncio
    async def test_append_to_non_list_raises(self, store, redis):
        redis.working_memory_get.return_value = {"session_id": "s1", "current_goal": "g"}
        with pytest.raises(ValueError, match="not a list"):
            await store.append_to_field("s1", "current_goal", "val")
