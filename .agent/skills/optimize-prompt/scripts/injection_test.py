#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from typing import Any


def _read_text(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")


def _run_predict_cmd(predict_cmd: str, prompt: str, timeout_s: int) -> str:
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
    p = argparse.ArgumentParser(description="Run adversarial inputs and validate output contract via regex.")
    p.add_argument("--prompt", required=True, help="Prompt template with {input}.")
    p.add_argument("--adversarial", required=True, help="Path to adversarial-examples.txt")
    p.add_argument("--predict-cmd", required=True, help="Shell command reading prompt from stdin.")
    p.add_argument("--expected-regex", required=True, help="Regex that MUST match output (e.g., '^(urgent|non-urgent)$').")
    p.add_argument("--timeout-s", type=int, default=30)
    p.add_argument("--out", required=True, help="Output JSON report path.")
    ns = p.parse_args()

    import re

    expected_re = re.compile(ns.expected_regex)
    tmpl = _read_text(ns.prompt)
    adv = [ln.strip() for ln in _read_text(ns.adversarial).splitlines() if ln.strip() and not ln.startswith("#")]

    results: list[dict[str, Any]] = []
    failures = 0
    for i, attack in enumerate(adv, start=1):
        full_prompt = tmpl.replace("{input}", attack)
        out = _run_predict_cmd(ns.predict_cmd, full_prompt, ns.timeout_s)
        ok = bool(expected_re.search(out.strip()))
        if not ok:
            failures += 1
        results.append({"i": i, "attack": attack, "output": out, "ok": ok})

    report = {"n": len(results), "failures": failures, "pass": failures == 0, "cases": results}
    pathlib.Path(ns.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if failures == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())

