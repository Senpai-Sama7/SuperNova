# SuperNova Documentation Index

> **For AI Assistants**: This file is your primary entry point. It contains enough metadata to determine which documentation file has the detailed information you need. Load this file first, then selectively load specific files as needed.

## Quick Reference

| Question Type | Consult |
|--------------|---------|
| "How is the project structured?" | `codebase_info.md` |
| "How does the agent work?" | `architecture.md`, `workflows.md` |
| "What components exist?" | `components.md` |
| "What APIs are available?" | `interfaces.md` |
| "What data types are used?" | `data_models.md` |
| "How do things flow end-to-end?" | `workflows.md` |
| "What dependencies are needed?" | `dependencies.md` |
| "What needs improvement?" | `review_notes.md` |

## File Summaries

### codebase_info.md
Basic project identity, metrics, language breakdown, and top-level directory structure. **Use when**: you need project name, version, file counts, or a quick structural overview.

### architecture.md
System architecture with Mermaid diagrams showing the cognitive loop, layer separation, design principles, and state management. **Use when**: you need to understand how the system is designed, why architectural decisions were made, or how layers interact.

### components.md
Detailed reference for every module, class, and file in the project — organized by package. Covers root-level modules (loop.py, context_assembly.py, etc.), all supernova/ subpackages, and the React dashboard. **Use when**: you need to find a specific file, understand what a module does, or see the full component inventory.

### interfaces.md
All HTTP API endpoints, WebSocket events, and internal Python interfaces with Mermaid class/sequence diagrams. Covers memory stores, tool registry, model router, interrupt coordinator, and configuration. **Use when**: you need API signatures, endpoint paths, or interface contracts.

### data_models.md
All data structures: AgentState TypedDict, WorkingMemory dataclass, memory records, API request/response models, database schemas, and TypeScript types. **Use when**: you need field definitions, type information, or database schema details.

### workflows.md
8 key workflows with Mermaid sequence/flowchart/state/gantt diagrams: message processing, skill crystallization, context assembly, HITL approval, model routing, worker scheduling, backup/recovery, and dashboard data flow. **Use when**: you need to understand how processes work end-to-end.

### dependencies.md
Complete dependency inventory: Python runtime/dev packages, frontend npm packages, infrastructure services (Docker Compose), and external API providers. **Use when**: you need to add dependencies, understand the tech stack, or set up the environment.

### review_notes.md
Documentation quality review: consistency issues, completeness gaps, and improvement recommendations. **Use when**: you want to know what's missing or needs attention.

## Cross-References

- **Cognitive Loop**: `architecture.md` (design) → `components.md` (loop.py details) → `workflows.md` (message processing flow) → `data_models.md` (AgentState)
- **Memory System**: `architecture.md` (4 memory types) → `components.md` (store implementations) → `interfaces.md` (store APIs) → `data_models.md` (record schemas)
- **Tool Execution**: `components.md` (registry + builtins) → `interfaces.md` (Capability flags) → `workflows.md` (HITL flow) → `data_models.md` (RiskLevel)
- **Dashboard**: `components.md` (React components) → `interfaces.md` (HTTP/WS APIs) → `data_models.md` (TypeScript types) → `workflows.md` (data flow)
- **Deployment**: `dependencies.md` (infrastructure services) → `components.md` (DEPLOYMENT.conf) → `workflows.md` (worker schedule)

## Root-Level Documentation

These files live in the project root (outside `.agents/summary/`) and provide additional context:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Consolidated AI assistant reference (full project context) |
| `README.md` | Project overview, quick start, architecture diagram |
| `CONTRIBUTING.md` | Development setup, code style, testing, contribution guide |
| `SYSTEM_RELATION_GRAPH.md` | Architecture knowledge graph with Mermaid entity-relationship diagrams |
| `PROGRESS_TRACKER.md` | 16-phase build specification and progress |
| `DEPLOYMENT.conf` | Production deployment: systemd units, Dockerfile, Nginx config |
| `mcp_and_skills/MCP_SERVERS.md` | MCP server inventory and configuration |
| `mcp_and_skills/MCP_INTEGRATION_SUMMARY.md` | MCP integration architecture |
| `mcp_and_skills/MCP_QUICK_REFERENCE.md` | MCP quick reference for tool usage |
