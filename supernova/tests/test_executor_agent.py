import pytest
from unittest.mock import AsyncMock, MagicMock

from supernova.core.agent.executor import ExecutorAgent
from supernova.core.agent.shared_state import SharedState


@pytest.fixture
def dummy_state():
    return SharedState(
        conversation_id="test-123",
        user_message="Test message",
    )


@pytest.mark.asyncio
async def test_executor_agent_no_action(dummy_state) -> None:
    """Test ExecutorAgent when the step dict lacks an 'action' key."""
    # Dummy tool registry, won't be called
    registry = MagicMock()
    executor = ExecutorAgent(tool_registry=registry)

    step = {"id": "step-1", "params": {"x": 1}}
    result = await executor.execute(dummy_state, step)

    assert result["step_id"] == "step-1"
    assert result["status"] == "error"
    assert "No action specified" in result["error"]


@pytest.mark.asyncio
async def test_executor_agent_success_with_registry(dummy_state) -> None:
    """Test ExecutorAgent successfully routing a step to the tool registry."""
    registry = AsyncMock()
    # Mock the execute_tool coroutine to return a specific string
    registry.execute_tool.return_value = "Tool execution successful"

    executor = ExecutorAgent(tool_registry=registry)
    step = {"id": "step-2", "action": "search_code", "params": {"query": "foo"}}
    
    result = await executor.execute(dummy_state, step)

    assert result["step_id"] == "step-2"
    assert result["status"] == "success"
    assert result["output"] == "Tool execution successful"
    assert result["error"] is None

    # Verify tool_registry.execute_tool was called with correct arguments
    registry.execute_tool.assert_called_once_with("search_code", {"query": "foo"})


@pytest.mark.asyncio
async def test_executor_agent_handles_registry_exception(dummy_state) -> None:
    """Test ExecutorAgent gracefully catching exceptions raised by the tool registry."""
    registry = AsyncMock()
    registry.execute_tool.side_effect = Exception("Tool exploded")

    executor = ExecutorAgent(tool_registry=registry)
    step = {"id": "step-3", "action": "risky_action", "params": {}}

    result = await executor.execute(dummy_state, step)

    assert result["step_id"] == "step-3"
    assert result["status"] == "error"
    assert result["output"] is None
    assert "Tool exploded" in result["error"]


@pytest.mark.asyncio
async def test_executor_agent_fallback_no_registry(dummy_state) -> None:
    """Test ExecutorAgent fallback behavior when tool registry lacks execute_tool."""
    # A registry object that lacks the execute_tool method
    class EmptyRegistry:
        pass

    executor = ExecutorAgent(tool_registry=EmptyRegistry())
    step = {"id": "step-4", "action": "echo", "params": {"msg": "hello"}}

    result = await executor.execute(dummy_state, step)

    assert result["step_id"] == "step-4"
    assert result["status"] == "success"
    assert "Executed echo" in result["output"]
    assert "{'msg': 'hello'}" in result["output"]
