"""supernova/core/agent/shared_state.py

Shared state schema for multi-agent coordination. Defines the data model
for state that needs to be shared between agents during collaborative
task execution.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SharedState(BaseModel):
    """Shared state for multi-agent coordination.
    
    This model defines the structure for state that needs to be shared
    between agents during collaborative task execution.
    """
    
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    user_message: str = Field(..., description="Original user message that initiated the task")
    plan: Optional[List[str]] = Field(None, description="List of execution steps")
    execution_results: Dict[str, str] = Field(default_factory=dict, description="Results keyed by step_id")
    critique: Optional[str] = Field(None, description="Critique or feedback on execution")
    final_response: Optional[str] = Field(None, description="Final response to user")
    memory_context: List[str] = Field(default_factory=list, description="Retrieved memory context")
    active_agents: List[str] = Field(default_factory=list, description="Currently active agent names")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Timestamps, token counts, etc.")