# Kimi CLI MCP & Skills Backup

**Created:** 2026-02-22  
**Source:** ~/ (Donovan's home directory)  
**Size:** ~769MB

## 📦 What's Included

This backup contains all MCP servers, skills, and configurations for Kimi CLI and related tools.

### 1. MCP Servers (`mcp-servers/`)
Main MCP server implementations:
- `android-app-builder/` - Android app building MCP
- `client/` - MCP client utilities
- `code-intelligence/` - Code analysis MCP
- `config/` - Configuration files
- `core/` - Core MCP functionality
- `execution-engine/` - Code execution MCP
- `knowledge-integration/` - Knowledge base MCP
- `quality-assurance/` - QA/testing MCP
- `safety-layer/` - Safety checking MCP
- `version-control/` - Git/version control MCP
- Various config files and setup scripts

### 2. Custom MCP Servers (`custom-mcp-servers/`)
- `Titanium-MCP/` - Titanium MCP server
- `devintelligence-mcp-server/` - DevIntelligence MCP
- `omega-mcp-server/` - Omega MCP server (system tools)
- `omni-mcp-server/` - Omni MCP server

### 3. Skills (`skills/`)
**46+ Skills** including:
- `mcp-builder/` - Guide for creating MCP servers
- `android-app/`, `android-app-dev/` - Android development
- `api-integration/` - API design patterns
- `architecture-design/` - System architecture
- `ci-cd-devops/` - DevOps practices
- `cloudflare-403-triage/` - Cloudflare troubleshooting
- `code-review-refactoring/` - Code quality
- `database-design-optimization/` - Database design
- `debugging-root-cause-analysis/` - Debugging
- `docx/`, `pdf/`, `pptx/`, `xlsx/` - Document processing
- `frontend-design/` - UI/UX design
- `multi-agent-orchestration/` - Multi-agent systems
- `notion-knowledge-capture/`, `notion-meeting-intelligence/`, `notion-research-documentation/`, `notion-spec-to-implementation/` - Notion integration
- `observability-monitoring/` - Monitoring
- `performance-engineering/` - Performance optimization
- `security-engineering/` - Security practices
- `test-driven-development/` - TDD
- `web-artifacts-builder/` - Web development
- `webapp-testing/` - Testing with Playwright
- And many more...

### 4. Kimi CLI Config (`kimiconfig/`)
- `config.toml` - Main Kimi CLI configuration

### 5. MCP Auth (`mcp-auth/`)
- Authentication tokens for MCP remote servers
- Multiple versions of mcp-remote

### 6. MCP Data (`mcp-data/`)
- MCP data storage

### 7. IDE Configs
- `vscode-config/` - VSCode/VSCodium MCP settings
- `copilot-config/` - GitHub Copilot MCP config
- `claude-config/` - Claude Code settings and MCP configs

### 8. Documentation
- `MCP_INTEGRATION_SUMMARY.md`
- `MCP_QUICK_REFERENCE.md`
- `MCP_SERVERS.md`

---

## 🚀 Restoration Guide

### Step 1: Copy Files to New Machine

```bash
# Copy this entire folder to your new machine
# Example using scp:
scp -r kimi-mcp-backup user@new-machine:~/

# Or using rsync:
rsync -avz kimi-mcp-backup/ user@new-machine:~/kimi-mcp-backup/
```

### Step 2: Restore Kimi CLI Config

```bash
# Create Kimi config directory
mkdir -p ~/.config/kimi

# Copy config
cp ~/kimi-mcp-backup/kimiconfig/* ~/.config/kimi/
```

### Step 3: Restore Skills

```bash
# Create skills directory
mkdir -p ~/.config/agents/skills

# Copy all skills
cp -r ~/kimi-mcp-backup/skills/* ~/.config/agents/skills/
```

### Step 4: Restore MCP Servers

```bash
# Copy MCP servers to home directory
cp -r ~/kimi-mcp-backup/mcp-servers ~/mcp-servers
cp -r ~/kimi-mcp-backup/custom-mcp-servers/Titanium-MCP ~/Titanium-MCP
cp -r ~/kimi-mcp-backup/custom-mcp-servers/devintelligence-mcp-server ~/devintelligence-mcp-server
cp -r ~/kimi-mcp-backup/custom-mcp-servers/omega-mcp-server ~/omega-mcp-server
cp -r ~/kimi-mcp-backup/custom-mcp-servers/omni-mcp-server ~/omni-mcp-server
```

### Step 5: Restore MCP Auth (Optional - may need re-auth)

```bash
mkdir -p ~/.mcp-auth
cp -r ~/kimi-mcp-backup/mcp-auth/* ~/.mcp-auth/
```

### Step 6: Restore IDE Configs (Optional)

**VSCode:**
```bash
mkdir -p ~/.vscode
cp ~/kimi-mcp-backup/vscode-config/mcp-settings.json ~/.vscode/
```

**GitHub Copilot:**
```bash
mkdir -p ~/.copilot
cp ~/kimi-mcp-backup/copilot-config/mcp-config.json ~/.copilot/
```

**Claude Code:**
```bash
mkdir -p ~/.claude
cp ~/kimi-mcp-backup/claude-config/claude_desktop_config.json ~/.claude/
cp ~/kimi-mcp-backup/claude-config/settings.json ~/.claude/
```

---

## ⚙️ Post-Restoration Setup

### 1. Install Kimi CLI (if not already installed)

```bash
# Using uv (recommended)
uv tool install kimi-cli

# Or using pip
pip install kimi-cli
```

### 2. Verify Skills

```bash
kimi skills list
```

### 3. Configure MCP Servers

Edit `~/.config/kimi/config.toml` to point to your MCP servers:

```toml
[mcp]
enabled = true

[[mcp.servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home/yourusername"]

[[mcp.servers]]
name = "memory"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-memory"]

# Add other servers as needed
```

### 4. Re-authenticate (if needed)

Some MCP servers may need re-authentication on the new machine:

```bash
# For remote MCP servers
kimi mcp auth <server-name>
```

---

## 🔧 Manual MCP Server Registration

If automatic discovery doesn't work, manually register MCP servers:

```bash
# Example: Register filesystem MCP
kimi mcp add filesystem npx -y @modelcontextprotocol/server-filesystem /home/username

# Example: Register memory MCP
kimi mcp add memory npx -y @modelcontextprotocol/server-memory

# Example: Register custom local MCP
kimi mcp add my-custom-mcp node /path/to/custom/mcp-server/index.js
```

---

## 📝 Important Notes

1. **Credentials**: Some authentication tokens in `mcp-auth/` may be tied to the original machine. You may need to re-authenticate certain services.

2. **Paths**: MCP configs often contain absolute paths. Update these to match your new machine's username and directory structure.

3. **Dependencies**: Some MCP servers require Node.js, Python, or other dependencies to be installed separately.

4. **Permissions**: Ensure executable permissions on scripts:
   ```bash
   chmod +x ~/mcp-servers/mcp-launcher.sh
   chmod +x ~/mcp-servers/setup-editor.sh
   ```

5. **Node.js**: Many MCP servers require Node.js. Install if needed:
   ```bash
   # Using nvm (recommended)
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install 20
   
   # Or using system package manager
   # Ubuntu/Debian: sudo apt install nodejs npm
   # macOS: brew install node
   ```

---

## 🆘 Troubleshooting

### MCP Server Not Found
```bash
# Check if server is registered
kimi mcp list

# Re-add if missing
kimi mcp add <name> <command> [args...]
```

### Permission Denied
```bash
# Fix permissions
chmod +x ~/mcp-servers/*/index.js
chmod +x ~/mcp-servers/mcp-launcher.sh
```

### Path Issues
Edit MCP configs to update absolute paths from `/home/donovan/` to your new home directory.

### Skills Not Loading
```bash
# Verify skills directory
ls ~/.config/agents/skills/

# Each skill should have a SKILL.md file
ls ~/.config/agents/skills/mcp-builder/SKILL.md
```

---

## 📚 File Locations Reference

| Component | Source Location | Restore Location |
|-----------|----------------|------------------|
| Kimi Config | `~/.config/kimi/` | `~/.config/kimi/` |
| Skills | `~/.config/agents/skills/` | `~/.config/agents/skills/` |
| MCP Servers | `~/mcp-servers/` | `~/mcp-servers/` |
| Custom MCPs | `~/*-mcp-server/` | `~/*-mcp-server/` |
| MCP Auth | `~/.mcp-auth/` | `~/.mcp-auth/` |
| MCP Data | `~/mcp-data/` | `~/mcp-data/` |
| VSCode Config | `~/.vscode/mcp-settings.json` | `~/.vscode/mcp-settings.json` |
| Claude Config | `~/.claude/claude_desktop_config.json` | `~/.claude/claude_desktop_config.json` |

---

## ✅ Verification Checklist

After restoration, verify everything works:

- [ ] `kimi --version` works
- [ ] `kimi skills list` shows all skills
- [ ] `kimi mcp list` shows MCP servers
- [ ] Can use skills in conversations (e.g., `@mcp-builder`)
- [ ] MCP tools appear in tool list
- [ ] Can execute MCP tool calls

---

**Backup created by:** Kimi Code CLI  
**For support:** Refer to original MCP documentation or Kimi CLI help
