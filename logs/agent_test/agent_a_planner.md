--- AGENT REPORT ---
AGENT: A
ROLE: Planner
TASK: Phase 10 Task Breakdown
START: 2026-02-26T12:42:02-06:00
STATUS: SUCCESS

## Findings

### Phase 10 Overview
**Phase Objective:** Wire nova-dashboard.jsx to real backend via WebSocket and REST API.
**Estimated Duration:** 1 session
**Completion Criteria:** Dashboard displays real-time data; no simulation mode.

### Task 10.1: Dashboard Backend Integration
**Context:** Connect React dashboard to FastAPI backend
**Dependencies:** Task 6.3 (FastAPI gateway), Task 9.1 (integration tests)

#### 10.1.1 Create `useNovaRealtime()` hook replacing simulation
- **Files to modify:** `/dashboard/src/hooks/useNovaRealtime.ts`
- **Acceptance criteria:** Hook connects to `/agent/stream/{session_id}` WebSocket; receives real events
- **Complexity:** M (Medium)
- **Implementation steps:**
  1. Remove simulation logic from existing hook
  2. Add WebSocket connection to `ws://localhost:8000/agent/stream/{session_id}`
  3. Implement JWT token authentication via query parameter
  4. Handle incoming event types: token, tool_start, tool_result, done, approval_request
  5. Update state management to use real data instead of mock data

#### 10.1.2 Implement WebSocket reconnection with exponential backoff
- **Files to modify:** `/dashboard/src/hooks/useNovaRealtime.ts`
- **Acceptance criteria:** On disconnect: retries with backoff (1s, 2s, 4s, 8s, 16s); max 5 attempts
- **Complexity:** M (Medium)
- **Implementation steps:**
  1. Add reconnection state management (attempt count, backoff timer)
  2. Implement exponential backoff algorithm
  3. Add connection state tracking (connecting, connected, disconnected, failed)
  4. Handle WebSocket close events and trigger reconnection
  5. Reset attempt count on successful connection

#### 10.1.3 Integrate dashboard API endpoints
- **Files to modify:** `/dashboard/src/NovaDashboard.tsx`, `/dashboard/src/hooks/useNovaRealtime.ts`
- **Acceptance criteria:** Fetches from `/memory/semantic`, `/memory/procedural`, `/admin/fleet`; displays real data
- **Complexity:** L (Large)
- **Implementation steps:**
  1. Replace mock data fetching with real API calls
  2. Add HTTP client configuration with JWT authentication
  3. Implement data fetching for semantic memories endpoint
  4. Implement data fetching for procedural memories endpoint
  5. Implement data fetching for fleet summary endpoint
  6. Update component state to use real API responses
  7. Add error handling for API failures

#### 10.1.4 Add connection states (connecting, connected, error)
- **Files to modify:** `/dashboard/src/NovaDashboard.tsx`, `/dashboard/src/components/ui/StatusIndicator.tsx`
- **Acceptance criteria:** UI shows spinner while connecting; error message on failure; retry button
- **Complexity:** S (Small)
- **Implementation steps:**
  1. Add connection status component to header
  2. Display loading spinner during connection attempts
  3. Show error messages with retry button on connection failure
  4. Add visual indicators for connection state (green=connected, yellow=connecting, red=error)

### Task 10.2: MCP Dashboard Integration
**Context:** Dashboard UI for MCP server management and skill activation
**Dependencies:** Task 6.4 (MCP API endpoints), Task 10.1 (Dashboard real-time)

#### 10.2.1 Add MCP servers panel to dashboard
- **Files to modify:** `/dashboard/src/NovaDashboard.tsx`, `/dashboard/src/components/cards/MCPServerCard.tsx`
- **Acceptance criteria:** Displays all MCP servers with health indicators; shows tool count per server
- **Complexity:** M (Medium)
- **Implementation steps:**
  1. Create MCPServerCard component
  2. Add MCP servers tab to main navigation
  3. Fetch server list from `/mcp/servers` endpoint
  4. Display server name, status, health indicator, and tool count
  5. Add refresh functionality for server status

#### 10.2.2 Add MCP tool explorer
- **Files to modify:** `/dashboard/src/components/cards/MCPToolCard.tsx`, `/dashboard/src/NovaDashboard.tsx`
- **Acceptance criteria:** Lists all available MCP tools; shows descriptions and parameters; allows testing
- **Complexity:** L (Large)
- **Implementation steps:**
  1. Create MCPToolCard component with tool details
  2. Fetch tools from `/mcp/tools` endpoint
  3. Display tool name, description, parameters, and server source
  4. Add tool testing interface with parameter input
  5. Implement tool execution via `/mcp/tools/{tool_name}` endpoint
  6. Show execution results and error handling

#### 10.2.3 Add skill activation UI
- **Files to modify:** `/dashboard/src/components/cards/SkillCard.tsx`, `/dashboard/src/NovaDashboard.tsx`
- **Acceptance criteria:** Lists available skills; toggle to activate/deactivate; shows active skills
- **Complexity:** M (Medium)
- **Implementation steps:**
  1. Create SkillCard component
  2. Fetch skills from `/skills` endpoint
  3. Display skill name, description, and activation status
  4. Add toggle switches for skill activation/deactivation
  5. Implement activation via `/skills/{skill_name}/activate` endpoint
  6. Show visual indicators for active skills

#### 10.2.4 Add MCP execution monitoring
- **Files to modify:** `/dashboard/src/components/charts/MCPExecutionChart.tsx`, `/dashboard/src/NovaDashboard.tsx`
- **Acceptance criteria:** Real-time display of MCP tool calls; latency metrics; error tracking
- **Complexity:** L (Large)
- **Implementation steps:**
  1. Create MCPExecutionChart component
  2. Listen for MCP tool execution events via WebSocket
  3. Track execution latency and success/failure rates
  4. Display real-time metrics in chart format
  5. Add filtering by server and tool type
  6. Implement error log display

#### 10.2.5 Integrate MCP events into cognitive loop visualization
- **Files to modify:** `/dashboard/src/components/charts/CognitiveCycleRing.tsx`
- **Acceptance criteria:** Shows when MCP tools are called during reasoning; displays tool results
- **Complexity:** M (Medium)
- **Implementation steps:**
  1. Extend CognitiveCycleRing to show MCP tool phases
  2. Add visual indicators for MCP tool execution in reasoning cycle
  3. Display tool names and execution status in cycle visualization
  4. Add hover tooltips showing tool results
  5. Integrate with existing cognitive loop state management

### Summary of Files to Modify:
1. `/dashboard/src/hooks/useNovaRealtime.ts` - Replace simulation with real WebSocket connection
2. `/dashboard/src/NovaDashboard.tsx` - Main dashboard component integration
3. `/dashboard/src/components/cards/MCPServerCard.tsx` - New component for MCP server display
4. `/dashboard/src/components/cards/MCPToolCard.tsx` - New component for MCP tool management
5. `/dashboard/src/components/cards/SkillCard.tsx` - New component for skill activation
6. `/dashboard/src/components/charts/MCPExecutionChart.tsx` - New component for MCP metrics
7. `/dashboard/src/components/charts/CognitiveCycleRing.tsx` - Extend for MCP integration
8. `/dashboard/src/components/ui/StatusIndicator.tsx` - New component for connection status

### Complexity Distribution:
- Small (S): 1 task
- Medium (M): 5 tasks  
- Large (L): 3 tasks

### Critical Dependencies:
- FastAPI backend must be running with all endpoints functional
- WebSocket streaming must be implemented and tested
- MCP API endpoints must be available and returning data
- JWT authentication must be working for API access

## Errors
None

END: 2026-02-26T12:42:56-06:00
--- END REPORT ---