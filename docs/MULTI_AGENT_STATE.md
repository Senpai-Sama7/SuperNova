# Multi-Agent Shared State

## Overview

The `SharedState` model defines the data structure for coordinating state between multiple agents during collaborative task execution. This enables agents to share context, track progress, and coordinate their activities.

## Schema Fields

### Core Identification
- **conversation_id**: Unique identifier for the conversation session
- **user_message**: Original user message that initiated the task

### Execution Tracking  
- **plan**: Optional list of execution steps
- **execution_results**: Dictionary mapping step_id to execution results
- **critique**: Optional critique or feedback on execution
- **final_response**: Optional final response to be sent to user

### Context Management
- **memory_context**: List of retrieved memory context items
- **active_agents**: List of currently active agent names
- **metadata**: Dictionary for timestamps, token counts, and other metadata

## Agent Access Patterns

### Read Access
All agents can read the full shared state to understand:
- Current execution context
- Previous step results
- Active collaborators
- Available memory context

### Write Access
Agents should follow these patterns:

**Planner Agent**:
- Writes to `plan` field
- Updates `metadata` with planning timestamps

**Executor Agent**:
- Writes to `execution_results` with step outcomes
- Updates `active_agents` when starting/finishing work
- Updates `metadata` with execution metrics

**Critic Agent**:
- Writes to `critique` field
- May update `plan` based on critique

**Response Agent**:
- Writes to `final_response` field
- Updates `metadata` with completion timestamp

## Conflict Resolution

### Concurrent Updates
- Use optimistic locking with version numbers in metadata
- Last writer wins for single-value fields
- Append-only for list fields where possible

### Field Ownership
- `plan`: Owned by planner, others read-only
- `execution_results`: Append-only, keyed by step_id
- `critique`: Owned by critic agent
- `final_response`: Owned by response agent
- `active_agents`: All agents can add/remove themselves
- `metadata`: Shared, use prefixed keys (e.g., "planner_start_time")

### State Transitions
1. **Planning**: Planner populates `plan` and `metadata`
2. **Execution**: Executors update `execution_results` and `active_agents`
3. **Critique**: Critic reviews and updates `critique`
4. **Response**: Response agent generates `final_response`

## Usage Example

```python
from supernova.core.agent.shared_state import SharedState

# Initialize shared state
state = SharedState(
    conversation_id="conv_123",
    user_message="Deploy the web application",
    metadata={"created_at": "2024-01-01T10:00:00Z"}
)

# Planner updates
state.plan = ["check_dependencies", "build_app", "deploy_app"]
state.metadata["planner_completed"] = "2024-01-01T10:01:00Z"

# Executor updates
state.execution_results["check_dependencies"] = "All dependencies satisfied"
state.active_agents.append("executor_1")

# Final response
state.final_response = "Application deployed successfully"
```