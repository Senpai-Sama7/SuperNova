from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ReasoningDepth(str, Enum):
    FAST = "fast"          # Single LLM call
    STANDARD = "standard"  # think → respond
    DEEP = "deep"          # think → draft → critique → revise

class ReasoningPipeline:
    def __init__(self, llm_router):
        self.llm = llm_router
    
    async def reason(self, query: str, context: str = "", depth: ReasoningDepth = ReasoningDepth.FAST) -> dict:
        if depth == ReasoningDepth.FAST:
            return await self._fast(query, context)
        elif depth == ReasoningDepth.STANDARD:
            return await self._standard(query, context)
        return await self._deep(query, context)
    
    async def _fast(self, query, context) -> dict:
        # Single call
        messages = [{"role": "user", "content": f"{context}\n\nUser: {query}"}]
        response = await self.llm.route_task("fast", messages)
        return {"response": response.content, "depth": "fast", "passes": 1}
    
    async def _standard(self, query, context) -> dict:
        # think → respond
        think_messages = [{"role": "user", "content": f"Think step by step about: {query}\nContext: {context}\nProvide your reasoning."}]
        thinking = await self.llm.route_task("planning", think_messages)
        
        respond_messages = [{"role": "user", "content": f"Based on this reasoning:\n{thinking.content}\n\nProvide a clear response to: {query}"}]
        response = await self.llm.route_task("smart", respond_messages)
        
        return {"response": response.content, "thinking": thinking.content, "depth": "standard", "passes": 2}
    
    async def _deep(self, query, context) -> dict:
        # think → draft → critique → revise
        think_messages = [{"role": "user", "content": f"Think step by step about: {query}\nContext: {context}"}]
        thinking = await self.llm.route_task("planning", think_messages)
        
        draft_messages = [{"role": "user", "content": f"Based on reasoning:\n{thinking.content}\n\nDraft a response to: {query}"}]
        draft = await self.llm.route_task("smart", draft_messages)
        
        critique_messages = [{"role": "user", "content": f"Critique this draft for errors, gaps, and improvements:\n{draft.content}"}]
        critique = await self.llm.route_task("reflection", critique_messages)
        
        final_messages = [{"role": "user", "content": f"Revise this draft based on critique:\nDraft: {draft.content}\nCritique: {critique.content}\nProvide improved final response."}]
        final = await self.llm.route_task("smart", final_messages)
        
        return {"response": final.content, "thinking": thinking.content, "draft": draft.content, "critique": critique.content, "depth": "deep", "passes": 4}