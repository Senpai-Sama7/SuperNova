"""User preferences API routes for controlling power, speed, and risk."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from supernova.api.auth import verify_token
from supernova.config import get_settings
from supernova.infrastructure.storage import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])

# Optional bearer token for authentication
_bearer = HTTPBearer(auto_error=False)


async def get_user_from_token(
    # B008: This is the recommended FastAPI pattern for optional authentication
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
) -> str:
    """Extract user_id from JWT token, or return 'default' if no token provided."""
    if credentials is None:
        return "default"
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return "default"


# In-memory cache for runtime access
_preferences_cache: dict[str, UserPreferences] = {}


RiskLevel = Literal["paranoid", "careful", "balanced", "fast"]
SpeedPreference = Literal["instant", "balanced", "thorough"]
HitlMode = Literal["always", "risky_only", "never"]


class ToolCapability(BaseModel):
    """Individual tool capability toggle."""

    name: str
    enabled: bool
    risk_level: str = "low"


class UserPreferences(BaseModel):
    """User preference profile for controlling agent behavior."""

    model_config = {"str_strip_whitespace": True}

    risk_level: RiskLevel = "balanced"
    speed_preference: SpeedPreference = "balanced"
    daily_budget_usd: float = Field(default=5.0, ge=0.0, le=100.0)
    auto_approve_timeout: int = Field(default=120, ge=0, le=600)
    max_tool_calls_per_turn: int = Field(default=10, ge=1, le=15)
    reflection_enabled: bool = True
    use_cache: bool = True
    hitl_mode: HitlMode = "risky_only"
    enabled_tools: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("enabled_tools", mode="before")
    @classmethod
    def sanitize_tools(cls, v: Any) -> list[str]:
        """Sanitize tool list to prevent injection."""
        if not isinstance(v, list):
            return []
        # Whitelist allowed tools
        allowed_tools = {
            "web_search",
            "file_read",
            "file_write",
            "code_exec",
            "web_browse",
            "send_email",
            "external_api",
            "shell_access",
        }
        return [str(t).strip()[:50] for t in v if isinstance(t, str) and t in allowed_tools]


PRESET_PROFILES: dict[str, dict[str, Any]] = {
    "paranoid": {
        "risk_level": "paranoid",
        "speed_preference": "thorough",
        "daily_budget_usd": 10.0,
        "auto_approve_timeout": 0,
        "max_tool_calls_per_turn": 5,
        "reflection_enabled": True,
        "use_cache": True,
        "hitl_mode": "always",
        "enabled_tools": ["web_search", "file_read"],
    },
    "careful": {
        "risk_level": "careful",
        "speed_preference": "balanced",
        "daily_budget_usd": 5.0,
        "auto_approve_timeout": 120,
        "max_tool_calls_per_turn": 10,
        "reflection_enabled": True,
        "use_cache": True,
        "hitl_mode": "risky_only",
        "enabled_tools": [],
    },
    "balanced": {
        "risk_level": "balanced",
        "speed_preference": "balanced",
        "daily_budget_usd": 5.0,
        "auto_approve_timeout": 120,
        "max_tool_calls_per_turn": 10,
        "reflection_enabled": True,
        "use_cache": True,
        "hitl_mode": "risky_only",
        "enabled_tools": [],
    },
    "fast": {
        "risk_level": "fast",
        "speed_preference": "instant",
        "daily_budget_usd": 2.0,
        "auto_approve_timeout": 30,
        "max_tool_calls_per_turn": 15,
        "reflection_enabled": False,
        "use_cache": True,
        "hitl_mode": "never",
        "enabled_tools": [],
    },
}


def _get_redis_key(user_id: str) -> str:
    """Get Redis key for user preferences."""
    return f"user_preferences:{user_id}"


async def _get_default_preferences() -> UserPreferences:
    """Get system default preferences from config."""
    settings = get_settings()
    prefs = settings.preferences
    return UserPreferences(
        risk_level=prefs.risk_level,
        speed_preference=prefs.speed_preference,
        daily_budget_usd=prefs.daily_budget_usd,
        auto_approve_timeout=prefs.auto_approve_timeout,
        max_tool_calls_per_turn=prefs.max_tool_calls_per_turn,
        reflection_enabled=prefs.reflection_enabled,
        use_cache=prefs.use_cache,
        hitl_mode=prefs.hitl_mode,
        enabled_tools=[],
    )


@router.get("", response_model=UserPreferences)
async def get_preferences(
    user_id: str = Depends(get_user_from_token),
) -> UserPreferences:
    """Get user preferences, returning defaults if not set."""
    try:
        redis_client = await get_redis_client()
        key = _get_redis_key(user_id)
        data = await redis_client._redis.get(key)

        if data is None:
            return await _get_default_preferences()

        stored = json.loads(data)
        return UserPreferences(**stored)
    except Exception as exc:
        logger.warning(f"Failed to load preferences: {exc}")
        return await _get_default_preferences()


@router.post("", response_model=UserPreferences)
async def set_preferences(
    preferences: UserPreferences,
    user_id: str = Depends(get_user_from_token),
) -> UserPreferences:
    """Set user preferences."""
    try:
        redis_client = await get_redis_client()
        key = _get_redis_key(user_id)
        await redis_client._redis.set(key, preferences.model_dump_json())
        # Update runtime cache for fast access
        update_runtime_cache(user_id, preferences)

        # Update agent runtime configuration
        try:
            from supernova.services.agent_config import update_agent_from_preferences  # noqa: PLC0415

            update_agent_from_preferences(user_id, preferences)
        except Exception as config_err:
            logger.warning(f"Failed to update agent config: {config_err}")

        logger.info(f"Preferences updated for user {user_id}")
    except Exception as exc:
        logger.warning(f"Failed to save preferences: {exc}")

    return preferences


@router.post("/preset/{preset_name}", response_model=UserPreferences)
async def apply_preset(
    preset_name: str,
    user_id: str = Depends(get_user_from_token),
) -> UserPreferences:
    """Apply a preset profile (paranoid, careful, balanced, fast)."""
    if preset_name not in PRESET_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset: {preset_name}. Available: {list(PRESET_PROFILES.keys())}",
        )

    preferences = UserPreferences(**PRESET_PROFILES[preset_name])
    return await set_preferences(preferences, user_id)


@router.get("/presets")
async def get_presets() -> dict[str, dict[str, Any]]:
    """Get all available preset profiles."""
    return PRESET_PROFILES


@router.get("/options")
async def get_preference_options() -> dict[str, Any]:
    """Get available options for each preference field."""
    return {
        "risk_level": {
            "type": "select",
            "options": [
                {
                    "value": "paranoid",
                    "label": "🔒 Ask me everything",
                    "description": "Maximum control, slower",
                },
                {
                    "value": "careful",
                    "label": "⚠️ Ask for risky things",
                    "description": "Good balance",
                },
                {"value": "balanced", "label": "⚖️ Balanced", "description": "Recommended"},
                {
                    "value": "fast",
                    "label": "🚀 Let it run",
                    "description": "Fastest, least control",
                },
            ],
            "default": "balanced",
        },
        "speed_preference": {
            "type": "select",
            "options": [
                {
                    "value": "instant",
                    "label": "⚡ Instant",
                    "description": "Lower quality, fastest",
                },
                {
                    "value": "balanced",
                    "label": "⚖️ Balanced",
                    "description": "Good speed and quality",
                },
                {
                    "value": "thorough",
                    "label": "🧠 Thoughtful",
                    "description": "Best quality, slowest",
                },
            ],
            "default": "balanced",
        },
        "daily_budget_usd": {
            "type": "range",
            "min": 0.10,
            "max": 25.0,
            "step": 0.10,
            "default": 5.0,
            "unit": "$",
        },
        "hitl_mode": {
            "type": "select",
            "options": [
                {"value": "always", "label": "Always ask", "description": "Approve every action"},
                {
                    "value": "risky_only",
                    "label": "Risky only",
                    "description": "Ask for risky actions",
                },
                {"value": "never", "label": "Never ask", "description": "Auto-approve all"},
            ],
            "default": "risky_only",
        },
        "max_tool_calls_per_turn": {
            "type": "range",
            "min": 1,
            "max": 15,
            "step": 1,
            "default": 10,
        },
        "reflection_enabled": {
            "type": "boolean",
            "default": True,
            "label": "Enable self-reflection",
            "description": "Agent evaluates its own responses",
        },
        "use_cache": {
            "type": "boolean",
            "default": True,
            "label": "Query Caching",
            "description": "Skip LLM for repeated queries",
        },
    }


# Runtime getter for agent loop - synchronous, uses cache
def get_runtime_preferences(user_id: str = "default") -> UserPreferences:
    """Get preferences for runtime agent execution.

    This is a synchronous function that returns cached preferences
    for use in the agent loop without async overhead.
    """
    if user_id in _preferences_cache:
        return _preferences_cache[user_id]

    # Return defaults from config
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule async fetch
            future = asyncio.run_coroutine_threadsafe(get_preferences(user_id), loop)
            return future.result(timeout=1.0)
    except RuntimeError:
        pass

    # Fall back to defaults
    return asyncio.run(_get_default_preferences())


def update_runtime_cache(user_id: str, preferences: UserPreferences) -> None:
    """Update the in-memory cache for fast runtime access."""
    _preferences_cache[user_id] = preferences
