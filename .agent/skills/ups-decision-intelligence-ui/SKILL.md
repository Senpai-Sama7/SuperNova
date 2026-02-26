---
name: ups-decision-intelligence-ui
description: Guides design and implementation of a dashboard/PWA that presents probabilistic predictions, calibration/coverage, uncertainty signals, semantic-entropy disagreement, and decision thresholds.
---

# UPS decision intelligence UI

PURPOSE
Generate or modify a "Unified Decision Intelligence Platform" style UI that surfaces:
- probabilistic predictions and intervals
- epistemic vs aleatoric uncertainty
- calibration metrics (ECE, coverage, sharpness)
- reasoning-path / exploration summaries (e.g., PUCT tree search)
- semantic-entropy disagreement detection
- deferral / human-in-the-loop escalation logic

REQUIRED UI CAPABILITIES (MUST INCLUDE)
1) Streaming ingestion (WebSocket or polling) with a small in-memory buffer (rolling window).
2) Conformal interval display (lower/upper bands) around a point estimate.
3) Bayesian belief state display (Beta-Binomial posterior mean/variance, credible-ish interval).
4) Semantic entropy panel:
- generate N hypotheses
- cluster by semantic equivalence
- compute entropy over clusters
- translate entropy -> confidence %
5) Deferral module:
- If confidence < threshold, show "defer to human" and list what information would reduce uncertainty.
- If moderate, "conditional proceed" with heightened monitoring.
- If high, "proceed with confidence".

IMPLEMENTATION GUIDELINES
- Engines:
  - BayesianEngine: conjugate Beta update for success/failure events; variance as epistemic proxy.
  - ConformalEngine: split conformal for regression (|y - y_hat| quantile).
  - PUCTEngine: AlphaZero-style search for selecting among discrete actions when needed (optional UI visualization).
- Metrics:
  - ECE (classification) or empirical interval coverage (regression) computed from recent window.
  - Sharpness: mean interval width (lower is sharper if coverage holds).
- Accessibility:
  - Clear labeling of uncertainty types and confidence.
  - Never hide intervals behind tooltips; show them directly.

DELIVERABLES
When asked to build or modify the UI, produce:
1) A component-level plan (tabs, cards, charts, data flow).
2) Code for the relevant files (React component + small engine modules).
3) A short "how to wire data" section (expected payload shape and example).

DEFAULT PAYLOAD SHAPE
{{
  "timestamp": 1700000000000,
  "t": 123,
  "actual": 1.23,
  "prediction": 1.10,
  "regime": "stable" | "volatile",
  "success": 0 | 1
}}

QUALITY BAR
- The UI must make it obvious when to trust the model and when to defer.
- Any "confidence" number must be tied to an explicit computation (entropy, calibration, or posterior variance), not vibes.


---

REFERENCE ASSETS (in the skill pack root folder)
- ups_output_schema.json
- core_contract.txt
