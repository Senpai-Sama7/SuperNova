# SuperNova — System Architecture

## Architectural Pattern

SuperNova implements a **cognitive architecture** inspired by human memory systems, built on LangGraph's stateful graph orchestration with PostgreSQL checkpointing for durable execution.

### High-Level Architecture

```mermaid
graph TB
    User([User Request]) --> Gateway[FastAPI Gateway<br/>api/gateway.py]
    Gateway --> Auth[JWT Auth<br/>api/auth.py]
    Gateway --> WS[WebSocket Broadcaster<br/>api/websockets.py]
    
    Gateway --> Loop[Cognitive Loop<br/>loop.py]
    
    subgraph "Cognitive Engine"
        Loop --> Perceive[1. PERCEIVE<br/>Restore checkpoint]
        Perceive --> Remember[2. REMEMBER<br/>Parallel memory retrieval]
        Remember --> Prime[3. PRIME<br/>Procedural skill check]
        Prime --> Assemble[4. ASSEMBLE<br/>Context window assembly]
        Assemble --> Reason[5. REASON<br/>LLM call via router]
        Reason --> Act[6. ACT<br/>Tool execution + HITL]
        Act --> Reflect[7. REFLECT<br/>Self-evaluation]
        Reflect --> Consolidate[8. CONSOLIDATE<br/>Memory write-back]
    end
    
    subgraph "Memory Layer"
        Episodic[(Neo4j/Graphiti<br/>Episodic Memory)]
        Semantic[(PostgreSQL/pgvector<br/>Semantic Memory)]
        Procedural[(PostgreSQL<br/>Procedural Memory)]
        Working[(Redis<br/>Working Memory)]
    end
    
    Remember --> Episodic
    Remember --> Semantic
    Prime --> Procedural
    Remember --> Working
    Consolidate --> Episodic
    Consolidate --> Working
    
    subgraph "Infrastructure"
        Router[Dynamic Model Router<br/>dynamic_router.py]
        Registry[Tool Registry<br/>tools/registry.py]
        Interrupts[Interrupt Coordinator<br/>interrupts.py]
        MCP[MCP Client<br/>mcp/client/]
    end
    
    Reason --> Router
    Act --> Registry
    Act --> Interrupts
    Act --> MCP
    
    subgraph "Background Workers (Celery)"
        Consolidation[Hourly: Memory consolidation]
        Heartbeat[15min: Health checks]
        Forgetting[Weekly: Forgetting curves]
        Crystallize[Daily: Skill crystallization]
        MCPMon[5min: MCP health monitor]
        Backup[Daily: Encrypted backup]
    end
    
    subgraph "Dashboard (React 19)"
        Dashboard[NovaDashboard.tsx]
        Dashboard --> Cards[Agent/Approval/MCP/Health Cards]
        Dashboard --> Charts[Cognitive Ring/Confidence/Sparkline]
        Dashboard --> ThreeD[3D Memory Visualization]
    end
    
    Dashboard -.->|HTTP polling + WS| Gateway
```

## Design Principles

1. **Durable Execution** — LangGraph + AsyncPostgresSaver checkpointing. Process crashes resume from the interrupted step.
2. **Positional Context Optimization** — Context window assembly following Liu et al. (2023) primacy/recency attention topology.
3. **Capability-Gated Security** — Tools declare required capabilities; execution validates at call time with HITL for high-risk operations.
4. **Self-Improvement** — SkillCrystallizationWorker extracts repeated tool-call patterns from Langfuse traces and compiles them into reusable LangGraph subgraphs.
5. **Observable by Default** — Every LLM call and tool execution traced in Langfuse with full I/O capture.

## Layer Separation

| Layer | Location | Responsibility |
|-------|----------|---------------|
| Cognitive Core | `loop.py`, `context_assembly.py`, `procedural.py`, `dynamic_router.py`, `interrupts.py` | Agent reasoning, memory retrieval, context assembly, model routing, safety |
| API | `supernova/api/` | HTTP/WS endpoints, auth, routing |
| Memory | `supernova/core/memory/` | Episodic, semantic, working memory stores |
| Infrastructure | `supernova/infrastructure/` | Storage, tools, security, observability, LLM cost control |
| Workers | `supernova/workers/` | Celery background tasks (consolidation, maintenance, monitoring) |
| MCP | `supernova/mcp/` | Model Context Protocol client and tool bridge |
| Skills | `supernova/skills/` | Skill file discovery, loading, hot-reload |
| Dashboard | `dashboard/src/` | React 19 monitoring UI with 3D visualizations |

## State Management

The agent's state is defined as `AgentState(TypedDict)` in `loop.py`:
- `messages`: Conversation history (Annotated with `operator.add` for immutable append)
- `session_id`, `thread_id`: Session tracking
- `memory_context`: Retrieved memories from all stores
- `active_plan`: Current execution plan
- `tool_calls_this_turn`: Safety counter (max 15 per turn)
- `reflection_critique`: Self-evaluation output
- `metadata`: Extensible metadata dict

All state transitions are pure functions returning dicts that merge into AgentState, making the graph fully checkpointable and unit-testable.
