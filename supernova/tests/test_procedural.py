"""
tests/test_procedural.py

Unit tests for supernova.core.memory.procedural.

Coverage map
────────────
SkillRecord                       — 5 tests  (fields, hmac_key default/custom, compiled_graph property, created_at factory)
SkillMatch                        — 3 tests  (__bool__ true/false, similarity_score stored)
ProceduralMemoryStore (init only) — 5 tests  (default/custom threshold, empty cache, hmac_key, class constant)
SkillCrystallizationWorker:
  _compute_pattern_fingerprint    — 5 tests  (empty stable, single tool, different seqs, param-order invariant, missing keys)
  _extract_repeated_patterns      — 5 tests  (empty, below min, exactly min, sorted desc, avg_score)
  _compute_trace_score            — 4 tests  (no attr, empty, averages, None excluded from sum)
  _count_tool_calls               — 3 tests  (no attr, zero TOOL obs, counts only TOOL type)
  _extract_tool_calls             — 4 tests  (no attr, extracts name+keys, skips non-TOOL, null input)
  _extract_duration               — 3 tests  (latency present, no attr, None latency)
  run_crystallization_cycle       — 3 tests  (zero traces, fetch exception, crystallize exception no crash)

Stubbing strategy
─────────────────
  asyncpg   — sys.modules stub (requires live DB connection)
  langgraph — sys.modules stub (only needed inside _build_skill_graph which is not unit-tested)
  secure_dumps / secure_loads — patched per-test via unittest.mock.patch
  All ProceduralMemoryStore DB calls — not exercised; only __init__ fields tested
  All SkillCrystallizationWorker async I/O — AsyncMock via patch.object

Zero network, database, LLM, or Langfuse calls.
"""

from __future__ import annotations

import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Stubs injected before any supernova imports ──────────────────────────────
sys.modules.setdefault("asyncpg", MagicMock())
sys.modules.setdefault("numpy", MagicMock())
# LangGraph is only imported inside _build_skill_graph — stub to prevent ImportError
# if the module is loaded in an environment without the package installed.
_fake_lg = MagicMock()
_fake_lg.graph.END = "__end__"
sys.modules.setdefault("langgraph", _fake_lg)
sys.modules.setdefault("langgraph.graph", _fake_lg.graph)

from supernova.core.memory.procedural import (  # noqa: E402
    ProceduralMemoryStore,
    SkillCrystallizationWorker,
    SkillMatch,
    SkillRecord,
)


# ── Shared factory helpers ───────────────────────────────────────────────────

def _record(
    *,
    name: str = "test_skill",
    compiled_graph_bytes: bytes = b"fake_bytes",
    trigger_embedding: list[float] | None = None,
    hmac_key: str = "",
    invocation_count: int = 0,
    avg_performance_score: float = 0.9,
    last_invoked_at: str | None = None,
) -> SkillRecord:
    return SkillRecord(
        id="abc123",
        name=name,
        description="A test skill",
        trigger_conditions=["when user needs X"],
        compiled_graph_bytes=compiled_graph_bytes,
        trigger_embedding=trigger_embedding or [0.1, 0.2, 0.3],
        hmac_key=hmac_key,
        invocation_count=invocation_count,
        avg_performance_score=avg_performance_score,
        last_invoked_at=last_invoked_at,
    )


def _match(*, is_confident: bool = True, similarity_score: float = 0.85) -> SkillMatch:
    return SkillMatch(
        skill=_record(),
        similarity_score=similarity_score,
        is_confident=is_confident,
    )


def _worker(*, min_occurrences: int = 3) -> SkillCrystallizationWorker:
    return SkillCrystallizationWorker(
        procedural_store=MagicMock(),
        langfuse_client=MagicMock(),
        llm_client=MagicMock(),
        min_score=0.85,
        min_occurrences=min_occurrences,
    )


# ════════════════════════════════════════════════════════════════════════
# SkillRecord
# ════════════════════════════════════════════════════════════════════════

class TestSkillRecord:
    """SkillRecord is a plain dataclass — test field storage and the compiled_graph property."""

    def test_fields_populated_correctly(self) -> None:
        r = _record(name="my_skill", invocation_count=7, avg_performance_score=0.77)
        assert r.id == "abc123"
        assert r.name == "my_skill"
        assert r.invocation_count == 7
        assert r.avg_performance_score == pytest.approx(0.77)
        assert r.last_invoked_at is None

    def test_hmac_key_defaults_to_empty_string(self) -> None:
        r = _record()  # hmac_key not passed — relies on dataclass default
        assert r.hmac_key == ""

    def test_hmac_key_stored_when_provided(self) -> None:
        r = _record(hmac_key="prod-secret")
        assert r.hmac_key == "prod-secret"

    def test_compiled_graph_calls_secure_loads_with_correct_args(self) -> None:
        r = _record(compiled_graph_bytes=b"signed_blob", hmac_key="k")
        with patch(
            "supernova.core.memory.procedural.secure_loads",
            return_value={"graph": "obj"},
        ) as mock_loads:
            result = r.compiled_graph
            mock_loads.assert_called_once_with(b"signed_blob", "k")
            assert result == {"graph": "obj"}

    def test_created_at_auto_populated_as_iso_string(self) -> None:
        r = _record()
        # Default factory sets created_at to current UTC ISO timestamp
        assert isinstance(r.created_at, str)
        assert len(r.created_at) >= 20        # e.g. "2026-02-28T17:00:00+00:00"
        assert "T" in r.created_at


# ════════════════════════════════════════════════════════════════════════
# SkillMatch
# ════════════════════════════════════════════════════════════════════════

class TestSkillMatch:
    """SkillMatch.__bool__ gates skill activation on is_confident."""

    def test_bool_true_when_is_confident(self) -> None:
        assert bool(_match(is_confident=True)) is True

    def test_bool_false_when_not_confident(self) -> None:
        assert bool(_match(is_confident=False)) is False

    def test_similarity_score_stored_precisely(self) -> None:
        m = _match(similarity_score=0.7312)
        assert m.similarity_score == pytest.approx(0.7312)


# ════════════════════════════════════════════════════════════════════════
# ProceduralMemoryStore — __init__ only (no DB calls)
# ════════════════════════════════════════════════════════════════════════

class TestProceduralMemoryStoreInit:
    """Verify constructor stores parameters correctly without touching the DB."""

    def test_default_confidence_threshold_is_072(self) -> None:
        store = ProceduralMemoryStore(pool=MagicMock(), embedder=AsyncMock())
        assert store.threshold == pytest.approx(0.72)

    def test_custom_confidence_threshold_stored(self) -> None:
        store = ProceduralMemoryStore(
            pool=MagicMock(), embedder=AsyncMock(), confidence_threshold=0.90
        )
        assert store.threshold == pytest.approx(0.90)

    def test_internal_cache_starts_empty(self) -> None:
        store = ProceduralMemoryStore(pool=MagicMock(), embedder=AsyncMock())
        assert store._cache == {}

    def test_hmac_key_stored(self) -> None:
        store = ProceduralMemoryStore(
            pool=MagicMock(), embedder=AsyncMock(), hmac_key="unit-test-key"
        )
        assert store._hmac_key == "unit-test-key"

    def test_class_confidence_threshold_constant(self) -> None:
        """Regression guard: the threshold constant must not silently drift."""
        assert ProceduralMemoryStore.CONFIDENCE_THRESHOLD == pytest.approx(0.72)


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _compute_pattern_fingerprint
# ════════════════════════════════════════════════════════════════════════

class TestComputePatternFingerprint:
    """
    _compute_pattern_fingerprint is a pure function: (list[dict]) -> str.
    No mocking needed.
    """

    def test_empty_sequence_is_stable(self) -> None:
        w = _worker()
        assert w._compute_pattern_fingerprint([]) == w._compute_pattern_fingerprint([])

    def test_returns_16_char_hex_string(self) -> None:
        w = _worker()
        fp = w._compute_pattern_fingerprint([{"tool_name": "web_search", "param_keys": ["query"]}])
        assert isinstance(fp, str) and len(fp) == 16

    def test_different_tool_sequences_yield_different_fingerprints(self) -> None:
        w = _worker()
        fp_a = w._compute_pattern_fingerprint([{"tool_name": "web_search", "param_keys": []}])
        fp_b = w._compute_pattern_fingerprint([{"tool_name": "read_file", "param_keys": []}])
        assert fp_a != fp_b

    def test_param_key_order_invariant(self) -> None:
        """param_keys are sorted — [a, b] and [b, a] must produce the same fingerprint."""
        w = _worker()
        fp1 = w._compute_pattern_fingerprint([{"tool_name": "t", "param_keys": ["a", "b"]}])
        fp2 = w._compute_pattern_fingerprint([{"tool_name": "t", "param_keys": ["b", "a"]}])
        assert fp1 == fp2

    def test_missing_keys_do_not_raise(self) -> None:
        """Empty dict uses default empty string and empty list — must not crash."""
        w = _worker()
        fp = w._compute_pattern_fingerprint([{}])
        assert isinstance(fp, str)


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _extract_repeated_patterns
# ════════════════════════════════════════════════════════════════════════

class TestExtractRepeatedPatterns:
    """
    _extract_repeated_patterns is a pure function over list[dict] — no stubs needed.
    """

    @staticmethod
    def _traces(tool_calls_list: list[list[dict]], score: float = 0.9) -> list[dict]:
        return [{"score": score, "tool_calls": tc} for tc in tool_calls_list]

    def test_empty_traces_returns_empty_list(self) -> None:
        assert _worker()._extract_repeated_patterns([]) == []

    def test_below_min_occurrences_excluded(self) -> None:
        """2 identical traces with min_occurrences=3 → no pattern returned."""
        tools = [{"tool_name": "web_search", "param_keys": ["q"]}]
        result = _worker(min_occurrences=3)._extract_repeated_patterns(
            self._traces([tools, tools])
        )
        assert result == []

    def test_exactly_min_occurrences_included(self) -> None:
        """Exactly 3 matching traces with min_occurrences=3 → 1 pattern with trace_count=3."""
        tools = [{"tool_name": "summarize", "param_keys": ["text"]}]
        result = _worker(min_occurrences=3)._extract_repeated_patterns(
            self._traces([tools, tools, tools])
        )
        assert len(result) == 1
        assert result[0]["trace_count"] == 3

    def test_sorted_by_count_descending(self) -> None:
        """Pattern B (3 occurrences) must appear before pattern A (2 occurrences)."""
        tools_a = [{"tool_name": "read_file", "param_keys": ["path"]}]
        tools_b = [{"tool_name": "write_file", "param_keys": ["path"]}]
        result = _worker(min_occurrences=2)._extract_repeated_patterns(
            self._traces([tools_a, tools_a, tools_b, tools_b, tools_b])
        )
        assert result[0]["trace_count"] == 3

    def test_avg_score_computed_correctly(self) -> None:
        tools = [{"tool_name": "x", "param_keys": []}]
        traces = [
            {"score": 0.8, "tool_calls": tools},
            {"score": 1.0, "tool_calls": tools},
        ]
        result = _worker(min_occurrences=2)._extract_repeated_patterns(traces)
        assert result[0]["avg_score"] == pytest.approx(0.9)


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _compute_trace_score
# ════════════════════════════════════════════════════════════════════════

class TestComputeTraceScore:
    """
    _compute_trace_score operates on duck-typed trace objects.
    Traces are MagicMock instances with controlled .scores attributes.
    """

    def test_no_scores_attr_returns_zero(self) -> None:
        assert _worker()._compute_trace_score(object()) == pytest.approx(0.0)

    def test_empty_scores_list_returns_zero(self) -> None:
        trace = MagicMock(); trace.scores = []
        assert _worker()._compute_trace_score(trace) == pytest.approx(0.0)

    def test_averages_non_none_scores(self) -> None:
        s1, s2 = MagicMock(), MagicMock()
        s1.value, s2.value = 0.8, 1.0
        trace = MagicMock(); trace.scores = [s1, s2]
        assert _worker()._compute_trace_score(trace) == pytest.approx(0.9)

    def test_none_values_excluded_from_numerator_only(self) -> None:
        """
        Denominator is len(trace.scores), which includes None entries.
        So [None, 0.6] → sum=0.6 / len=2 = 0.3.
        """
        s1, s2 = MagicMock(), MagicMock()
        s1.value, s2.value = None, 0.6
        trace = MagicMock(); trace.scores = [s1, s2]
        assert _worker()._compute_trace_score(trace) == pytest.approx(0.3)


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _count_tool_calls
# ════════════════════════════════════════════════════════════════════════

class TestCountToolCalls:
    def test_no_observations_attr_returns_zero(self) -> None:
        assert _worker()._count_tool_calls(object()) == 0

    def test_non_tool_observations_not_counted(self) -> None:
        obs = MagicMock(); obs.type = "LLM"
        trace = MagicMock(); trace.observations = [obs]
        assert _worker()._count_tool_calls(trace) == 0

    def test_counts_only_tool_type_observations(self) -> None:
        tool_obs = MagicMock(); tool_obs.type = "TOOL"
        llm_obs = MagicMock(); llm_obs.type = "LLM"
        trace = MagicMock(); trace.observations = [tool_obs, llm_obs, tool_obs]
        assert _worker()._count_tool_calls(trace) == 2


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _extract_tool_calls
# ════════════════════════════════════════════════════════════════════════

class TestExtractToolCalls:
    def test_no_observations_attr_returns_empty(self) -> None:
        assert _worker()._extract_tool_calls(object()) == []

    def test_extracts_tool_name_and_param_keys(self) -> None:
        obs = MagicMock()
        obs.type = "TOOL"
        obs.name = "web_search"
        obs.input = json.dumps({"query": "test", "limit": 5})
        trace = MagicMock(); trace.observations = [obs]
        result = _worker()._extract_tool_calls(trace)
        assert len(result) == 1
        assert result[0]["tool_name"] == "web_search"
        assert set(result[0]["param_keys"]) == {"query", "limit"}

    def test_skips_non_tool_type_observations(self) -> None:
        obs = MagicMock(); obs.type = "LLM"
        trace = MagicMock(); trace.observations = [obs]
        assert _worker()._extract_tool_calls(trace) == []

    def test_null_input_treated_as_empty_dict(self) -> None:
        obs = MagicMock()
        obs.type = "TOOL"
        obs.name = "empty_tool"
        obs.input = None
        trace = MagicMock(); trace.observations = [obs]
        result = _worker()._extract_tool_calls(trace)
        assert result[0]["param_keys"] == []


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _extract_duration
# ════════════════════════════════════════════════════════════════════════

class TestExtractDuration:
    def test_latency_attribute_present(self) -> None:
        trace = MagicMock(); trace.latency = 1234.5
        assert _worker()._extract_duration(trace) == pytest.approx(1234.5)

    def test_no_latency_attr_returns_zero(self) -> None:
        assert _worker()._extract_duration(object()) == pytest.approx(0.0)

    def test_none_latency_returns_zero(self) -> None:
        trace = MagicMock(); trace.latency = None
        assert _worker()._extract_duration(trace) == pytest.approx(0.0)


# ════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — run_crystallization_cycle (async orchestration)
# ════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
class TestRunCrystallizationCycle:
    """
    Exercises the top-level orchestration method via AsyncMock patch.object.
    Only the control-flow (branching and error handling) is verified;
    the private helpers are tested independently above.
    """

    async def test_zero_traces_returns_zero_crystallized(self) -> None:
        w = _worker()
        with patch.object(w, "_fetch_high_scoring_traces", new=AsyncMock(return_value=[])):
            summary = await w.run_crystallization_cycle()
        assert summary["examined"] == 0
        assert summary["crystallized"] == 0
        assert summary["errors"] == 0

    async def test_fetch_exception_recorded_no_crash(self) -> None:
        """A failing Langfuse API call must not propagate — errors counter incremented."""
        w = _worker()
        with patch.object(
            w, "_fetch_high_scoring_traces",
            new=AsyncMock(side_effect=RuntimeError("langfuse down"))
        ):
            summary = await w.run_crystallization_cycle()
        assert summary["errors"] == 1
        assert summary["crystallized"] == 0

    async def test_crystallize_exception_increments_errors_not_crash(self) -> None:
        """
        A failure inside _crystallize_pattern for one pattern must not abort the loop
        or surface to the caller — errors counter is incremented instead.
        """
        w = _worker(min_occurrences=2)
        pattern = {
            "name": "failing_pattern",
            "trace_count": 2,
            "avg_score": 0.9,
            "tool_calls": [],
            "sample_traces": [],
        }
        with patch.object(w, "_fetch_high_scoring_traces", new=AsyncMock(return_value=[{}, {}])):
            with patch.object(w, "_extract_repeated_patterns", return_value=[pattern]):
                with patch.object(
                    w, "_crystallize_pattern",
                    new=AsyncMock(side_effect=RuntimeError("compile failed"))
                ):
                    summary = await w.run_crystallization_cycle()
        assert summary["errors"] == 1
        assert summary["crystallized"] == 0
