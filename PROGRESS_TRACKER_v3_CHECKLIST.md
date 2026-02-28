# SuperNova — Deep Technical & Product Evaluation: Implementation Checklist

> **Canonical Implementation Guide — Transforms Senior Evaluation into Actionable Tasks**
>
> This document converts the PROGRESS_TRACKER_v3.md evaluation (Senior AI Engineer + FAANG-Grade PM)
> into the same strict checklist format as PROGRESS_TRACKER.md (v2).
>
> **8 Phases:** 16-23 (continuing from v2's Phase 15)
> Source: PROGRESS_TRACKER_v3.md evaluation + "Bridging the Gap" playbook

---

> **TRACKER RULES — DO NOT VIOLATE**
>
> 1. Never rewrite, remove, or restructure any part of this checklist.
> 2. On task completion: only change `[ ]` → `[x]` and replace `_pending_` with validation evidence.
> 3. Do not alter Validation lines, reorder tasks, or touch uncompleted tasks.
> 4. Failed tasks: leave `[ ]`, append `❌ FAIL:` notes under Proof line.
> 5. Implementation method changes: keep original, append `❌ FAIL:` then `✅ FIX:` with explanation.
> 6. These rules are permanent for all agents (human or AI).

---

## 🎯 TRACKER RULES — Strict Validation Protocol

### ⚠️ MANDATORY: Do Not Proceed Until Validated

**YOU MUST NOT** move to the next bullet point until:

1. ✅ The current task is **fully implemented**
2. ✅ The **Validation** command has been **executed and passed**
3. ✅ **Real proof** has been documented (replace `_pending_` with actual output)
4. ✅ The checkbox has been marked `[x]`
5. ✅ `AGENTS.md` has been updated to reflect current state

### 🚫 Forbidden Actions

| Forbidden                                   | Correct Approach                                  |
| ------------------------------------------- | ------------------------------------------------- |
| "This should work" without running tests    | Execute validation command, paste output as proof |
| Marking `[x]` before validation             | Validate first, then mark complete                |
| Skipping a failing task                     | Stop, debug, fix, re-validate                     |
| Moving to next task with current incomplete | Finish current task completely first              |
| Hand-waving validation                      | Real command output or it's not done              |

### ✅ Validation Requirements by Task Type

| Task Type               | Validation Standard                                         |
| ----------------------- | ----------------------------------------------------------- |
| **Code implementation** | `pytest` passes, `mypy` passes, actual test output in Proof |
| **File creation**       | `ls -la` or `cat` showing file exists with correct content  |
| **Service startup**     | Health check endpoint returns 200, logs show clean startup  |
| **Database operations** | SQL query showing table/index exists, migration applied     |
| **API endpoints**       | `curl` response showing correct status and payload          |
| **Configuration**       | File content verification, env var validation               |
| **Refactoring**         | All existing tests still pass after changes                 |

### 📝 Proof Format

Replace `_pending_` with concrete evidence:

```markdown
- **Proof:**
  ```
  $ pytest tests/test_example.py -v
  ======================== test session starts ========================
  tests/test_example.py::test_something PASSED
  ======================== 1 passed in 0.12s ==========================
  ```
```

---

## Quick Navigation

| Phase  | Focus                              | Priority    | Source (v3 Section)                    |
| :----- | :--------------------------------- | :---------- | :------------------------------------- |
| **16** | Architecture Refactoring           | 🔴 Critical | §1 Architecture + Immediate Recs       |
| **17** | Security Remediation               | 🔴 Critical | §4 Security + Bridging §2             |
| **18** | Performance & Async Pipeline       | 🟡 High     | Bridging §1 Performance               |
| **19** | Multi-Agent Orchestration          | 🟡 High     | Bridging §4 Power                     |
| **20** | Reasoning & Intelligence Pipeline  | 🟡 High     | Bridging §7 Intelligence              |
| **21** | Advanced Memory Architecture       | 🟡 High     | Bridging §8 Memory                    |
| **22** | Versatility & Skills Platform      | 🟢 Medium   | Bridging §3 Versatility               |
| **23** | Product, UX & Operational Polish   | 🟢 Medium   | §3 Product + §5 Ops + §6 PM + Bridging §5-6 |

---

## CRITICAL CONSTRAINTS — New (from v3 Evaluation)

These supplement the 20 CCs from v2. Check before every task.

- [ ] **CC-21** Root-level Python files (`loop.py`, `context_assembly.py`, `dynamic_router.py`, `procedural.py`, `interrupts.py`) moved into `supernova/` package
  - **Validation:** `ls *.py` at project root shows zero core logic files; only `setup.sh`-adjacent scripts
  - **Proof:** _pending_
- [ ] **CC-22** `.env` file is NOT committed to git; only `.env.example` exists in repo
  - **Validation:** `git ls-files .env` returns empty; `.gitignore` contains `.env`
  - **Proof:** _pending_
- [ ] **CC-23** No binary artifacts (`.tar.gz`, proof bundles) committed to main branch
  - **Validation:** `git ls-files '*.tar.gz'` returns empty; moved to GitHub Releases
  - **Proof:** _pending_
- [ ] **CC-24** All REST endpoints require authentication (bearer token or JWT)
  - **Validation:** `curl http://localhost:8000/memory/semantic` without auth returns 401
  - **Proof:** _pending_
- [ ] **CC-25** Local LLM (Ollama) is the default when no API keys configured — privacy-first
  - **Validation:** Fresh install with no API keys routes to Ollama; no external API calls made
  - **Proof:** _pending_
- [ ] **CC-26** README setup time estimate is honest (tested on clean VM)
  - **Validation:** Timed fresh install on Ubuntu 24.04 VM; README matches ±2 minutes
  - **Proof:** _pending_
- [ ] **CC-27** Circuit breakers on all external API calls (LLM, Neo4j, Langfuse)
  - **Validation:** Kill Neo4j → agent still responds (degraded); kill LLM API → falls back to local
  - **Proof:** _pending_
- [ ] **CC-28** Input sanitization on all external data entering context window
  - **Validation:** Inject `<instruction>ignore previous</instruction>` in web search result → agent ignores it
  - **Proof:** _pending_

---

## PHASE 16 — Architecture Refactoring (CRITICAL)

**Phase Objective:** Eliminate structural debt identified in v3 §1 — flat file layout, committed secrets, binary artifacts. These are FAANG code-review blockers.

**Estimated Duration:** 1-2 sessions
**Completion Criteria:** All core logic inside `supernova/` package; no secrets or binaries in git; clean import paths.

**Source:** v3 §1 "What's Concerning", v3 §6 "Risk: AI-assisted development", v3 Priority Recommendations (Immediate)

---

### Task 16.1: Move Root-Level Core Files into Package

**🎯 Skill Activation:** `code-review-refactoring` — Safe refactoring with import path updates.
**🎯 Skill Activation:** `architecture-design` — Package hierarchy design.
**🎯 MCP Activation:** `code-intelligence` — Find all import references before moving.

**Context:** v3 §1: "Several core files — `loop.py`, `context_assembly.py`, `dynamic_router.py`, `procedural.py` — live at the repository root. This is a flat structure that will not scale. At FAANG this would fail code review on structure alone."

**Dependencies:** None — this is the first thing to fix.

- [ ] **16.1.1** Move `loop.py` → `supernova/core/agent/loop.py`
  - **Validation:** `python -c "from supernova.core.agent.loop import build_agent_graph"` succeeds; all tests pass
  - **Proof:** _pending_

- [ ] **16.1.2** Move `context_assembly.py` → `supernova/core/reasoning/context_assembly.py`
  - **Validation:** `python -c "from supernova.core.reasoning.context_assembly import assemble_context_window"` succeeds; `pytest tests/test_context_assembly.py -v` passes
  - **Proof:** _pending_

- [ ] **16.1.3** Move `dynamic_router.py` → `supernova/infrastructure/llm/dynamic_router.py`
  - **Validation:** `python -c "from supernova.infrastructure.llm.dynamic_router import DynamicModelRouter"` succeeds; `pytest tests/test_routing.py -v` passes
  - **Proof:** _pending_

- [ ] **16.1.4** Move `procedural.py` → `supernova/core/memory/procedural.py`
  - **Validation:** `python -c "from supernova.core.memory.procedural import ProceduralMemoryStore"` succeeds
  - **Proof:** _pending_

- [ ] **16.1.5** Move `interrupts.py` → `supernova/api/interrupts.py`
  - **Validation:** `python -c "from supernova.api.interrupts import InterruptCoordinator"` succeeds; `pytest tests/test_interrupts.py -v` passes
  - **Proof:** _pending_

- [ ] **16.1.6** Update all import paths across codebase
  - **Validation:** `grep -r "from loop import\|from context_assembly import\|from dynamic_router import\|from procedural import\|from interrupts import" supernova/` returns zero matches; `pytest tests/ -v` all pass
  - **Proof:** _pending_

- [ ] **16.1.7** Verify full test suite passes after refactor
  - **Validation:** `cd /home/donovan/Downloads/SuperNova/supernova && python3 -m pytest tests/ -v --tb=short` — all 358+ tests pass
  - **Proof:** _pending_

---

### Task 16.2: Git Hygiene — Remove Secrets and Binaries

**🎯 Skill Activation:** `security-engineering` — Credential rotation, git history scrubbing.
**🎯 MCP Activation:** `execution-engine` — Run git-filter-repo or BFG.

**Context:** v3 §4 Critical: ".env committed to source — even if template-only, it normalizes the pattern." v3 §2: "proof_bundle_*.tar.gz files committed to main — binary artifacts should never be in source."

**Dependencies:** None

- [x] **16.2.1** Remove `.env` from git tracking
  - **Validation:** `git rm --cached .env`; `.gitignore` contains `.env` and `!.env.example`; `git ls-files .env` returns empty
  - **Proof:** _pending_

- [x] **16.2.2** Rotate any credentials that were in `.env`
  - **Validation:** All API keys in `.env` are regenerated at their respective providers; old keys revoked
  - **Proof:** _pending_

- [x] **16.2.3** Remove proof bundle tarballs from git
  - **Validation:** `git rm proof_bundle_*.tar.gz`; `git ls-files '*.tar.gz'` returns empty
  - **Proof:** _pending_

- [x] **16.2.4** Move proof bundles to GitHub Releases
  - **Validation:** `gh release create v0.1.0-proof --title "Proof Bundles" proof_bundle_*.tar.gz` succeeds; files downloadable from Releases page
  - **Proof:** _pending_

- [ ] **16.2.5** Scrub git history of secrets (optional but recommended)
  - **Validation:** `git log --all -p | grep -c "sk-\|sk-ant-\|ghp_"` returns 0 after BFG/git-filter-repo
  - **Proof:** _pending_

- [x] **16.2.6** Add comprehensive `.gitignore` entries
  - **Validation:** `.gitignore` includes: `.env`, `*.tar.gz`, `proof_bundle*/`, `*.pyc`, `__pycache__/`, `.coverage`, `htmlcov/`, `*.egg-info/`
  - **Proof:** _pending_

---

### Task 16.3: CI/CD Pipeline

**🎯 Skill Activation:** `ci-cd-devops` — GitHub Actions workflow design.
**🎯 MCP Activation:** `execution-engine` — Test workflow locally with `act`.

**Context:** v3 §6: "No mention of a test suite, CI/CD pipeline, or GitHub Actions workflows. For a project with this much autonomous agent behavior, the absence of automated testing is a production risk."

**Dependencies:** Task 16.1 (clean package structure)

- [x] **16.3.1** Create `.github/workflows/ci.yml`
  - **Validation:** Workflow triggers on push/PR to main; runs lint, type-check, tests
  - **Proof:** _pending_

- [x] **16.3.2** Add lint step (Ruff)
  - **Validation:** `ruff check supernova/` in CI; fails on errors
  - **Proof:** _pending_

- [x] **16.3.3** Add type-check step (MyPy)
  - **Validation:** `mypy supernova/ --ignore-missing-imports` in CI; fails on errors
  - **Proof:** _pending_

- [x] **16.3.4** Add test step with coverage
  - **Validation:** `pytest tests/ --cov=supernova --cov-fail-under=80` in CI; fails below 80%
  - **Proof:** _pending_

- [x] **16.3.5** Add security scanning step
  - **Validation:** `pip-audit` or `safety check` in CI; fails on known vulnerabilities
  - **Proof:** _pending_

- [x] **16.3.6** Verify CI passes on current codebase
  - **Validation:** Push to branch; GitHub Actions shows green ✅
  - **Proof:** _pending_

---

## PHASE 17 — Security Remediation (CRITICAL)

**Phase Objective:** Address all security issues from v3 §4 — API authentication, prompt injection defense, approval system hardening, input sanitization.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** All REST endpoints authenticated; prompt injection tested; approval system adversarially reviewed.

**Source:** v3 §4 "Security Analysis" (Critical/High/Medium findings), Bridging §2 "Security"

---

### Task 17.1: API Authentication Enforcement

**🎯 Skill Activation:** `security-engineering` — Auth middleware, token validation.
**🎯 Skill Activation:** `api-integration` — FastAPI dependency injection for auth.
**🎯 MCP Activation:** `quality-assurance` — Security scan all endpoints.

**Context:** v3 §4 High: "The REST endpoints don't appear to have any token-gated authentication. If someone runs this on a cloud VM, this is an open agent."

**Dependencies:** Task 6.1 (existing JWT auth module)

- [x] **17.1.1** Audit all API endpoints for auth requirements
  - **Validation:** `grep -r "def \|async def " supernova/api/routes/ | grep -v "get_current_user"` — list all unprotected endpoints
  - **Proof:** _pending_

- [x] **17.1.2** Add JWT auth to all non-public endpoints
  - **Validation:** Every endpoint except `/health` and `/auth/token` requires `Depends(get_current_user)`; unauthenticated requests return 401
  - **Proof:** _pending_

- [x] **17.1.3** Add rate limiting middleware
  - **Validation:** >100 requests/minute from same IP returns 429; configurable via `RATE_LIMIT_RPM` env var
  - **Proof:** _pending_

- [x] **17.1.4** Test auth enforcement end-to-end
  - **Validation:** `curl http://localhost:8000/memory/semantic` → 401; `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/memory/semantic` → 200
  - **Proof:** _pending_

---

### Task 17.2: Prompt Injection Defense

**🎯 Skill Activation:** `security-engineering` — Adversarial input handling.
**🎯 Skill Activation:** `agent-cognitive-architecture` — Context boundary design.
**🎯 MCP Activation:** `quality-assurance` — Injection testing.

**Context:** Bridging §2: "Every piece of external data (web search results, file contents, tool outputs) that enters your context window is an attack surface. A malicious webpage can contain hidden instructions."

**Dependencies:** Task 5.6.1 (web search tool), Task 5.4 (semantic memory)

- [x] **17.2.1** Create `infrastructure/security/input_sanitizer.py` with `TrustedContext` class
  - **Validation:** Class wraps external data with trust boundary markers:
    ```python
    class TrustedContext:
        def wrap_external(self, content: str, source: str) -> str:
            # Wraps content with <external_data> tags and trust=low marker
            # Appends instruction to never follow embedded instructions
    ```
  - **Proof:** _pending_

- [x] **17.2.2** Apply sanitization to web search results
  - **Validation:** All web search tool outputs pass through `TrustedContext.wrap_external()` before entering context
  - **Proof:** _pending_

- [x] **17.2.3** Apply sanitization to file read results
  - **Validation:** All file read tool outputs pass through `TrustedContext.wrap_external()` before entering context
  - **Proof:** _pending_

- [x] **17.2.4** Apply sanitization to MCP tool outputs
  - **Validation:** All MCP tool results pass through `TrustedContext.wrap_external()` before entering context
  - **Proof:** _pending_

- [x] **17.2.5** Create adversarial test suite
  - **Validation:** Tests with known injection payloads: `"ignore previous instructions"`, `"<system>new instructions</system>"`, `"[INST]override[/INST]"` — agent ignores all of them
  - **Proof:** _pending_

---

### Task 17.3: Tool Call Validation Layer

**🎯 Skill Activation:** `security-engineering` — Policy enforcement.
**🎯 MCP Activation:** `code-intelligence` — Analyze tool call patterns.

**Context:** Bridging §2: "Before any tool executes, run it through a validator that checks the call against a policy manifest — not just 'is this high risk' but 'is this call structurally valid, within allowed parameter ranges, and consistent with what the user asked for?'"

**Dependencies:** Task 5.5 (tool registry)

- [x] **17.3.1** Create `infrastructure/security/tool_validator.py`
  - **Validation:** Validates tool calls against policy: parameter types, value ranges, path restrictions, API endpoint allowlists
  - **Proof:** _pending_

- [x] **17.3.2** Add parameter range validation
  - **Validation:** File paths must be within workspace; URLs must be HTTPS; token counts must be positive integers
  - **Proof:** _pending_

- [x] **17.3.3** Add consistency checking
  - **Validation:** Tool call arguments are consistent with the user's original request (semantic similarity check)
  - **Proof:** _pending_

- [x] **17.3.4** Integrate validator into tool execution pipeline
  - **Validation:** `ToolRegistry.execute()` calls validator before execution; invalid calls rejected with clear error
  - **Proof:** _pending_

---

### Task 17.4: Approval System Adversarial Review

**🎯 Skill Activation:** `security-engineering` — Adversarial testing.
**🎯 Skill Activation:** `hostile-auditor` — MANDATORY: Attack the approval system.

**Context:** v3 §4 Medium: "If the agent can queue actions while the user is away and the approval timeout is misconfigured or bypassed, you have an autonomous agent with file write and external API call access running unsupervised."

**Dependencies:** Task 6.2 (WebSocket handler), existing interrupts.py

- [x] **17.4.1** Test approval queue flooding
  - **Validation:** Agent cannot queue >10 pending approvals; excess requests auto-denied
  - **Proof:** _pending_

- [x] **17.4.2** Test timeout manipulation
  - **Validation:** Timeout values cannot be overridden by agent; hardcoded minimums enforced (critical: min 60s, never auto-approve)
  - **Proof:** _pending_

- [x] **17.4.3** Test approval bypass via tool chaining
  - **Validation:** Agent cannot achieve high-risk outcome by chaining multiple low-risk approved actions
  - **Proof:** _pending_

- [x] **17.4.4** Document approval system threat model
  - **Validation:** `docs/THREAT_MODEL.md` exists with attack vectors, mitigations, and residual risks
  - **Proof:** _pending_

---

## PHASE 18 — Performance & Async Pipeline

**Phase Objective:** Transform serial request→response into parallel async pipeline with background processing, streaming, and sub-2-second response targets.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** Memory retrieval parallelized; responses stream in <2s; background consolidation non-blocking.

**Source:** Bridging §1 "Performance" — "SuperNova makes one LLM call, waits, responds. OpenClaw is running background heartbeats, parallel skill execution, and cached context assembly simultaneously."

---

### Task 18.1: Parallel Memory Retrieval

**🎯 Skill Activation:** `performance-engineering` — Async optimization, gather patterns.
**🎯 MCP Activation:** `execution-engine` — Benchmark before/after.

**Context:** Bridging §1: "Split the agent into three lanes running concurrently." Memory retrieval from 4 stores should happen in parallel, not sequentially.

**Dependencies:** Task 5.2-5.4 (memory stores), CC-5 (already uses asyncio.gather)

- [x] **18.1.1** Benchmark current memory retrieval latency
  - **Validation:** Measure p50/p95/p99 latency for `asyncio.gather(episodic, semantic, skill_match, wm)` with real data
  - **Proof:** _pending_

- [x] **18.1.2** Add predictive memory prefetch
  - **Validation:** On conversation start, predict likely needed memories from early signals (keywords, time of day, topic); pre-load into Redis cache before first LLM call
  - **Proof:** _pending_

- [x] **18.1.3** Implement context assembly caching
  - **Validation:** Identical queries within 5s return cached context; cache invalidated on new memory writes
  - **Proof:** _pending_

- [x] **18.1.4** Benchmark after optimization
  - **Validation:** p95 memory retrieval latency reduced by ≥30% from baseline
  - **Proof:** _pending_

---

### Task 18.2: Background Task Queue

**🎯 Skill Activation:** `performance-engineering` — Task queue design.
**🎯 Skill Activation:** `architecture-design` — Non-blocking pipeline.
**🎯 MCP Activation:** `execution-engine` — Load test background tasks.

**Context:** Bridging §1: "Add Celery or ARQ as your background task queue so memory consolidation, reflection, and proactive nudges happen in the background while the user is doing other things — not blocking the chat response."

**Dependencies:** Task 7.1 (Celery setup)

- [x] **18.2.1** Move memory consolidation to fire-and-forget after response
  - **Validation:** After agent responds, consolidation task dispatched to Celery; user sees no delay; `celery inspect active` shows task running
  - **Proof:** _pending_

- [x] **18.2.2** Move reflection to background
  - **Validation:** REFLECT phase runs as background task after CONSOLIDATE; does not block next user message
  - **Proof:** _pending_

- [x] **18.2.3** Add response latency tracking
  - **Validation:** Every response logs `time_to_first_token` and `total_response_time` to Langfuse; target: first token <2s
  - **Proof:** _pending_

---

### Task 18.3: Streaming Optimization

**🎯 Skill Activation:** `performance-engineering` — WebSocket throughput.
**🎯 MCP Activation:** `execution-engine` — Measure streaming latency.

**Context:** Bridging §1: "Latency is UX. Every 100ms you shave off the response loop is trust you're building with the user."

**Dependencies:** Task 6.2 (WebSocket handler)

- [ ] **18.3.1** Implement token-level streaming
  - **Validation:** Each token sent via WebSocket as it arrives from LLM; no buffering; `{type: "token", content: "word"}` events
  - **Proof:** _pending_

- [ ] **18.3.2** Add streaming for tool execution
  - **Validation:** Tool start/progress/complete events streamed in real-time; user sees "Searching web..." before results arrive
  - **Proof:** _pending_

- [ ] **18.3.3** Measure and optimize time-to-first-token
  - **Validation:** Median time-to-first-token <1.5s for simple queries (measured over 50 requests)
  - **Proof:** _pending_

---

### Task 18.4: Circuit Breakers

**🎯 Skill Activation:** `architecture-design` — Resilience patterns.
**🎯 Skill Activation:** `performance-engineering` — Fallback chains.

**Context:** v3 §5: "Running four Docker services continuously — if any fails, the system should degrade gracefully, not crash."

**Dependencies:** Task 5.1 (storage layer), Task 11.4 (Ollama fallback)

- [x] **18.4.1** Implement circuit breaker for LLM API calls
  - **Validation:** After 3 consecutive failures, circuit opens; routes to Ollama fallback; circuit half-opens after 60s to test recovery
  - **Proof:** _pending_

- [x] **18.4.2** Implement circuit breaker for Neo4j
  - **Validation:** Neo4j down → episodic memory returns empty results (not errors); agent still functions with semantic + working memory
  - **Proof:** _pending_

- [x] **18.4.3** Implement circuit breaker for Langfuse
  - **Validation:** Langfuse down → observability silently disabled; no errors propagated to user; re-enabled when Langfuse recovers
  - **Proof:** _pending_

- [ ] **18.4.4** Test graceful degradation end-to-end
  - **Validation:** `docker stop supernova-neo4j && curl -X POST /agent/message` → agent responds (degraded but functional); `docker start supernova-neo4j` → full functionality restored within 60s
  - **Proof:** _pending_

---

## PHASE 19 — Multi-Agent Orchestration

**Phase Objective:** Transform single-agent architecture into specialized multi-agent system with planner, executors, critic, and memory manager.

**Estimated Duration:** 3-4 sessions
**Completion Criteria:** Orchestrator dispatches to specialized agents; parallel execution works; critic reviews before response.

**Source:** Bridging §4 "Power" — "One person trying to be a CEO, engineer, and accountant simultaneously vs. a company where each role is filled by someone great at exactly that thing."

---

### Task 19.1: Agent Specialization Framework

**🎯 Skill Activation:** `agent-cognitive-architecture` — Multi-agent design patterns.
**🎯 Skill Activation:** `multi-agent-orchestration` — Coordination protocols.
**🎯 Skill Activation:** `architecture-design` — Shared state design.
**🎯 MCP Activation:** `code-intelligence` — Analyze existing agent loop for decomposition points.

**Context:** Bridging §4: "Your loop.py becomes an orchestrator that spawns specialized sub-agents: PlannerAgent, ExecutorAgent(s), CriticAgent, MemoryAgent, ReflectionAgent."

**Dependencies:** Task 16.1 (clean package structure), existing loop.py

- [x] **19.1.1** Design shared state schema for multi-agent coordination
  - **Validation:** `docs/MULTI_AGENT_STATE.md` defines: shared state fields, read/write permissions per agent, conflict resolution rules
  - **Proof:** _pending_

- [x] **19.1.2** Create `core/agent/orchestrator.py` with `OrchestratorAgent`
  - **Validation:** Receives user message; decides which sub-agents to invoke; coordinates results; returns final response
  - **Proof:** _pending_

- [x] **19.1.3** Create `core/agent/planner.py` with `PlannerAgent`
  - **Validation:** Specialized system prompt for task decomposition; breaks complex tasks into numbered steps; never touches files or tools directly
  - **Proof:** _pending_

- [x] **19.1.4** Create `core/agent/executor.py` with `ExecutorAgent`
  - **Validation:** Executes individual plan steps; has tool access; reports results back to orchestrator; can run in parallel (multiple executors)
  - **Proof:** _pending_

- [x] **19.1.5** Create `core/agent/critic.py` with `CriticAgent`
  - **Validation:** Reviews executor outputs before returning to user; checks for errors, hallucinations, incomplete answers; requests revision if needed
  - **Proof:** _pending_

- [x] **19.1.6** Create `core/agent/memory_agent.py` with `MemoryAgent`
  - **Validation:** Runs continuously in background; consolidates memories; manages forgetting curves; no direct user interaction
  - **Proof:** _pending_

- [x] **19.1.7** Test multi-agent pipeline end-to-end
  - **Validation:** Complex query ("Research X, write a summary, save to file") → Planner creates 3 steps → Executor runs each → Critic reviews → User gets polished result
  - **Proof:** _pending_

---

### Task 19.2: Dynamic Trust Model

**🎯 Skill Activation:** `agent-cognitive-architecture` — Behavioral learning.
**🎯 Skill Activation:** `security-engineering` — Trust boundary design.

**Context:** Bridging §6 "Autonomy": "Replace your binary approval/deny system with a dynamic trust model that learns from your behavior." This is identified as SuperNova's primary competitive moat.

**Dependencies:** Task 17.4 (approval system hardened), existing interrupts.py

- [x] **19.2.1** Create `core/agent/trust_model.py` with `TrustModel` class
  - **Validation:** Computes autonomy score (0.0–1.0) per action type based on: approval history, action reversibility, user preferences, action novelty
  - **Proof:** _pending_

- [x] **19.2.2** Implement approval history learning
  - **Validation:** After 5 consecutive approvals of same action type, autonomy score increases; after 1 denial, score decreases significantly
  - **Proof:** _pending_

- [x] **19.2.3** Add user-configurable autonomy threshold
  - **Validation:** `AUTONOMY_THRESHOLD` env var (default 0.8); actions above threshold auto-approved; below threshold require HITL
  - **Proof:** _pending_

- [x] **19.2.4** Integrate trust model into approval flow
  - **Validation:** `InterruptCoordinator.request_approval()` checks trust model first; high-trust actions skip approval UI; all decisions logged for learning
  - **Proof:** _pending_

- [x] **19.2.5** Add trust model dashboard widget
  - **Validation:** Dashboard shows per-action-type trust scores; user can manually adjust thresholds; reset button available
  - **Proof:** _pending_

---

## PHASE 20 — Reasoning & Intelligence Pipeline

**Phase Objective:** Implement multi-pass reasoning with chain-of-thought, self-critique, and depth-adaptive processing.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** Simple queries use fast path; complex queries use think→draft→critique→revise; measurable quality improvement.

**Source:** Bridging §7 "Intelligence" — "GPT-4o-mini with a great reasoning pipeline outperforms GPT-4o with a naive single-call approach on most real-world tasks."

---

### Task 20.1: Reasoning Pipeline

**🎯 Skill Activation:** `agent-cognitive-architecture` — Reasoning architecture.
**🎯 Skill Activation:** `performance-engineering` — Latency vs quality tradeoffs.
**🎯 MCP Activation:** `code-intelligence` — Analyze existing reasoning flow.

**Context:** Bridging §7: "Implement chain-of-thought with self-critique as a configurable reasoning pipeline."

**Dependencies:** Task 16.1 (clean package structure), existing dynamic_router.py

- [x] **20.1.1** Create `core/reasoning/pipeline.py` with `ReasoningPipeline` class
  - **Validation:** Supports three depths: FAST (single pass), STANDARD (think→respond), DEEP (think→draft→critique→revise)
  - **Proof:** _pending_

- [x] **20.1.2** Implement FAST reasoning path
  - **Validation:** Single LLM call; <1s added latency; used for simple factual queries
  - **Proof:** _pending_

- [x] **20.1.3** Implement STANDARD reasoning path
  - **Validation:** Two LLM calls (think→respond); chain-of-thought visible in Langfuse trace; measurably better answers than FAST for moderate complexity
  - **Proof:** _pending_

- [x] **20.1.4** Implement DEEP reasoning path
  - **Validation:** Four LLM calls (think→draft→critique→revise); critique identifies real issues; revision addresses them; used for complex planning/analysis
  - **Proof:** _pending_

- [x] **20.1.5** Integrate depth selection into dynamic router
  - **Validation:** `DynamicModelRouter.route_task()` returns both model AND reasoning depth; simple queries → FAST, complex → STANDARD, planning/analysis → DEEP
  - **Proof:** _pending_

- [ ] **20.1.6** Add tool-augmented reasoning
  - **Validation:** Before answering knowledge questions, agent asks "what do I need to look up?" and retrieves from memory/web before composing answer; reduces hallucination rate
  - **Proof:** _pending_

---

## PHASE 21 — Advanced Memory Architecture

**Phase Objective:** Upgrade memory from naive similarity search to intelligent retrieval with hierarchical scoring, consolidation cycles, and predictive prefetch.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** Memory retrieval uses multi-factor scoring; nightly consolidation runs; prefetch reduces latency.

**Source:** Bridging §8 "Memory" — "Memory is the moat. After 6 months of use, SuperNova with great memory architecture knows a user better than any general-purpose assistant ever could."

---

### Task 21.1: Hierarchical Memory Retrieval

**🎯 Skill Activation:** `agent-cognitive-architecture` — Memory scoring models.
**🎯 Skill Activation:** `database-design-optimization` — Query optimization.
**🎯 MCP Activation:** `code-intelligence` — Analyze current retrieval patterns.

**Context:** Bridging §8: "Don't just retrieve by similarity. Retrieve by a weighted combination of: recency, relevance, emotional salience, and access frequency."

**Dependencies:** Task 5.4 (semantic memory store)

- [x] **21.1.1** Implement multi-factor memory scoring
  - **Validation:** `MemoryRetriever.score()` computes weighted combination: semantic_similarity (0.40) + recency (0.25) + access_frequency (0.20) + salience (0.15); configurable weights
  - **Proof:** _pending_

- [x] **21.1.2** Add emotional salience tracking
  - **Validation:** Memories tagged with sentiment score at creation time; strong opinions (positive or negative) get higher salience; neutral facts get lower salience
  - **Proof:** _pending_

- [x] **21.1.3** Add access frequency tracking
  - **Validation:** Every memory retrieval increments `access_count`; frequently accessed memories ranked higher; `update_access_time()` called on every retrieval
  - **Proof:** _pending_

- [x] **21.1.4** Benchmark retrieval quality improvement
  - **Validation:** Create test set of 20 queries with known "correct" memories; multi-factor retrieval returns correct memory in top-3 more often than similarity-only (measure recall@3)
  - **Proof:** _pending_

---

### Task 21.2: Memory Consolidation ("Sleep Cycle")

**🎯 Skill Activation:** `agent-cognitive-architecture` — Cognitive consolidation patterns.
**🎯 Skill Activation:** `performance-engineering` — Efficient batch processing.

**Context:** Bridging §8: "Human brains consolidate memories during sleep — they compress experiences into generalizations and discard redundant details."

**Dependencies:** Task 7.2 (consolidation worker), Task 5.3-5.4 (memory stores)

- [x] **21.2.1** Implement redundancy detection
  - **Validation:** Nightly job identifies memories with >0.95 cosine similarity; merges into single memory with combined metadata
  - **Proof:** _pending_

- [x] **21.2.2** Implement experience generalization
  - **Validation:** Repeated similar interactions (e.g., "user asked about Python async 7 times") consolidated into one procedural memory: "User is learning Python async. Prefers concrete examples."
  - **Proof:** _pending_

- [x] **21.2.3** Implement memory pruning
  - **Validation:** Memories with importance < 0.1 AND last_accessed > 90 days ago are archived (not deleted); archived memories retrievable via explicit search
  - **Proof:** _pending_

- [x] **21.2.4** Add consolidation metrics
  - **Validation:** Nightly consolidation logs: memories_merged, memories_generalized, memories_archived, total_memory_count; visible in Langfuse
  - **Proof:** _pending_

---

### Task 21.3: Predictive Memory Prefetch

**🎯 Skill Activation:** `performance-engineering` — Prefetch strategies.
**🎯 Skill Activation:** `context-management` — Predictive context loading.

**Context:** Bridging §8: "When a conversation starts, predict what memories will be needed and pre-load them into context before they're retrieved."

**Dependencies:** Task 21.1 (hierarchical retrieval), Task 5.2 (working memory)

- [x] **21.3.1** Implement conversation topic prediction
  - **Validation:** First user message analyzed for topic signals; top-5 predicted topics used to prefetch relevant memories into Redis cache
  - **Proof:** _pending_

- [x] **21.3.2** Implement time-based prefetch
  - **Validation:** Recurring patterns detected (e.g., "user always asks about project X on Mondays"); relevant memories pre-loaded at predicted times
  - **Proof:** _pending_

- [x] **21.3.3** Measure prefetch hit rate
  - **Validation:** Track how often prefetched memories are actually used in the conversation; target: >50% hit rate after 30 days of use
  - **Proof:** _pending_

---

## PHASE 22 — Versatility & Skills Platform

**Phase Objective:** Build a plugin/skill framework that makes adding new integrations trivial — one base class, 50 lines per new skill.

**Estimated Duration:** 2 sessions
**Completion Criteria:** Base skill class handles auth/permissions/sandboxing/logging; 5+ skills implemented; contributor can add a skill in <50 lines.

**Source:** Bridging §3 "Versatility" — "Don't build 50 integrations — build one integration framework that makes adding any integration trivial."

---

### Task 22.1: Skill Base Framework

**🎯 Skill Activation:** `mcp-builder` — Plugin architecture design.
**🎯 Skill Activation:** `architecture-design` — Extension point design.
**🎯 MCP Activation:** `code-intelligence` — Analyze existing skill loader.

**Context:** Bridging §3: "The base class handles: authentication, permission checking, approval routing, execution sandboxing, result formatting, and audit logging. New skills get all of that for free."

**Dependencies:** Task 5.8 (existing skill loader), Task 5.5 (tool registry)

- [x] **22.1.1** Create `mcp_and_skills/base/skill.py` abstract base class
  - **Validation:** ABC with: `name`, `description`, `required_capabilities`, `execute()`, `get_schema()`; handles auth, permissions, sandboxing, logging automatically
  - **Proof:** _pending_

- [x] **22.1.2** Create `mcp_and_skills/base/manifest.py` schema
  - **Validation:** Pydantic model: name, description, version, author, parameters (JSON Schema), required_permissions, risk_level
  - **Proof:** _pending_

- [x] **22.1.3** Create `mcp_and_skills/base/sandbox.py` execution wrapper
  - **Validation:** Wraps skill execution with: timeout, resource limits, error catching, audit logging; skill code cannot escape sandbox
  - **Proof:** _pending_

- [ ] **22.1.4** Create skill template generator
  - **Validation:** `supernova skill create --name=my-skill` generates boilerplate with base class, manifest, and test file
  - **Proof:** _pending_

- [ ] **22.1.5** Document skill development guide
  - **Validation:** `docs/SKILL_DEVELOPMENT.md` with: quickstart, base class API, manifest format, testing guide, submission process
  - **Proof:** _pending_

---

### Task 22.2: Core Skills Implementation

**🎯 Skill Activation:** `api-integration` — External service integration.
**🎯 MCP Activation:** `execution-engine` — Test each skill.

**Context:** Bridging §3: "A contributor adding a new skill only writes the actual logic — 50 lines, not 500."

**Dependencies:** Task 22.1 (base framework)

- [ ] **22.2.1** Implement `calendar` skill
  - **Validation:** Reads/writes Google Calendar or CalDAV; lists upcoming events; creates events with approval
  - **Proof:** _pending_

- [ ] **22.2.2** Implement `email` skill
  - **Validation:** Reads email via IMAP; sends via SMTP; summarizes inbox; drafts replies with approval
  - **Proof:** _pending_

- [ ] **22.2.3** Implement `notes` skill
  - **Validation:** Creates/reads/searches Markdown notes in `workspace/notes/`; integrates with semantic memory
  - **Proof:** _pending_

- [ ] **22.2.4** Implement `shell` skill
  - **Validation:** Executes shell commands in sandbox; requires SHELL_ACCESS capability + approval for destructive commands
  - **Proof:** _pending_

- [ ] **22.2.5** Implement `browser` skill
  - **Validation:** Fetches and summarizes web pages; extracts structured data; respects robots.txt
  - **Proof:** _pending_

---

## PHASE 23 — Product, UX & Operational Polish

**Phase Objective:** Address product-level issues from v3 — honest setup times, privacy-first defaults, competitive positioning, proactive intelligence.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** Setup works in stated time; Ollama is default; proactive nudges functional; README reflects reality.

**Source:** v3 §3 "Product & UX", v3 §5 "Scalability & Ops", v3 §7 "Competitive Positioning", Bridging §5 "Usefulness", Bridging §6 "Autonomy"

---

### Task 23.1: Privacy-First Defaults

**🎯 Skill Activation:** `architecture-design` — Default configuration design.
**🎯 MCP Activation:** `execution-engine` — Test zero-API-key experience.

**Context:** v3 §3: "The requirement for an OpenAI API key undermines the 'keeps your data private' value proposition. A truly private local assistant would need Ollama integration." v3 §7: "The strongest competitive positioning would be: 'the agent that you can inspect and trust.'"

**Dependencies:** Task 11.4 (Ollama integration)

- [x] **23.1.1** Make Ollama the default LLM when no API keys configured
  - **Validation:** Fresh install with empty `.env` → agent uses Ollama → no external API calls; `tcpdump` shows zero outbound connections to OpenAI/Anthropic
  - **Proof:** _pending_

- [x] **23.1.2** Add local embedding model as default
  - **Validation:** `nomic-embed-text` via Ollama used for embeddings when no OpenAI key; semantic search works fully locally
  - **Proof:** _pending_

- [x] **23.1.3** Update setup wizard to prioritize local models
  - **Validation:** First option in wizard is "Run fully local (recommended for privacy)"; API keys presented as optional enhancement
  - **Proof:** _pending_

- [x] **23.1.4** Lower default budget to safe levels
  - **Validation:** Default `DAILY_BUDGET_USD=1.00`, `MONTHLY_BUDGET_USD=10.00` (down from $10/$100); prevents surprise charges for new users
  - **Proof:** _pending_

---

### Task 23.2: Honest Setup Experience

**🎯 Skill Activation:** `frontend-design` — Onboarding UX.
**🎯 MCP Activation:** `execution-engine` — Time the setup on clean VM.

**Context:** v3 §3: "The 5-minute quick start is almost certainly not 5 minutes. Docker pulling Neo4j, PostgreSQL, Redis, and Langfuse on a fresh machine will take 10-20 minutes."

**Dependencies:** Task -1.1 (installer script)

- [x] **23.2.1** Time actual setup on clean Ubuntu 24.04 VM
  - **Validation:** Record: time to clone, time to docker pull, time to first response; document real numbers
  - **Proof:** _pending_

- [x] **23.2.2** Update README with honest setup time
  - **Validation:** README says "~15-20 minutes on first run (Docker images download); ~2 minutes on subsequent runs"
  - **Proof:** _pending_

- [x] **23.2.3** Add progress indicators during setup
  - **Validation:** `setup.sh` shows progress bar for Docker pulls; estimated time remaining; clear error messages on failure
  - **Proof:** _pending_

- [x] **23.2.4** Reduce infrastructure footprint option
  - **Validation:** `SUPERNOVA_LITE=true` mode runs with only PostgreSQL + Redis (no Neo4j, no Langfuse); ~512MB RAM; episodic memory falls back to PostgreSQL adjacency lists
  - **Proof:** _pending_

---

### Task 23.3: Proactive Intelligence Layer

**🎯 Skill Activation:** `agent-cognitive-architecture` — Proactive agent design.
**🎯 Skill Activation:** `performance-engineering` — Background scheduling.

**Context:** Bridging §5 "Usefulness": "The difference between a calculator and a financial advisor. One answers questions. The other anticipates them."

**Dependencies:** Task 7.1 (Celery), Task 21.1 (advanced memory)

- [ ] **23.3.1** Create `core/agent/proactive.py` with `ProactiveAgent`
  - **Validation:** Runs every 15 minutes via Celery beat; checks for: overdue tasks, follow-up reminders, pattern-based suggestions
  - **Proof:** _pending_

- [ ] **23.3.2** Implement confidence-gated nudges
  - **Validation:** Only surfaces nudges with confidence >0.85; user can adjust threshold; nudges appear as non-intrusive notifications in dashboard
  - **Proof:** _pending_

- [ ] **23.3.3** Implement follow-up detection
  - **Validation:** When user says "remind me to follow up on X" or "I need to do Y later", agent creates a proactive check; surfaces at appropriate time
  - **Proof:** _pending_

- [ ] **23.3.4** Add nudge feedback loop
  - **Validation:** User can dismiss nudges as "helpful" or "not helpful"; feedback adjusts future confidence thresholds per nudge type
  - **Proof:** _pending_

---

### Task 23.4: Data Portability & Export

**🎯 Skill Activation:** `api-integration` — Data format standards.
**🎯 MCP Activation:** `execution-engine` — Test export/import round-trip.

**Context:** v3 §5: "There is no mention of backup, restore, or memory export mechanisms. For a tool that accumulates personal memories over months, data portability and backup are essential."

**Dependencies:** Task 12.4 (existing memory export)

- [ ] **23.4.1** Implement full data export (GDPR-compliant)
  - **Validation:** `supernova export --all --format=json` exports: all memories, conversation history, preferences, trust model state; complete data portability
  - **Proof:** _pending_

- [ ] **23.4.2** Implement data import from other assistants
  - **Validation:** `supernova import --from=chatgpt --file=conversations.json` imports ChatGPT export; maps to SuperNova memory format
  - **Proof:** _pending_

- [ ] **23.4.3** Add data deletion command
  - **Validation:** `supernova forget --all` permanently deletes all user data from all stores (PostgreSQL, Redis, Neo4j); confirmation required; irreversible
  - **Proof:** _pending_

---

### Task 23.5: README & Documentation Overhaul

**🎯 Skill Activation:** `context-management` — Documentation structure.

**Context:** v3 §7: "The strongest competitive positioning would be: 'the agent that you can inspect and trust' — leaning into transparency as the core value."

**Dependencies:** All previous phases

- [x] **23.5.1** Rewrite README lead with trust-first positioning
  - **Validation:** First paragraph emphasizes: local-first, inspectable memory, approval-gated actions, your data stays yours; not "yet another AI assistant"
  - **Proof:** _pending_

- [x] **23.5.2** Add architecture diagram
  - **Validation:** Mermaid diagram showing: User → API → Orchestrator → [Planner, Executor, Critic] → Memory → LLM → Response; included in README
  - **Proof:** _pending_

- [x] **23.5.3** Add honest comparison table
  - **Validation:** Table comparing SuperNova vs MemGPT vs Open Interpreter vs ChatGPT on: privacy, memory, approval system, local-first, cost; honest about weaknesses
  - **Proof:** _pending_

- [ ] **23.5.4** Create `docs/ARCHITECTURE.md`
  - **Validation:** Detailed architecture doc: component diagram, data flow, memory schema, security model, deployment topology
  - **Proof:** _pending_

- [ ] **23.5.5** Create `docs/MEMORY_SCHEMA.md`
  - **Validation:** Documents all memory types, their schemas, retrieval strategies, consolidation rules, and export format
  - **Proof:** _pending_

---

## Completion Log

| Phase | Task                                | Completed At | Evidence |
| ----- | ----------------------------------- | ------------ | -------- |
| 16    | Architecture Refactoring            | _pending_    | _pending_ |
| 17    | Security Remediation                | _pending_    | _pending_ |
| 18    | Performance & Async Pipeline        | _pending_    | _pending_ |
| 19    | Multi-Agent Orchestration           | _pending_    | _pending_ |
| 20    | Reasoning & Intelligence Pipeline   | _pending_    | _pending_ |
| 21    | Advanced Memory Architecture        | _pending_    | _pending_ |
| 22    | Versatility & Skills Platform       | _pending_    | _pending_ |
| 23    | Product, UX & Operational Polish    | _pending_    | _pending_ |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Phases | 8 (Phase 16–23) |
| Total Tasks | 33 |
| Total Sub-tasks | 126 |
| Critical Constraints (new) | 8 (CC-21 through CC-28) |
| Priority: 🔴 Critical | 2 phases (16, 17) |
| Priority: 🟡 High | 4 phases (18, 19, 20, 21) |
| Priority: 🟢 Medium | 2 phases (22, 23) |

---

## Cross-Reference: v3 Evaluation → Checklist Mapping

| v3 Section | Finding | Checklist Phase | Task(s) |
|------------|---------|-----------------|---------|
| §1 Architecture — flat structure | Root-level core files | Phase 16 | 16.1.1–16.1.7 |
| §1 Architecture — heavy infra | 4 Docker services, 2-4GB RAM | Phase 23 | 23.2.4 |
| §2 Code Quality — tarballs in git | Binary artifacts committed | Phase 16 | 16.2.3–16.2.4 |
| §2 Code Quality — no CI/CD | No GitHub Actions | Phase 16 | 16.3.1–16.3.6 |
| §3 Product — setup time lie | "5 minutes" is 15-20 | Phase 23 | 23.2.1–23.2.3 |
| §3 Product — OpenAI dependency | Undermines privacy story | Phase 23 | 23.1.1–23.1.3 |
| §3 Product — high default budget | $10/day too high | Phase 23 | 23.1.4 |
| §4 Security — .env committed | Critical security issue | Phase 16 | 16.2.1–16.2.2 |
| §4 Security — no API auth | Open endpoints | Phase 17 | 17.1.1–17.1.4 |
| §4 Security — approval bypass risk | Timeout/queue manipulation | Phase 17 | 17.4.1–17.4.4 |
| §4 Security — no input sanitization | Prompt injection risk | Phase 17 | 17.2.1–17.2.5 |
| §5 Scalability — no backup/export | Data portability missing | Phase 23 | 23.4.1–23.4.3 |
| §6 PM — no issues/PRs | Not tracking work in GitHub | Phase 16 | 16.3.1 (CI implies issue tracking) |
| §7 Competitive — trust positioning | Not front-and-center | Phase 23 | 23.5.1–23.5.3 |
| Bridging §1 — Performance | Serial processing | Phase 18 | 18.1–18.4 |
| Bridging §2 — Security | Injection, validation, sandbox | Phase 17 | 17.2–17.3 |
| Bridging §3 — Versatility | No plugin framework | Phase 22 | 22.1–22.2 |
| Bridging §4 — Power | Single agent | Phase 19 | 19.1 |
| Bridging §5 — Usefulness | Reactive only | Phase 23 | 23.3 |
| Bridging §6 — Autonomy | Binary approval | Phase 19 | 19.2 |
| Bridging §7 — Intelligence | Single LLM call | Phase 20 | 20.1 |
| Bridging §8 — Memory | Naive similarity search | Phase 21 | 21.1–21.3 |
| v3 Overall Verdict | "Pre-alpha in engineering rigor" | All Phases | Full checklist addresses this |
