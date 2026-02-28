"""Tests for the pure (side-effect-free) functions in supernova/core/agent/loop.py.

All framework dependencies (langgraph, langfuse, context_assembly, procedural)
are stubbed at module-import time so CI needs no running infra.

ToT paths covered:
  _classify_task     : planning / tool_call / fast / smart
  _should_trigger_reflection : tool_calls, plan-complete, long-response, short-default
  route_after_reasoning      : safety-gate / execute_tools (attr) / execute_tools (dict)
                               / reflect / default-consolidate
  route_after_reflection     : revise-loops-back / approved-consolidate / none-consolidate
  make_session_config        : base structure / extra-fields-merged
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Framework stubs — must happen before any supernova.core.agent.loop import
# ---------------------------------------------------------------------------

def _stub(name: str, obj=None):
    m = obj if obj is not None else MagicMock()
    sys.modules[name] = m
    return m

_lgg = _stub("langgraph.graph")
_lgg.END = "END"
_lgg.StateGraph = MagicMock()
_stub("langgraph")
_stub("langgraph.checkpoint")
_stub("langgraph.checkpoint.postgres")
_stub("langgraph.checkpoint.postgres.aio")

_lfd = _stub("langfuse.decorators")
_lfd.observe = lambda **kwargs: (lambda f: f)  # passthrough decorator
_lfd.langfuse_context = MagicMock()
_stub("langfuse")

_stub("supernova.core.reasoning")
_stub("supernova.core.reasoning.context_assembly")
_stub("supernova.core.memory.procedural")

# ---------------------------------------------------------------------------
# Import the pure functions under test
# ---------------------------------------------------------------------------
from supernova.core.agent.loop import (  # noqa: E402
    _classify_task,
    _should_trigger_reflection,
    route_after_reasoning,
    route_after_reflection,
    make_session_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s(**kwargs) -> dict:
    """Build a minimal AgentState-compatible dict."""
    base: dict = {
        "messages": [],
        "retrieved_episodic": [],
        "retrieved_semantic": [],
        "active_skill": None,
        "working_memory": {},
        "current_plan": [],
        "active_task": "",
        "tool_calls_this_turn": 0,
        "should_reflect": False,
        "reflection_critique": None,
        "session_id": "sess-test",
        "user_id": "u-test",
        "granted_capabilities": 0,
    }
    base.update(kwargs)
    return base


class _Resp:
    """Fake LLM response object."""
    def __init__(self, content: str = "", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


# ===========================================================================
# _classify_task
# ===========================================================================

def test_classify_planning() -> None:
    state = _s(current_plan=[{"step": "do X"}], tool_calls_this_turn=0)
    assert _classify_task(state) == "planning"


def test_classify_tool_call() -> None:
    state = _s(current_plan=[{"step": "do X"}], tool_calls_this_turn=2)
    assert _classify_task(state) == "tool_call"


def test_classify_fast() -> None:
    state = _s(
        messages=[{"role": "user", "content": "Hi!"}],
        tool_calls_this_turn=0,
        current_plan=[],
    )
    assert _classify_task(state) == "fast"


def test_classify_smart_keyword_trigger() -> None:
    state = _s(
        messages=[{"role": "user", "content": "Please analyze the tradeoffs."}],
        tool_calls_this_turn=0,
        current_plan=[],
    )
    assert _classify_task(state) == "smart"


def test_classify_smart_long_content() -> None:
    state = _s(
        messages=[{"role": "user", "content": "x" * 201}],
        tool_calls_this_turn=0,
        current_plan=[],
    )
    assert _classify_task(state) == "smart"


# ===========================================================================
# _should_trigger_reflection
# ===========================================================================

def test_no_reflect_when_tool_calls_present() -> None:
    resp = _Resp(tool_calls=[{"name": "bash"}])
    assert _should_trigger_reflection(_s(), resp) is False


def test_reflect_when_plan_all_complete() -> None:
    resp = _Resp(content="Done.")
    state = _s(current_plan=[
        {"status": "complete"},
        {"status": "complete"},
    ])
    assert _should_trigger_reflection(state, resp) is True


def test_no_reflect_when_plan_partially_incomplete() -> None:
    resp = _Resp(content="Still going.")
    state = _s(current_plan=[
        {"status": "complete"},
        {"status": "in_progress"},
    ])
    assert _should_trigger_reflection(state, resp) is False


def test_reflect_on_long_response() -> None:
    resp = _Resp(content="w" * 1600)
    assert _should_trigger_reflection(_s(), resp) is True


def test_no_reflect_on_short_simple_response() -> None:
    resp = _Resp(content="Sure, here you go.")
    assert _should_trigger_reflection(_s(), resp) is False


# ===========================================================================
# route_after_reasoning
# ===========================================================================

def test_route_safety_gate_at_15_calls() -> None:
    state = _s(tool_calls_this_turn=15)
    assert route_after_reasoning(state) == "consolidate"


def test_route_execute_tools_via_attr() -> None:
    class _Msg:
        tool_calls = [{"name": "search"}]
    state = _s(messages=[_Msg()], tool_calls_this_turn=0)
    assert route_after_reasoning(state) == "execute_tools"


def test_route_execute_tools_via_dict() -> None:
    state = _s(
        messages=[{"role": "assistant", "tool_calls": [{"id": "tc1"}]}],
        tool_calls_this_turn=0,
    )
    assert route_after_reasoning(state) == "execute_tools"


def test_route_to_reflect_when_flag_set() -> None:
    state = _s(
        messages=[{"role": "assistant", "content": "Here is my answer."}],
        should_reflect=True,
        reflection_critique=None,
        tool_calls_this_turn=0,
    )
    assert route_after_reasoning(state) == "reflect"


def test_route_default_consolidate() -> None:
    state = _s(
        messages=[{"role": "assistant", "content": "Here is my answer."}],
        should_reflect=False,
        tool_calls_this_turn=0,
    )
    assert route_after_reasoning(state) == "consolidate"


def test_route_no_messages_defaults_to_consolidate() -> None:
    state = _s(messages=[], tool_calls_this_turn=0, should_reflect=False)
    assert route_after_reasoning(state) == "consolidate"


# ===========================================================================
# route_after_reflection
# ===========================================================================

def test_route_reflection_revise_loops_back() -> None:
    state = _s(reflection_critique="REFLECTION: REVISE\nIssues: wrong claim.")
    assert route_after_reflection(state) == "reason"


def test_route_reflection_approved_consolidates() -> None:
    state = _s(reflection_critique="REFLECTION: APPROVED")
    assert route_after_reflection(state) == "consolidate"


def test_route_reflection_empty_critique_consolidates() -> None:
    state = _s(reflection_critique=None)
    assert route_after_reflection(state) == "consolidate"


# ===========================================================================
# make_session_config
# ===========================================================================

def test_session_config_base_structure() -> None:
    cfg = make_session_config("sess-abc", "user-xyz")
    assert cfg["configurable"]["thread_id"] == "sess-abc"
    assert cfg["configurable"]["user_id"] == "user-xyz"
    assert cfg["recursion_limit"] == 50


def test_session_config_extra_fields_merged() -> None:
    cfg = make_session_config("s1", "u1", extra={"tenant": "acme"})
    assert cfg["configurable"]["tenant"] == "acme"
    assert cfg["configurable"]["thread_id"] == "s1"
