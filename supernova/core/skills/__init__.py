"""SuperNova Skills Framework

Minimal skill base framework where:
- BaseSkill handles auth, permissions, sandboxing, logging
- New skills only implement execute()
"""

from .base import BaseSkill, SkillManifest
from .sandbox import sandboxed_execute

__all__ = ["BaseSkill", "SkillManifest", "sandboxed_execute"]