"""Tool-augmented reasoning that combines LLM reasoning with tool execution."""

import re
import logging
from typing import List, Dict, Any
from supernova.core.reasoning.pipeline import ReasoningPipeline
from supernova.infrastructure.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolAugmentedReasoner:
    """Combines reasoning pipeline with tool execution capabilities."""
    
    def __init__(self, reasoning_pipeline: ReasoningPipeline, tool_registry: ToolRegistry):
        self.reasoning = reasoning_pipeline
        self.tools = tool_registry
    
    async def reason_with_tools(self, query: str, context: str, available_tools: List[str]) -> Dict[str, Any]:
        """Reason with tools, invoking them when needed."""
        # Initial reasoning
        initial_result = await self.reasoning.reason(query, context)
        reasoning_text = initial_result["response"]
        
        # Check if reasoning identifies need for tool use
        tool_patterns = [
            r"I need to check",
            r"Let me look up",
            r"I should search",
            r"Let me find",
            r"I need to get"
        ]
        
        needs_tool = any(re.search(pattern, reasoning_text, re.IGNORECASE) for pattern in tool_patterns)
        
        if not needs_tool:
            return initial_result
        
        # Extract potential tool call from reasoning
        tool_call = self._extract_tool_call(reasoning_text, available_tools)
        
        if tool_call:
            try:
                # Execute the tool
                tool_result = await self.tools.execute(tool_call["name"], tool_call["args"])
                
                # Feed result back into reasoning
                enhanced_context = f"{context}\n\nTool Result from {tool_call['name']}: {tool_result}"
                final_result = await self.reasoning.reason(query, enhanced_context)
                
                return {
                    **final_result,
                    "tool_used": tool_call["name"],
                    "tool_result": tool_result,
                    "initial_reasoning": reasoning_text
                }
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return initial_result
        
        return initial_result
    
    def _extract_tool_call(self, text: str, available_tools: List[str]) -> Dict[str, Any]:
        """Extract tool call from reasoning text."""
        # Simple heuristic - look for tool names in text
        for tool_name in available_tools:
            if tool_name.lower() in text.lower():
                return {"name": tool_name, "args": {}}
        return None