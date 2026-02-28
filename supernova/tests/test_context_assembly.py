"""Tests for context_assembly.py — positional context window assembly."""

from __future__ import annotations

import re

import pytest

from supernova.core.reasoning.context_assembly import (
    ContextBudget,
    ContextInputs,
    assemble_context_window,
    estimate_context_stats,
    _format_episodic_context,
    _format_plan,
    _format_semantic_memories,
    _format_working_memory,
)


class TestContextBudget:
    def test_budget_overcommit_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match=r"overcommitted"):
            ContextBudget(total_tokens=10, primacy_tokens=5, recency_tokens=5, middle_tokens=1)

    def test_budget_exact_allocation_is_allowed(self) -> None:
        b = ContextBudget(total_tokens=10, primacy_tokens=3, recency_tokens=2, middle_tokens=5)
        assert b.primacy_tokens + b.recency_tokens + b.middle_tokens == b.total_tokens


class TestFormatPlan:
    def test_empty_plan_has_reactive_message(self) -> None:
        assert "No active plan" in _format_plan([])

    def test_markers_and_result_truncation(self) -> None:
        plan = [
            {"description": "do A", "status": "complete", "result": "x" * 500},
            {"description": "do B", "status": "active"},
            {"description": "do C", "status": "pending"},
        ]
        s = _format_plan(plan)
        assert "✓ Step 1" in s
        assert "→ Step 2" in s
        assert "○ Step 3" in s
        # Result line exists and is truncated to 200 chars
        assert "Result:" in s
        m = re.search(r"Result: (.*)", s)
        assert m is not None
        assert len(m.group(1)) <= 200


class TestFormatSemanticMemories:
    def test_empty_memories_returns_empty_string(self) -> None:
        assert _format_semantic_memories([]) == ""

    def test_ranking_by_importance_then_recency(self) -> None:
        memories = [
            {"content": "low importance recent", "importance": 1, "recency_score": 100},
            {"content": "high importance old", "importance": 9, "recency_score": 0},
            {"content": "high importance recent", "importance": 9, "recency_score": 50},
        ]
        s = _format_semantic_memories(memories, max_memories=15)
        # Highest importance + higher recency first
        first_idx = s.find("high importance recent")
        second_idx = s.find("high importance old")
        third_idx = s.find("low importance recent")
        assert 0 <= first_idx < second_idx < third_idx

    def test_confidence_tag_included_below_09(self) -> None:
        memories = [
            {"content": "uncertain fact", "importance": 5, "confidence": 0.89},
            {"content": "certain fact", "importance": 5, "confidence": 0.95},
        ]
        s = _format_semantic_memories(memories)
        assert "uncertain fact" in s
        assert "[confidence: 89%]" in s
        assert "certain fact" in s
        assert "confidence" not in s.split("certain fact")[0]  # no tag on high confidence

    def test_truncates_to_max_memories(self) -> None:
        memories = [{"content": f"m{i}", "importance": 5} for i in range(100)]
        s = _format_semantic_memories(memories, max_memories=2)
        # header + 2 memories lines
        assert s.count("\n") == 2
        assert "m0" in s or "m99" in s

    def test_default_category_fact_used(self) -> None:
        memories = [{"content": "some fact", "importance": 5}]
        s = _format_semantic_memories(memories)
        assert "[fact]" in s


class TestFormatWorkingMemory:
    def test_empty_working_memory_returns_empty_string(self) -> None:
        assert _format_working_memory({}) == ""

    def test_goal_scratchpad_attention_and_tool_results(self) -> None:
        wm = {
            "current_goal": "Fix it",
            "scratchpad": "line1\nline2",
            "attention_stack": ["A", "B"],
            "tool_results_buffer": [
                {"tool": "t1", "result": "r1"},
                {"tool": "t2", "result": "r2"},
                {"tool": "t3", "result": "r3"},
                {"tool": "t4", "result": "r4"},
                {"tool": "t5", "result": "r5"},
                {"tool": "t6", "result": "r6"},
            ],
        }
        s = _format_working_memory(wm)
        assert "Active goal: Fix it" in s
        assert "Scratchpad:" in s
        assert "  line1" in s
        assert "  line2" in s
        assert "Current focus: A → B" in s
        # only last 5 tool results are included (t2..t6)
        assert "t1" not in s
        for t in ["t2", "t3", "t4", "t5", "t6"]:
            assert t in s

    def test_tool_result_truncates_to_300_chars(self) -> None:
        wm = {
            "tool_results_buffer": [{"tool": "big", "result": "x" * 1000}],
        }
        s = _format_working_memory(wm)
        # After "big:" there should be at most 300 chars of x
        m = re.search(r"big: (x+)", s)
        assert m is not None
        assert len(m.group(1)) == 300


class TestFormatEpisodicContext:
    def test_empty_episodes_returns_empty_string(self) -> None:
        assert _format_episodic_context([]) == ""

    def test_ranks_by_score_and_truncates(self) -> None:
        episodes = [
            {"score": 0.1, "valid_from": "2026-02-01T10:00:00Z", "content": "low"},
            {"score": 0.9, "valid_from": "2026-02-02T10:00:00Z", "fact": "high"},
            {"score": 0.5, "valid_from": "2026-02-03T10:00:00Z", "content": "mid"},
        ]
        s = _format_episodic_context(episodes, max_episodes=2)
        assert "[2026-02-02] high" in s
        assert "[2026-02-03] mid" in s
        assert "low" not in s


class TestPrimacyZone:
    def test_primacy_zone_always_included(self):
        """System content always at message index 0."""
        inputs = ContextInputs(
            agent_identity="I am SuperNova",
            active_task="Do something",
            conversation_history=[{"role": "user", "content": "hello"}],
        )
        msgs = assemble_context_window(inputs)
        assert msgs[0]["role"] == "system"
        assert "I am SuperNova" in msgs[0]["content"]


class TestMiddleZone:
    def test_middle_zone_injection(self):
        """Semantic memories appear in middle, not first or last."""
        inputs = ContextInputs(
            agent_identity="Agent",
            semantic_memories=[{"content": "Python was created by Guido", "importance": 8}],
            conversation_history=[{"role": "user", "content": "tell me about Python"}],
        )
        msgs = assemble_context_window(inputs)
        # Middle zone: user injection at index 1, assistant ack at index 2
        assert len(msgs) >= 4
        assert msgs[1]["role"] == "user"
        assert "CONTEXT INJECTION" in msgs[1]["content"]
        assert "Python was created by Guido" in msgs[1]["content"]
        assert msgs[2]["role"] == "assistant"
        # Not first (system) or last (user message)
        assert "Python was created by Guido" not in msgs[0]["content"]

    def test_middle_zone_injection_from_tool_schemas_only(self) -> None:
        inputs = ContextInputs(
            agent_identity="Agent",
            tool_schemas=[{"name": "search"}, {"name": "fetch"}],
            conversation_history=[{"role": "user", "content": "hi"}],
        )
        msgs = assemble_context_window(inputs)
        assert msgs[1]["role"] == "user"
        assert "Available tools: search, fetch" in msgs[1]["content"]
        assert msgs[2]["role"] == "assistant"

    def test_no_middle_zone_messages_when_no_semantic_or_tools(self) -> None:
        inputs = ContextInputs(
            agent_identity="Agent",
            conversation_history=[{"role": "user", "content": "hi"}],
        )
        msgs = assemble_context_window(inputs)
        assert all("CONTEXT INJECTION" not in m["content"] for m in msgs)
        assert all(
            m["content"] != "Understood. I have the above context available as background reference. Proceeding with the active task."
            for m in msgs
        )


class TestRecencyZone:
    def test_recency_zone_prefix(self):
        """Working memory prepended to final user message."""
        inputs = ContextInputs(
            agent_identity="Agent",
            working_memory={"current_goal": "Fix the bug"},
            conversation_history=[{"role": "user", "content": "what next?"}],
        )
        msgs = assemble_context_window(inputs)
        last = msgs[-1]
        assert last["role"] == "user"
        assert "Fix the bug" in last["content"]
        assert "what next?" in last["content"]

    def test_recency_prefix_adds_user_message_delimiter(self) -> None:
        inputs = ContextInputs(
            agent_identity="Agent",
            working_memory={"current_goal": "Do X"},
            conversation_history=[{"role": "user", "content": "original"}],
        )
        msgs = assemble_context_window(inputs)
        assert "━━ USER MESSAGE ━━" in msgs[-1]["content"]
        assert msgs[-1]["content"].endswith("original")

    def test_state_update_appended_when_history_ends_with_assistant(self) -> None:
        inputs = ContextInputs(
            agent_identity="Agent",
            working_memory={"current_goal": "Resume"},
            conversation_history=[{"role": "assistant", "content": "done"}],
        )
        msgs = assemble_context_window(inputs)
        assert msgs[-1]["role"] == "user"
        assert "AGENT STATE UPDATE" in msgs[-1]["content"]
        assert "Resume" in msgs[-1]["content"]

    def test_state_update_appended_when_no_conversation_history(self) -> None:
        inputs = ContextInputs(agent_identity="Agent", working_memory={"current_goal": "G"})
        msgs = assemble_context_window(inputs)
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["role"] == "user"
        assert "AGENT STATE UPDATE" in msgs[-1]["content"]


class TestEdgeCases:
    def test_empty_inputs_produce_valid_messages(self):
        """Empty ContextInputs produces at least [system_msg]."""
        inputs = ContextInputs()
        msgs = assemble_context_window(inputs)
        assert len(msgs) >= 1
        assert msgs[0]["role"] == "system"

    def test_conversation_history_truncation(self):
        """Long history truncated from front, not back."""
        long_history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}" * 500}
            for i in range(100)
        ]
        inputs = ContextInputs(
            agent_identity="Agent",
            conversation_history=long_history,
        )
        budget = ContextBudget(total_tokens=100_000, recency_tokens=2_000)
        msgs = assemble_context_window(inputs, budget=budget)
        # Should include fewer messages than the full 100
        non_system = [m for m in msgs if m["role"] != "system"]
        assert len(non_system) < 100
        # Last message should be the last from history (recency preserved)
        assert msgs[-1]["content"].startswith("msg 99") or "msg 99" in msgs[-1]["content"]

    def test_token_counter_is_used_for_budget(self) -> None:
        calls = {"n": 0}

        def token_counter(text: str) -> int:
            calls["n"] += 1
            # Make each message cost 2 tokens regardless of length.
            return 2

        history = [
            {"role": "user", "content": "old"},
            {"role": "assistant", "content": "mid"},
            {"role": "user", "content": "new"},
        ]
        inputs = ContextInputs(agent_identity="Agent", conversation_history=history)
        budget = ContextBudget(total_tokens=100_000, recency_tokens=4)
        msgs = assemble_context_window(inputs, budget=budget, token_counter=token_counter)
        # history_budget_tokens = recency_tokens//2 = 2, so we can include only one history msg.
        assert any(m.get("content") == "new" for m in msgs)
        assert not any(m.get("content") == "old" for m in msgs)
        assert calls["n"] > 0


class TestContextStats:
    def test_context_stats_empty_messages(self) -> None:
        assert estimate_context_stats([]) == {"total": 0, "primacy": 0, "middle": 0, "recency": 0}

    def test_context_stats_returns_valid_percentages(self):
        """estimate_context_stats output is internally consistent."""
        inputs = ContextInputs(
            agent_identity="Agent",
            semantic_memories=[{"content": "fact", "importance": 5}],
            conversation_history=[{"role": "user", "content": "hi"}],
        )
        msgs = assemble_context_window(inputs)
        stats = estimate_context_stats(msgs)
        assert stats["total"] > 0
        assert stats["primacy"] >= 0
        assert stats["middle"] >= 0
        assert stats["recency"] >= 0
        assert stats["primacy"] + stats["middle"] + stats["recency"] == stats["total"]
        assert "%" in stats["primacy_pct"]
        assert "%" in stats["recency_pct"]

    def test_context_stats_middle_zone_nonzero_for_longer_messages(self) -> None:
        messages = [
            {"role": "system", "content": "s" * 40},
            {"role": "user", "content": "m1" * 40},
            {"role": "assistant", "content": "m2" * 40},
            {"role": "assistant", "content": "r1" * 40},
            {"role": "assistant", "content": "r2" * 40},
            {"role": "user", "content": "r3" * 40},
        ]
        stats = estimate_context_stats(messages)
        assert stats["middle"] > 0
        assert stats["total"] == stats["primacy"] + stats["middle"] + stats["recency"]
