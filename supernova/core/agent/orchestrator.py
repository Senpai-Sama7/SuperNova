"""OrchestratorAgent for coordinating multi-agent task execution."""

from __future__ import annotations

import uuid
from typing import List

import litellm

from .shared_state import SharedState


class OrchestratorAgent:
    """Coordinates multi-agent task execution based on query complexity."""
    
    def __init__(self):
        self.planning_keywords = {
            "plan", "steps", "break down", "organize", "structure", 
            "multi-step", "complex", "workflow", "process"
        }
    
    async def process(self, user_message: str, context: dict = None) -> str:
        """Process user message through appropriate agent coordination."""
        # Create shared state
        state = SharedState(
            conversation_id=str(uuid.uuid4()),
            user_message=user_message,
            metadata={"context": str(context or {})}
        )
        
        # Classify task and determine required agents
        required_agents = self._classify_task(user_message)
        state.active_agents = required_agents
        
        # Execute agent pipeline
        if "planner" in required_agents:
            from .planner import PlannerAgent
            planner = PlannerAgent()
            state = await planner.plan(state)
        
        # Always add critic for review
        state.critique = await self._critique_results(state)
        
        # Generate final response
        state.final_response = await self._generate_response(state)
        
        return state.final_response
    
    def _classify_task(self, message: str) -> List[str]:
        """Classify task complexity and return required agent list."""
        message_lower = message.lower()
        
        # Check for planning indicators
        needs_planning = any(keyword in message_lower for keyword in self.planning_keywords)
        
        if needs_planning:
            return ["planner", "executor", "critic"]
        else:
            return ["executor", "critic"]
    
    async def _critique_results(self, state: SharedState) -> str:
        """Generate critique of execution results."""
        prompt = f"""Review this task execution:
User Request: {state.user_message}
Plan: {state.plan or 'No plan generated'}
Results: {state.execution_results}

Provide brief critique focusing on completeness and accuracy."""
        
        response = await litellm.acompletion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    
    async def _generate_response(self, state: SharedState) -> str:
        """Generate final response to user."""
        if state.execution_results:
            return f"Task completed. Results: {list(state.execution_results.values())[0]}"
        elif state.plan:
            return f"Plan created with {len(state.plan)} steps: {'; '.join(state.plan[:3])}..."
        else:
            return "Task processed successfully."