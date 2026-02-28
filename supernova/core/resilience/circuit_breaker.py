import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 60.0, fallback: Callable = None):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback = fallback
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"CircuitBreaker[{self.name}]: half-open, testing recovery")
            elif self.fallback:
                logger.warning(f"CircuitBreaker[{self.name}]: open, using fallback")
                return await self.fallback(*args, **kwargs) if callable(self.fallback) else self.fallback
            else:
                raise CircuitOpenError(f"{self.name} circuit is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"CircuitBreaker[{self.name}]: recovered, closed")
            return result
        except Exception as e:
            self._record_failure()
            if self.fallback:
                return await self.fallback(*args, **kwargs) if callable(self.fallback) else self.fallback
            raise
    
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"CircuitBreaker[{self.name}]: OPEN after {self.failure_count} failures")

class CircuitOpenError(Exception):
    pass