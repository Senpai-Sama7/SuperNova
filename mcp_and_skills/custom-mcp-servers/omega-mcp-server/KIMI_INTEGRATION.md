# OMEGA MCP Server - Kimi CLI Integration

## 🎯 Integration Complete

OMEGA MCP Server v2.0 is now fully integrated with kimi-cli, providing access to all 44 tools across 10 categories.

## 📊 Integration Status

| Component | Status |
|-----------|--------|
| MCP Server Config | ✅ Added to `~/.kimi/mcp.json` |
| Tool Registration | ✅ 44 tools available |
| Connection Test | ✅ Passed |
| Auto-start | ✅ On kimi-cli launch |

## 🚀 Available Tools in Kimi

### Browser Automation (6 tools)
- `browser_navigate` - Navigate to URLs and wait for load
- `browser_screenshot` - Capture screenshots (PNG/base64)
- `browser_click` - Click elements on page
- `browser_fill` - Fill form inputs
- `browser_evaluate` - Execute JavaScript
- `browser_get_content` - Extract text/HTML

### System Management (5 tools)
- `system_get_metrics` - CPU, memory, disk usage
- `system_list_processes` - Running processes
- `system_disk_usage` - Filesystem usage
- `system_network_interfaces` - Network config
- `system_get_info` - Comprehensive system info

### Image Processing (4 tools)
- `image_ocr` - Text extraction (Tesseract)
- `image_resize` - Resize images
- `image_get_info` - Metadata extraction
- `image_convert` - Format conversion

### Docker Management (6 tools)
- `docker_list_containers` - List containers
- `docker_container_logs` - Retrieve logs
- `docker_run_container` - Create/start containers
- `docker_container_action` - Start/stop/restart/remove
- `docker_inspect_container` - Detailed info
- `docker_list_images` - List images

### WebSocket (4 tools)
- `ws_connect` - Establish connections
- `ws_send` - Send messages
- `ws_receive` - Receive messages
- `ws_close` - Close connections

### Network Tools (4 tools)
- `network_ping` - ICMP ping
- `network_port_scan` - TCP port scanning
- `network_dns_lookup` - DNS resolution
- `network_reverse_dns` - Reverse DNS

### Notifications (2 tools)
- `notify_desktop` - Desktop notifications
- `notify_beep` - System beep

### Red Team Security (4 tools)
- `cyber_subdomain_enum` - Subdomain enumeration
- `cyber_dns_analyze` - DNS security analysis
- `cyber_whois` - WHOIS lookups
- `cyber_headers_analyze` - HTTP header analysis

### Blue Team Security (5 tools)
- `cyber_threat_ip_lookup` - IP reputation check
- `cyber_cve_lookup` - CVE details lookup
- `cyber_cve_search` - CVE database search
- `cyber_threat_domain_lookup` - Domain reputation
- `cyber_threat_hash_lookup` - File hash check

### Purple Team Security (4 tools)
- `cyber_mitre_lookup` - MITRE ATT&CK lookup
- `cyber_mitre_search` - MITRE technique search
- `cyber_exercise_create` - Purple team exercises
- `cyber_coverage_map` - Detection coverage mapping

## 🔧 Usage in Kimi

Simply ask kimi to use any OMEGA tool:

```
"Take a screenshot of example.com"
"Check system CPU and memory usage"
"Scan ports on scanme.nmap.org"
"Enumerate subdomains for google.com"
"Get CVE details for CVE-2021-44228"
```

## 📝 Configuration Details

**Config file:** `~/.kimi/mcp.json`

```json
{
  "mcpServers": {
    "omega": {
      "command": "node",
      "args": ["/home/donovan/omega-mcp-server/dist/index.js"],
      "env": {
        "TRANSPORT": "stdio",
        "NODE_ENV": "production"
      }
    }
  }
}
```

## 🧪 Testing

Test the integration:
```bash
# List all MCP servers
kimi mcp list

# Test OMEGA connection
kimi mcp test omega

# Start kimi with OMEGA tools available
kimi
```

## 🔒 Security Notes

- OMEGA runs in stdio mode (local only)
- No network exposure by default
- Docker access requires user permissions
- Browser automation runs headless

## 🔄 Updating

To update OMEGA:
```bash
cd /home/donovan/omega-mcp-server
git pull  # If using git
npm run build
```

## 📚 RALPH Testing Results

All 44 tools verified via RALPH autonomous testing:
- **Pass Rate:** 100%
- **Categories Complete:** 10/10
- **Test Iterations:** 44/44
- **Status:** ✅ Production Ready

## 🛟 Support

For issues with OMEGA tools in kimi:
1. Check server status: `kimi mcp test omega`
2. Rebuild if needed: `npm run build`
3. Verify config: `cat ~/.kimi/mcp.json`

---

**Integration Date:** 2026-02-17  
**OMEGA Version:** 2.0.0  
**Total Tools:** 44 across 10 categories
