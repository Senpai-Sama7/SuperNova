# Memory System Schema

## Memory Types

SuperNova implements four distinct memory types based on cognitive science:

### Episodic Memory
- **Purpose**: Stores specific events and experiences
- **Content**: User interactions, agent decisions, tool results
- **Retention**: Long-term with gradual decay
- **Example**: "User asked about Python debugging at 2024-01-15 14:30"

### Semantic Memory
- **Purpose**: Stores factual knowledge and concepts
- **Content**: Learned facts, consolidated insights, domain knowledge
- **Retention**: Permanent with reinforcement
- **Example**: "Python uses indentation for code blocks"

### Procedural Memory
- **Purpose**: Stores learned skills and procedures
- **Content**: Successful workflows, tool usage patterns, problem-solving steps
- **Retention**: Strengthened through repetition
- **Example**: "To debug Python: 1) Check syntax, 2) Add print statements, 3) Use debugger"

### Working Memory
- **Purpose**: Temporary session state
- **Content**: Current goals, active plans, attention stack
- **Retention**: Session-scoped, cleared on completion
- **Example**: "Current goal: Fix authentication bug, Step 2/5: Check database connection"

## Storage Format

### MemoryItem Structure
```python
@dataclass
class MemoryItem:
    id: str                    # Unique identifier
    content: str               # Raw text content
    memory_type: str           # episodic|semantic|procedural|working
    relevance_score: float     # Cosine similarity (0-1)
    recency_score: float       # Time decay weight (0-1)
    composite_score: float     # Final ranking score
    salience_score: float      # Emotional importance (-1 to 1)
    metadata: Dict[str, Any]   # Timestamps, tags, source info
    retrieved_at: float        # Unix timestamp of retrieval
```

### Neo4j Schema
```cypher
// Memory nodes
CREATE (m:Memory {
    id: string,
    content: string,
    memory_type: string,
    created_at: timestamp,
    last_accessed: timestamp,
    salience_score: float,
    importance: float
})

// User relationships
CREATE (u:User)-[:OWNS]->(m:Memory)

// Memory associations
CREATE (m1:Memory)-[:RELATES_TO {strength: float}]->(m2:Memory)
```

## Retrieval Algorithm

### Weighted Scoring Formula
```
composite_score = α·relevance + β·recency + γ·type_weight + δ·salience

Where:
- α = 0.4 (relevance weight)
- β = 0.3 (recency weight) 
- γ = 0.2 (type preference weight)
- δ = 0.1 (salience weight)
```

### Scoring Components

1. **Relevance Score**: Cosine similarity between query and memory content
2. **Recency Score**: Exponential decay based on age: `exp(-λ * age_hours)`
3. **Type Weight**: Priority multiplier (procedural=1.2, semantic=1.0, episodic=0.8)
4. **Salience Score**: Emotional/importance weighting from user feedback

### Retrieval Process
1. **Query Expansion**: Add context from working memory
2. **Multi-Store Search**: Parallel search across all memory types
3. **Score Calculation**: Apply weighted formula to each result
4. **Ranking**: Sort by composite score, return top-k
5. **Cache Update**: Store results in Redis with TTL

## Consolidation Lifecycle

### Automatic Consolidation
- **Trigger**: Every 24 hours or 1000 new memories
- **Process**: Cluster similar episodic memories → summarize → store as semantic
- **Threshold**: Cosine similarity > 0.85 for clustering
- **Retention**: Original episodic memories marked for pruning

### Pruning Strategy
- **Working Memory**: Cleared after session timeout (30 minutes)
- **Episodic Memory**: Pruned after 90 days if not accessed
- **Semantic Memory**: Permanent unless explicitly deleted
- **Procedural Memory**: Strengthened by usage, weakened by disuse

### Memory Reinforcement
- **Access Boost**: Recently retrieved memories get salience +0.1
- **Success Boost**: Memories leading to successful outcomes get +0.2
- **User Feedback**: Explicit thumbs up/down adjusts salience ±0.3