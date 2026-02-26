"""Diagnostic CLI: supernova doctor | logs | status | report."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

DEFAULT_BASE = "http://localhost:8000"


async def cmd_doctor(args: argparse.Namespace) -> None:
    """Check all dependencies, configs, and API connectivity."""
    base = args.base_url
    checks: list[tuple[str, str, str]] = []  # (name, status, detail)

    # 1. Python version
    v = sys.version_info
    checks.append(("python", "ok" if v >= (3, 12) else "warn", f"{v.major}.{v.minor}.{v.micro}"))

    # 2. Docker
    docker = shutil.which("docker")
    checks.append(("docker", "ok" if docker else "missing", docker or "not found"))

    # 3. .env file
    env_path = Path(".env")
    checks.append((".env", "ok" if env_path.exists() else "missing", str(env_path.resolve())))

    # 4. API connectivity
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{base}/health")
            checks.append(("api", "ok" if r.status_code == 200 else "error", f"HTTP {r.status_code}"))
    except Exception as exc:
        checks.append(("api", "error", str(exc)[:80]))

    # 5. Deep health (if API is up)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{base}/health/deep")
            if r.status_code == 200:
                data = r.json()
                for svc in data.get("services", []):
                    checks.append((svc["name"], svc["status"], f'{svc["latency_ms"]}ms'))
    except Exception:
        pass

    print("\n  SuperNova Doctor\n  " + "=" * 40)
    for name, status, detail in checks:
        icon = {"ok": "✓", "warn": "⚠", "missing": "✗", "error": "✗", "healthy": "✓", "degraded": "⚠", "unhealthy": "✗"}.get(status, "?")
        print(f"  {icon} {name:<20} {status:<10} {detail}")
    print()


async def cmd_logs(args: argparse.Namespace) -> None:
    """Stream or tail log files."""
    log_path = Path(args.log_dir) / "supernova.log"
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        return
    lines = log_path.read_text().splitlines()
    tail = lines[-(args.tail):]
    if args.filter:
        tail = [l for l in tail if args.filter in l]
    for line in tail:
        print(line)


async def cmd_status(args: argparse.Namespace) -> None:
    """Show service status, version, uptime."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{args.base_url}/health")
            data = r.json()
            print(f"\n  Status:  {data.get('status', 'unknown')}")
            print(f"  Version: {data.get('version', 'unknown')}")
    except Exception as exc:
        print(f"\n  API unreachable: {exc}")


async def cmd_report(args: argparse.Namespace) -> None:
    """Generate a diagnostic bundle."""
    report: dict = {"generated_at": datetime.now(timezone.utc).isoformat(), "checks": {}}

    # Collect doctor checks
    report["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    report["docker"] = bool(shutil.which("docker"))

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{args.base_url}/health/deep")
            if r.status_code == 200:
                report["health"] = r.json()
            r2 = await client.get(f"{args.base_url}/metrics")
            if r2.status_code == 200:
                report["metrics_snapshot"] = r2.text[:2000]
    except Exception as exc:
        report["api_error"] = str(exc)[:200]

    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2))
    print(f"Diagnostic report written to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="supernova-diag", description="SuperNova diagnostics")
    parser.add_argument("--base-url", default=DEFAULT_BASE, help="API base URL")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check dependencies and connectivity")

    lp = sub.add_parser("logs", help="Tail log files")
    lp.add_argument("--tail", type=int, default=50, help="Number of lines")
    lp.add_argument("--filter", help="Filter string")
    lp.add_argument("--log-dir", default="logs", help="Log directory")

    sub.add_parser("status", help="Show service status")

    rp = sub.add_parser("report", help="Generate diagnostic bundle")
    rp.add_argument("--output", default="supernova-diagnostic.json", help="Output file")

    args = parser.parse_args()
    coro = {"doctor": cmd_doctor, "logs": cmd_logs, "status": cmd_status, "report": cmd_report}[args.command]
    asyncio.run(coro(args))


if __name__ == "__main__":
    main()
