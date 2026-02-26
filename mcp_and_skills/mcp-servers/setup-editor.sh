#!/bin/bash
# Setup MCP servers for various editors

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          MCP Server Editor Configuration Setup             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to detect editors
detect_editors() {
    local editors=()
    
    if command -v code &> /dev/null; then
        editors+=("vscode")
    fi
    
    if [ -d "$HOME/.cursor" ] || command -v cursor &> /dev/null; then
        editors+=("cursor")
    fi
    
    if [ -d "$HOME/.config/claude" ]; then
        editors+=("claude")
    fi
    
    if command -v kimiserver &> /dev/null || [ -d "$HOME/.kimi" ]; then
        editors+=("kimi")
    fi
    
    echo "${editors[@]}"
}

# Function to setup VS Code
setup_vscode() {
    echo "Setting up VS Code..."
    
    VSCODE_DIR="$HOME/.vscode"
    mkdir -p "$VSCODE_DIR"
    
    # Check if settings.json exists
    if [ -f "$VSCODE_DIR/settings.json" ]; then
        echo "  ⚠ VS Code settings.json exists, backing up..."
        cp "$VSCODE_DIR/settings.json" "$VSCODE_DIR/settings.json.backup.$(date +%Y%m%d%H%M%S)"
    fi
    
    # Copy MCP settings
    cp "$CONFIG_DIR/mcp-settings.json" "$VSCODE_DIR/mcp-settings.json"
    
    echo "  ✓ Copied to $VSCODE_DIR/mcp-settings.json"
    echo ""
    echo "  Add this to your VS Code settings.json:"
    echo '  "mcp": $(cat "$VSCODE_DIR/mcp-settings.json" | jq .)'
    echo ""
}

# Function to setup Cursor
setup_cursor() {
    echo "Setting up Cursor..."
    
    CURSOR_DIR="$HOME/.cursor"
    mkdir -p "$CURSOR_DIR"
    
    cp "$CONFIG_DIR/cursor-mcp.json" "$CURSOR_DIR/mcp.json"
    
    echo "  ✓ Copied to $CURSOR_DIR/mcp.json"
    echo ""
}

# Function to setup Claude Desktop
setup_claude() {
    echo "Setting up Claude Desktop..."
    
    CLAUDE_DIR="$HOME/.config/claude"
    mkdir -p "$CLAUDE_DIR"
    
    cp "$CONFIG_DIR/claude-mcp.json" "$CLAUDE_DIR/mcp.json"
    
    echo "  ✓ Copied to $CLAUDE_DIR/mcp.json"
    echo ""
}

# Function to setup Kimi
setup_kimi() {
    echo "Setting up Kimi CLI..."
    
    KIMI_DIR="$HOME/.config/kimi"
    mkdir -p "$KIMI_DIR"
    
    cp "$CONFIG_DIR/claude-mcp.json" "$KIMI_DIR/mcp-servers.json"
    
    echo "  ✓ Copied to $KIMI_DIR/mcp-servers.json"
    echo ""
}

# Function to create workspace config
create_workspace_config() {
    echo "Creating workspace configuration..."
    
    cat > "$SCRIPT_DIR/mcp-workspace.json" << EOF
{
  "mcpServers": {
    "code-intelligence": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/code-intelligence/src/server.py"],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR:$SCRIPT_DIR/core:$SCRIPT_DIR/safety-layer/src"
      }
    },
    "execution-engine": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/execution-engine/src/server.py"],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR:$SCRIPT_DIR/core:$SCRIPT_DIR/safety-layer/src"
      }
    },
    "version-control": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/version-control/src/server.py"],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR:$SCRIPT_DIR/core:$SCRIPT_DIR/safety-layer/src"
      }
    },
    "quality-assurance": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/quality-assurance/src/server.py"],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR:$SCRIPT_DIR/core:$SCRIPT_DIR/safety-layer/src"
      }
    },
    "knowledge-integration": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/knowledge-integration/src/server.py"],
      "env": {
        "PYTHONPATH": "$SCRIPT_DIR:$SCRIPT_DIR/core:$SCRIPT_DIR/safety-layer/src"
      }
    }
  }
}
EOF
    
    echo "  ✓ Created $SCRIPT_DIR/mcp-workspace.json"
    echo ""
}

# Main menu
main() {
    echo "Detected configuration options:"
    echo ""
    
    PS3="Select editor to configure (or 0 to exit): "
    options=("VS Code" "Cursor" "Claude Desktop" "Kimi CLI" "Create workspace config" "All" "Exit")
    
    select opt in "${options[@]}"; do
        case $REPLY in
            1) setup_vscode ;;
            2) setup_cursor ;;
            3) setup_claude ;;
            4) setup_kimi ;;
            5) create_workspace_config ;;
            6) 
                setup_vscode
                setup_cursor
                setup_claude
                setup_kimi
                create_workspace_config
                ;;
            7|0) 
                echo "Exiting..."
                exit 0
                ;;
            *) 
                echo "Invalid option"
                ;;
        esac
        
        echo ""
        echo "Configuration complete!"
        echo ""
        echo "Next steps:"
        echo "1. Restart your editor"
        echo "2. Check MCP server status in your editor's AI panel"
        echo "3. Try: 'Analyze the complexity of this function'"
        echo ""
        break
    done
}

# Run main if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
