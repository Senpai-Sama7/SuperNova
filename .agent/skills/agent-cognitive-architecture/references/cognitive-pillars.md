# Cognitive Pillars Reference

Use this reference to expand the architecture spec or audit findings. Keep outputs concise and actionable.

## 1) World Model (Active Inference)
**Design checklist**
- State: what hidden variables matter (system health, adversary capability, environment dynamics)?
- Transition model: how does state evolve with actions and time?
- Observation model: what signals are observed, and with what noise?
- Counterfactuals: can the agent simulate "what if" before acting?
- Uncertainty: how are confidence bounds represented and propagated?

**Signals and artifacts**
- State vector or graph
- Dynamics model (learned, rules, or hybrid)
- Simulation API (rollout depth, cost limits)

**Validation**
- Backtesting against known scenarios
- Stress tests with distribution shift

## 2) Theory of Mind (ToM)
**Design checklist**
- Actors: define roles, incentives, and capabilities.
- Intent modeling: classify likely objectives and escalation paths.
- Belief modeling: track what the adversary knows and expects.
- Update rules: change intent estimates based on new evidence.

**Signals and artifacts**
- Actor profiles
- Behavior-to-intent mapping
- Escalation tree

**Validation**
- Red-team scenarios
- Predictive accuracy vs. baseline heuristics

## 3) Metacognition
**Design checklist**
- Capability inventory: what the system can and cannot do.
- Confidence gating: thresholded action approval.
- Tool discovery: when to build or request new tools.
- Error awareness: explicit fault states and recovery paths.

**Signals and artifacts**
- Confidence model
- Capability registry
- Refusal and escalation logic

**Validation**
- Measure false confidence rate
- Evaluate safe fallback success rate

## 4) Goal Arbitration
**Design checklist**
- Hard constraints vs. soft goals defined explicitly.
- Priority order and tie-breaking rules.
- Budget limits (time, cost, operational impact).
- Safety overrides that block actions even if optimal for primary goal.

**Signals and artifacts**
- Constraint graph
- Utility function or ruleset
- Audit trail for decisions

**Validation**
- Conflict simulations (goal vs. safety, speed vs. accuracy)
- Traceability of decisions

## 5) Swarm Intelligence
**Design checklist**
- Role definitions (manager, planner, executor, verifier, adversary).
- Communication protocol and message schema.
- Consensus or voting strategies for critical actions.
- Recovery when a worker fails or diverges.

**Signals and artifacts**
- Agent registry
- Task assignment policy
- Supervisory checkpoints

**Validation**
- Latency/throughput tests
- Fault injection for worker failure

## 6) Persistent Memory
**Design checklist**
- Memory classes (ephemeral, session, long-term).
- Access controls and privacy boundaries.
- Retrieval evaluation to avoid stale or unsafe recall.
- Versioning and data decay policies.

**Signals and artifacts**
- Vector store or knowledge base
- Policy metadata and TTLs
- Retrieval confidence scoring

**Validation**
- Retrieval precision/recall
- Audit for sensitive data leakage
