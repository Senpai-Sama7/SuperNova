"""Tests for Phase 12: Backup, Recovery & Data Portability."""

from __future__ import annotations

import tarfile
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from supernova.core.backup.manager import BackupManager, BackupError, ROTATION_POLICY


# ── BackupManager ─────────────────────────────────────────────────────────────


class TestBackupManager:
    """Tests for BackupManager core functionality."""

    @pytest.fixture
    def tmp_backup_dir(self, tmp_path):
        return tmp_path / "backups"

    @pytest.fixture
    def manager(self, tmp_backup_dir):
        return BackupManager(
            backup_path=tmp_backup_dir,
            database_url="postgresql://test:test@localhost/test",
            neo4j_uri="bolt://localhost:7687",
            redis_url="redis://localhost:6379/0",
        )

    @pytest.mark.asyncio
    async def test_create_backup_produces_tarball(self, manager, tmp_backup_dir):
        """create_backup produces a .tar.gz archive."""
        with patch.object(manager, "_backup_postgres", new_callable=AsyncMock) as pg, \
             patch.object(manager, "_backup_neo4j", new_callable=AsyncMock) as neo, \
             patch.object(manager, "_backup_redis", new_callable=AsyncMock) as redis:
            # Make stubs create dummy files
            async def _pg(dest):
                dest.write_bytes(b"pgdump")
            async def _neo(dest):
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "neo4j.dump").write_bytes(b"neo4j")
            async def _redis(dest):
                dest.write_bytes(b"rdb")
            pg.side_effect = _pg
            neo.side_effect = _neo
            redis.side_effect = _redis

            archive = await manager.create_backup(name="test_backup")
            assert archive.exists()
            assert archive.name == "test_backup.tar.gz"
            with tarfile.open(archive, "r:gz") as tar:
                names = tar.getnames()
            assert "postgres.dump" in names

    @pytest.mark.asyncio
    async def test_verify_backup_valid(self, manager, tmp_backup_dir):
        """verify_backup returns True for valid archive."""
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)
        archive = tmp_backup_dir / "test.tar.gz"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "postgres.dump"
            p.write_bytes(b"data")
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(p, arcname="postgres.dump")
        assert await manager.verify_backup(archive) is True

    @pytest.mark.asyncio
    async def test_verify_backup_invalid(self, manager, tmp_backup_dir):
        """verify_backup returns False for corrupt file."""
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)
        bad = tmp_backup_dir / "bad.tar.gz"
        bad.write_bytes(b"not a tarball")
        assert await manager.verify_backup(bad) is False

    def test_list_backups_empty(self, manager, tmp_backup_dir):
        """list_backups returns empty list when no backups exist."""
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)
        assert manager.list_backups() == []

    def test_list_backups_finds_archives(self, manager, tmp_backup_dir):
        """list_backups finds .tar.gz files."""
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)
        (tmp_backup_dir / "backup_20260226.tar.gz").write_bytes(b"data")
        result = manager.list_backups()
        assert len(result) == 1
        assert "backup_20260226.tar.gz" in result[0]["name"]

    def test_rotate_backups_deletes_old(self, manager, tmp_backup_dir):
        """rotate_backups removes excess backups beyond policy limit."""
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)
        max_keep = sum(ROTATION_POLICY.values())
        for i in range(max_keep + 5):
            (tmp_backup_dir / f"backup_{i:04d}.tar.gz").write_bytes(b"x")
        deleted = manager.rotate_backups()
        assert deleted == 5
        remaining = list(tmp_backup_dir.glob("backup_*.tar.gz"))
        assert len(remaining) == max_keep

    @pytest.mark.asyncio
    async def test_restore_backup(self, manager, tmp_backup_dir):
        """restore_backup extracts and calls restore methods."""
        tmp_backup_dir.mkdir(parents=True, exist_ok=True)
        archive = tmp_backup_dir / "restore_test.tar.gz"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "postgres.dump"
            p.write_bytes(b"pgdata")
            with tarfile.open(archive, "w:gz") as tar:
                tar.add(p, arcname="postgres.dump")

        with patch.object(manager, "_restore_postgres", new_callable=AsyncMock) as rp:
            result = await manager.restore_backup(archive)
            assert result["postgres"] == "restored"
            rp.assert_called_once()


class TestBackupEncryption:
    """Tests for Fernet encryption/decryption."""

    @pytest.fixture
    def manager(self, tmp_path):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        return BackupManager(backup_path=tmp_path, encryption_key=key)

    def test_encrypt_decrypt_roundtrip(self, manager, tmp_path):
        """Encrypt then decrypt produces original content."""
        original = tmp_path / "test.tar.gz"
        original.write_bytes(b"secret backup data")
        encrypted = manager._encrypt(original)
        assert encrypted.suffix == ".enc"
        assert not original.exists()
        decrypted = manager._decrypt(encrypted)
        assert decrypted.read_bytes() == b"secret backup data"

    def test_decrypt_without_key_raises(self, tmp_path):
        """Decrypting without key raises BackupError."""
        mgr = BackupManager(backup_path=tmp_path)
        enc = tmp_path / "test.tar.gz.enc"
        enc.write_bytes(b"encrypted")
        with pytest.raises(BackupError, match="Encryption key required"):
            mgr._decrypt(enc)


# ── Celery Worker ─────────────────────────────────────────────────────────────


class TestBackupWorker:
    """Tests for the Celery backup task."""

    @pytest.mark.asyncio
    async def test_daily_backup_disabled(self):
        """Skips backup when disabled in settings."""
        from supernova.workers.backup import _do_backup

        mock_settings = MagicMock()
        mock_settings.backup.enabled = False
        with patch("supernova.config.get_settings", return_value=mock_settings):
            result = await _do_backup()
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_daily_backup_runs(self, tmp_path):
        """Runs full backup cycle when enabled."""
        from supernova.workers.backup import _do_backup

        mock_settings = MagicMock()
        mock_settings.backup.enabled = True
        mock_settings.backup.path = tmp_path
        mock_settings.backup.s3_bucket = None
        mock_settings.backup.s3_prefix = "supernova/"
        mock_settings.database_url = "postgresql://x"
        mock_settings.neo4j.uri = "bolt://x"
        mock_settings.redis_url = "redis://x"

        mock_mgr = AsyncMock()
        mock_mgr.create_backup.return_value = tmp_path / "test.tar.gz"
        mock_mgr.verify_backup.return_value = True
        mock_mgr.rotate_backups.return_value = 0

        with patch("supernova.config.get_settings", return_value=mock_settings), \
             patch("supernova.core.backup.manager.BackupManager.from_settings", return_value=mock_mgr):
            result = await _do_backup()
        assert result["status"] == "ok"
        assert result["verified"] is True


# ── Celery Beat Schedule ──────────────────────────────────────────────────────


class TestCelerySchedule:
    """Verify backup worker is importable and callable."""

    def test_backup_task_importable(self):
        """Verify the daily_backup function can be imported."""
        from supernova.workers.backup import daily_backup
        assert callable(daily_backup)


# ── Memory Export/Import API ──────────────────────────────────────────────────


class TestMemoryExportImport:
    """Tests for /memory/export and /memory/import endpoints."""

    @pytest.fixture
    def client(self):
        from supernova.api.gateway import app, _state, get_current_user
        from starlette.testclient import TestClient

        mock_store = AsyncMock()
        mock_store.search.return_value = [
            {"id": "1", "content": "Test memory", "category": "general", "created_at": "2026-01-01"},
        ]
        mock_store.get_by_category.return_value = [
            {"id": "1", "content": "Test memory", "category": "general"},
        ]
        mock_store.upsert = AsyncMock()
        _state["semantic_store"] = mock_store

        app.dependency_overrides[get_current_user] = lambda: "test-user"
        yield TestClient(app)
        app.dependency_overrides.clear()
        _state.pop("semantic_store", None)

    def test_export_json(self, client):
        resp = client.get("/memory/export?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["memories"][0]["content"] == "Test memory"

    def test_export_markdown(self, client):
        resp = client.get("/memory/export?format=markdown")
        assert resp.status_code == 200
        assert "# SuperNova Memory Export" in resp.text

    def test_export_with_category_filter(self, client):
        resp = client.get("/memory/export?format=json&category=general")
        assert resp.status_code == 200

    def test_import_memories(self, client):
        payload = {"memories": [{"content": "Imported memory", "metadata": {}}]}
        resp = client.post("/memory/import", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 1

    def test_import_skips_empty_content(self, client):
        payload = {"memories": [{"content": ""}, {"content": "Valid"}]}
        resp = client.post("/memory/import", json=payload)
        data = resp.json()
        assert data["imported"] == 1
        assert data["total_submitted"] == 2


# ── CLI ───────────────────────────────────────────────────────────────────────


class TestCLI:
    """Tests for the backup CLI."""

    def test_cli_backup_list(self, tmp_path):
        from supernova.core.backup.cli import main
        import sys

        mock_mgr = MagicMock()
        mock_mgr.list_backups.return_value = [
            {"name": "test.tar.gz", "size_bytes": 100, "created": "2026-01-01"},
        ]
        with patch("supernova.core.backup.cli._get_manager", return_value=mock_mgr), \
             patch.object(sys, "argv", ["cli", "backup", "--list"]):
            main()
        mock_mgr.list_backups.assert_called_once()

    def test_cli_backup_create(self, tmp_path):
        from supernova.core.backup.cli import main
        import sys

        mock_mgr = AsyncMock()
        mock_mgr.create_backup.return_value = tmp_path / "test.tar.gz"
        mock_mgr.verify_backup.return_value = True
        mock_mgr.rotate_backups.return_value = 0
        with patch("supernova.core.backup.cli._get_manager", return_value=mock_mgr), \
             patch.object(sys, "argv", ["cli", "backup", "--name", "test"]):
            main()
        mock_mgr.create_backup.assert_called_once()

    def test_cli_restore(self, tmp_path):
        from supernova.core.backup.cli import main
        import sys

        mock_mgr = AsyncMock()
        mock_mgr.restore_backup.return_value = {"postgres": "restored"}
        with patch("supernova.core.backup.cli._get_manager", return_value=mock_mgr), \
             patch.object(sys, "argv", ["cli", "restore", "--from", "backup.tar.gz"]):
            main()
        mock_mgr.restore_backup.assert_called_once()
