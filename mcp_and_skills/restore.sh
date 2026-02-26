#!/bin/bash
#
# Kimi CLI MCP & Skills Restore Script
# Usage: ./restore.sh [--skip-mcp-auth] [--dry-run]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_MCP_AUTH=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --skip-mcp-auth)
            SKIP_MCP_AUTH=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: ./restore.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-mcp-auth    Skip restoring MCP authentication (may need re-auth)"
            echo "  --dry-run          Show what would be done without making changes"
            echo "  --help             Show this help message"
            exit 0
            ;;
    esac
done

# Get the directory where this script is located
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Kimi MCP & Skills Restore${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "Backup location: $BACKUP_DIR"
echo "Target home: $HOME"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
    echo ""
fi

# Function to copy with dry-run support
copy_with_dryrun() {
    local src="$1"
    local dst="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN] Would copy:${NC} $src -> $dst"
    else
        if [ -e "$src" ]; then
            mkdir -p "$(dirname "$dst")"
            cp -r "$src" "$dst"
            echo -e "${GREEN}✓${NC} Copied: $src"
        else
            echo -e "${YELLOW}⚠${NC} Source not found: $src"
        fi
    fi
}

# Function to create directory with dry-run support
mkdir_with_dryrun() {
    local dir="$1"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN] Would create directory:${NC} $dir"
    else
        mkdir -p "$dir"
    fi
}

echo -e "${YELLOW}Step 1: Restoring Kimi CLI Config${NC}"
mkdir_with_dryrun "$HOME/.config/kimi"
copy_with_dryrun "$BACKUP_DIR/kimiconfig/config.toml" "$HOME/.config/kimi/config.toml"
echo ""

echo -e "${YELLOW}Step 2: Restoring Skills${NC}"
mkdir_with_dryrun "$HOME/.config/agents/skills"
for skill_dir in "$BACKUP_DIR"/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        copy_with_dryrun "$skill_dir" "$HOME/.config/agents/skills/$skill_name"
    fi
done
echo ""

echo -e "${YELLOW}Step 3: Restoring MCP Servers${NC}"
mkdir_with_dryrun "$HOME/mcp-servers"
for item in "$BACKUP_DIR/mcp-servers"/*; do
    if [ -e "$item" ]; then
        name=$(basename "$item")
        copy_with_dryrun "$item" "$HOME/mcp-servers/$name"
    fi
done
echo ""

echo -e "${YELLOW}Step 4: Restoring Custom MCP Servers${NC}"
for mcp_dir in "$BACKUP_DIR"/custom-mcp-servers/*/; do
    if [ -d "$mcp_dir" ]; then
        mcp_name=$(basename "$mcp_dir")
        copy_with_dryrun "$mcp_dir" "$HOME/$mcp_name"
    fi
done
echo ""

echo -e "${YELLOW}Step 5: Restoring MCP Data${NC}"
mkdir_with_dryrun "$HOME/mcp-data"
for item in "$BACKUP_DIR/mcp-data"/*; do
    if [ -e "$item" ]; then
        name=$(basename "$item")
        copy_with_dryrun "$item" "$HOME/mcp-data/$name"
    fi
done
echo ""

if [ "$SKIP_MCP_AUTH" = false ]; then
    echo -e "${YELLOW}Step 6: Restoring MCP Auth${NC}"
    echo -e "${YELLOW}Note: You may need to re-authenticate some services${NC}"
    mkdir_with_dryrun "$HOME/.mcp-auth"
    for item in "$BACKUP_DIR/mcp-auth"/*; do
        if [ -e "$item" ]; then
            name=$(basename "$item")
            copy_with_dryrun "$item" "$HOME/.mcp-auth/$name"
        fi
    done
else
    echo -e "${YELLOW}Step 6: Skipping MCP Auth (as requested)${NC}"
fi
echo ""

echo -e "${YELLOW}Step 7: Restoring IDE Configs${NC}"
# VSCode
if [ -f "$BACKUP_DIR/vscode-config/mcp-settings.json" ]; then
    mkdir_with_dryrun "$HOME/.vscode"
    copy_with_dryrun "$BACKUP_DIR/vscode-config/mcp-settings.json" "$HOME/.vscode/mcp-settings.json"
fi

# Copilot
if [ -f "$BACKUP_DIR/copilot-config/mcp-config.json" ]; then
    mkdir_with_dryrun "$HOME/.copilot"
    copy_with_dryrun "$BACKUP_DIR/copilot-config/mcp-config.json" "$HOME/.copilot/mcp-config.json"
fi

# Claude Code
if [ -f "$BACKUP_DIR/claude-config/claude_desktop_config.json" ]; then
    mkdir_with_dryrun "$HOME/.claude"
    copy_with_dryrun "$BACKUP_DIR/claude-config/claude_desktop_config.json" "$HOME/.claude/claude_desktop_config.json"
    copy_with_dryrun "$BACKUP_DIR/claude-config/settings.json" "$HOME/.claude/settings.json"
fi
echo ""

if [ "$DRY_RUN" = false ]; then
    echo -e "${YELLOW}Step 8: Setting permissions${NC}"
    # Make scripts executable
    find "$HOME/mcp-servers" -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Set executable permissions on scripts"
    echo ""
fi

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Restore Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    echo -e "${BLUE}Next steps:${NC}"
    echo ""
    echo "1. Verify kimi is installed:"
    echo "   kimi --version"
    echo ""
    echo "2. List available skills:"
    echo "   kimi skills list"
    echo ""
    echo "3. List MCP servers:"
    echo "   kimi mcp list"
    echo ""
    echo "4. Update any absolute paths in configs:"
    echo "   - ~/.config/kimi/config.toml"
    echo "   - ~/.vscode/mcp-settings.json"
    echo "   - ~/.claude/claude_desktop_config.json"
    echo ""
    echo "5. Re-authenticate if needed:"
    echo "   kimi mcp auth <server-name>"
    echo ""
    echo -e "${YELLOW}Note: Some paths may need updating from /home/donovan to your home directory${NC}"
else
    echo -e "${YELLOW}This was a dry run. No changes were made.${NC}"
    echo "Run without --dry-run to perform the actual restore."
fi
