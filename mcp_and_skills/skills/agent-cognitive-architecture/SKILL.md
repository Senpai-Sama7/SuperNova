---
name: agent-cognitive-architecture
description: "Design, audit, or specify autonomous agent systems that require world models, theory of mind, metacognition, goal arbitration, multi-agent orchestration, and persistent memory. Use for capability roadmaps, architecture specs, safety-aware planning, adversarial behavior modeling, or production readiness reviews of agentic systems."
---

# Agent Cognitive Architecture

## Overview
Provide a structured way to design or audit autonomous agent systems with explicit cognitive pillars and concrete, testable outputs.

## Workflow
1. Scope the environment, stakes, and constraints (safety, cost, latency, domain).
2. Map required capabilities (world model, ToM, metacognition, arbitration, swarm, memory).
3. Define state, observations, actions, and reward/utility surfaces.
4. Specify architecture modules and interfaces (who owns which signals and decisions).
5. Produce evaluation criteria, failure modes, and step-by-step implementation plan.

## Core Capabilities
### 1) World Model (Active Inference)
- Define latent state, transition dynamics, and observation model.
- Require counterfactual simulation before high-impact actions.
- Track uncertainty and prediction error; update beliefs over time.

### 2) Theory of Mind (Adversary/Intent Modeling)
- Model intent, capability, and likely escalation paths for other actors.
- Separate observed behavior from inferred intent; update as evidence changes.
- Require explicit adversary models in risky domains.

### 3) Metacognition (Self-Awareness)
- Maintain capability inventory and confidence estimates.
- Gate actions by confidence thresholds; request help or tools when low.
- Log decisions with rationales and uncertainty bounds.

### 4) Goal Arbitration (Constitutional/Constraint Balancing)
- Define a hierarchy of goals and hard constraints.
- Use utility functions or rule-based arbitration with explicit precedence.
- Provide override rules for safety and budget limits.

### 5) Swarm Intelligence (Multi-Agent Orchestration)
- Separate roles (planner, executor, verifier, toolsmith, adversary).
- Use manager-worker supervision and redundancy for critical actions.
- Enforce inter-agent contracts and conflict resolution.

### 6) Persistent Memory
- Store long-lived facts, policies, and incident history.
- Partition memory by sensitivity and access policy.
- Support retrieval evaluation to prevent stale or unsafe reuse.

## Deliverables
- Architecture spec (modules, data flow, interfaces).
- Capability gap analysis vs. requested behavior.
- Step-by-step build or remediation plan.
- Evaluation checklist and test scenarios.

## Reference
Read `references/cognitive-pillars.md` for deeper guidance.
Read `references/evaluation-matrix.md` for scoring and readiness criteria.
Read `references/domains/overview.md` to load the correct domain pack when context is specified.
