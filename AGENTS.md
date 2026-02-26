# SuperNova — AI Coding Agent Reference

> **Project Type**: Production-grade personal AI agent with persistent memory and autonomous cognition  
> **Language**: Python 3.12+ (backend), React/JSX (dashboard)  
> **Architecture**: LangGraph-based cognitive loop with multi-tier memory systems

---

## Project Overview

SuperNova is a durable, observable, and self-improving AI agent system implementing a cognitive architecture inspired by human memory systems. The agent features:

1. **Durable Execution** — Process crashes resume from the interrupted step via PostgreSQL checkpointing
2. **Observability** — Full tracing in Langfuse with input/output capture for every LLM call and tool execution
3. **Security** — Capability-gated tool execution with human-in-the-loop (HITL) approval for high-risk operations
4. **Self-Improvement** — Automatic skill crystallization from successful execution traces
5. **Positional Context Optimization** — Context window assembly following Liu et al. (2023) primacy/recency attention topology

### Five Core Properties

| Property             | Implementation                                       |
| -------------------- | ---------------------------------------------------- |
| Durable              | LangGraph + AsyncPostgresSaver checkpointing         |
| Observable           | Langfuse tracing with full I/O capture               |
| Secure               | Capability flags + HITL interrupt coordinator        |
| Self-improving       | SkillCrystallizationWorker from procedural.py        |
| Positionally optimal | Context assembly across Primacy/Middle/Recency zones |

---

## Technology Stack

### Backend Dependencies

Core runtime dependencies (from `supernova/pyproject.toml`):

```
langgraph>=0.2.0              # Stateful agent graph with checkpointing
langgraph-checkpoint-postgres>=0.1  # PostgreSQL checkpoint backend
langchain-core>=0.3.0         # Core LangChain components
litellm>=1.40.0               # Universal LLM proxy (100+ providers)
graphiti-core>=0.3.0          # Temporal knowledge graph (episodic memory)
asyncpg>=0.29.0               # Async PostgreSQL driver
sqlalchemy[asyncio]>=2.0.0    # ORM for database operations
redis[hiredis]>=5.0.0         # Working memory + Celery broker
neo4j>=5.20.0                 # Neo4j driver for episodic memory
fastapi>=0.111.0              # API layer
uvicorn[standard]>=0.29.0     # ASGI server with uvloop
websockets>=12.0              # WebSocket support
python-jose[cryptography]>=3.3.0  # JWT authentication
pydantic>=2.7.0               # Data validation
pydantic-settings>=2.2.0      # Environment configuration
celery[gevent]>=5.4.0         # Background task execution
celery-redbeat>=2.2.0         # Redis-backed Celery Beat scheduler
langfuse>=2.0.0               # Observability and tracing
msgpack>=1.0.8                # Binary serialization for working memory
httpx>=0.27.0                 # Async HTTP client
orjson>=3.10.0                # Fast JSON serialization
structlog>=24.1.0             # Structured logging
openai>=1.30.0                # OpenAI API client
tiktoken>=0.7.0               # Token counting
numpy>=1.26.0                 # Numerical operations
mcp>=1.0.0                    # Model Context Protocol client
```

### Frontend Dependencies

Dashboard UI (from `dashboard/package.json`):

```
React 19.2.0                  # UI framework
Vite 7.3.1                    # Build tool and dev server
Three.js 0.183.1              # 3D graphics (memory visualization)
@react-three/fiber 9.5.0      # React Three.js bindings
@react-three/drei 10.7.7      # Three.js helpers
GSAP 3.14.2                   # Animation library
Vitest 3.2.4                  # Unit testing
Playwright 1.56.1             # E2E testing
TypeScript 5.8.3              # Type checking
ESLint 9.39.1                 # Linting
```

### Infrastructure Services

- **PostgreSQL 16** — Semantic memory, procedural memory, checkpoints, pgvector extension
- **Neo4j 5** — Episodic memory via Graphiti temporal knowledge graph
- **Redis 7** — Working memory, Celery broker, embedding cache
- **Langfuse 2** — Trace observability dashboard

---

## Project Structure

> **Note**: Root-level Python modules (`loop.py`, `context_assembly.py`, etc.) are the canonical implementations. Files in `supernova/core/agent/` and `supernova/core/reasoning/` are thin re-export wrappers.

```
supernova/                      # Main Python package
├── __init__.py
├── config.py                   # Pydantic Settings configuration loader
├── pyproject.toml              # Python dependencies and tool configs
├── alembic.ini                 # Database migration configuration
│
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
│       ├── 23aa65fd8071_initial_schema.py
│       └── b7c3e9f12a45_audit_logs.py
│
├── api/                        # FastAPI application layer
│   ├── auth.py                 # JWT authentication (create_access_token, verify_token, get_current_user)
│   ├── gateway.py              # FastAPI gateway (lifespan, health, auth, WS, memory, admin, CORS)
│   ├── main.py                 # Legacy FastAPI app factory
│   ├── websockets.py           # WebSocket broadcaster and event stream handler
│   └── routes/
│       ├── agent.py            # POST /api/v1/agent/message
│       ├── dashboard.py        # GET /snapshot, POST /approvals/{id}/resolve
│       ├── mcp_routes.py       # MCP server and skills API endpoints
│       └── onboarding.py       # Setup wizard, key validation, cost estimate, first-run detection
│
├── core/                       # Core agent logic
│   ├── agent/                  # Re-export wrappers for root-level loop.py, interrupts.py
│   ├── backup/                 # Backup & recovery system
│   │   ├── manager.py          # BackupManager: pg_dump, neo4j, Redis, Fernet, S3
│   │   └── cli.py              # CLI: backup/restore/export commands
│   ├── memory/                 # Memory system implementations
│   │   ├── episodic.py         # Graphiti/Neo4j episodic memory
│   │   ├── semantic.py         # PostgreSQL/pgvector semantic memory
│   │   ├── working.py          # Redis working memory
│   │   └── procedural.py       # Re-export wrapper for root-level procedural.py
│   └── reasoning/              # Re-export wrappers for context_assembly.py, dynamic_router.py
│
├── infrastructure/             # Infrastructure adapters
│   ├── llm/
│   │   ├── cost_controller.py      # Redis-backed cost tracking + budget enforcement
│   │   └── ollama_client.py        # Async Ollama client for local LLM fallback
│   ├── security/
│   │   ├── serializer.py       # HMAC-signed pickle with restricted unpickler
│   │   ├── secrets.py          # AES-256-GCM vault + platform keychain
│   │   └── audit.py            # @audit_log decorator + query_audit_logs
│   ├── observability/
│   │   ├── logging.py          # structlog JSON config + correlation ID + rotation
│   │   ├── health.py           # Deep health checks + HealthAlertManager
│   │   ├── metrics.py          # Prometheus-format metrics collector
│   │   └── cli.py              # Diagnostic CLI (doctor/logs/status/report)
│   ├── storage/
│   │   ├── postgres.py         # PostgreSQL connection pool
│   │   └── redis.py            # Redis client
│   └── tools/
│       ├── builtin/
│       │   ├── code_exec.py    # Hardened sandbox (Docker/gVisor + seccomp + resource limits)
│       │   ├── file_ops.py     # File operations (path jail to ./workspace/)
│       │   └── web_search.py   # Web search (Tavily/SerpAPI)
│       └── registry.py         # Tool registry (capability-gated)
│
├── mcp/                        # Model Context Protocol integration
│   ├── client/
│   │   └── mcp_client.py      # MCPClient: server lifecycle, tool listing, calling, health
│   └── tools/
│       └── mcp_tool_bridge.py  # Converts MCP tool schemas to LangChain Tool format
│
├── skills/
│   └── loader.py               # SkillLoader: discovers .skill files, hot-reloads
│
├── tests/                      # Test suite (27 files)
│   ├── conftest.py             # Shared fixtures (db_pool, redis, mock_llm, embedder, registry, coordinator)
│   ├── test_agent_routes.py    # Agent message endpoint (new/existing session)
│   ├── test_api_main.py        # Legacy API factory tests
│   ├── test_auth.py
│   ├── test_backup.py          # Backup manager, worker, export/import, CLI tests
│   ├── test_builtin_tools.py
│   ├── test_context_assembly.py  # Primacy/middle/recency zone tests
│   ├── test_cost_controller.py   # Cost tracking, budget routing, Ollama client tests
│   ├── test_dashboard.py        # Dashboard helpers + snapshot/approval endpoints
│   ├── test_e2e.py              # End-to-end integration tests
│   ├── test_episodic.py
│   ├── test_gateway.py
│   ├── test_interrupts.py      # HITL approval flow, timeout, risk-level tests
│   ├── test_mcp_api.py
│   ├── test_mcp_client.py
│   ├── test_memory_retrieval.py  # Upsert/search round trip, forgetting curve, hybrid search
│   ├── test_observability.py    # Structured logging, health checks, metrics, CLI tests
│   ├── test_onboarding.py       # Setup wizard API tests
│   ├── test_registry.py
│   ├── test_routing.py         # Capability-vector routing, cost constraints, fleet summary
│   ├── test_security.py        # Serializer, secrets vault, audit logging, sandbox tests
│   ├── test_semantic.py
│   ├── test_skills.py
│   ├── test_storage.py         # Redis client + Postgres pool CRUD methods
│   ├── test_websockets.py
│   └── test_workers.py
│
├── workers/                    # Celery background workers
│   ├── celery_app.py           # Celery app (Redis broker, RedBeat, 6 beat schedules)
│   ├── consolidation.py        # Episodic→semantic transfer + skill crystallization
│   ├── heartbeat.py            # Redis/Postgres/Neo4j health checks + Langfuse trace
│   ├── maintenance.py          # Forgetting curves via asyncpg stored procedure
│   ├── mcp_monitor.py          # MCP server health + auto-restart with exponential backoff
│   └── backup.py               # Daily backup Celery task with rotation + verification

# Root-level specification files (load-bearing)
├── loop.py                     # Cognitive loop (LangGraph StateGraph) — 836 LOC
├── context_assembly.py         # Positional context window assembly — 368 LOC
├── procedural.py               # Compiled skill storage & crystallization — 670 LOC
├── dynamic_router.py           # Capability-vector model router — 825 LOC
├── interrupts.py               # HITL interrupt coordinator — 582 LOC
├── DEPLOYMENT.conf             # Systemd services, Dockerfile, Nginx config
├── docker-compose.yml          # Infrastructure stack (Postgres, Redis, Neo4j, Langfuse)
├── loadtest.py                 # Locust load testing script
├── setup.sh                    # Environment setup script
├── PROGRESS_TRACKER.md         # 16-phase build progress tracker
├── SYSTEM_RELATION_GRAPH.md    # Architecture knowledge graph with Mermaid diagrams
├── AGENTS.md                   # This file
├── README.md                   # Project overview and getting started
├── CONTRIBUTING.md             # Development and contribution guide
├── .env.example                # Environment variable template (70+ options)
└── .env                        # Local environment configuration (gitignored)

# Dashboard (React frontend)
dashboard/
├── package.json
├── vite.config.js
├── playwright.config.js
├── eslint.config.js
├── index.html
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── NovaDashboard.tsx           # Main dashboard component
│   ├── types/index.ts              # Centralized TypeScript types
│   ├── theme/index.ts              # Design tokens + API_BASE
│   ├── hooks/
│   │   ├── useNovaRealtime.ts      # HTTP polling + WebSocket with exponential backoff
│   │   └── useAnimation.ts         # GSAP animation utilities
│   ├── components/
│   │   ├── ui/                     # StatusDot, Badge, Glow, MiniBar, RiskPill
│   │   ├── cards/                  # AgentCard, ApprovalCard, MCPServersPanel, MCPToolExplorer, SkillPanel, MCPExecutionLog, CostWidget, ExportButton, HealthPanel
│   │   ├── charts/                 # CognitiveCycleRing, ConfidenceMeter, Sparkline, MemoryGraph, OrchestrationGraph, ConformalBandChart
│   │   ├── onboarding/             # SetupWizard, Tutorial, ExamplePrompts, FeatureDiscovery
│   │   ├── modes/                  # SimpleMode, ModeToggle (simple/advanced switching)
│   │   ├── help/                   # Tooltip, HelpPanel, KeyboardShortcuts, FAQ
│   │   ├── animated/               # AnimatedStatusDot, AnimatedGlow, AnimatedApprovalCard, AnimatedConfidenceMeter, AnimatedAgentCard, AnimatedMiniBar
│   │   ├── 3d/                     # 3D component index
│   │   ├── MemorySpace3D.tsx       # Three.js 3D memory visualization
│   │   ├── MemoryNode3D.tsx        # Individual 3D memory nodes
│   │   ├── ConnectionLines3D.tsx   # 3D connection lines
│   │   ├── EntropyField.tsx        # Entropy visualization
│   │   └── AdaptiveLighting.tsx    # Dynamic 3D lighting
│   ├── utils/
│   │   ├── numberGuards.ts         # Numeric validation utilities
│   │   └── entropy.ts              # Entropy calculations
│   ├── lib/animations.ts           # Animation utilities
│   └── styles/                     # CSS modules and global styles
├── tests/
│   └── e2e/                        # Playwright E2E tests
└── dist/                           # Production build output

# MCP and Skills
mcp_and_skills/                 # MCP servers and skill definitions
├── MCP_INTEGRATION_SUMMARY.md
├── MCP_QUICK_REFERENCE.md
├── MCP_SERVERS.md
├── skills/                     # Skill definitions (.skill files)
├── custom-mcp-servers/         # Custom MCP servers
├── mcp-servers/                # Pre-built MCP servers
└── ...                         # Various MCP configurations

# Workspace and logs
workspace/                      # Jailed file access directory
logs/                           # Application logs
```

---

## Build and Development Commands

### Environment Setup

```bash
# Run the automated setup script
./setup.sh

# Manual validation
python3 --version    # Requires 3.12+
docker --version
docker compose version

# Install uv (Astral's Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python Backend

```bash
cd supernova

# Install dependencies with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Database Migrations

```bash
cd supernova
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Running the Application

```bash
# Start infrastructure
docker compose up -d

# Start the API server (from supernova/ directory)
uvicorn api.gateway:app --reload --log-level debug

# Or from project root
PYTHONPATH=./supernova uvicorn supernova.api.gateway:app --reload

# Start Celery worker (terminal 2)
cd supernova && celery -A workers worker --loglevel=debug

# Start Celery Beat scheduler (terminal 3)
cd supernova && celery -A workers beat --loglevel=debug --scheduler=redbeat.RedBeatScheduler
```

### Dashboard (Frontend)

```bash
cd dashboard
npm install
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview production build
```

### Load Testing

```bash
pip install locust
locust -f loadtest.py --host http://localhost:8000
# Web UI: http://localhost:8089
# Headless: locust -f loadtest.py --host http://localhost:8000 --headless -u 50 -r 5 -t 60s
```

---

## Testing Commands

### Python Backend Tests

```bash
cd supernova

# Run all tests with coverage
pytest tests/ -v --cov=supernova --cov-report=term-missing

# Run with coverage threshold (80% minimum)
pytest tests/ --cov=supernova --cov-fail-under=80

# Run specific test file
pytest tests/test_auth.py -v

# Run unit tests only (exclude integration)
pytest tests/ -v -m "not integration"

# Run integration tests only
pytest tests/ -v -m integration

# Parallel execution
pytest tests/ -x --tb=short
```

### Frontend Tests

```bash
cd dashboard
npm run test:unit     # Vitest
npm run test:e2e      # Playwright
npm run test          # All tests
```

### Test Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| supernova/ | 80% |
| api/ | 80% |
| core/ | 85% |
| infrastructure/ | 80% |

---

## Code Style Guidelines

### Python Standards

**Ruff Configuration** (from `pyproject.toml`):
- Target: Python 3.12+
- Line length: 100 characters
- Indent: 4 spaces, double quotes

```bash
cd supernova
ruff check .           # Lint
ruff check . --fix     # Auto-fix
ruff format .          # Format
```

**Enabled Rules**: E, W, F, I, N, D (Google convention), UP, B, C4, SIM, ARG, PTH, ERA, PL, PERF, RUF

### MyPy Type Checking

```bash
cd supernova
mypy . --ignore-missing-imports
```

- Strict mode enabled
- All functions must have type annotations

### JavaScript/React Standards

```bash
cd dashboard
npm run lint
```

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Critical Variables**:
- `SUPERNOVA_SECRET_KEY` — Cryptographic key (generate: `openssl rand -hex 32`)
- `SUPERNOVA_ENV` — development/staging/production
- `POSTGRES_*` — PostgreSQL connection (host, port, db, user, password)
- `NEO4J_*` — Neo4j connection (uri, user, password)
- `REDIS_URL` — Redis connection
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — LLM provider keys
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` — Observability
- `PICKLE_HMAC_KEY` — Secure deserialization key
- `API_KEY_ENCRYPTION_KEY` — API key encryption

See `.env.example` for complete documentation of all 70+ configuration options.

### Pydantic Settings

```python
from supernova.config import get_settings
settings = get_settings()
```

Settings classes: `DatabaseSettings`, `RedisSettings`, `Neo4jSettings`, `LLMSettings`, `LangfuseSettings`, `SecuritySettings`

---

## Security Considerations

### Capability-Based Tool Permissions

```python
class Capability(Flag):
    READ_FILES   = auto()
    WRITE_FILES  = auto()
    EXECUTE_CODE = auto()
    WEB_SEARCH   = auto()
    WEB_BROWSE   = auto()
    SEND_EMAIL   = auto()
    SHELL_ACCESS = auto()
    EXTERNAL_API = auto()
```

### Path Jail
File operations restricted to `./workspace/` — any path containing `..` is rejected.

### Risk Levels and HITL

| Risk Level | Examples                            | Timeout | Auto-resolve |
| ---------- | ----------------------------------- | ------- | ------------ |
| LOW        | web_search, file_read               | 30s     | Approve      |
| MEDIUM     | file_write, code_execute            | 120s    | Deny         |
| HIGH       | send_email, post_to_service         | 300s    | Deny         |
| CRITICAL   | make_payment, delete_database       | 600s    | Deny         |

### Secret Handling
- Never log API keys, JWT tokens, or database passwords
- Log only first 8 characters of any secret for debugging
- Pickle deserialization only from trusted PostgreSQL with HMAC verification

---

## Cognitive Loop Phases

The agent's cognitive cycle (implemented in `loop.py`):

```
PERCEIVE    → restore state from checkpoint, receive new input
REMEMBER    → parallel retrieval from episodic + semantic + procedural + working memory
PRIME       → check procedural memory for applicable compiled skill
ASSEMBLE    → build optimally-positioned context window
REASON      → LLM call with assembled context
ACT         → execute tool calls (with interrupt checkpoint)
REFLECT     → optional self-evaluation if quality criteria triggered
CONSOLIDATE → write new episodes and update working memory
```

### Routing Logic

```python
def route_after_reasoning(state: AgentState) -> str:
    if tool_calls_this_turn >= 15:
        return "consolidate"  # Safety gate
    if last_message has tool_calls:
        return "execute_tools"
    if should_reflect and not reflection_critique:
        return "reflect"
    return "consolidate"
```

---

## Memory Systems

| System | Backend | Store | Latency | Purpose |
|--------|---------|-------|---------|---------|
| Episodic | Neo4j + Graphiti | `core/memory/episodic.py` | 20-80ms | Temporal reasoning — "what happened when?" |
| Semantic | PostgreSQL + pgvector | `core/memory/semantic.py` | 5-30ms | Factual retrieval — "what do I know about X?" |
| Working | Redis + msgpack | `core/memory/working.py` | <5ms | Fast ephemeral storage, current context |
| Procedural | PostgreSQL | `procedural.py` (root) | 10-50ms | Compiled skills — "how do I do Y?" |

---

## Deployment Architecture

### Docker Compose (Development)

```bash
docker compose up -d    # Start Postgres, Redis, Neo4j, Langfuse
```

### Systemd Services (Production)

| Service                    | Purpose               | Resource Limits              |
| -------------------------- | --------------------- | ---------------------------- |
| `supernova-agent.service`  | Main FastAPI process  | MemoryMax=2G, CPUQuota=200%  |
| `supernova-worker.service` | Celery worker         | MemoryMax=1G, CPUQuota=100%  |
| `supernova-beat.service`   | Celery Beat scheduler | MemoryMax=256M, CPUQuota=25% |

### Nginx Reverse Proxy
- TLS termination (Certbot/Let's Encrypt)
- WebSocket upgrade support (300s timeout)
- Rate limiting: 60 req/min general, 10 conn/min WebSocket
- Security headers (HSTS, CSP, X-Frame-Options)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness/readiness with backend checks |
| POST | `/api/v1/agent/message` | Send message to agent |
| GET | `/api/v1/dashboard/snapshot` | Full dashboard state |
| POST | `/api/v1/dashboard/approvals/{id}/resolve` | Approve/deny tool execution |
| GET | `/api/v1/onboarding/status` | Setup state |
| POST | `/api/v1/onboarding/validate-key` | Validate API key |
| GET | `/api/v1/onboarding/cost-estimate` | Cost projections |
| POST | `/api/v1/onboarding/complete` | Finalize setup |
| GET | `/api/v1/mcp/servers` | MCP server status |
| GET | `/api/v1/mcp/tools` | Available MCP tools |
| WS | `/ws/{session_id}` | Real-time event stream |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| LangGraph for orchestration | Checkpointing, state management, interrupt semantics — ~6 months to replicate |
| PostgreSQL for checkpoints | Durability across restarts; enables horizontal scaling |
| Three memory systems | Episodic (temporal), Semantic (factual), Procedural (skills) — mirrors human cognition |
| Positional context assembly | Liu et al. (2023): transformer attention has U-shaped bias; primacy/recency zones attended reliably |
| Root-level core modules | Keeps cognitive logic at top level for visibility; package wrappers for import convenience |

---

## Resources

- **Build Specification**: `PROGRESS_TRACKER.md` (16 phases)
- **Architecture Graph**: `SYSTEM_RELATION_GRAPH.md` (Mermaid diagrams)
- **Deployment Config**: `DEPLOYMENT.conf` (systemd, Docker, Nginx)
- **Dashboard UI**: `dashboard/src/NovaDashboard.tsx`
- **Setup Script**: `setup.sh`
- **Detailed Docs**: `.agents/summary/index.md` (knowledge base index)
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Graphiti Docs**: https://github.com/getzep/graphiti
- **MCP Docs**: https://modelcontextprotocol.io/

---

*Last Updated: 2026-02-26*
