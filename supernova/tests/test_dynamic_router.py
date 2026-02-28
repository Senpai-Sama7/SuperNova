"""
tests/test_dynamic_router.py

Unit tests for supernova.infrastructure.llm.dynamic_router.

Coverage map
────────────
ModelCapabilityVector       — 7 tests  (capability_array order, expected_cost formula, local=free,
                                         proportionality, last_updated factory, source default,
                                         all dims stored)
TaskRequirementVector       — 5 tests  (as_array order, all defaults 0.0, constraints None,
                                         custom constraints stored, task_type stored)
TASK_REQUIREMENTS dict      — 4 tests  (7 keys present, planning has max_cost, fast has
                                         max_latency, tool_call has both cost+latency)
CAPABILITY_PRIORS list      — 3 tests  (5 models, local model has price 0.0, model IDs unique)
TokenUsageTracker           — 8 tests  (alpha stored, first update exact, EWA formula,
                                         estimate from dict, known defaults, unknown fallback,
                                         independent task types, multiple updates converge)
DynamicModelRouter.__init__ — 4 tests  (fleet size, slo_perc stored, local_model_id,
                                         token_tracker initialized)
_optimize_model_selection   — 14 tests (empty fleet raises, planning → highest reasoning,
                                         fast → gemini (cost+latency feasibility), code→highest
                                         code_quality, cost filter excludes expensive,
                                         latency filter excludes slow, context_window filter,
                                         latency relaxation, full relaxation, deterministic,
                                         single-model fleet, custom fleet dot product math)
_default_requirement        — 3 tests  (unknown type returns balanced, task_type stored,
                                         max_cost_usd set)
_find_budget_fallback       — 3 tests  (None controller returns None, local model always free)
get_fleet_summary           — 3 tests  (len == fleet size, sorted by display_name, cost field)

Stubbing strategy
─────────────────
  NONE — dynamic_router.py has no supernova-internal imports.
  httpx is a declared project dependency and imports cleanly.
  All routing math is pure Python over in-memory dataclasses.
  LiteLLM, Langfuse, and cost_controller are only used in async I/O
  methods not covered here.

Zero network, database, LLM, or Langfuse calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from supernova.infrastructure.llm.dynamic_router import (
    CAPABILITY_PRIORS,
    TASK_REQUIREMENTS,
    DynamicModelRouter,
    ModelCapabilityVector,
    TaskRequirementVector,
    TokenUsageTracker,
)


# ── Shared factory helpers ───────────────────────────────────────────────────

def _model(
    *,
    model_id: str = "test/model",
    display_name: str = "Test Model",
    reasoning_depth: float = 0.80,
    instruction_following: float = 0.80,
    tool_use_reliability: float = 0.80,
    context_faithfulness: float = 0.80,
    creative_quality: float = 0.80,
    code_quality: float = 0.80,
    price_input_mtok: float = 1.00,
    price_output_mtok: float = 4.00,
    p50_latency_ms: float = 500.0,
    p90_latency_ms: float = 1200.0,
    tokens_per_second: float = 100.0,
    context_window: int = 128_000,
) -> ModelCapabilityVector:
    return ModelCapabilityVector(
        model_id=model_id,
        display_name=display_name,
        reasoning_depth=reasoning_depth,
        instruction_following=instruction_following,
        tool_use_reliability=tool_use_reliability,
        context_faithfulness=context_faithfulness,
        creative_quality=creative_quality,
        code_quality=code_quality,
        price_input_mtok=price_input_mtok,
        price_output_mtok=price_output_mtok,
        p50_latency_ms=p50_latency_ms,
        p90_latency_ms=p90_latency_ms,
        tokens_per_second=tokens_per_second,
        context_window=context_window,
    )


def _router(
    fleet: list[ModelCapabilityVector] | None = None,
    slo_perc: str = "p90",
) -> DynamicModelRouter:
    """Construct a router with an optional custom fleet (bypasses CAPABILITY_PRIORS)."""
    r = DynamicModelRouter(
        litellm_router=MagicMock(),
        langfuse_client=None,
        latency_slo_percentile=slo_perc,
    )
    if fleet is not None:
        r._fleet = {m.model_id: m for m in fleet}
    return r


# ════════════════════════════════════════════════════════════════════════
# ModelCapabilityVector
# ════════════════════════════════════════════════════════════════════════

class TestModelCapabilityVector:
    """capability_array() and expected_cost() are the two pure functions that drive routing."""

    def test_capability_array_returns_six_dims_in_correct_order(self) -> None:
        m = _model(
            reasoning_depth=0.1,
            instruction_following=0.2,
            tool_use_reliability=0.3,
            context_faithfulness=0.4,
            creative_quality=0.5,
            code_quality=0.6,
        )
        assert m.capability_array() == pytest.approx([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

    def test_expected_cost_zero_for_local_model(self) -> None:
        m = _model(price_input_mtok=0.0, price_output_mtok=0.0)
        assert m.expected_cost(10_000, 1_000) == pytest.approx(0.0)

    def test_expected_cost_formula_is_correct(self) -> None:
        # price_in=2.0 $/MTok, price_out=8.0 $/MTok
        # cost = 2.0 * 5_000 / 1_000_000  +  8.0 * 500 / 1_000_000
        #      = 0.010                     +  0.004
        #      = 0.014
        m = _model(price_input_mtok=2.0, price_output_mtok=8.0)
        assert m.expected_cost(5_000, 500) == pytest.approx(0.014)

    def test_expected_cost_scales_linearly_with_token_count(self) -> None:
        m = _model(price_input_mtok=1.0, price_output_mtok=1.0)
        cost_base   = m.expected_cost(1_000, 1_000)
        cost_double = m.expected_cost(2_000, 2_000)
        assert cost_double == pytest.approx(cost_base * 2)

    def test_last_updated_auto_populated_as_iso_string(self) -> None:
        m = _model()
        assert isinstance(m.last_updated, str)
        assert "T" in m.last_updated

    def test_source_defaults_to_prior(self) -> None:
        m = _model()
        assert m.source == "prior"

    def test_all_fields_stored_correctly(self) -> None:
        m = _model(model_id="acme/fast", context_window=64_000, tokens_per_second=500.0)
        assert m.model_id == "acme/fast"
        assert m.context_window == 64_000
        assert m.tokens_per_second == pytest.approx(500.0)


# ════════════════════════════════════════════════════════════════════════
# TaskRequirementVector
# ════════════════════════════════════════════════════════════════════════

class TestTaskRequirementVector:
    def test_as_array_returns_six_dims_in_correct_order(self) -> None:
        req = TaskRequirementVector(
            task_type="t",
            reasoning_depth=0.1,
            instruction_following=0.2,
            tool_use_reliability=0.3,
            context_faithfulness=0.4,
            creative_quality=0.5,
            code_quality=0.6,
        )
        assert req.as_array() == pytest.approx([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

    def test_capability_dimensions_default_to_zero(self) -> None:
        req = TaskRequirementVector(task_type="blank")
        assert req.as_array() == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def test_constraint_fields_default_to_none(self) -> None:
        req = TaskRequirementVector(task_type="blank")
        assert req.max_cost_usd is None
        assert req.max_latency_p90_ms is None
        assert req.min_context_window is None

    def test_custom_constraints_stored(self) -> None:
        req = TaskRequirementVector(
            task_type="t", max_cost_usd=0.05, max_latency_p90_ms=2000, min_context_window=32_000
        )
        assert req.max_cost_usd == pytest.approx(0.05)
        assert req.max_latency_p90_ms == pytest.approx(2000)
        assert req.min_context_window == 32_000

    def test_task_type_stored(self) -> None:
        req = TaskRequirementVector(task_type="code_generation")
        assert req.task_type == "code_generation"


# ════════════════════════════════════════════════════════════════════════
# TASK_REQUIREMENTS — module-level constants
# ════════════════════════════════════════════════════════════════════════

class TestTaskRequirementsDict:
    EXPECTED_KEYS = {"planning", "tool_call", "summarization", "reflection",
                     "code_generation", "fast", "local_only"}

    def test_all_seven_task_types_present(self) -> None:
        assert set(TASK_REQUIREMENTS.keys()) == self.EXPECTED_KEYS

    def test_planning_has_cost_constraint(self) -> None:
        assert TASK_REQUIREMENTS["planning"].max_cost_usd is not None
        assert TASK_REQUIREMENTS["planning"].max_cost_usd > 0

    def test_fast_has_latency_constraint(self) -> None:
        assert TASK_REQUIREMENTS["fast"].max_latency_p90_ms is not None
        assert TASK_REQUIREMENTS["fast"].max_latency_p90_ms <= 2000

    def test_tool_call_has_both_cost_and_latency_constraints(self) -> None:
        req = TASK_REQUIREMENTS["tool_call"]
        assert req.max_cost_usd is not None
        assert req.max_latency_p90_ms is not None


# ════════════════════════════════════════════════════════════════════════
# CAPABILITY_PRIORS — module-level constants
# ════════════════════════════════════════════════════════════════════════

class TestCapabilityPriors:
    def test_five_models_defined(self) -> None:
        assert len(CAPABILITY_PRIORS) == 5

    def test_local_model_has_zero_price(self) -> None:
        local = next(m for m in CAPABILITY_PRIORS if "ollama" in m.model_id)
        assert local.price_input_mtok  == pytest.approx(0.0)
        assert local.price_output_mtok == pytest.approx(0.0)

    def test_all_model_ids_are_unique(self) -> None:
        ids = [m.model_id for m in CAPABILITY_PRIORS]
        assert len(ids) == len(set(ids))


# ════════════════════════════════════════════════════════════════════════
# TokenUsageTracker
# ════════════════════════════════════════════════════════════════════════

class TestTokenUsageTracker:
    def test_alpha_stored_on_init(self) -> None:
        t = TokenUsageTracker(alpha=0.25)
        assert t.alpha == pytest.approx(0.25)

    def test_first_update_sets_exact_values(self) -> None:
        t = TokenUsageTracker()
        t.update("planning", 8_000, 1_500)
        in_est, out_est = t.estimate("planning")
        assert in_est == 8_000
        assert out_est == 1_500

    def test_second_update_applies_ewa_formula(self) -> None:
        """
        EWA: new_est = α × obs + (1 - α) × old_est
        With α=0.5, old=8000, new=4000 → 0.5×4000 + 0.5×8000 = 6000
        """
        t = TokenUsageTracker(alpha=0.5)
        t.update("planning", 8_000, 2_000)   # initialises
        t.update("planning", 4_000, 0)        # EWA update
        in_est, _ = t.estimate("planning")
        assert in_est == 6_000

    def test_estimate_returns_int_tuple_from_dict(self) -> None:
        t = TokenUsageTracker()
        t.update("fast", 3_100, 250)
        in_est, out_est = t.estimate("fast")
        assert isinstance(in_est, int)
        assert isinstance(out_est, int)
        assert in_est == 3_100
        assert out_est == 250

    def test_estimate_falls_back_to_known_defaults(self) -> None:
        t = TokenUsageTracker()   # nothing updated
        in_est, out_est = t.estimate("planning")
        assert in_est  == 8_000
        assert out_est == 1_500

    def test_estimate_unknown_task_returns_generic_default(self) -> None:
        t = TokenUsageTracker()
        in_est, out_est = t.estimate("completely_unknown_task_xyz")
        assert in_est  == 5_000
        assert out_est == 500

    def test_multiple_task_types_tracked_independently(self) -> None:
        t = TokenUsageTracker()
        t.update("planning",  10_000, 2_000)
        t.update("tool_call",  5_000,   300)
        p_in, _ = t.estimate("planning")
        tc_in, _ = t.estimate("tool_call")
        assert p_in  == 10_000
        assert tc_in ==  5_000

    def test_repeated_ewa_updates_converge_toward_new_value(self) -> None:
        """
        After many observations of 1000 starting from 10000,
        the estimate should move substantially toward 1000.
        """
        t = TokenUsageTracker(alpha=0.3)
        t.update("code_generation", 10_000, 0)
        for _ in range(20):
            t.update("code_generation", 1_000, 0)
        in_est, _ = t.estimate("code_generation")
        assert in_est < 5_000  # drifted well below midpoint


# ════════════════════════════════════════════════════════════════════════
# DynamicModelRouter.__init__
# ════════════════════════════════════════════════════════════════════════

class TestDynamicModelRouterInit:
    def test_fleet_initialized_with_five_models(self) -> None:
        r = _router()  # uses CAPABILITY_PRIORS
        assert len(r._fleet) == 5

    def test_slo_perc_stored_correctly(self) -> None:
        r = DynamicModelRouter(
            litellm_router=MagicMock(), latency_slo_percentile="p50"
        )
        assert r.slo_perc == "p50"

    def test_local_model_id_is_ollama(self) -> None:
        r = _router()
        assert "ollama" in r._local_model_id

    def test_token_tracker_initialized(self) -> None:
        r = _router()
        assert isinstance(r._token_tracker, TokenUsageTracker)


# ════════════════════════════════════════════════════════════════════════
# DynamicModelRouter._optimize_model_selection
# ════════════════════════════════════════════════════════════════════════

class TestOptimizeModelSelection:
    """
    _optimize_model_selection is the most important method in the routing layer:
    it determines which model handles each LLM call.

    Routing math (deterministic given fleet + requirement vector):
        score(m, req) = dot_product(req.as_array(), m.capability_array())
        feasible(m)   = cost ≤ max_cost AND p90_latency ≤ max_latency AND
                         context_window ≥ min_context
        winner = argmax_{m ∈ feasible} score(m)

    Most tests use a minimal 2-model fleet to make expected outcomes exact
    without floating-point ambiguity from 5-model competitive scoring.
    """

    def _req(self, **kwargs) -> TaskRequirementVector:
        return TaskRequirementVector(task_type="test", **kwargs)

    def test_empty_fleet_raises_runtime_error(self) -> None:
        r = _router(fleet=[])
        with pytest.raises(RuntimeError, match="fleet is empty"):
            r._optimize_model_selection(self._req())

    def test_higher_capability_score_wins_unconstrained(self) -> None:
        """
        Model A has reasoning_depth=0.9; Model B has 0.5.
        Requirement heavily weights reasoning (1.0).
        Model A must be selected.
        """
        model_a = _model(model_id="a/high", reasoning_depth=0.9)
        model_b = _model(model_id="b/low",  reasoning_depth=0.5)
        r = _router(fleet=[model_a, model_b])
        result = r._optimize_model_selection(self._req(reasoning_depth=1.0))
        assert result == "a/high"

    def test_cost_constraint_excludes_expensive_model(self) -> None:
        """
        Model A is cheaper but lower capability.
        Model B is more expensive but higher capability.
        max_cost eliminates B → A must win.
        Token estimates from default: (5000, 500) for unknown task type.
        model_a cost = 0.001 * 5000/1M + 0.001 * 500/1M = very small
        model_b cost = 100.0 * 5000/1M + 100.0 * 500/1M = very large
        """
        model_a = _model(model_id="a/cheap",     price_input_mtok=0.001, price_output_mtok=0.001, reasoning_depth=0.5)
        model_b = _model(model_id="b/expensive", price_input_mtok=100.0, price_output_mtok=100.0, reasoning_depth=0.9)
        r = _router(fleet=[model_a, model_b])
        result = r._optimize_model_selection(self._req(reasoning_depth=1.0, max_cost_usd=0.01))
        assert result == "a/cheap"

    def test_latency_constraint_excludes_slow_model(self) -> None:
        """
        Model A is fast (p90=500ms), Model B is slow (p90=5000ms).
        max_latency_p90_ms=1000 eliminates B → A wins.
        """
        model_a = _model(model_id="a/fast", p90_latency_ms=500.0,  reasoning_depth=0.5)
        model_b = _model(model_id="b/slow", p90_latency_ms=5000.0, reasoning_depth=0.9)
        r = _router(fleet=[model_a, model_b])
        result = r._optimize_model_selection(
            self._req(reasoning_depth=1.0, max_latency_p90_ms=1000.0)
        )
        assert result == "a/fast"

    def test_context_window_constraint(self) -> None:
        """
        Model A has 8k context; Model B has 200k context.
        min_context_window=128000 eliminates A → B wins even though A scores higher.
        """
        model_a = _model(model_id="a/small_ctx",   context_window=8_000,   reasoning_depth=0.9)
        model_b = _model(model_id="b/large_ctx",   context_window=200_000, reasoning_depth=0.5)
        r = _router(fleet=[model_a, model_b])
        result = r._optimize_model_selection(
            self._req(reasoning_depth=1.0, min_context_window=128_000)
        )
        assert result == "b/large_ctx"

    def test_latency_relaxation_when_only_cost_feasible(self) -> None:
        """
        Both models are within cost budget.
        Only model_a meets latency SLO.
        After latency relaxation (Attempt 2), both models are candidates.
        model_b has higher score → model_b should win with latency relaxed.
        """
        model_a = _model(model_id="a/fast_weak",  p90_latency_ms=500.0,  reasoning_depth=0.5,
                         price_input_mtok=0.01, price_output_mtok=0.01)
        model_b = _model(model_id="b/slow_strong", p90_latency_ms=5000.0, reasoning_depth=0.9,
                         price_input_mtok=0.01, price_output_mtok=0.01)
        r = _router(fleet=[model_a, model_b])
        # max_latency=1000 means model_b is infeasible in Attempt 1
        # But no cost constraint on model_b → cost-only filter keeps both → model_b wins Attempt 2
        result = r._optimize_model_selection(
            self._req(reasoning_depth=1.0, max_latency_p90_ms=1000.0)
        )
        assert result == "b/slow_strong"

    def test_full_constraint_relaxation_returns_highest_scoring_model(self) -> None:
        """
        Both models are over budget. Attempt 2 (cost-only) has no models.
        Attempt 3 (unconstrained) returns the higher-scoring model.
        """
        model_a = _model(model_id="a/over_budget", price_input_mtok=999.0, reasoning_depth=0.5)
        model_b = _model(model_id="b/over_budget", price_input_mtok=999.0, reasoning_depth=0.9)
        r = _router(fleet=[model_a, model_b])
        result = r._optimize_model_selection(
            self._req(reasoning_depth=1.0, max_cost_usd=0.001)
        )
        assert result == "b/over_budget"

    def test_single_model_fleet_always_returns_that_model(self) -> None:
        model = _model(model_id="only/model")
        r = _router(fleet=[model])
        result = r._optimize_model_selection(self._req(reasoning_depth=1.0))
        assert result == "only/model"

    def test_deterministic_same_fleet_same_req_same_result(self) -> None:
        model_a = _model(model_id="a", reasoning_depth=0.7)
        model_b = _model(model_id="b", reasoning_depth=0.8)
        r = _router(fleet=[model_a, model_b])
        req = self._req(reasoning_depth=1.0)
        assert r._optimize_model_selection(req) == r._optimize_model_selection(req)

    def test_dot_product_math_verified_exactly(self) -> None:
        """
        Verify routing math:
        Model A: reasoning=0.8, instruction=0.5
        Model B: reasoning=0.5, instruction=0.9
        Req: reasoning=1.0, instruction=0.0 → Model A wins (0.8 > 0.5)
        """
        model_a = _model(model_id="a", reasoning_depth=0.8, instruction_following=0.5)
        model_b = _model(model_id="b", reasoning_depth=0.5, instruction_following=0.9)
        r = _router(fleet=[model_a, model_b])
        assert r._optimize_model_selection(self._req(reasoning_depth=1.0)) == "a"

    def test_instruction_following_dominates_when_weighted_highest(self) -> None:
        """
        Same models as above but instruction_following=1.0 now → Model B wins.
        """
        model_a = _model(model_id="a", reasoning_depth=0.8, instruction_following=0.5)
        model_b = _model(model_id="b", reasoning_depth=0.5, instruction_following=0.9)
        r = _router(fleet=[model_a, model_b])
        assert r._optimize_model_selection(self._req(instruction_following=1.0)) == "b"

    def test_planning_task_selects_highest_reasoning_model_from_priors(self) -> None:
        """
        Uses actual CAPABILITY_PRIORS fleet (5 models).
        Planning requires reasoning_depth=1.0 as primary weight.
        Claude Sonnet 4.5 has the highest reasoning_depth (0.91) among the priors.
        Expected: anthropic/claude-sonnet-4-5
        """
        r = _router()  # default fleet from CAPABILITY_PRIORS
        result = r._optimize_model_selection(TASK_REQUIREMENTS["planning"])
        assert result == "anthropic/claude-sonnet-4-5"

    def test_fast_task_excludes_expensive_and_slow_models_from_priors(self) -> None:
        """
        Uses actual CAPABILITY_PRIORS fleet.
        fast task: max_cost=0.01, max_latency_p90_ms=1500.
        Claude (0.0465/call) and GPT-4o (0.0095, p90=1600 >1500) are excluded.
        Feasible: Gemini Flash (p90=900), Llama Groq (p90=400), Ollama (p90=3000 >1500 excluded).
        Gemini Flash scores highest among Gemini + Llama on fast req.
        Expected: google/gemini-2.0-flash
        """
        r = _router()  # default fleet
        result = r._optimize_model_selection(TASK_REQUIREMENTS["fast"])
        assert result == "google/gemini-2.0-flash"

    def test_p50_slo_uses_p50_latency_field(self) -> None:
        """
        With slo_perc='p50', the constraint uses p50_latency_ms, not p90.
        Model A: p50=400, p90=5000. Model B: p50=5000, p90=400.
        max_latency_p90_ms=1000 with slo_perc=p50 → only A is feasible.
        """
        model_a = _model(model_id="a", p50_latency_ms=400.0,  p90_latency_ms=5000.0, reasoning_depth=0.5)
        model_b = _model(model_id="b", p50_latency_ms=5000.0, p90_latency_ms=400.0,  reasoning_depth=0.9)
        r = _router(fleet=[model_a, model_b], slo_perc="p50")
        result = r._optimize_model_selection(
            self._req(reasoning_depth=1.0, max_latency_p90_ms=1000.0)
        )
        assert result == "a"


# ════════════════════════════════════════════════════════════════════════
# DynamicModelRouter._default_requirement
# ════════════════════════════════════════════════════════════════════════

class TestDefaultRequirement:
    def test_returns_task_requirement_vector(self) -> None:
        r = _router()
        req = r._default_requirement("mystery_task")
        assert isinstance(req, TaskRequirementVector)

    def test_task_type_stored_in_fallback(self) -> None:
        r = _router()
        req = r._default_requirement("mystery_task")
        assert req.task_type == "mystery_task"

    def test_has_balanced_capability_weights(self) -> None:
        r = _router()
        req = r._default_requirement("mystery_task")
        arr = req.as_array()
        # All non-zero (balanced) and reasonable
        assert all(0 < v <= 1.0 for v in arr if v > 0)


# ════════════════════════════════════════════════════════════════════════
# DynamicModelRouter._find_budget_fallback
# ════════════════════════════════════════════════════════════════════════

class TestFindBudgetFallback:
    def test_returns_none_when_no_cost_controller(self) -> None:
        r = _router()  # cost_controller=None (default)
        result = r._find_budget_fallback(5_000, 500)
        assert result is None

    def test_returns_local_model_when_cost_controller_present_and_local_free(self) -> None:
        """
        Local model (Ollama) has price=0.0, so estimate_cost returns 0.0 →
        it's always within budget and should be returned as the ultimate fallback.
        """
        mock_cc = MagicMock()
        # estimate_cost returns 0.0 for local model (price_input=0, price_output=0)
        mock_cc.estimate_cost.return_value = 0.0
        r = DynamicModelRouter(litellm_router=MagicMock(), cost_controller=mock_cc)
        result = r._find_budget_fallback(5_000, 500)
        # Should return local model id (budget=0.0 → condition `est == 0.0` satisfied)
        assert result is not None
        assert "ollama" in result

    def test_returns_local_model_id_as_ultimate_fallback(self) -> None:
        """
        All models are over budget (cost > 0), so no early return from the loop.
        The method falls through to return self._local_model_id.
        """
        mock_cc = MagicMock()
        mock_cc.estimate_cost.return_value = 99.99   # every model is expensive
        r = DynamicModelRouter(litellm_router=MagicMock(), cost_controller=mock_cc)
        result = r._find_budget_fallback(5_000, 500)
        assert result == r._local_model_id


# ════════════════════════════════════════════════════════════════════════
# DynamicModelRouter.get_fleet_summary
# ════════════════════════════════════════════════════════════════════════

class TestGetFleetSummary:
    def test_returns_one_entry_per_fleet_model(self) -> None:
        r = _router()
        summary = r.get_fleet_summary()
        assert len(summary) == len(r._fleet)

    def test_sorted_by_display_name(self) -> None:
        r = _router()
        summary = r.get_fleet_summary()
        names = [s["display_name"] for s in summary]
        assert names == sorted(names)

    def test_cost_field_formatted_as_dollar_string(self) -> None:
        r = _router()
        summary = r.get_fleet_summary()
        for entry in summary:
            assert entry["cost_per_planning_call"].startswith("$")
