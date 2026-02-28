#!/usr/bin/env python3
"""Fail CI when forbidden local-secret or artifact files are tracked."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_EXACT = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
}

ALLOWED_ENV_TEMPLATES = {
    ".env.example",
    ".env.production.example",
}

FORBIDDEN_SUFFIXES = (
    ".tar.gz",
    ".zip",
    ".bak",
    ".dump",
    ".sqlite",
)

FORBIDDEN_PREFIXES = (
    "proof_bundle",
    "backup_",
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def find_violations(paths: list[str]) -> list[str]:
    violations: list[str] = []

    for raw_path in paths:
        path = Path(raw_path)
        name = path.name

        if name in FORBIDDEN_EXACT:
            violations.append(f"forbidden tracked environment file: {raw_path}")
            continue

        if name.startswith(".env") and name not in ALLOWED_ENV_TEMPLATES:
            violations.append(f"unexpected tracked environment file: {raw_path}")
            continue

        if name.startswith(FORBIDDEN_PREFIXES):
            violations.append(f"forbidden generated artifact: {raw_path}")
            continue

        if name.endswith(FORBIDDEN_SUFFIXES):
            violations.append(f"forbidden archive or backup artifact: {raw_path}")

    return violations


def main() -> int:
    violations = find_violations(tracked_files())
    if not violations:
        print("Repository hygiene check passed.")
        return 0

    print("Repository hygiene check failed:", file=sys.stderr)
    for violation in violations:
        print(f" - {violation}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
