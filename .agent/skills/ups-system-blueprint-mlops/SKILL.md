---
name: ups-system-blueprint-mlops
description: Provides an end-to-end architecture and MLOps blueprint for prediction systems covering data, modeling, uncertainty quantification, calibration, robustness, monitoring, and retraining.
---

# UPS system blueprint and MLOps

PURPOSE
Design end-to-end prediction systems that are deployable, auditable, and decision-aligned. This skill is for "how do we build it?" questions.

GOLD STANDARD ARCHITECTURE
Forecast -> Calibrate -> Decide -> Monitor
A) Data Definition & Versioning (avoid leakage; version everything)
B) Base Predictive Model to produce a distribution/quantiles/ensemble
C) Uncertainty Decomposition (epistemic vs aleatoric)
D) Calibration Layer (temperature scaling / conformal / isotonic / quantile recalibration)
E) Decision Layer (expected utility; constraints; risk adjustment)
F) Monitoring & Governance (scoring rules; calibration; drift; retrain triggers)

[[ROUTE:MODEL_SELECTION]] (PRODUCTION DEFAULTS)
1) Tabular:
- Default: gradient boosting (XGBoost/LightGBM/CatBoost) + conformal wrapper for intervals.
- Deep tabular only when multimodal fusion or very large scale justifies it (e.g., FT-Transformer).

2) Time series / spatiotemporal:
- Default: strong baselines (ETS/ARIMA/Prophet variants) + probabilistic head or quantiles.
- Modern: PatchTST / iTransformer for multivariate; SSMs (Mamba-like) for very long horizons.
- If cross-domain zero-shot is needed: time-series foundation models (tokenized series) with probabilistic output.

3) Text:
- Default: pretrained transformer encoder/decoder with calibrated probabilities.
- If uncertainty matters: ensembles or MC dropout; calibrate post-hoc.

4) Vision:
- Default: ViT/CNN backbone with calibration; conformal sets if high-stakes.

5) Graphs:
- Default: GNN with uncertainty wrappers; evaluate across ego-nets / components for OOD.

[[ROUTE:EVALUATION]]
Use proper scoring rules as primary metrics:
- NLL / log score (probabilistic)
- Brier score (classification)
- CRPS (distributional forecast)
- Pinball loss (quantiles)
Calibration diagnostics:
- Classification: reliability diagram, ECE/MCE
- Regression: PIT histogram, interval coverage
Backtesting:
- Rolling-origin / walk-forward for temporal; blocked CV; regime stress tests
Worst-case:
- Subgroup evaluation; worst-k% slices; OOD set evaluation

[[ROUTE:CALIBRATION]]
- Classification: temperature scaling, Platt, isotonic.
- Regression: conformal prediction (split conformal baseline), conformalized quantile regression (CQR) for adaptive intervals.
- State explicitly what coverage target is (e.g., 90%, 95%) and how you will verify.

[[ROUTE:ROBUSTNESS]]
Always plan for:
- Distribution shift (train vs prod)
- Temporal drift (trend/seasonality/regime)
- Domain gap (new markets, devices, cohorts)
- Adversarial / strategic users (when applicable)
Mitigations:
- Conformal wrappers; OOD detectors; drift monitors; retraining triggers; causal methods for interventions.

[[ROUTE:CAUSAL]] (WHEN THE QUESTION IS "WHAT IF WE DO X?")
- Distinguish P(y|x) prediction from P(y|do(x)) effect.
- Propose an identification strategy: randomized experiment if possible; otherwise adjustment (backdoor/front-door), double machine learning for high-dimensional confounding, or IV/RDD where appropriate.
- Output an effect estimate with uncertainty and sensitivity checks, not just an association.

[[ROUTE:MONITORING]]
Track (at minimum):
- Probabilistic: NLL, CRPS, Brier/pinball
- Calibration: ECE, coverage vs target
- Drift/OOD: KL/Wasserstein, feature PSI, OOD rate
- Business: expected utility / cost / SLA
Retrain triggers (any one is enough):
- ECE exceeds threshold (e.g., > 0.10)
- Coverage falls below target (e.g., < 95% for a 95% interval)
- Accuracy or utility drops beyond tolerance
- Drift metrics exceed threshold; OOD rate spikes
- Policy/environment changes; label definition changes; scheduled cycle

DELIVERABLE TEMPLATE (MUST PRODUCE)
1) One-page blueprint: data -> model -> UQ -> calibration -> decision -> monitoring.
2) Model selection justification by modality and constraints.
3) Evaluation plan with metrics + backtesting + subgroup/worst-case.
4) Deployment & monitoring checklist + retraining triggers.

SAFEGUARDS
- Explicitly call out leakage risks.
- If requirements are ambiguous, propose a minimal viable baseline and a roadmap for iteration.


---

REFERENCE ASSETS (in the skill pack root folder)
- ups_output_schema.json
- core_contract.txt
