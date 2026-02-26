# SuperNova Agent Core: Skills & MCP Integration ✅

All materials from `mcp_and_skills` have been fully integrated into the SuperNova workspace.

## 🧠 Brain Structure

- **Skills Directory:** `.agent/skills/` (43 skills loaded)
- **MCP Servers:** `.agent/mcp-servers/` (5 custom servers with 100+ tools)
- **Tool Bridge:** `.agent/mcp-bridge.py` (Execute any MCP tool via command line)

## 🛠️ MCP Tool Access

You can invoke any of the integrated MCP tools using the following pattern:
`python3 .agent/mcp-bridge.py <server> <tool> '<args_json>'`

### Available Servers

- `code-intelligence`: Semantic analysis, AST parsing, complexity metrics.
- `execution-engine`: Safe command execution, build pipelines, test runners.
- `version-control`: Advanced Git operations, lightweight checkpoints.
- `quality-assurance`: Security scans, linting, type-checking.
- `knowledge-integration`: Documentation search, DB introspection.

## 📚 Integrated Skills (Highlights)

The agent now has high-level expertise in:

- **Autonomous Agents:** `agent-cognitive-architecture`, `multi-agent-orchestration`
- **Quality & Security:** `hostile-auditor`, `security-engineering`, `test-driven-development`
- **Data & Docs:** `pdf`, `docx`, `pptx`, `xlsx`, `notion-*`
- **App Dev:** `android-app-dev`, `frontend-design`, `api-integration`
- **Operations:** `ci-cd-devops`, `observability-monitoring`

## 🚀 Getting Started

To verify the integration, run:

```bash
python3 .agent/mcp-bridge.py code-intelligence code/get_structure '{"file": "procedural.py"}'
```

All systems are operational. The Antigravity agent is now fully equipped with the SuperNova Power Suite.
