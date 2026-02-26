#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import pathlib
import random
import re


TECHNIQUES = {
    "role": "Add a role/responsibility header.",
    "output_contract": "Add strict output contract instructions.",
    "few_shot": "Add a few labeled examples.",
    "contrastive": "Add contrastive near-boundary examples.",
    "self_check": "Add a self-check checklist.",
    "step_back": "Add a step-back framing line.",
}


def _read_text(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")


def _write_text(path: str, content: str) -> None:
    pathlib.Path(path).write_text(content, encoding="utf-8")


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80] or "variation"


def _apply_role(base: str, role: str) -> str:
    return f"You are {role}.\nYour job is to follow the instructions exactly.\n\n{base}"


def _apply_output_contract(base: str, contract: str) -> str:
    return f"{base}\n\nOutput contract:\n{contract}\n"


def _apply_step_back(base: str) -> str:
    return "Before answering, restate the goal in one sentence.\n\n" + base


def _apply_self_check(base: str, checklist: str) -> str:
    return f"{base}\n\nSelf-check before final output:\n{checklist}\n"


def _apply_examples(base: str, examples: str, header: str) -> str:
    return f"{base}\n\n{header}\n{examples}\n"


def main() -> int:
    p = argparse.ArgumentParser(description="Generate prompt variations by applying named techniques.")
    p.add_argument("--base-prompt", required=True, help="Path to base prompt text.")
    p.add_argument("--out-dir", required=True, help="Output directory.")
    p.add_argument("--techniques", required=True, help="Comma-separated technique names.")
    p.add_argument("--num-variations", type=int, default=3)
    p.add_argument("--role", default="a careful assistant", help="Role text for role technique.")
    p.add_argument("--output-contract", default="Return only the answer. No extra text.", help="Contract text.")
    p.add_argument("--checklist", default="- Output matches contract\n- No extra commentary", help="Checklist text.")
    p.add_argument("--examples-file", default="", help="Optional examples text to insert (few-shot/contrastive).")
    p.add_argument("--seed", type=int, default=0)
    ns = p.parse_args()

    base = _read_text(ns.base_prompt).strip() + "\n"
    out_dir = pathlib.Path(ns.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    techs = [t.strip() for t in ns.techniques.split(",") if t.strip()]
    unknown = [t for t in techs if t not in TECHNIQUES]
    if unknown:
        raise SystemExit(f"unknown techniques: {', '.join(unknown)} (known: {', '.join(sorted(TECHNIQUES))})")

    examples_text = _read_text(ns.examples_file).strip() if ns.examples_file else ""

    rng = random.Random(ns.seed)
    for i in range(ns.num_variations):
        content = base

        # Shuffle application order a bit to explore interaction effects.
        order = techs[:]
        rng.shuffle(order)

        for t in order:
            if t == "role":
                content = _apply_role(content, ns.role)
            elif t == "output_contract":
                content = _apply_output_contract(content, ns.output_contract)
            elif t == "step_back":
                content = _apply_step_back(content)
            elif t == "self_check":
                content = _apply_self_check(content, ns.checklist)
            elif t == "few_shot":
                if not examples_text:
                    continue
                content = _apply_examples(content, examples_text, header="Examples (few-shot):")
            elif t == "contrastive":
                if not examples_text:
                    continue
                content = _apply_examples(content, examples_text, header="Examples (contrastive):")

        name = f"{i+1:02d}-{_slug('-'.join(order))}.txt"
        _write_text(str(out_dir / name), content)

    # Write a small manifest.
    manifest = out_dir / "manifest.txt"
    _write_text(
        str(manifest),
        "Generated variations:\n"
        + "\n".join(sorted([p.name for p in out_dir.glob("*.txt") if p.name != "manifest.txt"]))
        + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

