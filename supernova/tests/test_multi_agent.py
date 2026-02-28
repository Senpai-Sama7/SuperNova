import pytest
from unittest.mock import AsyncMock, patch

from supernova.core.agent.orchestrator import OrchestratorAgent
from supernova.core.agent.planner import PlannerAgent
from supernova.core.agent.shared_state import SharedState

# A dummy response structure for litellm.acompletion
class DummyChoice:
    def __init__(self, content):
        self.message = type('Message', (), {'content': content})()

class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]


def test_orchestrator_classify_task_simple() -> None:
    """Test classification of a simple task (no planning keywords)."""
    orchestrator = OrchestratorAgent()
    agents = orchestrator._classify_task("Tell me a joke")
    assert agents == ["executor", "critic"]


def test_orchestrator_classify_task_complex() -> None:
    """Test classification of a task that triggers the planner."""
    orchestrator = OrchestratorAgent()
    agents = orchestrator._classify_task("I need you to plan out a multi-step workflow for this.")
    assert "planner" in agents
    assert "executor" in agents
    assert "critic" in agents


@pytest.mark.asyncio
@patch("litellm.acompletion", new_callable=AsyncMock)
async def test_planner_parses_numbered_steps(mock_acompletion) -> None:
    """Test the planner extracts only the numbered steps from LLM output."""
    mock_acompletion.return_value = DummyResponse(
        "Here is the plan:\n"
        "1. Analyze the context\n"
        "2. Build the module\n"
        "3. Write tests\n"
        "And that's it!"
    )

    state = SharedState(
        conversation_id="test-123",
        user_message="Plan out the building of a module",
    )
    planner = PlannerAgent()
    new_state = await planner.plan(state)

    assert new_state.plan is not None
    assert len(new_state.plan) == 3
    assert new_state.plan == ["Analyze the context", "Build the module", "Write tests"]


@pytest.mark.asyncio
@patch("supernova.core.agent.planner.PlannerAgent.plan", new_callable=AsyncMock)
@patch("litellm.acompletion", new_callable=AsyncMock)
async def test_orchestrator_process_full_path(mock_acompletion, mock_plan) -> None:
    """
    Test the full orchestration flow.
    We mock the planner to append a plan to the state, and litellm for the critic call.
    """
    # Critic agent mock output
    mock_acompletion.return_value = DummyResponse("The plan looks fine.")

    # Planner mock side-effect
    async def fake_plan(state):
        state.plan = ["Step 1"]
        return state

    mock_plan.side_effect = fake_plan

    orchestrator = OrchestratorAgent()
    
    # "plan" keyword triggers planner execution inside OrchestratorAgent.process()
    final_response = await orchestrator.process("Please plan this task.")

    assert mock_plan.called
    assert "Plan created with 1 steps" in final_response
    # Verify a critic call happened
    assert mock_acompletion.called
