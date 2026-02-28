"""
core/agent/loop.py

The cognitive loop — the central executive of the agent.

This module wires together every subsystem developed across this architecture:
  - Positionally-aware context assembly (context_assembly.py)
  - Procedural memory retrieval and skill activation (procedural.py)
  - Episodic + semantic memory retrieval
  - LangGraph stateful orchestration with PostgreSQL checkpointing
  - Reflexion-style self-evaluation
  - IronClaw-inspired capability-based tool permissions

Cognitive cycle (per reasoning step):
    1. PERCEIVE   — restore state from checkpoint, receive new input
    2. REMEMBER   — parallel retrieval from episodic + semantic stores
    3. PRIME      — check procedural memory for an applicable compiled skill
    4. ASSEMBLE   — build the optimally-positioned context window
    5. REASON     — LLM call with assembled context
    6. ACT        — execute tool calls (with interrupt checkpoint)
    7. REFLECT    — optional self-evaluation if quality criteria triggered
    8. CONSOLIDATE — write new episodes and update working memory

Checkpointing via AsyncPostgresSaver means every state transition is durable.
A process crash between any two steps resumes from the last successful step.

LangGraph architectural note:
    StateGraph nodes are pure async functions: (AgentState) -> dict.
    The dict returned is merged (not replaced) into AgentState via the
    Annotated[list, operator.add] type annotations on list fields.
    This immutable-update semantics makes state transitions formally composable
    and enables snapshot/restore without defensive copying.

    The routing function (route_after_reasoning) implements the control flow
    of the cognitive loop as a pure function of state — no side effects,
    fully deterministic. This is the key property that makes the graph
    both checkpointable and unit-testable.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Annotated, Any, TypedDict

import operator
from datetime import datetime, timezone

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langfuse.decorators import observe, langfuse_context

from supernova.core.reasoning.context_assembly import (
    ContextBudget,
    ContextInputs,
    assemble_context_window,
    estimate_context_stats,
)
from supernova.core.memory.procedural import ProceduralMemoryStore, SkillMatch

logger = logging.getLogger(__name__)


# ─── Agent State Definition ───────────────────────────────────────────────────

class AgentState(TypedDict):
    """
    The complete, serializable cognitive state at any point in the graph.

    Design principles:
      1. All fields are JSON-serializable primitives (list, dict, str, int, bool, None)
         This is required for AsyncPostgresSaver to checkpoint state to PostgreSQL.
         No Python objects, no class instances, no callables.

      2. List fields use Annotated[list, operator.add] rather than replacement.
         When a node returns {"messages": [new_msg]}, LangGraph appends new_msg
         to the existing list rather than replacing it. This is the difference
         between an append-log (correct) and a replace-buffer (loses history).

      3. All fields have sensible defaults. LangGraph initializes state from the
         first invocation's input dict, so fields absent from the initial input
         use their TypedDict defaults (Python 3.11+ TypedDict supports defaults
         via NotRequired or field defaults; here we handle this in graph.compile()).
    """
    # ── Conversation ──────────────────────────────────────────────────────────
    messages:              Annotated[list[dict], operator.add]   # Full message history

    # ── Memory snapshots (populated by retrieval node) ────────────────────────
    retrieved_episodic:    list[dict]      # From Graphiti temporal graph
    retrieved_semantic:    list[dict]      # From pgvector semantic store
    active_skill:          dict | None     # Activated procedural skill (or None)

    # ── Cognitive state ───────────────────────────────────────────────────────
    working_memory:        dict            # Current WM snapshot from Redis
    current_plan:          list[dict]      # Active multi-step plan
    active_task:           str             # Current goal description

    # ── Control flow signals ──────────────────────────────────────────────────
    tool_calls_this_turn:  int             # Guard against infinite tool loops
    should_reflect:        bool            # Trigger Reflexion self-evaluation?
    reflection_critique:   str | None      # Output of reflection node

    # ── Session context ───────────────────────────────────────────────────────
    session_id:            str
    user_id:               str
    granted_capabilities:  int             # Bitmask (matches Capability flag values)


# ─── Node Implementations ─────────────────────────────────────────────────────

@observe(name="memory_retrieval")
async def memory_retrieval_node(
    state: AgentState,
    *,
    episodic_store: Any,
    semantic_store: Any,
    procedural_store: ProceduralMemoryStore,
    working_memory_store: Any,
) -> dict:
    """
    PERCEIVE + REMEMBER step: parallel retrieval from all memory systems.

    Parallelism strategy:
        asyncio.gather fires all retrieval coroutines concurrently.
        Total latency = max(episodic, semantic, procedural, working_memory)
        rather than their sum. For typical retrieval times:
          episodic (Graphiti):  20–80ms
          semantic (pgvector):  5–30ms
          procedural (pgvector): 5–20ms
          working memory (Redis): <5ms
        Sequential: ~110–135ms. Parallel: ~80ms. Savings compound across turns.

    Procedural skill activation:
        The most recent user message provides the "situation description"
        for procedural memory retrieval. If a skill matches with confidence
        above the threshold, it is loaded into active_skill for use by
        the reasoning node's context assembly.

        The skill itself is NOT invoked here — procedural memory lookup
        is a read-only operation that informs context assembly. The skill
        graph may be invoked later if the reasoning node confirms its relevance.
    """
    # Extract the most recent user message for retrieval queries
    last_user_msg = next(
        (m["content"] for m in reversed(state["messages"]) if m["role"] == "user"),
        ""
    )

    langfuse_context.update_current_observation(
        input=last_user_msg,
        metadata={"session_id": state["session_id"]},
    )

    # Parallel retrieval from all memory subsystems
    episodic_task    = episodic_store.recall(last_user_msg, limit=8)
    semantic_task    = semantic_store.search(last_user_msg, limit=12)
    procedural_task  = procedural_store.recall_skill(last_user_msg)
    wm_task          = working_memory_store.get(state["session_id"])

    episodic, semantic, skill_match, wm = await asyncio.gather(
        episodic_task, semantic_task, procedural_task, wm_task,
        return_exceptions=True,   # Prevent one failure from killing all retrievals
    )

    # Graceful degradation: log errors but don't fail the cognitive loop
    def safe(result: Any, default: Any, label: str) -> Any:
        if isinstance(result, Exception):
            logger.warning("Memory retrieval failed (%s): %s", label, result)
            return default
        return result

    episodic       = safe(episodic, [], "episodic")
    semantic       = safe(semantic, [], "semantic")
    skill_match    = safe(skill_match, None, "procedural")
    working_memory = safe(wm, {}, "working_memory")

    # Serialize skill match for state (state must be JSON-serializable)
    active_skill = None
    if isinstance(skill_match, SkillMatch) and skill_match:
        active_skill = {
            "name":             skill_match.skill.name,
            "description":      skill_match.skill.description,
            "trigger_conditions": skill_match.skill.trigger_conditions,
            "similarity_score": skill_match.similarity_score,
            # NOTE: The compiled graph bytes are NOT stored in state (not serializable).
            # The procedural_store.recall_skill call is repeated in executor if needed.
        }
        logger.debug(
            "Procedural skill activated: '%s' (similarity=%.3f)",
            skill_match.skill.name, skill_match.similarity_score,
        )

    langfuse_context.update_current_observation(
        output={
            "episodic_count":    len(episodic),
            "semantic_count":    len(semantic),
            "skill_activated":   active_skill["name"] if active_skill else None,
            "working_memory_keys": list(working_memory.keys()),
        }
    )

    return {
        "retrieved_episodic": episodic,
        "retrieved_semantic":  semantic,
        "active_skill":        active_skill,
        "working_memory":      working_memory,
    }


@observe(name="agent_reasoning")
async def reasoning_node(
    state: AgentState,
    *,
    llm_router: Any,
    tool_registry: Any,
    agent_identity: str,
) -> dict:
    """
    ASSEMBLE + REASON step: build optimal context window, invoke LLM.

    This is the most latency-sensitive node in the graph (LLM call dominates).
    Every optimization in context assembly pays dividends here — fewer wasted
    tokens means lower cost and, more importantly, higher signal density in
    the context window the model actually attends to.

    Procedural skill context injection:
        If an activated skill was found by the retrieval node, its description
        and trigger conditions are injected into the system prompt's "loaded skills"
        section (PRIMACY zone). This primes the model to follow the skill's
        pattern without hardcoding control flow — the model can still deviate
        if the situation warrants it, but the cognitive inertia toward the
        skill pattern reduces the planning overhead.

    Tool schema injection:
        Tool schemas are placed in the MIDDLE zone (background knowledge).
        This is intentional: tool schemas are referenced when the LLM decides
        to call a tool, which requires more deliberate attention than the
        background recall that the middle zone supports adequately.
        For agents with >20 tools, consider a two-stage approach: LLM first
        selects relevant tools, then tool schemas are injected into a second
        LLM call for actual parameter generation.
    """
    # Build active skills list from procedural memory
    active_skills: list[str] = []
    if skill := state.get("active_skill"):
        skill_summary = (
            f"{skill['name']}: {skill['description']} "
            f"(activated with {skill['similarity_score']:.0%} confidence)"
        )
        active_skills.append(skill_summary)

    # Assemble the context window using positional optimization
    context_inputs = ContextInputs(
        agent_identity     = agent_identity,
        active_task        = state.get("active_task", ""),
        current_plan       = state.get("current_plan", []),
        active_skills      = active_skills,
        semantic_memories  = state.get("retrieved_semantic", []),
        tool_schemas       = tool_registry.get_tool_schemas(
            granted_capabilities=state.get("granted_capabilities", 0)
        ),
        episodic_context   = state.get("retrieved_episodic", []),
        working_memory     = state.get("working_memory", {}),
        conversation_history = state["messages"],
    )

    budget = ContextBudget(
        total_tokens   = 100_000,
        primacy_tokens = 3_000,
        recency_tokens = 20_000,
        middle_tokens  = 77_000,
    )

    assembled_messages = assemble_context_window(context_inputs, budget)
    context_stats      = estimate_context_stats(assembled_messages)

    langfuse_context.update_current_observation(
        metadata={
            "context_stats":       context_stats,
            "skill_activated":     active_skills[0] if active_skills else None,
            "episodic_memories":   len(state.get("retrieved_episodic", [])),
            "semantic_memories":   len(state.get("retrieved_semantic", [])),
            "tool_calls_this_turn": state.get("tool_calls_this_turn", 0),
        }
    )

    # Determine which model tier to use based on task complexity
    task_type = _classify_task(state)
    response = await llm_router.route_task(
        task_type = task_type,
        messages  = assembled_messages,
        tools     = tool_registry.get_tool_schemas(
            granted_capabilities=state.get("granted_capabilities", 0)
        ),
        tool_choice = "auto",
    )

    logger.debug(
        "Reasoning complete: task_type=%s, context_tokens=%d, primacy=%.0f%%",
        task_type,
        context_stats["total"],
        float(context_stats["primacy_pct"].rstrip("%")),
    )

    return {
        "messages": [response],
        # Signal whether reflection should be considered based on task complexity
        "should_reflect": _should_trigger_reflection(state, response),
    }


def _classify_task(state: AgentState) -> str:
    """
    Classify the current task for model routing.

    The classification determines which model tier handles this reasoning step.
    Heuristics are intentionally simple — the goal is to route ~60-70% of
    sub-tasks to cheaper models without quality loss, not to achieve perfect
    classification (which would itself require an LLM call, negating the savings).
    """
    tool_calls_so_far = state.get("tool_calls_this_turn", 0)
    has_plan = bool(state.get("current_plan"))
    messages = state.get("messages", [])
    last_content = messages[-1].get("content", "") if messages else ""

    # Multi-step planning invocations need the strongest model
    if has_plan and tool_calls_so_far == 0:
        return "planning"

    # Tool calls after planning established can use a capable-but-cheaper model
    if tool_calls_so_far > 0:
        return "tool_call"

    # Simple conversational exchanges — cheap model is fine
    if len(last_content) < 200 and not any(
        kw in last_content.lower()
        for kw in ["analyze", "plan", "research", "compare", "evaluate", "strategy"]
    ):
        return "fast"

    return "smart"


def _should_trigger_reflection(state: AgentState, response: Any) -> bool:
    """
    Determine whether the Reflexion self-evaluation loop should fire.

    Reflection is expensive (one additional LLM call per trigger) so it should
    be reserved for situations where quality uncertainty is high:
      1. First completion of a multi-step plan (did we get it right?)
      2. Complex tasks (long responses with multiple claims)
      3. Stochastic/creative tasks where variance is high

    It is explicitly disabled for:
      1. Tool call steps (not a final output)
      2. Short conversational responses
      3. Sessions where the user has disabled it (future: settings flag)
    """
    # Never reflect mid-tool-loop
    if hasattr(response, "tool_calls") and response.tool_calls:
        return False

    # Reflect when completing a plan
    plan = state.get("current_plan", [])
    if plan and all(s.get("status") == "complete" for s in plan):
        return True

    # Reflect on long, complex responses (rough proxy for task complexity)
    content = getattr(response, "content", "") or ""
    if isinstance(content, str) and len(content) > 1500:
        return True

    return False


@observe(name="tool_execution")
async def tool_execution_node(
    state: AgentState,
    *,
    tool_registry: Any,
    interrupt_coordinator: Any,
) -> dict:
    """
    ACT step: execute tool calls from the LLM's response.

    Security model (IronClaw-inspired):
        Tool execution is gated by the capability bitmask stored in state.
        The tool_registry validates capabilities at call time, not just at
        registration time, because granted_capabilities may change across
        a multi-session conversation (e.g., user grants file write access
        mid-conversation).

    Parallelism:
        Tools are classified as safe-to-parallelize or sequentially-dependent.
        Independent tools (read-only, no shared state) run concurrently.
        Dependent tools (write operations, stateful) run sequentially.
        The classification is conservative: if unsure, run sequentially.
        The latency win from parallelism (often 2-4×) is significant enough
        to justify the classification overhead.

    Human-in-the-loop:
        High-risk tool calls trigger the interrupt_coordinator before execution.
        This is implemented via LangGraph's interrupt_before mechanism — the graph
        pauses, serializes state to PostgreSQL, and waits for an external signal
        (from the WebSocket handler or OS notification approval) before resuming.
        The interrupt is entirely at the framework level; no tool sees it.
    """
    last_message = state["messages"][-1]

    if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
        return {"tool_calls_this_turn": state["tool_calls_this_turn"]}

    tool_calls = last_message.tool_calls

    # Classify tools for parallel vs. sequential execution
    parallel_calls   = []
    sequential_calls = []
    for tc in tool_calls:
        tool = tool_registry.get_tool(tc.name)
        if tool and getattr(tool, "is_safe_parallel", False):
            parallel_calls.append(tc)
        else:
            sequential_calls.append(tc)

    tool_messages = []
    granted = state.get("granted_capabilities", 0)

    # Execute parallel tools concurrently
    if parallel_calls:
        parallel_results = await asyncio.gather(*[
            tool_registry.execute(tc.name, tc.args, granted_capabilities=granted)
            for tc in parallel_calls
        ])
        for tc, result in zip(parallel_calls, parallel_results):
            tool_messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      str(result.get("result", result.get("error", "No output"))),
                "name":         tc.name,
            })

    # Execute sequential tools one by one
    for tc in sequential_calls:
        result = await tool_registry.execute(
            tc.name, tc.args,
            granted_capabilities=granted,
        )
        tool_messages.append({
            "role":         "tool",
            "tool_call_id": tc.id,
            "content":      str(result.get("result", result.get("error", "No output"))),
            "name":         tc.name,
        })

    langfuse_context.update_current_observation(
        metadata={
            "tools_called":    [tc.name for tc in tool_calls],
            "parallel_count":  len(parallel_calls),
            "sequential_count": len(sequential_calls),
        }
    )

    return {
        "messages":            tool_messages,
        "tool_calls_this_turn": state["tool_calls_this_turn"] + len(tool_calls),
    }


@observe(name="reflection")
async def reflection_node(
    state: AgentState,
    *,
    llm_router: Any,
) -> dict:
    """
    REFLECT step: Reflexion-style self-evaluation (Shinn et al., 2023).

    The Reflexion paper demonstrated that agents improve significantly when
    they explicitly evaluate their own output before finalizing it. The
    mechanism: a second LLM call critiques the first's output using a
    structured rubric, and the critique is injected back into the reasoning
    context for revision.

    Key implementation choices:
      1. The reflection call uses the SAME model tier as reasoning (not a
         cheaper model) because reflection quality is the binding constraint —
         a weak reflection produces useless or misleading critiques.

      2. The reflection prompt is injected as a new USER message, not a
         system message. This frames the reflection as new external feedback
         rather than a change to the agent's identity or instructions,
         which produces cleaner critiques empirically.

      3. The graph routes back to reasoning_node after reflection, not to
         the response sink. This enables multi-round reflection — though
         in practice more than one reflection round rarely improves quality
         and doubles the cost, so the implementation caps it.
    """
    reflection_prompt = """
    You are reviewing your previous response for quality and accuracy.

    Evaluate your last response against these criteria:
    1. ACCURACY — Did you make any factual errors or unsupported claims?
    2. COMPLETENESS — Did you actually answer what was asked, or did you drift?
    3. MEMORY FIDELITY — Did you correctly use the provided memory context?
    4. TOOL USE — Were your tool calls appropriate? Did you miss obvious tools to use?
    5. PLAN ADHERENCE — Are you making progress on the current plan?

    If the response is high quality, respond: "REFLECTION: APPROVED"
    If it needs revision, respond:
    "REFLECTION: REVISE
    Issues found: [list specific problems]
    Corrected approach: [what to do differently]"

    Keep your reflection concise (under 100 words).
    """.strip()

    response = await llm_router.route_task(
        task_type = "smart",   # Always use capable model for reflection
        messages  = state["messages"] + [{"role": "user", "content": reflection_prompt}],
    )

    critique = getattr(response, "content", "") or ""
    needs_revision = "REVISE" in critique.upper()

    langfuse_context.update_current_observation(
        output={"critique": critique, "needs_revision": needs_revision}
    )

    if needs_revision:
        logger.info("Reflection triggered revision: %s", critique[:200])
        return {
            "messages":          [{"role": "user", "content": f"[SELF-CRITIQUE]\n{critique}"}],
            "reflection_critique": critique,
            "should_reflect":    False,   # Don't re-reflect after revision
        }
    else:
        return {
            "should_reflect":    False,
            "reflection_critique": critique,
        }


@observe(name="memory_consolidation")
async def memory_consolidation_node(
    state: AgentState,
    *,
    episodic_store: Any,
    working_memory_store: Any,
) -> dict:
    """
    CONSOLIDATE step: write new knowledge and update cognitive state.

    This node fires after the agent produces a final response (not after
    every tool call) to avoid writing partial or misleading intermediate
    states to long-term memory.

    The consolidation writes:
      1. The completed conversation turn to the episodic store (Graphiti).
         Graphiti's entity extraction automatically identifies new facts,
         people, and relationships mentioned in the exchange and updates
         the temporal knowledge graph accordingly.

      2. The updated working memory to Redis, including any plan progress,
         attention updates, and tool result buffering from this turn.

    The write is fire-and-forget (asyncio.create_task) — we don't block
    the response path on memory writes. Durability is handled by PostgreSQL
    and Redis's AOF persistence, not by synchronous acknowledgment.
    """
    # Build episode content from the last few message turns
    recent_messages = state["messages"][-6:]
    episode_content  = "\n\n".join(
        f"[{m['role'].upper()}]: {m.get('content', '')[:1000]}"
        for m in recent_messages
        if m.get("content")
    )

    # Fire-and-forget: don't block response on memory writes
    asyncio.create_task(
        _write_episode_async(episodic_store, episode_content, state)
    )

    # Update working memory (also async)
    updated_wm = {
        **state.get("working_memory", {}),
        "last_turn_at":      datetime.now(timezone.utc).isoformat(),
        "tool_calls_total":  (
            state.get("working_memory", {}).get("tool_calls_total", 0) +
            state.get("tool_calls_this_turn", 0)
        ),
    }
    asyncio.create_task(
        working_memory_store.set_dict(state["session_id"], updated_wm)
    )

    return {}   # State update complete; no fields need merging


async def _write_episode_async(
    episodic_store: Any,
    content: str,
    state: AgentState,
) -> None:
    """Write an episode to the Graphiti temporal store. Errors are logged, not raised."""
    try:
        await episodic_store.record_episode(
            content=content,
            metadata={
                "session_id": state["session_id"],
                "user_id":    state["user_id"],
                "turn_at":    datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error("Failed to write episode to episodic store: %s", e)


# ─── Routing Functions ────────────────────────────────────────────────────────

def route_after_reasoning(state: AgentState) -> str:
    """
    The cognitive loop's control flow decision function.

    This is the only function in the entire graph that inspects state and
    returns routing strings — all control flow is concentrated here rather
    than scattered across nodes. This is intentional: centralized routing
    makes the agent's decision logic auditable and testable in isolation.

    Routing priority (highest to lowest):
      1. Safety gate: too many tool calls → force response (prevent loops)
      2. Tool calls requested → execute tools
      3. Reflection triggered → self-evaluate
      4. Default → consolidate and respond
    """
    tool_calls_this_turn = state.get("tool_calls_this_turn", 0)

    # Safety gate: prevent runaway tool loops
    # 15 tool calls per turn is generous; most tasks need <5
    # The limit is logged as a warning, not an error — it's expected
    # behavior for complex orchestration tasks
    if tool_calls_this_turn >= 15:
        logger.warning(
            "Tool call limit reached (%d calls) for session %s. Forcing response.",
            tool_calls_this_turn, state.get("session_id", "?")
        )
        return "consolidate"

    # Check if the LLM's last message requested tool calls
    last_message = state["messages"][-1] if state["messages"] else {}
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "execute_tools"
    if isinstance(last_message, dict) and last_message.get("tool_calls"):
        return "execute_tools"

    # Reflection gate
    if state.get("should_reflect") and not state.get("reflection_critique"):
        return "reflect"

    return "consolidate"


def route_after_reflection(state: AgentState) -> str:
    """
    After reflection, either revise (loop back to reasoning) or accept.

    The critique message was already injected into state["messages"] by
    reflection_node if revision is needed. Routing back to reasoning_node
    causes a second LLM call with the critique in context — the model
    sees its own self-evaluation and produces a revised response.
    """
    critique = state.get("reflection_critique", "")
    if critique and "REVISE" in critique.upper():
        return "reason"     # Loop: reasoning sees the critique and revises
    return "consolidate"    # Accept: no revision needed


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def build_agent_graph(
    checkpointer:          AsyncPostgresSaver,
    episodic_store:        Any,
    semantic_store:        Any,
    procedural_store:      ProceduralMemoryStore,
    working_memory_store:  Any,
    tool_registry:         Any,
    interrupt_coordinator: Any,
    llm_router:            Any,
    agent_identity:        str,
    enable_hitl:           bool = True,
) -> Any:
    """
    Assemble and compile the complete agent cognitive loop.

    The compiled graph is a pure Python object — no database connections,
    no network sockets. It can be safely cached in process memory and
    reused across sessions (the checkpointer handles session isolation
    via thread_id keys in the configuration dict).

    Human-in-the-loop configuration:
        interrupt_before=["execute_tools"] means LangGraph will:
          1. Execute all nodes before execute_tools normally
          2. Checkpoint state BEFORE entering execute_tools
          3. Raise a GraphInterrupt exception to the caller
          4. The caller (WebSocket handler) signals the interrupt_coordinator
          5. On approval: graph.invoke(None, config) resumes from the checkpoint
          6. On denial: the tool node is skipped, reasoning_node gets a
             tool_denied message, and produces a response without the tool

        When enable_hitl=False (e.g., fully autonomous mode), the interrupt
        is omitted and tools execute without human approval. This is appropriate
        for low-risk background tasks (heartbeat, memory consolidation) but
        should be the explicit opt-in, not the default.
    """
    graph = StateGraph(AgentState)

    # ── Node registration with injected dependencies ─────────────────────────
    # LangGraph nodes are called with (state) by the framework.
    # Dependencies are injected via functools.partial-style closures.
    # This keeps nodes testable in isolation (pass mock dependencies).

    async def _retrieve(state: AgentState) -> dict:
        return await memory_retrieval_node(
            state,
            episodic_store       = episodic_store,
            semantic_store       = semantic_store,
            procedural_store     = procedural_store,
            working_memory_store = working_memory_store,
        )

    async def _reason(state: AgentState) -> dict:
        return await reasoning_node(
            state,
            llm_router     = llm_router,
            tool_registry  = tool_registry,
            agent_identity = agent_identity,
        )

    async def _execute_tools(state: AgentState) -> dict:
        return await tool_execution_node(
            state,
            tool_registry         = tool_registry,
            interrupt_coordinator = interrupt_coordinator,
        )

    async def _reflect(state: AgentState) -> dict:
        return await reflection_node(state, llm_router=llm_router)

    async def _consolidate(state: AgentState) -> dict:
        return await memory_consolidation_node(
            state,
            episodic_store       = episodic_store,
            working_memory_store = working_memory_store,
        )

    graph.add_node("retrieve_memory", _retrieve)
    graph.add_node("reason",          _reason)
    graph.add_node("execute_tools",   _execute_tools)
    graph.add_node("reflect",         _reflect)
    graph.add_node("consolidate",     _consolidate)

    # ── Edge definitions ─────────────────────────────────────────────────────
    graph.set_entry_point("retrieve_memory")
    graph.add_edge("retrieve_memory", "reason")

    graph.add_conditional_edges(
        "reason",
        route_after_reasoning,
        {
            "execute_tools": "execute_tools",
            "reflect":       "reflect",
            "consolidate":   "consolidate",
        }
    )

    # After tool execution: always reason again about the results
    graph.add_edge("execute_tools", "reason")

    # After reflection: either revise (→ reason) or accept (→ consolidate)
    graph.add_conditional_edges(
        "reflect",
        route_after_reflection,
        {
            "reason":      "reason",
            "consolidate": "consolidate",
        }
    )

    # Memory consolidation is the terminal node
    graph.add_edge("consolidate", END)

    # ── Compilation ──────────────────────────────────────────────────────────
    interrupt_nodes = ["execute_tools"] if enable_hitl else []

    compiled = graph.compile(
        checkpointer    = checkpointer,
        interrupt_before = interrupt_nodes,
    )

    logger.info(
        "Agent graph compiled: HITL=%s, nodes=%s",
        enable_hitl, list(graph.nodes.keys())
    )

    return compiled


# ─── Graph Configuration Helper ──────────────────────────────────────────────

def make_session_config(
    session_id: str,
    user_id:    str,
    extra:      dict | None = None,
) -> dict:
    """
    Build the LangGraph invocation config for a specific session.

    The thread_id is the session isolation key: all checkpoints, state
    snapshots, and interrupt continuations use this as the partition key.
    Two sessions with different thread_ids are completely isolated even
    if they share the same compiled graph object and checkpointer connection.

    Recommendation: use session_id directly as thread_id so that your
    application's session concept maps 1:1 to LangGraph's checkpoint namespace.
    """
    config = {
        "configurable": {
            "thread_id": session_id,
            "user_id":   user_id,
        },
        "recursion_limit": 50,  # Maximum graph steps per invocation
    }
    if extra:
        config["configurable"].update(extra)
    return config
