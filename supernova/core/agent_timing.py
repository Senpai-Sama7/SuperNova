"""Agent response wrapper with timing and background consolidation."""

import asyncio
from typing import Any, Optional

import structlog

from supernova.core.timing import response_timer, background_manager

logger = structlog.get_logger(__name__)


class TimedAgentResponse:
    """Wrapper for agent responses with timing and background tasks."""
    
    def __init__(self, consolidator: Optional[Any] = None, use_celery: bool = True):
        self.consolidator = consolidator
        self.use_celery = use_celery
        self._timer = response_timer
    
    async def __aenter__(self):
        """Start response timing."""
        self._timer.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete timing and schedule background tasks."""
        metrics = self._timer.complete()
        
        # Schedule background consolidation after response
        if self.consolidator is not None:
            if self.use_celery:
                try:
                    from supernova.workers.consolidation import background_consolidate
                    background_consolidate.delay()
                    logger.debug("celery_consolidation_scheduled")
                except ImportError:
                    # Fallback to asyncio if Celery unavailable
                    background_manager.schedule_consolidation(self.consolidator)
            else:
                background_manager.schedule_consolidation(self.consolidator)
    
    def mark_first_token(self):
        """Mark time to first token."""
        self._timer.first_token()


# Convenience function for quick integration
async def timed_response(response_func, consolidator=None, use_celery=True):
    """Execute a response function with timing and background tasks."""
    async with TimedAgentResponse(consolidator, use_celery) as timer:
        # Mark first token when response starts generating
        timer.mark_first_token()
        return await response_func()