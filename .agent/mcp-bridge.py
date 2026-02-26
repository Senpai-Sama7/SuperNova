import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# Adjust sys.path to find core modules
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_SERVERS_DIR = SCRIPT_DIR / "mcp-servers"
CORE_DIR = MCP_SERVERS_DIR / "core"
SAFETY_DIR = MCP_SERVERS_DIR / "safety-layer" / "src"

sys.path.insert(0, str(MCP_SERVERS_DIR))
sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(SAFETY_DIR))

# Import from the copied mcp-servers structure
try:
    from mcp_client import MCPClient
except ImportError:
    # If standard import fails, try to load relative to this script
    sys.path.insert(0, str(SCRIPT_DIR / "mcp-servers" / "client"))
    from mcp_client import MCPClient

async def call_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]):
    """Call a tool on a specific MCP server."""
    client = MCPClient()
    
    # Configure server path if needed
    server_map = {
        "code-intelligence": str(MCP_SERVERS_DIR / "code-intelligence" / "src" / "server.py"),
        "execution-engine": str(MCP_SERVERS_DIR / "execution-engine" / "src" / "server.py"),
        "version-control": str(MCP_SERVERS_DIR / "version-control" / "src" / "server.py"),
        "quality-assurance": str(MCP_SERVERS_DIR / "quality-assurance" / "src" / "server.py"),
        "knowledge-integration": str(MCP_SERVERS_DIR / "knowledge-integration" / "src" / "server.py"),
    }
    
    if server_name not in server_map:
        print(f"Error: Unknown server '{server_name}'")
        return
    
    # Update client config for this run
    from mcp_client import ServerConfig
    client.server_configs[server_name] = ServerConfig(
        name=server_name,
        command="python3",
        args=[server_map[server_name]]
    )
    
    try:
        await client.start_servers()
        result = await client.call_tool(server_name, tool_name, arguments)
        print(json.dumps(result, indent=2))
    finally:
        await client.stop_servers()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 mcp-bridge.py <server_name> <tool_name> [json_args]")
        sys.exit(1)
        
    server = sys.argv[1]
    tool = sys.argv[2]
    args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    
    asyncio.run(call_mcp_tool(server, tool, args))
