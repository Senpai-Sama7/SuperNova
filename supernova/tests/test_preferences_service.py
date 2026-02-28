"""Tests for preferences service and runtime integration."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from supernova.api.routes.preferences import UserPreferences, HitlMode
from supernova.services.preferences import (
    RuntimeConfig,
    get_runtime_config,
    should_interrupt_for_risk,
    is_tool_enabled,
    _prefs_to_config,
)


class TestRuntimeConfig:
    """Test RuntimeConfig generation from preferences."""

    def test_balanced_preferences(self):
        """Test config from balanced preset."""
        prefs = UserPreferences(
            risk_level="balanced",
            speed_preference="balanced",
            hitl_mode="risky_only",
            reflection_enabled=True,
            max_tool_calls_per_turn=10,
        )
        config = _prefs_to_config(prefs)

        assert config.risk_level == "balanced"
        assert config.speed_preference == "balanced"
        assert config.hitl_mode == "risky_only"
        assert config.enable_hitl is True
        assert config.reflection_enabled is True
        assert config.max_tool_calls_per_turn == 10

    def test_paranoid_always_hitl(self):
        """Test paranoid preset enables always HITL."""
        prefs = UserPreferences(
            risk_level="paranoid",
            hitl_mode="always",
        )
        config = _prefs_to_config(prefs)

        assert config.enable_hitl is True
        assert config.hitl_mode == "always"

    def test_fast_disables_hitl(self):
        """Test fast preset disables HITL."""
        prefs = UserPreferences(
            risk_level="fast",
            hitl_mode="never",
        )
        config = _prefs_to_config(prefs)

        assert config.enable_hitl is False
        assert config.hitl_mode == "never"

    def test_reflection_disabled(self):
        """Test reflection can be disabled."""
        prefs = UserPreferences(reflection_enabled=False)
        config = _prefs_to_config(prefs)

        assert config.reflection_enabled is False

    def test_tool_filtering(self):
        """Test enabled tools are passed through."""
        prefs = UserPreferences(enabled_tools=["web_search", "file_read"])
        config = _prefs_to_config(prefs)

        assert config.enabled_tools == ["web_search", "file_read"]

    def test_empty_tools_allows_all(self):
        """Test empty enabled_tools allows all tools."""
        prefs = UserPreferences(enabled_tools=[])
        config = _prefs_to_config(prefs)

        assert config.enabled_tools == []


class TestShouldInterruptForRisk:
    """Test HITL interrupt decision logic."""

    def test_never_interrupt_mode(self):
        """Test never mode never interrupts."""
        assert should_interrupt_for_risk("shell_access", "critical", "never") is False
        assert should_interrupt_for_risk("web_search", "low", "never") is False

    def test_always_interrupt_mode(self):
        """Test always mode always interrupts."""
        assert should_interrupt_for_risk("shell_access", "critical", "always") is True
        assert should_interrupt_for_risk("web_search", "low", "always") is True

    def test_risky_only_interrupts_high_risk(self):
        """Test risky_only mode interrupts high-risk tools."""
        assert should_interrupt_for_risk("shell_access", "critical", "risky_only") is True
        assert should_interrupt_for_risk("code_exec", "high", "risky_only") is True

    def test_risky_only_allows_low_risk(self):
        """Test risky_only mode allows low-risk tools."""
        assert should_interrupt_for_risk("web_search", "low", "risky_only") is False
        assert should_interrupt_for_risk("file_read", "low", "risky_only") is False


class TestIsToolEnabled:
    """Test tool enable/disable checks."""

    def test_empty_enabled_list_allows_all(self):
        """Test empty list allows all tools."""
        assert is_tool_enabled("web_search", []) is True
        assert is_tool_enabled("shell_access", []) is True

    def test_enabled_list_restricts_tools(self):
        """Test non-empty list only allows listed tools."""
        assert is_tool_enabled("web_search", ["web_search", "file_read"]) is True
        assert is_tool_enabled("file_read", ["web_search", "file_read"]) is True
        assert is_tool_enabled("shell_access", ["web_search", "file_read"]) is False

    def test_unknown_tool_when_listed(self):
        """Test unknown tool when specific tools are listed."""
        assert is_tool_enabled("unknown_tool", ["web_search"]) is False


class TestGetRuntimeConfig:
    """Test get_runtime_config function."""

    @patch("supernova.services.preferences.get_runtime_preferences")
    def test_get_runtime_config(self, mock_get_prefs):
        """Test getting runtime config."""
        mock_get_prefs.return_value = UserPreferences(
            risk_level="careful",
            speed_preference="balanced",
            hitl_mode="risky_only",
            reflection_enabled=True,
            max_tool_calls_per_turn=8,
        )

        config = get_runtime_config("test_user")

        assert config.risk_level == "careful"
        assert config.max_tool_calls_per_turn == 8
        mock_get_prefs.assert_called_once_with("test_user")
