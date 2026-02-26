"""Tests for onboarding & setup wizard API routes — Phase 15."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from supernova.api.routes.onboarding import _setup_state, router

# Build a minimal FastAPI app for testing
from fastapi import FastAPI

_app = FastAPI()
_app.include_router(router)


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset setup state between tests."""
    _setup_state["completed"] = False
    _setup_state["completed_at"] = None
    _setup_state["config"] = {}
    yield


@pytest.fixture()
async def client():
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Setup Status ──────────────────────────────────────────────────────────────

class TestSetupStatus:
    @pytest.mark.asyncio
    async def test_initial_status_is_first_run(self, client: AsyncClient):
        r = await client.get("/setup/status")
        assert r.status_code == 200
        data = r.json()
        assert data["first_run"] is True
        assert data["completed"] is False
        assert data["completed_at"] is None

    @pytest.mark.asyncio
    async def test_status_after_completion(self, client: AsyncClient):
        await client.post("/setup/complete", json={"api_keys": {}, "default_model": "gpt-4o-mini", "privacy_mode": False, "theme": "dark"})
        r = await client.get("/setup/status")
        data = r.json()
        assert data["completed"] is True
        assert data["first_run"] is False
        assert data["completed_at"] is not None


# ── Key Validation ────────────────────────────────────────────────────────────

class TestKeyValidation:
    @pytest.mark.asyncio
    async def test_valid_openai_key(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "openai", "api_key": "sk-" + "a" * 40})
        assert r.status_code == 200
        assert r.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_invalid_openai_prefix(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "openai", "api_key": "bad-" + "a" * 40})
        assert r.json()["valid"] is False
        assert "sk-" in r.json()["message"]

    @pytest.mark.asyncio
    async def test_key_too_short(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "openai", "api_key": "sk-short"})
        assert r.json()["valid"] is False
        assert "too short" in r.json()["message"]

    @pytest.mark.asyncio
    async def test_valid_anthropic_key(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "anthropic", "api_key": "sk-ant-" + "b" * 40})
        assert r.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_invalid_anthropic_prefix(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "anthropic", "api_key": "sk-" + "b" * 40})
        assert r.json()["valid"] is False

    @pytest.mark.asyncio
    async def test_ollama_always_valid(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "ollama", "api_key": "anything"})
        assert r.json()["valid"] is True
        assert "local" in r.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_valid_google_key(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "google", "api_key": "AI" + "c" * 30})
        assert r.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_invalid_provider_rejected(self, client: AsyncClient):
        r = await client.post("/setup/validate-key", json={"provider": "invalid", "api_key": "test"})
        assert r.status_code == 422  # Pydantic validation


# ── Cost Estimate ─────────────────────────────────────────────────────────────

class TestCostEstimate:
    @pytest.mark.asyncio
    async def test_returns_estimates(self, client: AsyncClient):
        r = await client.get("/setup/cost-estimate")
        assert r.status_code == 200
        data = r.json()
        assert "estimates" in data
        assert len(data["estimates"]) >= 3

    @pytest.mark.asyncio
    async def test_estimates_have_required_fields(self, client: AsyncClient):
        r = await client.get("/setup/cost-estimate")
        for est in r.json()["estimates"]:
            assert "model" in est
            assert "estimated_monthly_usd" in est
            assert isinstance(est["estimated_monthly_usd"], (int, float))

    @pytest.mark.asyncio
    async def test_ollama_is_free(self, client: AsyncClient):
        r = await client.get("/setup/cost-estimate")
        ollama = [e for e in r.json()["estimates"] if "ollama" in e["model"]]
        assert len(ollama) >= 1
        assert ollama[0]["estimated_monthly_usd"] == 0.0


# ── Setup Complete ────────────────────────────────────────────────────────────

class TestSetupComplete:
    @pytest.mark.asyncio
    async def test_complete_setup(self, client: AsyncClient):
        r = await client.post("/setup/complete", json={
            "api_keys": {"openai": "sk-" + "x" * 40},
            "default_model": "gpt-4o",
            "privacy_mode": True,
            "theme": "dark",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "setup_complete"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_keys_are_hashed_in_state(self, client: AsyncClient):
        await client.post("/setup/complete", json={
            "api_keys": {"openai": "sk-" + "x" * 40},
            "default_model": "gpt-4o-mini",
            "privacy_mode": False,
            "theme": "dark",
        })
        stored = _setup_state["config"]["api_keys"]
        assert "openai" in stored
        # Key should be hashed (16 hex chars), not raw
        assert stored["openai"] != "sk-" + "x" * 40
        assert len(stored["openai"]) == 16

    @pytest.mark.asyncio
    async def test_complete_with_defaults(self, client: AsyncClient):
        r = await client.post("/setup/complete", json={})
        assert r.status_code == 200
        assert _setup_state["completed"] is True
