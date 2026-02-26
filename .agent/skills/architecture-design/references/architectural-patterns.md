# Architectural Patterns Reference

## Monolithic Architecture

### When to Use
- Small team (< 10 developers)
- Rapid prototyping/MVP
- Simple domain with low complexity
- Tight coupling requirements

### Characteristics
- Single codebase
- Single deployment unit
- Shared database
- In-process communication

### Patterns
```
┌─────────────────────────────────────┐
│           Monolith                  │
│  ┌─────────┐ ┌─────────┐ ┌───────┐  │
│  │  Auth   │ │ Payments│ │Orders │  │
│  └────┬────┘ └────┬────┘ └───┬───┘  │
│       └───────────┼──────────┘       │
│            ┌──────┴──────┐           │
│            │   Database  │           │
│            └─────────────┘           │
└─────────────────────────────────────┘
```

## Microservices Architecture

### When to Use
- Multiple teams (> 20 developers)
- Independent deploy requirements
- Different scaling needs per component
- Clear domain boundaries

### Characteristics
- Service per bounded context
- Independent databases
- Inter-service communication
- Polyglot persistence

### Service Communication

| Pattern | Sync/Async | Use Case |
|---------|-----------|----------|
| REST API | Sync | Simple queries, CRUD |
| gRPC | Sync | Internal service calls |
| Message Queue | Async | Event-driven, eventual consistency |
| Event Bus | Async | Broadcast, loose coupling |
| GraphQL Federation | Sync | Aggregated APIs |

### Patterns
```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Auth    │      │ Payments │      │  Orders  │
│ Service  │      │ Service  │      │ Service  │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │
     └─────────────────┼─────────────────┘
                       │
              ┌────────┴────────┐
              │   API Gateway   │
              └────────┬────────┘
                       │
                   ┌───┴───┐
                   │Client │
                   └───────┘
```

## Event-Driven Architecture

### When to Use
- Audit trails required
- Loose coupling critical
- Complex workflows
- Real-time processing

### Event Patterns

**Event Notification:**
```
Service A ──Event──→ Service B (reacts)
```

**Event-Carried State Transfer:**
```
Service A ──Full Data──→ Service B (updates local cache)
```

**Event Sourcing:**
```
Commands → Event Store → Projections → Read Models
```

### Saga Patterns

**Choreography:**
```
OrderService ──OrderCreated──→ PaymentService
                                   │
                                   ▼
                            InventoryService
                                   │
                                   ▼
                            ShippingService
```

**Orchestration:**
```
                    ┌──────────────┐
OrderService ──────→│  Orchestrator│
                    │   (Saga)     │
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    PaymentService InventoryService ShippingService
```

## Serverless Architecture

### When to Use
- Variable/unknown workloads
- Event processing
- Rapid scaling requirements
- Cost optimization (low baseline)

### Patterns

**Function as a Service:**
```
API Gateway → Lambda → DynamoDB
                │
                ├──→ SNS (async)
                └──→ S3 (file processing)
```

**Fat Lambda:**
- Single function handles multiple routes
- Reduced cold starts
- Simpler deployment

## Layered Architecture

### Standard Layers
```
┌─────────────────┐
│  Presentation   │  ← Controllers, Views, DTOs
├─────────────────┤
│   Application   │  ← Use Cases, Services
├─────────────────┤
│    Domain       │  ← Entities, Value Objects, Domain Services
├─────────────────┤
│ Infrastructure  │  ← Repositories, External APIs, DB
└─────────────────┘
```

### Dependency Rule
Dependencies point inward. Domain has no external dependencies.

## Hexagonal Architecture (Ports & Adapters)

### Structure
```
         ┌──────────────┐
         │   External   │
         │   Systems    │
         └──────┬───────┘
                │
    ┌───────────┴───────────┐
    │     Adapters          │
    │  (Driven/Driving)     │
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │      Application      │
    │       (Ports)         │
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │        Domain         │
    │     (Business Logic)  │
    └───────────────────────┘
```

## CQRS (Command Query Responsibility Segregation)

### When to Use
- Read/write load asymmetry
- Different data models for reads/writes
- Event sourcing
- Complex query requirements

### Pattern
```
Commands ──→ Command Handler ──→ Write Model ──→ Event Store
                                             │
                                             ▼
                                          Projector
                                             │
                                             ▼
Query ──→ Query Handler ──→ Read Model ←── Projection
```

## Decision Matrix

| Factor | Monolith | Microservices | Serverless |
|--------|----------|---------------|------------|
| Team Size | Small | Large | Any |
| Time to Market | Fast | Slower | Fast |
| Scalability | Vertical | Horizontal | Automatic |
| Complexity | Low | High | Medium |
| Operational Cost | Low | High | Variable |
| Debugging | Easy | Hard | Medium |
| Technology Diversity | Low | High | Medium |
