# Contributing to SuperNova

## Development Setup

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Node.js 18+ (for dashboard)
- [uv](https://astral.sh/uv) (recommended) or pip

### 1. Clone and Install

```bash
git clone <repository-url>
cd SuperNova

# Python backend
cd supernova
uv sync --all-extras    # or: pip install -e ".[dev]"

# Dashboard
cd ../dashboard
npm install
```

### 2. Start Infrastructure

```bash
docker compose up -d    # PostgreSQL, Redis, Neo4j, Langfuse
```

### 3. Run Migrations

```bash
cd supernova
alembic upgrade head
```

### 4. Configure Environment

```bash
cp .env.example .env
# Fill in required API keys (OPENAI_API_KEY, SUPERNOVA_SECRET_KEY)
```

### 5. Verify Setup

```bash
# Backend tests
cd supernova && pytest tests/ -v --cov=supernova

# Dashboard tests
cd dashboard && npm test

# Start API server
cd supernova && uvicorn api.gateway:app --reload
# Check: http://localhost:8000/healthz
```

---

## Code Style

### Python

- **Formatter/Linter**: Ruff
- **Type Checker**: MyPy (strict mode)
- **Line length**: 100 characters
- **Indent**: 4 spaces
- **Quotes**: Double quotes
- **Target**: Python 3.12+

```bash
cd supernova
ruff check .           # Lint
ruff check . --fix     # Auto-fix
ruff format .          # Format
mypy . --ignore-missing-imports  # Type check
```

**Ruff rules enabled**: E, W, F, I, N, D (Google convention), UP, B, C4, SIM, ARG, PTH, ERA, PL, PERF, RUF

**All functions must have type annotations.** Use `from __future__ import annotations` at the top of every file.

### TypeScript/React

```bash
cd dashboard
npm run lint           # ESLint
npm run type-check     # TypeScript strict
```

---

## Testing

### Python Backend

```bash
cd supernova

# All tests with coverage
pytest tests/ -v --cov=supernova --cov-report=term-missing

# Specific file
pytest tests/test_auth.py -v

# Unit tests only
pytest tests/ -v -m "not integration"

# Integration tests only
pytest tests/ -v -m integration
```

**Coverage requirements**: 80% minimum across all modules.

**Test markers**:
- `@pytest.mark.slow` — Long-running tests
- `@pytest.mark.integration` — Requires running infrastructure
- `@pytest.mark.unit` — Pure unit tests

**Shared fixtures** (in `conftest.py`): `db_pool`, `redis_client`, `mock_llm`, `embedder`, `registry`, `coordinator`

### Dashboard

```bash
cd dashboard
npm run test:unit     # Vitest unit tests
npm run test:e2e      # Playwright E2E tests
npm run test          # All tests
```

---

## Project Architecture

### Key Principle: Root-Level Core Modules

The cognitive core lives at the project root (`loop.py`, `context_assembly.py`, `procedural.py`, `dynamic_router.py`, `interrupts.py`). Files in `supernova/core/agent/` and `supernova/core/reasoning/` are thin re-export wrappers for import convenience.

**When modifying core logic, edit the root-level files.**

### Package Layout

| Package | Purpose |
|---------|---------|
| `supernova/api/` | FastAPI endpoints, auth, WebSocket |
| `supernova/core/memory/` | Memory store implementations |
| `supernova/core/backup/` | Backup & recovery |
| `supernova/infrastructure/` | Storage, tools, security, observability |
| `supernova/mcp/` | Model Context Protocol client |
| `supernova/skills/` | Skill loader |
| `supernova/workers/` | Celery background tasks |
| `supernova/tests/` | Test suite (27 files) |
| `dashboard/src/` | React 19 frontend |

---

## Adding New Features

### Adding a New API Endpoint

1. Create route in `supernova/api/routes/`
2. Mount router in `supernova/api/gateway.py`
3. Add tests in `supernova/tests/`
4. Update API table in `AGENTS.md`

### Adding a New Tool

1. Create tool function in `supernova/infrastructure/tools/builtin/`
2. Define `Capability` requirements and `RiskLevel`
3. Register in `gateway.py` lifespan
4. Add tests in `supernova/tests/test_builtin_tools.py`

### Adding a New Memory Type

1. Implement store class in `supernova/core/memory/`
2. Add retrieval to `memory_retrieval_node()` in `loop.py`
3. Add consolidation to `memory_consolidation_node()` in `loop.py`
4. Add tests

### Adding a New Worker Task

1. Create task in `supernova/workers/`
2. Register in `celery_app.py` autodiscover and beat_schedule
3. Add tests in `supernova/tests/test_workers.py`

### Adding a Dashboard Component

1. Create component in `dashboard/src/components/`
2. Export from category index file
3. Add TypeScript types to `dashboard/src/types/index.ts`
4. Wire into `NovaDashboard.tsx` or relevant parent

---

## Database Migrations

```bash
cd supernova

# Create new migration
alembic revision --autogenerate -m "description of change"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## Security Guidelines

- **Never commit** `.env`, API keys, or secrets
- **Path jail**: File operations restricted to `./workspace/`
- **HMAC verification**: All pickle deserialization uses signed payloads
- **Audit logging**: Use `@audit_log` decorator for sensitive operations
- **Log sanitization**: Only log first 8 characters of any secret

---

## Commit Convention

Use descriptive commit messages:
```
Phase N done                    # Major milestone
chore: description              # Maintenance
fix: description                # Bug fix
feat: description               # New feature
test: description               # Test additions
docs: description               # Documentation
```

---

## Resources

- [AGENTS.md](AGENTS.md) — Full project reference for AI assistants
- [DEPLOYMENT.conf](DEPLOYMENT.conf) — Production deployment guide
- [PROGRESS_TRACKER.md](PROGRESS_TRACKER.md) — Build phases and specifications
- [.agents/summary/index.md](.agents/summary/index.md) — Detailed documentation index
