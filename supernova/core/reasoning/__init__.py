"""Reasoning modules for SuperNova."""

from supernova.core.reasoning.context_assembly import (
    ContextBudget,
    ContextInputs,
    assemble_context_window,
    estimate_context_stats,
)
from supernova.infrastructure.llm.dynamic_router import DynamicModelRouter

__all__ = [
    "ContextBudget",
    "ContextInputs",
    "assemble_context_window",
    "estimate_context_stats",
    "DynamicModelRouter",
]


# New reasoning pipeline (Phase 20)
from supernova.core.reasoning.pipeline import ReasoningPipeline, ReasoningDepth
from supernova.core.reasoning.router import select_depth

__all__ += ["ReasoningPipeline", "ReasoningDepth", "select_depth"]
