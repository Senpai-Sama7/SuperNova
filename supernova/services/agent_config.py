"""Agent runtime configuration manager.

This module provides integration between user preferences and the agent loop.
It allows updating agent behavior at runtime based on user settings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from supernova.services.preferences import (
    RuntimeConfig,
    get_runtime_config,
    is_tool_enabled,
    should_interrupt_for_risk,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from supernova.api.routes.preferences import UserPreferences


class AgentConfigManager:
    """Manages agent runtime configuration based on user preferences.

    This class provides a bridge between user preferences and the agent loop,
    allowing dynamic updates to agent behavior without restarting the service.
    """

    def __init__(self) -> None:
        """Initialize the agent config manager."""
        self._configs: dict[str, RuntimeConfig] = {}
        self._tool_registry: Any = None

    def set_tool_registry(self, registry: Any) -> None:
        """Set the tool registry for dynamic tool enable/disable."""
        self._tool_registry = registry

    def get_config(self, user_id: str = "default") -> RuntimeConfig:
        """Get runtime configuration for a user."""
        if user_id not in self._configs:
            self._configs[user_id] = get_runtime_config(user_id)
        return self._configs[user_id]

    def update_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        """Update runtime configuration when preferences change.

        Args:
            user_id: The user identifier
            preferences: The new user preferences
        """
        config = get_runtime_config(user_id)
        self._configs[user_id] = config

        if self._tool_registry and preferences.enabled_tools:
            self._tool_registry.set_enabled_tools(preferences.enabled_tools)
            logger.info(f"Updated tool registry for user {user_id}: {preferences.enabled_tools}")

        logger.info(
            f"Updated agent config for user {user_id}: "
            f"HITL={config.enable_hitl}, reflection={config.reflection_enabled}, "
            f"max_tools={config.max_tool_calls_per_turn}"
        )

    def should_interrupt(self, tool_name: str, user_id: str = "default") -> bool:
        """Check if a tool call should be interrupted for user approval.

        Args:
            tool_name: Name of the tool being called
            user_id: The user identifier

        Returns:
            True if the tool should be interrupted
        """
        config = self.get_config(user_id)

        if not config.enable_hitl:
            return False

        tool_risk_levels = {
            "web_search": "low",
            "file_read": "low",
            "file_write": "medium",
            "code_exec": "high",
            "web_browse": "low",
            "send_email": "high",
            "external_api": "medium",
            "shell_access": "critical",
        }

        risk_level = tool_risk_levels.get(tool_name, "low")
        return should_interrupt_for_risk(tool_name, risk_level, config.hitl_mode)

    def can_use_tool(self, tool_name: str, user_id: str = "default") -> bool:
        """Check if a tool is enabled for the user.

        Args:
            tool_name: Name of the tool to check
            user_id: The user identifier

        Returns:
            True if the tool can be used
        """
        config = self.get_config(user_id)
        return is_tool_enabled(tool_name, config.enabled_tools)


_agent_config_manager: AgentConfigManager | None = None


def get_agent_config_manager() -> AgentConfigManager:
    """Get the global agent config manager instance."""
    global _agent_config_manager  # noqa: PLW0603
    if _agent_config_manager is None:
        _agent_config_manager = AgentConfigManager()
    return _agent_config_manager


def update_agent_from_preferences(user_id: str, preferences: UserPreferences) -> None:
    """Convenience function to update agent config from preferences.

    Call this after user preferences are saved to update the agent runtime.
    """
    manager = get_agent_config_manager()
    manager.update_preferences(user_id, preferences)
