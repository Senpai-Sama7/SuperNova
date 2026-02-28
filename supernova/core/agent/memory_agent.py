"""MemoryAgent - Background agent for extracting and storing conversation facts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import litellm
from supernova.core.agent.shared_state import SharedState

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Background agent that extracts key facts and manages memory consolidation."""
    
    def __init__(self, memory_store: Any = None, model: str = "gpt-4o-mini", consolidation_threshold: int = 50):
        self.memory_store = memory_store
        self.model = model
        self.consolidation_threshold = consolidation_threshold
    
    async def process(self, state: SharedState) -> None:
        """Extract key facts from conversation and store to memory.
        
        Args:
            state: Current shared state
            
        Note:
            Fire-and-forget background processing, no return value
        """
        try:
            # Extract key facts from conversation
            facts = await self._extract_facts(state)
            
            if facts and self.memory_store:
                # Store facts to memory
                await self._store_facts(facts)
                
                # Check if consolidation needed
                memory_count = await self._get_memory_count()
                if memory_count > self.consolidation_threshold:
                    asyncio.create_task(self._consolidate_memory())
                    
        except Exception as e:
            logger.error(f"Memory processing failed: {e}")
    
    async def _extract_facts(self, state: SharedState) -> list[str]:
        """Extract key facts from the conversation."""
        prompt = f"""Extract key facts from this conversation that should be remembered:

User: {state.user_message}
Results: {state.execution_results}
Response: {state.final_response or 'None'}

Return only important, factual information as a JSON list of strings.
Focus on: user preferences, discovered information, successful solutions.
Exclude: temporary states, error messages, routine confirmations."""

        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            facts_text = response.choices[0].message.content
            return json.loads(facts_text) if facts_text.startswith('[') else []
            
        except Exception as e:
            logger.error(f"Fact extraction failed: {e}")
            return []
    
    async def _store_facts(self, facts: list[str]) -> None:
        """Store facts to memory store."""
        if hasattr(self.memory_store, 'store_facts'):
            await self.memory_store.store_facts(facts)
    
    async def _get_memory_count(self) -> int:
        """Get current memory count."""
        if hasattr(self.memory_store, 'count'):
            return await self.memory_store.count()
        return 0
    
    async def _consolidate_memory(self) -> None:
        """Consolidate memory when threshold exceeded."""
        if hasattr(self.memory_store, 'consolidate'):
            await self.memory_store.consolidate()