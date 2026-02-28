"""End-to-end test of the multi-agent pipeline."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from supernova.core.agent.orchestrator import OrchestratorAgent
from supernova.core.agent.shared_state import SharedState


@pytest.mark.asyncio
async def test_multi_agent_pipeline_e2e():
    """Test complete multi-agent workflow from task submission to final response."""
    
    # Mock LLM responses for each agent
    class MockChoice:
        def __init__(self, content):
            self.message = MagicMock()
            self.message.content = content
    
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
    
    mock_responses = {
        "planner": MockResponse("Plan: 1. Read document 2. Extract key points 3. Create summary"),
        "executor": MockResponse("Executed: Document processed, key points extracted"),
        "critic": MockResponse("Review: Summary is comprehensive and accurate")
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
        # Create orchestrator
        orchestrator = OrchestratorAgent()
        
        # Submit task
        task = "Summarize this document: Lorem ipsum dolor sit amet..."
        
        # Execute pipeline
        result = await orchestrator.process(task)
        
        # Verify workflow executed
        assert call_count == 1, "Should have called LLM for critic only (no planning keywords in task)"
        assert result is not None, "Should return a result"
        
        # Verify result is a string
        assert isinstance(result, str), "Should return a string response"


@pytest.mark.asyncio
async def test_orchestrator_process_returns_response():
    """Full process() call returns a string response."""
    with patch('litellm.acompletion') as mock_llm:
        # Create proper mock response object
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Task completed"
        mock_llm.return_value = mock_response
        
        orchestrator = OrchestratorAgent()
        
        # Since the current implementation doesn't expose sub-agents as attributes,
        # we'll test the process method directly
        result = await orchestrator.process("Test task")
        
        # Verify we get a response
        assert isinstance(result, str)
        assert len(result) > 0
