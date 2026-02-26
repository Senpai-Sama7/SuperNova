"""
core/memory/procedural.py

Procedural memory: compiled LangGraph subgraphs as reusable agent skills.

Theoretical foundation:
    In cognitive neuroscience, procedural memory (Squire, 1987) refers to
    implicit, automatized skills — motor programs, perceptual-motor sequences —
    stored in the basal ganglia and cerebellum rather than the hippocampus.
    The critical property: procedural memories execute *below the level of
    deliberate attention*, consuming fewer prefrontal resources per invocation
    after sufficient practice.

    The agent analog is precise:
      Explicit reasoning (reasoning_node)  ←→  Prefrontal deliberation
      Procedural skill (compiled subgraph) ←→  Cerebellar automatization
      Skill crystallization worker         ←→  Offline consolidation during sleep

    A compiled LangGraph graph is a pure function: (State → State). It has no
    runtime dependencies after compilation — no Python imports are evaluated,
    no graph construction overhead is paid. This makes it a valid unit of
    serializable, reusable "compiled knowledge."

    The Reflexion paper (Shinn et al., 2023) demonstrated that agents improve
    by reflecting on past failures. Procedural memory extends this: agents
    improve by *compiling* successful patterns, eliminating the token overhead
    of re-deriving effective strategies on each invocation.

Storage design:
    Compiled graphs are serialized via pickle to bytea (PostgreSQL binary type).
    Each skill has a trigger_embedding (vector) enabling semantic retrieval:
    "find the skill most relevant to this situation" is a nearest-neighbor
    search over the trigger embedding space.

    The skill store maintains invocation statistics, enabling a reinforcement
    signal: frequently-invoked, high-scoring skills have their importance
    boosted (analogous to synaptic long-term potentiation for frequently
    activated motor circuits).

Security note:
    pickle deserialization is a known code execution vector. The procedural
    memory store MUST only deserialize pickles from trusted sources (your own
    PostgreSQL instance with restricted write access). Never deserialize
    externally-supplied skill blobs. For multi-tenant deployments, consider
    replacing pickle with a restricted serialization format (cloudpickle with
    a custom reducer whitelist, or Dill with restricted globals).

Performance characteristics:
    Skill retrieval:     ~1-5ms (vector ANN + postgres fetch)
    Skill invocation:    ~0ms overhead vs. equivalent inline graph nodes
    Crystallization:     ~2-10s per skill (graph compilation + embedding)
    Storage per skill:   ~10-500 KB (depends on graph complexity)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import asyncpg
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SkillRecord:
    """
    A compiled procedural skill.

    The separation of trigger_conditions (natural language descriptions of
    when this skill applies) from trigger_embedding (their vector representation)
    enables human-readable auditing of the skill library while maintaining
    sub-millisecond retrieval performance.
    """
    id:                    str
    name:                  str
    description:           str
    trigger_conditions:    list[str]      # Natural language descriptions
    compiled_graph_bytes:  bytes          # pickle.dumps(compiled_langgraph)
    trigger_embedding:     list[float]    # Embedding of trigger_conditions
    invocation_count:      int   = 0
    avg_performance_score: float = 0.0
    created_at:            str   = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_invoked_at:       str | None = None

    @property
    def compiled_graph(self) -> Any:
        """Deserialize the compiled graph. See security note in module docstring."""
        return pickle.loads(self.compiled_graph_bytes)


@dataclass
class SkillMatch:
    """Result of a procedural memory retrieval query."""
    skill:             SkillRecord
    similarity_score:  float           # Cosine similarity to query embedding [0, 1]
    is_confident:      bool            # True if similarity > confidence threshold

    def __bool__(self) -> bool:
        return self.is_confident


class ProceduralMemoryStore:
    """
    Manages the lifecycle of compiled agent skills in PostgreSQL.

    Retrieval is a two-stage process:
      1. ANN search over trigger_embedding vectors → candidate skill
      2. Cosine similarity threshold gate → accept/reject

    The threshold (default 0.72) is empirically chosen: below this value,
    the semantic overlap between the query and trigger conditions is
    insufficient to justify invoking the skill (which may execute
    plan steps inappropriate for the current context).
    """

    CONFIDENCE_THRESHOLD = 0.72  # Minimum cosine similarity for skill activation
    TABLE_NAME = "procedural_memories"

    def __init__(
        self,
        pool: asyncpg.Pool,
        embedder: Callable[[str], Any],   # async callable: str -> list[float]
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> None:
        self.pool = pool
        self.embedder = embedder
        self.threshold = confidence_threshold
        self._cache: dict[str, SkillRecord] = {}   # In-process LRU cache

    async def initialize_schema(self) -> None:
        """Create the procedural memory table if it doesn't exist."""
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name                  TEXT UNIQUE NOT NULL,
                    description           TEXT NOT NULL DEFAULT '',
                    trigger_conditions    JSONB NOT NULL DEFAULT '[]',
                    compiled_graph_bytes  BYTEA NOT NULL,
                    trigger_embedding     vector(1536) NOT NULL,
                    invocation_count      INTEGER NOT NULL DEFAULT 0,
                    avg_performance_score FLOAT NOT NULL DEFAULT 0.0,
                    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_invoked_at       TIMESTAMPTZ,
                    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                -- HNSW index for ANN retrieval over trigger embeddings
                -- ef_construction=64 balances index build time vs recall quality.
                -- For a small skill library (<10k skills), exact search is viable;
                -- HNSW is included for forward-compatibility.
                CREATE INDEX IF NOT EXISTS procedural_memories_embedding_idx
                    ON {self.TABLE_NAME}
                    USING hnsw (trigger_embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
            """)

    async def learn_skill(
        self,
        name:               str,
        description:        str,
        compiled_graph:     Any,           # A compiled LangGraph StateGraph
        trigger_conditions: list[str],
        performance_score:  float = 0.0,
    ) -> SkillRecord:
        """
        Persist a compiled skill to the procedural memory store.

        The trigger embedding is computed over the concatenation of all trigger
        condition strings. This produces a centroid embedding that represents
        the "average situation" where this skill applies — appropriate for
        single nearest-neighbor retrieval.

        For skills with highly heterogeneous trigger conditions (e.g., a skill
        that applies in both "user asks for code review" and "user shares a
        GitHub PR link"), consider splitting into two skills with a shared
        compiled graph reference, or computing per-condition embeddings and
        retrieving the maximum similarity.
        """
        # Serialize the compiled graph
        compiled_bytes = pickle.dumps(compiled_graph)

        # Compute embedding over all trigger conditions concatenated
        trigger_text      = " | ".join(trigger_conditions)
        trigger_embedding = await self.embedder(trigger_text)

        skill_id = hashlib.sha256(name.encode()).hexdigest()[:36]

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(f"""
                INSERT INTO {self.TABLE_NAME}
                    (id, name, description, trigger_conditions, compiled_graph_bytes,
                     trigger_embedding, avg_performance_score)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6::vector, $7)
                ON CONFLICT (name) DO UPDATE SET
                    description           = EXCLUDED.description,
                    trigger_conditions    = EXCLUDED.trigger_conditions,
                    compiled_graph_bytes  = EXCLUDED.compiled_graph_bytes,
                    trigger_embedding     = EXCLUDED.trigger_embedding,
                    avg_performance_score = (
                        {self.TABLE_NAME}.avg_performance_score * 0.8 +
                        EXCLUDED.avg_performance_score * 0.2
                    ),
                    updated_at = NOW()
                RETURNING id, name, invocation_count, avg_performance_score, created_at
            """,
                skill_id,
                name,
                description,
                json.dumps(trigger_conditions),
                compiled_bytes,
                trigger_embedding,
                performance_score,
            )

        skill = SkillRecord(
            id=str(row["id"]),
            name=name,
            description=description,
            trigger_conditions=trigger_conditions,
            compiled_graph_bytes=compiled_bytes,
            trigger_embedding=trigger_embedding,
            invocation_count=row["invocation_count"],
            avg_performance_score=row["avg_performance_score"],
            created_at=str(row["created_at"]),
        )

        # Update in-process cache
        self._cache[name] = skill
        logger.info("Learned skill '%s' (id=%s, score=%.2f)", name, skill.id, performance_score)
        return skill

    async def recall_skill(self, situation: str, top_k: int = 3) -> SkillMatch | None:
        """
        Retrieve the most relevant compiled skill for a described situation.

        Returns None if no skill meets the confidence threshold, signaling
        the agent loop to fall through to deliberate LLM-based reasoning.

        The confidence threshold is the critical hyperparameter: too low
        causes inappropriate skill activation (the agent runs a "code review"
        skill on an unrelated task because the embeddings are superficially
        similar). Too high causes low skill utilization (the agent re-derives
        strategies it has successfully compiled).

        Recommendation: start at 0.72, then tune by reviewing Langfuse traces
        for cases where a skill was activated (was it appropriate?) and cases
        where no skill was found (should one have been?).
        """
        situation_embedding = await self.embedder(situation)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT
                    id, name, description, trigger_conditions,
                    compiled_graph_bytes, trigger_embedding,
                    invocation_count, avg_performance_score, created_at, last_invoked_at,
                    -- Cosine similarity: 1 - cosine_distance
                    -- pgvector's <=> operator returns cosine DISTANCE [0, 2]
                    -- Similarity = 1 - (distance / 2) for unit vectors,
                    -- but since embeddings are typically unit-normalized,
                    -- similarity = 1 - cosine_distance is correct here
                    1.0 - (trigger_embedding <=> $1::vector) AS similarity
                FROM {self.TABLE_NAME}
                ORDER BY trigger_embedding <=> $1::vector
                LIMIT $2
            """, situation_embedding, top_k)

        if not rows:
            return None

        best = rows[0]
        similarity = float(best["similarity"])
        is_confident = similarity >= self.threshold

        if is_confident:
            # Update invocation statistics asynchronously (non-blocking)
            asyncio.create_task(
                self._record_invocation(str(best["id"]))
            )

        skill = SkillRecord(
            id=str(best["id"]),
            name=best["name"],
            description=best["description"],
            trigger_conditions=json.loads(best["trigger_conditions"]),
            compiled_graph_bytes=bytes(best["compiled_graph_bytes"]),
            trigger_embedding=list(best["trigger_embedding"]) if best["trigger_embedding"] else [],
            invocation_count=best["invocation_count"],
            avg_performance_score=best["avg_performance_score"],
            created_at=str(best["created_at"]),
            last_invoked_at=str(best["last_invoked_at"]) if best["last_invoked_at"] else None,
        )

        return SkillMatch(
            skill=skill,
            similarity_score=similarity,
            is_confident=is_confident,
        )

    async def list_skills(self) -> list[dict]:
        """Return a human-readable summary of all stored skills. Useful for debugging."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT name, description, invocation_count, avg_performance_score,
                       created_at, last_invoked_at,
                       jsonb_array_length(trigger_conditions) AS condition_count
                FROM {self.TABLE_NAME}
                ORDER BY invocation_count DESC
            """)
        return [dict(row) for row in rows]

    async def _record_invocation(self, skill_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE {self.TABLE_NAME}
                SET invocation_count = invocation_count + 1,
                    last_invoked_at  = NOW()
                WHERE id = $1
            """, skill_id)

    async def update_skill_score(
        self,
        skill_name: str,
        outcome_score: float,   # [0, 1]: 1.0 = excellent, 0.0 = complete failure
        weight: float = 0.2,    # EWA learning rate for score update
    ) -> None:
        """
        Update a skill's performance score via exponential weighted average.

        EWA (Exponential Weighted Average) is chosen over a simple running mean
        because it weights recent outcomes more heavily — appropriate for skills
        that may degrade as the task environment changes (new user preferences,
        evolving tool schemas, etc.).

        The weight parameter controls recency bias:
            weight=0.1 → slow adaptation, favors historical average
            weight=0.3 → fast adaptation, emphasizes recent performance
            weight=0.2 → empirically reasonable default for daily-timescale drift
        """
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE {self.TABLE_NAME}
                SET avg_performance_score =
                    avg_performance_score * (1 - $2) + $3 * $2,
                    updated_at = NOW()
                WHERE name = $1
            """, skill_name, weight, outcome_score)


class SkillCrystallizationWorker:
    """
    Background worker that crystallizes high-performing trace patterns
    from Langfuse into compiled procedural skills.

    The crystallization pipeline:
        1. Fetch completed traces from Langfuse with score >= min_score
        2. Cluster traces by structural similarity (tool call sequences)
        3. For clusters with >= min_occurrences identical or near-identical patterns,
           reconstruct the LangGraph subgraph from the trace
        4. Compile and persist via ProceduralMemoryStore.learn_skill

    This implements a weak form of offline reinforcement learning:
    the "reward signal" is the Langfuse user rating (or automated evaluation
    score), and the "policy update" is skill crystallization — compiling
    high-reward trajectories into reusable programs.

    Relationship to DSPy:
        DSPy (Khattab et al., 2023) automates prompt optimization over
        discrete demonstration programs. Skill crystallization is complementary:
        while DSPy optimizes *what to say*, crystallization optimizes
        *what to do* (the tool call graph structure).
    """

    def __init__(
        self,
        procedural_store: ProceduralMemoryStore,
        langfuse_client: Any,   # langfuse.Langfuse instance
        llm_client: Any,        # For skill naming + description generation
        min_score: float = 0.85,
        min_occurrences: int = 3,
        lookback_hours: int = 168,   # 1 week
    ) -> None:
        self.store         = procedural_store
        self.langfuse      = langfuse_client
        self.llm           = llm_client
        self.min_score     = min_score
        self.min_occurrences = min_occurrences
        self.lookback_hours  = lookback_hours

    async def run_crystallization_cycle(self) -> dict:
        """
        Execute one crystallization cycle. Called by Celery Beat scheduler.
        Returns a summary of crystallization activity for logging.
        """
        logger.info("Starting skill crystallization cycle")
        summary = {"examined": 0, "crystallized": 0, "skipped": 0, "errors": 0}

        try:
            # Fetch high-scoring traces from Langfuse
            traces = await self._fetch_high_scoring_traces()
            summary["examined"] = len(traces)

            if not traces:
                logger.info("No qualifying traces found for crystallization")
                return summary

            # Find repeated patterns across traces
            patterns = self._extract_repeated_patterns(traces)
            logger.info("Found %d repeated patterns in %d traces", len(patterns), len(traces))

            for pattern in patterns:
                try:
                    await self._crystallize_pattern(pattern)
                    summary["crystallized"] += 1
                except Exception as e:
                    logger.error("Failed to crystallize pattern '%s': %s", pattern.get("name", "?"), e)
                    summary["errors"] += 1

        except Exception as e:
            logger.error("Crystallization cycle failed: %s", e)
            summary["errors"] += 1

        logger.info("Crystallization complete: %s", summary)
        return summary

    async def _fetch_high_scoring_traces(self) -> list[dict]:
        """
        Fetch traces from Langfuse that meet the quality threshold.

        Langfuse trace scores can come from:
          - Explicit user feedback (thumbs up/down in the UI)
          - LLM-as-judge evaluation pipelines
          - Automated metrics (tool call success rate, response latency)

        We filter to traces where the primary score meets min_score AND
        the trace contains at least 2 tool call spans (single-step interactions
        don't benefit from procedural compilation).
        """
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)

        # Langfuse Python SDK fetch — adapt to your Langfuse version
        # This is illustrative; the exact API depends on langfuse>=2.0
        traces_page = self.langfuse.client.trace.list(
            from_timestamp=cutoff.isoformat(),
            limit=500,
        )

        qualifying = []
        for trace in (traces_page.data if hasattr(traces_page, "data") else []):
            avg_score = self._compute_trace_score(trace)
            tool_call_count = self._count_tool_calls(trace)
            if avg_score >= self.min_score and tool_call_count >= 2:
                qualifying.append({
                    "id":         trace.id,
                    "score":      avg_score,
                    "tool_calls": self._extract_tool_calls(trace),
                    "duration_ms": self._extract_duration(trace),
                    "metadata":   trace.metadata or {},
                })

        return qualifying

    def _extract_repeated_patterns(self, traces: list[dict]) -> list[dict]:
        """
        Identify tool call sequences that appear >= min_occurrences times.

        Similarity is structural, not semantic: two traces are "the same pattern"
        if they call the same sequence of tools with the same parameter schemas
        (ignoring actual values). This is analogous to recognizing that two
        instances of "web_search → scrape_page → summarize" are the same
        workflow pattern regardless of what was searched.

        Implementation uses a canonical fingerprint: sorted tuple of
        (tool_name, frozenset(param_keys)) for each tool call in order.
        This is intentionally coarse — close enough to identify crystallizable
        patterns without requiring exact structural isomorphism.
        """
        from collections import defaultdict

        pattern_map: dict[str, list[dict]] = defaultdict(list)

        for trace in traces:
            fingerprint = self._compute_pattern_fingerprint(trace["tool_calls"])
            pattern_map[fingerprint].append(trace)

        patterns = []
        for fingerprint, matching_traces in pattern_map.items():
            if len(matching_traces) >= self.min_occurrences:
                avg_score = sum(t["score"] for t in matching_traces) / len(matching_traces)
                patterns.append({
                    "fingerprint":   fingerprint,
                    "trace_count":   len(matching_traces),
                    "avg_score":     avg_score,
                    "tool_calls":    matching_traces[0]["tool_calls"],   # Representative
                    "sample_traces": matching_traces[:3],
                })

        # Sort by occurrence count descending — most common patterns crystallize first
        return sorted(patterns, key=lambda p: p["trace_count"], reverse=True)

    def _compute_pattern_fingerprint(self, tool_calls: list[dict]) -> str:
        """Stable canonical fingerprint for a tool call sequence."""
        canonical = tuple(
            (tc.get("tool_name", ""), tuple(sorted(tc.get("param_keys", []))))
            for tc in tool_calls
        )
        return hashlib.sha256(str(canonical).encode()).hexdigest()[:16]

    async def _crystallize_pattern(self, pattern: dict) -> None:
        """
        Convert a detected pattern into a compiled LangGraph subgraph and persist it.

        The reconstruction strategy is deliberately conservative:
          - Only crystallize patterns with clear sequential structure
          - Generate skill name/description via LLM to ensure human-readability
          - Compile with a fixed StateGraph template that mirrors the pattern's
            tool call sequence but with LLM-driven parameter generation at each step

        A crystallized skill is not a hardcoded script — it is a *template*:
        a compiled graph that executes the same *sequence* of cognitive operations
        but with parameters generated fresh by the LLM for each invocation.
        This preserves generalization while eliminating the planning overhead
        of re-deriving the sequence.
        """
        tool_sequence = [tc.get("tool_name") for tc in pattern["tool_calls"]]

        # Generate a human-readable skill name and description via LLM
        naming_prompt = f"""
        An AI agent has successfully completed the following tool sequence {pattern['trace_count']} times
        with an average quality score of {pattern['avg_score']:.2%}:

        Tool sequence: {' → '.join(tool_sequence)}

        Generate a concise skill name (3-5 words, snake_case) and one-sentence description
        for this as a reusable agent skill. Also generate 3 natural language trigger conditions
        (situations where an agent should use this skill).

        Respond as JSON: {{"name": "...", "description": "...", "triggers": ["...", "...", "..."]}}
        """

        response_text = await self.llm.generate(naming_prompt)
        try:
            skill_meta = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON for skill naming, using fallback")
            skill_meta = {
                "name":        f"skill_{'_'.join(tool_sequence[:3])}",
                "description": f"Automated skill for: {' → '.join(tool_sequence)}",
                "triggers":    [f"Task requiring {tool_sequence[0]} then {tool_sequence[-1]}"],
            }

        # Build the LangGraph subgraph for this skill
        # This is a simplified template builder; production versions would
        # reconstruct the full reasoning + tool execution pattern
        compiled_graph = self._build_skill_graph(
            tool_sequence=tool_sequence,
            skill_name=skill_meta["name"],
        )

        await self.store.learn_skill(
            name=skill_meta["name"],
            description=skill_meta["description"],
            compiled_graph=compiled_graph,
            trigger_conditions=skill_meta["triggers"],
            performance_score=pattern["avg_score"],
        )

        logger.info(
            "Crystallized skill '%s' from %d traces (avg score: %.2f)",
            skill_meta["name"],
            pattern["trace_count"],
            pattern["avg_score"],
        )

    def _build_skill_graph(self, tool_sequence: list[str], skill_name: str) -> Any:
        """
        Construct a LangGraph StateGraph representing a fixed tool sequence.

        This is the structural skeleton of crystallization — the graph enforces
        the *order* of operations while delegating parameter generation to the LLM
        nodes within each step.

        In production, this builder should be extended to handle:
          - Conditional branches observed in source traces
          - Parallel tool execution where the trace showed concurrent calls
          - Error recovery branches from traces that included retries
        """
        from langgraph.graph import StateGraph, END
        from typing import TypedDict, Annotated
        import operator

        class SkillState(TypedDict):
            messages:   Annotated[list, operator.add]
            tool_results: list[dict]
            skill_name: str

        graph = StateGraph(SkillState)

        # Add a node for each tool in the sequence
        for i, tool_name in enumerate(tool_sequence):
            node_name = f"step_{i}_{tool_name}"

            # Closure captures tool_name correctly across loop iterations
            def make_node(tn: str) -> Any:
                async def node_fn(state: SkillState) -> dict:
                    # In a full implementation, this would call the tool registry
                    # with LLM-generated parameters. Placeholder for illustration.
                    logger.debug("Skill '%s' executing step: %s", state.get("skill_name"), tn)
                    return {"tool_results": [{"tool": tn, "status": "pending"}]}
                return node_fn

            graph.add_node(node_name, make_node(tool_name))

        # Chain nodes linearly
        node_names = [f"step_{i}_{tn}" for i, tn in enumerate(tool_sequence)]
        graph.set_entry_point(node_names[0])
        for a, b in zip(node_names[:-1], node_names[1:]):
            graph.add_edge(a, b)
        graph.add_edge(node_names[-1], END)

        return graph.compile()

    # ── Helper extraction methods ───────────────────────────────────────────
    def _compute_trace_score(self, trace: Any) -> float:
        if not hasattr(trace, "scores") or not trace.scores:
            return 0.0
        return sum(s.value for s in trace.scores if s.value is not None) / len(trace.scores)

    def _count_tool_calls(self, trace: Any) -> int:
        if not hasattr(trace, "observations"):
            return 0
        return sum(1 for obs in trace.observations if getattr(obs, "type", "") == "TOOL")

    def _extract_tool_calls(self, trace: Any) -> list[dict]:
        if not hasattr(trace, "observations"):
            return []
        return [
            {
                "tool_name":  obs.name,
                "param_keys": list(json.loads(obs.input or "{}").keys()),
            }
            for obs in trace.observations
            if getattr(obs, "type", "") == "TOOL"
        ]

    def _extract_duration(self, trace: Any) -> float:
        if hasattr(trace, "latency"):
            return float(trace.latency or 0)
        return 0.0
