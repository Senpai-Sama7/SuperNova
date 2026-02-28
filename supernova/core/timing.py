"""Response timing and background task management for Phase 18."""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Response timing metrics
_response_times: List[Dict[str, float]] = []
_MAX_RESPONSE_METRICS = 500


class ResponseTimer:
    """Track response latency metrics."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.first_token_time: Optional[float] = None
    
    def start(self) -> None:
        """Start timing a response."""
        self.start_time = time.monotonic()
    
    def first_token(self) -> None:
        """Mark time to first token."""
        if self.start_time is not None:
            self.first_token_time = time.monotonic()
    
    def complete(self) -> Dict[str, float]:
        """Complete timing and return metrics."""
        if self.start_time is None:
            return {}
        
        end_time = time.monotonic()
        total_time = end_time - self.start_time
        
        metrics = {
            "total_response_time": total_time,
            "timestamp": end_time
        }
        
        if self.first_token_time is not None:
            metrics["time_to_first_token"] = self.first_token_time - self.start_time
        
        # Store metrics
        _response_times.append(metrics)
        if len(_response_times) > _MAX_RESPONSE_METRICS:
            _response_times.pop(0)
        
        # Log every 5 responses
        if len(_response_times) % 5 == 0:
            self._log_response_metrics()
        
        logger.debug("response_timing", **{k: v*1000 for k, v in metrics.items() if k != "timestamp"})
        return metrics
    
    def _log_response_metrics(self) -> None:
        """Log p50/p95 response metrics."""
        if not _response_times:
            return
        
        total_times = [m["total_response_time"] for m in _response_times]
        ttft_times = [m["time_to_first_token"] for m in _response_times if "time_to_first_token" in m]
        
        total_sorted = sorted(total_times)
        n = len(total_sorted)
        total_p50 = total_sorted[int(n * 0.5)] * 1000
        total_p95 = total_sorted[int(n * 0.95)] * 1000
        
        metrics = {
            "total_p50_ms": total_p50,
            "total_p95_ms": total_p95,
            "samples": n
        }
        
        if ttft_times:
            ttft_sorted = sorted(ttft_times)
            ttft_n = len(ttft_sorted)
            metrics["ttft_p50_ms"] = ttft_sorted[int(ttft_n * 0.5)] * 1000
            metrics["ttft_p95_ms"] = ttft_sorted[int(ttft_n * 0.95)] * 1000
        
        logger.info("response_latency", **metrics)


class BackgroundTaskManager:
    """Manage background consolidation tasks."""
    
    def __init__(self):
        self._tasks: List[asyncio.Task] = []
    
    def schedule_consolidation(self, consolidator: Any, query: str = "recent events") -> None:
        """Schedule memory consolidation as background task."""
        task = asyncio.create_task(self._run_consolidation(consolidator, query))
        self._tasks.append(task)
        
        # Clean up completed tasks
        self._tasks = [t for t in self._tasks if not t.done()]
        
        logger.debug("background_consolidation_scheduled", active_tasks=len(self._tasks))
    
    async def _run_consolidation(self, consolidator: Any, query: str) -> None:
        """Run consolidation in background."""
        try:
            start_time = time.monotonic()
            records = await consolidator.consolidate(query)
            elapsed = time.monotonic() - start_time
            
            logger.info("background_consolidation_complete", 
                       records=len(records), elapsed_ms=elapsed*1000)
        except Exception as exc:
            logger.error("background_consolidation_failed", error=str(exc))
    
    def get_active_count(self) -> int:
        """Get number of active background tasks."""
        self._tasks = [t for t in self._tasks if not t.done()]
        return len(self._tasks)


# Global instances
response_timer = ResponseTimer()
background_manager = BackgroundTaskManager()