"""
supernova/tests/test_procedural.py

Unit tests for the procedural memory subsystem (procedural.py).

Architecture audit finding addressed:
    procedural.py (29,307 bytes) was flagged [ABSENT] — no test_procedural.py
    existed in supernova/tests/. This file closes that coverage gap.

Design decisions:
    - All asyncpg.Pool interactions are mocked via AsyncMock; no real
      PostgreSQL connection is required. Mark with @pytest.mark.unit.
    - secure_dumps / secure_loads are patched at the `procedural` module
      namespace (not the source module) to intercept the import binding.
    - LangGraph graph.compile() IS called in TestBuildSkillGraph — this
      tests real LangGraph behaviour, making those tests slightly slower
      but ensuring the compiled graph structure is exercised.
    - SkillCrystallizationWorker._fetch_high_scoring_traces is patched out
      in cycle tests to isolate cycle orchestration logic from Langfuse SDK.

Markers:
    @pytest.mark.unit     — all tests in this file
    @pytest.mark.asyncio  — all async tests (pytest-asyncio required)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# procedural.py lives at the repository root; pytest adds rootdir to sys.path
from procedural import (
    ProceduralMemoryStore,
    SkillCrystallizationWorker,
    SkillMatch,
    SkillRecord,
)

# ── Constants ────────────────────────────────────────────────────────────────

DUMMY_BYTES: bytes = b"hmac-signed-skill-payload"
DUMMY_EMBEDDING: list[float] = [0.1] * 1536
HMAC_KEY: str = "test-hmac-key-32chars-padded123"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def dummy_skill() -> SkillRecord:
    return SkillRecord(
        id="abc123",
        name="test_skill",
        description="A test skill for unit tests",
        trigger_conditions=["when user asks to test", "during QA workflow"],
        compiled_graph_bytes=DUMMY_BYTES,
        trigger_embedding=DUMMY_EMBEDDING,
        hmac_key=HMAC_KEY,
        invocation_count=5,
        avg_performance_score=0.88,
    )


@pytest.fixture
def mock_pool():
    """asyncpg.Pool mock returning a context-managed async connection."""
    pool = MagicMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


@pytest.fixture
def mock_embedder():
    """Async embedder returning a fixed 1536-dim vector."""

    async def _embed(text: str) -> list[float]:  # noqa: ARG001
        return DUMMY_EMBEDDING

    return _embed


@pytest.fixture
def procedural_store(mock_pool, mock_embedder) -> ProceduralMemoryStore:
    pool, _ = mock_pool
    return ProceduralMemoryStore(
        pool=pool,
        embedder=mock_embedder,
        confidence_threshold=0.72,
        hmac_key=HMAC_KEY,
    )


@pytest.fixture
def mock_langfuse() -> MagicMock:
    lf = MagicMock()
    lf.client.trace.list.return_value = MagicMock(data=[])
    return lf


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value=json.dumps({
            "name": "crystallized_test_skill",
            "description": "A crystallized skill for testing",
            "triggers": ["trigger A", "trigger B", "trigger C"],
        })
    )
    return llm


@pytest.fixture
def crystallization_worker(
    procedural_store: ProceduralMemoryStore,
    mock_langfuse: MagicMock,
    mock_llm: MagicMock,
) -> SkillCrystallizationWorker:
    return SkillCrystallizationWorker(
        procedural_store=procedural_store,
        langfuse_client=mock_langfuse,
        llm_client=mock_llm,
        min_score=0.85,
        min_occurrences=3,
    )


# ── SkillRecord ───────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestSkillRecord:
    def test_instantiation_stores_fields(self, dummy_skill: SkillRecord) -> None:
        assert dummy_skill.id == "abc123"
        assert dummy_skill.name == "test_skill"
        assert dummy_skill.invocation_count == 5
        assert dummy_skill.avg_performance_score == pytest.approx(0.88)
        assert dummy_skill.compiled_graph_bytes == DUMMY_BYTES
        assert dummy_skill.trigger_embedding == DUMMY_EMBEDDING

    def test_created_at_auto_populated_as_iso_string(self) -> None:
        skill = SkillRecord(
            id="x",
            name="auto_time",
            description="desc",
            trigger_conditions=[],
            compiled_graph_bytes=b"",
            trigger_embedding=[],
        )
        parsed = datetime.fromisoformat(skill.created_at)
        assert parsed.tzinfo is not None

    def test_last_invoked_at_defaults_none(self) -> None:
        skill = SkillRecord(
            id="y",
            name="no_invocation",
            description="",
            trigger_conditions=[],
            compiled_graph_bytes=b"",
            trigger_embedding=[],
        )
        assert skill.last_invoked_at is None

    def test_compiled_graph_property_delegates_to_secure_loads(self, dummy_skill: SkillRecord) -> None:
        fake_graph = object()
        with patch("procedural.secure_loads", return_value=fake_graph) as mock_sl:
            result = dummy_skill.compiled_graph
        mock_sl.assert_called_once_with(DUMMY_BYTES, HMAC_KEY)
        assert result is fake_graph

    def test_compiled_graph_raises_on_tampered_bytes(self, dummy_skill: SkillRecord) -> None:
        from procedural import SerializationError  # noqa: PLC0415
        with patch("procedural.secure_loads", side_effect=SerializationError("tampered")):
            with pytest.raises(SerializationError):
                _ = dummy_skill.compiled_graph

    def test_trigger_conditions_list_preserved(self, dummy_skill: SkillRecord) -> None:
        assert len(dummy_skill.trigger_conditions) == 2
        assert "when user asks to test" in dummy_skill.trigger_conditions


# ── SkillMatch ────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestSkillMatch:
    def test_bool_true_when_confident(self, dummy_skill: SkillRecord) -> None:
        match = SkillMatch(skill=dummy_skill, similarity_score=0.85, is_confident=True)
        assert bool(match) is True

    def test_bool_false_when_not_confident(self, dummy_skill: SkillRecord) -> None:
        match = SkillMatch(skill=dummy_skill, similarity_score=0.50, is_confident=False)
        assert bool(match) is False

    def test_bool_exactly_at_threshold_respects_is_confident_flag(self, dummy_skill: SkillRecord) -> None:
        # is_confident is set by the store, not derived from score here
        match_yes = SkillMatch(skill=dummy_skill, similarity_score=0.72, is_confident=True)
        match_no  = SkillMatch(skill=dummy_skill, similarity_score=0.72, is_confident=False)
        assert bool(match_yes) is True
        assert bool(match_no)  is False

    def test_similarity_score_stored_precisely(self, dummy_skill: SkillRecord) -> None:
        match = SkillMatch(skill=dummy_skill, similarity_score=0.913456, is_confident=True)
        assert match.similarity_score == pytest.approx(0.913456)

    def test_skill_reference_preserved(self, dummy_skill: SkillRecord) -> None:
        match = SkillMatch(skill=dummy_skill, similarity_score=0.8, is_confident=True)
        assert match.skill is dummy_skill


# ── ProceduralMemoryStore: schema ─────────────────────────────────────────────


@pytest.mark.unit
class TestInitializeSchema:
    @pytest.mark.asyncio
    async def test_creates_table_if_not_exists(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.execute = AsyncMock()
        await procedural_store.initialize_schema()
        conn.execute.assert_awaited_once()
        sql: str = conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS" in sql
        assert "procedural_memories" in sql

    @pytest.mark.asyncio
    async def test_schema_includes_hnsw_index(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.execute = AsyncMock()
        await procedural_store.initialize_schema()
        sql: str = conn.execute.call_args[0][0]
        assert "hnsw" in sql.lower()
        assert "vector_cosine_ops" in sql

    @pytest.mark.asyncio
    async def test_schema_includes_trigger_embedding_column(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.execute = AsyncMock()
        await procedural_store.initialize_schema()
        sql: str = conn.execute.call_args[0][0]
        assert "trigger_embedding" in sql


# ── ProceduralMemoryStore: learn_skill ────────────────────────────────────────


@pytest.mark.unit
class TestLearnSkill:
    def _fake_row(self, name: str = "test_skill") -> dict:
        return {
            "id": "skill-uuid-1234",
            "name": name,
            "invocation_count": 0,
            "avg_performance_score": 0.9,
            "created_at": datetime.now(timezone.utc),
        }

    @pytest.mark.asyncio
    async def test_returns_skill_record_with_correct_name(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=self._fake_row())
        with patch("procedural.secure_dumps", return_value=DUMMY_BYTES):
            skill = await procedural_store.learn_skill(
                name="test_skill",
                description="A test",
                compiled_graph=MagicMock(),
                trigger_conditions=["when testing"],
                performance_score=0.9,
            )
        assert skill.name == "test_skill"
        assert skill.compiled_graph_bytes == DUMMY_BYTES
        assert skill.trigger_embedding == DUMMY_EMBEDDING

    @pytest.mark.asyncio
    async def test_populates_in_process_cache(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=self._fake_row("cached_skill"))
        with patch("procedural.secure_dumps", return_value=b"bytes"):
            await procedural_store.learn_skill(
                name="cached_skill",
                description="",
                compiled_graph=MagicMock(),
                trigger_conditions=[],
            )
        assert "cached_skill" in procedural_store._cache

    @pytest.mark.asyncio
    async def test_skill_id_is_sha256_of_name_first_36_chars(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        captured: list[Any] = []

        async def capture_fetchrow(sql: str, *args: Any, **kwargs: Any) -> dict:
            captured.extend(args)
            return {
                "id": args[0],
                "name": args[1],
                "invocation_count": 0,
                "avg_performance_score": 0.0,
                "created_at": datetime.now(timezone.utc),
            }

        conn.fetchrow = capture_fetchrow
        with patch("procedural.secure_dumps", return_value=b"b"):
            await procedural_store.learn_skill(
                name="my_unique_skill",
                description="",
                compiled_graph=MagicMock(),
                trigger_conditions=[],
            )
        expected_id = hashlib.sha256(b"my_unique_skill").hexdigest()[:36]
        assert captured[0] == expected_id

    @pytest.mark.asyncio
    async def test_trigger_conditions_joined_for_embedding(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=self._fake_row())
        calls: list[str] = []

        async def recording_embedder(text: str) -> list[float]:
            calls.append(text)
            return DUMMY_EMBEDDING

        procedural_store.embedder = recording_embedder
        with patch("procedural.secure_dumps", return_value=b"b"):
            await procedural_store.learn_skill(
                name="emb_test",
                description="",
                compiled_graph=MagicMock(),
                trigger_conditions=["cond A", "cond B", "cond C"],
            )
        assert len(calls) == 1
        assert "cond A" in calls[0] and "cond B" in calls[0] and "cond C" in calls[0]


# ── ProceduralMemoryStore: recall_skill ───────────────────────────────────────


@pytest.mark.unit
class TestRecallSkill:
    def _fake_row(self, similarity: float, name: str = "code_review_skill") -> dict:
        return {
            "id": "skill-id",
            "name": name,
            "description": "Reviews code",
            "trigger_conditions": json.dumps(["when user shares code"]),
            "compiled_graph_bytes": DUMMY_BYTES,
            "trigger_embedding": DUMMY_EMBEDDING,
            "invocation_count": 2,
            "avg_performance_score": 0.9,
            "created_at": datetime.now(timezone.utc),
            "last_invoked_at": None,
            "similarity": similarity,
        }

    @pytest.mark.asyncio
    async def test_returns_none_when_no_rows(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[])
        result = await procedural_store.recall_skill("some situation")
        assert result is None

    @pytest.mark.asyncio
    async def test_confident_match_above_threshold(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[self._fake_row(similarity=0.85)])
        with patch("procedural.asyncio.create_task"):
            result = await procedural_store.recall_skill("show me this code")
        assert result is not None
        assert result.is_confident is True
        assert result.similarity_score == pytest.approx(0.85)
        assert result.skill.name == "code_review_skill"

    @pytest.mark.asyncio
    async def test_not_confident_below_threshold(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[self._fake_row(similarity=0.50)])
        result = await procedural_store.recall_skill("unrelated query")
        assert result is not None
        assert result.is_confident is False
        assert not bool(result)

    @pytest.mark.asyncio
    async def test_invocation_task_created_when_confident(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[self._fake_row(similarity=0.90)])
        with patch("procedural.asyncio.create_task") as mock_task:
            await procedural_store.recall_skill("confident situation")
        mock_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_invocation_task_below_threshold(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[self._fake_row(similarity=0.40)])
        with patch("procedural.asyncio.create_task") as mock_task:
            await procedural_store.recall_skill("unlikely match")
        mock_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_conditions_deserialized_from_json(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conditions = ["cond 1", "cond 2"]
        row = self._fake_row(similarity=0.88)
        row["trigger_conditions"] = json.dumps(conditions)
        conn.fetch = AsyncMock(return_value=[row])
        with patch("procedural.asyncio.create_task"):
            result = await procedural_store.recall_skill("something")
        assert result is not None
        assert result.skill.trigger_conditions == conditions

    @pytest.mark.asyncio
    async def test_hmac_key_injected_into_skill_record(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[self._fake_row(similarity=0.80)])
        with patch("procedural.asyncio.create_task"):
            result = await procedural_store.recall_skill("check hmac")
        assert result is not None
        assert result.skill.hmac_key == HMAC_KEY


# ── ProceduralMemoryStore: update_skill_score ─────────────────────────────────


@pytest.mark.unit
class TestUpdateSkillScore:
    @pytest.mark.asyncio
    async def test_execute_called_with_correct_args(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.execute = AsyncMock()
        await procedural_store.update_skill_score(
            skill_name="my_skill",
            outcome_score=1.0,
            weight=0.2,
        )
        conn.execute.assert_awaited_once()
        args = conn.execute.call_args[0]
        assert "my_skill" in args
        assert 1.0 in args
        assert 0.2 in args

    @pytest.mark.asyncio
    async def test_ewa_formula_present_in_sql(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.execute = AsyncMock()
        await procedural_store.update_skill_score("sk", 0.5)
        sql: str = conn.execute.call_args[0][0]
        # EWA: score * (1 - weight) + new * weight
        assert "1 -" in sql or "(1-" in sql or "1-" in sql

    @pytest.mark.asyncio
    async def test_default_weight_is_0_2(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.execute = AsyncMock()
        await procedural_store.update_skill_score("sk", 0.8)
        args = conn.execute.call_args[0]
        assert 0.2 in args


# ── ProceduralMemoryStore: list_skills ────────────────────────────────────────


@pytest.mark.unit
class TestListSkills:
    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[
            {
                "name": "skill_a", "description": "a", "invocation_count": 3,
                "avg_performance_score": 0.9, "created_at": "2026-01-01",
                "last_invoked_at": None, "condition_count": 2,
            },
        ])
        result = await procedural_store.list_skills()
        assert isinstance(result, list)
        assert result[0]["name"] == "skill_a"

    @pytest.mark.asyncio
    async def test_empty_store_returns_empty_list(self, procedural_store: ProceduralMemoryStore, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetch = AsyncMock(return_value=[])
        result = await procedural_store.list_skills()
        assert result == []


# ── SkillCrystallizationWorker: fingerprinting ────────────────────────────────


@pytest.mark.unit
class TestComputePatternFingerprint:
    def test_identical_sequences_produce_same_fingerprint(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        calls_a = [{"tool_name": "web_search", "param_keys": ["query"]},
                   {"tool_name": "summarize",   "param_keys": ["text"]}]
        calls_b = [{"tool_name": "web_search", "param_keys": ["query"]},
                   {"tool_name": "summarize",   "param_keys": ["text"]}]
        assert (crystallization_worker._compute_pattern_fingerprint(calls_a) ==
                crystallization_worker._compute_pattern_fingerprint(calls_b))

    def test_different_tools_different_fingerprint(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        calls_a = [{"tool_name": "web_search", "param_keys": ["query"]}]
        calls_b = [{"tool_name": "code_exec",  "param_keys": ["code"]}]
        assert (crystallization_worker._compute_pattern_fingerprint(calls_a) !=
                crystallization_worker._compute_pattern_fingerprint(calls_b))

    def test_fingerprint_is_16_hex_chars(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        fp = crystallization_worker._compute_pattern_fingerprint(
            [{"tool_name": "tool_x", "param_keys": ["a", "b"]}]
        )
        assert len(fp) == 16
        assert all(c in "0123456789abcdef" for c in fp)

    def test_param_key_order_ignored(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        """param_keys are sorted in fingerprint — order of keys must not matter."""
        calls_a = [{"tool_name": "t", "param_keys": ["a", "b"]}]
        calls_b = [{"tool_name": "t", "param_keys": ["b", "a"]}]
        assert (crystallization_worker._compute_pattern_fingerprint(calls_a) ==
                crystallization_worker._compute_pattern_fingerprint(calls_b))

    def test_empty_sequence_returns_valid_fingerprint(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        fp = crystallization_worker._compute_pattern_fingerprint([])
        assert isinstance(fp, str)
        assert len(fp) == 16

    def test_tool_order_matters(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        """Different tool orderings must produce different fingerprints."""
        calls_ab = [{"tool_name": "a", "param_keys": []}, {"tool_name": "b", "param_keys": []}]
        calls_ba = [{"tool_name": "b", "param_keys": []}, {"tool_name": "a", "param_keys": []}]
        assert (crystallization_worker._compute_pattern_fingerprint(calls_ab) !=
                crystallization_worker._compute_pattern_fingerprint(calls_ba))


# ── SkillCrystallizationWorker: pattern extraction ───────────────────────────


@pytest.mark.unit
class TestExtractRepeatedPatterns:
    def _make_trace(self, tool_names: list[str], score: float = 0.9) -> dict:
        return {
            "score": score,
            "tool_calls": [{"tool_name": t, "param_keys": ["q"]} for t in tool_names],
            "duration_ms": 100.0,
            "metadata": {},
        }

    def test_pattern_with_enough_occurrences_returned(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        traces = [self._make_trace(["search", "summarize"]) for _ in range(4)]
        patterns = crystallization_worker._extract_repeated_patterns(traces)
        assert len(patterns) == 1
        assert patterns[0]["trace_count"] == 4

    def test_pattern_below_min_occurrences_excluded(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        # min_occurrences=3; only 2 traces here
        traces = [self._make_trace(["search", "summarize"]) for _ in range(2)]
        patterns = crystallization_worker._extract_repeated_patterns(traces)
        assert patterns == []

    def test_two_patterns_returned_sorted_by_count_desc(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        traces = (
            [self._make_trace(["a", "b"]) for _ in range(5)] +
            [self._make_trace(["c", "d"]) for _ in range(3)]
        )
        patterns = crystallization_worker._extract_repeated_patterns(traces)
        assert len(patterns) == 2
        assert patterns[0]["trace_count"] == 5
        assert patterns[1]["trace_count"] == 3

    def test_average_score_computed_correctly(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        traces = [
            self._make_trace(["tool_x"], score=0.9),
            self._make_trace(["tool_x"], score=0.7),
            self._make_trace(["tool_x"], score=0.8),
        ]
        patterns = crystallization_worker._extract_repeated_patterns(traces)
        assert len(patterns) == 1
        assert patterns[0]["avg_score"] == pytest.approx(0.8)

    def test_single_occurrence_never_returned(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        traces = [
            self._make_trace(["unique_a"]),
            self._make_trace(["unique_b"]),
            self._make_trace(["unique_c"]),
        ]
        patterns = crystallization_worker._extract_repeated_patterns(traces)
        assert patterns == []


# ── SkillCrystallizationWorker: crystallization cycle ────────────────────────


@pytest.mark.unit
class TestRunCrystallizationCycle:
    @pytest.mark.asyncio
    async def test_empty_traces_returns_zero_crystallized(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        with patch.object(crystallization_worker, "_fetch_high_scoring_traces", AsyncMock(return_value=[])):
            summary = await crystallization_worker.run_crystallization_cycle()
        assert summary["crystallized"] == 0
        assert summary["examined"] == 0
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    async def test_crystallize_errors_are_counted_not_raised(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        qualifying = [
            {"id": f"t{i}", "score": 0.95,
             "tool_calls": [{"tool_name": "x", "param_keys": []}],
             "duration_ms": 0, "metadata": {}}
            for i in range(3)
        ]
        with (
            patch.object(crystallization_worker, "_fetch_high_scoring_traces", AsyncMock(return_value=qualifying)),
            patch.object(crystallization_worker, "_crystallize_pattern", AsyncMock(side_effect=RuntimeError("fail"))),
        ):
            summary = await crystallization_worker.run_crystallization_cycle()
        assert summary["errors"] >= 1
        assert summary["crystallized"] == 0

    @pytest.mark.asyncio
    async def test_full_cycle_crystallizes_qualifying_pattern(self, crystallization_worker: SkillCrystallizationWorker, mock_pool) -> None:
        _, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={
            "id": "new-uuid",
            "name": "crystallized_test_skill",
            "invocation_count": 0,
            "avg_performance_score": 0.9,
            "created_at": datetime.now(timezone.utc),
        })
        qualifying = [
            {"id": f"t{i}", "score": 0.92,
             "tool_calls": [
                 {"tool_name": "web_search", "param_keys": ["q"]},
                 {"tool_name": "summarize",  "param_keys": ["text"]},
             ],
             "duration_ms": 120, "metadata": {}}
            for i in range(3)
        ]
        with (
            patch.object(crystallization_worker, "_fetch_high_scoring_traces", AsyncMock(return_value=qualifying)),
            patch("procedural.secure_dumps", return_value=DUMMY_BYTES),
        ):
            summary = await crystallization_worker.run_crystallization_cycle()
        assert summary["crystallized"] >= 1
        assert summary["errors"] == 0

    @pytest.mark.asyncio
    async def test_examined_count_matches_traces_fetched(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        traces = [
            {"id": f"t{i}", "score": 0.5,
             "tool_calls": [{"tool_name": f"tool_{i}", "param_keys": []}],
             "duration_ms": 0, "metadata": {}}
            for i in range(7)
        ]
        with patch.object(crystallization_worker, "_fetch_high_scoring_traces", AsyncMock(return_value=traces)):
            summary = await crystallization_worker.run_crystallization_cycle()
        assert summary["examined"] == 7


# ── SkillCrystallizationWorker: _build_skill_graph ───────────────────────────


@pytest.mark.unit
class TestBuildSkillGraph:
    def test_single_tool_sequence_compiles(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        graph = crystallization_worker._build_skill_graph(
            tool_sequence=["web_search"],
            skill_name="single_tool_skill",
        )
        assert graph is not None

    def test_multi_tool_sequence_compiles(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        graph = crystallization_worker._build_skill_graph(
            tool_sequence=["web_search", "summarize", "format_output"],
            skill_name="multi_step_skill",
        )
        assert graph is not None

    def test_graph_is_invocable(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        """The compiled graph must be callable (accepts state dict)."""
        graph = crystallization_worker._build_skill_graph(
            tool_sequence=["tool_a"],
            skill_name="invocable_skill",
        )
        assert callable(graph.invoke) or hasattr(graph, "ainvoke")

    def test_empty_tool_sequence_raises(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        """Empty sequence causes IndexError on node_names[0] — expected current behaviour."""
        with pytest.raises((IndexError, Exception)):
            crystallization_worker._build_skill_graph(
                tool_sequence=[],
                skill_name="empty_skill",
            )


# ── SkillCrystallizationWorker: helper extraction methods ────────────────────


@pytest.mark.unit
class TestHelperMethods:
    def test_compute_trace_score_returns_zero_with_no_scores_attr(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(spec=[])  # No 'scores' attribute
        assert crystallization_worker._compute_trace_score(trace) == 0.0

    def test_compute_trace_score_returns_zero_with_empty_scores(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(scores=[])
        assert crystallization_worker._compute_trace_score(trace) == 0.0

    def test_compute_trace_score_averages_multiple_values(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(scores=[MagicMock(value=0.8), MagicMock(value=1.0)])
        assert crystallization_worker._compute_trace_score(trace) == pytest.approx(0.9)

    def test_compute_trace_score_single_value(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(scores=[MagicMock(value=0.75)])
        assert crystallization_worker._compute_trace_score(trace) == pytest.approx(0.75)

    def test_count_tool_calls_returns_zero_no_observations_attr(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(spec=[])
        assert crystallization_worker._count_tool_calls(trace) == 0

    def test_count_tool_calls_only_counts_tool_type(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        obs_tool = MagicMock(type="TOOL")
        obs_llm  = MagicMock(type="LLM")
        obs_ret  = MagicMock(type="RETRIEVAL")
        trace = MagicMock(observations=[obs_tool, obs_llm, obs_tool, obs_ret])
        assert crystallization_worker._count_tool_calls(trace) == 2

    def test_extract_tool_calls_returns_empty_list_no_observations(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(spec=[])
        assert crystallization_worker._extract_tool_calls(trace) == []

    def test_extract_tool_calls_parses_input_json(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        obs = MagicMock(type="TOOL", name="web_search", input=json.dumps({"query": "test", "limit": 5}))
        trace = MagicMock(observations=[obs])
        calls = crystallization_worker._extract_tool_calls(trace)
        assert len(calls) == 1
        assert calls[0]["tool_name"] == "web_search"
        assert set(calls[0]["param_keys"]) == {"query", "limit"}

    def test_extract_duration_with_latency_attr(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(latency=250.5)
        assert crystallization_worker._extract_duration(trace) == pytest.approx(250.5)

    def test_extract_duration_returns_zero_without_latency(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(spec=[])
        assert crystallization_worker._extract_duration(trace) == 0.0

    def test_extract_duration_handles_none_latency(self, crystallization_worker: SkillCrystallizationWorker) -> None:
        trace = MagicMock(latency=None)
        assert crystallization_worker._extract_duration(trace) == 0.0
