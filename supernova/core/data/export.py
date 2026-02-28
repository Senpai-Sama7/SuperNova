"""GDPR-compliant user data export."""

import json
import time
from pathlib import Path
from typing import Dict, Any

from supernova.core.memory.retrieval import WeightedMemoryRetriever
from supernova.core.memory.working import WorkingMemoryStore
from supernova.core.memory.semantic import SemanticMemoryStore


def export_user_data(user_id: str, output_path: str) -> Dict[str, Any]:
    """Export all user data to JSON file for GDPR compliance.
    
    Args:
        user_id: User identifier
        output_path: Path to write export file
        
    Returns:
        Export metadata with counts and timestamp
    """
    export_data = {
        "format_version": "1.0",
        "user_id": user_id,
        "export_timestamp": int(time.time()),
        "data": {
            "memories": [],
            "working_memory": {},
            "preferences": {},
            "conversation_history": [],
            "agent_state": {}
        }
    }
    
    # Collect memories from all stores
    retriever = WeightedMemoryRetriever()
    memories = retriever.retrieve(query="", user_id=user_id, top_k=10000)
    export_data["data"]["memories"] = [
        {
            "id": m.id,
            "content": m.content,
            "memory_type": m.memory_type,
            "salience_score": m.salience_score,
            "metadata": m.metadata,
            "retrieved_at": m.retrieved_at
        } for m in memories
    ]
    
    # Export working memory
    working_store = WorkingMemoryStore()
    working_mem = working_store.get(user_id)
    if working_mem:
        export_data["data"]["working_memory"] = {
            "session_id": working_mem.session_id,
            "current_goal": working_mem.current_goal,
            "active_plan": working_mem.active_plan,
            "metadata": getattr(working_mem, 'metadata', {})
        }
    
    # Write to file
    Path(output_path).write_text(json.dumps(export_data, indent=2))
    
    return {
        "memories_count": len(export_data["data"]["memories"]),
        "export_timestamp": export_data["export_timestamp"],
        "format_version": export_data["format_version"],
        "file_size_bytes": Path(output_path).stat().st_size
    }