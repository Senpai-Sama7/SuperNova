"""PlannerAgent for task decomposition and planning."""

from __future__ import annotations

import litellm

from supernova.config import get_settings

from .shared_state import SharedState


class PlannerAgent:
    """Breaks down complex tasks into numbered execution steps."""
    
    def __init__(self):
        self.system_prompt = """You are a task planning specialist. Break down user requests into clear, numbered steps.

Rules:
- Create 3-7 concrete, actionable steps
- Each step should be specific and measurable
- Steps should be in logical execution order
- Focus on what needs to be done, not how to do it
- Return only the numbered list, no extra text

Example:
1. Analyze the current codebase structure
2. Identify missing components
3. Design the new module interface
4. Implement core functionality
5. Add error handling and validation
6. Write unit tests
7. Update documentation"""
    
    async def plan(self, state: SharedState) -> SharedState:
        """Generate execution plan for the user message."""
        prompt = f"Break down this task into steps:\n\n{state.user_message}"
        
        settings = get_settings()
        response = await litellm.acompletion(
            model=settings.llm.effective_default_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        plan_text = response.choices[0].message.content.strip()
        
        # Parse numbered steps
        steps = []
        for line in plan_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('- ')):
                # Remove numbering and clean up
                step = line.split('.', 1)[-1].strip() if '.' in line else line.lstrip('- ').strip()
                if step:
                    steps.append(step)
        
        state.plan = steps
        return state