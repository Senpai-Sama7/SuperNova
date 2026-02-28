#!/usr/bin/env python3
"""Validate required production configuration before deployment."""

from __future__ import annotations

import os
import sys

REQUIRED = (
    "SUPERNOVA_SECRET_KEY",
    "POSTGRES_PASSWORD",
    "NEO4J_PASSWORD",
    "LITELLM_MASTER_KEY",
    "PICKLE_HMAC_KEY",
    "API_KEY_ENCRYPTION_KEY",
    "CORS_ORIGINS",
)

DISALLOWED_EXACT = {
    "POSTGRES_PASSWORD": {"supernova_dev_password"},
    "NEO4J_PASSWORD": {"supernova_neo4j_dev"},
    "LITELLM_MASTER_KEY": {"sk-supernova-dev", "sk-supernova-dev-key-change-in-production"},
    "PICKLE_HMAC_KEY": {"dev-hmac-key"},
    "API_KEY_ENCRYPTION_KEY": {"dev-encryption-key"},
}

DISALLOWED_TOKENS = (
    "change-me",
    "placeholder",
    "example",
    "your-",
    "generate-with-",
    "replace-me",
    "not-real",
)


def value_is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    normalized = value.strip().lower()
    if not normalized:
        return True
    return any(token in normalized for token in DISALLOWED_TOKENS)


def validate() -> list[str]:
    issues: list[str] = []

    if os.getenv("SUPERNOVA_ENV", "development") != "production":
        return issues

    for key in REQUIRED:
        value = os.getenv(key)
        if value_is_placeholder(value):
            issues.append(f"{key} must be set to a real non-placeholder value in production")
            continue

        if key in DISALLOWED_EXACT and value in DISALLOWED_EXACT[key]:
            issues.append(f"{key} cannot use the development default in production")

    cors_origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "").split(",") if item.strip()]
    if not cors_origins:
        issues.append("CORS_ORIGINS must contain at least one explicit origin in production")
    elif any("localhost" in item or "127.0.0.1" in item for item in cors_origins):
        issues.append("CORS_ORIGINS cannot include localhost or 127.0.0.1 in production")

    if os.getenv("CODE_SANDBOX", "docker") == "none":
        issues.append("CODE_SANDBOX cannot be 'none' in production")

    return issues


def main() -> int:
    issues = validate()
    if not issues:
        print("Production configuration validation passed.")
        return 0

    print("Production configuration validation failed:", file=sys.stderr)
    for issue in issues:
        print(f" - {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
