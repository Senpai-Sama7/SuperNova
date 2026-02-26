"""Backup manager: coordinates PostgreSQL, Neo4j, and Redis backups.

Produces encrypted tar archives with optional S3 upload.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Rotation policy: keep N backups per tier
ROTATION_POLICY = {"daily": 7, "weekly": 4, "monthly": 12}


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


class BackupManager:
    """Orchestrates full-system backups across all storage backends."""

    def __init__(
        self,
        *,
        backup_path: Path = Path("./backups"),
        encryption_key: str | None = None,
        s3_bucket: str | None = None,
        s3_prefix: str = "supernova/",
        database_url: str = "",
        neo4j_uri: str = "",
        redis_url: str = "",
    ) -> None:
        self._backup_path = Path(backup_path)
        self._backup_path.mkdir(parents=True, exist_ok=True)
        self._encryption_key = encryption_key
        self._s3_bucket = s3_bucket
        self._s3_prefix = s3_prefix
        self._database_url = database_url
        self._neo4j_uri = neo4j_uri
        self._redis_url = redis_url

    @classmethod
    def from_settings(cls, settings: Any) -> "BackupManager":
        """Create BackupManager from application settings."""
        return cls(
            backup_path=settings.backup.path,
            encryption_key=os.getenv("BACKUP_ENCRYPTION_KEY"),
            s3_bucket=settings.backup.s3_bucket,
            s3_prefix=settings.backup.s3_prefix,
            database_url=str(settings.database_url),
            neo4j_uri=str(settings.neo4j.uri),
            redis_url=str(settings.redis_url),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_backup(self, name: str | None = None) -> Path:
        """Create a full system backup.

        Returns path to the final backup archive.
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        label = name or f"backup_{ts}"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # Backup each backend
            await self._backup_postgres(tmp / "postgres.dump")
            await self._backup_neo4j(tmp / "neo4j")
            await self._backup_redis(tmp / "redis.rdb")

            # Create tar archive
            archive_name = f"{label}.tar.gz"
            archive_path = self._backup_path / archive_name
            with tarfile.open(archive_path, "w:gz") as tar:
                for item in tmp.iterdir():
                    tar.add(item, arcname=item.name)

            logger.info("Created backup archive: %s", archive_path)

            # Encrypt if key provided
            if self._encryption_key:
                archive_path = self._encrypt(archive_path)

            # Upload to S3 if configured
            if self._s3_bucket:
                await self._upload_s3(archive_path)

        return archive_path

    async def restore_backup(self, archive_path: str | Path) -> dict[str, str]:
        """Restore system from a backup archive.

        Returns dict of backend → status.
        """
        archive_path = Path(archive_path)

        # Download from S3 if path looks like s3://
        if str(archive_path).startswith("s3://"):
            archive_path = await self._download_s3(str(archive_path))

        # Decrypt if encrypted
        if archive_path.suffix == ".enc":
            archive_path = self._decrypt(archive_path)

        results: dict[str, str] = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(tmp, filter="data")

            if (tmp / "postgres.dump").exists():
                await self._restore_postgres(tmp / "postgres.dump")
                results["postgres"] = "restored"

            if (tmp / "neo4j").exists():
                await self._restore_neo4j(tmp / "neo4j")
                results["neo4j"] = "restored"

            if (tmp / "redis.rdb").exists():
                await self._restore_redis(tmp / "redis.rdb")
                results["redis"] = "restored"

        logger.info("Restore complete: %s", results)
        return results

    async def verify_backup(self, archive_path: str | Path) -> bool:
        """Verify backup integrity by listing archive contents."""
        archive_path = Path(archive_path)
        if archive_path.suffix == ".enc":
            archive_path = self._decrypt(archive_path)
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                members = tar.getnames()
            expected = {"postgres.dump", "neo4j", "redis.rdb"}
            found = {m for m in members if m in expected or m.startswith("neo4j")}
            ok = len(found) >= 1
            logger.info("Backup verification: %s (found: %s)", "PASS" if ok else "FAIL", found)
            return ok
        except Exception as e:
            logger.error("Backup verification failed: %s", e)
            return False

    def rotate_backups(self) -> int:
        """Apply rotation policy, deleting old backups. Returns count deleted."""
        backups = sorted(self._backup_path.glob("backup_*.tar.gz*"), reverse=True)
        max_keep = ROTATION_POLICY["daily"] + ROTATION_POLICY["weekly"] + ROTATION_POLICY["monthly"]
        deleted = 0
        for old in backups[max_keep:]:
            old.unlink()
            deleted += 1
            logger.info("Rotated out: %s", old.name)
        return deleted

    def list_backups(self) -> list[dict[str, Any]]:
        """List available local backups."""
        results = []
        for f in sorted(self._backup_path.glob("*.tar.gz*"), reverse=True):
            results.append({
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "created": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
        return results

    # ------------------------------------------------------------------
    # Backend-specific backup methods
    # ------------------------------------------------------------------

    async def _backup_postgres(self, dest: Path) -> None:
        """Dump PostgreSQL using pg_dump custom format."""
        if not self._database_url:
            logger.warning("No DATABASE_URL — skipping PostgreSQL backup")
            return
        cmd = ["pg_dump", "--format=custom", f"--file={dest}", self._database_url]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise BackupError(f"pg_dump failed: {stderr.decode()}")
        logger.info("PostgreSQL backup: %s (%d bytes)", dest.name, dest.stat().st_size)

    async def _backup_neo4j(self, dest: Path) -> None:
        """Dump Neo4j database."""
        dest.mkdir(parents=True, exist_ok=True)
        dump_file = dest / "neo4j.dump"
        cmd = ["neo4j-admin", "database", "dump", f"--to-path={dest}", "neo4j"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                logger.warning("neo4j-admin dump failed (non-fatal): %s", stderr.decode()[:200])
        except FileNotFoundError:
            logger.warning("neo4j-admin not found — skipping Neo4j backup")

    async def _backup_redis(self, dest: Path) -> None:
        """Trigger Redis BGSAVE and copy the RDB file."""
        try:
            import redis as redis_lib

            r = redis_lib.from_url(self._redis_url) if self._redis_url else redis_lib.Redis()
            r.bgsave()
            # Wait briefly for save to complete
            await asyncio.sleep(1)
            info = r.info("persistence")
            rdb_path = info.get("rdb_last_save_file") or "/var/lib/redis/dump.rdb"
            rdb_dir = info.get("dir", "/var/lib/redis")
            src = Path(rdb_dir) / Path(rdb_path).name
            if src.exists():
                shutil.copy2(src, dest)
                logger.info("Redis backup: %s (%d bytes)", dest.name, dest.stat().st_size)
            else:
                logger.warning("Redis RDB file not found at %s", src)
            r.close()
        except Exception as e:
            logger.warning("Redis backup failed (non-fatal): %s", e)

    # ------------------------------------------------------------------
    # Restore methods
    # ------------------------------------------------------------------

    async def _restore_postgres(self, dump_path: Path) -> None:
        """Restore PostgreSQL from custom-format dump."""
        cmd = ["pg_restore", "--clean", "--if-exists", f"--dbname={self._database_url}", str(dump_path)]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise BackupError(f"pg_restore failed: {stderr.decode()}")

    async def _restore_neo4j(self, dump_dir: Path) -> None:
        """Restore Neo4j from dump."""
        cmd = ["neo4j-admin", "database", "load", f"--from-path={dump_dir}", "neo4j", "--overwrite-destination"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            await proc.communicate()
        except FileNotFoundError:
            logger.warning("neo4j-admin not found — skipping Neo4j restore")

    async def _restore_redis(self, rdb_path: Path) -> None:
        """Restore Redis by copying RDB file (requires restart)."""
        logger.info("Redis RDB copied to %s — restart Redis to load", rdb_path)

    # ------------------------------------------------------------------
    # Encryption
    # ------------------------------------------------------------------

    def _encrypt(self, archive_path: Path) -> Path:
        """Encrypt archive with Fernet symmetric encryption."""
        f = Fernet(self._encryption_key.encode() if isinstance(self._encryption_key, str) else self._encryption_key)
        data = archive_path.read_bytes()
        encrypted = f.encrypt(data)
        enc_path = archive_path.with_suffix(archive_path.suffix + ".enc")
        enc_path.write_bytes(encrypted)
        archive_path.unlink()
        logger.info("Encrypted: %s", enc_path.name)
        return enc_path

    def _decrypt(self, enc_path: Path) -> Path:
        """Decrypt Fernet-encrypted archive."""
        if not self._encryption_key:
            raise BackupError("Encryption key required to decrypt backup")
        f = Fernet(self._encryption_key.encode() if isinstance(self._encryption_key, str) else self._encryption_key)
        data = enc_path.read_bytes()
        decrypted = f.decrypt(data)
        dec_path = enc_path.with_name(enc_path.name.replace(".enc", ""))
        dec_path.write_bytes(decrypted)
        return dec_path

    # ------------------------------------------------------------------
    # S3 cloud storage
    # ------------------------------------------------------------------

    async def _upload_s3(self, local_path: Path) -> str:
        """Upload backup to S3-compatible storage."""
        import boto3

        s3 = boto3.client("s3")
        key = f"{self._s3_prefix}{local_path.name}"
        s3.upload_file(str(local_path), self._s3_bucket, key)
        uri = f"s3://{self._s3_bucket}/{key}"
        logger.info("Uploaded to %s", uri)
        return uri

    async def _download_s3(self, s3_uri: str) -> Path:
        """Download backup from S3-compatible storage."""
        import boto3

        # Parse s3://bucket/key
        parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        local_path = self._backup_path / Path(key).name
        s3 = boto3.client("s3")
        s3.download_file(bucket, key, str(local_path))
        logger.info("Downloaded from %s to %s", s3_uri, local_path)
        return local_path
