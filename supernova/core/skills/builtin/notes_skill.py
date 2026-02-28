import json
import os
from datetime import datetime
from typing import Any
from supernova.core.skills.base import BaseSkill, SkillManifest

class NotesSkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="notes",
            description="Create, search, and list text notes",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "list", "search"]},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "query": {"type": "string"}
                },
                "required": ["action"]
            }
        )
        self.notes_file = "data/notes.json"
    
    def _load_notes(self) -> list:
        os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
        if os.path.exists(self.notes_file):
            with open(self.notes_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_notes(self, notes: list):
        with open(self.notes_file, 'w') as f:
            json.dump(notes, f, indent=2)
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params["action"]
        
        if action == "create":
            note = {
                "id": len(self._load_notes()) + 1,
                "title": params.get("title", "Untitled"),
                "content": params.get("content", ""),
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat()
            }
            
            notes = self._load_notes()
            notes.append(note)
            self._save_notes(notes)
            
            return {"note_created": note}
        
        elif action == "list":
            notes = self._load_notes()
            return {"notes": notes, "count": len(notes)}
        
        elif action == "search":
            query = params.get("query", "").lower()
            notes = self._load_notes()
            matches = [
                note for note in notes
                if query in note["title"].lower() or query in note["content"].lower()
            ]
            return {"matches": matches, "count": len(matches)}