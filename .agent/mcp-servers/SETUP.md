# MCP Server Setup Guide

## Quick Setup

### Option 1: Copy to VS Code / Cursor / Windsurf

```bash
# For VS Code with Claude extension
cp ~/mcp-servers/config/mcp-settings.json ~/.vscode/mcp-settings.json

# For Cursor
cp ~/mcp-servers/config/cursor-mcp.json ~/.cursor/mcp.json

# For Claude Desktop (if available)
cp ~/mcp-servers/config/claude-mcp.json ~/.config/claude/mcp.json
```

### Option 2: Manual Configuration

#### VS Code (with Claude or Cline extension)

Open VS Code settings (Cmd/Ctrl + Shift + P → "Preferences: Open User Settings (JSON)") and add:

```json
{
  "mcp": {
    "servers": {
      "code-intelligence": {
        "type": "stdio",
        "command": "python3",
        "args": ["/home/donovan/mcp-servers/code-intelligence/src/server.py"],
        "env": {
          "PYTHONPATH": "/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
        }
      },
      "execution-engine": {
        "type": "stdio",
        "command": "python3",
        "args": ["/home/donovan/mcp-servers/execution-engine/src/server.py"],
        "env": {
          "PYTHONPATH": "/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
        }
      },
      "version-control": {
        "type": "stdio",
        "command": "python3",
        "args": ["/home/donovan/mcp-servers/version-control/src/server.py"],
        "env": {
          "PYTHONPATH": "/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
        }
      },
      "quality-assurance": {
        "type": "stdio",
        "command": "python3",
        "args": ["/home/donovan/mcp-servers/quality-assurance/src/server.py"],
        "env": {
          "PYTHONPATH": "/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
        }
      },
      "knowledge-integration": {
        "type": "stdio",
        "command": "python3",
        "args": ["/home/donovan/mcp-servers/knowledge-integration/src/server.py"],
        "env": {
          "PYTHONPATH": "/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
        }
      }
    }
  }
}
```

#### Cursor

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP"
3. Click "Edit in settings.json"
4. Paste the contents of `~/mcp-servers/config/cursor-mcp.json`

#### Kimi CLI

For Kimi CLI, add to your `.kimi/settings.json`:

```json
{
  "mcpServers": {
    "code-intelligence": {
      "command": "python3",
      "args": ["/home/donovan/mcp-servers/code-intelligence/src/server.py"],
      "env": {
        "PYTHONPATH": "/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
      }
    }
    // ... add other servers
  }
}
```

## Verify Setup

### Test Individual Server

```bash
cd ~/mcp-servers

# Test code-intelligence
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python3 code-intelligence/src/server.py
```

### Test All Servers

```bash
cd ~/mcp-servers
./mcp-launcher.sh start

# In another terminal, check status
./mcp-launcher.sh status
```

## Troubleshooting

### "No MCP servers configured"

1. Check configuration file location for your editor
2. Verify paths are absolute (not relative)
3. Ensure PYTHONPATH includes all necessary directories

### "Module not found"

```bash
# Set PYTHONPATH explicitly
export PYTHONPATH="/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"

# Then run your editor from this shell
```

### "Permission denied"

```bash
chmod +x ~/mcp-servers/*/src/server.py
chmod +x ~/mcp-servers/mcp-launcher.sh
```

### Server crashes on start

Check logs:
```bash
cat ~/mcp-servers/logs/*.log
```

## Available Tools by Server

### code-intelligence
- `code/analyze_function` - Analyze function complexity and risks
- `code/find_references` - Find symbol usages
- `code/detect_code_smells` - Detect anti-patterns
- `code/calculate_complexity` - Calculate cyclomatic complexity
- `code/get_structure` - Get file structure
- `code/find_duplicates` - Find duplicate code
- `code/dependency_graph` - Build dependency graph

### execution-engine
- `execution/execute` - Execute commands safely
- `execution/execute_pipeline` - Execute command pipelines
- `execution/build` - Run builds
- `execution/test` - Run tests
- `execution/watch` - Watch files
- `execution/kill` - Kill processes
- `execution/get_status` - Get execution status

### version-control
- `git/status`, `git/diff`, `git/log` - Repository info
- `git/add`, `git/commit` - Change management
- `git/branch`, `git/checkout` - Branch operations
- `git/stash`, `git/blame` - Advanced git
- `checkpoint/*` - Lightweight snapshots

### quality-assurance
- `qa/security_scan` - Security scanning
- `qa/lint` - Code linting
- `qa/type_check` - Type checking
- `qa/coverage` - Coverage analysis
- `qa/dependency_audit` - CVE scanning
- `qa/complexity_report` - Complexity report

### knowledge-integration
- `docs/search`, `docs/fetch` - Documentation
- `db/schema`, `db/query` - Database access
- `db/analyze` - Query analysis
- `api/test`, `api/validate_schema` - API testing
- `web/search`, `web/fetch` - Web access
- `pattern/retrieve` - Code patterns

## Editor-Specific Locations

| Editor | Config Location |
|--------|----------------|
| VS Code | `~/.vscode/settings.json` or workspace `.vscode/settings.json` |
| Cursor | `~/.cursor/mcp.json` or `.cursor/mcp.json` (workspace) |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Claude Desktop | `~/.config/claude/mcp.json` |
| Kimi CLI | `~/.config/kimi/settings.json` |

## Next Steps

Once configured, your AI assistant can:

1. **Analyze code**: "Analyze the complexity of this function"
2. **Run tests**: "Run the test suite and check coverage"
3. **Security scan**: "Scan for security vulnerabilities"
4. **Git operations**: "Commit these changes with a semantic message"
5. **Database queries**: "Check the database schema for users table"

See `QUICKSTART.md` for example workflows!
