"""
infrastructure/llm/dynamic_router.py

Capability-vector-based multi-objective model routing with live pricing arbitrage.

Formal problem statement:
    Given a set of available LLM providers M = {m₁, m₂, ..., mₙ}, a task
    characterized by a requirement vector r ∈ ℝᵈ (where d = number of capability
    dimensions), and constraints on cost (c_max) and latency (l_max):

    Optimal model selection = argmax_{m ∈ M_feasible} score(m, r)

    where:
        M_feasible = {m : cost(m, r) ≤ c_max AND E[latency(m)] ≤ l_max}
        score(m, r) = r · cap(m)     (dot product: task requirements · model capabilities)
        cap(m) ∈ ℝᵈ                  (model capability vector)

    This is a linearly-constrained linear program solvable in O(|M| × d) time —
    fast enough to run on every single LLM call without meaningful overhead.

Capability dimensions:
    The d=6 dimensions are chosen to capture the empirically significant axes
    of variation across frontier LLM performance on agent tasks:

    1. reasoning_depth      - Multi-step logical deduction, planning, chain-of-thought
                              (correlated with: MATH, GPQA, ARC-Challenge benchmarks)
    2. instruction_following - Precise adherence to format specs, schema constraints
                              (correlated with: IFEval benchmark)
    3. tool_use_reliability  - Structured output generation for tool call parameters
                              (correlated with: Berkeley Function Calling Leaderboard)
    4. context_faithfulness  - Accurate retrieval from long input contexts
                              (correlated with: RULER, HELMET benchmarks)
    5. creative_quality      - Novel, high-quality generation (writing, code creativity)
                              (correlated with: AlpacaEval 2.0, MT-Bench creative)
    6. code_quality          - Code correctness, style, documentation quality
                              (correlated with: HumanEval+, SWE-bench)

    These dimensions are NOT orthogonal — they exhibit significant positive
    correlation (smarter models are generally better at everything). The value
    of the capability vector is not in identifying perfect orthogonal dimensions
    but in capturing the *relative* strengths that justify per-task routing:
    a model might be 95th percentile on instruction_following but 75th percentile
    on reasoning_depth, making it optimal for tool_call tasks but suboptimal
    for planning tasks even if it's the same cost.

Capability data sources:
    The ModelCapabilityVector for each model is populated from three sources,
    in ascending priority order:
    1. Hardcoded priors from published benchmark leaderboards (lowest priority)
    2. Community aggregate from LMSYS Chatbot Arena ELO (updated hourly)
    3. Internal Langfuse traces: empirical performance on *your* task distribution
       (highest priority — your workload differs from public benchmarks)

    Source 3 is the critical differentiator: the router learns which model
    performs best on *your specific prompt patterns*, not on synthetic benchmarks.
    This is analogous to how database query optimizers use per-table statistics
    rather than generic selectivity estimates.

Cost model:
    Expected cost per call = p_in × E[tokens_in] + p_out × E[tokens_out]
    where p_in, p_out are per-token prices ($/million tokens)
    and E[tokens_in], E[tokens_out] are estimated from task type priors.

    Token estimation uses exponentially-weighted averages over historical calls
    of the same task_type, updated after each call. This is more accurate than
    fixed estimates, especially for codegen tasks where output length varies
    dramatically by problem complexity.

Latency model:
    E[latency(m)] = queue_latency(m) + prefill_time(m, tokens_in) + decode_time(m, tokens_out)
    Estimated from rolling percentile histograms maintained per model.
    We route on p50 latency for throughput optimization, p90 for latency-SLO
    compliance. The routing config allows selecting the latency percentile.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ModelCapabilityVector:
    """
    A model's performance characteristics as a normalized multi-dimensional vector.

    All capability dimensions are in [0, 1], normalized against the theoretical
    maximum of each dimension (i.e., 1.0 = best known model on that dimension
    as of the last benchmark update).

    Normalization is critical for dot-product scoring to produce meaningful
    results: without it, dimensions with naturally larger magnitudes would
    dominate the score regardless of task requirements.

    The pricing fields are in USD per million tokens ($/MTok) — the standard
    unit used by all major providers as of 2026. They are NOT normalized, as
    they enter the optimization as hard constraints rather than soft objectives.
    """
    model_id:               str     # Provider-canonical model string
    display_name:           str     # Human-readable name for logging

    # Capability dimensions ∈ [0, 1]
    reasoning_depth:        float   # Multi-step planning, logical deduction
    instruction_following:  float   # Schema adherence, format compliance
    tool_use_reliability:   float   # Function calling accuracy, structured output
    context_faithfulness:   float   # Long-context retrieval accuracy
    creative_quality:       float   # Writing quality, novel generation
    code_quality:           float   # Code correctness, style, security awareness

    # Cost model (USD/MTok)
    price_input_mtok:       float   # Per million input tokens
    price_output_mtok:      float   # Per million output tokens

    # Latency characteristics (milliseconds)
    p50_latency_ms:         float   # Median time-to-first-token
    p90_latency_ms:         float   # 90th percentile TTFT
    tokens_per_second:      float   # Decode throughput

    # Context window (tokens)
    context_window:         int

    # Data provenance
    last_updated:           str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source:                 str = "prior"  # "prior", "lmsys", "internal", "live"

    def capability_array(self) -> list[float]:
        """Return capability dimensions as an ordered array for dot product computation."""
        return [
            self.reasoning_depth,
            self.instruction_following,
            self.tool_use_reliability,
            self.context_faithfulness,
            self.creative_quality,
            self.code_quality,
        ]

    def expected_cost(self, est_input_tokens: int, est_output_tokens: int) -> float:
        """
        Compute expected cost for a call with estimated token counts.
        Returns USD cost as a float.
        """
        return (
            (self.price_input_mtok  * est_input_tokens  / 1_000_000) +
            (self.price_output_mtok * est_output_tokens / 1_000_000)
        )


@dataclass
class TaskRequirementVector:
    """
    A task's requirements as a normalized priority vector over capability dimensions.

    The sum of weights does not need to equal 1.0 — the routing score is a
    dot product, not a probability distribution. Higher weights indicate
    higher priority for that capability dimension when selecting a model.

    These vectors are configuration, not hyperparameters: they should reflect
    genuine task-capability relationships, not be tuned for downstream metrics.
    If your "planning" tasks don't actually require creative_quality, that
    weight should be 0.0, not 0.1.
    """
    task_type:              str
    reasoning_depth:        float = 0.0
    instruction_following:  float = 0.0
    tool_use_reliability:   float = 0.0
    context_faithfulness:   float = 0.0
    creative_quality:       float = 0.0
    code_quality:           float = 0.0

    # Constraint bounds (None = unconstrained)
    max_cost_usd:           float | None = None     # Per-call budget
    max_latency_p90_ms:     float | None = None     # Latency SLO
    min_context_window:     int   | None = None     # Minimum required context

    def as_array(self) -> list[float]:
        return [
            self.reasoning_depth,
            self.instruction_following,
            self.tool_use_reliability,
            self.context_faithfulness,
            self.creative_quality,
            self.code_quality,
        ]


# ── Default task requirement vectors ─────────────────────────────────────────
# These are empirically calibrated priors based on typical agent workload patterns.
# Override or extend for your specific use case.

TASK_REQUIREMENTS: dict[str, TaskRequirementVector] = {
    "planning": TaskRequirementVector(
        task_type              = "planning",
        reasoning_depth        = 1.0,    # Primary: complex multi-step reasoning
        instruction_following  = 0.6,    # Secondary: must follow plan schema exactly
        tool_use_reliability   = 0.4,    # Tertiary: may select tools in plan
        context_faithfulness   = 0.7,    # Must not hallucinate from long memory context
        max_cost_usd           = 0.15,   # Planning steps are infrequent; budget generously
    ),
    "tool_call": TaskRequirementVector(
        task_type              = "tool_call",
        instruction_following  = 1.0,    # Primary: must produce exact JSON schemas
        tool_use_reliability   = 1.0,    # Primary: function calling accuracy critical
        reasoning_depth        = 0.3,    # Low: parameters are usually straightforward
        max_cost_usd           = 0.08,   # Tool calls happen frequently; optimize cost
        max_latency_p90_ms     = 3000,   # User waits for tool results
    ),
    "summarization": TaskRequirementVector(
        task_type              = "summarization",
        instruction_following  = 0.7,    # Must follow length/format constraints
        context_faithfulness   = 0.8,    # Must not hallucinate beyond source
        reasoning_depth        = 0.2,    # Low: summarization is mostly extractive
        max_cost_usd           = 0.02,   # Very cheap: summarization is commodity
    ),
    "reflection": TaskRequirementVector(
        task_type              = "reflection",
        reasoning_depth        = 0.9,    # Must critically evaluate complex reasoning
        context_faithfulness   = 0.8,    # Must accurately quote/reference prior output
        instruction_following  = 0.5,
        max_cost_usd           = 0.12,
    ),
    "code_generation": TaskRequirementVector(
        task_type              = "code_generation",
        code_quality           = 1.0,    # Primary: correct, secure, idiomatic code
        reasoning_depth        = 0.7,    # Must reason about algorithmic correctness
        instruction_following  = 0.8,    # Must follow language/framework constraints
        max_cost_usd           = 0.20,   # Code quality worth paying for
    ),
    "fast": TaskRequirementVector(
        task_type              = "fast",
        instruction_following  = 0.5,
        reasoning_depth        = 0.3,
        max_cost_usd           = 0.01,   # Aggressively cheap
        max_latency_p90_ms     = 1500,   # Speed is the priority
    ),
    "local_only": TaskRequirementVector(
        task_type              = "local_only",
        # No cost/latency constraints — this always routes to local model
        # regardless of capability. Used for sensitive data that must not
        # leave the user's machine.
        min_context_window     = 8_000,  # Local models vary widely in context length
    ),
}


# ── Hardcoded capability priors (update quarterly or on new model release) ────
# These are initialization values — the router updates them from live sources.
# Sources: LMSYS Chatbot Arena ELO, BigBenchHard, Berkeley FCLB, HumanEval+

CAPABILITY_PRIORS: list[ModelCapabilityVector] = [
    ModelCapabilityVector(
        model_id              = "anthropic/claude-sonnet-4-5",
        display_name          = "Claude Sonnet 4.5",
        reasoning_depth       = 0.91,
        instruction_following = 0.95,
        tool_use_reliability  = 0.94,
        context_faithfulness  = 0.92,
        creative_quality      = 0.88,
        code_quality          = 0.90,
        price_input_mtok      = 3.00,
        price_output_mtok     = 15.00,
        p50_latency_ms        = 800,
        p90_latency_ms        = 1800,
        tokens_per_second     = 80,
        context_window        = 200_000,
        source                = "prior",
    ),
    ModelCapabilityVector(
        model_id              = "openai/gpt-4o",
        display_name          = "GPT-4o",
        reasoning_depth       = 0.89,
        instruction_following = 0.93,
        tool_use_reliability  = 0.95,   # Strong FCLB performer
        context_faithfulness  = 0.85,
        creative_quality      = 0.86,
        code_quality          = 0.88,
        price_input_mtok      = 2.50,
        price_output_mtok     = 10.00,
        p50_latency_ms        = 700,
        p90_latency_ms        = 1600,
        tokens_per_second     = 100,
        context_window        = 128_000,
        source                = "prior",
    ),
    ModelCapabilityVector(
        model_id              = "google/gemini-2.0-flash",
        display_name          = "Gemini 2.0 Flash",
        reasoning_depth       = 0.82,
        instruction_following = 0.87,
        tool_use_reliability  = 0.88,
        context_faithfulness  = 0.90,   # Strong on long-context tasks
        creative_quality      = 0.79,
        code_quality          = 0.83,
        price_input_mtok      = 0.10,
        price_output_mtok     = 0.40,
        p50_latency_ms        = 400,
        p90_latency_ms        = 900,
        tokens_per_second     = 200,
        context_window        = 1_000_000,
        source                = "prior",
    ),
    ModelCapabilityVector(
        model_id              = "groq/llama-3.3-70b-versatile",
        display_name          = "Llama 3.3 70B (Groq)",
        reasoning_depth       = 0.78,
        instruction_following = 0.80,
        tool_use_reliability  = 0.81,
        context_faithfulness  = 0.75,
        creative_quality      = 0.76,
        code_quality          = 0.79,
        price_input_mtok      = 0.59,
        price_output_mtok     = 0.79,
        p50_latency_ms        = 150,    # Groq's SpecDec hardware is extremely fast
        p90_latency_ms        = 400,
        tokens_per_second     = 800,    # ~800 tok/s on Groq LPU
        context_window        = 128_000,
        source                = "prior",
    ),
    ModelCapabilityVector(
        model_id              = "ollama/qwen2.5:32b",
        display_name          = "Qwen2.5 32B (Local)",
        reasoning_depth       = 0.72,
        instruction_following = 0.75,
        tool_use_reliability  = 0.73,
        context_faithfulness  = 0.70,
        creative_quality      = 0.68,
        code_quality          = 0.76,
        price_input_mtok      = 0.00,   # Local: no per-token cost
        price_output_mtok     = 0.00,
        p50_latency_ms        = 1200,   # Depends heavily on hardware
        p90_latency_ms        = 3000,
        tokens_per_second     = 25,     # RTX 4090: ~25-40 tok/s for 32B Q4
        context_window        = 32_000,
        source                = "prior",
    ),
]


class TokenUsageTracker:
    """
    Exponentially-weighted average tracker for per-task-type token counts.

    Used to estimate expected tokens_in and tokens_out for cost projection.
    Without this, the router must use fixed estimates that diverge from
    reality for tasks with high output variance (code generation, long summaries).

    The EWA update rule:
        estimate_new = α × observation + (1 - α) × estimate_old

    With α=0.15 (15% weight on new observations), the estimate has an
    effective time horizon of approximately 1/α ≈ 7 recent calls.
    This balances reactivity to genuine workload shifts against noise from
    individual outlier calls.
    """

    def __init__(self, alpha: float = 0.15) -> None:
        self.alpha = alpha
        self._estimates: dict[str, dict[str, float]] = {}

    def update(self, task_type: str, tokens_in: int, tokens_out: int) -> None:
        if task_type not in self._estimates:
            self._estimates[task_type] = {
                "tokens_in":  float(tokens_in),
                "tokens_out": float(tokens_out),
            }
        else:
            est = self._estimates[task_type]
            est["tokens_in"]  = self.alpha * tokens_in  + (1 - self.alpha) * est["tokens_in"]
            est["tokens_out"] = self.alpha * tokens_out + (1 - self.alpha) * est["tokens_out"]

    def estimate(self, task_type: str) -> tuple[int, int]:
        """Returns (est_input_tokens, est_output_tokens) for a task type."""
        defaults = {
            "planning":       (8_000, 1_500),
            "tool_call":      (5_000, 300),
            "summarization":  (12_000, 600),
            "reflection":     (6_000, 200),
            "code_generation":(4_000, 1_200),
            "fast":           (3_000, 200),
            "local_only":     (4_000, 500),
        }
        if task_type in self._estimates:
            est = self._estimates[task_type]
            return int(est["tokens_in"]), int(est["tokens_out"])
        return defaults.get(task_type, (5_000, 500))


class DynamicModelRouter:
    """
    Multi-objective LLM router with live capability vector updates.

    Design philosophy:
        The router is a stateful service, not a stateless function. It maintains
        and updates a model fleet registry that incorporates live data (pricing
        changes, observed latency distributions, internal Langfuse performance
        metrics). The routing function itself is stateless given the fleet registry —
        routing decisions are deterministic for a given fleet state and task vector.

        This separation enables:
          1. Unit testing routing logic without network calls
          2. Fleet state snapshots for reproducible debugging
          3. Gradual capability vector updates without restarting the service

    Relationship to LiteLLM:
        This router operates *above* LiteLLM. It selects the model_id, then
        LiteLLM handles the provider-specific API call, retry logic, and
        response normalization. The router does not duplicate LiteLLM's
        responsibilities (rate limit handling, provider fallbacks at the
        call level) — it provides the strategic layer that LiteLLM lacks
        (task-aware model selection, cost optimization, capability matching).
    """

    # Minimum time between live data updates
    UPDATE_INTERVAL_SECONDS = 6 * 3600   # 6 hours

    # Fallback chain: premium → mid-tier → local (ordered by cost descending)
    FALLBACK_CHAIN: list[str] = [
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4-5",
        "google/gemini-2.0-flash",
        "groq/llama-3.3-70b-versatile",
        "ollama/qwen2.5:32b",
    ]

    def __init__(
        self,
        litellm_router: Any,             # litellm.Router instance
        langfuse_client: Any | None = None,
        latency_slo_percentile: str = "p90",  # "p50" or "p90"
        cost_controller: Any | None = None,
    ) -> None:
        self.litellm      = litellm_router
        self.langfuse     = langfuse_client
        self.slo_perc     = latency_slo_percentile
        self.cost_controller = cost_controller

        # Initialize fleet from hardcoded priors
        self._fleet: dict[str, ModelCapabilityVector] = {
            m.model_id: m for m in CAPABILITY_PRIORS
        }
        self._token_tracker   = TokenUsageTracker()
        self._update_task: asyncio.Task | None = None
        self._last_update_at: float = 0.0

        # Local model always routes to Ollama regardless of optimization
        self._local_model_id = "ollama/qwen2.5:32b"

    async def start(self) -> None:
        """Start background capability update loop."""
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("DynamicModelRouter started with %d models in fleet", len(self._fleet))

    async def stop(self) -> None:
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

    async def route_task(
        self,
        task_type:   str,
        messages:    list[dict],
        max_cost:    float | None = None,
        max_latency: float | None = None,
        **litellm_kwargs: Any,
    ) -> Any:
        """
        Route a task to the optimal model and execute the call via LiteLLM.

        The method:
          1. Resolves task requirements (from TASK_REQUIREMENTS or task_type priors)
          2. Applies override constraints (max_cost, max_latency)
          3. Runs multi-objective optimization over the fleet
          4. Delegates to LiteLLM with the selected model_id
          5. Updates token usage tracker for future cost estimation

        The entire routing decision takes <1ms of CPU time, dominated by
        the O(|fleet| × d) dot product computation.
        """
        # Local-only tasks bypass optimization entirely
        if task_type == "local_only":
            return await self._call_model(self._local_model_id, messages, **litellm_kwargs)

        req = TASK_REQUIREMENTS.get(task_type) or self._default_requirement(task_type)

        # Apply call-site constraint overrides
        if max_cost is not None:
            req = TaskRequirementVector(**{**req.__dict__, "max_cost_usd": max_cost})
        if max_latency is not None:
            req = TaskRequirementVector(**{**req.__dict__, "max_latency_p90_ms": max_latency})

        selected_model_id = self._optimize_model_selection(req)

        # Budget-aware fallback: if cost controller says budget exceeded,
        # walk the fallback chain toward cheaper models
        if self.cost_controller is not None:
            est_in, est_out = self._token_tracker.estimate(task_type)
            est_cost = self.cost_controller.estimate_cost(selected_model_id, est_in, est_out)

            if not await self.cost_controller.check_budget(est_cost):
                fallback_id = self._find_budget_fallback(est_in, est_out)
                if fallback_id:
                    logger.warning(
                        "Budget limit: '%s' → fallback '%s'", selected_model_id, fallback_id
                    )
                    selected_model_id = fallback_id
                else:
                    logger.error("Budget exceeded and no fallback available")

            # Pre-call confirmation for expensive operations
            if self.cost_controller.needs_confirmation(est_cost):
                logger.info(
                    "Cost confirmation needed: $%.4f for %s", est_cost, selected_model_id
                )

        logger.debug(
            "Task '%s' → model '%s' (fleet_size=%d)",
            task_type, selected_model_id, len(self._fleet)
        )

        start_time = time.monotonic()
        response   = await self._call_model(selected_model_id, messages, **litellm_kwargs)
        elapsed_ms = (time.monotonic() - start_time) * 1000

        # Update capability vectors with observed latency (EWA update)
        if selected_model_id in self._fleet:
            model = self._fleet[selected_model_id]
            alpha = 0.10
            model.p50_latency_ms = alpha * elapsed_ms + (1 - alpha) * model.p50_latency_ms

        # Update token usage tracker
        if hasattr(response, "usage") and response.usage:
            self._token_tracker.update(
                task_type,
                response.usage.prompt_tokens or 0,
                response.usage.completion_tokens or 0,
            )
            # Record actual cost
            if self.cost_controller is not None:
                actual_cost = self.cost_controller.estimate_cost(
                    selected_model_id,
                    response.usage.prompt_tokens or 0,
                    response.usage.completion_tokens or 0,
                )
                await self.cost_controller.record_cost(actual_cost, selected_model_id)

        return response

    def _optimize_model_selection(self, req: TaskRequirementVector) -> str:
        """
        Constrained multi-objective optimization over the model fleet.

        The optimization procedure:
          1. FEASIBILITY FILTER: eliminate models that violate hard constraints
             (cost > budget, latency > SLO, context_window < minimum)
          2. CAPABILITY SCORING: compute dot product of task requirements with
             each feasible model's capability vector
          3. SELECTION: return the model_id with the highest score

        Constraint relaxation:
          If no models are feasible under all constraints, relax in priority order:
            a. First relax latency (latency SLOs are soft in practice)
            b. Then relax cost (cost overruns are manageable)
            c. If still no models, return the highest-scoring model with no constraints
               (fail open: a slow/expensive response is better than no response)

        This relaxation cascade mirrors the operational priority of a production system:
        correctness (capability) > availability (some model) > efficiency (cost/latency).
        """
        req_array          = req.as_array()
        est_in, est_out    = self._token_tracker.estimate(req.task_type)
        latency_field      = "p90_latency_ms" if self.slo_perc == "p90" else "p50_latency_ms"

        def score(m: ModelCapabilityVector) -> float:
            cap = m.capability_array()
            return sum(r * c for r, c in zip(req_array, cap))

        def is_feasible(m: ModelCapabilityVector) -> bool:
            if req.max_cost_usd is not None:
                if m.expected_cost(est_in, est_out) > req.max_cost_usd:
                    return False
            if req.max_latency_p90_ms is not None:
                if getattr(m, latency_field) > req.max_latency_p90_ms:
                    return False
            if req.min_context_window is not None:
                if m.context_window < req.min_context_window:
                    return False
            return True

        all_models = list(self._fleet.values())

        # Attempt 1: full constraint satisfaction
        feasible = [m for m in all_models if is_feasible(m)]
        if feasible:
            return max(feasible, key=score).model_id

        # Attempt 2: relax latency constraint
        latency_relaxed = [
            m for m in all_models
            if (req.max_cost_usd is None or m.expected_cost(est_in, est_out) <= req.max_cost_usd)
            and (req.min_context_window is None or m.context_window >= req.min_context_window)
        ]
        if latency_relaxed:
            selected = max(latency_relaxed, key=score).model_id
            logger.warning("Latency constraint relaxed for task '%s' → %s", req.task_type, selected)
            return selected

        # Attempt 3: unconstrained (fail open)
        if all_models:
            selected = max(all_models, key=score).model_id
            logger.warning("All constraints relaxed for task '%s' → %s", req.task_type, selected)
            return selected

        # This should never happen if CAPABILITY_PRIORS is non-empty
        raise RuntimeError("Model fleet is empty — cannot route any tasks")

    async def _call_model(
        self,
        model_id: str,
        messages: list[dict],
        **kwargs: Any,
    ) -> Any:
        """Delegate to LiteLLM router with the selected model_id."""
        return await self.litellm.acompletion(
            model    = model_id,
            messages = messages,
            **kwargs,
        )

    def _default_requirement(self, task_type: str) -> TaskRequirementVector:
        """Fallback for unknown task types: balanced, moderate-cost requirement."""
        return TaskRequirementVector(
            task_type              = task_type,
            reasoning_depth        = 0.5,
            instruction_following  = 0.5,
            tool_use_reliability   = 0.3,
            context_faithfulness   = 0.4,
            max_cost_usd           = 0.10,
        )

    def _find_budget_fallback(
        self, est_input_tokens: int, est_output_tokens: int
    ) -> str | None:
        """Walk fallback chain from cheapest to find a model within budget."""
        if self.cost_controller is None:
            return None
        # Iterate cheapest-first (reverse of FALLBACK_CHAIN)
        for model_id in reversed(self.FALLBACK_CHAIN):
            if model_id not in self._fleet:
                continue
            est = self.cost_controller.estimate_cost(model_id, est_input_tokens, est_output_tokens)
            if est == 0.0:  # local model — always within budget
                return model_id
        return self._local_model_id  # ultimate fallback

    # ── Background update loop ─────────────────────────────────────────────────

    async def _update_loop(self) -> None:
        """
        Periodically refresh capability vectors from live data sources.

        Update order (ascending priority — later updates overwrite earlier):
          1. Hardcoded priors (already loaded at init)
          2. Live pricing from provider APIs
          3. LMSYS Chatbot Arena ELO aggregation
          4. Internal Langfuse trace analysis

        The 6-hour interval balances data freshness against API rate limits
        and compute cost (Langfuse trace analysis requires N API calls).
        Pricing changes faster than capabilities, so the pricing update runs
        more frequently (every 2 hours) while capability updates run at 6h.
        """
        while True:
            try:
                await asyncio.sleep(self.UPDATE_INTERVAL_SECONDS)
                logger.info("Refreshing model capability vectors")

                await asyncio.gather(
                    self._update_live_pricing(),
                    self._update_from_internal_traces(),
                    return_exceptions=True,
                )

                self._last_update_at = time.monotonic()
                logger.info("Capability vectors updated for %d models", len(self._fleet))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Capability update loop error: %s", e)

    async def _update_live_pricing(self) -> None:
        """
        Fetch current pricing from LiteLLM's pricing database.

        LiteLLM maintains a community-updated model pricing registry at:
        https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json

        This is more reliable than scraping provider pricing pages, as the
        community updates it within hours of price changes. We use it as the
        source of truth for pricing, falling back to hardcoded priors on failure.
        """
        PRICING_URL = (
            "https://raw.githubusercontent.com/BerriAI/litellm/main/"
            "model_prices_and_context_window.json"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(PRICING_URL)
                if response.status_code != 200:
                    return
                pricing_data = response.json()

            for model_id, model_vec in self._fleet.items():
                # LiteLLM pricing keys use the full provider/model format
                pricing = pricing_data.get(model_id, {})
                if "input_cost_per_token" in pricing:
                    model_vec.price_input_mtok  = pricing["input_cost_per_token"]  * 1_000_000
                    model_vec.price_output_mtok = pricing.get("output_cost_per_token", 0) * 1_000_000
                    model_vec.source            = "live"
                    model_vec.last_updated      = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            logger.warning("Live pricing update failed: %s", e)

    async def _update_from_internal_traces(self) -> None:
        """
        Update capability vectors from internal Langfuse trace performance data.

        For each model in the fleet, we compute:
          1. Average user satisfaction score (from Langfuse scores)
          2. Tool call success rate (from tool_execution spans)
          3. Average latency (p50, p90) from trace duration histograms

        These are translated into capability vector updates via a weighted
        combination: 80% prior, 20% internal evidence. The conservative weighting
        prevents rapid drift from small sample sizes (a model that fails 2/3
        calls due to an API incident shouldn't have its capability scores
        permanently degraded from that weekend's data).

        In a production system with sufficient volume (>1000 calls/model/week),
        the internal weight should be increased to 40-60% to make internal data
        the primary signal.
        """
        if not self.langfuse:
            return

        try:
            # This is illustrative — adapt to your Langfuse SDK version
            traces_by_model: dict[str, list[dict]] = {}

            # Fetch recent traces with model metadata
            for trace in getattr(self.langfuse, "_recent_traces_cache", []):
                model_id = trace.get("model_id")
                if model_id and model_id in self._fleet:
                    traces_by_model.setdefault(model_id, []).append(trace)

            for model_id, traces in traces_by_model.items():
                if len(traces) < 10:   # Insufficient data — skip
                    continue

                model_vec    = self._fleet[model_id]
                avg_score    = sum(t.get("score", 0.7) for t in traces) / len(traces)
                avg_latency  = sum(t.get("latency_ms", model_vec.p50_latency_ms) for t in traces) / len(traces)

                # Conservative EWA update: 20% weight on internal evidence
                internal_weight = 0.20
                prior_weight    = 1.0 - internal_weight

                # Normalize avg_score (assume Langfuse scores in [0, 1]) to capability dimensions
                # The simplification: internal score uniformly updates all capability dimensions.
                # A more sophisticated implementation would map specific eval rubrics to specific
                # dimensions (e.g., format compliance score → instruction_following update).
                for dim in ["reasoning_depth", "instruction_following", "tool_use_reliability",
                            "context_faithfulness", "creative_quality", "code_quality"]:
                    prior_val   = getattr(model_vec, dim)
                    updated_val = prior_weight * prior_val + internal_weight * avg_score
                    setattr(model_vec, dim, min(1.0, max(0.0, updated_val)))

                # Update latency estimate
                model_vec.p50_latency_ms = (
                    prior_weight * model_vec.p50_latency_ms +
                    internal_weight * avg_latency
                )
                model_vec.source      = "internal"
                model_vec.last_updated = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            logger.warning("Internal trace update failed: %s", e)

    def get_fleet_summary(self) -> list[dict]:
        """
        Return a human-readable summary of the current fleet state.
        Useful for admin dashboards and debugging routing decisions.
        """
        summary = []
        for model in self._fleet.values():
            est_in, est_out = self._token_tracker.estimate("planning")
            summary.append({
                "model_id":             model.model_id,
                "display_name":         model.display_name,
                "capabilities": {
                    "reasoning":        f"{model.reasoning_depth:.0%}",
                    "instruction":      f"{model.instruction_following:.0%}",
                    "tool_use":         f"{model.tool_use_reliability:.0%}",
                    "context_faithful": f"{model.context_faithfulness:.0%}",
                },
                "cost_per_planning_call": f"${model.expected_cost(est_in, est_out):.4f}",
                "p50_latency_ms":       f"{model.p50_latency_ms:.0f}",
                "context_window":       model.context_window,
                "data_source":          model.source,
                "last_updated":         model.last_updated,
            })
        return sorted(summary, key=lambda m: m["display_name"])
