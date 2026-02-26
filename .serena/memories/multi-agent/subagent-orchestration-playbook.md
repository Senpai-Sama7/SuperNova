# Multi-Agent Subagent Orchestration Playbook

> Proven pattern from 2026-02-26 — 4 agents, 4/4 SUCCESS, true concurrency confirmed.

## Pre-Flight Checklist

### 1. Create Log Directory + Manifest FIRST
```bash
mkdir -p /path/to/project/logs/agent_test
```
Write a `MANIFEST.md` with: test design, agent assignments table, dispatch timestamp.
This gives you a paper trail before anything runs.

### 2. List Available Agents Before Designing Tasks
```
use_subagent → ListAgents
```
Know what agents exist and their specialties BEFORE assigning work. Different agents have different strengths:
- `ai engineer` — good at analysis, planning, reasoning tasks
- `C0Di3` — good at code execution, command running, verification
- `kiro_default` — general purpose, file reading, system commands

### 3. Task Design Principles (CRITICAL)
- **Non-overlapping outputs**: Each agent writes to a DIFFERENT file. Never have two agents write to the same file.
- **Non-overlapping inputs**: Avoid two agents modifying the same resource. Read-only is fine for shared files.
- **READ-ONLY constraint**: Always include "Do NOT modify any source files" in every prompt unless modification is the explicit goal.
- **Verifiable artifacts**: Each agent must produce a file you can read afterward. No "fire and forget."
- **Independent tasks**: No agent should depend on another agent's output. They can't communicate with each other.

### 4. Prompt Template (Copy This)
Every agent prompt MUST include these sections:
```
ROLE: [specific expert role]
MISSION: [one-sentence objective]

STEPS:
1. Record start time: date -Iseconds
2. [specific numbered steps with exact commands]
N-1. Record end time: date -Iseconds
N. Write report to [UNIQUE file path]

OUTPUT FORMAT:
--- AGENT REPORT ---
AGENT: [letter]
ROLE: [name]
TASK: [description]
START: [timestamp]
STATUS: SUCCESS | PARTIAL | FAILED

## Findings
[structured results]

## Errors
[any errors or 'None']

END: [timestamp]
--- END REPORT ---

CONSTRAINTS:
- READ-ONLY: Do NOT modify source files. Only write to the log file.
- [task-specific constraints]
- If you encounter any error, log it in Errors with full details.
```

### 5. Key Prompt Details That Matter
- **Exact file paths**: Give full absolute paths, not relative. Agents don't share your working directory.
- **Exact commands**: Spell out the full command string. Don't say "run pytest" — say `cd /full/path && python3 -m pytest tests/ -o "addopts=" -q 2>&1`
- **Error protocol**: Tell agents what to do on failure (log it, don't crash). Otherwise they may silently skip.
- **Timestamps**: `date -Iseconds` at start and end. This is how you prove concurrency.
- **relevant_context parameter**: Use this to give agents background info they need without cluttering the main prompt.

## Execution

### Launch All Agents in ONE Call
```
use_subagent → InvokeSubagents → content.subagents = [agent1, agent2, agent3, agent4]
```
All 4 must be in the SAME `InvokeSubagents` call. If you make separate calls, they run sequentially.
Max 4 subagents per call.

### What Happens Under the Hood
- All 4 agents spawn simultaneously
- Each gets its own isolated context (they can't see each other)
- Each has access to filesystem, bash, and other tools independently
- They return when all are done (blocking call)

## Post-Execution Verification

### Automated Checks (Run This Script)
```bash
# 1. File existence
for f in agent_a.md agent_b.md agent_c.md agent_d.md; do
  [ -f "logs/agent_test/$f" ] && echo "✅ $f" || echo "❌ $f MISSING"
done

# 2. Status extraction
for f in logs/agent_test/agent_*.md; do
  grep -i "^STATUS:" "$f"
done

# 3. Timestamp extraction (concurrency proof)
for f in logs/agent_test/agent_*.md; do
  echo "$(basename $f):"
  grep -i "^START:\|^END:" "$f"
done

# 4. Error extraction
for f in logs/agent_test/agent_*.md; do
  echo "=== $(basename $f) ==="
  sed -n '/## Errors/,/^---\|^END\|^##/{p}' "$f"
done
```

### Concurrency Proof
Compare START timestamps. If agents launched in the same `InvokeSubagents` call:
- START times should be within ~30s of each other
- Execution windows should overlap
- Draw an ASCII timeline to visualize

### Cross-Validation
Look for consistency across agent outputs:
- If Agent B says "234 tests" and Agent D says "5 tables" — do those numbers make sense together?
- If Agent A plans tasks and Agent C identifies gaps — do they agree on what's missing?

## Master Report Template
After verification, write a `MASTER_REPORT.md` containing:
1. Execution summary table (agent, status, start, end, duration)
2. Concurrency timeline (ASCII art)
3. Individual capability verification
4. Error analysis table
5. Coordination assessment (file conflicts, resource contention, data consistency)
6. Diagnostic playbook (failure mode → detection → investigation → fix)

## Failure Modes & Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| Agent log file missing | Agent crashed or path wrong | Check subagent error output; verify path is absolute |
| STATUS: FAILED | Task-specific error | Read ## Errors section; address root cause |
| Timestamps sequential, not overlapping | Agents in separate calls | Put all agents in ONE InvokeSubagents call |
| Agent modified source files | Missing READ-ONLY constraint | Always include constraint in prompt |
| Agent produced unstructured output | Missing output format template | Include exact format template in prompt |
| Agent ran wrong command | Ambiguous instructions | Use exact command strings, not descriptions |
| Two agents wrote same file | Overlapping output paths | Each agent gets a unique filename |

## Performance Benchmarks (from 2026-02-26 test)
- 4 agents, all SUCCESS
- Wall clock: ~88s total
- Sequential equivalent: ~198s (54+40+59+45)
- Speedup: 2.25x
- Peak concurrency: all 4 running at 12:42:45–12:42:56
- Artifact sizes: 1.3KB – 7.5KB per agent report
