#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import pathlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_json(path: str, obj: Any) -> None:
    pathlib.Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


@dataclass(frozen=True)
class PRF:
    precision: float
    recall: float
    f1: float


def _prf(tp: int, fp: int, fn: int) -> PRF:
    p = _safe_div(tp, tp + fp)
    r = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * p * r, p + r)
    return PRF(p, r, f1)


def classification_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    y_true = [str(r.get("expected", "")).strip() for r in rows]
    y_pred = [str(r.get("predicted", "")).strip() for r in rows]

    labels = sorted(set(y_true) | set(y_pred))
    tp = Counter()
    fp = Counter()
    fn = Counter()

    correct = 0
    for yt, yp in zip(y_true, y_pred):
        if yt == yp:
            correct += 1
            tp[yt] += 1
        else:
            fp[yp] += 1
            fn[yt] += 1

    per_label: dict[str, Any] = {}
    for lab in labels:
        prf = _prf(tp[lab], fp[lab], fn[lab])
        per_label[lab] = {"precision": prf.precision, "recall": prf.recall, "f1": prf.f1, "support": y_true.count(lab)}

    macro_f1 = sum(per_label[l]["f1"] for l in labels) / len(labels) if labels else 0.0
    micro = _prf(sum(tp.values()), sum(fp.values()), sum(fn.values()))
    acc = _safe_div(correct, len(rows))

    return {
        "n": len(rows),
        "accuracy": acc,
        "macro_f1": macro_f1,
        "micro_precision": micro.precision,
        "micro_recall": micro.recall,
        "micro_f1": micro.f1,
        "per_label": per_label,
    }


def _lcs_len(a: list[str], b: list[str]) -> int:
    # Classic DP, O(n*m) but fine for short strings.
    n, m = len(a), len(b)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev = 0
        for j in range(1, m + 1):
            tmp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = tmp
    return dp[m]


def rouge_l(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores: list[float] = []
    for r in rows:
        ref = str(r.get("expected", "")).strip().split()
        hyp = str(r.get("predicted", "")).strip().split()
        if not ref and not hyp:
            scores.append(1.0)
            continue
        if not ref or not hyp:
            scores.append(0.0)
            continue
        lcs = _lcs_len(ref, hyp)
        prec = _safe_div(lcs, len(hyp))
        rec = _safe_div(lcs, len(ref))
        f = _safe_div(2 * prec * rec, prec + rec)
        scores.append(f)
    mean = sum(scores) / len(scores) if scores else 0.0
    return {"n": len(rows), "rouge_l_f": mean}


def exact_match(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = 0
    for r in rows:
        if str(r.get("expected", "")).strip() == str(r.get("predicted", "")).strip():
            ok += 1
    return {"n": len(rows), "exact_match": _safe_div(ok, len(rows))}


def bootstrap_ci(values: list[float], iters: int, seed: int) -> tuple[float, float]:
    import random

    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(iters):
        samp = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(samp) / n)
    means.sort()
    lo = means[int(0.025 * iters)]
    hi = means[int(0.975 * iters)]
    return (lo, hi)


def main() -> int:
    p = argparse.ArgumentParser(description="Compute metrics from evaluation JSONL.")
    p.add_argument("--results", required=True, help="Path to results JSONL (id/input/expected/predicted).")
    p.add_argument("--task", choices=["classification", "generation", "exact_match"], default="classification")
    p.add_argument("--out", required=True, help="Output JSON path.")
    p.add_argument("--bootstrap-iters", type=int, default=0, help="If >0, compute bootstrap CI for primary metric.")
    p.add_argument("--seed", type=int, default=0)
    ns = p.parse_args()

    rows = _read_jsonl(ns.results)
    if ns.task == "classification":
        metrics = classification_metrics(rows)
        primary = [float(r.get("ok", False)) for r in rows]  # ok boolean per row
        primary_name = "accuracy"
        primary_val = metrics["accuracy"]
    elif ns.task == "generation":
        metrics = rouge_l(rows)
        primary = []  # compute CI over per-example rouge-l
        for r in rows:
            ref = str(r.get("expected", "")).strip().split()
            hyp = str(r.get("predicted", "")).strip().split()
            if not ref and not hyp:
                primary.append(1.0)
            elif not ref or not hyp:
                primary.append(0.0)
            else:
                lcs = _lcs_len(ref, hyp)
                prec = _safe_div(lcs, len(hyp))
                rec = _safe_div(lcs, len(ref))
                primary.append(_safe_div(2 * prec * rec, prec + rec))
        primary_name = "rouge_l_f"
        primary_val = metrics["rouge_l_f"]
    else:
        metrics = exact_match(rows)
        primary = [1.0 if str(r.get("expected", "")).strip() == str(r.get("predicted", "")).strip() else 0.0 for r in rows]
        primary_name = "exact_match"
        primary_val = metrics["exact_match"]

    if ns.bootstrap_iters and ns.bootstrap_iters > 0:
        lo, hi = bootstrap_ci(primary, ns.bootstrap_iters, ns.seed)
        metrics["bootstrap_ci_95"] = {primary_name: {"lo": lo, "hi": hi, "value": primary_val}}

    _write_json(ns.out, metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

