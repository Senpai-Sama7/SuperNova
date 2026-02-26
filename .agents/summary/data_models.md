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
