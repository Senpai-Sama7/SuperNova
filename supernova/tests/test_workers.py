"""Tests for Phase 7: Background Workers."""

from __future__ import annotations

import asyncio
import sys
import time
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Mock celery + redbeat before any worker imports
# ---------------------------------------------------------------------------
_celery_mod = ModuleType("celery")
_celery_sched = ModuleType("celery.schedules")


class _FakeCrontab:
    def __init__(self, **kw):
        self.kw = kw


_celery_sched.crontab = _FakeCrontab


class _FakeCelery:
    def __init__(self, name, **kw):
        self.name = name
        self.conf = MagicMock()
        self.conf.beat_schedule = {}
        self._tasks = {}

    def task(self, **kw):
        def decorator(fn):
            self._tasks[kw.get("name", fn.__name__)] = fn
            return fn
        return decorator

    def autodiscover_tasks(self, modules):
        self._discovered = modules


_celery_mod.Celery = _FakeCelery
sys.modules.setdefault("celery", _celery_mod)
sys.modules.setdefault("celery.schedules", _celery_sched)
sys.modules.setdefault("redbeat", ModuleType("redbeat"))


# ---------------------------------------------------------------------------
# Task 7.1: Celery App Tests
# ---------------------------------------------------------------------------
class TestCeleryApp:
    def _import_app(self):
        # Force reimport to pick up mocks
        mod_name = "supernova.workers.celery_app"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        from supernova.workers.celery_app import app
        return app

    def test_app_created(self):
        app = self._import_app()
        assert app.name == "supernova"

    def test_beat_schedule_has_five_entries(self):
        app = self._import_app()
        # conf.update was called with beat_schedule
        call_args = app.conf.update.call_args
        schedule = call_args[1].get("beat_schedule") or call_args[0][0] if call_args[0] else None
        if schedule is None:
            # Try kwargs
            for call in app.conf.update.call_args_list:
                if "beat_schedule" in (call[1] if call[1] else {}):
                    schedule = call[1]["beat_schedule"]
                    break
        assert schedule is not None
        assert len(schedule) == 5
        expected_keys = {
            "consolidation-hourly",
            "heartbeat-15min",
            "forgetting-weekly",
            "skill-crystallization-daily",
            "mcp-health-5min",
        }
        assert set(schedule.keys()) == expected_keys

    def test_beat_schedule_task_names(self):
        app = self._import_app()
        schedule = app.conf.update.call_args[1]["beat_schedule"]
        assert schedule["consolidation-hourly"]["task"] == \
            "supernova.workers.consolidation.consolidate_episodic_memories"
        assert schedule["heartbeat-15min"]["task"] == \
            "supernova.workers.heartbeat.run_heartbeat_cycle"
        assert schedule["forgetting-weekly"]["task"] == \
            "supernova.workers.maintenance.run_forgetting_curves"
        assert schedule["skill-crystallization-daily"]["task"] == \
            "supernova.workers.consolidation.crystallize_skills"
        assert schedule["mcp-health-5min"]["task"] == \
            "supernova.workers.mcp_monitor.check_mcp_health"

    def test_redbeat_scheduler_configured(self):
        app = self._import_app()
        call_kw = app.conf.update.call_args[1]
        assert call_kw["beat_scheduler"] == "redbeat.RedBeatScheduler"

    def test_json_serializer(self):
        app = self._import_app()
        call_kw = app.conf.update.call_args[1]
        assert call_kw["task_serializer"] == "json"
        assert call_kw["result_serializer"] == "json"

    def test_autodiscover_modules(self):
        app = self._import_app()
        assert hasattr(app, "_discovered")
        assert "supernova.workers.consolidation" in app._discovered
        assert "supernova.workers.heartbeat" in app._discovered
        assert "supernova.workers.maintenance" in app._discovered
        assert "supernova.workers.mcp_monitor" in app._discovered


# ---------------------------------------------------------------------------
# Task 7.2: Consolidation Worker Tests
# ---------------------------------------------------------------------------
class TestConsolidationWorker:
    def test_consolidate_task_registered(self):
        from supernova.workers.consolidation import consolidate_episodic_memories
        assert callable(consolidate_episodic_memories)

    def test_crystallize_task_registered(self):
        from supernova.workers.consolidation import crystallize_skills
        assert callable(crystallize_skills)

    @pytest.mark.asyncio
    async def test_do_consolidation_success(self):
        mock_episodic = AsyncMock()
        mock_episodic.search = AsyncMock(return_value=[
            {"uuid": "1", "fact": "Python is great"},
            {"uuid": "2", "content": "LangGraph rocks"},
        ])
        mock_semantic = AsyncMock()
        mock_semantic.store = AsyncMock()

        ep_mod = MagicMock()
        ep_mod.EpisodicMemoryStore = lambda: mock_episodic
        sem_mod = MagicMock()
        sem_mod.SemanticMemoryStore = lambda: mock_semantic

        import supernova.workers.consolidation as cmod
        with patch.dict("sys.modules", {
            "supernova.core.memory.episodic": ep_mod,
            "supernova.core.memory.semantic": sem_mod,
        }):
            result = await cmod._do_consolidation()

        assert result["episodes_fetched"] == 2
        assert result["facts_extracted"] == 2
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_do_consolidation_handles_errors(self):
        mock_episodic = AsyncMock()
        mock_episodic.search = AsyncMock(side_effect=Exception("Neo4j down"))

        import supernova.workers.consolidation as cmod
        with patch.dict("sys.modules", {
            "supernova.core.memory.episodic": MagicMock(EpisodicMemoryStore=lambda: mock_episodic),
            "supernova.core.memory.semantic": MagicMock(),
        }):
            result = await cmod._do_consolidation()

        assert result["errors"] >= 1

    @pytest.mark.asyncio
    async def test_do_crystallization_handles_missing_module(self):
        import supernova.workers.consolidation as cmod
        with patch("importlib.import_module", side_effect=ModuleNotFoundError("no procedural")):
            result = await cmod._do_crystallization()
        assert result["errors"] >= 1


# ---------------------------------------------------------------------------
# Task 7.3: Heartbeat Worker Tests
# ---------------------------------------------------------------------------
class TestHeartbeatWorker:
    def test_heartbeat_task_registered(self):
        from supernova.workers.heartbeat import run_heartbeat_cycle
        assert callable(run_heartbeat_cycle)

    @pytest.mark.asyncio
    async def test_do_heartbeat_all_healthy(self):
        mock_redis = AsyncMock()
        mock_redis.connect = AsyncMock()
        mock_redis.disconnect = AsyncMock()
        mock_redis.client = AsyncMock()
        mock_redis.client.ping = AsyncMock(return_value=True)

        mock_pg = AsyncMock()
        mock_pg.connect = AsyncMock()
        mock_pg.disconnect = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock()))
        mock_pg.pool = mock_pool

        mock_episodic = AsyncMock()
        mock_episodic.initialize = AsyncMock()

        import supernova.workers.heartbeat as hmod
        with patch.dict("sys.modules", {
            "supernova.infrastructure.storage.redis": MagicMock(AsyncRedisClient=lambda: mock_redis),
            "supernova.infrastructure.storage.postgres": MagicMock(AsyncPostgresPool=lambda: mock_pg),
            "supernova.core.memory.episodic": MagicMock(EpisodicMemoryStore=lambda: mock_episodic),
            "langfuse": MagicMock(),
        }):
            result = await hmod._do_heartbeat()

        assert result["redis"] == "healthy"
        assert result["postgres"] == "healthy"
        assert result["neo4j"] == "healthy"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_do_heartbeat_redis_down(self):
        import supernova.workers.heartbeat as hmod
        with patch.dict("sys.modules", {
            "supernova.infrastructure.storage.redis": MagicMock(
                AsyncRedisClient=MagicMock(side_effect=Exception("Connection refused"))
            ),
            "supernova.infrastructure.storage.postgres": MagicMock(
                AsyncPostgresPool=MagicMock(side_effect=Exception("PG down"))
            ),
            "supernova.core.memory.episodic": MagicMock(
                EpisodicMemoryStore=MagicMock(side_effect=Exception("Neo4j down"))
            ),
        }):
            result = await hmod._do_heartbeat()

        assert "unhealthy" in result["redis"]
        assert "unhealthy" in result["postgres"]
        assert "unhealthy" in result["neo4j"]


# ---------------------------------------------------------------------------
# Task 7.4: Maintenance Worker Tests
# ---------------------------------------------------------------------------
class TestMaintenanceWorker:
    def test_forgetting_task_registered(self):
        from supernova.workers.maintenance import run_forgetting_curves
        assert callable(run_forgetting_curves)

    @pytest.mark.asyncio
    async def test_do_forgetting_success(self):
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="CALL 42")
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn),
            __aexit__=AsyncMock(),
        ))
        mock_pg = AsyncMock()
        mock_pg.connect = AsyncMock()
        mock_pg.disconnect = AsyncMock()
        mock_pg.pool = mock_pool

        import supernova.workers.maintenance as mmod
        with patch.dict("sys.modules", {
            "supernova.infrastructure.storage.postgres": MagicMock(AsyncPostgresPool=lambda: mock_pg),
        }):
            result = await mmod._do_forgetting()

        assert result["errors"] == 0
        assert result["rows_affected"] == 42

    @pytest.mark.asyncio
    async def test_do_forgetting_handles_error(self):
        import supernova.workers.maintenance as mmod
        with patch.dict("sys.modules", {
            "supernova.infrastructure.storage.postgres": MagicMock(
                AsyncPostgresPool=MagicMock(side_effect=Exception("PG down"))
            ),
        }):
            result = await mmod._do_forgetting()

        assert result["errors"] >= 1


# ---------------------------------------------------------------------------
# Task 7.5: MCP Health Monitor Tests
# ---------------------------------------------------------------------------
class TestMCPMonitor:
    def test_health_task_registered(self):
        from supernova.workers.mcp_monitor import check_mcp_health
        assert callable(check_mcp_health)

    def test_backoff_calculation(self):
        from supernova.workers.mcp_monitor import _backoff_seconds
        assert _backoff_seconds(1) == 30.0
        assert _backoff_seconds(2) == 60.0
        assert _backoff_seconds(3) == 120.0

    def test_backoff_caps_at_5(self):
        from supernova.workers.mcp_monitor import _backoff_seconds
        # 2^5 = 32, so 30 * 32 = 960
        assert _backoff_seconds(6) == 960.0
        assert _backoff_seconds(10) == 960.0  # capped

    @pytest.mark.asyncio
    async def test_do_health_check_all_healthy(self):
        mock_client = AsyncMock()
        mock_client.get_server_status = MagicMock(return_value=[
            {"name": "server1", "healthy": True, "config": None},
        ])
        mock_client.health_check = AsyncMock()

        import supernova.workers.mcp_monitor as mmod
        with patch.dict("sys.modules", {
            "supernova.mcp.client.mcp_client": MagicMock(MCPClient=lambda: mock_client),
        }):
            result = await mmod._do_health_check()

        assert result["checked"] == 1
        assert result["healthy"] == 1
        assert result["restarted"] == 0

    @pytest.mark.asyncio
    async def test_do_health_check_unhealthy_triggers_restart(self):
        mock_config = MagicMock()
        mock_client = AsyncMock()
        mock_client.get_server_status = MagicMock(return_value=[
            {"name": "bad-server", "healthy": False, "config": mock_config},
        ])
        mock_client.health_check = AsyncMock()
        mock_client.start_server = AsyncMock()

        import supernova.workers.mcp_monitor as mmod
        # Reset failure tracking
        mmod._failure_counts.clear()
        mmod._last_restart.clear()

        with patch.dict("sys.modules", {
            "supernova.mcp.client.mcp_client": MagicMock(MCPClient=lambda: mock_client),
        }):
            result = await mmod._do_health_check()

        assert result["restarted"] == 1
        assert mmod._failure_counts["bad-server"] == 1

    @pytest.mark.asyncio
    async def test_alert_after_max_failures(self):
        mock_client = AsyncMock()
        mock_client.get_server_status = MagicMock(return_value=[
            {"name": "flaky", "healthy": False, "config": MagicMock()},
        ])
        mock_client.health_check = AsyncMock()
        mock_client.start_server = AsyncMock()

        import supernova.workers.mcp_monitor as mmod
        mmod._failure_counts.clear()
        mmod._last_restart.clear()
        mmod._failure_counts["flaky"] = 2  # Will become 3

        with patch.dict("sys.modules", {
            "supernova.mcp.client.mcp_client": MagicMock(MCPClient=lambda: mock_client),
        }):
            result = await mmod._do_health_check()

        assert len(result["alerts"]) == 1
        assert "flaky" in result["alerts"][0]

    @pytest.mark.asyncio
    async def test_backoff_skips_restart(self):
        mock_client = AsyncMock()
        mock_client.get_server_status = MagicMock(return_value=[
            {"name": "backed-off", "healthy": False, "config": MagicMock()},
        ])
        mock_client.health_check = AsyncMock()
        mock_client.start_server = AsyncMock()

        import supernova.workers.mcp_monitor as mmod
        mmod._failure_counts.clear()
        mmod._last_restart.clear()
        # Pretend we just restarted
        mmod._last_restart["backed-off"] = time.time()
        mmod._failure_counts["backed-off"] = 1

        with patch.dict("sys.modules", {
            "supernova.mcp.client.mcp_client": MagicMock(MCPClient=lambda: mock_client),
        }):
            result = await mmod._do_health_check()

        # Should NOT restart due to backoff
        assert result["restarted"] == 0
