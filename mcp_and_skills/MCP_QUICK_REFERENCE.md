# MCP Quick Reference for kimi-cli

## All Configured Servers (17 total)

### Local Custom Servers
```
code-intelligence    execution-engine     version-control
quality-assurance    knowledge-integration android-app-builder
```

### Official Reference Servers
```
filesystem           memory               sequential-thinking
everything           fetch                git
time
```

### Browser & Automation
```
playwright           chrome-devtools
```

### Documentation & Knowledge
```
context7             context7-http
```

## Quick Commands

```bash
# List all servers
kimi mcp list

# Test a server
kimi mcp test filesystem

# Add stdio server
kimi mcp add --transport stdio myserver -- node myserver.js

# Add HTTP server
kimi mcp add --transport http myserver https://api.example.com/mcp

# Remove server
kimi mcp remove myserver

# View tools in session
/mcp
```

## Key Tools by Server

| Server | Key Tools |
|--------|-----------|
| `filesystem` | read_file, write_file, list_directory, search_files |
| `fetch` | fetch, fetch_html |
| `git` | git_status, git_log, git_diff |
| `memory` | create_entities, add_observations, read_graph |
| `time` | get_current_time, convert_time |
| `sequential-thinking` | sequentialthinking |
| `context7` | resolve-library-id, get-library-docs |
| `code-intelligence` | code/analyze_function, code/find_references |
| `execution-engine` | execution/execute, execution/build, execution/test |
| `version-control` | git/status, git/commit, checkpoint/create |
| `quality-assurance` | qa/security_scan, qa/lint, qa/coverage |
| `knowledge-integration` | docs/search, web/search, db/schema |

## Configuration Location

```
~/.kimi/mcp.json
~/.config/kimi/mcp-servers.json
```

## Testing

```bash
~/test-mcp-servers.sh
```

## Full Documentation

See: `~/MCP_INTEGRATION_SUMMARY.md`
