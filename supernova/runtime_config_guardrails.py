"""Runtime configuration guardrails for production deployments."""

from __future__ import annotations

from supernova.config import get_settings

_PLACEHOLDER_TOKENS = (
    "change-me",
    "placeholder",
    "example",
    "your-",
    "generate-with-",
    "replace-me",
    "not-real",
)


def _looks_like_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    normalized = value.strip().lower()
    if not normalized:
        return True
    return any(token in normalized for token in _PLACEHOLDER_TOKENS)


def validate_runtime_configuration() -> None:
    """Raise on unsafe production configuration before the API starts."""
    settings = get_settings()
    if not settings.is_production:
        return

    issues: list[str] = []

    if _looks_like_placeholder(settings.secret_key) or len(settings.secret_key) < 32:
        issues.append("SUPERNOVA_SECRET_KEY must be a strong non-placeholder value")

    if settings.database.password == "supernova_dev_password":
        issues.append("POSTGRES_PASSWORD cannot use the development default")

    if settings.neo4j.password == "supernova_neo4j_dev":
        issues.append("NEO4J_PASSWORD cannot use the development default")

    if settings.llm.litellm_master_key in {"sk-supernova-dev", "sk-supernova-dev-key-change-in-production"}:
        issues.append("LITELLM_MASTER_KEY cannot use the development default")

    if settings.security.pickle_hmac_key == "dev-hmac-key":
        issues.append("PICKLE_HMAC_KEY cannot use the development default")

    if settings.security.api_key_encryption_key == "dev-encryption-key":
        issues.append("API_KEY_ENCRYPTION_KEY cannot use the development default")

    if not settings.security.cors_origins_list:
        issues.append("CORS_ORIGINS must contain at least one explicit origin")
    elif any("localhost" in origin or "127.0.0.1" in origin for origin in settings.security.cors_origins_list):
        issues.append("CORS_ORIGINS cannot include localhost or 127.0.0.1")

    if settings.sandbox.sandbox == "none":
        issues.append("CODE_SANDBOX cannot be 'none'")

    if issues:
        raise RuntimeError("Invalid production configuration: " + "; ".join(issues))
