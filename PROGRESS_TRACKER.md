# SuperNova Build Progress Tracker

> **Canonical Build Guide — Single Source of Truth**
>
> This document integrates: Core Specification | Senior Engineering Review | Skill/MCP Activations | Security & Operations Requirements
>
> **16 Phases:** -1 (Packaging) → 0 (Validation) → 1-10 (Core) → 11-15 (Security, Cost, Backup, UX, Observability)

---

> **RACKER RULES — DO NOT VIOLATE**
>
> 1. Never rewrite, remove, or restructure any part of this checklist.
> 2. On task completion: only change `[ ]` → `[x]` and replace `_pending_` with validation evidence.
> 3. Do not alter Validation lines, reorder tasks, or touch uncompleted tasks.
> 4. Failed tasks: leave `[ ]`, append `❌ FAIL:` notes under Proof line.
> 5. Implementation method changes: keep original, append `❌ FAIL:` then `✅ FIX:` with explanation.
> 6. These rules are permanent for all agents (human or AI).

---

## CRITICAL CONSTRAINTS — Check before every task

- [ ] **CC-1** `AgentState.messages` uses `Annotated[list[dict], operator.add]` — verified in loop.py
- [ ] **CC-2** All state is JSON-serializable — no Python objects in LangGraph state
- [ ] **CC-3** File tools jail to `./workspace/` — reject paths with `..`
- [ ] **CC-4** Tool capabilities validated at execution time, not just registration
- [ ] **CC-5** Memory retrieval uses `asyncio.gather()` — never sequential
- [ ] **CC-6** Compiled LangGraph graph created once at startup — never rebuild per request
- [ ] **CC-7** Embedding cache in Redis with `em:{sha256(text)[:16]}` keys, TTL=3600
- [ ] **CC-8** Working memory uses msgpack (not JSON) for serialization
- [ ] **CC-9** MCP tool calls timeout after 30 seconds — prevent hanging servers
- [ ] **CC-10** MCP server health checked before tool execution — failover to built-in tools
- [ ] **CC-11** Skill files are hot-reloadable — changes reflected without restart

### Security & Operations Constraints (Added per Senior Review)

- [ ] **CC-12** No pickle deserialization without cryptographic signatures — use cloudpickle + HMAC
- [ ] **CC-13** API keys encrypted at rest — never in plain text env vars only
- [ ] **CC-14** All privileged actions logged to audit_log table
- [ ] **CC-15** Daily automated backups enabled — verify backup integrity weekly
- [ ] **CC-16** Spending limits enforced — hard stop when budget exceeded
- [ ] **CC-17** Cost estimation before expensive LLM calls — user confirmation >$0.50
- [ ] **CC-18** Local model fallback available — Ollama integration functional
- [ ] **CC-19** Code execution in sandboxed environment — gVisor or strict Docker
- [ ] **CC-20** Structured JSON logging with correlation IDs — all requests traceable

---

## Quick Navigation

| Phase  | Focus                        | Priority                            |
| :----- | :--------------------------- | :---------------------------------- |
| **-1** | **Packaging & Distribution** | 🔴 Critical for non-technical users |
| 0      | Environment Validation       | Existing                            |
| 1-10   | Core Implementation          | Existing                            |
| 11     | Cost Management              | 🔴 Added per Senior Review          |
| 12     | Backup & Recovery            | 🔴 Added per Senior Review          |
| 13     | Security Hardening           | 🟡 Added per Senior Review          |
| 14     | Observability                | 🟡 Added per Senior Review          |
| 15     | User Experience              | 🟡 Added per Senior Review          |

---

## PHASE -1 — Packaging & Distribution (CRITICAL)

**Phase Objective:** Enable non-technical users to install and run SuperNova with one click.

**Estimated Duration:** 2-3 sessions  
**Completion Criteria:** Non-technical user can install and start SuperNova in under 5 minutes.

**Why this matters:** The existing plan assumes CLI proficiency (Python, Docker, env vars). This blocks 95% of potential users.

---

### Task -1.1: One-Line Installer Script

**🎯 Skill Activation:** `create-plan` — Installation flow design.  
**🎯 MCP Activation:** `execution-engine` — Test installer on multiple platforms.

**Context:** Primary installation method for non-technical users.

**Dependencies:** None

- [ ] **-1.1.1** Create `install.sh` for Linux/macOS
  - **Validation:** Detects OS/architecture; installs Docker if needed; downloads release; runs setup
  - **Proof:** _pending_

- [ ] **-1.1.2** Create `install.ps1` for Windows
  - **Validation:** PowerShell script with equivalent functionality
  - **Proof:** _pending_

- [ ] **-1.1.3** Add dependency checks with helpful messages
  - **Validation:** Checks Python, Docker; provides installation links if missing
  - **Proof:** _pending_

- [ ] **-1.1.4** Test on clean VMs (Ubuntu, macOS, Windows)
  - **Validation:** Fresh OS install → running SuperNova in < 10 minutes
  - **Proof:** _pending_

---

### Task -1.2: Desktop Application Bundle

**🎯 Skill Activation:** `frontend-design` — Desktop app wrapper.  
**🎯 Skill Activation:** `architecture-design` — Embedded runtime design.

**Context:** Ultimate ease-of-use: double-click to run, no terminal needed.

**Dependencies:** Task 2.1 (dependencies defined)

- [ ] **-1.2.1** Research Tauri vs Electron for wrapper
  - **Validation:** Document trade-offs; select approach
  - **Proof:** _pending_

- [ ] **-1.2.2** Create desktop app wrapper
  - **Validation:** Embeds Python runtime; bundles all dependencies; single executable
  - **Proof:** _pending_

- [ ] **-1.2.3** Implement auto-updater
  - **Validation:** Checks for updates; one-click install; rollback capability
  - **Proof:** _pending_

- [ ] **-1.2.4** Code signing for binaries
  - **Validation:** Signed for Windows (EV cert), macOS (notarization), Linux (GPG)
  - **Proof:** _pending_

---

### Task -1.3: Pre-built Distribution Images

**🎯 Skill Activation:** `ci-cd-devops` — Automated builds.  
**🎯 MCP Activation:** `execution-engine` — Test distributed images.

**Context:** Users shouldn't need to build from source.

**Dependencies:** Task -1.1 (installer)

- [ ] **-1.3.1** Set up Docker Hub automated builds
  - **Validation:** `docker pull supernova/agent:latest` works
  - **Proof:** _pending_

- [ ] **-1.3.2** Create GitHub Releases workflow
  - **Validation:** Tagged releases auto-build binaries; attach to release
  - **Proof:** _pending_

- [ ] **-1.3.3** Create Homebrew formula
  - **Validation:** `brew install supernova` works on macOS/Linux
  - **Proof:** _pending_

- [ ] **-1.3.4** Create AUR package (Arch Linux)
  - **Validation:** `yay -S supernova` works
  - **Proof:** _pending_

---

### Task -1.4: Demo Mode

**🎯 Skill Activation:** `architecture-design` — Mock service design.  
**🎯 MCP Activation:** `execution-engine` — Test demo functionality.

**Context:** Let users try SuperNova without API keys.

**Dependencies:** Task 6.3 (API gateway)

- [ ] **-1.4.1** Implement mock LLM responses
  - **Validation:** Works without API keys; realistic demo conversations
  - **Proof:** _pending_

- [ ] **-1.4.2** Create demo tutorial
  - **Validation:** Guided tour of features using mock data
  - **Proof:** _pending_

- [ ] **-1.4.3** Add "Upgrade to Real" CTA
  - **Validation:** Clear path to add API keys and use real models
  - **Proof:** _pending_

---

## PHASE 0 — Environment Validation

**Phase Objective:** Verify all prerequisites before any implementation. Do not proceed if any check fails.

**Estimated Duration:** 10 minutes
**Completion Criteria:** All environment checks pass; `.env` file exists and is configured.

---

### Task 0.1: Environment Prerequisites Check

**🎯 Skill Activation:** `debugging-root-cause-analysis` — If any validation fails, activate immediately for systematic troubleshooting.

**Context:** Per PHASE 0 of SUPERNOVA_AGENT_PROMPT.md — must validate Python 3.12+, Docker, PostgreSQL tools, and disk space before building.

**Dependencies:** None

- [ ] **0.1.1** Verify Python 3.12+ is installed
  - **Validation:** `python3 --version` outputs 3.12.x or higher
  - **Proof:** _pending_

- [ ] **0.1.2** Verify uv or pip is available
  - **Validation:** `which uv || which pip` returns path to package manager
  - **Proof:** _pending_

- [ ] **0.1.3** Verify Docker and Docker Compose are available
  - **Validation:** `docker --version` and `docker compose version` both return version strings
  - **Proof:** _pending_

- [ ] **0.1.4** Verify PostgreSQL client tools are available
  - **Validation:** `psql --version` returns version string
  - **Proof:** _pending_

- [ ] **0.1.5** Verify sufficient disk space (~3GB available)
  - **Validation:** `df -h .` shows at least 3GB free
  - **Proof:** _pending_

- [ ] **0.1.6** Create `.env` file from `.env.example`
  - **Validation:** `test -f .env` passes; file contains all required environment variables
  - **Proof:** _pending_

---

### Task 0.2: MCP Environment Validation

**🎯 MCP Activation:** `execution-engine` — Use for running version checks and installation validation commands.

**Context:** MCP servers require Node.js, npx, and specific environment variables. Per mcp_and_skills/README-RESTORE.md.

**Dependencies:** None

- [ ] **0.2.1** Verify Node.js 20+ is installed
  - **Validation:** `node --version` outputs v20.x.x or higher
  - **Proof:** _pending_

- [ ] **0.2.2** Verify npx is available
  - **Validation:** `which npx` returns path; `npx --version` works
  - **Proof:** _pending_

- [ ] **0.2.3** Verify MCP servers directory exists
  - **Validation:** `test -d mcp_and_skills/mcp-servers` passes
  - **Proof:** _pending_

- [ ] **0.2.4** Verify skills directory exists
  - **Validation:** `test -d mcp_and_skills/skills` passes; contains SKILL.md files
  - **Proof:** _pending_

- [ ] **0.2.5** Test MCP filesystem server availability
  - **Validation:** `npx -y @modelcontextprotocol/server-filesystem --version` or help command works
  - **Proof:** _pending_

- [ ] **0.2.6** Test MCP memory server availability
  - **Validation:** `npx -y @modelcontextprotocol/server-memory --version` or help command works
  - **Proof:** _pending_

---

## PHASE 1 — Project Scaffold

**Phase Objective:** Create exact directory structure per specification. All import paths depend on this layout.

**Estimated Duration:** 15 minutes
**Completion Criteria:** All directories and `__init__.py` files exist; Python can import from all packages.

---

### Task 1.1: Directory Structure Creation

**🎯 Skill Activation:** `create-plan` — Generate step-by-step directory creation plan before executing.
**🎯 MCP Activation:** `filesystem` — Use for all directory and file creation operations.

**Context:** Per PHASE 1 of SUPERNOVA_AGENT_PROMPT.md — exact structure required for import paths to work.

**Dependencies:** Task 0.1 (environment validated)

- [ ] **1.1.1** Create root directory `supernova/`
  - **Validation:** Directory exists; `ls supernova/` succeeds
  - **Proof:** _pending_

- [ ] **1.1.2** Create `supernova/core/` package structure
  - **Validation:** `supernova/core/__init__.py`, `supernova/core/agent/__init__.py`, `supernova/core/memory/__init__.py`, `supernova/core/reasoning/__init__.py` all exist
  - **Proof:** _pending_

- [ ] **1.1.3** Create `supernova/infrastructure/` package structure
  - **Validation:** `supernova/infrastructure/__init__.py`, `supernova/infrastructure/llm/__init__.py`, `supernova/infrastructure/storage/__init__.py`, `supernova/infrastructure/tools/__init__.py`, `supernova/infrastructure/tools/builtin/__init__.py` all exist
  - **Proof:** _pending_

- [ ] **1.1.4** Create `supernova/api/` package structure
  - **Validation:** `supernova/api/__init__.py`, `supernova/api/routes/__init__.py` exist
  - **Proof:** _pending_

- [ ] **1.1.5** Create `supernova/workers/` package structure
  - **Validation:** `supernova/workers/__init__.py` exists
  - **Proof:** _pending_

- [ ] **1.1.6** Create `supernova/deploy/` and `supernova/deploy/postgres/` directories
  - **Validation:** Directories exist; will hold docker-compose.yml and init.sql
  - **Proof:** _pending_

- [ ] **1.1.7** Create `supernova/tests/` package structure
  - **Validation:** `supernova/tests/__init__.py` exists
  - **Proof:** _pending_

- [ ] **1.1.8** Create `supernova/alembic/` and `supernova/alembic/versions/` directories
  - **Validation:** Directories exist; will hold migration files
  - **Proof:** _pending_

- [ ] **1.1.9** Create `supernova/mcp/` package structure
  - **Validation:** `supernova/mcp/__init__.py`, `supernova/mcp/client/__init__.py`, `supernova/mcp/tools/__init__.py` exist
  - **Proof:** _pending_

- [ ] **1.1.10** Create `supernova/skills/` directory for skill definitions
  - **Validation:** Directory exists; will hold skill loader
  - **Proof:** _pending_

---

### Task 1.2: Specification Files Copy

**🎯 MCP Activation:** `filesystem` — Use read_file to verify source specs, write_file to copy to destination.
**🎯 Skill Activation:** `hostile-auditor` — Verify all files copied correctly and AST-parse before proceeding.

**Context:** Per PHASE 5 of SUPERNOVA_AGENT_PROMPT.md — these files are load-bearing specifications. Copy verbatim, do not modify.

**Dependencies:** Task 1.1 (directory structure created)

- [ ] **1.2.1** Copy `core/agent/loop.py` specification
  - **Validation:** File exists at `supernova/core/agent/loop.py`; `python -c "import ast; ast.parse(open('supernova/core/agent/loop.py').read())"` passes
  - **Proof:** Implemented in root `loop.py`; modularization to `supernova/core/agent/loop.py` pending.

- [ ] **1.2.2** Copy `core/memory/procedural.py` specification
  - **Validation:** File exists at `supernova/core/memory/procedural.py`; AST parse passes
  - **Proof:** Implemented in root `procedural.py`; modularization to `supernova/core/memory/procedural.py` pending.

- [ ] **1.2.3** Copy `core/reasoning/context_assembly.py` specification
  - **Validation:** File exists at `supernova/core/reasoning/context_assembly.py`; AST parse passes
  - **Proof:** Implemented in root `context_assembly.py`; modularization to `supernova/core/reasoning/context_assembly.py` pending.

- [ ] **1.2.4** Copy `infrastructure/llm/dynamic_router.py` specification
  - **Validation:** File exists at `supernova/infrastructure/llm/dynamic_router.py`; AST parse passes
  - **Proof:** Implemented in root `dynamic_router.py`; modularization to `supernova/infrastructure/llm/dynamic_router.py` pending.

- [ ] **1.2.5** Copy `api/interrupts.py` specification
  - **Validation:** File exists at `supernova/api/interrupts.py`; AST parse passes
  - **Proof:** Implemented in root `interrupts.py`; modularization to `supernova/api/interrupts.py` pending.

- [ ] **1.2.6** Copy `deploy/docker-compose.yml` specification
  - **Validation:** File exists at `supernova/deploy/docker-compose.yml`; `docker compose -f supernova/deploy/docker-compose.yml config` parses
  - **Proof:** _pending_

- [ ] **1.2.7** Extract and create `deploy/postgres/init.sql` from DEPLOYMENT.conf
  - **Validation:** File exists at `supernova/deploy/postgres/init.sql`; contains pgvector extension and checkpoint schema
  - **Proof:** _pending_

---

## PHASE 2 — Dependency Specification

**Phase Objective:** Create `pyproject.toml` with exact dependencies and tool configurations.

**Estimated Duration:** 15 minutes
**Completion Criteria:** `pip install -e ".[dev]"` succeeds; all imports resolve.

---

### Task 2.1: pyproject.toml Creation

**🎯 Skill Activation:** `architecture-design` — Validate dependency choices align with system requirements.
**🎯 MCP Activation:** `quality-assurance` — Type-check dependencies for compatibility after installation.

**Context:** Per PHASE 2 of SUPERNOVA_AGENT_PROMPT.md — exact dependencies with version pins. No additions without explicit reason.

**Dependencies:** Task 1.1 (directory structure created)

- [ ] **2.1.1** Create `pyproject.toml` with build-system requirements
  - **Validation:** File contains `[build-system]` with `hatchling`; `[project]` with name="supernova", version="2.0.0", requires-python=">=3.12"
  - **Proof:** _pending_

- [ ] **2.1.2** Add core agent orchestration dependencies
  - **Validation:** `langgraph>=0.2.0`, `langgraph-checkpoint-postgres>=0.1` listed
  - **Proof:** _pending_

- [ ] **2.1.3** Add LLM routing dependencies
  - **Validation:** `litellm>=1.40.0` listed
  - **Proof:** _pending_

- [ ] **2.1.4** Add memory systems dependencies
  - **Validation:** `graphiti-core>=0.3.0`, `asyncpg>=0.29.0`, `sqlalchemy[asyncio]>=2.0.0`, `redis[hiredis]>=5.0.0` listed
  - **Proof:** _pending_

- [ ] **2.1.5** Add API layer dependencies
  - **Validation:** `fastapi>=0.111.0`, `uvicorn[standard]>=0.29.0`, `websockets>=12.0`, `python-jose[cryptography]>=3.3.0`, `pydantic>=2.7.0`, `pydantic-settings>=2.2.0` listed
  - **Proof:** _pending_

- [ ] **2.1.6** Add background task dependencies
  - **Validation:** `celery[gevent]>=5.4.0`, `redbeat>=2.2.0` listed
  - **Proof:** _pending_

- [ ] **2.1.7** Add observability and serialization dependencies
  - **Validation:** `langfuse>=2.0.0`, `msgpack>=1.0.8`, `httpx>=0.27.0`, `orjson>=3.10.0` listed
  - **Proof:** _pending_

- [ ] **2.1.8** Add embedding dependencies
  - **Validation:** `openai>=1.30.0`, `tiktoken>=0.7.0` listed
  - **Proof:** _pending_

- [ ] **2.1.9** Add dev dependencies
  - **Validation:** `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, `pytest-cov>=5.0.0`, `ruff>=0.4.0`, `mypy>=1.10.0`, `alembic>=1.13.0` listed
  - **Proof:** _pending_

- [ ] **2.1.10** Add tool configurations (ruff, mypy, pytest)
  - **Validation:** `[tool.ruff]` with target-version="py312", line-length=100; `[tool.mypy]` with strict=true; `[tool.pytest.ini_options]` with asyncio_mode="auto"
  - **Proof:** _pending_

- [ ] **2.1.11** Add MCP client dependency
  - **Validation:** `mcp>=1.0.0` or `mcp-python-sdk` listed in dependencies
  - **Proof:** _pending_

- [ ] **2.1.12** Verify installation succeeds
  - **Validation:** `pip install -e "supernova/[dev]"` completes without errors
  - **Proof:** _pending_

---

## PHASE 3 — Environment Configuration

**Phase Objective:** Create `.env.example` with all required environment variables.

**Estimated Duration:** 10 minutes
**Completion Criteria:** `.env.example` created; can be copied to `.env` and filled in.

---

### Task 3.1: Environment File Creation

**Context:** Per PHASE 3 of SUPERNOVA_AGENT_PROMPT.md — exact structure required for configuration.

**Dependencies:** Task 1.1 (directory structure created)

- [ ] **3.1.1** Create `.env.example` with LLM provider keys section
  - **Validation:** Contains `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` placeholders
  - **Proof:** _pending_

- [ ] **3.1.2** Add database connection section
  - **Validation:** Contains `DATABASE_URL`, `POSTGRES_PASSWORD`, `REDIS_URL`
  - **Proof:** _pending_

- [ ] **3.1.3** Add Neo4j configuration
  - **Validation:** Contains `NEO4J_URI`, `NEO4J_PASSWORD`
  - **Proof:** _pending_

- [ ] **3.1.4** Add Langfuse configuration
  - **Validation:** Contains `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_HOST`, `LANGFUSE_DB_PASSWORD`, `LANGFUSE_NEXTAUTH_SECRET`, `LANGFUSE_SALT`
  - **Proof:** _pending_

- [ ] **3.1.5** Add agent configuration
  - **Validation:** Contains `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ENVIRONMENT`, `LOG_LEVEL`
  - **Proof:** _pending_

- [ ] **3.1.6** Add agent identity configuration
  - **Validation:** Contains `AGENT_NAME`, `AGENT_IDENTITY`
  - **Proof:** _pending_

- [ ] **3.1.7** Add MCP configuration section
  - **Validation:** Contains `MCP_SERVERS_CONFIG_PATH`, `MCP_DEFAULT_TIMEOUT`, `MCP_ENABLE_SKILLS`
  - **Proof:** _pending_

- [ ] **3.1.8** Add MCP server-specific environment variables
  - **Validation:** Contains optional paths for custom MCP servers: `MCP_CODE_INTELLIGENCE_PATH`, `MCP_EXECUTION_ENGINE_PATH`, `MCP_QUALITY_ASSURANCE_PATH`, etc.
  - **Proof:** _pending_

---

## PHASE 4 — Database Schema

**Phase Objective:** Create initial Alembic migration with exact SQL schema.

**Estimated Duration:** 30 minutes
**Completion Criteria:** `alembic upgrade head` runs without error; all tables and indexes created.

---

### Task 4.1: Alembic Setup

**Context:** Database migrations manage schema evolution. Must be set up before infrastructure layer.

**Dependencies:** Task 2.1 (dependencies installed), Task 1.2.7 (specification files copied)

- [ ] **4.1.1** Initialize Alembic
  - **Validation:** `alembic init alembic` creates `alembic.ini` and `alembic/` directory with `env.py`, `script.py.mako`
  - **Proof:** _pending_

- [ ] **4.1.2** Configure Alembic for async PostgreSQL
  - **Validation:** `alembic.ini` has `sqlalchemy.url` from environment; `env.py` uses `asyncpg`
  - **Proof:** _pending_

---

### Task 4.2: Initial Migration (001_initial_schema.py)

**🎯 Skill Activation:** `database-design-optimization` — Validate schema design, index choices, and HNSW configuration.
**🎯 MCP Activation:** `execution-engine` — Run migrations and verify with SQL queries.

**Context:** Per PHASE 4 of SUPERNOVA_AGENT_PROMPT.md — exact SQL schema required.

**Dependencies:** Task 4.1 (Alembic initialized)

- [ ] **4.2.1** Create migration with pgvector and pg_trgm extensions
  - **Validation:** `CREATE EXTENSION IF NOT EXISTS vector` and `pg_trgm` in upgrade
  - **Proof:** _pending_

- [ ] **4.2.2** Create `semantic_memories` table with vector(1536) column
  - **Validation:** Table has id, user_id, content, embedding, category, confidence, importance, tags, source, timestamps; embedding is vector(1536)
  - **Proof:** _pending_

- [ ] **4.2.3** Create HNSW index on semantic_memories.embedding
  - **Validation:** `CREATE INDEX ... USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`
  - **Proof:** _pending_

- [ ] **4.2.4** Create additional indexes on semantic_memories
  - **Validation:** FTS index with `to_tsvector`, user_id index, importance index, last_accessed index all created
  - **Proof:** _pending_

- [ ] **4.2.5** Create `procedural_memories` table
  - **Validation:** Table has id, name, description, trigger_conditions (JSONB), compiled_graph_bytes (BYTEA), trigger_embedding (vector), invocation_count, avg_performance_score, timestamps
  - **Proof:** _pending_

- [ ] **4.2.6** Create HNSW index on procedural_memories.trigger_embedding
  - **Validation:** `CREATE INDEX ... USING hnsw (trigger_embedding vector_cosine_ops)`
  - **Proof:** _pending_

- [ ] **4.2.7** Create `tool_execution_log` table
  - **Validation:** Table has id, session_id, user_id, tool_name, tool_args, result, success, latency_ms, error_message, risk_level, hitl_approved, executed_at
  - **Proof:** _pending_

- [ ] **4.2.8** Create indexes on tool_execution_log
  - **Validation:** Indexes on session_id, tool_name, executed_at
  - **Proof:** _pending_

- [ ] **4.2.9** Create `hybrid_memory_search` SQL function
  - **Validation:** Function accepts user_id, query_embedding, query_text, limit, category, min_importance; returns RRF-ranked results
  - **Proof:** _pending_

- [ ] **4.2.10** Create `run_forgetting_curves` stored procedure
  - **Validation:** Procedure updates importance (decay by 0.85), deletes low-importance old memories
  - **Proof:** _pending_

- [ ] **4.2.11** Run migration and verify
  - **Validation:** `alembic upgrade head` succeeds; `psql -c "\\dt"` shows all tables
  - **Proof:** _pending_

---

## PHASE 5 — Infrastructure Layer (BUILD THESE)

**Phase Objective:** Implement storage layer, memory stores, and tool registry.

**Estimated Duration:** 3-4 sessions
**Completion Criteria:** All infrastructure files exist and pass type checking; memory stores integrate.

---

### Task 5.1: Storage Layer (postgres.py, redis.py)

**🎯 Skill Activation:** `database-design-optimization` — Connection pool sizing, async patterns.
**🎯 Skill Activation:** `performance-engineering` — Pool configuration, timeout settings.
**🎯 MCP Activation:** `execution-engine` — Test database connections, verify pool behavior.

**Context:** Per PHASE 6A, 6B of SUPERNOVA_AGENT_PROMPT.md — connection pool wrappers.

**Dependencies:** Task 4.2 (database schema migrated), Task 2.1 (dependencies installed)

- [ ] **5.1.1** Create `infrastructure/storage/postgres.py`
  - **Validation:** `AsyncPostgresPool` class with `get_pool()`, `execute()`, `fetch()`, `fetchrow()`, `fetchval()`; min=5, max=20, command_timeout=60; `SET timezone='UTC'` on connect; lifespan `connect()`/`disconnect()` methods
  - **Proof:** _pending_

- [ ] **5.1.2** Create `infrastructure/storage/redis.py`
  - **Validation:** `AsyncRedisClient` class with `get_client()`; `working_memory_get()`, `working_memory_set()`, `working_memory_delete()`; key prefix `wm:{session_id}`; TTL=86400; msgpack serialization
  - **Proof:** _pending_

- [ ] **5.1.3** Verify type checking passes
  - **Validation:** `mypy supernova/infrastructure/storage/ --ignore-missing-imports` passes
  - **Proof:** _pending_

---

### Task 5.2: Working Memory Store

**🎯 Skill Activation:** `performance-engineering` — Serialization optimization (msgpack vs JSON).
**🎯 Skill Activation:** `context-management` — Cache strategies, TTL optimization.
**🎯 MCP Activation:** `code-intelligence` — Static analysis for serialization patterns.

**Context:** Per PHASE 6C of SUPERNOVA_AGENT_PROMPT.md — msgpack-serialized working memory.

**Dependencies:** Task 5.1.2 (Redis client)

- [ ] **5.2.1** Create `core/memory/working.py` with `WorkingMemory` dataclass
  - **Validation:** Dataclass has fields: session_id, current_goal, active_plan, tool_results_buffer, attention_stack, scratchpad, last_updated
  - **Proof:** _pending_

- [ ] **5.2.2** Implement `WorkingMemoryStore.get()`
  - **Validation:** Returns `WorkingMemory | None`; deserializes msgpack
  - **Proof:** _pending_

- [ ] **5.2.3** Implement `WorkingMemoryStore.set()`
  - **Validation:** Serializes to msgpack; stores with TTL; returns None
  - **Proof:** _pending_

- [ ] **5.2.4** Implement `WorkingMemoryStore.update_field()` for atomic partial updates
  - **Validation:** Updates single field without rewriting entire object
  - **Proof:** _pending_

---

### Task 5.3: Episodic Memory Store

**🎯 Skill Activation:** `agent-cognitive-architecture` — Temporal knowledge design, episode modeling.
**🎯 Skill Activation:** `database-design-optimization` — Graph queries, Neo4j optimization.
**🎯 MCP Activation:** `code-intelligence` — Analyze Graphiti integration patterns.

**Context:** Per PHASE 6D of SUPERNOVA_AGENT_PROMPT.md — Graphiti wrapper for temporal knowledge.

**Dependencies:** Task 5.1.1 (PostgreSQL pool), Task 1.2.1 (Graphiti dependency)

- [ ] **5.3.1** Create `core/memory/episodic.py` with `EpisodicMemoryStore` class
  - **Validation:** Class wraps `graphiti_core.Graphiti`; constructor takes neo4j_uri, neo4j_password, llm_client, embedder
  - **Proof:** _pending_

- [ ] **5.3.2** Implement `record_episode()`
  - **Validation:** Writes content + metadata to Graphiti; handles exceptions without raising
  - **Proof:** _pending_

- [ ] **5.3.3** Implement `recall()` with embedding-based retrieval
  - **Validation:** Returns list[dict] with keys: fact, valid_from, valid_until, score; limit parameter works
  - **Proof:** _pending_

- [ ] **5.3.4** Implement `get_recent()` for consolidation
  - **Validation:** Fetches raw episodes from last N hours; returns list[dict]
  - **Proof:** _pending_

- [ ] **5.3.5** Add error handling (never raise to caller)
  - **Validation:** All methods catch exceptions, log them, return empty result or None
  - **Proof:** _pending_

---

### Task 5.4: Semantic Memory Store

**🎯 Skill Activation:** `database-design-optimization` — Vector indexing (HNSW), hybrid search RRF.
**🎯 Skill Activation:** `performance-engineering` — Embedding caching, query optimization.
**🎯 MCP Activation:** `knowledge-integration` — Validate web search integration for embeddings.

**Context:** Per PHASE 6E of SUPERNOVA_AGENT_PROMPT.md — pgvector with hybrid search.

**Dependencies:** Task 5.1.1 (PostgreSQL pool), Task 4.2 (schema with hybrid function)

- [ ] **5.4.1** Create `core/memory/semantic.py` with `SemanticMemoryStore` class
  - **Validation:** Class initialized with Postgres pool + embedder client
  - **Proof:** _pending_

- [ ] **5.4.2** Implement `embed()` with Redis caching
  - **Validation:** Calls text-embedding-3-small via LiteLLM; caches in Redis with `em:{sha256(text)[:16]}` key; TTL=3600
  - **Proof:** _pending_

- [ ] **5.4.3** Implement `search()` using hybrid SQL function
  - **Validation:** Calls `hybrid_memory_search()`; returns list[dict]; category filter works
  - **Proof:** _pending_

- [ ] **5.4.4** Implement `upsert()` with content hash deduplication
  - **Validation:** Inserts or updates by content hash; returns UUID
  - **Proof:** _pending_

- [ ] **5.4.5** Implement `update_access_time()`
  - **Validation:** Updates `last_accessed` timestamp for memory_id
  - **Proof:** _pending_

- [ ] **5.4.6** Implement `get_by_category()`
  - **Validation:** Returns all memories for user_id + category
  - **Proof:** _pending_

---

### Task 5.5: Tool Registry

**🎯 Skill Activation:** `security-engineering` — Capability model design, permission boundaries.
**🎯 Skill Activation:** `api-integration` — Tool schema design, OpenAI compatibility.
**🎯 Skill Activation:** `code-review-refactoring` — Review capability validation logic.
**🎯 MCP Activation:** `quality-assurance` — Security scan the registry implementation.

**Context:** Per PHASE 6F of SUPERNOVA_AGENT_PROMPT.md — capability-gated tool system.

**Dependencies:** Task 5.1.1 (PostgreSQL for audit log), Task 2.1 (dependencies)

- [ ] **5.5.1** Create `infrastructure/tools/registry.py` with `Capability` Flag enum
  - **Validation:** READ_FILES, WRITE_FILES, EXECUTE_CODE, WEB_SEARCH, WEB_BROWSE, SEND_EMAIL, SHELL_ACCESS, EXTERNAL_API flags defined
  - **Proof:** _pending_

- [ ] **5.5.2** Create `ToolRegistry` class
  - **Validation:** Initialized with `granted_capabilities: Capability`
  - **Proof:** _pending_

- [ ] **5.5.3** Implement `register()` with capability validation
  - **Validation:** Validates tool's `required_capabilities` subset of granted; raises `PermissionError` if not
  - **Proof:** _pending_

- [ ] **5.5.4** Implement `execute()` with runtime capability check
  - **Validation:** Re-validates capabilities at execution; 30-second timeout via `asyncio.wait_for`; writes to `tool_execution_log`
  - **Proof:** _pending_

- [ ] **5.5.5** Implement `get_tool_schemas()` for LLM function calling
  - **Validation:** Returns OpenAI-format schemas only for tools user can execute
  - **Proof:** _pending_

- [ ] **5.5.6** Implement `get_tool()` for direct access
  - **Validation:** Returns Tool | None by name
  - **Proof:** _pending_

---

### Task 5.6: Built-in Tools

**Context:** Per PHASE 6G, 6H, 6I of SUPERNOVA_AGENT_PROMPT.md — web search, file ops, code execution.

**Dependencies:** Task 5.5 (ToolRegistry)

- [ ] **5.6.1** Create `infrastructure/tools/builtin/web_search.py`
  - **Validation:** `WebSearchTool` with name="web_search", required_capabilities=WEB_SEARCH, is_safe_parallel=True; uses TAVILY_API_KEY or SERPAPI_KEY; returns OpenAI schema
  - **Proof:** _pending_

- [ ] **5.6.2** Create `infrastructure/tools/builtin/file_ops.py`
  - **Validation:** `FileReadTool` and `FileWriteTool`; path jail to `./workspace/`; rejects `..` traversal; READ_FILES and WRITE_FILES capabilities
  - **Proof:** _pending_

- [ ] **5.6.3** Create `infrastructure/tools/builtin/code_exec.py`
  - **Validation:** `CodeExecutionTool`; Docker sandbox with `python:3.12-slim`, network_disabled=True, mem_limit="128m", cpu_quota=50000; fallback to subprocess with resource limits
  - **Proof:** _pending_

---

### Task 5.7: MCP Client Infrastructure

**🎯 Skill Activation:** `mcp-builder` — MCP protocol implementation, server lifecycle management.
**🎯 Skill Activation:** `multi-agent-orchestration` — Server management, health monitoring patterns.
**🎯 Skill Activation:** `api-integration` — Tool bridging, error translation.
**🎯 MCP Activation:** `code-intelligence` — Analyze MCP SDK usage patterns.
**🎯 MCP Activation:** `execution-engine` — Test MCP server connections.

**Context:** MCP (Model Context Protocol) integration allows SuperNova to use external MCP servers. Per mcp_and_skills/MCP_INTEGRATION_SUMMARY.md.

**Dependencies:** Task 2.1.11 (MCP dependency), Task 0.2 (MCP environment validated)

- [ ] **5.7.1** Create `mcp/client/mcp_client.py` with `MCPClient` class
  - **Validation:** Class manages MCP server connections via stdio; handles server lifecycle (start, ping, stop)
  - **Proof:** _pending_

- [ ] **5.7.2** Implement server configuration loading
  - **Validation:** Loads MCP servers from `mcp_and_skills/` directory; parses server definitions (command, args, env)
  - **Proof:** _pending_

- [ ] **5.7.3** Implement `list_tools()` for MCP server discovery
  - **Validation:** Queries connected MCP servers; aggregates tool schemas; returns OpenAI-compatible format
  - **Proof:** _pending_

- [ ] **5.7.4** Implement `call_tool()` for MCP tool execution
  - **Validation:** Routes tool calls to appropriate MCP server; 30-second timeout; returns result or error
  - **Proof:** _pending_

- [ ] **5.7.5** Implement MCP server health checking
  - **Validation:** Periodic health checks; marks unhealthy servers; failover to built-in tools
  - **Proof:** _pending_

- [ ] **5.7.6** Create `mcp/tools/mcp_tool_bridge.py`
  - **Validation:** Bridges MCP tools to SuperNova's ToolRegistry; capability mapping; error translation
  - **Proof:** _pending_

---

### Task 5.8: Skills Integration

**🎯 Skill Activation:** `context-management` — Skill injection design, prompt engineering.
**🎯 Skill Activation:** `performance-engineering` — Hot-reload implementation, file watching.
**🎯 MCP Activation:** `filesystem` — Watch skill files for changes.
**🎯 MCP Activation:** `knowledge-integration` — Parse SKILL.md content.

**Context:** Skills provide specialized knowledge and workflows. Per mcp_and_skills/skills/ directory.

**Dependencies:** Task 1.1.10 (skills directory)

- [ ] **5.8.1** Create `skills/loader.py` with `SkillLoader` class
  - **Validation:** Discovers skills from `mcp_and_skills/skills/`; parses SKILL.md files; extracts metadata
  - **Proof:** _pending_

- [ ] **5.8.2** Implement skill hot-reloading
  - **Validation:** Watches skill files for changes; reloads without restart; debounced (500ms)
  - **Proof:** _pending_

- [ ] **5.8.3** Create skill-to-prompt converter
  - **Validation:** Converts SKILL.md content to system prompt additions; injects into context assembly
  - **Proof:** _pending_

- [ ] **5.8.4** Implement skill registry
  - **Validation:** Maps skill names to content; lists available skills; activates/deactivates per session
  - **Proof:** _pending_

- [ ] **5.8.5** Test with mcp-builder skill
  - **Validation:** Loads `mcp_and_skills/skills/mcp-builder/SKILL.md`; content injectable into prompts
  - **Proof:** _pending_

---

## PHASE 6 — API Layer

**Phase Objective:** Implement FastAPI gateway, WebSocket handler, and authentication.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** API starts; WebSocket streams; JWT auth works.

---

### Task 6.1: Authentication

**🎯 Skill Activation:** `security-engineering` — JWT implementation, token validation.
**🎯 Skill Activation:** `api-integration` — FastAPI dependency patterns.
**🎯 MCP Activation:** `quality-assurance` — Security scan auth implementation.

**Context:** Per PHASE 7A of SUPERNOVA_AGENT_PROMPT.md — JWT handling.

**Dependencies:** Task 3.1 (environment with JWT_SECRET_KEY)

- [ ] **6.1.1** Create `api/auth.py` with `create_access_token()`
  - **Validation:** Returns JWT string; accepts user_id and expires_delta_hours (default 24)
  - **Proof:** _pending_

- [ ] **6.1.2** Implement `verify_token()`
  - **Validation:** Returns user_id from token; raises HTTPException(401) on invalid
  - **Proof:** _pending_

- [ ] **6.1.3** Implement `get_current_user()` FastAPI dependency
  - **Validation:** Extracts token from HTTPBearer; returns user_id
  - **Proof:** _pending_

---

### Task 6.2: WebSocket Handler

**🎯 Skill Activation:** `api-integration` — Streaming protocol design, event mapping.
**🎯 Skill Activation:** `performance-engineering` — Connection management, memory leak prevention.
**🎯 MCP Activation:** `execution-engine` — Load test WebSocket connections.

**Context:** Per PHASE 7B of SUPERNOVA_AGENT_PROMPT.md — streaming agent events.

**Dependencies:** Task 6.1 (auth), Task 1.2 (specification files), Task 5.x (memory and tools)

- [ ] **6.2.1** Create `api/websockets.py` with `WebSocketBroadcaster` class
  - **Validation:** Has `send(thread_id: str, data: dict)` method; connection registry dict
  - **Proof:** _pending_

- [ ] **6.2.2** Implement `handle_agent_stream()` coroutine
  - **Validation:** Accepts connection; registers in broadcaster; receives JSON; runs `agent_graph.astream_events()`
  - **Proof:** _pending_

- [ ] **6.2.3** Implement event type mapping
  - **Validation:** on_chat_model_stream → {type: token}; on_tool_start → {type: tool_start}; on_tool_end → {type: tool_result}; on_chain_end → {type: done}; GraphInterrupt → {type: approval_request}
  - **Proof:** _pending_

- [ ] **6.2.4** Implement disconnect handling
  - **Validation:** Unregisters from broadcaster on disconnect; no memory leaks
  - **Proof:** _pending_

---

### Task 6.3: FastAPI Gateway

**🎯 Skill Activation:** `api-integration` — FastAPI patterns, lifespan management.
**🎯 Skill Activation:** `architecture-design` — Endpoint design, middleware composition.
**🎯 MCP Activation:** `quality-assurance` — Type check all endpoints.
**🎯 MCP Activation:** `execution-engine` — Load test the API.

**Context:** Per PHASE 7C of SUPERNOVA_AGENT_PROMPT.md — main application.

**Dependencies:** Task 6.2 (WebSocket handler), Task 5.x (infrastructure)

- [ ] **6.3.1** Create `api/gateway.py` with lifespan context manager
  - **Validation:** Lifespan initializes DB pool, Redis, Graphiti, LiteLLM router, agent graph (compiled once)
  - **Proof:** _pending_

- [ ] **6.3.2** Implement `GET /health` endpoint
  - **Validation:** Returns `{"status": "ok", "version": "2.0.0"}`
  - **Proof:** _pending_

- [ ] **6.3.3** Implement `POST /auth/token` endpoint
  - **Validation:** Accepts `{"user_id": str}`; returns `{"access_token": str}`
  - **Proof:** _pending_

- [ ] **6.3.4** Implement `WebSocket /agent/stream/{session_id}` endpoint
  - **Validation:** Requires JWT in query param `?token=...`; uses handler from websockets.py
  - **Proof:** _pending_

- [ ] **6.3.5** Implement `GET /memory/semantic` endpoint
  - **Validation:** Requires JWT; returns user's semantic memories
  - **Proof:** _pending_

- [ ] **6.3.6** Implement `GET /memory/procedural` endpoint
  - **Validation:** Returns list of compiled skills
  - **Proof:** _pending_

- [ ] **6.3.7** Implement `GET /admin/fleet` endpoint
  - **Validation:** Returns `DynamicModelRouter.get_fleet_summary()`
  - **Proof:** _pending_

- [ ] **6.3.8** Mount interrupt router at `/hitl`
  - **Validation:** Routes from `api/interrupts.py` available at `/hitl/*`
  - **Proof:** _pending_

- [ ] **6.3.9** Add CORS middleware
  - **Validation:** Allows all origins in dev; `ALLOWED_ORIGINS` env var restricts in prod; uses orjson for responses
  - **Proof:** _pending_

---

### Task 6.4: MCP API Endpoints

**🎯 Skill Activation:** `mcp-builder` — MCP tool exposure patterns.
**🎯 Skill Activation:** `api-integration` — RESTful tool endpoints design.
**🎯 Skill Activation:** `multi-agent-orchestration` — Server state management.
**🎯 MCP Activation:** `code-intelligence` — Analyze MCP API patterns.

**Context:** Expose MCP server management and skill activation via REST API.

**Dependencies:** Task 5.7 (MCP client), Task 5.8 (Skills loader)

- [ ] **6.4.1** Implement `GET /mcp/servers` endpoint
  - **Validation:** Returns list of configured MCP servers with health status
  - **Proof:** _pending_

- [ ] **6.4.2** Implement `GET /mcp/tools` endpoint
  - **Validation:** Returns aggregated tools from all healthy MCP servers
  - **Proof:** _pending_

- [ ] **6.4.3** Implement `POST /mcp/tools/{tool_name}` endpoint
  - **Validation:** Executes MCP tool with provided arguments; returns result
  - **Proof:** _pending_

- [ ] **6.4.4** Implement `GET /skills` endpoint
  - **Validation:** Returns list of available skills from `mcp_and_skills/skills/`
  - **Proof:** _pending_

- [ ] **6.4.5** Implement `POST /skills/{skill_name}/activate` endpoint
  - **Validation:** Activates skill for session; injects into context
  - **Proof:** _pending_

- [ ] **6.4.6** Implement WebSocket MCP events
  - **Validation:** Streams MCP tool execution events; tool_start, tool_progress, tool_complete
  - **Proof:** _pending_

---

## PHASE 7 — Background Workers

**Phase Objective:** Implement Celery workers for consolidation, heartbeat, and maintenance.

**Estimated Duration:** 1-2 sessions
**Completion Criteria:** Workers start; scheduled tasks run; no errors.

---

### Task 7.1: Celery Application Setup

**🎯 Skill Activation:** `observability-monitoring` — Worker monitoring, task tracking.
**🎯 Skill Activation:** `performance-engineering` — Queue optimization, beat scheduling.
**🎯 MCP Activation:** `execution-engine` — Test Celery startup and task execution.

**Context:** Per PHASE 8A of SUPERNOVA_AGENT_PROMPT.md — RedBeat scheduler.

**Dependencies:** Task 2.1 (celery/redbeat dependencies), Task 1.2.6 (docker-compose with Redis)

- [ ] **7.1.1** Create `workers/celery_app.py`
  - **Validation:** Celery app with Redis broker; RedBeatScheduler; beat_schedule with consolidation-hourly, heartbeat-check-every-15min, forgetting-curves-weekly, skill-crystallization-daily
  - **Proof:** _pending_

- [ ] **7.1.2** Verify Celery starts without error
  - **Validation:** `celery -A supernova.workers worker --loglevel=info` starts; connects to Redis
  - **Proof:** _pending_

---

### Task 7.2: Consolidation Worker

**Context:** Per PHASE 8B of SUPERNOVA_AGENT_PROMPT.md — episodic→semantic transfer.

**Dependencies:** Task 7.1 (Celery app), Task 5.3 (episodic store), Task 5.4 (semantic store)

- [ ] **7.2.1** Create `workers/consolidation.py` with `consolidate_episodic_memories()` task
  - **Validation:** Fetches last 24h episodes from Graphiti; uses LLM (fast tier) to extract facts; writes to semantic memory via upsert
  - **Proof:** _pending_

- [ ] **7.2.2** Implement `crystallize_skills()` task
  - **Validation:** Instantiates `SkillCrystallizationWorker` from `core/memory/procedural.py`; calls `run_crystallization_cycle()`
  - **Proof:** _pending_

---

### Task 7.3: Heartbeat Worker

**Context:** Per PHASE 8C of SUPERNOVA_AGENT_PROMPT.md — periodic status checks.

**Dependencies:** Task 7.1 (Celery app)

- [ ] **7.3.1** Create `workers/heartbeat.py` with `run_heartbeat_cycle()` task
  - **Validation:** Checks pending scheduled tasks; generates status summary; logs to Langfuse as background trace
  - **Proof:** _pending_

---

### Task 7.4: Maintenance Worker

**Context:** Per PHASE 8D of SUPERNOVA_AGENT_PROMPT.md — forgetting curves.

**Dependencies:** Task 7.1 (Celery app), Task 4.2.10 (run_forgetting_curves procedure)

- [ ] **7.4.1** Create `workers/maintenance.py` with `run_forgetting_curves()` task
  - **Validation:** Calls `CALL run_forgetting_curves()` via asyncpg; logs row counts affected
  - **Proof:** _pending_

---

### Task 7.5: MCP Health Monitoring

**Context:** Monitor MCP server health and restart unhealthy servers automatically.

**Dependencies:** Task 5.7 (MCP client), Task 7.1 (Celery app)

- [ ] **7.5.1** Create `workers/mcp_monitor.py` with `check_mcp_health()` task
  - **Validation:** Pings all configured MCP servers; updates health status; logs to Langfuse
  - **Proof:** _pending_

- [ ] **7.5.2** Implement automatic MCP server restart
  - **Validation:** Restarts unhealthy servers; exponential backoff for failing servers; alerts after 3 failures
  - **Proof:** _pending_

- [ ] **7.5.3** Schedule health checks every 5 minutes
  - **Validation:** Celery beat schedule configured; task runs every 5 minutes
  - **Proof:** _pending_

---

## PHASE 8 — Test Suite

**Phase Objective:** Comprehensive test coverage for all critical paths.

**Estimated Duration:** 2-3 sessions
**Completion Criteria:** ≥80% coverage; all tests pass; CI-ready.

---

### Task 8.1: Test Fixtures

**🎯 Skill Activation:** `test-driven-development` — Fixture design, test isolation patterns.
**🎯 Skill Activation:** `architecture-design` — Test architecture, dependency injection.
**🎯 MCP Activation:** `code-intelligence` — Analyze test coverage patterns.

**Context:** Per PHASE 9 of SUPERNOVA_AGENT_PROMPT.md — test infrastructure.

**Dependencies:** Task 5.x (all infrastructure), Task 4.2 (database)

- [ ] **8.1.1** Create `tests/conftest.py` with `db_pool` fixture
  - **Validation:** Asyncpg pool pointing to `supernova_test` database; test isolation
  - **Proof:** _pending_

- [ ] **8.1.2** Add `redis_client` fixture
  - **Validation:** Aioredis client pointing to db 15; test isolation
  - **Proof:** _pending_

- [ ] **8.1.3** Add `mock_llm` fixture
  - **Validation:** Mock LiteLLM router with predefined responses; no API calls
  - **Proof:** _pending_

- [ ] **8.1.4** Add `mock_embedder` fixture
  - **Validation:** Returns deterministic 1536-dim zero vectors; fast; no API calls
  - **Proof:** _pending_

- [ ] **8.1.5** Add `tool_registry` fixture
  - **Validation:** Registry with `READ_FILES | WEB_SEARCH` granted
  - **Proof:** _pending_

- [ ] **8.1.6** Add `interrupt_coordinator` fixture
  - **Validation:** Fresh coordinator with mock broadcaster
  - **Proof:** _pending_

---

### Task 8.2: Context Assembly Tests

**🎯 Skill Activation:** `context-management` — Validate primacy/middle/recency zones.
**🎯 Skill Activation:** `test-driven-development` — FIRST principles for context tests.
**🎯 MCP Activation:** `code-intelligence` — Verify context window calculations.

**Context:** Per PHASE 9 of SUPERNOVA_AGENT_PROMPT.md — positional awareness verification.

**Dependencies:** Task 8.1 (fixtures), Task 1.2.3 (context_assembly.py spec)

- [ ] **8.2.1** Create `tests/test_context_assembly.py`
  - **Validation:** File exists and imports
  - **Proof:** _pending_

- [ ] **8.2.2** Test `test_primacy_zone_always_included()`
  - **Validation:** System content always at message index 0
  - **Proof:** _pending_

- [ ] **8.2.3** Test `test_middle_zone_injection()`
  - **Validation:** Semantic memories appear in middle, not first or last
  - **Proof:** _pending_

- [ ] **8.2.4** Test `test_recency_zone_prefix()`
  - **Validation:** Working memory prepended to final user message
  - **Proof:** _pending_

- [ ] **8.2.5** Test `test_empty_inputs_produce_valid_messages()`
  - **Validation:** Empty ContextInputs produces at least [system_msg, user_msg]
  - **Proof:** _pending_

- [ ] **8.2.6** Test `test_conversation_history_truncation()`
  - **Validation:** Long history truncated from front, not back
  - **Proof:** _pending_

- [ ] **8.2.7** Test `test_context_stats_returns_valid_percentages()`
  - **Validation:** `estimate_context_stats` output is internally consistent
  - **Proof:** _pending_

---

### Task 8.3: Routing Tests

**Context:** Per PHASE 9 of SUPERNOVA_AGENT_PROMPT.md — model selection verification.

**Dependencies:** Task 8.1 (fixtures), Task 1.2.4 (dynamic_router.py spec)

- [ ] **8.3.1** Create `tests/test_routing.py`
  - **Validation:** File exists and imports
  - **Proof:** _pending_

- [ ] **8.3.2** Test `test_planning_task_routes_to_highest_reasoning_model()`
  - **Validation:** Planning routes to model with higher reasoning_depth
  - **Proof:** _pending_

- [ ] **8.3.3** Test `test_cost_constraint_eliminates_expensive_models()`
  - **Validation:** max_cost=0.001 excludes expensive models
  - **Proof:** _pending_

- [ ] **8.3.4** Test `test_local_only_bypasses_optimization()`
  - **Validation:** local_only task always returns local model
  - **Proof:** _pending_

- [ ] **8.3.5** Test `test_constraint_relaxation_cascade()`
  - **Validation:** When no model feasible, relaxation fires in correct order
  - **Proof:** _pending_

- [ ] **8.3.6** Test `test_fleet_summary_returns_all_models()`
  - **Validation:** `get_fleet_summary()` returns all models
  - **Proof:** _pending_

---

### Task 8.4: Interrupts Tests

**Context:** Per PHASE 9 of SUPERNOVA_AGENT_PROMPT.md — HITL workflow verification.

**Dependencies:** Task 8.1 (fixtures), Task 1.2.5 (interrupts.py spec)

- [ ] **8.4.1** Create `tests/test_interrupts.py`
  - **Validation:** File exists and imports
  - **Proof:** _pending_

- [ ] **8.4.2** Test `test_approval_resolves_when_decision_submitted()`
  - **Validation:** `submit_decision()` unblocks `request_approval()`
  - **Proof:** _pending_

- [ ] **8.4.3** Test `test_timeout_auto_approves_low_risk()`
  - **Validation:** Low risk auto-approves after timeout
  - **Proof:** _pending_

- [ ] **8.4.4** Test `test_timeout_auto_denies_high_risk()`
  - **Validation:** High risk auto-denies after timeout
  - **Proof:** _pending_

- [ ] **8.4.5** Test `test_unknown_thread_id_returns_false()`
  - **Validation:** `submit_decision` returns False for unknown thread_id
  - **Proof:** _pending_

- [ ] **8.4.6** Test `test_os_notification_does_not_raise_if_binary_missing()`
  - **Validation:** FileNotFoundError suppressed for missing notify binary
  - **Proof:** _pending_

---

### Task 8.5: Memory Retrieval Tests

**Context:** Per PHASE 9 of SUPERNOVA_AGENT_PROMPT.md — end-to-end memory verification.

**Dependencies:** Task 8.1 (fixtures), Task 5.x (memory stores)

- [ ] **8.5.1** Create `tests/test_memory_retrieval.py`
  - **Validation:** File exists and imports
  - **Proof:** _pending_

- [ ] **8.5.2** Test `test_upsert_and_search_round_trip()`
  - **Validation:** Insert memory, search for similar text, assert appears in results
  - **Proof:** _pending_

- [ ] **8.5.3** Test `test_forgetting_curve_decays_importance()`
  - **Validation:** Create memory with importance=5, run forgetting curve, assert importance < 5
  - **Proof:** _pending_

- [ ] **8.5.4** Test `test_hybrid_search_returns_higher_score_than_vector_only()`
  - **Validation:** RRF score >= vector-only score for exact keyword match
  - **Proof:** _pending_

- [ ] **8.5.5** Test `test_working_memory_round_trip()`
  - **Validation:** Set and get working memory; fields survive msgpack serialization
  - **Proof:** _pending_

---

### Task 8.6: MCP Integration Tests

**Context:** Test MCP client, tool execution, and skill loading.

**Dependencies:** Task 8.1 (fixtures), Task 5.7 (MCP client)

- [ ] **8.6.1** Create `tests/test_mcp_client.py`
  - **Validation:** File exists and imports
  - **Proof:** _pending_

- [ ] **8.6.2** Test `test_mcp_server_connection()`
  - **Validation:** Connects to MCP filesystem server; lists tools successfully
  - **Proof:** _pending_

- [ ] **8.6.3** Test `test_mcp_tool_execution()`
  - **Validation:** Executes MCP tool (e.g., read_file); returns expected result
  - **Proof:** _pending_

- [ ] **8.6.4** Test `test_mcp_timeout_handling()`
  - **Validation:** Tool exceeding 30s timeout returns error; doesn't hang
  - **Proof:** _pending_

- [ ] **8.6.5** Test `test_mcp_health_check()`
  - **Validation:** Health check detects server status; unhealthy servers marked
  - **Proof:** _pending_

- [ ] **8.6.6** Create `tests/test_skills.py`
  - **Validation:** File exists and imports
  - **Proof:** _pending_

- [ ] **8.6.7** Test `test_skill_loading()`
  - **Validation:** Loads skill from `mcp_and_skills/skills/`; parses SKILL.md correctly
  - **Proof:** _pending_

- [ ] **8.6.8** Test `test_skill_hot_reload()`
  - **Validation:** Skill file change detected; content updated without restart
  - **Proof:** _pending_

- [ ] **8.6.9** Test `test_skill_injection()`
  - **Validation:** Active skill content appears in assembled context
  - **Proof:** _pending_

---

## PHASE 9 — Integration Verification

**Phase Objective:** End-to-end smoke tests and final validation.

**Estimated Duration:** 1 session
**Completion Criteria:** All 10 steps complete; ≥80% coverage; Langfuse shows traces.

---

### Task 9.1: Full Integration Test

**🎯 Skill Activation:** `hostile-auditor` — MANDATORY: Full adversarial system audit.
**🎯 Skill Activation:** `debugging-root-cause-analysis` — Systematic failure diagnosis.
**🎯 Skill Activation:** `create-plan` — Generate integration test execution plan.
**🎯 MCP Activation:** `execution-engine` — Run all smoke tests and validate.
**🎯 MCP Activation:** `quality-assurance` — Final lint, type check, security scan.

**Context:** Per PHASE 10 of SUPERNOVA_AGENT_PROMPT.md — complete system verification.

**Dependencies:** All previous tasks

- [ ] **9.1.1** Start infrastructure services
  - **Validation:** `docker compose up -d postgres neo4j redis langfuse` succeeds; all healthy
  - **Proof:** _pending_

- [ ] **9.1.2** Run database migrations
  - **Validation:** `alembic upgrade head` runs without error
  - **Proof:** _pending_

- [ ] **9.1.3** Run test suite with coverage
  - **Validation:** `pytest tests/ -v --cov=core --cov=infrastructure --cov=api --cov-report=term-missing` shows ≥80% coverage
  - **Proof:** _pending_

- [ ] **9.1.4** Start FastAPI application
  - **Validation:** `uvicorn api.gateway:app --reload` starts; `/health` responds
  - **Proof:** _pending_

- [ ] **9.1.5** Test authentication endpoint
  - **Validation:** `POST /auth/token` returns `{"access_token": "eyJ..."}`
  - **Proof:** _pending_

- [ ] **9.1.6** Test WebSocket streaming
  - **Validation:** `wscat -c "ws://localhost:8000/agent/stream/test?token=..."` connects; sending message produces token stream
  - **Proof:** _pending_

- [ ] **9.1.7** Verify Langfuse traces
  - **Validation:** Open http://localhost:3000; traces visible with memory retrieval and reasoning spans
  - **Proof:** _pending_

- [ ] **9.1.8** Start Celery worker
  - **Validation:** `celery -A workers worker --loglevel=debug` starts without error
  - **Proof:** _pending_

- [ ] **9.1.9** Start Celery beat
  - **Validation:** `celery -A workers beat --loglevel=debug` starts; schedules loaded
  - **Proof:** _pending_

- [ ] **9.1.10** Trigger manual consolidation
  - **Validation:** `celery -A workers call workers.consolidation.consolidate_episodic_memories` executes without error
  - **Proof:** _pending_

- [ ] **9.1.11** Test MCP filesystem server integration
  - **Validation:** `GET /mcp/tools` includes filesystem tools; `POST /mcp/tools/read_file` reads file successfully
  - **Proof:** _pending_

- [ ] **9.1.12** Test skill activation
  - **Validation:** `POST /skills/mcp-builder/activate` succeeds; skill content appears in agent responses
  - **Proof:** _pending_

- [ ] **9.1.13** Verify MCP health monitoring
  - **Validation:** MCP servers show healthy status; `workers/mcp_monitor.py` task runs
  - **Proof:** _pending_

---

### Task 9.2: Final Checklist Verification

**🎯 Skill Activation:** `hostile-auditor` — MANDATORY: Verify no placeholders, all code is real.
**🎯 Skill Activation:** `code-review-refactoring` — Final code quality review.
**🎯 Skill Activation:** `security-engineering` — Verify security properties.
**🎯 MCP Activation:** `quality-assurance` — Run full test suite with coverage.
**🎯 MCP Activation:** `execution-engine` — Verify all 13 checklist items.

**Context:** Per COMPLETION CHECKLIST of SUPERNOVA_AGENT_PROMPT.md — all items must pass.

**Dependencies:** Task 9.1 (integration tests passed)

- [ ] **9.2.1** Verify pytest coverage ≥80%
  - **Validation:** Coverage report shows ≥80% for core, infrastructure, api
  - **Proof:** _pending_

- [ ] **9.2.2** Verify docker compose brings up 7 services healthy
  - **Validation:** `docker compose ps` shows 7 services all healthy
  - **Proof:** _pending_

- [ ] **9.2.3** Verify alembic on fresh database
  - **Validation:** Drop and recreate database; `alembic upgrade head` succeeds
  - **Proof:** _pending_

- [ ] **9.2.4** Verify WebSocket smoke test
  - **Validation:** Second message to same session_id demonstrates memory continuity
  - **Proof:** _pending_

- [ ] **9.2.5** Verify `/admin/fleet` endpoint
  - **Validation:** Returns model capability fleet summary
  - **Proof:** _pending_

- [ ] **9.2.6** Verify `/memory/procedural` endpoint
  - **Validation:** Returns empty list for fresh install
  - **Proof:** _pending_

- [ ] **9.2.7** Verify Celery heartbeat task
  - **Validation:** Worker processes heartbeat task without error
  - **Proof:** _pending_

- [ ] **9.2.8** Verify file write tool rejects path traversal
  - **Validation:** `../etc/passwd` rejected by FileWriteTool
  - **Proof:** _pending_

- [ ] **9.2.9** Verify Ruff linter passes
  - **Validation:** `ruff check .` returns no errors
  - **Proof:** _pending_

- [ ] **9.2.10** Verify MyPy type checking passes
  - **Validation:** `mypy core/ infrastructure/ api/ --ignore-missing-imports` passes
  - **Proof:** _pending_

- [ ] **9.2.11** Verify MCP servers are accessible
  - **Validation:** `GET /mcp/servers` returns configured servers; all show healthy
  - **Proof:** _pending_

- [ ] **9.2.12** Verify skills are loadable
  - **Validation:** `GET /skills` returns skills from `mcp_and_skills/skills/`; count >= 40
  - **Proof:** _pending_

- [ ] **9.2.13** Verify MCP tool execution works
  - **Validation:** Can execute MCP tool via API; result returned within 30s
  - **Proof:** _pending_

---

## PHASE 10 — Dashboard Integration

**Phase Objective:** Wire nova-dashboard.jsx to real backend via WebSocket and REST API.

**Estimated Duration:** 1 session
**Completion Criteria:** Dashboard displays real-time data; no simulation mode.

---

### Task 10.1: Dashboard Backend Integration

**🎯 Skill Activation:** `frontend-design` — UI component design, React patterns.
**🎯 Skill Activation:** `api-integration` — WebSocket integration, state management.
**🎯 MCP Activation:** `execution-engine` — Build and test frontend.
**🎯 MCP Activation:** `webapp-testing` — E2E testing with Playwright.

**Context:** Connect React dashboard to FastAPI backend.

**Dependencies:** Task 6.3 (FastAPI gateway), Task 9.1 (integration tests)

- [ ] **10.1.1** Create `useNovaRealtime()` hook replacing simulation
  - **Validation:** Hook connects to `/agent/stream/{session_id}` WebSocket; receives real events
  - **Proof:** _pending_

- [ ] **10.1.2** Implement WebSocket reconnection with exponential backoff
  - **Validation:** On disconnect: retries with backoff (1s, 2s, 4s, 8s, 16s); max 5 attempts
  - **Proof:** _pending_

- [ ] **10.1.3** Integrate dashboard API endpoints
  - **Validation:** Fetches from `/memory/semantic`, `/memory/procedural`, `/admin/fleet`; displays real data
  - **Proof:** _pending_

- [ ] **10.1.4** Add connection states (connecting, connected, error)
  - **Validation:** UI shows spinner while connecting; error message on failure; retry button
  - **Proof:** _pending_

---

### Task 10.2: MCP Dashboard Integration

**🎯 Skill Activation:** `frontend-design` — Dashboard UI, visual components.
**🎯 Skill Activation:** `observability-monitoring` — Metrics visualization.
**🎯 Skill Activation:** `multi-agent-orchestration` — Server status display.
**🎯 MCP Activation:** `webapp-testing` — Test dashboard UI interactions.

**Context:** Dashboard UI for MCP server management and skill activation.

**Dependencies:** Task 6.4 (MCP API endpoints), Task 10.1 (Dashboard real-time)

- [ ] **10.2.1** Add MCP servers panel to dashboard
  - **Validation:** Displays all MCP servers with health indicators; shows tool count per server
  - **Proof:** _pending_

- [ ] **10.2.2** Add MCP tool explorer
  - **Validation:** Lists all available MCP tools; shows descriptions and parameters; allows testing
  - **Proof:** _pending_

- [ ] **10.2.3** Add skill activation UI
  - **Validation:** Lists available skills; toggle to activate/deactivate; shows active skills
  - **Proof:** _pending_

- [ ] **10.2.4** Add MCP execution monitoring
  - **Validation:** Real-time display of MCP tool calls; latency metrics; error tracking
  - **Proof:** _pending_

- [ ] **10.2.5** Integrate MCP events into cognitive loop visualization
  - **Validation:** Shows when MCP tools are called during reasoning; displays tool results
  - **Proof:** _pending_

---

## PHASE 11 — Cost Management & Budget Controls

**Phase Objective:** Prevent unexpected API costs with spending limits, alerts, and budget-aware routing.

**Estimated Duration:** 1 session  
**Completion Criteria:** Users cannot exceed set budgets; automatic fallback to cheaper models; cost visibility in dashboard.

---

### Task 11.1: Cost Tracking Infrastructure

**🎯 Skill Activation:** `performance-engineering` — Efficient counters and caching.  
**🎯 Skill Activation:** `observability-monitoring` — Metrics collection and alerting.  
**🎯 MCP Activation:** `code-intelligence` — Verify cost calculation accuracy.

**Context:** CRITICAL for non-technical users to avoid surprise bills. Per Senior Engineering Review.

**Dependencies:** Task 5.1.2 (Redis client), Task 2.1 (dependencies)

- [ ] **11.1.1** Create `infrastructure/llm/cost_controller.py` with `CostController` class
  - **Validation:** Tracks spending per day/month; Redis-backed counters; atomic increments
  - **Proof:** _pending_

- [ ] **11.1.2** Implement `check_budget()` method
  - **Validation:** Returns True/False based on configured limits; checks both daily and monthly
  - **Proof:** _pending_

- [ ] **11.1.3** Implement `record_cost()` method
  - **Validation:** Records actual spend after LLM call; updates running totals
  - **Proof:** _pending_

- [ ] **11.1.4** Add cost estimation helper
  - **Validation:** Estimates cost before call based on token counts; accurate within 20%
  - **Proof:** _pending_

---

### Task 11.2: Budget-Aware Model Routing

**🎯 Skill Activation:** `architecture-design` — Routing logic enhancement.  
**🎯 MCP Activation:** `quality-assurance` — Test fallback scenarios.

**Context:** Modify existing router to respect budgets and auto-fallback.

**Dependencies:** Task 11.1 (cost controller), Task 1.2.4 (dynamic_router.py)

- [ ] **11.2.1** Integrate cost checks into `DynamicModelRouter`
  - **Validation:** Router checks budget before model selection; respects spending limits
  - **Proof:** _pending_

- [ ] **11.2.2** Implement model fallback chain
  - **Validation:** When approaching limits: GPT-4 → Claude 3.5 → local model; seamless transition
  - **Proof:** _pending_

- [ ] **11.2.3** Add pre-call cost confirmation for expensive operations
  - **Validation:** Operations >$0.50 require user confirmation via WebSocket
  - **Proof:** _pending_

---

### Task 11.3: Cost Visibility & Alerts

**🎯 Skill Activation:** `frontend-design` — Dashboard UI for cost display.  
**🎯 MCP Activation:** `execution-engine` — Test alert delivery.

**Dependencies:** Task 6.3 (API gateway), Task 10.1 (dashboard)

- [ ] **11.3.1** Add cost endpoints to API
  - **Validation:** `GET /admin/costs` returns current spend, limits, projections
  - **Proof:** _pending_

- [ ] **11.3.2** Create dashboard cost widget
  - **Validation:** Shows daily/monthly spend with progress bars; color-coded warnings
  - **Proof:** _pending_

- [ ] **11.3.3** Implement WebSocket cost alerts
  - **Validation:** Alerts at 50%, 80%, 100% of budget; visible in UI
  - **Proof:** _pending_

- [ ] **11.3.4** Add cost configuration to `.env.example`
  - **Validation:** `DAILY_BUDGET_USD`, `MONTHLY_BUDGET_USD`, `ENABLE_COST_CONFIRMATION`
  - **Proof:** _pending_

---

### Task 11.4: Local Model Fallback

**🎯 Skill Activation:** `performance-engineering` — Local inference optimization.  
**🎯 MCP Activation:** `execution-engine` — Test local model integration.

**Context:** Enable zero-cost operation with local LLMs.

**Dependencies:** Task 11.2 (budget-aware routing)

- [ ] **11.4.1** Add Ollama integration
  - **Validation:** `infrastructure/llm/ollama_client.py` with async inference
  - **Proof:** _pending_

- [ ] **11.4.2** Add local embedding model support
  - **Validation:** sentence-transformers fallback for embeddings when API budget exceeded
  - **Proof:** _pending_

- [ ] **11.4.3** Document local model setup
  - **Validation:** README section on running with Ollama; tested on macOS/Linux
  - **Proof:** _pending_

---

## PHASE 12 — Backup, Recovery & Data Portability

**Phase Objective:** Protect user data with automated backups, export/import, and disaster recovery.

**Estimated Duration:** 1-2 sessions  
**Completion Criteria:** Daily automated backups; one-click restore; memory export to Markdown/JSON.

---

### Task 12.1: Backup Infrastructure

**🎯 Skill Activation:** `database-design-optimization` — Efficient database dumps.  
**🎯 Skill Activation:** `observability-monitoring` — Backup monitoring.  
**🎯 MCP Activation:** `execution-engine` — Test backup/restore procedures.

**Context:** CRITICAL for a "personal AI agent with persistent memory". Per Senior Engineering Review.

**Dependencies:** Task 4.2 (database schema), Task 5.1 (storage layer)

- [ ] **12.1.1** Create `core/backup/manager.py` with `BackupManager` class
  - **Validation:** Coordinates PostgreSQL, Neo4j, Redis backups
  - **Proof:** _pending_

- [ ] **12.1.2** Implement PostgreSQL backup
  - **Validation:** Uses `pg_dump` with custom format; includes schema + data
  - **Proof:** _pending_

- [ ] **12.1.3** Implement Neo4j backup
  - **Validation:** Uses `neo4j-admin dump`; includes temporal graph data
  - **Proof:** _pending_

- [ ] **12.1.4** Implement Redis RDB snapshot
  - **Validation:** Triggers `BGSAVE`; copies dump.rdb
  - **Proof:** _pending_

- [ ] **12.1.5** Add backup encryption
  - **Validation:** GPG encryption with user-provided passphrase
  - **Proof:** _pending_

---

### Task 12.2: Automated Backup Scheduling

**🎯 Skill Activation:** `performance-engineering` — Efficient scheduling.  
**🎯 MCP Activation:** `execution-engine` — Verify scheduled execution.

**Dependencies:** Task 12.1 (backup infrastructure), Task 7.1 (Celery setup)

- [ ] **12.2.1** Create `workers/backup.py` with Celery tasks
  - **Validation:** `daily_backup()` task scheduled via RedBeat
  - **Proof:** _pending_

- [ ] **12.2.2** Implement backup rotation
  - **Validation:** Keeps 7 daily, 4 weekly, 12 monthly backups; deletes old ones
  - **Proof:** _pending_

- [ ] **12.2.3** Add backup verification
  - **Validation:** Test-restores backup to verify integrity
  - **Proof:** _pending_

---

### Task 12.3: Cloud Backup Storage

**🎯 Skill Activation:** `api-integration` — S3 API integration.  
**🎯 Skill Activation:** `security-engineering` — Secure credential handling.

**Dependencies:** Task 12.1 (backup infrastructure)

- [ ] **12.3.1** Add S3-compatible storage support
  - **Validation:** Uploads backups to AWS S3, GCS, or MinIO; configurable endpoint
  - **Proof:** _pending_

- [ ] **12.3.2** Add backup download/restore from cloud
  - **Validation:** `supernova restore --from=s3://bucket/backup-file`
  - **Proof:** _pending_

- [ ] **12.3.3** Document cloud backup setup
  - **Validation:** Step-by-step guide for S3, GCS, Backblaze B2
  - **Proof:** _pending_

---

### Task 12.4: Memory Export/Import

**🎯 Skill Activation:** `api-integration` — Data format conversion.  
**🎯 MCP Activation:** `filesystem` — File operations.

**Context:** User data portability - GDPR compliance, migration.

**Dependencies:** Task 5.4 (semantic memory), Task 5.3 (episodic memory)

- [ ] **12.4.1** Implement memory export API
  - **Validation:** `GET /memory/export` returns JSON with all user memories
  - **Proof:** _pending_

- [ ] **12.4.2** Add Markdown export format
  - **Validation:** Conversations exported as readable Markdown files
  - **Proof:** _pending_

- [ ] **12.4.3** Implement selective export
  - **Validation:** Filter by date range, category, memory type
  - **Proof:** _pending_

- [ ] **12.4.4** Implement memory import
  - **Validation:** `POST /memory/import` accepts JSON; validates and inserts
  - **Proof:** _pending_

- [ ] **12.4.5** Add export UI to dashboard
  - **Validation:** Button to "Export My Data"; download starts automatically
  - **Proof:** _pending_

---

### Task 12.5: CLI Commands

**🎯 MCP Activation:** `execution-engine` — CLI testing.

**Dependencies:** Task 12.1 (backup infrastructure)

- [ ] **12.5.1** Create `supernova backup` CLI
  - **Validation:** `supernova backup create --name="pre-update"`
  - **Proof:** _pending_

- [ ] **12.5.2** Create `supernova restore` CLI
  - **Validation:** `supernova restore --from="backup-2026-02-25.enc"`
  - **Proof:** _pending_

- [ ] **12.5.3** Create `supernova export` CLI
  - **Validation:** `supernova export --format=markdown --output=./my-memories.md`
  - **Proof:** _pending_

---

## PHASE 13 — Security Hardening

**Phase Objective:** Production-grade security with audit logging, secrets encryption, and sandboxing.

**Estimated Duration:** 1-2 sessions  
**Completion Criteria:** Security audit passes; pickle replaced; secrets encrypted; audit log functional.

---

### Task 13.1: Secure Serialization (CRITICAL)

**🎯 Skill Activation:** `security-engineering` — Secure serialization patterns.  
**🎯 MCP Activation:** `quality-assurance` — Security scan the implementation.

**Context:** pickle deserialization in procedural.py is a known RCE vulnerability.

**Dependencies:** Task 1.2.2 (procedural.py spec)

- [ ] **13.1.1** Replace pickle with cloudpickle + whitelist
  - **Validation:** Uses cloudpickle with custom reducer; only allows safe types
  - **Proof:** _pending_

- [ ] **13.1.2** Add cryptographic signing
  - **Validation:** Serialized data signed with HMAC; rejects tampered data
  - **Proof:** _pending_

- [ ] **13.1.3** Add serialization tests
  - **Validation:** Tests that malicious payloads are rejected
  - **Proof:** _pending_

---

### Task 13.2: Secrets Management

**🎯 Skill Activation:** `security-engineering` — Encryption at rest.  
**🎯 MCP Activation:** `quality-assurance` — Verify encryption implementation.

**Context:** API keys in plain env vars are a security risk.

**Dependencies:** Task 3.1 (environment configuration)

- [ ] **13.2.1** Create `infrastructure/security/secrets.py`
  - **Validation:** Master password derivation (Argon2); AES-256-GCM encryption
  - **Proof:** _pending_

- [ ] **13.2.2** Implement keychain integration
  - **Validation:** macOS Keychain support; Linux libsecret; Windows Credential Manager
  - **Proof:** _pending_

- [ ] **13.2.3** Add secrets migration
  - **Validation:** One-time migration from env vars to encrypted store
  - **Proof:** _pending_

- [ ] **13.2.4** Document secrets setup
  - **Validation:** Clear instructions for master password setup
  - **Proof:** _pending_

---

### Task 13.3: Audit Logging

**🎯 Skill Activation:** `security-engineering` — Audit trail design.  
**🎯 Skill Activation:** `observability-monitoring` — Log management.

**Dependencies:** Task 4.2 (database), Task 6.3 (API layer)

- [ ] **13.3.1** Create `audit_logs` table
  - **Validation:** Columns: id, timestamp, user_id, action, resource, details, ip_address
  - **Proof:** _pending_

- [ ] **13.3.2** Implement audit decorator
  - **Validation:** `@audit_log` decorator logs all privileged operations
  - **Proof:** _pending_

- [ ] **13.3.3** Add audit logging to critical operations
  - **Validation:** File write/delete, API key changes, config changes all logged
  - **Proof:** _pending_

- [ ] **13.3.4** Create audit log API
  - **Validation:** `GET /admin/audit-logs` returns paginated audit entries
  - **Proof:** _pending_

---

### Task 13.4: Enhanced Sandboxing

**🎯 Skill Activation:** `security-engineering` — Container security.  
**🎯 MCP Activation:** `execution-engine` — Test sandbox boundaries.

**Context:** Current Docker sandbox needs hardening.

**Dependencies:** Task 5.6.3 (code execution tool)

- [ ] **13.4.1** Research gVisor/kata-containers integration
  - **Validation:** Document feasibility; implement if viable
  - **Proof:** _pending_

- [ ] **13.4.2** Add network namespace isolation
  - **Validation:** Code execution cannot access internal network
  - **Proof:** _pending_

- [ ] **13.4.3** Implement resource limits enforcement
  - **Validation:** Strict CPU, memory, disk I/O limits for code execution
  - **Proof:** _pending_

- [ ] **13.4.4** Add syscall filtering
  - **Validation:** Seccomp profile restricting dangerous syscalls
  - **Proof:** _pending_

---

## PHASE 14 — Observability & Diagnostics

**Phase Objective:** Production-ready monitoring, alerting, and troubleshooting tools.

**Estimated Duration:** 1 session  
**Completion Criteria:** All services monitored; alerts configured; `supernova doctor` works.

---

### Task 14.1: Structured Logging

**🎯 Skill Activation:** `observability-monitoring` — Logging best practices.  
**🎯 MCP Activation:** `code-intelligence` — Verify log structure.

**Dependencies:** Task 1.1 (project structure)

- [ ] **14.1.1** Configure structured JSON logging
  - **Validation:** All logs are JSON with timestamp, level, message, correlation_id
  - **Proof:** _pending_

- [ ] **14.1.2** Add correlation ID middleware
  - **Validation:** All requests get unique ID; propagated to all subsystems
  - **Proof:** _pending_

- [ ] **14.1.3** Configure log rotation
  - **Validation:** Logs rotate daily; 30-day retention
  - **Proof:** _pending_

---

### Task 14.2: Health Check System

**🎯 Skill Activation:** `api-integration` — Health endpoint design.  
**🎯 MCP Activation:** `execution-engine` — Test health checks.

**Dependencies:** Task 6.3 (API gateway)

- [ ] **14.2.1** Implement `/health/deep` endpoint
  - **Validation:** Checks PostgreSQL, Redis, Neo4j, MCP servers, LLM APIs
  - **Proof:** _pending_

- [ ] **14.2.2** Add health check dashboard
  - **Validation:** Visual indicators for each service status
  - **Proof:** _pending_

- [ ] **14.2.3** Implement health-based alerting
  - **Validation:** WebSocket alert when service goes unhealthy
  - **Proof:** _pending_

---

### Task 14.3: Metrics Collection

**🎯 Skill Activation:** `observability-monitoring` — Metrics design.  
**🎯 MCP Activation:** `execution-engine` — Metrics endpoint testing.

**Dependencies:** Task 6.3 (API gateway)

- [ ] **14.3.1** Add Prometheus metrics endpoint
  - **Validation:** `/metrics` returns Prometheus-format metrics
  - **Proof:** _pending_

- [ ] **14.3.2** Implement key metrics
  - **Validation:** Request latency, token usage, error rates, memory hit rates
  - **Proof:** _pending_

- [ ] **14.3.3** Create Grafana dashboard (optional)
  - **Validation:** JSON dashboard importable to Grafana
  - **Proof:** _pending_

---

### Task 14.4: Diagnostic CLI

**🎯 Skill Activation:** `debugging-root-cause-analysis` — Diagnostic patterns.  
**🎯 MCP Activation:** `execution-engine` — Test CLI functionality.

**Context:** Essential for non-technical users to self-diagnose issues.

**Dependencies:** All infrastructure tasks

- [ ] **14.4.1** Create `supernova doctor` command
  - **Validation:** Checks all dependencies, configs, API connectivity; reports issues
  - **Proof:** _pending_

- [ ] **14.4.2** Implement `supernova logs` command
  - **Validation:** Streams logs with filtering options
  - **Proof:** _pending_

- [ ] **14.4.3** Add `supernova status` command
  - **Validation:** Shows service status, version, uptime
  - **Proof:** _pending_

- [ ] **14.4.4** Create automated diagnostics report
  - **Validation:** `supernova report` generates diagnostic bundle for support
  - **Proof:** _pending_

---

## PHASE 15 — User Experience & Onboarding

**Phase Objective:** Make SuperNova accessible to non-technical users with guided onboarding and simplified UI.

**Estimated Duration:** 1-2 sessions  
**Completion Criteria:** First-run tutorial works; simple mode available; mobile-responsive.

---

### Task 15.1: Setup Wizard

**🎯 Skill Activation:** `frontend-design` — Wizard UI design.  
**🎯 MCP Activation:** `webapp-testing` — E2E testing.

**Context:** Non-technical users need GUI setup, not `.env` files.

**Dependencies:** Task 6.3 (API gateway), Task 10.1 (dashboard)

- [ ] **15.1.1** Create setup wizard UI
  - **Validation:** Step-by-step: API keys, model selection, privacy settings, theme
  - **Proof:** _pending_

- [ ] **15.1.2** Add API key validation
  - **Validation:** Tests keys with actual API calls; shows clear error messages
  - **Proof:** _pending_

- [ ] **15.1.3** Add cost estimation during setup
  - **Validation:** Shows estimated monthly cost based on selected models
  - **Proof:** _pending_

- [ ] **15.1.4** Implement first-run detection
  - **Validation:** Redirects to wizard on first access; skips after completion
  - **Proof:** _pending_

---

### Task 15.2: Dashboard Modes

**🎯 Skill Activation:** `frontend-design` — UI simplification.  
**🎯 MCP Activation:** `webapp-testing` — Test both modes.

**Dependencies:** Task 10.1 (dashboard)

- [ ] **15.2.1** Implement Simple Mode
  - **Validation:** Chat interface only; hides technical internals; clean design
  - **Proof:** _pending_

- [ ] **15.2.2** Implement Advanced Mode
  - **Validation:** Full technical dashboard with all visualizations
  - **Proof:** _pending_

- [ ] **15.2.3** Add mode toggle
  - **Validation:** Easy switch between modes; preference persisted
  - **Proof:** _pending_

---

### Task 15.3: Onboarding Tutorial

**🎯 Skill Activation:** `frontend-design` — Tutorial overlay design.  
**🎯 MCP Activation:** `webapp-testing` — Test tutorial flow.

**Dependencies:** Task 15.1 (setup wizard)

- [ ] **15.3.1** Create interactive tutorial
  - **Validation:** Overlay highlights features; user progresses step-by-step
  - **Proof:** _pending_

- [ ] **15.3.2** Add example prompts library
  - **Validation:** "Try asking: ..." suggestions; categorized by use case
  - **Proof:** _pending_

- [ ] **15.3.3** Implement feature discovery
  - **Validation:** Highlights new features after updates
  - **Proof:** _pending_

---

### Task 15.4: Help System

**🎯 Skill Activation:** `context-management` — Documentation organization.  
**🎯 MCP Activation:** `knowledge-integration` — Help content indexing.

**Dependencies:** Task 10.1 (dashboard)

- [ ] **15.4.1** Add contextual tooltips
  - **Validation:** Hover over UI elements shows helpful explanations
  - **Proof:** _pending_

- [ ] **15.4.2** Create help panel
  - **Validation:** Searchable documentation within the app
  - **Proof:** _pending_

- [ ] **15.4.3** Add keyboard shortcuts reference
  - **Validation:** Modal with all shortcuts; accessible via `?` key
  - **Proof:** _pending_

- [ ] **15.4.4** Create FAQ section
  - **Validation:** Common questions with answers; expandable sections
  - **Proof:** _pending_

---

### Task 15.5: Mobile Responsiveness

**🎯 Skill Activation:** `frontend-design` — Responsive design.  
**🎯 MCP Activation:** `webapp-testing` — Mobile testing.

**Dependencies:** Task 10.1 (dashboard)

- [ ] **15.5.1** Implement responsive breakpoints
  - **Validation:** Works on 320px mobile, 768px tablet, 1920px desktop
  - **Proof:** _pending_

- [ ] **15.5.2** Add touch-friendly controls
  - **Validation:** Buttons sized for touch; swipe gestures where appropriate
  - **Proof:** _pending_

- [ ] **15.5.3** Optimize mobile layout
  - **Validation:** Collapsible panels; bottom sheet for controls
  - **Proof:** _pending_

---

## Completion Log

| Phase | Task                                                       | Completed At              | Evidence                                               |
| ----- | ---------------------------------------------------------- | ------------------------- | ------------------------------------------------------ |
| 0     | PROGRESS_TRACKER.md aligned with SUPERNOVA_AGENT_PROMPT.md | 2026-02-25T22:42:00-06:00 | This document with 10 phases matching prompt structure |
| 0     | Senior Engineering Review completed                        | 2026-02-25T22:45:00-06:00 | SENIOR_ENGINEERING_REVIEW.md with 5 new phases added   |
