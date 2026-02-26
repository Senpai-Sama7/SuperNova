# Cyber Defense Domain Pack

Use this pack for SOC automation, threat response, and adversarial security operations.

## Domain assumptions
- High impact decisions can affect availability and safety.
- Adversaries adapt; theory of mind is critical.
- Auditability and rollback are mandatory.

## Capability emphasis
- World model: network topology, service dependencies, blast radius modeling.
- ToM: attacker intent classification, escalation prediction.
- Metacognition: refuse aggressive actions under low confidence.
- Arbitration: safety and availability constraints override speed.
- Swarm: separate detection, containment, and forensics agents.
- Memory: incident history and playbooks with TTLs.

## Example outputs
- "Simulate containment action impact across critical services before execution."
- "Model attacker intent as credential theft vs. ransomware; choose containment accordingly."

## Tests and validation
- Red-team scenarios with staged escalation.
- Chaos testing for containment actions.
- Post-incident audit trail checks.
