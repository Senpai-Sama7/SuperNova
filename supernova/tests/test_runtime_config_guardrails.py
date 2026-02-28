"""Unit tests for runtime production configuration guardrails."""

from __future__ import annotations

import pytest

from supernova.config import get_settings
from supernova.runtime_config_guardrails import validate_runtime_configuration


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def clear_guardrail_env(monkeypatch: pytest.MonkeyPatch) -> None:
    keys = [
        "SUPERNOVA_ENV",
        "SUPERNOVA_SECRET_KEY",
        "POSTGRES_PASSWORD",
        "NEO4J_PASSWORD",
        "LITELLM_MASTER_KEY",
        "PICKLE_HMAC_KEY",
        "API_KEY_ENCRYPTION_KEY",
        "CORS_ORIGINS",
        "CODE_SANDBOX",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.unit
def test_runtime_guardrails_allow_development_defaults(clear_guardrail_env: None) -> None:
    validate_runtime_configuration()


@pytest.mark.unit
def test_runtime_guardrails_reject_default_postgres_password(
    clear_guardrail_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPERNOVA_ENV", "production")
    monkeypatch.setenv("SUPERNOVA_SECRET_KEY", "a" * 64)

    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        validate_runtime_configuration()


@pytest.mark.unit
def test_runtime_guardrails_reject_localhost_cors(
    clear_guardrail_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPERNOVA_ENV", "production")
    monkeypatch.setenv("SUPERNOVA_SECRET_KEY", "a" * 64)
    monkeypatch.setenv("POSTGRES_PASSWORD", "prod-db-password")
    monkeypatch.setenv("NEO4J_PASSWORD", "prod-neo4j-password")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "prod-litellm-master-key")
    monkeypatch.setenv("PICKLE_HMAC_KEY", "prod-hmac-key-material")
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", "prod-encryption-key-material")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,http://localhost:3000")

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_runtime_configuration()


@pytest.mark.unit
def test_runtime_guardrails_reject_disabled_sandbox(
    clear_guardrail_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPERNOVA_ENV", "production")
    monkeypatch.setenv("SUPERNOVA_SECRET_KEY", "a" * 64)
    monkeypatch.setenv("POSTGRES_PASSWORD", "prod-db-password")
    monkeypatch.setenv("NEO4J_PASSWORD", "prod-neo4j-password")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "prod-litellm-master-key")
    monkeypatch.setenv("PICKLE_HMAC_KEY", "prod-hmac-key-material")
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", "prod-encryption-key-material")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("CODE_SANDBOX", "none")

    with pytest.raises(RuntimeError, match="CODE_SANDBOX"):
        validate_runtime_configuration()


@pytest.mark.unit
def test_runtime_guardrails_accept_valid_production_values(
    clear_guardrail_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPERNOVA_ENV", "production")
    monkeypatch.setenv("SUPERNOVA_SECRET_KEY", "b" * 64)
    monkeypatch.setenv("POSTGRES_PASSWORD", "prod-db-password")
    monkeypatch.setenv("NEO4J_PASSWORD", "prod-neo4j-password")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "prod-litellm-master-key")
    monkeypatch.setenv("PICKLE_HMAC_KEY", "prod-hmac-key-material")
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", "prod-encryption-key-material")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://admin.example.com")
    monkeypatch.setenv("CODE_SANDBOX", "docker")

    validate_runtime_configuration()
