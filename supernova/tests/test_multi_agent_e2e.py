"""End-to-end test of the multi-agent pipeline."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from supernova.core.agent.orchestrator import OrchestratorAgent
from supernova.core.agent.shared_state import SharedAgentState


@pytest.mark.asyncio
async def test_multi_agent_pipeline_e2e():
    """Test complete multi-agent workflow from task submission to final response."""
    
    # Mock LLM responses for each agent
    mock_responses = {
        "planner": {"choices": [{"message": {"content": "Plan: 1. Read document 2. Extract key points 3. Create summary"}}]},
        "executor": {"choices": [{"message": {"content": "Executed: Document processed, key points extracted"}}]},
        "critic": {"choices": [{"message": {"content": "Review: Summary is comprehensive and accurate"}}]}
    }
    
    call_count = 0
    async def mock_acompletion(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_responses["planner"]
        elif call_count == 2:
            return mock_responses["executor"]
        else:
            return mock_responses["critic"]
    
    with patch('litellm.acompletion', side_effect=mock_acompletion):
        # Create orchestrator with mock config
        config = MagicMock()
        config.model = "gpt-4"
        config.max_iterations = 3
        
        orchestrator = OrchestratorAgent(config)
        
        # Submit task
        task = "Summarize this document: Lorem ipsum dolor sit amet..."
        
        # Execute pipeline
        result = await orchestrator.process_task(task)
        
        # Verify workflow executed
        assert call_count == 3, "Should have called LLM for planner, executor, and critic"
        assert result is not None, "Should return a result"
        
        # Verify state transitions
        state = orchestrator.shared_state
        assert isinstance(state, SharedAgentState)
        assert state.current_task == task
        assert state.status in ["completed", "success"]


@pytest.mark.asyncio
async def test_agent_delegation_flow():
    """Test that orchestrator properly delegates to sub-agents."""
    
    with patch('litellm.acompletion') as mock_llm:
        mock_llm.return_value = {"choices": [{"message": {"content": "Task completed"}}]}
        
        config = MagicMock()
        orchestrator = OrchestratorAgent(config)
        
        # Mock sub-agents
        orchestrator.planner = AsyncMock()
        orchestrator.executor = AsyncMock()
        orchestrator.critic = AsyncMock()
        
        await orchestrator.process_task("Test task")
        
        # Verify delegation occurred
        orchestrator.planner.create_plan.assert_called_once()
        orchestrator.executor.execute_steps.assert_called_once()
        orchestrator.critic.review_output.assert_called_once()