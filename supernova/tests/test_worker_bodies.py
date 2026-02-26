"""Tests for worker body execution paths (backup, consolidation, maintenance)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# workers/backup.py — _do_backup
# ---------------------------------------------------------------------------

class TestBackupWorkerBody:
    @pytest.mark.asyncio
    async def test_do_backup_disabled(self):
        from workers.backup import _do_backup

        settings = MagicMock()
        settings.backup.enabled = False
        with patch("supernova.config.get_settings", return_value=settings):
            result = await _do_backup()
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_do_backup_runs(self, tmp_path):
        from workers.backup import _do_backup

        settings = MagicMock()
        settings.backup.enabled = True

        mock_mgr = AsyncMock()
        mock_mgr.create_backup.return_value = tmp_path / "backup.tar.gz"
        mock_mgr.verify_backup.return_value = True
        mock_mgr.rotate_backups = MagicMock(return_value=2)

        backup_mod = MagicMock()
        backup_mod.BackupManager.from_settings = MagicMock(return_value=mock_mgr)

        with (
            patch("supernova.config.get_settings", return_value=settings),
            patch.dict("sys.modules", {"supernova.core.backup.manager": backup_mod}),
        ):
            result = await _do_backup()

        assert result["status"] == "ok"
        assert result["verified"] is True
        assert result["rotated"] == 2


# ---------------------------------------------------------------------------
# workers/consolidation.py — _do_consolidation, _do_crystallization
# ---------------------------------------------------------------------------

class TestConsolidationWorkerBody:
    @pytest.mark.asyncio
    async def test_do_consolidation_extracts_facts(self):
        from workers.consolidation import _do_consolidation

        mock_episodic = AsyncMock()
        mock_episodic.search.return_value = [
            {"fact": "Python is great", "uuid": "1"},
            {"content": "Redis is fast", "uuid": "2"},
            {"uuid": "3"},  # no content — should skip
        ]
        mock_semantic = AsyncMock()

        ep_mod = MagicMock()
        ep_mod.EpisodicMemoryStore = MagicMock(return_value=mock_episodic)
        sem_mod = MagicMock()
        sem_mod.SemanticMemoryStore = MagicMock(return_value=mock_semantic)

        with patch.dict(
            "sys.modules",
            {
                "supernova.core.memory.episodic": ep_mod,
                "supernova.core.memory.semantic": sem_mod,
            },
        ):
            result = await _do_consolidation()

        assert result["episodes_fetched"] == 3
        assert result["facts_extracted"] == 2
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_do_consolidation_handles_store_error(self):
        from workers.consolidation import _do_consolidation

        mock_episodic = AsyncMock()
        mock_episodic.search.return_value = [{"fact": "data", "uuid": "1"}]
        mock_semantic = AsyncMock()
        mock_semantic.store.side_effect = RuntimeError("db down")

        ep_mod = MagicMock()
        ep_mod.EpisodicMemoryStore = MagicMock(return_value=mock_episodic)
        sem_mod = MagicMock()
        sem_mod.SemanticMemoryStore = MagicMock(return_value=mock_semantic)

        with patch.dict(
            "sys.modules",
            {
                "supernova.core.memory.episodic": ep_mod,
                "supernova.core.memory.semantic": sem_mod,
            },
        ):
            result = await _do_consolidation()

        assert result["errors"] == 1

    @pytest.mark.asyncio
    async def test_do_crystallization_success(self):
        from workers.consolidation import _do_crystallization

        mock_worker = MagicMock()
        mock_worker.run_crystallization_cycle = AsyncMock(return_value={"crystallized": 3})

        mock_mod = MagicMock()
        mock_mod.SkillCrystallizationWorker = type("FakeWorker", (), {
            "__new__": lambda cls: mock_worker,
        })

        with patch("importlib.import_module", return_value=mock_mod):
            result = await _do_crystallization()

        assert result["crystallized"] == 3
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_do_crystallization_import_error(self):
        from workers.consolidation import _do_crystallization

        with patch("importlib.import_module", side_effect=ImportError("no module")):
            result = await _do_crystallization()

        assert result["errors"] == 1


# ---------------------------------------------------------------------------
# workers/maintenance.py — _do_forgetting
# ---------------------------------------------------------------------------

class TestMaintenanceWorkerBody:
    @pytest.mark.asyncio
    async def test_do_forgetting_parses_result(self):
        from workers.maintenance import _do_forgetting

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "CALL 42"

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_pg = AsyncMock()
        mock_pg.pool = mock_pool
        mock_pg.connect = AsyncMock()
        mock_pg.disconnect = AsyncMock()

        pg_mod = MagicMock()
        pg_mod.AsyncPostgresPool = MagicMock(return_value=mock_pg)

        with patch.dict("sys.modules", {"supernova.infrastructure.storage.postgres": pg_mod}):
            result = await _do_forgetting()

        assert result["rows_affected"] == 42
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_do_forgetting_no_digit_in_result(self):
        from workers.maintenance import _do_forgetting

        mock_conn = AsyncMock()
        mock_conn.execute.return_value = "CALL"

        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_pg = AsyncMock()
        mock_pg.pool = mock_pool
        mock_pg.connect = AsyncMock()
        mock_pg.disconnect = AsyncMock()

        pg_mod = MagicMock()
        pg_mod.AsyncPostgresPool = MagicMock(return_value=mock_pg)

        with patch.dict("sys.modules", {"supernova.infrastructure.storage.postgres": pg_mod}):
            result = await _do_forgetting()

        assert result["rows_affected"] == 0

    @pytest.mark.asyncio
    async def test_do_forgetting_connection_error(self):
        from workers.maintenance import _do_forgetting

        mock_pg = AsyncMock()
        mock_pg.connect.side_effect = RuntimeError("connection refused")

        pg_mod = MagicMock()
        pg_mod.AsyncPostgresPool = MagicMock(return_value=mock_pg)

        with patch.dict("sys.modules", {"supernova.infrastructure.storage.postgres": pg_mod}):
            result = await _do_forgetting()

        assert result["errors"] == 1
