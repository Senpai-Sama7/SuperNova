"""Working memory implementation for SuperNova.

Provides WorkingMemory dataclass and WorkingMemoryStore for managing
ephemeral agent state with Redis-backed persistence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from supernova.infrastructure.storage.redis import AsyncRedisClient, get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class WorkingMemory:
    """Working memory for an agent session.
    
    Represents the ephemeral state of an agent during a conversation,
    including current goals, plans, tool results, and attention stack.
    
    Attributes:
        session_id: Unique session identifier.
        current_goal: Current high-level goal.
        active_plan: List of planned steps.
        tool_results_buffer: Recent tool execution results.
        attention_stack: Stack of attention contexts.
        scratchpad: Free-form notes.
        last_updated: Timestamp of last update.
    """
    session_id: str
    current_goal: str = ""
    active_plan: list[str] = field(default_factory=list)
    tool_results_buffer: list[dict[str, Any]] = field(default_factory=list)
    attention_stack: list[str] = field(default_factory=list)
    scratchpad: str = ""
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "current_goal": self.current_goal,
            "active_plan": self.active_plan,
            "tool_results_buffer": self.tool_results_buffer,
            "attention_stack": self.attention_stack,
            "scratchpad": self.scratchpad,
            "last_updated": self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkingMemory:
        """Create from dictionary."""
        # Parse timestamp if present
        last_updated = datetime.utcnow()
        if "last_updated" in data:
            try:
                last_updated = datetime.fromisoformat(data["last_updated"])
            except (ValueError, TypeError):
                pass
        
        return cls(
            session_id=data.get("session_id", ""),
            current_goal=data.get("current_goal", ""),
            active_plan=data.get("active_plan", []),
            tool_results_buffer=data.get("tool_results_buffer", []),
            attention_stack=data.get("attention_stack", []),
            scratchpad=data.get("scratchpad", ""),
            last_updated=last_updated,
        )


class WorkingMemoryStore:
    """Store for working memory.
    
    Provides CRUD operations for WorkingMemory with Redis backend.
    Uses msgpack serialization for efficient storage.
    
    Example:
        >>> store = WorkingMemoryStore()
        >>> memory = WorkingMemory(session_id="123", current_goal="test")
        >>> await store.set(memory)
        >>> retrieved = await store.get("123")
    """
    
    def __init__(self, redis_client: Optional[AsyncRedisClient] = None) -> None:
        """Initialize the store.
        
        Args:
            redis_client: Redis client. If None, uses global client.
        """
        self._redis = redis_client
    
    async def _get_redis(self) -> AsyncRedisClient:
        """Get Redis client, initializing if needed."""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    async def get(self, session_id: str) -> Optional[WorkingMemory]:
        """Get working memory for a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            WorkingMemory or None if not found.
        """
        try:
            redis = await self._get_redis()
            data = await redis.working_memory_get(session_id)
            
            if data is None:
                return None
            
            return WorkingMemory.from_dict(data)
        except Exception as e:
            logger.error(f"Error getting working memory for {session_id}: {e}")
            return None
    
    async def set(
        self, 
        memory: WorkingMemory, 
        ttl: Optional[int] = None
    ) -> None:
        """Store working memory.
        
        Args:
            memory: WorkingMemory to store.
            ttl: TTL in seconds. Uses default if not specified.
        """
        try:
            redis = await self._get_redis()
            memory.last_updated = datetime.utcnow()
            await redis.working_memory_set(
                memory.session_id, 
                memory.to_dict(),
                ttl=ttl
            )
        except Exception as e:
            logger.error(f"Error setting working memory for {memory.session_id}: {e}")
            raise
    
    async def delete(self, session_id: str) -> None:
        """Delete working memory.
        
        Args:
            session_id: Session identifier.
        """
        try:
            redis = await self._get_redis()
            await redis.working_memory_delete(session_id)
        except Exception as e:
            logger.error(f"Error deleting working memory for {session_id}: {e}")
            raise
    
    async def exists(self, session_id: str) -> bool:
        """Check if working memory exists.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if exists.
        """
        try:
            redis = await self._get_redis()
            return await redis.working_memory_exists(session_id)
        except Exception as e:
            logger.error(f"Error checking working memory for {session_id}: {e}")
            return False
    
    async def update_field(
        self,
        session_id: str,
        field: str,
        value: Any,
    ) -> None:
        """Update a single field without rewriting entire object.
        
        This performs a partial update by fetching, modifying, and storing.
        For true atomic updates, use Redis hash operations (not implemented).
        
        Args:
            session_id: Session identifier.
            field: Field name to update.
            value: New value.
        """
        try:
            # Get current memory
            memory = await self.get(session_id)
            if memory is None:
                # Create new if doesn't exist
                memory = WorkingMemory(session_id=session_id)
            
            # Update field
            if hasattr(memory, field):
                setattr(memory, field, value)
            else:
                raise ValueError(f"Invalid field: {field}")
            
            # Store back
            await self.set(memory)
        except Exception as e:
            logger.error(f"Error updating field {field} for {session_id}: {e}")
            raise
    
    async def append_to_field(
        self,
        session_id: str,
        field: str,
        value: Any,
    ) -> None:
        """Append to a list field.
        
        Args:
            session_id: Session identifier.
            field: List field name (e.g., 'active_plan', 'tool_results_buffer').
            value: Value to append.
        """
        try:
            memory = await self.get(session_id)
            if memory is None:
                memory = WorkingMemory(session_id=session_id)
            
            current = getattr(memory, field, None)
            if not isinstance(current, list):
                raise ValueError(f"Field {field} is not a list")
            
            current.append(value)
            await self.set(memory)
        except Exception as e:
            logger.error(f"Error appending to field {field} for {session_id}: {e}")
            raise


# Global store instance
_store_instance: Optional[WorkingMemoryStore] = None


async def get_working_memory_store() -> WorkingMemoryStore:
    """Get or create the global WorkingMemoryStore.
    
    Returns:
        WorkingMemoryStore instance.
    """
    global _store_instance
    if _store_instance is None:
        _store_instance = WorkingMemoryStore()
    return _store_instance
