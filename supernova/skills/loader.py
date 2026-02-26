"""Skill loader with hot-reloading, prompt conversion, and registry."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """A loaded skill with metadata and content."""
    name: str
    description: str
    content: str
    path: Path
    mtime: float = 0.0


class SkillLoader:
    """Discovers, loads, and hot-reloads skills from a directory."""

    def __init__(self, skills_dir: str | Path) -> None:
        self._dir = Path(skills_dir)
        self._skills: dict[str, Skill] = {}
        self._active: set[str] = set()
        self._debounce_s = 0.5

    def discover(self) -> list[Skill]:
        """Scan skills directory for .skill files and SKILL.md in subdirs."""
        found: list[Skill] = []
        if not self._dir.exists():
            logger.warning("Skills directory not found: %s", self._dir)
            return found

        # .skill files at root level
        for p in self._dir.glob("*.skill"):
            skill = self._parse_skill(p)
            if skill:
                found.append(skill)

        # SKILL.md in subdirectories
        for p in self._dir.glob("*/SKILL.md"):
            skill = self._parse_skill(p)
            if skill:
                found.append(skill)

        for s in found:
            self._skills[s.name] = s
        logger.info("Discovered %d skills", len(found))
        return found

    def _parse_skill(self, path: Path) -> Skill | None:
        """Parse a skill file with YAML frontmatter."""
        try:
            text = path.read_text(encoding="utf-8")
            name, description, content = "", "", text
            # Parse YAML frontmatter
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].strip().splitlines():
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("description:"):
                            description = line.split(":", 1)[1].strip()
                    content = parts[2].strip()
            if not name:
                name = path.stem if path.suffix == ".skill" else path.parent.name
            return Skill(
                name=name, description=description, content=content,
                path=path, mtime=path.stat().st_mtime,
            )
        except Exception as e:
            logger.error("Failed to parse skill %s: %s", path, e)
            return None

    def reload_changed(self) -> list[str]:
        """Check for modified skill files and reload them. Returns changed names."""
        changed: list[str] = []
        for name, skill in list(self._skills.items()):
            try:
                mtime = skill.path.stat().st_mtime
                if mtime > skill.mtime + self._debounce_s:
                    reloaded = self._parse_skill(skill.path)
                    if reloaded:
                        self._skills[name] = reloaded
                        changed.append(name)
                        logger.info("Reloaded skill: %s", name)
            except FileNotFoundError:
                del self._skills[name]
                self._active.discard(name)
                changed.append(name)
        return changed

    def to_prompt(self, skill_name: str) -> str:
        """Convert a skill to a system prompt addition."""
        skill = self._skills.get(skill_name)
        if not skill:
            return ""
        return f"<skill name=\"{skill.name}\">\n{skill.content}\n</skill>"

    def get_active_prompts(self) -> str:
        """Get combined prompt text for all active skills."""
        parts = [self.to_prompt(n) for n in self._active if n in self._skills]
        return "\n\n".join(parts)

    def activate(self, name: str) -> bool:
        """Activate a skill for the current session."""
        if name not in self._skills:
            return False
        self._active.add(name)
        return True

    def deactivate(self, name: str) -> None:
        """Deactivate a skill."""
        self._active.discard(name)

    def list_skills(self) -> list[dict[str, Any]]:
        """Return metadata for all discovered skills."""
        return [
            {"name": s.name, "description": s.description, "active": s.name in self._active}
            for s in self._skills.values()
        ]

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)
