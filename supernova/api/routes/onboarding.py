"""Onboarding & setup wizard API routes."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/setup", tags=["onboarding"])

# In-memory setup state (production would use DB)
_setup_state: dict[str, Any] = {"completed": False, "completed_at": None, "config": {}}


class KeyValidationRequest(BaseModel):
    provider: str = Field(..., pattern="^(openai|anthropic|google|ollama)$")
    api_key: str = Field(..., min_length=1)


class KeyValidationResponse(BaseModel):
    valid: bool
    provider: str
    message: str


class SetupConfig(BaseModel):
    api_keys: dict[str, str] = Field(default_factory=dict)
    default_model: str = "ollama/llama3.1"
    privacy_mode: bool = True
    theme: str = "dark"


@router.get("/status")
async def setup_status() -> dict[str, Any]:
    """Check if first-run setup has been completed."""
    return {
        "completed": _setup_state["completed"],
        "completed_at": _setup_state["completed_at"],
        "first_run": not _setup_state["completed"],
    }


@router.post("/validate-key", response_model=KeyValidationResponse)
async def validate_api_key(body: KeyValidationRequest) -> KeyValidationResponse:
    """Validate an API key by checking format and prefix."""
    key = body.api_key
    checks: dict[str, tuple[str, str]] = {
        "openai": ("sk-", "OpenAI key must start with 'sk-'"),
        "anthropic": ("sk-ant-", "Anthropic key must start with 'sk-ant-'"),
        "google": ("AI", "Google key must start with 'AI'"),
        "ollama": ("", "Ollama runs locally — no key required"),
    }
    prefix, err_msg = checks.get(body.provider, ("", "Unknown provider"))
    if body.provider == "ollama":
        return KeyValidationResponse(valid=True, provider="ollama", message="Local model — no key needed")
    if prefix and not key.startswith(prefix):
        return KeyValidationResponse(valid=False, provider=body.provider, message=err_msg)
    if len(key) < 20:
        return KeyValidationResponse(valid=False, provider=body.provider, message="Key too short")
    return KeyValidationResponse(valid=True, provider=body.provider, message="Key format valid")


@router.get("/cost-estimate")
async def cost_estimate() -> dict[str, list[dict[str, Any]]]:
    """Return estimated monthly costs for available models."""
    estimates = [
        {"model": "ollama/llama3.1", "estimated_monthly_usd": 0.0, "tokens_per_month": 0, "recommended": True},
        {"model": "ollama/llama3", "estimated_monthly_usd": 0.0, "tokens_per_month": 0},
        {"model": "gpt-4o-mini", "estimated_monthly_usd": 5.0, "tokens_per_month": 1_000_000},
        {"model": "claude-3-haiku", "estimated_monthly_usd": 3.0, "tokens_per_month": 1_000_000},
        {"model": "gpt-4o", "estimated_monthly_usd": 30.0, "tokens_per_month": 1_000_000},
        {"model": "claude-3.5-sonnet", "estimated_monthly_usd": 25.0, "tokens_per_month": 1_000_000},
    ]
    return {"estimates": estimates}


@router.post("/complete")
async def complete_setup(config: SetupConfig) -> dict[str, Any]:
    """Mark first-run setup as complete and store configuration."""
    _setup_state["completed"] = True
    _setup_state["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    safe_config = config.model_dump()
    safe_config["api_keys"] = {
        k: hashlib.sha256(v.encode()).hexdigest()[:16] for k, v in config.api_keys.items()
    }
    _setup_state["config"] = safe_config
    return {"status": "setup_complete", "completed_at": _setup_state["completed_at"]}
