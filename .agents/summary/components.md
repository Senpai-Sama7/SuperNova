# SuperNova — Components Reference

## Root-Level Modules (Load-Bearing)

These files live at the project root and contain the core cognitive logic. They are imported by `supernova/core/agent/` wrappers.

### loop.py — Cognitive Loop (836 LOC)
Central executive implementing the 8-phase cognitive cycle as a LangGraph StateGraph.

**Key exports:**
- `AgentState(TypedDict)` — Immutable state container for the agent graph
- `build_agent_graph(db_pool, redis, ...)` → compiled LangGraph `CompiledStateGraph`
- `make_session_config(session_id, thread_id)` → RunnableConfig for graph invocation
- `memory_retrieval_node()` — Parallel episodic + semantic + working memory retrieval
- `reasoning_node()` — LLM call via DynamicModelRouter with context assembly
- `tool_execution_node()` — Capability-gated tool execution with HITL interrupts
- `reflection_node()` — Optional self-evaluation
- `memory_consolidation_node()` — Episode writing + working memory update
- `route_after_reasoning()` — Pure routing function (tool calls → execute, reflect → reflect, else → consolidate)

### context_assembly.py — Context Window Assembly (368 LOC)
Implements positional context optimization based on Liu et al. (2023) primacy/recency attention topology.

**Key exports:**
- `ContextZone(Enum)` — PRIMACY, MIDDLE, RECENCY zones
- `ContextBudget` — Token budget allocation across zones
- `ContextInputs` — All inputs for context assembly (system prompt, memories, plan, history)
- `assemble_context_window(inputs, budget)` → `list[dict]` of positioned messages
- `estimate_context_stats(messages)` → token usage statistics

### procedural.py — Procedural Memory & Skill Crystallization (670 LOC)
Compiled skill storage and automatic skill extraction from execution traces.

**Key exports:**
- `SkillRecord` — Dataclass for stored skills (name, description, trigger_patterns, compiled_graph)
- `SkillMatch` — Result of skill recall (skill, confidence, match_reason)
- `ProceduralMemoryStore` — PostgreSQL-backed skill CRUD + recall via embedding similarity
- `SkillCrystallizationWorker` — Extracts repeated tool-call patterns from Langfuse traces, compiles into LangGraph subgraphs

### dynamic_router.py — Capability-Vector Model Router (825 LOC)
Routes LLM calls to optimal models based on task requirements, cost constraints, and live performance data.

**Key exports:**
- `ModelCapabilityVector` — Per-model capability profile (reasoning, coding, speed, cost, context_window)
- `TaskRequirementVector` — Per-task requirement profile
- `TokenUsageTracker` — EMA-based token usage estimation per task type
- `DynamicModelRouter` — Main router with live pricing updates, budget enforcement, Ollama fallback

### interrupts.py — HITL Interrupt Coordinator (582 LOC)
Human-in-the-loop approval system for high-risk tool executions.

**Key exports:**
- `RiskLevel(Enum)` — LOW, MEDIUM, HIGH, CRITICAL with per-level timeouts
- `PendingApproval` — Approval request with tool details, risk assessment, expiry
- `ApprovalResult(NamedTuple)` — Decision outcome (approved, reason, decided_by)
- `InterruptCoordinator` — Manages approval lifecycle with OS notifications and WebSocket alerts
- `create_interrupt_router(coordinator)` → FastAPI router for approval endpoints

---

## supernova/ Package

### api/ — FastAPI Application Layer

| File | Purpose |
|------|---------|
| `gateway.py` | Main FastAPI app factory with lifespan, CORS, health, auth, WS, all route mounts |
| `auth.py` | JWT authentication (create_access_token, verify_token, get_current_user) |
| `websockets.py` | WebSocketBroadcaster for real-time event streaming |
| `routes/agent.py` | `POST /api/v1/agent/message` — Agent message endpoint |
| `routes/dashboard.py` | `GET /api/v1/dashboard/snapshot`, `POST /approvals/{id}/resolve` |
| `routes/mcp_routes.py` | MCP server management and skills API |
| `routes/onboarding.py` | Setup wizard: status, key validation, cost estimate, completion |

### core/memory/ — Memory System Implementations

| File | Store | Backend | Latency |
|------|-------|---------|---------|
| `episodic.py` | `EpisodicMemoryStore` | Neo4j + Graphiti | 20-80ms |
| `semantic.py` | `SemanticMemoryStore` | PostgreSQL + pgvector (HNSW) | 5-30ms |
| `working.py` | `WorkingMemoryStore` + `WorkingMemory` dataclass | Redis + msgpack | <5ms |
| `procedural.py` (root) | `ProceduralMemoryStore` | PostgreSQL | 10-50ms |

### core/backup/ — Backup & Recovery

| File | Purpose |
|------|---------|
| `manager.py` | `BackupManager`: pg_dump, Neo4j export, Redis RDB, Fernet encryption, S3 upload, rotation |
| `cli.py` | CLI commands: backup, restore, export, verify |

### infrastructure/llm/ — LLM Infrastructure

| File | Purpose |
|------|---------|
| `cost_controller.py` | Redis-backed cost tracking + budget enforcement per model/session |
| `ollama_client.py` | Async Ollama client for local LLM fallback |

### infrastructure/security/ — Security Infrastructure

| File | Purpose |
|------|---------|
| `serializer.py` | HMAC-signed pickle with `_RestrictedUnpickler` (allowlisted classes only) |
| `secrets.py` | `SecretsVault`: AES-256-GCM encryption + platform keychain integration |
| `audit.py` | `@audit_log` decorator + `query_audit_logs` for compliance |

### infrastructure/observability/ — Observability

| File | Purpose |
|------|---------|
| `logging.py` | structlog JSON config + correlation ID middleware + log rotation |
| `health.py` | `deep_health_check()` for Postgres/Redis/Neo4j + `HealthAlertManager` |
| `metrics.py` | `MetricsCollector` with Prometheus-format rendering + `RequestTimer` |
| `cli.py` | Diagnostic CLI: doctor, logs, status, report |

### infrastructure/tools/ — Tool System

| File | Purpose |
|------|---------|
| `registry.py` | `ToolRegistry` with `Capability(Flag)` gating, execution logging |
| `builtin/code_exec.py` | Docker/gVisor sandbox with seccomp + resource limits |
| `builtin/file_ops.py` | File read/write with path jail to `./workspace/` |
| `builtin/web_search.py` | Tavily/SerpAPI web search |

### mcp/ — Model Context Protocol

| File | Purpose |
|------|---------|
| `client/mcp_client.py` | `MCPClient`: server lifecycle, tool listing, tool calling, health checks |
| `tools/mcp_tool_bridge.py` | `bridge_mcp_tools()`: converts MCP tool schemas to LangChain Tool format |

### skills/ — Skill System

| File | Purpose |
|------|---------|
| `loader.py` | `SkillLoader`: discovers `.skill` files, hot-reloads on change, converts to prompts |

### workers/ — Celery Background Workers

| File | Task | Schedule |
|------|------|----------|
| `celery_app.py` | App config + RedBeat scheduler | — |
| `consolidation.py` | Episodic→semantic transfer + skill crystallization | Hourly / Daily 2am |
| `heartbeat.py` | Redis/Postgres/Neo4j health checks + Langfuse trace | Every 15min |
| `maintenance.py` | Forgetting curves via asyncpg stored procedure | Weekly Sunday 3am |
| `mcp_monitor.py` | MCP server health + auto-restart with exponential backoff | Every 5min |
| `backup.py` | Daily backup with rotation + verification | Daily 2:30am |

---

## dashboard/ — React Frontend

### Core Architecture
- **React 19** + **Vite 7** + **TypeScript 5.8**
- **Three.js** (via @react-three/fiber) for 3D memory visualization
- **GSAP** for animations
- HTTP polling (3s) + WebSocket with exponential backoff

### Key Components

| Category | Components |
|----------|-----------|
| Cards | AgentCard, ApprovalCard, MCPServersPanel, MCPToolExplorer, SkillPanel, MCPExecutionLog, CostWidget, ExportButton, HealthPanel |
| Charts | CognitiveCycleRing, ConfidenceMeter, Sparkline, MemoryGraph, OrchestrationGraph, ConformalBandChart |
| UI | StatusDot, Badge, Glow, MiniBar, RiskPill |
| 3D | MemorySpace3D, MemoryNode3D, ConnectionLines3D, EntropyField, AdaptiveLighting |
| Onboarding | SetupWizard, Tutorial, ExamplePrompts, FeatureDiscovery |
| Modes | SimpleMode, ModeToggle (simple/advanced dashboard switching) |
| Help | Tooltip, HelpPanel, KeyboardShortcuts, FAQ |
| Animated | AnimatedStatusDot, AnimatedGlow, AnimatedApprovalCard, AnimatedConfidenceMeter, AnimatedAgentCard, AnimatedMiniBar |

### Hooks
- `useNovaRealtime` — HTTP polling + WebSocket with exponential backoff
- `useAnimation` — GSAP animation utilities

---

## MCP & Skills Inventory

### mcp_and_skills/ Directory

External MCP server configurations and skill definitions used by SuperNova's `MCPClient` and `SkillLoader`.

#### Custom MCP Server: omni-mcp-server

Location: `mcp_and_skills/custom-mcp-servers/omni-mcp-server/`

| Tool Module | Capabilities |
|-------------|-------------|
| `browser.ts` | Puppeteer browser automation |
| `docker.ts` | Container management |
| `system.ts` | System monitoring |
| `network.ts` | Network operations |
| `websocket.ts` | WebSocket connections |
| `image.ts` | Image processing, OCR |
| `notify.ts` | Desktop notifications |

#### Skill Files (43 total)

Skills are `.skill` definition files discovered by `SkillLoader` and hot-reloaded at runtime.

| Category | Skills |
|----------|--------|
| Agent/Architecture | `agent-cognitive-architecture`, `architecture-design`, `multi-agent-orchestration` |
| Development | `code-review-refactoring`, `debugging-root-cause-analysis`, `test-driven-development`, `frontend-design`, `api-integration`, `database-design-optimization` |
| DevOps/Infra | `ci-cd-devops`, `observability-monitoring`, `performance-engineering`, `security-engineering`, `cloudflare-403-triage` |
| AI/Prompts | `optimize-prompt`, `context-management`, `create-plan`, `mcp-builder`, `spec-forge` |
| Documents | `docx`, `pdf`, `pptx`, `xlsx` |
| GitHub | `gh-address-comments`, `gh-fix-ci` |
| Notion | `notion-knowledge-capture`, `notion-meeting-intelligence`, `notion-research-documentation`, `notion-spec-to-implementation` |
| Android | `android-app`, `android-app-dev`, `android-instructor-led-curriculum` |
| UPS Domain | `ups-causal-interventions`, `ups-decision-intelligence-ui`, `ups-evaluation-calibration`, `ups-kb-authoring`, `ups-predict-dashboard`, `ups-probabilistic-answering`, `ups-system-blueprint-mlops` |
| Web | `web-artifacts-builder`, `webapp-testing` |
| Other | `hostile-auditor`, `linear` |

#### Reference Documentation

| File | Content |
|------|---------|
| `MCP_SERVERS.md` | Server inventory with credentials mapping |
| `MCP_INTEGRATION_SUMMARY.md` | Full integration architecture (17 servers) |
| `MCP_QUICK_REFERENCE.md` | Quick reference for MCP tool usage |
| `skills/README.md` | Skill authoring guide |
| `skills/INTEGRATION_STATUS.md` | Skill integration status tracker |
