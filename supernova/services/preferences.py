"""Preferences service for runtime integration with the agent loop.

This module provides a bridge between user preferences stored in Redis
and the agent's cognitive loop. It allows the agent to respect user
settings for HITL, reflection, tool limits, and model routing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

RiskLevel = Literal["paranoid", "careful", "balanced", "fast"]
SpeedPreference = Literal["instant", "balanced", "thorough"]
HitlMode = Literal["always", "risky_only", "never"]


@dataclass
class RuntimeConfig:
    """Runtime configuration derived from user preferences."""

    enable_hitl: bool
    reflection_enabled: bool
    max_tool_calls_per_turn: int
    risk_level: RiskLevel
    speed_preference: SpeedPreference
    hitl_mode: HitlMode
    enabled_tools: list[str]


def get_runtime_config(user_id: str = "default") -> RuntimeConfig:
    """Get runtime configuration for the agent loop.

    This is a synchronous function that returns cached preferences
    for use in the agent loop without async overhead.

    Args:
        user_id: The user identifier (default: "default")

    Returns:
        RuntimeConfig: Configuration derived from user preferences
    """
    prefs = get_runtime_preferences(user_id)

    return _prefs_to_config(prefs)


def _prefs_to_config(prefs: Any) -> RuntimeConfig:
    """Convert UserPreferences to RuntimeConfig."""
    enable_hitl = prefs.hitl_mode != "never"

    return RuntimeConfig(
        enable_hitl=enable_hitl,
        reflection_enabled=prefs.reflection_enabled,
        max_tool_calls_per_turn=prefs.max_tool_calls_per_turn,
        risk_level=prefs.risk_level,
        speed_preference=prefs.speed_preference,
        hitl_mode=prefs.hitl_mode,
        enabled_tools=prefs.enabled_tools,
    )


def should_interrupt_for_risk(
    tool_name: str,
    risk_level: str,
    hitl_mode: HitlMode,
) -> bool:
    """Determine if a tool call should trigger human-in-the-loop.

    Args:
        tool_name: Name of the tool being called
        risk_level: Risk level of the tool (low, medium, high, critical)
        hitl_mode: User's HITL preference

    Returns:
        bool: True if the tool should be interrupted
    """
    if hitl_mode == "never":
        return False
    if hitl_mode == "always":
        return True

    high_risk_tools = {"shell_access", "code_exec", "file_write", "send_email"}
    return tool_name in high_risk_tools or risk_level in ("high", "critical")


def is_tool_enabled(tool_name: str, enabled_tools: list[str]) -> bool:
    """Check if a tool is enabled for the user.

    If enabled_tools is empty, all tools are allowed.
    If enabled_tools has items, only those tools are allowed.

    Args:
        tool_name: Name of the tool to check
        enabled_tools: List of enabled tool names from preferences

    Returns:
        bool: True if the tool is enabled
    """
    if not enabled_tools:
        return True
    return tool_name in enabled_tools


async def sync_preferences_to_runtime(user_id: str, prefs: Any) -> None:
    """Sync preferences to runtime cache.

    Call this after preferences are updated to ensure the agent loop
    uses the latest settings without waiting for cache refresh.

    Args:
        user_id: The user identifier
        prefs: The updated preferences
    """
    update_runtime_cache(user_id, prefs)
    logger.info(f"Preferences synced to runtime cache for user {user_id}")


def get_runtime_preferences(user_id: str = "default") -> Any:
    """Proxy to preferences route runtime accessor without import-cycle at module load."""
    from supernova.api.routes.preferences import get_runtime_preferences as _get_runtime_preferences

    return _get_runtime_preferences(user_id)


def update_runtime_cache(user_id: str, prefs: Any) -> None:
    """Proxy to preferences route cache updater without import-cycle at module load."""
    from supernova.api.routes.preferences import update_runtime_cache as _update_runtime_cache

    _update_runtime_cache(user_id, prefs)
