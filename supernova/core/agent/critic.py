"""CriticAgent - Reviews execution results before returning to user."""

from __future__ import annotations

import logging
from typing import Any

import litellm

from supernova.config import get_settings
from supernova.core.agent.shared_state import SharedState

logger = logging.getLogger(__name__)


class CriticAgent:
    """Reviews execution results and checks for issues before user response."""
    
    def __init__(self, model: str | None = None):
        settings = get_settings()
        self.model = model or settings.llm.effective_default_model
    
    async def review(self, state: SharedState) -> SharedState:
        """Review execution results and critique quality.
        
        Args:
            state: Current shared state with execution results
            
        Returns:
            Updated state with critique and optionally revised final_response
        """
        try:
            # Build critique prompt
            prompt = self._build_critique_prompt(state)
            
            # Call LLM for critique
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            critique_text = response.choices[0].message.content
            
            # Parse critique for issues
            has_issues = "ISSUES_FOUND" in critique_text
            
            # Update state with critique
            state.critique = critique_text
            
            # If issues found, request revision
            if has_issues and state.final_response:
                revision_prompt = f"Original response: {state.final_response}\n\nCritique: {critique_text}\n\nProvide a revised response:"
                
                revision_response = await litellm.acompletion(
                    model=self.model,
                    messages=[{"role": "user", "content": revision_prompt}],
                    temperature=0.3
                )
                
                state.final_response = revision_response.choices[0].message.content
            
            return state
            
        except Exception as e:
            logger.error(f"Critique failed: {e}")
            state.critique = f"Critique error: {str(e)}"
            return state
    
    def _build_critique_prompt(self, state: SharedState) -> str:
        """Build prompt for critiquing execution results."""
        return f"""Review this task execution for errors, incomplete answers, or hallucination risk:

User Query: {state.user_message}
Execution Results: {state.execution_results}
Final Response: {state.final_response or 'None'}

Check for:
1. Errors in execution
2. Incomplete or missing information
3. Potential hallucinations or inaccuracies

If issues found, start response with "ISSUES_FOUND:" and explain.
If no issues, start with "NO_ISSUES:" and provide brief validation."""