"""User data import from export format."""

import json
from pathlib import Path
from typing import Dict, Any

from supernova.core.memory.working import WorkingMemoryStore, WorkingMemory
from supernova.core.memory.semantic import SemanticMemoryStore


def import_user_data(input_path: str, user_id: str) -> Dict[str, Any]:
    """Import user data from export JSON file.
    
    Args:
        input_path: Path to export file
        user_id: Target user identifier
        
    Returns:
        Import results with counts and validation status
    """
    data = json.loads(Path(input_path).read_text())
    
    # Validate schema
    required_fields = ["format_version", "user_id", "data"]
    if not all(field in data for field in required_fields):
        raise ValueError(f"Invalid export format, missing: {required_fields}")
    
    if data["format_version"] != "1.0":
        raise ValueError(f"Unsupported format version: {data['format_version']}")
    
    imported_counts = {"memories": 0, "working_memory": 0, "preferences": 0}
    
    # Import memories
    if "memories" in data["data"]:
        semantic_store = SemanticMemoryStore()
        for memory in data["data"]["memories"]:
            semantic_store.store(
                content=memory["content"],
                memory_type=memory["memory_type"],
                user_id=user_id,
                metadata=memory.get("metadata", {})
            )
            imported_counts["memories"] += 1
    
    # Import working memory
    if "working_memory" in data["data"] and data["data"]["working_memory"]:
        working_store = WorkingMemoryStore()
        wm_data = data["data"]["working_memory"]
        working_mem = WorkingMemory(
            session_id=wm_data.get("session_id", user_id),
            current_goal=wm_data.get("current_goal", ""),
            active_plan=wm_data.get("active_plan", [])
        )
        working_store.store(user_id, working_mem)
        imported_counts["working_memory"] = 1
    
    return {
        "imported_counts": imported_counts,
        "source_user": data["user_id"],
        "target_user": user_id,
        "format_version": data["format_version"]
    }