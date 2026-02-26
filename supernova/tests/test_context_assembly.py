"""Tests for context_assembly.py — positional context window assembly."""

from __future__ import annotations

import sys
from pathlib import Path

# context_assembly.py lives at project root
_root = str(Path(__file__).resolve().parents[2])
if _root not in sys.path:
    sys.path.insert(0, _root)

from context_assembly import (
    ContextBudget,
    ContextInputs,
    assemble_context_window,
    estimate_context_stats,
)


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


class TestContextStats:
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
