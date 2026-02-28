"""Tests for worker startup runtime configuration guardrails."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


_celery_mod = ModuleType("celery")
_celery_sched = ModuleType("celery.schedules")


class _FakeCrontab:
    def __init__(self, **kw):
        self.kw = kw


_celery_sched.crontab = _FakeCrontab


class _FakeCelery:
    def __init__(self, name, **kw):
        self.name = name
        self.conf = type("Conf", (), {"update": lambda self, **kwargs: None})()

    def autodiscover_tasks(self, modules):
        self._discovered = modules


_celery_mod.Celery = _FakeCelery
sys.modules.setdefault("celery", _celery_mod)
sys.modules.setdefault("celery.schedules", _celery_sched)
sys.modules.setdefault("redbeat", ModuleType("redbeat"))


@pytest.fixture
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "SUPERNOVA_ENV",
        "SUPERNOVA_SECRET_KEY",
        "POSTGRES_PASSWORD",
        "NEO4J_PASSWORD",
        "LITELLM_MASTER_KEY",
        "PICKLE_HMAC_KEY",
        "API_KEY_ENCRYPTION_KEY",
        "CORS_ORIGINS",
        "CODE_SANDBOX",
    ]:
        monkeypatch.delenv(key, raising=False)


def _reload_worker_module() -> None:
    module_name = "supernova.workers.celery_app"
    if module_name in sys.modules:
        del sys.modules[module_name]
    importlib.import_module(module_name)


@pytest.mark.unit
def test_worker_import_allows_development_defaults(clear_env: None) -> None:
    _reload_worker_module()


@pytest.mark.unit
def test_worker_import_rejects_invalid_production_defaults(
    clear_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPERNOVA_ENV", "production")
    monkeypatch.setenv("SUPERNOVA_SECRET_KEY", "a" * 64)

    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        _reload_worker_module()


@pytest.mark.unit
def test_worker_import_accepts_secure_production_values(
    clear_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPERNOVA_ENV", "production")
    monkeypatch.setenv("SUPERNOVA_SECRET_KEY", "b" * 64)
    monkeypatch.setenv("POSTGRES_PASSWORD", "prod-db-password")
    monkeypatch.setenv("NEO4J_PASSWORD", "prod-neo4j-password")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "prod-litellm-master-key")
    monkeypatch.setenv("PICKLE_HMAC_KEY", "prod-hmac-key-material")
    monkeypatch.setenv("API_KEY_ENCRYPTION_KEY", "prod-encryption-key-material")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("CODE_SANDBOX", "docker")

    _reload_worker_module()
