"""Setup progress indicator for SuperNova installation."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SetupProgress:
    """Simple progress indicator for setup steps."""
    
    def __init__(self) -> None:
        """Initialize progress tracker."""
        self.current_step: Optional[str] = None
        
    def start(self, step_name: str) -> None:
        """Start a setup step."""
        self.current_step = step_name
        logger.info(f"🚀 Starting: {step_name}")
        
    def complete(self, step_name: str) -> None:
        """Mark a setup step as complete."""
        logger.info(f"✅ Completed: {step_name}")
        if self.current_step == step_name:
            self.current_step = None
            
    def fail(self, step_name: str, error: str) -> None:
        """Mark a setup step as failed."""
        logger.error(f"❌ Failed: {step_name} - {error}")
        if self.current_step == step_name:
            self.current_step = None