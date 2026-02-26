#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shlex
import subprocess
import sys
from typing import Any


def _read_text(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _run_predict_cmd(predict_cmd: str, prompt: str, timeout_s: int) -> str:
    """
    Run a user-provided command that reads the full prompt from stdin and prints the model output to stdout.
    This keeps the evaluator model-agnostic (OpenAI SDK, curl, local LLM, etc.).
    """
    proc = subprocess.run(
        predict_cmd,
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        timeout=timeout_s,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"predict cmd failed (rc={proc.returncode}): {predict_cmd}\n"
            f"stderr:\n{proc.stderr.decode('utf-8', errors='replace')}"
        )
    return proc.stdout.decode("utf-8", errors="replace").strip()


def main() -> int:
    p = argparse.ArgumentParser(description="Evaluate a prompt against a JSONL dataset.")
    p.add_argument("--prompt", required=True, help="Prompt file. Use {input} placeholder to inject input.")
    p.add_argument("--data", required=True, help="Dataset JSONL (see references/dataset_schema.md).")
    p.add_argument("--out", required=True, help="Output results JSONL.")
    p.add_argument("--predict-cmd", default="", help="Shell command to run. Reads prompt from stdin, outputs prediction.")
    p.add_argument("--max-examples", type=int, default=0)
    p.add_argument("--timeout-s", type=int, default=30)
    p.add_argument("--cache-dir", default="", help="Optional cache dir keyed by (prompt hash, id).")
    p.add_argument("--label-regex", default="", help="Optional regex to extract a label from model output.")
    ns = p.parse_args()

    prompt_tmpl = _read_text(ns.prompt)
    rows = _read_jsonl(ns.data)
    if ns.max_examples and ns.max_examples > 0:
        rows = rows[: ns.max_examples]

    prompt_hash = _sha256_text(prompt_tmpl)
    cache_dir = pathlib.Path(ns.cache_dir) if ns.cache_dir else None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)

    import re

    label_re = re.compile(ns.label_regex) if ns.label_regex else None

    out_rows: list[dict[str, Any]] = []
    for r in rows:
        ex_id = str(r.get("id", ""))
        inp = str(r.get("input", ""))
        expected = str(r.get("expected", ""))

        full_prompt = prompt_tmpl.replace("{input}", inp)

        predicted = ""
        raw_output = ""
        cache_path = None
        if cache_dir and ex_id:
            cache_path = cache_dir / f"{prompt_hash}-{ex_id}.txt"
            if cache_path.exists():
                raw_output = cache_path.read_text(encoding="utf-8")

        if raw_output:
            pass
        elif not ns.predict_cmd:
            raw_output = ""
        else:
            raw_output = _run_predict_cmd(ns.predict_cmd, full_prompt, ns.timeout_s)
            if cache_path:
                cache_path.write_text(raw_output, encoding="utf-8")

        if label_re:
            m = label_re.search(raw_output)
            predicted = m.group(1).strip() if m else ""
        else:
            predicted = raw_output.strip()

        ok = (predicted.strip() == expected.strip()) if (expected or predicted) else True
        out_rows.append(
            {
                "id": ex_id,
                "input": inp,
                "expected": expected,
                "predicted": predicted,
                "ok": bool(ok),
                "raw_output": raw_output if raw_output and raw_output != predicted else "",
                "metadata": r.get("metadata", {}),
                "group": r.get("group", {}),
            }
        )

    _write_jsonl(ns.out, out_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

