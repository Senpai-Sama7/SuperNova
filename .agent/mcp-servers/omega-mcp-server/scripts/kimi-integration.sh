#!/bin/bash
# OMEGA MCP Server - Kimi CLI Integration Manager

set -e

OMEGA_DIR="/home/donovan/omega-mcp-server"
KIMI_CONFIG="$HOME/.kimi/mcp.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🚀 OMEGA MCP Server - Kimi CLI Integration Manager          ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
}

status() {
    print_header
    echo -e "${YELLOW}📊 Integration Status${NC}"
    echo "────────────────────────────────────────────────────────────────"
    
    # Check OMEGA build
    if [ -f "$OMEGA_DIR/dist/index.js" ]; then
        echo -e "${GREEN}✓${NC} OMEGA server built"
    else
        echo -e "${RED}✗${NC} OMEGA server not built"
    fi
    
    # Check kimi config
    if [ -f "$KIMI_CONFIG" ]; then
        if grep -q "omega" "$KIMI_CONFIG"; then
            echo -e "${GREEN}✓${NC} OMEGA in kimi config"
        else
            echo -e "${RED}✗${NC} OMEGA not in kimi config"
        fi
    else
        echo -e "${RED}✗${NC} Kimi config not found"
    fi
    
    # Check kimi installation
    if command -v kimi &> /dev/null; then
        echo -e "${GREEN}✓${NC} Kimi CLI installed"
    else
        echo -e "${RED}✗${NC} Kimi CLI not found"
    fi
    
    echo
    echo -e "${YELLOW}🔧 Available Commands${NC}"
    echo "────────────────────────────────────────────────────────────────"
    echo "  test        - Test OMEGA connection"
    echo "  build       - Rebuild OMEGA server"
    echo "  tools       - List all 44 OMEGA tools"
    echo "  reinstall   - Reinstall integration"
}

test_connection() {
    echo -e "${YELLOW}🧪 Testing OMEGA Connection...${NC}"
    echo "────────────────────────────────────────────────────────────────"
    
    if kimi mcp test omega 2>&1; then
        echo
        echo -e "${GREEN}✅ OMEGA MCP Server is working correctly!${NC}"
    else
        echo
        echo -e "${RED}❌ OMEGA connection test failed${NC}"
        echo "Try rebuilding: ./kimi-integration.sh build"
    fi
}

build_server() {
    echo -e "${YELLOW}🔨 Building OMEGA MCP Server...${NC}"
    echo "────────────────────────────────────────────────────────────────"
    
    cd "$OMEGA_DIR"
    
    if npm run build 2>&1; then
        echo
        echo -e "${GREEN}✅ Build successful!${NC}"
        echo "Start kimi and OMEGA will be available automatically."
    else
        echo
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi
}

list_tools() {
    echo -e "${YELLOW}🔧 OMEGA Tools (44 Total)${NC}"
    echo "────────────────────────────────────────────────────────────────"
    
    kimi mcp test omega 2>&1 | grep "^-" | head -50
}

reinstall() {
    echo -e "${YELLOW}🔄 Reinstalling OMEGA Integration...${NC}"
    echo "────────────────────────────────────────────────────────────────"
    
    # Rebuild
    cd "$OMEGA_DIR"
    npm run build
    
    # Update config
    if [ -f "$KIMI_CONFIG" ]; then
        # Backup existing config
        cp "$KIMI_CONFIG" "$KIMI_CONFIG.backup.$(date +%Y%m%d%H%M%S)"
        
        # Add OMEGA if not present
        if ! grep -q "omega" "$KIMI_CONFIG"; then
            echo "Adding OMEGA to kimi config..."
            node -e "
                const fs = require('fs');
                const config = JSON.parse(fs.readFileSync('$KIMI_CONFIG', 'utf8'));
                config.mcpServers.omega = {
                    command: 'node',
                    args: ['$OMEGA_DIR/dist/index.js'],
                    env: { TRANSPORT: 'stdio', NODE_ENV: 'production' }
                };
                fs.writeFileSync('$KIMI_CONFIG', JSON.stringify(config, null, 2));
            "
        fi
        
        echo -e "${GREEN}✅ Integration reinstalled!${NC}"
    else
        echo -e "${RED}❌ Kimi config not found at $KIMI_CONFIG${NC}"
        exit 1
    fi
}

# Main command handler
case "${1:-status}" in
    status)
        status
        ;;
    test)
        test_connection
        ;;
    build)
        build_server
        ;;
    tools)
        list_tools
        ;;
    reinstall)
        reinstall
        ;;
    *)
        echo "Usage: $0 {status|test|build|tools|reinstall}"
        exit 1
        ;;
esac
