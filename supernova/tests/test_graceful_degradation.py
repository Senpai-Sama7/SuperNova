"""Test graceful degradation when circuit breakers are open."""

import pytest
from unittest.mock import AsyncMock
from supernova.core.resilience.circuit_breaker import CircuitBreaker, CircuitState

class TestGracefulDegradation:
    """Test system behavior when circuit breakers are open."""
    
    @pytest.mark.asyncio
    async def test_llm_breaker_open_returns_fallback(self):
        """Test that open LLM circuit breaker returns fallback message."""
        # Mock fallback function
        async def fallback_response(*args, **kwargs):
            return "I'm currently experiencing technical difficulties. Please try again later."
        
        # Create circuit breaker with fallback
        breaker = CircuitBreaker(
            name="llm_service",
            failure_threshold=1,
            fallback=fallback_response
        )
        
        # Mock failing LLM function
        async def failing_llm(*args, **kwargs):
            raise Exception("LLM service unavailable")
        
        # Trigger failure to open circuit
        try:
            await breaker.call(failing_llm)
        except Exception:
            pass
        
        # Verify circuit is open
        assert breaker.state == CircuitState.OPEN
        
        # Call should return fallback instead of crashing
        result = await breaker.call(failing_llm)
        assert result == "I'm currently experiencing technical difficulties. Please try again later."
    
    @pytest.mark.asyncio
    async def test_tool_breaker_open_returns_cached_result(self):
        """Test that open tool circuit breaker returns cached result."""
        cached_result = {"status": "cached", "data": "Previous successful result"}
        
        async def cache_fallback(*args, **kwargs):
            return cached_result
        
        breaker = CircuitBreaker(
            name="tool_service", 
            failure_threshold=1,
            fallback=cache_fallback
        )
        
        async def failing_tool(*args, **kwargs):
            raise Exception("Tool service down")
        
        # Open the circuit
        try:
            await breaker.call(failing_tool)
        except Exception:
            pass
        
        assert breaker.state == CircuitState.OPEN
        
        # Should return cached result
        result = await breaker.call(failing_tool)
        assert result == cached_result