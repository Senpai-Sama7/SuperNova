"""Tests for Skills Integration (Task 5.8)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from supernova.skills.loader import SkillLoader, Skill


class TestSkillLoader:
    def _make_skill_dir(self, tmp_path: Path) -> Path:
        """Create a test skills directory with sample skills."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # .skill file at root
        (skills_dir / "test.skill").write_text(
            "---\nname: test-skill\ndescription: A test skill\n---\n# Test\nDo things."
        )
        # SKILL.md in subdirectory
        sub = skills_dir / "mcp-builder"
        sub.mkdir()
        (sub / "SKILL.md").write_text(
            "---\nname: mcp-builder\ndescription: Build MCP servers\n---\n# MCP Guide\nBuild stuff."
        )
        return skills_dir

    def test_discover_finds_skills(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        found = loader.discover()
        assert len(found) == 2
        names = {s.name for s in found}
        assert "test-skill" in names
        assert "mcp-builder" in names

    def test_discover_missing_dir(self, tmp_path):
        loader = SkillLoader(tmp_path / "nonexistent")
        found = loader.discover()
        assert found == []

    def test_parse_frontmatter(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        skill = loader.get_skill("test-skill")
        assert skill is not None
        assert skill.description == "A test skill"
        assert skill.content == "# Test\nDo things."

    def test_parse_no_frontmatter(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "plain.skill").write_text("Just content, no frontmatter.")
        loader = SkillLoader(skills_dir)
        found = loader.discover()
        assert len(found) == 1
        assert found[0].name == "plain"
        assert found[0].content == "Just content, no frontmatter."

    def test_to_prompt(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        prompt = loader.to_prompt("mcp-builder")
        assert '<skill name="mcp-builder">' in prompt
        assert "# MCP Guide" in prompt

    def test_to_prompt_missing(self, tmp_path):
        loader = SkillLoader(tmp_path)
        assert loader.to_prompt("nonexistent") == ""

    def test_activate_deactivate(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        assert loader.activate("test-skill") is True
        assert loader.activate("nonexistent") is False
        skills = loader.list_skills()
        active = [s for s in skills if s["active"]]
        assert len(active) == 1
        assert active[0]["name"] == "test-skill"
        loader.deactivate("test-skill")
        skills = loader.list_skills()
        assert all(not s["active"] for s in skills)

    def test_get_active_prompts(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        loader.activate("test-skill")
        loader.activate("mcp-builder")
        prompts = loader.get_active_prompts()
        assert "test-skill" in prompts
        assert "mcp-builder" in prompts

    def test_list_skills(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        skills = loader.list_skills()
        assert len(skills) == 2
        assert all("name" in s and "description" in s and "active" in s for s in skills)

    def test_reload_changed(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        # Modify a skill file
        skill_file = skills_dir / "test.skill"
        time.sleep(0.6)  # Exceed debounce
        skill_file.write_text(
            "---\nname: test-skill\ndescription: Updated\n---\n# Updated content"
        )
        changed = loader.reload_changed()
        assert "test-skill" in changed
        skill = loader.get_skill("test-skill")
        assert skill.description == "Updated"

    def test_reload_deleted(self, tmp_path):
        skills_dir = self._make_skill_dir(tmp_path)
        loader = SkillLoader(skills_dir)
        loader.discover()
        loader.activate("test-skill")
        (skills_dir / "test.skill").unlink()
        changed = loader.reload_changed()
        assert "test-skill" in changed
        assert loader.get_skill("test-skill") is None

    def test_real_mcp_builder_skill(self):
        """Test with actual mcp-builder skill from project."""
        skills_dir = Path("/home/donovan/Downloads/SuperNova/mcp_and_skills/skills")
        if not skills_dir.exists():
            pytest.skip("Skills directory not available")
        loader = SkillLoader(skills_dir)
        found = loader.discover()
        assert len(found) > 0
        skill = loader.get_skill("mcp-builder")
        assert skill is not None
        prompt = loader.to_prompt("mcp-builder")
        assert "MCP" in prompt
