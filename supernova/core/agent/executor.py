"""ExecutorAgent - Executes individual plan steps with tool access."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from supernova.core.agent.shared_state import SharedState

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """Executes individual plan steps with tool registry access."""
    
    def __init__(self, tool_registry: Any):
        self.tool_registry = tool_registry
    
    async def execute(self, state: SharedState, step: dict) -> dict:
        """Execute a single plan step.
        
        Args:
            state: Current shared state
            step: Step dict with {id, action, params}
            
        Returns:
            Result dict with {step_id, status, output, error}
        """
        step_id = step.get("id", "unknown")
        
        try:
            action = step.get("action")
            params = step.get("params", {})
            
            if not action:
                return {
                    "step_id": step_id,
                    "status": "error", 
                    "output": None,
                    "error": "No action specified"
                }
            
            # Execute tool call if available
            if hasattr(self.tool_registry, 'execute_tool'):
                output = await self.tool_registry.execute_tool(action, params)
            else:
                # Fallback for simple actions
                output = f"Executed {action} with params {params}"
            
            return {
                "step_id": step_id,
                "status": "success",
                "output": output,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Execution failed for step {step_id}: {e}")
            return {
                "step_id": step_id,
                "status": "error",
                "output": None,
                "error": str(e)
            }