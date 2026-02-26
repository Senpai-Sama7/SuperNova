---
name: multi-agent-orchestration
description: Coordination patterns, role definitions, and communication protocols for multi-agent AI systems. Use when decomposing complex tasks across multiple agents, designing agent workflows, managing agent communication, resolving agent conflicts, or building autonomous agent teams.
---

# Multi-Agent Orchestration

Patterns for coordinating multiple AI agents to solve complex problems.

## When to Use Multiple Agents

**Single agent is sufficient when:**
- Task fits in context window
- Clear sequential steps
- Single domain of expertise
- Simple input/output

**Multiple agents needed when:**
- Task exceeds single agent capacity
- Multiple domains require specialists
- Parallel work streams possible
- Quality improvement through review/redesign
- Autonomous operation required

## Agent Roles

### Common Role Types

| Role | Responsibility | When to Use |
|------|---------------|-------------|
| **Planner** | Decomposes tasks, assigns work | Complex multi-step tasks |
| **Specialist** | Deep expertise in one domain | Technical implementation |
| **Reviewer** | Quality assurance, validation | Before finalizing work |
| **Integrator** | Combines outputs, resolves conflicts | Multi-agent outputs |
| **Researcher** | Information gathering | Unknown domains, requirements |
| **Validator** | Tests, verifies correctness | Critical correctness needs |

### Role Definition Template

```yaml
name: backend-developer
description: Implements server-side logic, APIs, and database interactions
expertise:
  - REST API design
  - Database schema design
  - Authentication/authorization
  - Performance optimization
constraints:
  - Must write tests for all code
  - Must follow existing patterns
  - Must handle errors explicitly
inputs:
  - requirements
  - api-spec
  - database-schema
outputs:
  - implementation
  - tests
  - documentation
```

## Orchestration Patterns

### 1. Manager-Worker

One planner agent coordinates multiple worker agents:

```
┌─────────────┐
│   Planner   │── Decomposes task, assigns subtasks
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌──────┐
│Worker│ │Worker│── Execute subtasks
│  A   │ │  B   │
└──┬───┘ └──┬───┘
   │        │
   └────┬───┘
        ▼
   ┌─────────┐
   │Integrator│── Combines results
   └─────────┘
```

**Best for**: Divide-and-conquer problems with clear subtask boundaries.

### 2. Pipeline

Sequential processing where each agent transforms output:

```
Input → [Agent A] → [Agent B] → [Agent C] → Output
        Analysis    Design      Implement
```

**Best for**: Assembly-line workflows with defined handoffs.

### 3. Peer Review

Parallel execution with cross-validation:

```
         ┌──────────┐
Input ──→│ Agent A  │─┐
         └──────────┘ │
                     ├──→ [Comparator] → Consensus or Escalation
         ┌──────────┐ │
Input ──→│ Agent B  │─┘
         └──────────┘
```

**Best for**: High-stakes decisions requiring confidence.

### 4. Specialist Assembly

Each agent contributes domain expertise:

```
┌──────────┐
│ Frontend │── UI/UX implementation
└────┬─────┘
     │
┌────┴─────┐
│ Backend  │── API and business logic
└────┬─────┘
     │
┌────┴─────┐
│   DBA    │── Database optimization
└──────────┘
```

**Best for**: Full-stack features requiring multiple domains.

### 5. Debate/Adversarial

Agents argue different positions:

```
[Agent: Pro-Feature] ←────┐
                          ├──→ [Synthesizer] → Balanced decision
[Agent: Risk-Assessment] ←┘
```

**Best for**: Complex trade-off decisions.

## Communication Protocols

### Message Format

```json
{
  "message_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "from": "agent-name",
  "to": "agent-name or broadcast",
  "type": "request|response|notification|error",
  "context": {
    "task_id": "uuid",
    "parent_message": "uuid",
    "priority": "high|medium|low"
  },
  "payload": {
    "type": "code|analysis|question|decision",
    "content": "...",
    "metadata": {}
  }
}
```

### State Sharing

**Shared state store:**
```yaml
shared_state:
  requirements: {...}
  design_decisions: [...]
  code_modules:
    auth: {...}
    payments: {...}
  test_results: [...]
  blockers: [...]
```

Agents read/write to shared state instead of direct messages for loose coupling.

### Conflict Resolution

**When agents disagree:**

1. **Escalation**: Human decides
2. **Voting**: Majority rules
3. **Weighted**: Senior agent decides
4. **Synthesis**: Merge best of both
5. **Iteration**: Re-debate with new information

## Task Decomposition

### Decomposition Strategies

**By component:**
```
Feature: User authentication
├── Component: Login UI
├── Component: Session management
├── Component: Password reset
└── Component: 2FA
```

**By layer:**
```
Feature: Payment processing
├── Layer: API endpoints
├── Layer: Business logic
├── Layer: Database models
└── Layer: External integrations
```

**By workflow:**
```
Feature: Checkout
├── Step: Cart validation
├── Step: Payment authorization
├── Step: Inventory reservation
└── Step: Confirmation
```

### Dependency Management

Track what must complete before what:

```
Database Schema ──→ Repository ──→ Service ──→ API
                         ↑
                    Migration Script
```

Use scripts/dependency-tracker.py:
```bash
python scripts/dependency-tracker.py \
  --tasks tasks.yaml \
  --output order.json
```

## Quality Assurance

### Review Gates

Before finalizing:

```
[Implementation] → [Self-Review] → [Peer-Review] → [Integration-Test] → [Done]
      ↓                ↓              ↓               ↓
   Lint/Format    Check checklist   Cross-check    Automated tests
   Type check     Verify coverage   Spot issues    Manual verification
```

### Consensus Building

For critical decisions:

1. Each agent presents position
2. Clarifying questions
3. Identify areas of agreement
4. Resolve disagreements with evidence
5. Document decision and rationale

### Error Recovery

**When an agent fails:**

```
1. Log failure context
2. Retry with clarification (max 3 attempts)
3. Escalate to human or alternate agent
4. Rollback dependent work if necessary
5. Update shared state with lessons learned
```

## Autonomous Operation

### Self-Coordination Loop

```
┌─────────────────────────────────────┐
│ 1. Monitor shared state for tasks   │
│ 2. Claim task matching capabilities │
│ 3. Execute task                     │
│ 4. Update shared state              │
│ 5. Notify dependent agents          │
│ 6. Return to monitoring             │
└─────────────────────────────────────┘
```

### Health Monitoring

Track agent performance:

```yaml
agent_health:
  backend_agent:
    tasks_completed: 45
    success_rate: 0.94
    avg_response_time: 2.3m
    last_active: "2024-01-15T10:30:00Z"
    current_load: 2
    max_load: 5
```

## Implementation Tools

Use scripts/agent-coordinator.py:

```bash
# Start coordinated session
python scripts/agent-coordinator.py \
  --config orchestration.yaml \
  --task "implement user authentication" \
  --agents planner,frontend,backend,qa

# Monitor progress
python scripts/agent-coordinator.py \
  --status \
  --session session-123

# Resolve conflict
python scripts/agent-coordinator.py \
  --resolve-conflict \
  --agents agent-a,agent-b \
  --topic "database choice"
```

## Resources

- [role-definitions.md](references/role-definitions.md) - Agent role templates
- [communication-protocols.md](references/communication-protocols.md) - Message formats
- [orchestration-patterns.md](references/orchestration-patterns.md) - Advanced patterns
