# SuperNova — Data Models

## Core State Types

### AgentState (loop.py)
The central state container for the cognitive loop, defined as a `TypedDict`:

| Field | Type | Description |
|-------|------|-------------|
| `messages` | `Annotated[list[dict], operator.add]` | Conversation history (immutable append via LangGraph) |
| `session_id` | `str` | Current session identifier |
| `thread_id` | `str` | LangGraph thread for checkpointing |
| `memory_context` | `dict` | Retrieved memories from all stores |
| `active_plan` | `list[dict]` | Current execution plan steps |
| `tool_calls_this_turn` | `int` | Safety counter (max 15) |
| `reflection_critique` | `str \| None` | Self-evaluation output |
| `metadata` | `dict` | Extensible metadata |

### WorkingMemory (core/memory/working.py)
Dataclass for ephemeral session state stored in Redis:

| Field | Type | Default |
|-------|------|---------|
| `session_id` | `str` | required |
| `current_goal` | `str` | `""` |
| `active_context` | `list[str]` | `[]` |
| `scratch_pad` | `dict[str, Any]` | `{}` |
| `turn_count` | `int` | `0` |
| `last_tool_results` | `list[dict]` | `[]` |
| `pending_actions` | `list[dict]` | `[]` |

Serialized via msgpack for Redis storage.

## Memory Data Models

### Episodic Memory Record
Stored in Neo4j via Graphiti temporal knowledge graph:

| Field | Description |
|-------|-------------|
| `episode_id` | Unique identifier |
| `session_id` | Originating session |
| `content` | Episode narrative text |
| `timestamp` | When the episode occurred |
| `metadata` | Arbitrary key-value pairs |
| `embedding` | Vector representation for similarity search |

### Semantic Memory Record
Stored in PostgreSQL with pgvector HNSW index:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Primary key |
| `content` | `text` | Memory content |
| `category` | `str` | Classification (fact, preference, instruction) |
| `embedding` | `vector(1536)` | OpenAI embedding |
| `importance` | `float` | Relevance score (0-1) |
| `access_count` | `int` | Retrieval frequency |
| `last_accessed` | `timestamp` | For forgetting curves |
| `created_at` | `timestamp` | Creation time |
| `metadata` | `jsonb` | Extensible metadata |

### Skill Record (procedural.py)

| Field | Type | Description |
|-------|------|-------------|
| `skill_id` | `str` | Unique identifier |
| `name` | `str` | Human-readable name |
| `description` | `str` | What the skill does |
| `trigger_patterns` | `list[str]` | Situations that activate this skill |
| `graph_definition` | `dict` | Serialized LangGraph subgraph |
| `embedding` | `vector` | For similarity-based recall |
| `invocation_count` | `int` | Usage tracking |
| `success_score` | `float` | Performance metric |
| `created_at` | `timestamp` | When crystallized |

## API Request/Response Models

### AgentMessageRequest
```python
class AgentMessageRequest(BaseModel):
    message: str
    session_id: str | None = None
    thread_id: str | None = None
```

### PendingApproval
```python
class PendingApproval:
    thread_id: str
    tool_name: str
    tool_args: dict
    risk_level: RiskLevel
    summary: str
    requested_at: float  # monotonic timestamp
    timeout_seconds: float
    auto_resolve: bool  # True=approve, False=deny on timeout
```

### RiskLevel
```python
class RiskLevel(Enum):
    LOW = "low"          # 30s timeout, auto-approve
    MEDIUM = "medium"    # 120s timeout, auto-deny
    HIGH = "high"        # 300s timeout, auto-deny
    CRITICAL = "critical"  # 600s timeout, auto-deny
```

### ModelCapabilityVector
```python
@dataclass
class ModelCapabilityVector:
    model_id: str
    provider: str
    reasoning: float      # 0-1
    coding: float         # 0-1
    speed: float          # 0-1
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_window: int
    supports_tools: bool
    supports_vision: bool
```

## Dashboard TypeScript Types

### Core Types (dashboard/src/types/index.ts)

```typescript
interface Agent {
  id: string; name: string; role: AgentRole;
  status: AgentStatus; progress: number; load: number;
  successRate: number; lastActive: string;
}

interface MemoryNode {
  id: string; type: MemoryNodeType; label: string;
  content?: string; timestamp: string;
  relevance?: number; strength?: number;
  connections: string[];
}

interface DashboardSnapshot {
  agents: Agent[]; memory: MemoryGraphData;
  approvals: PendingApproval[]; mcpServers: MCPServer[];
  costs: CostData; health: HealthStatus;
}
```

## Database Schema

### PostgreSQL Tables
Managed via Alembic migrations in `supernova/alembic/versions/`:

1. **`23aa65fd8071_initial_schema.py`** — Core tables: semantic_memories, procedural_skills, sessions
2. **`b7c3e9f12a45_audit_logs.py`** — Audit log table for compliance tracking

### Neo4j Graph Schema
Managed by Graphiti:
- **Nodes**: Episode, Entity, Concept
- **Relationships**: HAPPENED_BEFORE, RELATES_TO, PART_OF (temporal edges)

### Redis Key Patterns
| Pattern | Purpose | TTL |
|---------|---------|-----|
| `wm:{session_id}` | Working memory (msgpack) | Session-based |
| `cost:{model}:{date}` | Daily cost tracking | 30 days |
| `embed_cache:{hash}` | Embedding cache | 7 days |

---

## Database Schema (Alembic Migrations)

Two migrations in `supernova/alembic/versions/`:

### Migration 1: `23aa65fd8071_initial_schema.py`

**Extensions**: `vector` (pgvector), `pg_trgm` (trigram similarity)

#### `semantic_memories`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK, `gen_random_uuid()` |
| `user_id` | VARCHAR(255) | Indexed, scopes queries per user |
| `content` | TEXT | Full-text search (GIN `to_tsvector`) |
| `embedding` | vector(1536) | HNSW index (m=16, ef_construction=64, cosine) |
| `category` | VARCHAR(100) | Indexed; composite index with importance |
| `confidence` | FLOAT | Default 0.5 |
| `importance` | FLOAT | Default 0.5, DESC index for priority retrieval |
| `tags` | TEXT[] | ARRAY, default `{}` |
| `source` | VARCHAR(500) | |
| `access_count` | INTEGER | Default 0 |
| `created_at` | TIMESTAMPTZ | `now()` |
| `updated_at` | TIMESTAMPTZ | `now()` |
| `last_accessed_at` | TIMESTAMPTZ | DESC NULLS LAST index (LRU eviction) |

#### `procedural_memories`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK, `gen_random_uuid()` |
| `name` | VARCHAR(255) | UNIQUE, indexed |
| `description` | TEXT | |
| `trigger_conditions` | JSONB | GIN index for JSONB queries |
| `compiled_graph_bytes` | BYTEA | Serialized LangGraph subgraph |
| `trigger_embedding` | vector(1536) | HNSW index (m=16, ef_construction=64, cosine) |
| `invocation_count` | INTEGER | DESC index |
| `avg_performance_score` | FLOAT | Default 0.5 |
| `success_count` | INTEGER | Default 0 |
| `failure_count` | INTEGER | Default 0 |
| `is_active` | BOOLEAN | Partial index (`WHERE is_active = true`) |
| `created_at` | TIMESTAMPTZ | `now()` |
| `updated_at` | TIMESTAMPTZ | `now()` |
| `last_invoked_at` | TIMESTAMPTZ | |

#### `checkpoints` (LangGraph state persistence)

| Column | Type | Notes |
|--------|------|-------|
| `thread_id` | VARCHAR(255) | PK (composite), indexed |
| `checkpoint_ns` | VARCHAR(255) | PK (composite), default `''` |
| `checkpoint_id` | VARCHAR(255) | PK (composite) |
| `parent_checkpoint_id` | VARCHAR(255) | Nullable |
| `type` | VARCHAR(50) | |
| `checkpoint` | JSONB | Serialized graph state |
| `metadata` | JSONB | Default `{}` |
| `created_at` | TIMESTAMPTZ | DESC index |

#### `audit_log` (initial)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK, `gen_random_uuid()` |
| `timestamp` | TIMESTAMPTZ | DESC index |
| `action` | VARCHAR(100) | Indexed |
| `actor` | VARCHAR(255) | Indexed |
| `resource_type` | VARCHAR(100) | |
| `resource_id` | VARCHAR(255) | |
| `details` | JSONB | Default `{}` |
| `ip_address` | VARCHAR(45) | |
| `user_agent` | VARCHAR(500) | |
| `correlation_id` | VARCHAR(255) | Indexed |

### Migration 2: `b7c3e9f12a45_audit_logs.py`

Adds a separate `audit_logs` table (distinct from `audit_log` above):

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGINT | PK, autoincrement |
| `timestamp` | TIMESTAMPTZ | Indexed, `now()` |
| `user_id` | TEXT | Indexed |
| `action` | TEXT | Indexed |
| `resource` | TEXT | |
| `details` | JSON | |
| `ip_address` | TEXT | |

> **Note**: Two audit tables exist — `audit_log` (UUID-keyed, from initial schema) and `audit_logs` (BIGINT-keyed, from migration 2). The latter is the active table used by `infrastructure/security/audit.py`.
