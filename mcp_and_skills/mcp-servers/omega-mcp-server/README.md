# 🚀 OMEGA MCP Server v2.0

**The Ultimate Combination**: Omni capabilities + PurpleShield cybersecurity in one powerful MCP server.

```
╔══════════════════════════════════════════════════════════════════╗
║  🌐 OMNI (31 tools)      +      🛡️ PURPLESHIELD (13 tools)       ║
║                                                                  ║
║  Browser • System • Docker • WebSocket • Image • Network         ║
║       +                                                          ║
║  Red Team • Blue Team • Purple Team • MITRE ATT&CK               ║
║                                                                  ║
║                    TOTAL: 44 TOOLS                               ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🌐 Omni Capabilities (31 Tools)

### Browser Automation (6 tools)
Navigate JavaScript-heavy sites, take screenshots, interact with dynamic content.

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to URL with JS rendering |
| `browser_screenshot` | Capture screenshots |
| `browser_click` | Click elements |
| `browser_fill` | Fill form inputs |
| `browser_evaluate` | Execute JavaScript in browser |
| `browser_get_content` | Extract rendered content |

### System Monitoring (5 tools)
Real-time system metrics and process inspection.

| Tool | Purpose |
|------|---------|
| `system_get_metrics` | CPU, memory, disk usage |
| `system_list_processes` | Running processes |
| `system_disk_usage` | Filesystem usage |
| `system_network_interfaces` | Network interface stats |
| `system_get_info` | System information |

### Image Processing (4 tools)
OCR, resize, convert, and analyze images.

| Tool | Purpose |
|------|---------|
| `image_ocr` | Text recognition from images |
| `image_resize` | Resize images |
| `image_get_info` | Image metadata |
| `image_convert` | Format conversion |

### Docker Management (6 tools)
Full container and image control.

| Tool | Purpose |
|------|---------|
| `docker_list_containers` | List containers |
| `docker_container_logs` | View container logs |
| `docker_run_container` | Run new containers |
| `docker_container_action` | Start/stop/restart/remove |
| `docker_inspect_container` | Container details |
| `docker_list_images` | List images |

### WebSocket Client (4 tools)
Persistent real-time connections.

| Tool | Purpose |
|------|---------|
| `ws_connect` | Connect to WebSocket |
| `ws_send` | Send messages |
| `ws_receive` | Receive messages |
| `ws_close` | Close connection |

### Network Tools (4 tools)
Network diagnostics and scanning.

| Tool | Purpose |
|------|---------|
| `network_ping` | ICMP ping |
| `network_port_scan` | TCP port scanning |
| `network_dns_lookup` | DNS record lookup |
| `network_reverse_dns` | Reverse DNS lookup |

### Notifications (2 tools)
System alerts.

| Tool | Purpose |
|------|---------|
| `notify_desktop` | Desktop notifications |
| `notify_beep` | System beep |

---

## 🛡️ PurpleShield Cybersecurity (13 Tools)

### 🔴 Red Team (4 tools)
Offensive security reconnaissance.

| Tool | Purpose |
|------|---------|
| `cyber_subdomain_enum` | Subdomain enumeration via certificate transparency |
| `cyber_dns_analyze` | DNS security analysis |
| `cyber_whois` | Domain registration lookup |
| `cyber_headers_analyze` | HTTP security header analysis |

### 🔵 Blue Team (5 tools)
Defensive security and threat intelligence.

| Tool | Purpose |
|------|---------|
| `cyber_threat_ip_lookup` | IP reputation check |
| `cyber_threat_domain_lookup` | Domain reputation analysis |
| `cyber_threat_hash_lookup` | File hash malware check |
| `cyber_cve_lookup` | CVE vulnerability details |
| `cyber_cve_search` | Search CVE database |

### 🟣 Purple Team (4 tools)
MITRE ATT&CK and exercise management.

| Tool | Purpose |
|------|---------|
| `cyber_mitre_lookup` | MITRE ATT&CK technique details |
| `cyber_mitre_search` | Search ATT&CK techniques |
| `cyber_exercise_create` | Create purple team exercise |
| `cyber_coverage_map` | Map detection coverage |

---

## 🚀 Installation

```bash
cd omega-mcp-server
npm install
npm run build
```

### Environment Variables (Optional)

```bash
# For VirusTotal threat intelligence
export VIRUSTOTAL_API_KEY=your_key_here

# For HTTP transport
export TRANSPORT=http
export PORT=3000
```

---

## 🎯 Usage

### Local Mode (stdio)
```bash
npm start
```

### HTTP Mode
```bash
export TRANSPORT=http
npm start
# Server available at http://localhost:3000/mcp
```

### MCP Client Configuration

```json
{
  "mcpServers": {
    "omega": {
      "command": "node",
      "args": ["/home/donovan/omega-mcp-server/dist/index.js"],
      "env": {
        "VIRUSTOTAL_API_KEY": "optional_key"
      }
    }
  }
}
```

---

## 💡 Example Workflows

### Web Application Security Assessment
```
browser_navigate → browser_screenshot → cyber_headers_analyze
```

### Threat Investigation
```
cyber_threat_ip_lookup → cyber_dns_analyze → cyber_cve_search
```

### Infrastructure Monitoring
```
system_get_metrics → docker_list_containers → network_port_scan
```

### Purple Team Exercise
```
cyber_mitre_search → cyber_exercise_create → cyber_coverage_map
```

### Real-time Threat Intel
```
ws_connect → ws_send → ws_receive → cyber_threat_ip_lookup
```

---

## 📊 Tool Categories Summary

| Category | Count | Use Case |
|----------|-------|----------|
| **Browser** | 6 | Web automation, screenshots, JS execution |
| **System** | 5 | Resource monitoring, process management |
| **Image** | 4 | OCR, image manipulation |
| **Docker** | 6 | Container lifecycle management |
| **WebSocket** | 4 | Real-time streaming data |
| **Network** | 4 | Connectivity testing, port scanning |
| **Notify** | 2 | User notifications |
| **Red Team** | 4 | Reconnaissance, OSINT |
| **Blue Team** | 5 | Threat intel, CVE lookup |
| **Purple Team** | 4 | MITRE ATT&CK, exercises |

---

## 🔒 Security Notes

- **Port scanning**: Only scan hosts you own/have permission to scan
- **Browser automation**: Can access any website; respect robots.txt
- **Docker tools**: Requires Docker permissions
- **Threat intel**: Some features require API keys for full functionality

---

## 📄 License

MIT - Use responsibly!
