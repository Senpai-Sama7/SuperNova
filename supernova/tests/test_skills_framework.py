from __future__ import annotations

import asyncio
from typing import Any

import pytest
from pydantic import ValidationError

from supernova.core.skills.base import BaseSkill, SkillManifest
from supernova.core.skills.sandbox import sandboxed_execute


class DummySkill(BaseSkill):
    """A simple dummy skill for testing."""

    def __init__(self, should_fail: bool = False, should_timeout: bool = False):
        self.manifest = SkillManifest(
            name="dummy_skill",
            description="A dummy skill",
            version="1.0.0",
            risk_level="low",
        )
        self.should_fail = should_fail
        self.should_timeout = should_timeout

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        if self.should_fail:
            raise ValueError("Intentional failure")
        if self.should_timeout:
            # Sleep longer than the test timeout
            await asyncio.sleep(10)
        return {"output": f"processed {params.get('input', 'nothing')}"}


def test_skill_manifest_validation() -> None:
    """Test that SkillManifest correctly validates inputs and applies defaults."""
    manifest = SkillManifest(name="test_skill", description="testing")
    assert manifest.name == "test_skill"
    assert manifest.version == "0.1.0"
    assert manifest.risk_level == "low"

    with pytest.raises(ValidationError):
        # Missing required description
        SkillManifest(name="test_skill")  # type: ignore


@pytest.mark.asyncio
async def test_sandboxed_execute_success() -> None:
    """Test successful execution through the sandbox wrapper."""
    skill = DummySkill()
    result = await sandboxed_execute(skill, {"input": "data"}, timeout=1.0)

    assert result["status"] == "success"
    assert result["result"] == {"output": "processed data"}
    assert result["error"] is None
    assert "execution_time_ms" in result
    assert isinstance(result["execution_time_ms"], int)


@pytest.mark.asyncio
async def test_sandboxed_execute_failure() -> None:
    """Test that exceptions raised by a skill are cleanly caught by the sandbox."""
    skill = DummySkill(should_fail=True)
    result = await sandboxed_execute(skill, {}, timeout=1.0)

    assert result["status"] == "error"
    assert result["result"] is None
    assert "Intentional failure" in result["error"]
    assert "execution_time_ms" in result


@pytest.mark.asyncio
async def test_sandboxed_execute_timeout() -> None:
    """Test that long-running skills are terminated."""
    skill = DummySkill(should_timeout=True)
    
    # Use a very short timeout to ensure it triggers quickly
    result = await sandboxed_execute(skill, {}, timeout=0.1)

    assert result["status"] == "timeout"
    assert result["result"] is None
    assert "timed out" in result["error"].lower()
    assert "execution_time_ms" in result
