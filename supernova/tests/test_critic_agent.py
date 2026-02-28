"""Tests for CriticAgent.

Critical paths covered:
  A. NO_ISSUES  -> single LLM call, state.final_response unchanged
  B. ISSUES_FOUND -> two LLM calls, state.final_response replaced by revision
  C. LLM throws  -> caught, state.critique carries error message, no crash
  D. _build_critique_prompt -> pure unit test, no mocking needed
"""
from __future__ import annotations

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
        conversation_id="crit-test-001",
        user_message="What is 2 + 2?",
        execution_results={"step-1": "4"},
        final_response="The answer is 4.",
    )


# ── D: pure unit test ────────────────────────────────────
@patch("supernova.core.agent.critic.get_settings")
def test_build_critique_prompt_contains_key_fields(mock_settings, state) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    from supernova.core.agent.critic import CriticAgent

    critic = CriticAgent(model="gpt-4o-mini")
    prompt = critic._build_critique_prompt(state)

    assert "What is 2 + 2?" in prompt
    assert "The answer is 4." in prompt
    assert "ISSUES_FOUND" in prompt
    assert "NO_ISSUES" in prompt


# ── A: NO_ISSUES path ───────────────────────────────────
@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.critic.get_settings")
async def test_critic_no_issues_keeps_response(
    mock_settings, mock_llm, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.return_value = _LLMResponse("NO_ISSUES: Correct and complete.")

    from supernova.core.agent.critic import CriticAgent
    critic = CriticAgent(model="gpt-4o-mini")
    original = state.final_response
    updated = await critic.review(state)

    # Critique stored, response untouched, only one LLM call made
    assert updated.critique == "NO_ISSUES: Correct and complete."
    assert updated.final_response == original
    mock_llm.assert_called_once()


# ── B: ISSUES_FOUND path ────────────────────────────────
@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.critic.get_settings")
async def test_critic_issues_found_triggers_revision(
    mock_settings, mock_llm, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.side_effect = [
        _LLMResponse("ISSUES_FOUND: Response was incomplete."),
        _LLMResponse("Revised: The answer is definitely 4."),
    ]

    from supernova.core.agent.critic import CriticAgent
    critic = CriticAgent(model="gpt-4o-mini")
    updated = await critic.review(state)

    assert "ISSUES_FOUND" in updated.critique
    assert updated.final_response == "Revised: The answer is definitely 4."
    # Exactly two LLM calls: critique + revision
    assert mock_llm.call_count == 2


# ── C: LLM failure path ─────────────────────────────────
@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
@patch("supernova.core.agent.critic.get_settings")
async def test_critic_llm_failure_is_safe(
    mock_settings, mock_llm, state
) -> None:
    mock_settings.return_value.llm.effective_default_model = "gpt-4o-mini"
    mock_llm.side_effect = Exception("LLM service unavailable")
    original_response = state.final_response

    from supernova.core.agent.critic import CriticAgent
    critic = CriticAgent(model="gpt-4o-mini")
    updated = await critic.review(state)

    # Error captured in critique, response NOT overwritten
    assert "Critique error" in updated.critique
    assert "LLM service unavailable" in updated.critique
    assert updated.final_response == original_response
