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
Vitest 3.2.4                  # Unit testing
Playwright 1.56.1             # E2E testing
ESLint 9.39.1                 # Linting
```

### Infrastructure Services

- **PostgreSQL** — Semantic memory, procedural memory, checkpoints, pgvector extension
- **Neo4j** — Episodic memory via Graphiti temporal knowledge graph
- **Redis** — Working memory, Celery broker, embedding cache
- **Langfuse** — Trace observability dashboard

---

## Project Structure

```
supernova/                      # Main Python package
├── __init__.py
├── config.py                   # Pydantic Settings configuration loader
├── pyproject.toml              # Python dependencies and tool configs
├── alembic.ini                 # Database migration configuration
├── README.md
│
├── alembic/                    # Database migrations
│   ├── env.py
│   └── versions/
│       └── 23aa65fd8071_initial_schema.py
│
├── api/                        # FastAPI application layer
│   ├── __init__.py
│   ├── auth.py                 # JWT authentication (create_access_token, verify_token, get_current_user)
│   ├── gateway.py              # FastAPI gateway (lifespan, health, auth, WS, memory, admin, CORS)
│   ├── main.py                 # Legacy FastAPI app factory
│   ├── websockets.py           # WebSocket broadcaster and event stream handler
│   └── routes/
│       ├── __init__.py
│       ├── agent.py            # Agent execution endpoints
│       ├── dashboard.py        # Dashboard API endpoints
│       └── mcp_routes.py       # MCP server and skills API endpoints
│
├── core/                       # Core agent logic
│   ├── __init__.py
│   ├── agent/
│   │   └── __init__.py
│   ├── memory/                 # Memory system implementations
│   │   ├── __init__.py
│   │   ├── episodic.py         # Graphiti/Neo4j episodic memory
│   │   ├── semantic.py         # PostgreSQL/pgvector semantic memory
│   │   └── working.py          # Redis working memory
│   └── reasoning/
│       └── __init__.py
│
├── infrastructure/             # Infrastructure adapters
│   ├── __init__.py
│   ├── llm/
│   │   └── __init__.py
│   ├── storage/                # Database connections
│   │   ├── __init__.py
│   │   ├── postgres.py         # PostgreSQL connection pool
│   │   └── redis.py            # Redis client
│   └── tools/                  # Tool implementations
│       ├── __init__.py
│       ├── builtin/            # Built-in tools
│       │   ├── __init__.py
│       │   ├── code_exec.py    # Code execution sandbox (Docker + subprocess fallback)
│       │   ├── file_ops.py     # File operations (path jail to ./workspace/)
│       │   └── web_search.py   # Web search (Tavily/SerpAPI)
│       └── registry.py         # Tool registry (capability-gated)
│
├── mcp/                        # Model Context Protocol integration
│   ├── __init__.py
│   ├── client/                 # MCP client implementation
│   │   ├── __init__.py
│   │   └── mcp_client.py
│   └── tools/                  # MCP tool bridge
│       ├── __init__.py
│       └── mcp_tool_bridge.py
│
├── skills/                     # Skill system
│   ├── __init__.py
│   └── loader.py
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures (db_pool, redis, mock_llm, embedder, registry, coordinator)
│   ├── test_agent_routes.py       # Agent message endpoint (new/existing session)
│   ├── test_auth.py
│   ├── test_builtin_tools.py
│   ├── test_context_assembly.py  # Primacy/middle/recency zone tests
│   ├── test_dashboard.py         # Dashboard helpers + snapshot/approval endpoints
│   ├── test_episodic.py
│   ├── test_gateway.py
│   ├── test_interrupts.py      # HITL approval flow, timeout, risk-level tests
│   ├── test_mcp_api.py
│   ├── test_mcp_client.py
│   ├── test_memory_retrieval.py  # Upsert/search round trip, forgetting curve, hybrid search, working memory
│   ├── test_registry.py
│   ├── test_routing.py         # Capability-vector routing, cost constraints, fleet summary
│   ├── test_semantic.py
│   ├── test_skills.py
│   ├── test_storage.py           # Redis client + Postgres pool CRUD methods
│   ├── test_websockets.py
│   └── test_workers.py
│
├── workers/                    # Celery background workers
│   ├── __init__.py
│   ├── celery_app.py           # Celery app (Redis broker, RedBeat, 5 beat schedules)
│   ├── consolidation.py        # Episodic→semantic transfer + skill crystallization
│   ├── heartbeat.py            # Redis/Postgres/Neo4j health checks + Langfuse trace
│   ├── maintenance.py          # Forgetting curves via asyncpg stored procedure
│   └── mcp_monitor.py          # MCP server health + auto-restart with exponential backoff

# Root-level specification files (load-bearing)
├── loop.py                     # Cognitive loop (LangGraph StateGraph)
├── context_assembly.py         # Positional context window assembly
├── procedural.py               # Compiled skill storage & crystallization
├── dynamic_router.py           # Capability-vector model router
├── interrupts.py               # HITL interrupt coordinator
├── DEPLOYMENT.conf             # Systemd services, Dockerfile, Nginx config
├── nova-dashboard.jsx          # React monitoring dashboard
├── setup.sh                    # Environment setup script
├── PROGRESS_TRACKER.md         # 16-phase build progress tracker
├── AGENTS.md                   # This file
├── .env.example                # Environment variable template
└── .env                        # Local environment configuration (gitignored)

# Dashboard (React frontend)
dashboard/
├── package.json
├── vite.config.js
├── playwright.config.js
├── eslint.config.js
├── index.html
├── src/
│   ├── App.jsx
│   ├── App.css
│   ├── main.jsx
│   ├── index.css
│   ├── NovaDashboard.jsx
│   ├── assets/
│   └── utils/
├── tests/
│   └── e2e/
├── public/
└── dist/

# MCP and Skills
mcp_and_skills/                 # MCP servers and skill definitions
├── MCP_INTEGRATION_SUMMARY.md
├── MCP_QUICK_REFERENCE.md
├── MCP_SERVERS.md
├── README-RESTORE.md
├── claude-config/              # Claude Desktop MCP configurations
├── copilot-config/             # GitHub Copilot MCP settings
├── custom-mcp-servers/         # Custom MCP servers
├── dot-mcp/
├── kimiconfig/
├── mcp-auth/
├── mcp-data/
├── mcp-servers/                # Pre-built MCP servers
├── skills/                     # Skill definitions
└── vscode-config/              # VS Code MCP settings

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

# Manual validation of environment
python3 --version    # Requires 3.12+
docker --version
docker compose version
psql --version

# Install uv (Astral's Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python Backend

```bash
# Navigate to supernova directory
cd supernova

# Install dependencies with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"

# Install GPU extras
pip install -e ".[gpu]"
```

### Database Migrations

```bash
# Navigate to supernova directory
cd supernova

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

### Running the Application

```bash
# Start the API server (from supernova/ directory)
uvicorn api.gateway:app --reload --log-level debug

# Or from project root with PYTHONPATH
PYTHONPATH=./supernova uvicorn supernova.api.gateway:app --reload

# Start Celery worker (terminal 2, from supernova/)
celery -A workers worker --loglevel=debug

# Start Celery Beat scheduler (terminal 3, from supernova/)
celery -A workers beat --loglevel=debug --scheduler=redbeat.RedBeatScheduler
```

### Dashboard (Frontend)

```bash
cd dashboard

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
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

# Run slow tests
pytest tests/ -v -m slow

# Parallel test execution
pytest tests/ -x --tb=short
```

### Frontend Tests

```bash
cd dashboard

# Run unit tests (Vitest)
npm run test:unit

# Run E2E tests (Playwright)
npm run test:e2e

# Run all tests
npm run test
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
# Linting
cd supernova
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

**Enabled Rules**:
- `E`, `W` - pycodestyle errors/warnings
- `F` - Pyflakes
- `I` - isort (import sorting)
- `N` - pep8-naming
- `D` - pydocstyle (Google convention)
- `UP` - pyupgrade
- `B` - flake8-bugbear
- `C4` - flake8-comprehensions
- `SIM` - flake8-simplify
- `ARG` - flake8-unused-arguments
- `PTH` - flake8-use-pathlib
- `ERA` - eradicate
- `PL` - Pylint
- `PERF` - Perflint
- `RUF` - Ruff-specific rules

### MyPy Type Checking

```bash
cd supernova
mypy . --ignore-missing-imports
```

Configuration:
- Strict mode enabled
- All functions must have type annotations
- No bare `Any` without justification comment

### JavaScript/React Standards

```bash
cd dashboard

# Linting
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
- `SUPERNOVA_SECRET_KEY` - Cryptographic key (generate: `openssl rand -hex 32`)
- `SUPERNOVA_ENV` - development/staging/production
- `DATABASE_URL` - PostgreSQL connection
- `NEO4J_URI` / `NEO4J_PASSWORD` - Neo4j connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` - LLM provider keys
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` - Observability
- `PICKLE_HMAC_KEY` - Secure deserialization key
- `API_KEY_ENCRYPTION_KEY` - API key encryption

See `.env.example` for complete documentation of all 70+ configuration options.

### Pydantic Settings

Configuration is loaded via `supernova/config.py` using Pydantic Settings:

```python
from supernova.config import get_settings

settings = get_settings()
print(settings.database_url)
print(settings.is_development)
```

---

## Security Considerations

### Capability-Based Tool Permissions

Tools declare required capabilities; execution validates at call time:

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

File operations are restricted to `./workspace/` — any path containing `..` is rejected.

### Risk Levels and HITL

| Risk Level | Examples                            | Timeout | Auto-resolve |
| ---------- | ----------------------------------- | ------- | ------------ |
| LOW        | web_search, file_read, memory_query | 30s     | Approve      |
| MEDIUM     | file_write, code_execute            | 120s    | Deny         |
| HIGH       | send_email, post_to_service         | 300s    | Deny         |
| CRITICAL   | make_payment, delete_database       | 600s    | Deny         |

### Secret Handling

- Never log API keys, JWT tokens, or database passwords
- Log only first 8 characters of any secret for debugging
- Environment variables loaded from `/etc/supernova/secrets.env` (systemd)
- Pickle deserialization only from trusted PostgreSQL

---

## Deployment Architecture

### Systemd Services

Defined in `DEPLOYMENT.conf`:

| Service                    | Purpose               | Resource Limits              |
| -------------------------- | --------------------- | ---------------------------- |
| `supernova-agent.service`  | Main FastAPI process  | MemoryMax=2G, CPUQuota=200%  |
| `supernova-worker.service` | Celery worker         | MemoryMax=1G, CPUQuota=100%  |
| `supernova-beat.service`   | Celery Beat scheduler | MemoryMax=256M, CPUQuota=25% |

**Deployment Commands**:
```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now supernova-agent supernova-worker supernova-beat

# Monitor
sudo journalctl -u supernova-agent -f
sudo systemctl status supernova-agent
```

### Docker Multi-Stage Build

- **Builder stage**: Full build environment (~1.2GB)
- **Production stage**: Minimal runtime image (~400-600MB)
- Base: `python:3.12-slim` (Debian Bookworm)

```bash
# Build image
docker build -f deploy/Dockerfile -t supernova:latest .

# Run container
docker run -p 8000:8000 --env-file .env supernova:latest
```

### Nginx Reverse Proxy

Features (from `DEPLOYMENT.conf`):
- TLS termination (Certbot/Let's Encrypt)
- WebSocket upgrade support (300s timeout for slow LLM responses)
- Rate limiting: 60 req/min general, 10 conn/min WebSocket
- Security headers (HSTS, CSP, X-Frame-Options)

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

### Episodic Memory (Neo4j + Graphiti)
- **Purpose**: Temporal reasoning — "what happened when?"
- **Store**: `core/memory/episodic.py`
- **Latency**: 20-80ms (ANN over temporal graph)

### Semantic Memory (PostgreSQL + pgvector)
- **Purpose**: Factual retrieval — "what do I know about X?"
- **Store**: `core/memory/semantic.py`
- **Latency**: 5-30ms (HNSW index)

### Working Memory (Redis)
- **Purpose**: Fast ephemeral storage, current context
- **Store**: `core/memory/working.py`
- **Latency**: <5ms (in-memory with AOF persistence)

### Procedural Memory (PostgreSQL)
- **Purpose**: Compiled skills — "how do I do Y?"
- **Store**: `procedural.py` (root level)
- Contains skill crystallization logic

---

## MCP Integration

The project includes comprehensive MCP (Model Context Protocol) infrastructure:

- **17 MCP servers** configured (see `mcp_and_skills/MCP_INTEGRATION_SUMMARY.md`)
- Custom servers: code-intelligence, execution-engine, version-control, quality-assurance
- Official servers: filesystem, memory, git, fetch, time
- Browser automation: playwright, chrome-devtools
- Documentation: context7

MCP client implementation: `supernova/mcp/client/mcp_client.py`

---

## API Endpoints

### Health Check
- `GET /healthz` - Liveness/readiness with backend checks

### Agent API
- Defined in `api/routes/agent.py`
- WebSocket streaming support

### Dashboard API
- Defined in `api/routes/dashboard.py`
- Metrics and monitoring endpoints

---

## Key Design Decisions

### Why LangGraph?
LangGraph provides checkpointing, state management, and interrupt semantics that would require ~6 months of engineering to replicate reliably.

### Why PostgreSQL for Checkpoints?
Durability guarantees across process restarts; enables horizontal scaling of stateless workers.

### Why Three Memory Systems?
- **Episodic** (Graphiti/Neo4j): Temporal reasoning — "what happened when?"
- **Semantic** (pgvector): Factual retrieval — "what do I know about X?"
- **Procedural** (PostgreSQL): Compiled skills — "how do I do Y?"

### Why Positional Context Assembly?
Liu et al. (2023) demonstrated that transformer attention has U-shaped bias: primacy and recency zones are attended reliably; middle degrades to ~40% recall.

---

## Resources

- **Build Specification**: `PROGRESS_TRACKER.md` (16 phases)
- **Deployment Config**: `DEPLOYMENT.conf` (systemd, Docker, Nginx)
- **Dashboard UI**: `dashboard/src/NovaDashboard.jsx`
- **Setup Script**: `setup.sh`
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Graphiti Docs**: https://github.com/getzep/graphiti
- **MCP Docs**: https://modelcontextprotocol.io/

---

*Last Updated: 2026-02-26*
