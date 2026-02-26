#!/bin/bash
# MCP Servers Launcher
# Usage: ./mcp-launcher.sh [start|stop|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${SCRIPT_DIR}/core:${SCRIPT_DIR}/safety-layer/src:${PYTHONPATH}"

case "${1:-start}" in
    start)
        echo "Starting MCP Servers..."
        python3 -c "
import asyncio
import sys
sys.path.insert(0, '${SCRIPT_DIR}')
from client.mcp_client import MCPClient

async def main():
    client = MCPClient('${SCRIPT_DIR}/config/servers.json')
    await client.start_servers()
    print('Servers started. Press Ctrl+C to stop.')
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping servers...')
        await client.stop_servers()

asyncio.run(main())
"
        ;;
    stop)
        echo "Stopping MCP Servers..."
        pkill -f "mcp-.*server" 2>/dev/null || true
        echo "Servers stopped."
        ;;
    status)
        echo "MCP Server Status:"
        ps aux | grep -E "mcp-.*server" | grep -v grep || echo "No servers running"
        ;;
    *)
        echo "Usage: $0 [start|stop|status]"
        exit 1
        ;;
esac
