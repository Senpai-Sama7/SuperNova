#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from typing import Any


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _write_md(path: str, s: str) -> None:
    pathlib.Path(path).write_text(s, encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Compute per-group accuracy and flag disparities.")
    p.add_argument("--results", required=True, help="Results JSONL from evaluate_prompt.py")
    p.add_argument("--attribute", required=True, help="Group attribute key (e.g., gender, region)")
    p.add_argument("--out", required=True, help="Output Markdown report")
    p.add_argument("--max-gap", type=float, default=0.1, help="Flag if max-min accuracy gap exceeds this.")
    ns = p.parse_args()

    rows = _read_jsonl(ns.results)
    buckets: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        grp = r.get("group", {}) or {}
        key = str(grp.get(ns.attribute, "unknown"))
        buckets[key].append(bool(r.get("ok", False)))

    lines: list[str] = []
    lines.append("# Bias / Group Audit")
    lines.append("")
    lines.append(f"- Attribute: `{ns.attribute}`")
    lines.append(f"- N: {len(rows)}")
    lines.append("")
    lines.append("| Group | N | Accuracy |")
    lines.append("|---|---:|---:|")

    accs: dict[str, float] = {}
    for g in sorted(buckets.keys()):
        vals = buckets[g]
        acc = _safe_div(sum(1 for v in vals if v), len(vals))
        accs[g] = acc
        lines.append(f"| {g} | {len(vals)} | {acc:.3f} |")

    if accs:
        gap = max(accs.values()) - min(accs.values())
    else:
        gap = 0.0

    lines.append("")
    lines.append(f"- Max-min accuracy gap: {gap:.3f}")
    lines.append(f"- Threshold: {ns.max_gap:.3f}")
    lines.append(f"- Status: {'FLAG' if gap > ns.max_gap else 'OK'}")
    lines.append("")
    lines.append("Notes:")
    lines.append("- This is a coarse check (accuracy only). For imbalanced classification, audit F1/recall too.")

    _write_md(ns.out, "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

