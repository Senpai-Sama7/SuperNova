"""CLI for backup, restore, and memory export operations.

Usage:
    python -m supernova.core.backup.cli backup [--name NAME] [--list]
    python -m supernova.core.backup.cli restore --from PATH
    python -m supernova.core.backup.cli export [--format json|markdown] [--output PATH]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


def _get_manager():
    from supernova.config import get_settings
    from supernova.core.backup.manager import BackupManager
    return BackupManager.from_settings(get_settings())


async def cmd_backup(args: argparse.Namespace) -> None:
    """Create or list backups."""
    mgr = _get_manager()
    if args.list:
        for b in mgr.list_backups():
            print(f"  {b['name']}  ({b['size_bytes']} bytes)  {b['created']}")
        return
    archive = await mgr.create_backup(name=args.name)
    print(f"Backup created: {archive}")
    verified = await mgr.verify_backup(archive)
    print(f"Verified: {verified}")
    deleted = mgr.rotate_backups()
    if deleted:
        print(f"Rotated {deleted} old backup(s)")


async def cmd_restore(args: argparse.Namespace) -> None:
    """Restore from a backup archive."""
    mgr = _get_manager()
    source = args.source
    results = await mgr.restore_backup(source)
    for backend, status in results.items():
        print(f"  {backend}: {status}")


async def cmd_export(args: argparse.Namespace) -> None:
    """Export memories to file."""
    import httpx

    base = "http://127.0.0.1:8000"
    token = args.token or ""
    fmt = args.format
    url = f"{base}/memory/export?format={fmt}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    output = Path(args.output) if args.output else Path(f"supernova-export.{fmt if fmt == 'json' else 'md'}")
    output.write_bytes(resp.content)
    print(f"Exported to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="supernova", description="SuperNova backup & export CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # backup
    bp = sub.add_parser("backup", help="Create or list backups")
    bp.add_argument("--name", help="Backup name (default: timestamped)")
    bp.add_argument("--list", action="store_true", help="List existing backups")

    # restore
    rp = sub.add_parser("restore", help="Restore from backup")
    rp.add_argument("--from", dest="source", required=True, help="Backup file or s3:// URI")

    # export
    ep = sub.add_parser("export", help="Export memories")
    ep.add_argument("--format", choices=["json", "markdown"], default="json")
    ep.add_argument("--output", help="Output file path")
    ep.add_argument("--token", help="Auth token")

    args = parser.parse_args()

    if args.command == "backup":
        asyncio.run(cmd_backup(args))
    elif args.command == "restore":
        asyncio.run(cmd_restore(args))
    elif args.command == "export":
        asyncio.run(cmd_export(args))


if __name__ == "__main__":
    main()
