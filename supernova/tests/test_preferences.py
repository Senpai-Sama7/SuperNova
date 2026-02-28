"""Tests for user preferences API and service."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from supernova.api.routes.preferences import (
    UserPreferences,
    PRESET_PROFILES,
    get_runtime_preferences,
    update_runtime_cache,
    _preferences_cache,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear preferences cache before each test."""
    _preferences_cache.clear()
    yield
    _preferences_cache.clear()


class TestUserPreferences:
    """Test UserPreferences model validation."""

    def test_default_preferences(self):
        """Test default preference values."""
        prefs = UserPreferences()
        assert prefs.risk_level == "balanced"
        assert prefs.speed_preference == "balanced"
        assert prefs.daily_budget_usd == 5.0
        assert prefs.auto_approve_timeout == 120
        assert prefs.max_tool_calls_per_turn == 10
        assert prefs.reflection_enabled is True
        assert prefs.use_cache is True
        assert prefs.hitl_mode == "risky_only"
        assert prefs.enabled_tools == []

    def test_custom_preferences(self):
        """Test custom preference values."""
        prefs = UserPreferences(
            risk_level="paranoid",
            speed_preference="thorough",
            daily_budget_usd=10.0,
            max_tool_calls_per_turn=5,
        )
        assert prefs.risk_level == "paranoid"
        assert prefs.speed_preference == "thorough"
        assert prefs.daily_budget_usd == 10.0
        assert prefs.max_tool_calls_per_turn == 5

    def test_budget_validation(self):
        """Test daily budget bounds validation."""
        with pytest.raises(ValueError):
            UserPreferences(daily_budget_usd=-1.0)
        with pytest.raises(ValueError):
            UserPreferences(daily_budget_usd=101.0)

    def test_tool_validation(self):
        """Test tool name validation and sanitization."""
        prefs = UserPreferences(enabled_tools=["web_search", "file_read", "invalid_tool"])
        assert "web_search" in prefs.enabled_tools
        assert "file_read" in prefs.enabled_tools
        assert "invalid_tool" not in prefs.enabled_tools


class TestPresetProfiles:
    """Test preset profile configurations."""

    def test_all_presets_exist(self):
        """Test all expected presets are defined."""
        assert "paranoid" in PRESET_PROFILES
        assert "careful" in PRESET_PROFILES
        assert "balanced" in PRESET_PROFILES
        assert "fast" in PRESET_PROFILES

    def test_paranoid_preset(self):
        """Test paranoid preset configuration."""
        preset = PRESET_PROFILES["paranoid"]
        assert preset["risk_level"] == "paranoid"
        assert preset["hitl_mode"] == "always"
        assert preset["max_tool_calls_per_turn"] == 5

    def test_fast_preset(self):
        """Test fast preset configuration."""
        preset = PRESET_PROFILES["fast"]
        assert preset["risk_level"] == "fast"
        assert preset["hitl_mode"] == "never"
        assert preset["reflection_enabled"] is False

    def test_presets_have_all_required_fields(self):
        """Test each preset has all required preference fields."""
        required_fields = [
            "risk_level",
            "speed_preference",
            "daily_budget_usd",
            "auto_approve_timeout",
            "max_tool_calls_per_turn",
            "reflection_enabled",
            "use_cache",
            "hitl_mode",
            "enabled_tools",
        ]
        for preset_name, preset in PRESET_PROFILES.items():
            for field in required_fields:
                assert field in preset, f"Preset {preset_name} missing {field}"


class TestRuntimeCache:
    """Test runtime cache operations."""

    def test_update_runtime_cache(self):
        """Test updating runtime cache."""
        prefs = UserPreferences(risk_level="paranoid")
        update_runtime_cache("test_user", prefs)
        assert "test_user" in _preferences_cache
        assert _preferences_cache["test_user"].risk_level == "paranoid"

    def test_get_runtime_preferences_from_cache(self):
        """Test retrieving from cache."""
        prefs = UserPreferences(risk_level="careful")
        update_runtime_cache("test_user", prefs)
        retrieved = get_runtime_preferences("test_user")
        assert retrieved.risk_level == "careful"

    @patch("supernova.api.routes.preferences.get_redis_client")
    @patch("supernova.api.routes.preferences._get_default_preferences")
    def test_get_runtime_preferences_fallback(self, mock_default, mock_redis):
        """Test fallback to defaults when not in cache."""
        mock_default.return_value = UserPreferences(risk_level="balanced")
        result = get_runtime_preferences("nonexistent_user")
        assert result.risk_level == "balanced"
