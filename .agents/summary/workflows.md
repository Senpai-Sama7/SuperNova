# SuperNova — Key Workflows

## 1. Agent Message Processing

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as FastAPI Gateway
    participant Auth as JWT Auth
    participant Graph as LangGraph
    participant Memory as Memory Stores
    participant Router as Model Router
    participant Tools as Tool Registry
    participant HITL as Interrupt Coordinator
    
    Client->>Gateway: POST /api/v1/agent/message
    Gateway->>Auth: verify_token()
    Auth-->>Gateway: user context
    
    Gateway->>Graph: invoke(AgentState)
    
    Note over Graph: 1. PERCEIVE — restore checkpoint
    Graph->>Memory: parallel retrieval
    Memory-->>Graph: episodic + semantic + working + procedural
    
    Note over Graph: 2-4. REMEMBER → PRIME → ASSEMBLE
    Graph->>Graph: assemble_context_window()
    
    Note over Graph: 5. REASON
    Graph->>Router: route_task(messages, task_type)
    Router-->>Graph: LLM response
    
    alt Has tool calls
        Note over Graph: 6. ACT
        Graph->>Tools: execute(tool_name, args)
        Tools->>HITL: request_approval (if risk > LOW)
        HITL-->>Tools: ApprovalResult
        Tools-->>Graph: tool result
        Graph->>Graph: route_after_reasoning → loop back to REASON
    end
    
    alt Should reflect
        Note over Graph: 7. REFLECT
        Graph->>Router: self-evaluation call
        Router-->>Graph: critique
    end
    
    Note over Graph: 8. CONSOLIDATE
    Graph->>Memory: write episodes + update working memory
    Graph-->>Gateway: final response
    Gateway-->>Client: JSON response
```

## 2. Skill Crystallization (Daily Worker)

```mermaid
flowchart TD
    A[Celery Beat: daily 2am] --> B[SkillCrystallizationWorker.run_crystallization_cycle]
    B --> C[Fetch high-scoring Langfuse traces]
    C --> D[Extract repeated tool-call patterns]
    D --> E{Pattern frequency ≥ threshold?}
    E -->|Yes| F[Compute pattern fingerprint]
    F --> G[Build LangGraph subgraph]
    G --> H[Store in ProceduralMemoryStore]
    H --> I[Skill available for PRIME phase]
    E -->|No| J[Skip — not yet crystallized]
```

## 3. Context Window Assembly

```mermaid
flowchart LR
    subgraph "Primacy Zone (high attention)"
        A[System prompt]
        B[Active plan]
        C[Procedural skill match]
    end
    
    subgraph "Middle Zone (degraded attention)"
        D[Semantic memories]
        E[Episodic context]
        F[Working memory]
    end
    
    subgraph "Recency Zone (high attention)"
        G[Recent conversation history]
        H[Current user message]
    end
    
    A --> D --> G
    
    style A fill:#2d5a2d
    style B fill:#2d5a2d
    style C fill:#2d5a2d
    style G fill:#2d5a2d
    style H fill:#2d5a2d
    style D fill:#5a3a2d
    style E fill:#5a3a2d
    style F fill:#5a3a2d
```

Token budget is allocated across zones. Important content placed in primacy/recency zones where transformer attention is strongest.

## 4. HITL Approval Flow

```mermaid
stateDiagram-v2
    [*] --> ToolCallDetected
    ToolCallDetected --> RiskAssessment
    
    RiskAssessment --> AutoApprove: LOW risk
    RiskAssessment --> PendingApproval: MEDIUM/HIGH/CRITICAL
    
    PendingApproval --> WaitingForDecision
    WaitingForDecision --> Approved: User approves
    WaitingForDecision --> Denied: User denies
    WaitingForDecision --> TimedOut: Timeout reached
    
    TimedOut --> AutoApprove: LOW (auto-approve)
    TimedOut --> AutoDeny: MEDIUM+ (auto-deny)
    
    AutoApprove --> ExecuteTool
    Approved --> ExecuteTool
    Denied --> SkipTool
    AutoDeny --> SkipTool
    
    ExecuteTool --> [*]
    SkipTool --> [*]
```

## 5. Model Routing Decision

```mermaid
flowchart TD
    A[Incoming task] --> B[Classify task type]
    B --> C[Build TaskRequirementVector]
    C --> D[Score each model]
    D --> E{Budget remaining?}
    E -->|Yes| F[Select highest-scoring feasible model]
    E -->|No| G[Find budget fallback]
    G --> H{Ollama available?}
    H -->|Yes| I[Route to local Ollama]
    H -->|No| J[Use cheapest cloud model]
    F --> K[Call model via LiteLLM]
    I --> K
    J --> K
    K --> L[Track cost + update EMA estimates]
```

## 6. Background Worker Schedule

```mermaid
gantt
    title Celery Beat Schedule (UTC)
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Every 5min
    MCP Health Check    :active, 00:00, 5m
    
    section Every 15min
    Heartbeat           :active, 00:00, 15m
    
    section Hourly
    Memory Consolidation :crit, 00:00, 60m
    
    section Daily
    Skill Crystallization :02:00, 30m
    Encrypted Backup      :02:30, 30m
    
    section Weekly
    Forgetting Curves     :03:00, 60m
```

## 7. Backup & Recovery

```mermaid
flowchart TD
    A[Daily 2:30am Celery task] --> B[BackupManager.create_backup]
    B --> C[pg_dump PostgreSQL]
    B --> D[Neo4j Cypher export]
    B --> E[Redis RDB snapshot]
    C & D & E --> F[Create tar archive]
    F --> G[Fernet encrypt]
    G --> H{S3 configured?}
    H -->|Yes| I[Upload to S3]
    H -->|No| J[Store locally]
    I & J --> K[Rotate old backups]
    K --> L[Verify backup integrity]
```

## 8. Dashboard Data Flow

```mermaid
flowchart LR
    subgraph Backend
        API[FastAPI /dashboard/snapshot]
        WS[WebSocket /ws/{session}]
    end
    
    subgraph Dashboard
        Hook[useNovaRealtime hook]
        State[React State]
        Cards[Card Components]
        Charts[Chart Components]
        ThreeD[3D Visualization]
    end
    
    API -->|HTTP poll 3s| Hook
    WS -->|Real-time events| Hook
    Hook --> State
    State --> Cards
    State --> Charts
    State --> ThreeD
```
