# SuperNova — Interfaces & APIs

## HTTP API (FastAPI)

Base URL: `http://localhost:8000/api/v1`

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness/readiness with backend checks (Postgres, Redis, Neo4j) |

### Agent
| Method | Path | Description |
|--------|------|-------------|
| POST | `/agent/message` | Send message to agent (new or existing session) |

**Request body** (`AgentMessageRequest`):
```json
{
  "message": "string",
  "session_id": "string (optional)",
  "thread_id": "string (optional)"
}
```

### Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/snapshot` | Full dashboard state (agents, memory, approvals, MCP, costs, health) |
| POST | `/dashboard/approvals/{approval_id}/resolve` | Approve/deny pending tool execution |

### Onboarding
| Method | Path | Description |
|--------|------|-------------|
| GET | `/onboarding/status` | First-run detection, setup state |
| POST | `/onboarding/validate-key` | Validate LLM provider API key |
| GET | `/onboarding/cost-estimate` | Monthly cost projections per model |
| POST | `/onboarding/complete` | Finalize setup configuration |

### MCP
| Method | Path | Description |
|--------|------|-------------|
| GET | `/mcp/servers` | List MCP server status |
| GET | `/mcp/tools` | List available MCP tools |
| POST | `/mcp/tools/{name}/call` | Execute MCP tool |
| GET | `/mcp/skills` | List loaded skills |

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/token` | Generate JWT access token |

**JWT flow**: `create_access_token(data)` → `verify_token(token)` → `get_current_user(token)`

### WebSocket
| Path | Description |
|------|-------------|
| `ws://localhost:8000/ws/{session_id}` | Real-time agent event stream |

Events: `agent_status`, `tool_execution`, `approval_request`, `memory_update`, `health_alert`

---

## Internal Python Interfaces

### Memory Stores

```mermaid
classDiagram
    class EpisodicMemoryStore {
        +record_episode(session_id, content, metadata) → str
        +recall(query, session_id, limit) → list[dict]
        +get_recent(session_id, limit) → list[dict]
        +close()
    }
    
    class SemanticMemoryStore {
        +embed(text) → list[float]
        +search(query, category, limit, threshold) → list[dict]
        +upsert(content, category, metadata) → UUID
        +update_access_time(memory_id)
        +get_by_category(category, limit) → list[dict]
    }
    
    class WorkingMemoryStore {
        +get(session_id) → WorkingMemory
        +set(session_id, memory, ttl)
        +delete(session_id)
        +exists(session_id) → bool
        +update_field(session_id, field, value)
        +append_to_field(session_id, field, value)
    }
    
    class ProceduralMemoryStore {
        +initialize_schema()
        +learn_skill(name, description, trigger_patterns, graph_def) → str
        +recall_skill(situation, top_k) → SkillMatch
        +list_skills() → list[dict]
        +update_skill_score(skill_id, delta)
    }
```

### Tool Registry

```mermaid
classDiagram
    class Capability {
        <<Flag>>
        READ_FILES
        WRITE_FILES
        EXECUTE_CODE
        WEB_SEARCH
        WEB_BROWSE
        SEND_EMAIL
        SHELL_ACCESS
        EXTERNAL_API
    }
    
    class Tool {
        +name: str
        +description: str
        +function: Callable
        +schema: dict
        +required_capabilities: Capability
        +risk_level: RiskLevel
    }
    
    class ToolRegistry {
        +register(tool: Tool)
        +execute(name, args, session_capabilities) → Any
        +get_tool_schemas(session_capabilities) → list[dict]
        +get_tool(name) → Tool
    }
```

### Model Router

```mermaid
classDiagram
    class DynamicModelRouter {
        +start()
        +stop()
        +route_task(messages, task_type, budget_remaining) → response
        +get_fleet_summary() → list[dict]
    }
    
    class ModelCapabilityVector {
        +model_id: str
        +provider: str
        +reasoning: float
        +coding: float
        +speed: float
        +cost_per_1k_input: float
        +cost_per_1k_output: float
        +context_window: int
        +capability_array() → list[float]
        +expected_cost(input_tokens, output_tokens) → float
    }
    
    class TaskRequirementVector {
        +task_type: str
        +min_reasoning: float
        +min_coding: float
        +max_latency_ms: float
        +max_cost: float
        +min_context: int
        +as_array() → list[float]
    }
```

### Interrupt Coordinator

```mermaid
sequenceDiagram
    participant Agent as Cognitive Loop
    participant IC as InterruptCoordinator
    participant WS as WebSocket
    participant User as Dashboard User
    
    Agent->>IC: request_approval(tool_name, args, risk_level)
    IC->>WS: notify_websocket(pending_approval)
    IC->>IC: notify_os(desktop notification)
    
    alt User approves within timeout
        User->>IC: submit_decision(thread_id, approved=true)
        IC-->>Agent: ApprovalResult(approved=True)
    else Timeout
        IC-->>Agent: ApprovalResult(approved=auto_resolve)
    end
```

### Configuration

```mermaid
classDiagram
    class Settings {
        +env: str
        +secret_key: str
        +debug: bool
        +database: DatabaseSettings
        +redis: RedisSettings
        +neo4j: Neo4jSettings
        +llm: LLMSettings
        +langfuse: LangfuseSettings
        +security: SecuritySettings
        +is_development: bool
        +is_production: bool
    }
    
    Settings --> DatabaseSettings
    Settings --> RedisSettings
    Settings --> Neo4jSettings
```

Access via: `from supernova.config import get_settings; settings = get_settings()`
