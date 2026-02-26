# Fix: "No MCP servers configured"

## Quick Fix

Your MCP servers are built and working, but your editor doesn't know about them yet.

## For Kimi CLI

```bash
# Create the config directory if it doesn't exist
mkdir -p ~/.config/kimi

# Copy the MCP configuration
cp ~/mcp-servers/mcp-workspace.json ~/.config/kimi/mcp-servers.json

# Verify
cat ~/.config/kimi/mcp-servers.json
```

## For Claude Desktop (if installed)

```bash
mkdir -p ~/.config/claude
cp ~/mcp-servers/mcp-workspace.json ~/.config/claude/mcp.json
```

## For VS Code

1. Open VS Code
2. Press `Ctrl/Cmd + Shift + P`
3. Type "Preferences: Open User Settings (JSON)"
4. Add this to your settings.json:

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

## Verify Servers Work

Test each server:

```bash
cd ~/mcp-servers

# Test code-intelligence
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 code-intelligence/src/server.py

# Test execution-engine  
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 execution-engine/src/server.py

# Test version-control
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 version-control/src/server.py

# Test quality-assurance
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 quality-assurance/src/server.py

# Test knowledge-integration
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 knowledge-integration/src/server.py
```

Each should output a JSON list of available tools.

## Alternative: Direct Launcher

If your editor doesn't support MCP yet, you can still use the servers directly:

```bash
cd ~/mcp-servers
./mcp-launcher.sh start

# Servers are now running and can be called via stdio
```

## What If It Still Doesn't Work?

### Check Python Path

```bash
export PYTHONPATH="/home/donovan/mcp-servers:/home/donovan/mcp-servers/core:/home/donovan/mcp-servers/safety-layer/src"
```

### Check File Permissions

```bash
chmod +x ~/mcp-servers/*/src/server.py
```

### Test Server Manually

```bash
cd ~/mcp-servers
python3 code-intelligence/src/server.py
# Type: {"jsonrpc":"2.0","id":1,"method":"initialize"}
# Press Enter
# Should see: {"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {...}}}
```

### Check Logs

```bash
cat ~/mcp-servers/logs/*.log
```

## Getting Help

See full documentation:
- `~/mcp-servers/SETUP.md` - Complete setup guide
- `~/mcp-servers/README.md` - Full documentation
- `~/mcp-servers/QUICKSTART.md` - Quick reference
