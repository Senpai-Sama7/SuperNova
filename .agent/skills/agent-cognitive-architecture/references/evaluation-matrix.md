# Evaluation Matrix

Use this matrix to score readiness and prioritize remediation. Assign 0-3 per criterion.

Scoring:
- 0 = missing
- 1 = ad hoc / incomplete
- 2 = implemented but fragile
- 3 = robust and validated

## Pillar Coverage
- World model: state, dynamics, uncertainty, simulation
- Theory of mind: actor models, intent inference, escalation modeling
- Metacognition: capability map, confidence gating, refusal/escalation
- Goal arbitration: constraints, priorities, overrides, audit trail
- Swarm: roles, supervision, consensus, recovery
- Memory: persistence, access control, retrieval evaluation

## Safety and Reliability
- Decision traceability and audit logging
- Safe fallback behaviors under uncertainty
- Rate limits and resource bounds
- Adversarial robustness and red-team tests

## Operational Readiness
- Monitoring and alerting for key signals
- Incident response playbooks
- Versioning of policies and prompts
- Reproducible evaluations and regression tests

## Suggested Outputs
- Scorecard table with totals and high-risk gaps
- Remediation roadmap ordered by safety impact
- Minimal acceptance criteria for production
