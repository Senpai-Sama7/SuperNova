---
name: optimize-prompt
description: >
  Optimize and harden prompts with measurable improvements. Use when a user asks to "optimize",
  "improve", "refine", or "prompt engineer" instructions, or when you need systematic evaluation,
  A/B testing, and iteration logs. Use for prompt variations, benchmarking, bias audits, and
  injection/robustness testing. Not for fine-tuning, weight updates, or generic writing edits
  without an objective function.
---

# Optimize Prompt

## Core Idea

Turn "make this prompt better" into an objective-driven loop: define success, build a test set,
establish a baseline, generate variations, evaluate, validate on holdout, and ship a prompt card.

## Decision Tree

1. Do you have an objective and metric?
   - No: do Phase 1 (Problem Formulation).
   - Yes: proceed.
2. Do you have a baseline prompt?
   - No: synthesize a baseline prompt from the objective, then proceed.
3. Do you have a dataset/test set?
   - No: build a small test set (20-100 examples) that includes edge cases.
4. Is this prompt user-facing or exposed to untrusted input?
   - Yes: run injection/robustness checks and document limitations.
5. Does the task involve human attributes or protected classes?
   - Yes: run bias audit and document results.

## 6-Phase Workflow

### Phase 1: Problem Formulation

Goal: produce a crisp spec that can be scored.

Ask for:
- Task type (classification, extraction, generation, decisioning)
- Output contract (labels/JSON schema/format constraints)
- Primary metric (accuracy/F1/exact-match/ROUGE-L/etc.)
- Secondary constraints (latency, token budget, safety)

Artifacts:
- `objective.md` (task + metric + constraints)

### Phase 2: Baseline Establishment

Goal: get a baseline score and failure modes.

1. Evaluate baseline prompt (or a synthesized baseline).
2. Inspect failures and categorize them (format errors, edge cases, ambiguity, reasoning gaps).

Artifacts:
- `baseline-results.jsonl` (per-example predictions + correctness)
- `baseline-metrics.json` (aggregate)
- `failure-notes.md`

### Phase 3: Technique Selection

Select 3-5 techniques based on task type and constraints.

Load:
- `references/prompting-techniques.md`

### Phase 4: Iterative Optimization

Use deterministic variation generation + evaluation loop.

1. Generate variations: `scripts/generate_variations.py`
2. Evaluate variations: `scripts/evaluate_prompt.py` (requires a `--predict-cmd`; use `scripts/predict_openai.py` or `scripts/predict_ollama.py`)
3. Compute metrics: `scripts/calculate_metrics.py`
4. Keep an iteration log and stop on plateau.

Artifacts:
- `iteration-log.jsonl`
- `top-candidates.txt`

### Phase 5: Holdout Validation

Goal: detect overfitting to the validation set.

1. Create or load a holdout set that was not used in Phase 2/4.
2. Evaluate top 3 candidates and compute confidence intervals (bootstrap).

Artifacts:
- `holdout-report.md`
- `final-metrics.json`

### Phase 6: Documentation & Handoff

Required outputs:
- `final-prompt.txt`
- `prompt-card.md` (see template in `references/prompt_card_template.md`)
- `reproduce.md` (exact commands, model runner, dataset hashes)

## Tools In This Skill

### scripts/

- `scripts/generate_variations.py`
  - Create prompt variants from a base prompt using named techniques.
- `scripts/evaluate_prompt.py`
  - Evaluate prompts against a JSONL dataset using a user-provided `--predict-cmd`.
- `scripts/calculate_metrics.py`
  - Compute metrics for classification/exact match and basic text similarity (ROUGE-L).
- `scripts/bias_audit.py`
  - Compute per-group metrics and flag large disparities.
- `scripts/injection_test.py`
  - Run an adversarial input suite and validate output contract (regex).
- `scripts/test-all.sh`
  - Run smoke tests for the scripts.

### scripts/
 
- `scripts/predict_openai.py`: run OpenAI Completion/Chat models via REST (needs `OPENAI_API_KEY`).
- `scripts/predict_ollama.py`: call Ollama’s local HTTP API.

### references/

- `references/prompting-techniques.md`
- `references/optimization-theory.md`
- `references/benchmark-datasets.md`
- `references/adversarial-examples.txt`
- `references/prompt_card_template.md`
- `references/dataset_schema.md`

## Guardrails

Do:
- Refuse harmful optimization goals (fraud, deception, harassment).
- Treat personal data as sensitive; require consent and minimal data handling.
- Put cost controls on evaluation (cap examples/variants; cache).
- Validate output formats strictly if the prompt is used programmatically.

Don't:
- Attempt jailbreak/bypass guidance for protected systems.
- Claim improvement without measuring on a test set.
