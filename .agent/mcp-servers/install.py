#!/usr/bin/env python3
"""
Installation script for MCP Servers

Sets up the MCP server ecosystem for agentic AI coding CLI.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_python_version() -> bool:
    """Check Python version compatibility."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies() -> bool:
    """Check if required dependencies are available."""
    deps_ok = True
    
    # Check git
    if shutil.which("git"):
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        print(f"✓ Git: {result.stdout.strip()}")
    else:
        print("⚠ Git not found (version-control server will be limited)")
    
    # Check curl
    if shutil.which("curl"):
        print("✓ curl (for API testing)")
    else:
        print("⚠ curl not found (knowledge-integration server will be limited)")
    
    return deps_ok


def setup_directories() -> None:
    """Create necessary directories."""
    base_path = Path(__file__).parent
    
    dirs_to_create = [
        base_path / "logs",
        base_path / "data",
        base_path / "cache",
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(exist_ok=True)
        print(f"✓ Created directory: {dir_path}")


def make_scripts_executable() -> None:
    """Make server scripts executable."""
    base_path = Path(__file__).parent
    
    servers = [
        "code-intelligence",
        "execution-engine", 
        "version-control",
        "quality-assurance",
        "knowledge-integration"
    ]
    
    for server in servers:
        script_path = base_path / server / "src" / "server.py"
        if script_path.exists():
            script_path.chmod(0o755)
            print(f"✓ Made executable: {script_path}")


def create_launcher_script() -> None:
    """Create a launcher script for easy server startup."""
    base_path = Path(__file__).parent
    
    launcher_content = """#!/bin/bash
# MCP Servers Launcher
# Usage: ./mcp-launcher.sh [start|stop|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

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
        print('\\nStopping servers...')
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
"""
    
    launcher_path = base_path / "mcp-launcher.sh"
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    launcher_path.chmod(0o755)
    print(f"✓ Created launcher: {launcher_path}")


def print_usage() -> None:
    """Print usage instructions."""
    print("""
🚀 MCP Servers Installation Complete!

Usage:
  1. Start all servers:
     ./mcp-launcher.sh start

  2. Stop all servers:
     ./mcp-launcher.sh stop

  3. Check status:
     ./mcp-launcher.sh status

  4. Use in Python:
     from client.mcp_client import MCPClient
     
     client = MCPClient()
     await client.start_servers()
     
     # Call a tool
     result = await client.call_tool(
         "code-intelligence",
         "code/analyze_function",
         {"file": "src/main.py", "function": "process_data"}
     )

Configuration:
  - Servers config: config/servers.json
  - Safety policies: config/policies.yaml

Servers:
  ✓ code-intelligence - Code analysis and refactoring
  ✓ execution-engine - Command execution and builds
  ✓ version-control - Git operations
  ✓ quality-assurance - Security and quality checks
  ✓ knowledge-integration - Documentation and databases

For more information, see README.md
""")


def main():
    """Main installation process."""
    print_header("MCP Servers Installation")
    
    print("Checking requirements...")
    if not check_python_version():
        sys.exit(1)
    
    check_dependencies()
    
    print("\nSetting up directories...")
    setup_directories()
    
    print("\nConfiguring scripts...")
    make_scripts_executable()
    
    print("\nCreating launcher...")
    create_launcher_script()
    
    print_header("Installation Complete")
    print_usage()


if __name__ == "__main__":
    main()
