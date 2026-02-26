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

### Core Dependencies

```
langgraph>=0.2.0              # Stateful agent graph with checkpointing
langgraph-checkpoint-postgres>=0.1  # PostgreSQL checkpoint backend
litellm>=1.40.0               # Universal LLM proxy (100+ providers)
graphiti-core>=0.3.0          # Temporal knowledge graph (episodic memory)
asyncpg>=0.29.0               # Async PostgreSQL driver
redis[hiredis]>=5.0.0         # Working memory + Celery broker
fastapi>=0.111.0              # API layer
uvicorn[standard]>=0.29.0     # ASGI server with uvloop
celery[gevent]>=5.4.0         # Background task execution
redbeat>=2.2.0                # Redis-backed Celery Beat scheduler
langfuse>=2.0.0               # Observability and tracing
msgpack>=1.0.8                # Binary serialization for working memory
```

### Infrastructure Services

- **PostgreSQL** — Semantic memory, procedural memory, checkpoints
- **Neo4j** — Episodic memory via Graphiti temporal knowledge graph
- **Redis** — Working memory, Celery broker, embedding cache
- **Langfuse** — Trace observability dashboard

---

## Project Structure

```
supernova/
├── core/                       # Core agent cognition
│   ├── agent/
│   │   └── loop.py            # ← SPEC: Cognitive loop (LangGraph StateGraph)
│   ├── memory/
│   │   ├── working.py         # Redis-based working memory store
│   │   ├── episodic.py        # Graphiti wrapper for temporal memory
│   │   ├── semantic.py        # pgvector semantic memory store
│   │   └── procedural.py      # ← SPEC: Compiled skill storage & crystallization
│   └── reasoning/
│       └── context_assembly.py # ← SPEC: Positional context window assembly
├── infrastructure/             # External service integrations
│   ├── llm/
│   │   └── dynamic_router.py  # ← SPEC: Capability-vector model router
│   ├── storage/
│   │   ├── postgres.py        # Asyncpg pool wrapper
│   │   └── redis.py           # Aioredis client wrapper
│   └── tools/
│       ├── registry.py        # Capability-gated tool registry
│       ├── sandbox.py         # Docker sandboxed code execution
│       └── builtin/
│           ├── web_search.py  # Tavily/SerpAPI search
│           ├── file_ops.py    # Jailed file read/write
│           └── code_exec.py   # Sandboxed Python execution
├── api/                        # FastAPI application
│   ├── gateway.py             # Main FastAPI app entrypoint
│   ├── websockets.py          # Streaming WebSocket handler
│   ├── auth.py                # JWT verification
│   ├── interrupts.py          # ← SPEC: HITL interrupt coordinator
│   └── routes/
│       ├── sessions.py        # Session management endpoints
│       ├── memory.py          # Memory retrieval endpoints
│       └── admin.py           # Admin/fleet status endpoints
├── workers/                    # Celery background workers
│   ├── celery_app.py          # Celery + RedBeat configuration
│   ├── heartbeat.py           # Periodic agent cognition tasks
│   ├── consolidation.py       # Episodic→semantic memory consolidation
│   └── maintenance.py         # Forgetting curves + cleanup
├── deploy/                     # Deployment configurations
│   ├── docker-compose.yml     # Full infrastructure stack
│   ├── DEPLOYMENT.conf        # Systemd services, Dockerfile, Nginx config
│   └── postgres/
│       └── init.sql           # Initial schema
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── test_context_assembly.py
│   ├── test_memory_retrieval.py
│   ├── test_routing.py
│   └── test_interrupts.py
├── pyproject.toml             # Dependencies and tool configuration
└── nova-dashboard.jsx         # React monitoring dashboard (specification artifact)
```

---

## Specification Files (Read-Only)

The following files are **load-bearing specifications**. Copy them exactly as provided—do not refactor, restructure, or "improve" them:

| File                                   | Purpose                                                                      |
| -------------------------------------- | ---------------------------------------------------------------------------- |
| `core/reasoning/context_assembly.py`   | Positionally-aware context window assembly with Primacy/Middle/Recency zones |
| `core/memory/procedural.py`            | Procedural memory with SkillCrystallizationWorker                            |
| `core/agent/loop.py`                   | The cognitive loop (LangGraph StateGraph with checkpointing)                 |
| `infrastructure/llm/dynamic_router.py` | Capability-vector model routing with live pricing                            |
| `api/interrupts.py`                    | HITL interrupt coordinator with risk-stratified timeouts                     |
| `DEPLOYMENT.conf`                      | Systemd services, multi-stage Dockerfile, Nginx configuration                |

### Critical Constraint from loop.py

The `AgentState.messages` field **must** use `Annotated[list[dict], operator.add]`:

```python
class AgentState(TypedDict):
    messages: Annotated[list[dict], operator.add]  # CRITICAL: LangGraph appends, not replaces
```

If this annotation is missing, tool results will overwrite conversation history and the agent will have no memory within a session.

---

## Build and Run Commands

### Environment Setup

```bash
# Validate environment (Python 3.12+, Docker, PostgreSQL tools)
python3 --version
docker --version
docker compose version
psql --version

# Install dependencies
uv sync --all-extras
# or: pip install -e ".[dev]"
```

### Database Initialization

```bash
# Start infrastructure services
docker compose up -d postgres neo4j redis langfuse

# Wait for healthy status
docker compose ps

# Run migrations
alembic upgrade head
```

### Running the Application

```bash
# Start the API server
uvicorn api.gateway:app --reload --log-level debug

# Start Celery worker (terminal 2)
celery -A workers worker --loglevel=debug

# Start Celery Beat scheduler (terminal 3)
celery -A workers beat --loglevel=debug
```

### Testing

```bash
# Run full test suite with coverage
pytest tests/ -v --cov=core --cov=infrastructure --cov=api --cov-report=term-missing

# Target: ≥80% coverage
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy core/ infrastructure/ api/ --ignore-missing-imports
```

---

## Testing Strategy

### Test Coverage Requirements

| Test File                  | Coverage Target                                                           |
| -------------------------- | ------------------------------------------------------------------------- |
| `test_context_assembly.py` | Primacy zone, middle zone injection, recency prefix, truncation           |
| `test_routing.py`          | Planning routing, cost constraints, local-only bypass, relaxation cascade |
| `test_interrupts.py`       | Approval resolution, timeout policies, unknown thread handling            |
| `test_memory_retrieval.py` | Round-trip upsert/search, forgetting curves, hybrid search RRF            |

### Key Test Scenarios

1. **Context Assembly**: Verify primacy zone always includes system content at index 0
2. **Memory Retrieval**: Verify episodic, semantic, procedural, and working memory run in parallel (`asyncio.gather`)
3. **Routing**: Verify constraint relaxation fires in correct order (latency → cost → unconstrained)
4. **Interrupts**: Verify low-risk auto-approves on timeout, high-risk auto-denies

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

File operations are restricted to `./workspace/`—any path containing `..` is rejected.

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

---

## Deployment Architecture

### Systemd Services

| Service                    | Purpose               | Resource Limits              |
| -------------------------- | --------------------- | ---------------------------- |
| `supernova-agent.service`  | Main FastAPI process  | MemoryMax=2G, CPUQuota=200%  |
| `supernova-worker.service` | Celery worker         | MemoryMax=1G, CPUQuota=100%  |
| `supernova-beat.service`   | Celery Beat scheduler | MemoryMax=256M, CPUQuota=25% |

### Docker Multi-Stage Build

- **Builder stage**: Full build environment with compilers (~1.2GB)
- **Production stage**: Minimal runtime image (~400-600MB)
- Uses `python:3.12-slim` (Debian Bookworm) not Alpine (musl compatibility issues)

### Nginx Reverse Proxy

- TLS termination (Certbot/Let's Encrypt)
- WebSocket upgrade support (`proxy_read_timeout 300s` for slow LLM responses)
- Rate limiting: 60 req/min general, 10 conn/min WebSocket

---

## Code Style Guidelines

### Python Standards

- **Type annotations** required on all function signatures—no bare `Any` without comment
- **Docstrings** explaining _why_, not just _what_
- **Async error handling**—never let exceptions propagate from memory stores or tools
- **State serialization**—all LangGraph state must be JSON-serializable primitives only

### Ruff Configuration (pyproject.toml)

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "I", "UP", "B", "SIM"]
```

### MyPy Configuration

```toml
[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

---

## Performance Requirements

| Operation                       | Target Latency | Strategy                       |
| ------------------------------- | -------------- | ------------------------------ |
| Memory retrieval (all 4 stores) | ~80ms          | Parallel `asyncio.gather`      |
| Episodic (Graphiti)             | 20-80ms        | ANN over temporal graph        |
| Semantic (pgvector)             | 5-30ms         | HNSW index                     |
| Working memory (Redis)          | <5ms           | In-memory with AOF persistence |
| Context assembly                | <1ms           | CPU-bound string ops           |

### Critical Optimizations

1. **Compiled graph reuse** — LangGraph graph created once at startup, reused across all sessions
2. **Embedding cache** — Redis cache with `em:{sha256(text)[:16]}` keys, TTL=3600
3. **Msgpack serialization** — 3-5× smaller, 10× faster than JSON for working memory
4. **Parallel tool execution** — Read-only tools run concurrently; writes run sequentially

---

## Cognitive Loop Phases

The agent's cognitive cycle (implemented in `loop.py`):

```
PERCEIVE   → restore state from checkpoint, receive new input
REMEMBER   → parallel retrieval from episodic + semantic + procedural + working memory
PRIME      → check procedural memory for applicable compiled skill
ASSEMBLE   → build optimally-positioned context window
REASON     → LLM call with assembled context
ACT        → execute tool calls (with interrupt checkpoint)
REFLECT    → optional self-evaluation if quality criteria triggered
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

## Development Workflow

1. **Read the spec** — Before modifying any file, read the corresponding specification section in `SUPERNOVA_AGENT_PROMPT.md`
2. **Verify mental model** — Before running commands, verify your understanding of what they will do
3. **Check library APIs** — Use bash/read tools to check installed package documentation rather than hallucinating signatures
4. **Run tests** — All changes must pass `pytest tests/` with ≥80% coverage
5. **Quality gates** — `ruff check .` and `mypy` must pass before committing

---

## Key Design Decisions

### Why LangGraph over custom orchestration?

LangGraph provides checkpointing, state management, and interrupt semantics that would require ~6 months of engineering to replicate reliably.

### Why PostgreSQL for checkpoints?

Durability guarantees across process restarts; enables horizontal scaling of stateless workers.

### Why three memory systems?

- **Episodic** (Graphiti/Neo4j): Temporal reasoning — "what happened when?"
- **Semantic** (pgvector): Factual retrieval — "what do I know about X?"
- **Procedural** (PostgreSQL): Compiled skills — "how do I do Y?"

### Why positional context assembly?

Liu et al. (2023) demonstrated that transformer attention has U-shaped bias: primacy and recency zones are attended reliably; middle degrades to ~40% recall.

---

## Resources

- **Build Specification**: `SUPERNOVA_AGENT_PROMPT.md` (762 lines, 10 phases)
- **Deployment Config**: `DEPLOYMENT.conf` (systemd, Docker, Nginx)
- **Dashboard UI**: `nova-dashboard.jsx` (React component with real-time simulation)
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Graphiti Docs**: https://github.com/getzep/graphiti
