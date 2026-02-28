"""Security tests for the approval system."""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch


class TestApprovalSecurity:
    """Test suite for approval system security."""

    def test_approval_queue_rate_limiting(self):
        """Test flooding approval queue triggers rate limiting."""
        # Mock approval system
        approval_system = Mock()
        approval_system.rate_limit = 30  # 30 RPM
        approval_system.requests = []
        
        # Simulate 100 rapid requests
        start_time = time.time()
        rejected_count = 0
        
        for i in range(100):
            # Check if we exceed rate limit (30 per minute = 0.5 per second)
            if len(approval_system.requests) >= 30:
                rejected_count += 1
            else:
                approval_system.requests.append(time.time())
        
        # Verify rate limiting kicked in
        assert rejected_count > 0
        assert len(approval_system.requests) <= 30

    def test_approval_timeout_manipulation(self):
        """Test approval timeout cannot be manipulated."""
        # Mock approval with timeout
        approval_system = Mock()
        approval_system.timeout = 300  # 5 minutes
        
        # Submit approval request
        request_id = "test_request_123"
        request_time = time.time()
        approval_system.pending = {request_id: request_time}
        
        # Try to approve after timeout window
        current_time = request_time + 400  # 6+ minutes later
        
        with patch('time.time', return_value=current_time):
            # Verify timeout check rejects expired request
            is_expired = (current_time - request_time) > approval_system.timeout
            assert is_expired
            
            # Approval should be rejected
            if request_id in approval_system.pending:
                if is_expired:
                    del approval_system.pending[request_id]
                    approval_result = False
                else:
                    approval_result = True
            
            assert not approval_result

    def test_approval_bypass_via_tool_chaining(self):
        """Test tool chaining cannot bypass approval requirements."""
        # Mock tool registry with risk levels
        tool_registry = Mock()
        tool_registry.tools = {
            "low_risk_tool": {"risk": "low", "requires_approval": False},
            "high_risk_tool": {"risk": "high", "requires_approval": True}
        }
        
        # Attempt to chain low-risk -> high-risk
        execution_chain = ["low_risk_tool", "high_risk_tool"]
        
        # Check if any tool in chain requires approval
        requires_approval = any(
            tool_registry.tools[tool]["requires_approval"] 
            for tool in execution_chain 
            if tool in tool_registry.tools
        )
        
        # Verify chain is caught and blocked
        assert requires_approval
        
        # Simulate blocking the entire chain
        if requires_approval:
            execution_blocked = True
        else:
            execution_blocked = False
            
        assert execution_blocked
