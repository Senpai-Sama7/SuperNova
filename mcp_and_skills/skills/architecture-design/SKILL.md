---
name: architecture-design
description: System architecture design, pattern selection, and technology decision-making for scalable software systems. Use when designing new systems, evaluating architectural trade-offs, selecting between monolith/microservices/serverless, defining service boundaries, choosing databases and infrastructure, or reviewing system designs for scalability, maintainability, and reliability.
---

# Architecture Design

Guide for designing software systems with proper architectural thinking, pattern selection, and technology decisions.

## Core Principles

1. **Start with requirements**: Understand functional and non-functional requirements before choosing patterns
2. **Trade-off analysis**: Every decision has costs; document why alternatives were rejected
3. **Evolution over perfection**: Design for change, not for the ideal end state
4. **Validate with constraints**: Check against scalability, security, latency, and cost requirements

## Design Workflow

### 1. Requirements Analysis

Classify requirements into:
- **Functional**: What the system does (features, behaviors)
- **Non-functional**: How the system performs (SLAs, scalability, latency, throughput)
- **Constraints**: Hard limits (budget, compliance, existing tech stack)

Use [requirements-framework.md](references/requirements-framework.md) for structured analysis.

### 2. Architectural Style Selection

Choose based on team size, scale needs, and complexity:

| Style | Best For | Trade-offs |
|-------|----------|------------|
| Monolith | Small teams, rapid iteration, simple domains | Harder to scale independently |
| Microservices | Multiple teams, independent deploys, complex domains | Operational complexity, distributed systems challenges |
| Serverless | Variable workloads, event-driven, cost optimization | Cold starts, vendor lock-in, debugging complexity |
| Event-Driven | Async processing, loose coupling, audit trails | Eventual consistency complexity, message ordering |
| Modular Monolith | Migration path, clear boundaries, single deploy | Requires discipline to maintain modularity |

See [architectural-patterns.md](references/architectural-patterns.md) for detailed comparisons.

### 3. Component Design

Define boundaries using:
- **Domain-Driven Design**: Bounded contexts, aggregates, domain events
- **Ports and Adapters**: Clear interfaces between business logic and infrastructure
- **CQRS**: Separate read/write models when access patterns differ significantly

Reference [component-patterns.md](references/component-patterns.md) for implementation guidance.

### 4. Data Architecture

Decisions needed:
- Database type (SQL, NoSQL, Graph, Time-series)
- Data ownership per service
- Caching strategy and invalidation
- Event sourcing vs state storage

Use [data-architecture.md](references/data-architecture.md) for decision trees.

### 5. Integration Patterns

Choose communication styles:
- **Synchronous**: REST, gRPC for query operations and simple commands
- **Asynchronous**: Message queues, event buses for long-running operations
- **Hybrid**: Saga pattern for distributed transactions

See [integration-patterns.md](references/integration-patterns.md) for patterns and anti-patterns.

### 6. Validation Checklist

Before finalizing design:
- [ ] Failure modes identified (single points of failure?)
- [ ] Scalability path clear (horizontal scaling possible?)
- [ ] Security boundaries defined (authentication, authorization, data protection)
- [ ] Observability planned (metrics, logs, traces)
- [ ] Deployment strategy feasible (zero-downtime, rollback capable)
- [ ] Cost model understood (compute, storage, bandwidth)

## Anti-Patterns to Avoid

1. **Premature distribution**: Microservices for small teams without clear boundaries
2. **Database per service overkill**: When services need tight consistency
3. **Chatty services**: Excessive inter-service calls causing latency
4. **Shared databases**: Breaking service autonomy
5. **Sagas for simple cases**: Over-engineering local transactions

## Architecture Decision Records (ADRs)

Document significant decisions using this format:

```markdown
## Context
What is the issue we're facing?

## Decision
What did we decide?

## Consequences
Positive and negative outcomes

## Alternatives Considered
Why were they rejected?
```

Store ADRs in `docs/architecture/adr-XXX-title.md`.

## Resources

- [requirements-framework.md](references/requirements-framework.md) - Structured requirements analysis
- [architectural-patterns.md](references/architectural-patterns.md) - Pattern comparisons and selection
- [component-patterns.md](references/component-patterns.md) - Component design guidance
- [data-architecture.md](references/data-architecture.md) - Data layer decisions
- [integration-patterns.md](references/integration-patterns.md) - Service communication
