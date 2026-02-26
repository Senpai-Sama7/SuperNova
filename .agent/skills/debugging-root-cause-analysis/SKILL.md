---
name: debugging-root-cause-analysis
description: Systematic debugging and root cause analysis for software failures, errors, and anomalous behavior. Use when investigating bugs, production incidents, test failures, performance regressions, mysterious errors, or any situation where code is not behaving as expected and the cause is unknown.
---

# Debugging & Root Cause Analysis

Systematic methodology for investigating and resolving software failures.

## The Scientific Method Applied to Debugging

1. **Observe**: Gather data about the failure
2. **Hypothesize**: Form theories about possible causes
3. **Experiment**: Test hypotheses with minimal, focused changes
4. **Analyze**: Evaluate results and refine or confirm
5. **Conclude**: Document root cause and resolution

## Debugging Workflow

### Phase 1: Information Gathering

**Collect symptoms systematically:**
- Error messages (full stack traces, not summaries)
- Timeline (when did it start? what changed?)
- Frequency (always, intermittent, specific conditions?)
- Scope (affects all users, specific segments, single instance?)
- Environment (prod, staging, local, specific versions?)

**Use scripts/log-analyzer.py for automated log analysis:**
```bash
python ~/.config/agents/skills/debugging-root-cause-analysis/scripts/log-analyzer.py \
  --file /path/to/logs \
  --error-pattern "Exception" \
  --time-window "1h"
```

### Phase 2: Hypothesis Generation

Common failure categories to check:

| Category | Clues | Common Causes |
|----------|-------|---------------|
| **Logic errors** | Wrong output, edge cases | Boundary conditions, null handling, concurrency |
| **Integration failures** | 5xx errors, timeouts | API changes, network issues, auth expiration |
| **Resource exhaustion** | Slowdowns, crashes | Memory leaks, connection pools, disk space |
| **Configuration issues** | Works in dev not prod | Environment variables, feature flags, defaults |
| **Race conditions** | Intermittent, hard to reproduce | Threading, async/await, distributed locks |
| **Data corruption** | Inconsistent state | Migration errors, encoding issues, schema drift |

Reference [failure-patterns.md](references/failure-patterns.md) for extensive pattern matching.

### Phase 3: Controlled Experiments

**Binary search approach:**
1. Identify midpoint in execution flow
2. Add logging/validation at midpoint
3. Determine if issue occurs before or after
4. Repeat until root cause isolated

**Isolation techniques:**
- Comment out half the code
- Mock external dependencies
- Use feature flags to disable components
- Run with minimal dataset

### Phase 4: Root Cause Verification

**Prove the cause by:**
- Reproducing consistently
- Explaining all observed symptoms
- Predicting and verifying related effects
- Checking if fix resolves issue without side effects

## Specialized Debugging Techniques

### Memory Issues

Use scripts/memory-profiler.py:
```bash
python scripts/memory-profiler.py --pid <PID> --duration 60
```

Look for:
- Growing heap over time (leak)
- Sudden spikes (batch processing)
- Fragmentation patterns

### Performance Regression

1. Profile before and after (scripts/performance-diff.py)
2. Compare flame graphs
3. Check for N+1 queries, missing indexes
4. Verify caching is working

### Concurrency Bugs

Tools and techniques:
- Thread dump analysis (scripts/thread-analyzer.py)
- Race condition detection with stress testing
- Deadlock detection in stack traces
- Happens-before relationship analysis

### Distributed System Failures

Check in order:
1. Network connectivity (ping, traceroute)
2. Service health (health endpoints)
3. Log correlation across services (trace IDs)
4. Clock skew between nodes
5. Circuit breaker states

Reference [distributed-debugging.md](references/distributed-debugging.md).

## Log Analysis Framework

**Structured logging query patterns:**

```python
# Find error clusters by message pattern
{service="api", level="error"} 
|~ "(?i)connection refused|timeout|deadlock"
| pattern `<_> msg="<message>" <_>`
| group by (message) count()

# Trace request across services
{trace_id="abc-123"}
| sort by (timestamp)
| line_format "{{.service}}: {{.msg}}"
```

## Common Language-Specific Patterns

See [language-debugging.md](references/language-debugging.md) for:
- Python: GIL contention, asyncio deadlocks, import cycles
- JavaScript: Event loop blocking, promise chains, closure leaks
- Java: Heap dumps, thread contention, GC pauses
- Go: Goroutine leaks, channel blocking, context cancellation

## Post-Incident Process

1. **Immediate**: Mitigate impact (rollback, scale up, disable feature)
2. **Investigation**: Follow this debugging process
3. **Resolution**: Fix root cause, verify in staging
4. **Documentation**: Write incident postmortem
5. **Prevention**: Add monitoring, tests, or guards

Use [postmortem-template.md](references/postmortem-template.md).

## Resources

- [failure-patterns.md](references/failure-patterns.md) - Catalog of common failure patterns
- [distributed-debugging.md](references/distributed-debugging.md) - Multi-service debugging
- [language-debugging.md](references/language-debugging.md) - Language-specific techniques
- [postmortem-template.md](references/postmortem-template.md) - Incident documentation
