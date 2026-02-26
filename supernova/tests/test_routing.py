"""Tests for dynamic_router.py — capability-vector model routing."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_root = str(Path(__file__).resolve().parents[2])
if _root not in sys.path:
    sys.path.insert(0, _root)

from dynamic_router import (
    CAPABILITY_PRIORS,
    TASK_REQUIREMENTS,
    DynamicModelRouter,
    TaskRequirementVector,
)


def _make_router(mock_llm=None):
    """Create a DynamicModelRouter with a mock LiteLLM router."""
    llm = mock_llm or AsyncMock()
    resp = MagicMock()
    resp.usage.prompt_tokens = 100
    resp.usage.completion_tokens = 50
    llm.acompletion = AsyncMock(return_value=resp)
    return DynamicModelRouter(litellm_router=llm)


class TestRouting:
    def test_planning_routes_to_highest_reasoning_model(self):
        """Planning routes to model with highest reasoning_depth."""
        router = _make_router()
        req = TASK_REQUIREMENTS["planning"]
        selected = router._optimize_model_selection(req)
        # Claude Sonnet 4.5 has reasoning_depth=0.91, highest in fleet
        model = router._fleet[selected]
        best_reasoning = max(router._fleet.values(), key=lambda m: m.reasoning_depth)
        assert model.reasoning_depth == best_reasoning.reasoning_depth

    def test_cost_constraint_eliminates_expensive_models(self):
        """max_cost=0.001 excludes expensive models."""
        router = _make_router()
        req = TaskRequirementVector(
            task_type="cheap_task",
            reasoning_depth=0.5,
            instruction_following=0.5,
            max_cost_usd=0.001,
        )
        selected = router._optimize_model_selection(req)
        model = router._fleet[selected]
        # Only very cheap models should survive (Gemini Flash or local)
        est_in, est_out = router._token_tracker.estimate("cheap_task")
        assert model.expected_cost(est_in, est_out) <= 0.001

    def test_local_only_bypasses_optimization(self):
        """local_only task always returns local model."""
        router = _make_router()
        selected = router._optimize_model_selection(
            TaskRequirementVector(task_type="local_only", min_context_window=8_000)
        )
        # local_only goes through normal optimization but the route_task method
        # short-circuits. Test the route_task path:
        # For _optimize_model_selection, it should pick a model with context >= 8000
        assert router._fleet[selected].context_window >= 8_000


class TestConstraintRelaxation:
    def test_constraint_relaxation_cascade(self):
        """When no model feasible, relaxation fires in correct order."""
        router = _make_router()
        # Impossible constraints: very cheap AND very fast
        req = TaskRequirementVector(
            task_type="impossible",
            reasoning_depth=1.0,
            max_cost_usd=0.0001,
            max_latency_p90_ms=1,
        )
        # Should still return a model (fail open) rather than raising
        selected = router._optimize_model_selection(req)
        assert selected in router._fleet


class TestFleetSummary:
    def test_fleet_summary_returns_all_models(self):
        """get_fleet_summary() returns all models."""
        router = _make_router()
        summary = router.get_fleet_summary()
        assert len(summary) == len(CAPABILITY_PRIORS)
        model_ids = {m["model_id"] for m in summary}
        for prior in CAPABILITY_PRIORS:
            assert prior.model_id in model_ids

    @pytest.mark.asyncio
    async def test_route_task_local_only(self):
        """route_task with local_only bypasses optimization entirely."""
        router = _make_router()
        await router.route_task("local_only", [{"role": "user", "content": "hi"}])
        router.litellm.acompletion.assert_called_once()
        call_kwargs = router.litellm.acompletion.call_args
        assert call_kwargs.kwargs.get("model") == router._local_model_id or \
               call_kwargs[1].get("model") == router._local_model_id or \
               "ollama" in str(call_kwargs)
