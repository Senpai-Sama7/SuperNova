"""End-to-end test of the multi-agent pipeline."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from supernova.core.agent.orchestrator import OrchestratorAgent


@pytest.mark.asyncio
async def test_orchestrator_simple_task():
    """Simple task routes to executor + critic only."""
    with patch('litellm.acompletion') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Done"))]
        )
        orchestrator = OrchestratorAgent()
        agents = orchestrator._classify_task("What is 2+2?")
        assert "executor" in agents
        assert "critic" in agents
        assert "planner" not in agents


@pytest.mark.asyncio
async def test_orchestrator_complex_task_needs_planner():
    """Complex task with planning keywords routes to planner."""
    orchestrator = OrchestratorAgent()
    agents = orchestrator._classify_task("Break down the steps to deploy this app")
    assert "planner" in agents
    assert "executor" in agents
    assert "critic" in agents


@pytest.mark.asyncio
async def test_orchestrator_process_returns_response():
    """Full process() call returns a string response."""
    with patch('litellm.acompletion') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Reviewed"))]
        )
        orchestrator = OrchestratorAgent()
        result = await orchestrator.process("Hello world")
        assert isinstance(result, str)
        assert len(result) > 0
