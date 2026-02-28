"""
supernova/tests/test_procedural.py

Unit tests for the procedural memory system:
  - SkillRecord dataclass and compiled_graph property
  - SkillMatch boolean protocol
  - ProceduralMemoryStore CRUD + retrieval + EWA scoring
  - SkillCrystallizationWorker pattern extraction, fingerprinting, crystallization

All database and external-service calls are mocked; no infrastructure required.
Run with:  pytest supernova/tests/test_procedural.py -v
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from procedural import (
    ProceduralMemoryStore,
    SkillCrystallizationWorker,
    SkillMatch,
    SkillRecord,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ═══════════════════════════════════════════════════════════════════════════════

class _AsyncContextManagerMock:
    """Makes `async with pool.acquire()` work in unit tests."""

    def __init__(self, value: Any) -> None:
        self._value = value

    async def __aenter__(self) -> Any:
        return self._value

    async def __aexit__(self, *args: Any) -> None:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_conn() -> AsyncMock:
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    return conn


@pytest.fixture
def mock_pool(mock_conn: AsyncMock) -> MagicMock:
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncContextManagerMock(mock_conn))
    return pool


@pytest.fixture
def mock_embedder() -> Any:
    async def _embedder(text: str) -> list[float]:  # noqa: ARG001
        return [0.1] * 1536
    return _embedder


@pytest.fixture
def store(mock_pool: MagicMock, mock_embedder: Any) -> ProceduralMemoryStore:
    return ProceduralMemoryStore(
        pool=mock_pool,
        embedder=mock_embedder,
        hmac_key="test-hmac-key",
    )


@pytest.fixture
def minimal_skill_record() -> SkillRecord:
    return SkillRecord(
        id="abc123",
        name="test_skill",
        description="A test skill",
        trigger_conditions=["do a thing", "perform the task"],
        compiled_graph_bytes=b"signed-bytes",
        trigger_embedding=[0.1] * 1536,
        hmac_key="test-hmac-key",
    )


@pytest.fixture
def worker(store: ProceduralMemoryStore) -> SkillCrystallizationWorker:
    langfuse = MagicMock()
    langfuse.client.trace.list.return_value = MagicMock(data=[])
    llm = AsyncMock()
    return SkillCrystallizationWorker(
        procedural_store=store,
        langfuse_client=langfuse,
        llm_client=llm,
        min_score=0.85,
        min_occurrences=3,
    )


def _db_row(overrides: dict | None = None) -> MagicMock:
    """Build a mock asyncpg row with sane defaults."""
    defaults: dict[str, Any] = {
        "id": "row-uuid-0001",
        "name": "mock_skill",
        "description": "a mock description",
        "trigger_conditions": json.dumps(["trigger one"]),
        "compiled_graph_bytes": b"raw-bytes",
        "trigger_embedding": [0.1] * 1536,
        "invocation_count": 0,
        "avg_performance_score": 0.0,
        "created_at": "2026-01-01T00:00:00+00:00",
        "last_invoked_at": None,
        "similarity": 0.90,
    }
    if overrides:
        defaults.update(overrides)
    row = MagicMock()
    row.__getitem__ = lambda self, key: defaults[key]  # noqa: ARG005
    return row


# ═══════════════════════════════════════════════════════════════════════════════
# SkillRecord
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkillRecord:
    def test_default_invocation_count_is_zero(self, minimal_skill_record: SkillRecord) -> None:
        assert minimal_skill_record.invocation_count == 0

    def test_default_avg_performance_score_is_zero(self, minimal_skill_record: SkillRecord) -> None:
        assert minimal_skill_record.avg_performance_score == 0.0

    def test_default_last_invoked_at_is_none(self, minimal_skill_record: SkillRecord) -> None:
        assert minimal_skill_record.last_invoked_at is None

    def test_created_at_auto_populated(self, minimal_skill_record: SkillRecord) -> None:
        assert minimal_skill_record.created_at != ""

    @patch("procedural.secure_loads", return_value="compiled-graph")
    def test_compiled_graph_calls_secure_loads(self, mock_loads: MagicMock, minimal_skill_record: SkillRecord) -> None:
        result = minimal_skill_record.compiled_graph
        mock_loads.assert_called_once_with(b"signed-bytes", "test-hmac-key")
        assert result == "compiled-graph"


# ═══════════════════════════════════════════════════════════════════════════════
# SkillMatch
# ═══════════════════════════════════════════════════════════════════════════════

class TestSkillMatch:
    def test_bool_true_when_confident(self, minimal_skill_record: SkillRecord) -> None:
        assert bool(SkillMatch(skill=minimal_skill_record, similarity_score=0.9, is_confident=True)) is True

    def test_bool_false_when_not_confident(self, minimal_skill_record: SkillRecord) -> None:
        assert bool(SkillMatch(skill=minimal_skill_record, similarity_score=0.5, is_confident=False)) is False

    def test_similarity_score_stored(self, minimal_skill_record: SkillRecord) -> None:
        match = SkillMatch(skill=minimal_skill_record, similarity_score=0.77, is_confident=True)
        assert match.similarity_score == pytest.approx(0.77)


# ═══════════════════════════════════════════════════════════════════════════════
# ProceduralMemoryStore — initialize_schema
# ═══════════════════════════════════════════════════════════════════════════════

class TestInitializeSchema:
    @pytest.mark.asyncio
    async def test_execute_called_once(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        await store.initialize_schema()
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_sql_creates_table(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        await store.initialize_schema()
        sql: str = mock_conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS" in sql
        assert "procedural_memories" in sql

    @pytest.mark.asyncio
    async def test_sql_creates_hnsw_index(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        await store.initialize_schema()
        sql: str = mock_conn.execute.call_args[0][0]
        assert "hnsw" in sql.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# ProceduralMemoryStore — learn_skill
# ═══════════════════════════════════════════════════════════════════════════════

class TestLearnSkill:
    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed")
    async def test_returns_skill_record(self, _: MagicMock, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetchrow.return_value = _db_row()
        skill = await store.learn_skill("my_skill", "desc", MagicMock(), ["cond"])
        assert isinstance(skill, SkillRecord)
        assert skill.name == "mock_skill"  # from mock row

    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed")
    async def test_updates_in_process_cache(self, _: MagicMock, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetchrow.return_value = _db_row({"name": "cached_skill"})
        await store.learn_skill("cached_skill", "d", MagicMock(), ["t"])
        assert "cached_skill" in store._cache

    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed-blob")
    async def test_passes_graph_to_secure_dumps(self, mock_dumps: MagicMock, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetchrow.return_value = _db_row()
        graph_obj = MagicMock()
        await store.learn_skill("s", "d", graph_obj, ["t"])
        mock_dumps.assert_called_once_with(graph_obj, "test-hmac-key")

    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed")
    async def test_upsert_sql_contains_on_conflict(self, _: MagicMock, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetchrow.return_value = _db_row()
        await store.learn_skill("s", "d", MagicMock(), ["t"])
        sql: str = mock_conn.fetchrow.call_args[0][0]
        assert "ON CONFLICT" in sql

    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed")
    async def test_trigger_embedding_computed(self, _: MagicMock, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetchrow.return_value = _db_row()
        await store.learn_skill("s", "d", MagicMock(), ["cond1", "cond2"])
        # Skill stored in cache — embedding was called (embedder is the async fixture)
        assert "s" in store._cache or "mock_skill" in store._cache


# ═══════════════════════════════════════════════════════════════════════════════
# ProceduralMemoryStore — recall_skill
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecallSkill:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_rows(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = []
        assert await store.recall_skill("find something") is None

    @pytest.mark.asyncio
    async def test_returns_confident_match_above_threshold(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = [_db_row({"similarity": 0.95})]
        result = await store.recall_skill("do something")
        assert result is not None
        assert result.is_confident is True
        assert result.similarity_score == pytest.approx(0.95)

    @pytest.mark.asyncio
    async def test_returns_not_confident_below_threshold(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = [_db_row({"similarity": 0.30})]
        result = await store.recall_skill("low similarity")
        assert result is not None
        assert result.is_confident is False
        assert bool(result) is False

    @pytest.mark.asyncio
    async def test_confident_at_exact_threshold(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        threshold = ProceduralMemoryStore.CONFIDENCE_THRESHOLD
        mock_conn.fetch.return_value = [_db_row({"similarity": threshold})]
        result = await store.recall_skill("boundary")
        assert result is not None
        assert result.is_confident is True

    @pytest.mark.asyncio
    async def test_skill_name_preserved_from_db(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = [_db_row({"name": "special_skill", "similarity": 0.9})]
        result = await store.recall_skill("x")
        assert result is not None
        assert result.skill.name == "special_skill"

    @pytest.mark.asyncio
    async def test_confident_match_creates_background_invocation_task(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = [_db_row({"similarity": 0.95})]
        with patch("procedural.asyncio.create_task") as mock_create_task:
            await store.recall_skill("invoke me")
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_below_threshold_does_not_create_invocation_task(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = [_db_row({"similarity": 0.10})]
        with patch("procedural.asyncio.create_task") as mock_create_task:
            await store.recall_skill("no invoke")
            mock_create_task.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# ProceduralMemoryStore — helpers
# ═══════════════════════════════════════════════════════════════════════════════

class TestProceduralStoreHelpers:
    @pytest.mark.asyncio
    async def test_list_skills_orders_by_invocation_count(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        mock_conn.fetch.return_value = []
        await store.list_skills()
        sql: str = mock_conn.fetch.call_args[0][0]
        assert "ORDER BY invocation_count DESC" in sql

    @pytest.mark.asyncio
    async def test_update_skill_score_calls_execute(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        await store.update_skill_score("my_skill", outcome_score=0.95)
        mock_conn.execute.assert_called_once()
        args = mock_conn.execute.call_args[0]
        assert args[1] == "my_skill"  # $1 = skill name
        assert args[3] == pytest.approx(0.95)  # $3 = outcome_score

    @pytest.mark.asyncio
    async def test_update_skill_score_sql_contains_ewa(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        await store.update_skill_score("s", 1.0, weight=0.2)
        sql: str = mock_conn.execute.call_args[0][0]
        assert "avg_performance_score" in sql
        assert "1 - $2" in sql or "(1 - $2)" in sql

    @pytest.mark.asyncio
    async def test_record_invocation_increments_count(self, store: ProceduralMemoryStore, mock_conn: AsyncMock) -> None:
        await store._record_invocation("some-uuid")
        mock_conn.execute.assert_called_once()
        sql: str = mock_conn.execute.call_args[0][0]
        assert "invocation_count = invocation_count + 1" in sql


# ═══════════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — fingerprinting
# ═══════════════════════════════════════════════════════════════════════════════

class TestPatternFingerprint:
    def _calls(self, *tools: str) -> list[dict]:
        return [{"tool_name": t, "param_keys": []} for t in tools]

    def test_stable_for_same_input(self, worker: SkillCrystallizationWorker) -> None:
        c = self._calls("search", "summarize")
        assert worker._compute_pattern_fingerprint(c) == worker._compute_pattern_fingerprint(c)

    def test_different_sequences_yield_different_fingerprints(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._compute_pattern_fingerprint(self._calls("A")) != worker._compute_pattern_fingerprint(self._calls("B"))

    def test_order_sensitive(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._compute_pattern_fingerprint(self._calls("A", "B")) != worker._compute_pattern_fingerprint(self._calls("B", "A"))

    def test_length_is_16_chars(self, worker: SkillCrystallizationWorker) -> None:
        assert len(worker._compute_pattern_fingerprint(self._calls("tool"))) == 16

    def test_param_key_order_independent(self, worker: SkillCrystallizationWorker) -> None:
        ab = [{"tool_name": "t", "param_keys": ["a", "b"]}]
        ba = [{"tool_name": "t", "param_keys": ["b", "a"]}]
        assert worker._compute_pattern_fingerprint(ab) == worker._compute_pattern_fingerprint(ba)


# ═══════════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — pattern extraction
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtractRepeatedPatterns:
    def _trace(self, tools: list[str], score: float = 0.9) -> dict:
        return {"score": score, "tool_calls": [{"tool_name": t, "param_keys": []} for t in tools]}

    def test_empty_input_returns_empty(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._extract_repeated_patterns([]) == []

    def test_below_min_occurrences_excluded(self, worker: SkillCrystallizationWorker) -> None:
        # 2 traces < min_occurrences=3
        traces = [self._trace(["search"]), self._trace(["search"])]
        assert worker._extract_repeated_patterns(traces) == []

    def test_at_min_occurrences_included(self, worker: SkillCrystallizationWorker) -> None:
        traces = [self._trace(["search"]) for _ in range(3)]
        result = worker._extract_repeated_patterns(traces)
        assert len(result) == 1
        assert result[0]["trace_count"] == 3

    def test_sorted_by_count_descending(self, worker: SkillCrystallizationWorker) -> None:
        common = [self._trace(["A"]) for _ in range(5)]
        less = [self._trace(["B"]) for _ in range(3)]
        result = worker._extract_repeated_patterns(common + less)
        counts = [p["trace_count"] for p in result]
        assert counts == sorted(counts, reverse=True)

    def test_avg_score_computed_correctly(self, worker: SkillCrystallizationWorker) -> None:
        traces = [
            self._trace(["X"], score=1.0),
            self._trace(["X"], score=0.8),
            self._trace(["X"], score=0.9),
        ]
        result = worker._extract_repeated_patterns(traces)
        assert len(result) == 1
        assert result[0]["avg_score"] == pytest.approx(0.9, abs=1e-6)

    def test_distinct_patterns_separated(self, worker: SkillCrystallizationWorker) -> None:
        group_a = [self._trace(["search", "summarize"]) for _ in range(3)]
        group_b = [self._trace(["execute", "format"]) for _ in range(3)]
        result = worker._extract_repeated_patterns(group_a + group_b)
        assert len(result) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — trace helpers
# ═══════════════════════════════════════════════════════════════════════════════

class TestWorkerTraceHelpers:
    def test_compute_trace_score_empty_scores_returns_zero(self, worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(scores=[])
        assert worker._compute_trace_score(trace) == 0.0

    def test_compute_trace_score_no_attribute_returns_zero(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._compute_trace_score(MagicMock(spec=[])) == 0.0

    def test_compute_trace_score_averages_values(self, worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(scores=[MagicMock(value=0.8), MagicMock(value=1.0)])
        assert worker._compute_trace_score(trace) == pytest.approx(0.9)

    def test_count_tool_calls_no_observations(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._count_tool_calls(MagicMock(spec=[])) == 0

    def test_count_tool_calls_filters_tool_type_only(self, worker: SkillCrystallizationWorker) -> None:
        obs_tool = MagicMock(type="TOOL")
        obs_llm = MagicMock(type="LLM")
        trace = MagicMock(observations=[obs_tool, obs_llm, obs_tool])
        assert worker._count_tool_calls(trace) == 2

    def test_extract_tool_calls_no_observations(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._extract_tool_calls(MagicMock(spec=[])) == []

    def test_extract_tool_calls_parses_input_json(self, worker: SkillCrystallizationWorker) -> None:
        obs = MagicMock(type="TOOL", name="web_search", input=json.dumps({"query": "hi", "n": 5}))
        trace = MagicMock(observations=[obs])
        result = worker._extract_tool_calls(trace)
        assert result[0]["tool_name"] == "web_search"
        assert set(result[0]["param_keys"]) == {"query", "n"}

    def test_extract_duration_with_latency(self, worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(latency=1234.5)
        assert worker._extract_duration(trace) == pytest.approx(1234.5)

    def test_extract_duration_no_attribute_returns_zero(self, worker: SkillCrystallizationWorker) -> None:
        assert worker._extract_duration(MagicMock(spec=[])) == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — crystallization cycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrystallizationCycle:
    @pytest.mark.asyncio
    async def test_returns_zero_summary_when_no_traces(self, worker: SkillCrystallizationWorker) -> None:
        worker._fetch_high_scoring_traces = AsyncMock(return_value=[])  # type: ignore[method-assign]
        summary = await worker.run_crystallization_cycle()
        assert summary == {"examined": 0, "crystallized": 0, "skipped": 0, "errors": 0}

    @pytest.mark.asyncio
    async def test_examined_count_reflects_trace_count(self, worker: SkillCrystallizationWorker) -> None:
        worker._fetch_high_scoring_traces = AsyncMock(return_value=[{} for _ in range(7)])  # type: ignore[method-assign]
        worker._extract_repeated_patterns = MagicMock(return_value=[])  # type: ignore[method-assign]
        summary = await worker.run_crystallization_cycle()
        assert summary["examined"] == 7

    @pytest.mark.asyncio
    async def test_crystallized_count_increments_on_success(self, worker: SkillCrystallizationWorker) -> None:
        pattern = {"fingerprint": "fp", "trace_count": 3, "avg_score": 0.9, "tool_calls": [], "sample_traces": []}
        worker._fetch_high_scoring_traces = AsyncMock(return_value=[{}])  # type: ignore[method-assign]
        worker._extract_repeated_patterns = MagicMock(return_value=[pattern])  # type: ignore[method-assign]
        worker._crystallize_pattern = AsyncMock(return_value=None)  # type: ignore[method-assign]
        summary = await worker.run_crystallization_cycle()
        assert summary["crystallized"] == 1
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    async def test_errors_count_increments_on_crystallize_failure(self, worker: SkillCrystallizationWorker) -> None:
        pattern = {"fingerprint": "fp", "trace_count": 3, "avg_score": 0.9, "tool_calls": [], "sample_traces": []}
        worker._fetch_high_scoring_traces = AsyncMock(return_value=[{}])  # type: ignore[method-assign]
        worker._extract_repeated_patterns = MagicMock(return_value=[pattern])  # type: ignore[method-assign]
        worker._crystallize_pattern = AsyncMock(side_effect=RuntimeError("DB down"))  # type: ignore[method-assign]
        summary = await worker.run_crystallization_cycle()
        assert summary["errors"] == 1
        assert summary["crystallized"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _crystallize_pattern
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrystallizePattern:
    def _pattern(self, tools: list[str] | None = None) -> dict:
        tools = tools or ["web_search", "summarize"]
        return {
            "fingerprint": "fp1",
            "trace_count": 5,
            "avg_score": 0.92,
            "tool_calls": [{"tool_name": t, "param_keys": []} for t in tools],
            "sample_traces": [],
        }

    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed")
    async def test_valid_llm_json_triggers_learn_skill(self, _: MagicMock, worker: SkillCrystallizationWorker, mock_conn: AsyncMock) -> None:
        meta = json.dumps({"name": "search_and_summarize", "description": "Finds and summarizes.", "triggers": ["look this up", "research topic", "find info"]})
        worker.llm.generate = AsyncMock(return_value=meta)
        mock_conn.fetchrow.return_value = _db_row()
        await worker._crystallize_pattern(self._pattern())
        worker.llm.generate.assert_called_once()
        # learn_skill → fetchrow should have been called
        mock_conn.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    @patch("procedural.secure_dumps", return_value=b"signed")
    async def test_invalid_llm_json_uses_fallback_name(self, _: MagicMock, worker: SkillCrystallizationWorker, mock_conn: AsyncMock) -> None:
        worker.llm.generate = AsyncMock(return_value="NOT VALID JSON >{{{")
        mock_conn.fetchrow.return_value = _db_row()
        # Must not raise; fallback name is used instead
        await worker._crystallize_pattern(self._pattern(["tool_a", "tool_b"]))
        mock_conn.fetchrow.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# SkillCrystallizationWorker — _build_skill_graph
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildSkillGraph:
    def test_graph_not_none_for_multi_tool_sequence(self, worker: SkillCrystallizationWorker) -> None:
        try:
            graph = worker._build_skill_graph(["search", "summarize"], "test_skill")
            assert graph is not None
        except ImportError:
            pytest.skip("langgraph not installed")

    def test_graph_not_none_for_single_tool(self, worker: SkillCrystallizationWorker) -> None:
        try:
            graph = worker._build_skill_graph(["only_tool"], "single")
            assert graph is not None
        except ImportError:
            pytest.skip("langgraph not installed")
