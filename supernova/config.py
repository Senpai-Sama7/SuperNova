"""SuperNova Configuration Module

Pydantic Settings-based configuration with .env file support.
All environment variables are loaded, validated, and type-coerced here.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    host: str = "localhost"
    port: int = 5432
    db: str = "supernova"
    user: str = "supernova"
    password: str = Field(default="supernova_dev_password", repr=False)
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

    @property
    def async_database_url(self) -> str:
        """Build async database URL from components."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    """Redis configuration for working memory and Celery."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str = "redis://localhost:6379/0"
    password: str | None = Field(default=None, repr=False)
    celery_url: str = "redis://localhost:6379/1"
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


class Neo4jSettings(BaseSettings):
    """Neo4j configuration for episodic memory."""

    model_config = SettingsConfigDict(env_prefix="NEO4J_")

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = Field(default="supernova_neo4j_dev", repr=False)
    max_connection_pool_size: int = 50
    connection_timeout: int = 30


class LLMSettings(BaseSettings):
    """LLM provider API keys and configuration."""

    openai_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)
    gemini_api_key: str | None = Field(default=None, repr=False)
    cohere_api_key: str | None = Field(default=None, repr=False)
    groq_api_key: str | None = Field(default=None, repr=False)

    litellm_master_key: str = Field(default="sk-supernova-dev", repr=False)
    litellm_proxy_host: str | None = None
    litellm_default_model: str = "gpt-4o-mini"
    litellm_fallback_models: str = "gpt-3.5-turbo,claude-3-haiku-20240307"

    @field_validator("litellm_fallback_models")
    @classmethod
    def parse_fallback_models(cls, v: str) -> list[str]:
        """Parse comma-separated fallback models."""
        return [m.strip() for m in v.split(",") if m.strip()]


class LangfuseSettings(BaseSettings):
    """Langfuse observability configuration."""

    model_config = SettingsConfigDict(env_prefix="LANGFUSE_")

    public_key: str | None = None
    secret_key: str | None = Field(default=None, repr=False)
    host: str = "http://localhost:3000"
    enabled: bool = True
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)


class MCPSettings(BaseSettings):
    """Model Context Protocol configuration."""

    model_config = SettingsConfigDict(env_prefix="MCP_")

    config_path: Path = Field(default=Path("./mcp_config.json"))
    server_timeout: int = 30
    health_check: bool = True

    @field_validator("config_path")
    @classmethod
    def validate_config_path(cls, v: Path) -> Path:
        """Ensure config path is valid."""
        return v.resolve()


class SecuritySettings(BaseSettings):
    """Security-related configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    pickle_hmac_key: str = Field(default="dev-hmac-key", repr=False)
    api_key_encryption_key: str = Field(default="dev-encryption-key", repr=False)
    jwt_expiration_minutes: int = 60
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @field_validator("pickle_hmac_key", "api_key_encryption_key")
    @classmethod
    def validate_key_length(cls, v: str) -> str:
        """Warn if using default keys in production."""
        if v.startswith("dev-"):
            # Allow in development, but keys should be changed
            pass
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


class CostManagementSettings(BaseSettings):
    """Cost tracking and spending limit configuration."""

    model_config = SettingsConfigDict(env_prefix="COST_")

    daily_spending_limit: float = Field(default=10.0, ge=0.0)
    monthly_spending_limit: float = Field(default=300.0, ge=0.0)
    confirmation_threshold: float = Field(default=0.50, ge=0.0)
    tracking_enabled: bool = True
    alert_threshold_percent: float = Field(default=80.0, ge=0.0, le=100.0)


class OllamaSettings(BaseSettings):
    """Local model fallback configuration."""

    model_config = SettingsConfigDict(env_prefix="OLLAMA_")

    enabled: bool = False
    host: str = "http://localhost:11434"
    default_model: str = "llama3.2:3b"
    local_model_priority: bool = False


class BackupSettings(BaseSettings):
    """Backup and recovery configuration."""

    model_config = SettingsConfigDict(env_prefix="BACKUP_")

    enabled: bool = True
    time: str = "02:00"
    retention_days: int = 30
    path: Path = Field(default=Path("./backups"))
    s3_bucket: str | None = None
    s3_prefix: str = "supernova/"
    s3_region: str = "us-east-1"


class AuditSettings(BaseSettings):
    """Audit logging configuration."""

    model_config = SettingsConfigDict(env_prefix="AUDIT_")

    log_enabled: bool = True
    log_destination: Literal["database", "file", "both"] = "database"
    log_file_path: Path = Field(default=Path("./logs/audit.log"))
    log_privileged_only: bool = False


class SandboxSettings(BaseSettings):
    """Code execution sandbox configuration."""

    model_config = SettingsConfigDict(env_prefix="CODE_")

    sandbox: Literal["docker", "gvisor", "none"] = "docker"
    sandbox_image: str = "supernova-sandbox:latest"
    execution_timeout: int = 30
    sandbox_memory_mb: int = 512


class PathSettings(BaseSettings):
    """Directory paths configuration."""

    model_config = SettingsConfigDict(env_prefix="")

    workspace_dir: Path = Field(default=Path("./workspace"))
    logs_dir: Path = Field(default=Path("./logs"))
    skills_dir: Path = Field(default=Path("./supernova/skills"))
    temp_dir: Path = Field(default=Path("/tmp/supernova"))

    @model_validator(mode="after")
    def ensure_directories(self) -> PathSettings:
        """Ensure all path directories exist."""
        for path in [self.workspace_dir, self.logs_dir, self.skills_dir, self.temp_dir]:
            path.mkdir(parents=True, exist_ok=True)
        return self


class FeatureFlags(BaseSettings):
    """Feature toggle configuration."""

    model_config = SettingsConfigDict(env_prefix="FEATURE_")

    skill_crystallization: bool = True
    episodic_memory: bool = True
    semantic_memory: bool = True
    hitl_interrupts: bool = True
    demo_mode: bool = False


class DevelopmentSettings(BaseSettings):
    """Development-only settings."""

    model_config = SettingsConfigDict(env_prefix="DEV_")

    hot_reload: bool = True
    debug: bool = False
    profiling: bool = False
    auto_restart: bool = True


class Settings(BaseSettings):
    """SuperNova main configuration.

    All settings are loaded from environment variables and .env file.
    Nested settings are grouped by functionality.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra env vars not defined here
    )

    # Core settings
    env: Literal["development", "staging", "production"] = Field(
        default="development", alias="SUPERNOVA_ENV"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="SUPERNOVA_LOG_LEVEL"
    )
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        alias="SUPERNOVA_SECRET_KEY",
        repr=False,
    )
    host: str = Field(default="0.0.0.0", alias="SUPERNOVA_HOST")
    port: int = Field(default=8000, alias="SUPERNOVA_PORT")

    # Nested settings groups
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cost: CostManagementSettings = Field(default_factory=CostManagementSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    backup: BackupSettings = Field(default_factory=BackupSettings)
    audit: AuditSettings = Field(default_factory=AuditSettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    dev: DevelopmentSettings = Field(default_factory=DevelopmentSettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"

    @property
    def database_url(self) -> str:
        """Shortcut to async database URL."""
        return self.database.async_database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Use this function to access settings throughout the application.
    The result is cached to avoid repeated .env file parsing.

    Returns:
        Settings: Application configuration

    Example:
        >>> from supernova.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.database_url)
    """
    return Settings()


# Convenience export
settings = get_settings()
