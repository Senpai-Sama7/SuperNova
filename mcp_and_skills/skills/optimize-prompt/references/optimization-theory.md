# Optimization Notes (Practical)

## Objective function

Define:
- Metric (what you maximize)
- Constraints (token budget, latency, safety)
- Allowed output contract

If the metric is ambiguous, you will "optimize vibes" and regress in production.

## Common stopping criteria

- Plateau: best metric hasn't improved for N iterations (default N=3).
- Budget: max variants evaluated or max wall-clock.
- Diminishing returns: improvement smaller than a practical threshold.

## Avoid overfitting prompts

Symptoms:
- Great validation improvements but holdout drop.

Mitigations:
- Increase example diversity.
- Reduce overly specific heuristics that only match your test set.
- Add adversarial and boundary cases.
- Keep instruction set minimal; avoid conflicting rules.
