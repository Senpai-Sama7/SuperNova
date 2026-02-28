from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class SkillManifest(BaseModel):
    name: str
    description: str
    version: str = "0.1.0"
    author: str = "unknown"
    parameters: dict = {}  # JSON Schema for inputs
    required_permissions: list[str] = []
    risk_level: str = "low"  # low/medium/high/critical

class BaseSkill(ABC):
    manifest: SkillManifest
    
    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the skill with given parameters."""
        ...
    
    def get_schema(self) -> dict:
        return self.manifest.model_dump()