# SuperNova Architecture

## High-Level Component Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│  Authentication  │───▶│  Orchestrator   │
│  (FastAPI/HTTP) │    │   & Rate Limit   │    │   (Core Logic)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       ▼                                 ▼                                 ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │  Agent Manager  │              │ Memory System   │              │  LLM Interface  │
              │ (Multi-Agent)   │              │ (Neo4j-backed)  │              │ (OpenAI/Claude) │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
                       │                                │                                │
                       ▼                                ▼                                ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │ Circuit Breaker │              │ Retrieval Cache │              │ Token Tracking  │
              │ & Approval Gate │              │ (Redis/Memory)  │              │ & Cost Control  │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
```

## Request Flow

1. **API Gateway** → Receives HTTP requests, validates format
2. **Authentication** → Verifies user tokens, applies rate limits
3. **Orchestrator** → Routes requests to appropriate agents
4. **Agent Manager** → Selects and coordinates specialized agents
5. **Memory System** → Retrieves relevant context using weighted scoring
6. **LLM Interface** → Processes requests with context injection
7. **Circuit Breaker** → Monitors failures, applies approval gates
8. **Response** → Returns structured results with metadata

## Key Design Decisions

### Local-First Architecture
- All user data stored locally (Neo4j + Redis)
- No cloud dependencies for core functionality
- Export/import for data portability (GDPR compliance)

### Approval-Gated Operations
- High-risk actions require explicit user confirmation
- Circuit breakers prevent runaway operations
- Audit trail for all system modifications

### Multi-Agent Coordination
- Specialized agents for different domains (memory, reasoning, tools)
- Shared working memory for session state
- Hierarchical task delegation with result aggregation

### Memory-Centric Design
- All interactions stored as episodic memories
- Semantic consolidation reduces noise over time
- Weighted retrieval: relevance + recency + salience + type

## Directory Structure

```
supernova/
├── api/                    # FastAPI endpoints and middleware
├── core/
│   ├── agent/             # Agent implementations and coordination
│   ├── memory/            # Memory storage, retrieval, consolidation
│   ├── orchestrator/      # Request routing and workflow management
│   ├── data/              # Data portability (export/import/delete)
│   └── llm/               # LLM interface and prompt management
├── infrastructure/
│   ├── storage/           # Neo4j, Redis, file system adapters
│   ├── monitoring/        # Metrics, logging, health checks
│   └── security/          # Authentication, rate limiting, validation
└── config/                # Environment-specific configurations
```

## Scalability Considerations

- **Horizontal**: Multiple agent instances with shared memory
- **Vertical**: Memory consolidation and pruning for large datasets
- **Caching**: Redis for hot paths, Neo4j for persistent storage
- **Monitoring**: Structured logging with performance metrics

## Security Model

- **Authentication**: JWT tokens with configurable expiration
- **Authorization**: Role-based access to agent capabilities
- **Data Protection**: Local storage with optional encryption
- **Audit Trail**: All operations logged with user attribution