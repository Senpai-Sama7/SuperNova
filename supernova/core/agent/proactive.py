"""ProactiveAgent for detecting opportunities and providing intelligent nudges."""

from __future__ import annotations

import re
from typing import Any

import litellm

from supernova.config import get_settings


class ProactiveAgent:
    """Detects opportunities for proactive suggestions and follow-ups."""
    
    def __init__(self, config: dict = None):
        settings = get_settings()
        self.model = settings.llm.effective_default_model
        self.feedback_data = {}  # nudge_type -> {"accepted": int, "rejected": int}
        
    async def detect_opportunities(self, context: dict) -> list[dict]:
        """Analyze conversation context for proactive suggestions."""
        messages = context.get("messages", [])
        if not messages:
            return []
            
        opportunities = []
        
        # Detect incomplete tasks
        last_msg = messages[-1].get("content", "")
        if any(word in last_msg.lower() for word in ["todo", "later", "remind", "incomplete"]):
            opportunities.append({
                "type": "incomplete_task",
                "suggestion": "Would you like me to help complete this task or set a reminder?",
                "confidence": 0.8
            })
            
        # Detect unanswered questions
        question_patterns = [r'\?[^?]*$', r'\bwhat\b', r'\bhow\b', r'\bwhy\b', r'\bwhen\b']
        if any(re.search(pattern, last_msg, re.IGNORECASE) for pattern in question_patterns):
            opportunities.append({
                "type": "unanswered_question", 
                "suggestion": "I notice there might be an unanswered question. Can I help clarify?",
                "confidence": 0.75
            })
            
        # Detect follow-up opportunities
        if len(messages) >= 2:
            followups = await self.detect_followups(messages[-3:])
            opportunities.extend(followups)
            
        return opportunities
        
    def filter_nudges(self, opportunities: list[dict], threshold: float = 0.7) -> list[dict]:
        """Filter opportunities by confidence threshold."""
        return [opp for opp in opportunities if opp.get("confidence", 0) >= threshold]
        
    async def detect_followups(self, messages: list[dict]) -> list[dict]:
        """Detect when questions were partially answered or topics dropped."""
        if len(messages) < 2:
            return []
            
        followups = []
        
        for i in range(len(messages) - 1):
            msg = messages[i].get("content", "")
            next_msg = messages[i + 1].get("content", "")
            
            # Check for question words in message
            question_words = ["what", "how", "why", "when", "where", "which"]
            has_question = any(word in msg.lower() for word in question_words)
            
            # Simple heuristic: if question asked but response is very short
            if has_question and len(next_msg.split()) < 10:
                followups.append({
                    "type": "partial_answer",
                    "suggestion": "The previous response seems brief. Would you like more detail?",
                    "confidence": 0.72
                })
                
        return followups
        
    def record_feedback(self, nudge_id: str, accepted: bool):
        """Record user feedback on nudges to adjust confidence over time."""
        nudge_type = nudge_id.split("_")[0]  # Extract type from ID
        
        if nudge_type not in self.feedback_data:
            self.feedback_data[nudge_type] = {"accepted": 0, "rejected": 0}
            
        if accepted:
            self.feedback_data[nudge_type]["accepted"] += 1
        else:
            self.feedback_data[nudge_type]["rejected"] += 1
            
    def get_adjusted_confidence(self, nudge_type: str, base_confidence: float) -> float:
        """Adjust confidence based on historical feedback."""
        if nudge_type not in self.feedback_data:
            return base_confidence
            
        data = self.feedback_data[nudge_type]
        total = data["accepted"] + data["rejected"]
        
        if total == 0:
            return base_confidence
            
        acceptance_rate = data["accepted"] / total
        # Adjust confidence based on acceptance rate
        adjustment = (acceptance_rate - 0.5) * 0.2  # Max ±0.1 adjustment
        return max(0.0, min(1.0, base_confidence + adjustment))