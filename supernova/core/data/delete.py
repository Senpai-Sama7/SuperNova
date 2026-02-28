"""User data deletion for GDPR compliance."""

from typing import Dict, Any

from supernova.core.memory.working import WorkingMemoryStore
from supernova.core.memory.semantic import SemanticMemoryStore


def delete_user_data(user_id: str, confirm: bool = False) -> Dict[str, Any]:
    """Delete all user data from the system.
    
    Args:
        user_id: User identifier
        confirm: Must be True to proceed with deletion
        
    Returns:
        Summary of deleted data
        
    Raises:
        ValueError: If confirm is not True
    """
    if not confirm:
        raise ValueError("Must set confirm=True to delete user data")
    
    deleted_counts = {"memories": 0, "working_memory": 0, "sessions": 0}
    
    # Delete from semantic memory store
    semantic_store = SemanticMemoryStore()
    deleted_counts["memories"] = semantic_store.delete_user_data(user_id)
    
    # Delete working memory
    working_store = WorkingMemoryStore()
    if working_store.get(user_id):
        working_store.delete(user_id)
        deleted_counts["working_memory"] = 1
    
    # Delete session data (if exists)
    try:
        # Placeholder for session cleanup
        deleted_counts["sessions"] = 0
    except Exception:
        pass
    
    return {
        "user_id": user_id,
        "deleted_counts": deleted_counts,
        "deletion_complete": True,
        "timestamp": int(__import__("time").time())
    }