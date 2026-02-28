"""
core/reasoning/context_assembly.py

Positionally-aware context window assembly for LLM agent cognition.

Theoretical foundation:
    Liu et al. (2023) "Lost in the Middle: How Language Models Use Long Contexts"
    established empirically that transformer attention exhibits a U-shaped bias
    over sequence position: primacy (token 0..~500) and recency (last ~2000 tokens)
    are attended to reliably; the middle of a long context degrades to ~40% recall
    for the central quartile.

    This is not a quirk of a particular model — it reflects the structural bias of
    causal attention: keys near the query (recency) have lower relative positional
    encoding distances; keys at the start benefit from being attended to by every
    subsequent token during training. The middle receives neither benefit.

    Architectural implication: context assembly is not concatenation. It is a
    *scheduling problem* over a finite, non-uniform attention bandwidth resource.

Strategy:
    PRIMACY ZONE  [0 : ~800 tokens]   → agent identity, active task, current plan
    MIDDLE ZONE   [800 : -2000 tokens] → background facts, supplementary knowledge
    RECENCY ZONE  [-2000 : end]        → episodic history, working memory, user message

    Irreplaceable, high-precision information goes to primacy + recency.
    Supplementary knowledge that enriches but whose partial loss is tolerable
    goes to the middle.

    The "assistant acknowledgment" trick: injecting background knowledge as an
    early user→assistant exchange pushes that content into the middle zone while
    keeping the system prompt slot clean for critical instructions. This exploits
    the fact that the model's own prior "statements" receive different positional
    treatment than raw context dumps.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ContextZone(Enum):
    """
    Positional priority zones mapped to transformer attention reliability.

    These are empirical designations, not architectural guarantees.
    The exact token boundaries shift with model architecture and context length,
    but the relative ordering (recency > primacy > middle) is consistent across
    decoder-only transformers trained with causal attention masks.
    """
    PRIMACY = auto()    # Highest recall: system-level instructions, active goal
    MIDDLE  = auto()    # Lowest recall: supplementary, tolerable-loss knowledge
    RECENCY = auto()    # Highest recall: current state, recent conversation


@dataclass
class ContextBudget:
    """
    Token budget allocator across zones.

    Why per-zone budgets matter: a naive "stuff everything until full" strategy
    tends to fill the middle with retrieved memories, leaving recency thin —
    precisely backwards from the optimal allocation.

    These defaults are calibrated for a 128k context model. Scale proportionally.
    For 200k+ models (Claude 3.7, Gemini 2.0 Ultra), the middle degradation curve
    flattens somewhat but does not disappear — primacy/recency bias persists.
    """
    total_tokens:      int = 100_000   # Reserve 28k for output
    primacy_tokens:    int = 3_000     # System + task + plan
    recency_tokens:    int = 20_000    # Working memory + conversation history
    middle_tokens:     int = 77_000    # Background knowledge — use conservatively

    def __post_init__(self) -> None:
        allocated = self.primacy_tokens + self.recency_tokens + self.middle_tokens
        if allocated > self.total_tokens:
            raise ValueError(
                f"Budget overcommitted: {allocated} > {self.total_tokens} tokens. "
                f"Reduce zone allocations."
            )


@dataclass
class ContextInputs:
    """
    All raw cognitive inputs for a single agent reasoning step.

    Separation of inputs from assembly logic enables:
    1. Independent unit testing of each memory retrieval subsystem
    2. Easy introspection/logging of exactly what fed into each LLM call
    3. Budget-aware truncation without coupling retrieval logic to assembly logic
    """
    # PRIMACY candidates
    agent_identity:     str               = ""   # Who the agent is, its values/rules
    active_task:        str               = ""   # What the agent is doing *right now*
    current_plan:       list[dict]        = field(default_factory=list)
    active_skills:      list[str]         = field(default_factory=list)   # Procedural memory hits

    # MIDDLE candidates
    semantic_memories:  list[dict]        = field(default_factory=list)   # Long-term facts
    tool_schemas:       list[dict]        = field(default_factory=list)   # Available tools

    # RECENCY candidates
    episodic_context:   list[dict]        = field(default_factory=list)   # Recent relevant episodes
    working_memory:     dict[str, Any]    = field(default_factory=dict)   # Current cognitive state
    conversation_history: list[dict]      = field(default_factory=list)   # Full message thread
    retrieved_memories: list[dict]        = field(default_factory=list)   # This-turn retrieval hits


def _format_plan(plan: list[dict]) -> str:
    """Render a structured plan as a readable, token-efficient string."""
    if not plan:
        return "No active plan. Operate reactively."
    lines = ["Current execution plan:"]
    for i, step in enumerate(plan, 1):
        status = step.get("status", "pending")
        marker = "✓" if status == "complete" else "→" if status == "active" else "○"
        lines.append(f"  {marker} Step {i}: {step.get('description', '')}")
        if step.get("result") and status == "complete":
            lines.append(f"      Result: {step['result'][:200]}")
    return "\n".join(lines)


def _format_semantic_memories(memories: list[dict], max_memories: int = 15) -> str:
    """
    Render semantic memories for middle-zone injection.

    Truncation strategy: prioritize by importance score, then recency.
    We truncate here rather than relying on the model to ignore excess —
    tokens in the middle zone cost both latency and attention bandwidth
    even when nominally "ignored."
    """
    if not memories:
        return ""

    ranked = sorted(
        memories,
        key=lambda m: (m.get("importance", 5), m.get("recency_score", 0)),
        reverse=True
    )[:max_memories]

    lines = ["[BACKGROUND KNOWLEDGE — factual context, may be partial]"]
    for mem in ranked:
        category = mem.get("category", "fact")
        content  = mem.get("content", "")
        conf     = mem.get("confidence", 1.0)
        conf_tag = f" [confidence: {conf:.0%}]" if conf < 0.9 else ""
        lines.append(f"  [{category}]{conf_tag} {content}")
    return "\n".join(lines)


def _format_working_memory(wm: dict) -> str:
    """Render current working memory state for recency-zone injection."""
    parts = []

    if goal := wm.get("current_goal"):
        parts.append(f"Active goal: {goal}")
    if scratchpad := wm.get("scratchpad"):
        parts.append(f"Scratchpad:\n{textwrap.indent(scratchpad, '  ')}")
    if attention := wm.get("attention_stack"):
        parts.append(f"Current focus: {' → '.join(attention)}")
    if tool_results := wm.get("tool_results_buffer"):
        results_str = "\n".join(
            f"  {r.get('tool')}: {str(r.get('result', ''))[:300]}"
            for r in tool_results[-5:]   # Last 5 results only
        )
        parts.append(f"Recent tool results:\n{results_str}")

    return "\n".join(parts) if parts else ""


def _format_episodic_context(episodes: list[dict], max_episodes: int = 6) -> str:
    """
    Render recent relevant episodes for recency-zone context.

    Selection: most relevant (by retrieval score), limited to avoid crowding
    the conversation history out of the recency zone.
    """
    if not episodes:
        return ""

    ranked = sorted(episodes, key=lambda e: e.get("score", 0), reverse=True)[:max_episodes]
    lines = ["[RELEVANT MEMORY — retrieved episodes]"]
    for ep in ranked:
        when = ep.get("valid_from", "")[:10]   # Date only, no time
        fact = ep.get("fact", ep.get("content", ""))
        lines.append(f"  [{when}] {fact}")
    return "\n".join(lines)


def assemble_context_window(
    inputs: ContextInputs,
    budget: ContextBudget | None = None,
    token_counter: Any | None = None,
) -> list[dict]:
    """
    Assemble the optimal context window for a single reasoning step.

    Returns a list of chat messages in OpenAI/Anthropic format, ready to pass
    directly to any LiteLLM-compatible router.

    Architecture:
        Message 0  [SYSTEM]    → PRIMACY ZONE
                                  Agent identity + active task + plan + skills.
                                  This slot receives the absolute highest attention.

        Message 1  [USER]      → MIDDLE ZONE injection
                                  Background semantic knowledge wrapped in a
                                  [CONTEXT INJECTION] frame to signal supplementary nature.

        Message 2  [ASSISTANT] → MIDDLE ZONE acknowledgment
                                  A brief assistant turn acknowledging the injected context.
                                  This serves two purposes:
                                  (a) Validates the context syntactically in the turn structure
                                  (b) Positions the background knowledge earlier in the sequence
                                      than the real conversation, exploiting the attention topology

        Messages 3..N-1        → Conversation history (truncated to budget)

        Message N  [USER]      → RECENCY ZONE prefix + actual user message
                                  Working memory state + episodic hits prepended to the
                                  final user turn, placing them in the highest-recall position.

    Note on the acknowledgment turn:
        Some models (particularly Claude 3.x+ and GPT-4o) may exhibit slightly
        different behavior with injected assistant turns. In practice, the quality
        improvement from positional optimization outweighs any mild instruction-
        following artifacts. Monitor via Langfuse traces and A/B test if needed.

    Args:
        inputs:        All cognitive inputs for this reasoning step
        budget:        Token budget across zones (uses defaults if None)
        token_counter: Optional callable(str) -> int for precise budget enforcement.
                       If None, uses rough char/4 approximation.

    Returns:
        List of message dicts with 'role' and 'content' keys.
    """
    budget = budget or ContextBudget()

    def approx_tokens(text: str) -> int:
        if token_counter:
            return token_counter(text)
        return max(1, len(text) // 4)   # GPT-4 tokenizer approximation

    # ─── PRIMACY ZONE: System message ────────────────────────────────────────
    plan_str   = _format_plan(inputs.current_plan)
    skills_str = "\n".join(f"  • {s}" for s in inputs.active_skills) if inputs.active_skills else "  None loaded."

    system_content = f"""{inputs.agent_identity}

━━ ACTIVE TASK ━━
{inputs.active_task or "Awaiting user direction."}

━━ EXECUTION PLAN ━━
{plan_str}

━━ LOADED SKILLS (Procedural Memory) ━━
{skills_str}
""".strip()

    messages: list[dict] = [
        {"role": "system", "content": system_content}
    ]

    # ─── MIDDLE ZONE: Background knowledge injection ──────────────────────────
    # Only inject if we have something worth saying — empty middle zone is
    # better than a sparse one (empty messages waste tokens and confuse some models)
    semantic_str = _format_semantic_memories(inputs.semantic_memories)
    tool_schema_str = ""
    if inputs.tool_schemas:
        tool_names = [t.get("name", "?") for t in inputs.tool_schemas]
        tool_schema_str = f"\nAvailable tools: {', '.join(tool_names)}"

    middle_content = "\n\n".join(filter(None, [semantic_str, tool_schema_str]))

    if middle_content.strip():
        messages.append({
            "role": "user",
            "content": f"[CONTEXT INJECTION — supplementary background]\n\n{middle_content}"
        })
        messages.append({
            "role": "assistant",
            "content": (
                "Understood. I have the above context available as background reference. "
                "Proceeding with the active task."
            )
        })

    # ─── Conversation history (budget-constrained) ────────────────────────────
    # Walk backward through history, accumulating until we approach the recency budget.
    # This ensures the most recent exchanges are always included.
    history_budget_tokens = budget.recency_tokens // 2   # Share recency budget with WM state
    history_tokens_used   = 0
    history_to_include    = []

    for msg in reversed(inputs.conversation_history):
        msg_tokens = approx_tokens(msg.get("content", ""))
        if history_tokens_used + msg_tokens > history_budget_tokens:
            break
        history_to_include.insert(0, msg)
        history_tokens_used += msg_tokens

    messages.extend(history_to_include)

    # ─── RECENCY ZONE: State prefix on final user message ────────────────────
    wm_str       = _format_working_memory(inputs.working_memory)
    episodic_str = _format_episodic_context(inputs.episodic_context + inputs.retrieved_memories)

    recency_prefix_parts = [p for p in [wm_str, episodic_str] if p.strip()]
    recency_prefix = "\n\n".join(recency_prefix_parts)

    # The last message in conversation_history is the user's current message.
    # Prepend the recency-zone state to maximize its attended position.
    if messages and messages[-1]["role"] == "user":
        original_content = messages[-1]["content"]
        messages[-1]["content"] = (
            f"{recency_prefix}\n\n━━ USER MESSAGE ━━\n{original_content}"
            if recency_prefix
            else original_content
        )
    elif recency_prefix:
        # Edge case: conversation ended with an assistant turn.
        # This happens during multi-step tool execution. Inject state as standalone user message.
        messages.append({
            "role": "user",
            "content": f"[AGENT STATE UPDATE]\n\n{recency_prefix}"
        })

    return messages


def estimate_context_stats(messages: list[dict]) -> dict:
    """
    Diagnostic: estimate token distribution across zones for a given message list.
    Useful for Langfuse metadata and budget tuning.
    """
    if not messages:
        return {"total": 0, "primacy": 0, "middle": 0, "recency": 0}

    def approx(text: str) -> int:
        return max(1, len(text) // 4)

    zone_tokens = {"primacy": 0, "middle": 0, "recency": 0}

    # Classify by position in the list (rough heuristic matching assembly logic)
    n = len(messages)
    for i, msg in enumerate(messages):
        tokens = approx(msg.get("content", ""))
        if i == 0:
            zone_tokens["primacy"] += tokens
        elif 0 < i < n - 3:
            zone_tokens["middle"] += tokens
        else:
            zone_tokens["recency"] += tokens

    total = sum(zone_tokens.values())
    return {
        "total":   total,
        "primacy": zone_tokens["primacy"],
        "middle":  zone_tokens["middle"],
        "recency": zone_tokens["recency"],
        "primacy_pct": f"{zone_tokens['primacy']/total:.1%}" if total else "0%",
        "recency_pct": f"{zone_tokens['recency']/total:.1%}" if total else "0%",
    }
