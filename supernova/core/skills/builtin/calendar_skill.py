import json
import os
from datetime import datetime, timedelta
from typing import Any
from supernova.core.skills.base import BaseSkill, SkillManifest

class CalendarSkill(BaseSkill):
    def __init__(self):
        self.manifest = SkillManifest(
            name="calendar",
            description="Create and manage calendar events",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "list"]},
                    "title": {"type": "string"},
                    "start": {"type": "string", "format": "date-time"},
                    "duration_hours": {"type": "number", "default": 1}
                },
                "required": ["action"]
            }
        )
        self.events_file = "data/calendar_events.json"
    
    def _load_events(self) -> list:
        os.makedirs(os.path.dirname(self.events_file), exist_ok=True)
        if os.path.exists(self.events_file):
            with open(self.events_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_events(self, events: list):
        with open(self.events_file, 'w') as f:
            json.dump(events, f, indent=2)
    
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params["action"]
        
        if action == "create":
            title = params.get("title", "Untitled Event")
            start = datetime.fromisoformat(params["start"])
            duration = params.get("duration_hours", 1)
            end = start + timedelta(hours=duration)
            
            event = {
                "id": len(self._load_events()) + 1,
                "title": title,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "created": datetime.now().isoformat()
            }
            
            events = self._load_events()
            events.append(event)
            self._save_events(events)
            
            return {"event_created": event}
        
        elif action == "list":
            events = self._load_events()
            return {"events": events, "count": len(events)}