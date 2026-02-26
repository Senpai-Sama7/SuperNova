---
name: ups-evaluation-calibration
description: Evaluation and calibration for probabilistic predictions (scoring rules, ECE, backtesting, conformal coverage).
---

# UPS Evaluation and Calibration

## Overview

This Skill turns model quality into measurable, decision-relevant evidence: proper scoring, calibration diagnostics, backtesting, and worst-case evaluation.

Use this Skill when the user asks about evaluating probabilistic models, calibration, reliability, ECE, backtesting, or coverage guarantees.

## Core capabilities

- Proper scoring rule selection by output type
- Calibration diagnostics (reliability) and remediation
- Temporal backtesting (walk-forward, blocked splits) and leakage guardrails
- Subgroup and worst-case evaluation patterns
- Conformal coverage validation and maintenance plan

## What to produce (checklist)

1) Define the predictive object (event probability, quantiles, or full distribution) and the horizon.
2) Choose primary metrics:
   - Classification: log loss, Brier; plus calibration (ECE/reliability).
   - Regression: CRPS; pinball loss for quantiles; NLL if parametric.
   - Decision: expected utility under the real cost model.
3) Backtest appropriately:
   - Time series: walk-forward or rolling windows.
   - Non-stationary: stratify by regimes; check stability over time.
4) Calibrate:
   - Diagnose: reliability curve + ECE (and trends over time).
   - Fix: temperature scaling / Platt / isotonic (classification); conformalized quantiles / conformal intervals (regression).
5) Report worst-case:
   - Include subgroup and min-subgroup results when safety-critical.

## Output format

A) What is being predicted (definition and horizon)
B) Metrics to report (primary + secondary) and why
C) Backtest plan (splits, windowing, leakage controls)
D) Calibration diagnostics + remediation plan
E) Acceptance criteria (what good enough means for the decision)
F) Monitoring plan (ECE drift, coverage drift, data drift triggers)

## Example prompts

- How do we evaluate and calibrate a churn probability model?
- Design a backtest for a demand forecasting model with regime changes.
- We need 90% coverage intervals. How do we validate and maintain them?
