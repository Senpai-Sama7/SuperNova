"""Tests for MemoryAgent.

Critical paths covered:
  A. Valid JSON from LLM    -> facts correctly parsed into list
  B. Non-JSON from LLM      -> empty list returned, no crash
  C. process() happy path   -> store_facts called with salience-scored dicts
  D. Consolidation trigger  -> asyncio.create_task fires consolidate() when
                               memory count exceeds threshold
  E. process() LLM failure  -> exception swallowed, store_facts NOT called
"""
from __future__ import annotations

import asyncio

import pytest
from unittest.mock import AsyncMock, patch

from supernova.core.agent.shared_state import SharedState


# ── shared test helpers ──────────────────────────────────
class _Msg:
    def __init__(self, content: str):
        self.content = content

class _Choice:
    def __init__(self, content: str):
        self.message = _Msg(content)

class _LLMResponse:
    def __init__(self, content: str):
        self.choices = [_Choice(content)]


@pytest.fixture()
def state() -> SharedState:
    return SharedState(
        conversation_id="mem-test-001",
        user_message="What is 2 + 2?",
        execution_results={"step-1": "4"},
        final_response="The answer is 4.",
    )


# ── A: valid JSON fact extraction ────────────────────────
@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.memory_agent.get_settings")
async def test_extract_facts_valid_json(
    mock_settings, mock_llm, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.return_value = _LLMResponse(
        '["User asked arithmetic", "Answer was 4"]'
    )

    from supernova.core.agent.memory_agent import MemoryAgent
    agent = MemoryAgent(model="gpt-4o-mini")
    facts = await agent._extract_facts(state)

    assert len(facts) == 2
    assert "User asked arithmetic" in facts
    assert "Answer was 4" in facts


# ── B: non-JSON graceful fallback ───────────────────────
@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.memory_agent.get_settings")
async def test_extract_facts_non_json_returns_empty(
    mock_settings, mock_llm, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.return_value = _LLMResponse("Sorry, no facts found here.")

    from supernova.core.agent.memory_agent import MemoryAgent
    agent = MemoryAgent(model="gpt-4o-mini")
    facts = await agent._extract_facts(state)

    assert facts == []


# ── C: store_facts called with salience ─────────────────
@pytest.mark.asyncio
@patch("supernova.core.agent.memory_agent.compute_salience", return_value=0.75)
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.memory_agent.get_settings")
async def test_process_stores_facts_with_salience(
    mock_settings, mock_llm, _salience, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.return_value = _LLMResponse('["Key insight"]')

    memory_store = AsyncMock()
    memory_store.count = AsyncMock(return_value=3)  # below threshold

    from supernova.core.agent.memory_agent import MemoryAgent
    agent = MemoryAgent(memory_store=memory_store, model="gpt-4o-mini")
    await agent.process(state)

    memory_store.store_facts.assert_called_once()
    stored = memory_store.store_facts.call_args[0][0]
    assert len(stored) == 1
    assert stored[0]["content"] == "Key insight"
    assert stored[0]["salience_score"] == 0.75


# ── D: consolidation triggered above threshold ───────────
@pytest.mark.asyncio
@patch("supernova.core.agent.memory_agent.compute_salience", return_value=0.9)
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.memory_agent.get_settings")
async def test_process_triggers_consolidation(
    mock_settings, mock_llm, _salience, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.return_value = _LLMResponse('["Fact A"]')

    memory_store = AsyncMock()
    memory_store.count = AsyncMock(return_value=99)  # above threshold of 50

    from supernova.core.agent.memory_agent import MemoryAgent
    agent = MemoryAgent(
        memory_store=memory_store,
        model="gpt-4o-mini",
        consolidation_threshold=50,
    )
    await agent.process(state)

    # Yield to event loop so the asyncio.create_task can run
    await asyncio.sleep(0)

    memory_store.store_facts.assert_called_once()
    memory_store.consolidate.assert_called_once()


# ── E: LLM failure swallowed silently ───────────────────
@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.memory_agent.get_settings")
async def test_process_llm_failure_does_not_crash(
    mock_settings, mock_llm, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.side_effect = Exception("Network error")

    memory_store = AsyncMock()

    from supernova.core.agent.memory_agent import MemoryAgent
    agent = MemoryAgent(memory_store=memory_store, model="gpt-4o-mini")

    # Must not raise
    await agent.process(state)

    # store_facts should NEVER be called if fact extraction failed
    memory_store.store_facts.assert_not_called()
