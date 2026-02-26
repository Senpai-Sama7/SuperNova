---
name: ups-predict-dashboard
description: Design a UPS-style prediction dashboard/PWA covering uncertainty, calibration, decision metrics, conformal bands, and deferral tiers.
---

# UPS Predict Dashboard (PWA / UI)

## Overview

This Skill describes how to build a UPS-style prediction dashboard: hypotheses, uncertainty panels, calibration metrics, conformal intervals, decision metrics, and deferral logic.

Use when the user wants a UI/dashboard/PWA for probabilistic forecasting, or an architecture for forecast → calibrate → decide → monitor.

## Core capabilities

- Dashboard IA for distribution, uncertainty, calibration, decision, monitoring
- Semantic-entropy or hypothesis-disagreement panel for model reasoning uncertainty
- Conformal interval visualization (coverage bands)
- Decision widgets (expected utility, thresholds, CVaR knob)
- Deferral logic (proceed / proceed-with-conditions / defer) with explicit criteria

## Recommended UI modules

1) Inputs and scenario definition
2) Predictive distribution panel
   - Quantiles, intervals, distribution visualization
3) Uncertainty panel
   - Epistemic vs aleatoric narrative; disagreement gauge
4) Calibration panel
   - Reliability summary, ECE, recent-window trend
5) Decision panel
   - Expected utility calculator; optional CVaR; threshold slider
6) Monitoring panel
   - Drift signals, retrain triggers, coverage alerts
7) Deferral panel
   - Tiered recommendation and what evidence would reduce uncertainty

## Output format

A) Feature list (MVP vs v2)
B) Data model (predictions, outcomes, calibration stats, drift stats)
C) Architecture in words (front-end, API, model service, monitoring)
D) Interaction flows (question → distribution → decision → monitoring)
E) Metrics and alerting (ECE, coverage, drift)

## Example prompts

- Design a PWA dashboard for probabilistic sales forecasts with calibration monitoring.
- How should we implement deferral tiers based on disagreement and coverage?
- What does an MVP architecture look like for this system?
