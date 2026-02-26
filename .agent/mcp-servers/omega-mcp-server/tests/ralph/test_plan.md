# OMEGA MCP Server - RALPH Test Plan

**Version:** 2.0.0  
**Total Test Cases:** 44  
**Categories:** Omni (31) + PurpleShield Cyber (13)

---

## 🌐 BROWSER AUTOMATION (6 tools)

### TC-001: browser_navigate - Basic Navigation
**Priority:** Critical  
**Category:** browser  
**Prerequisites:** Puppeteer browser installation

**Test Steps:**
1. Call browser_navigate with URL "https://example.com"
2. Wait for page to load with wait_until="networkidle2"

**Expected Result:**
- Success: true
- URL matches requested URL
- Title is extracted
- Status code returned
- Viewport dimensions present

---

### TC-002: browser_navigate - JavaScript Rendering
**Priority:** Critical  
**Category:** browser  
**Prerequisites:** Internet connection

**Test Steps:**
1. Navigate to a JavaScript-heavy site (e.g., React app)
2. Verify wait_until handles dynamic content

**Expected Result:**
- Page fully rendered
- Dynamic content loaded
- No timeout errors

---

### TC-003: browser_screenshot - Full Page Capture
**Priority:** High  
**Category:** browser  
**Prerequisites:** Browser navigated to page

**Test Steps:**
1. Navigate to example.com
2. Take screenshot with full_page=true
3. Verify image data returned

**Expected Result:**
- Screenshot captured successfully
- Image data is valid base64 or saved to file
- Size information present

---

### TC-004: browser_screenshot - Element Capture
**Priority:** High  
**Category:** browser  
**Prerequisites:** Page with identifiable element

**Test Steps:**
1. Navigate to page
2. Take screenshot of specific element using selector

**Expected Result:**
- Element found and captured
- Cropped screenshot returned

---

### TC-005: browser_click - Element Interaction
**Priority:** High  
**Category:** browser  
**Prerequisites:** Page with clickable element

**Test Steps:**
1. Navigate to test page
2. Click element using CSS selector
3. Verify click executed

**Expected Result:**
- Click performed without error
- Element exists message or navigation occurs

---

### TC-006: browser_fill - Form Input
**Priority:** High  
**Category:** browser  
**Prerequisites:** Page with form input

**Test Steps:**
1. Navigate to form page
2. Fill input field with test value
3. Verify value entered

**Expected Result:**
- Input field populated
- No errors during typing

---

### TC-007: browser_evaluate - JavaScript Execution
**Priority:** Medium  
**Category:** browser  
**Prerequisites:** Browser page open

**Test Steps:**
1. Navigate to page
2. Execute JavaScript: document.title
3. Verify result returned

**Expected Result:**
- Script executes successfully
- Result is JSON-serializable
- Type information present

---

### TC-008: browser_get_content - Text Extraction
**Priority:** Medium  
**Category:** browser  
**Prerequisites:** Browser navigated to page

**Test Steps:**
1. Navigate to example.com
2. Get page content as text
3. Verify text extracted

**Expected Result:**
- Text content returned
- HTML stripped (when include_html=false)

---

---

## 📊 SYSTEM MONITORING (5 tools)

### TC-009: system_get_metrics - Basic Metrics
**Priority:** Critical  
**Category:** system  
**Prerequisites:** None

**Test Steps:**
1. Call system_get_metrics
2. Verify all metric categories returned

**Expected Result:**
- CPU usage percentage present
- Memory stats (total, used, free)
- Disk usage stats
- Uptime seconds

---

### TC-010: system_get_metrics - With Temperatures
**Priority:** Medium  
**Category:** system  
**Prerequisites:** Hardware sensors available

**Test Steps:**
1. Call with include_temperatures=true
2. Check for temperature data

**Expected Result:**
- Temperature data included if available
- No error if sensors unavailable

---

### TC-011: system_list_processes - Process Enumeration
**Priority:** High  
**Category:** system  
**Prerequisites:** None

**Test Steps:**
1. List processes with default limit
2. Sort by CPU
3. Verify process details

**Expected Result:**
- Process list returned
- Each process has PID, name, CPU%, memory
- Sorted correctly

---

### TC-012: system_disk_usage - Filesystem Stats
**Priority:** High  
**Category:** system  
**Prerequisites:** None

**Test Steps:**
1. Get disk usage for all filesystems
2. Verify each entry has required fields

**Expected Result:**
- All mounted filesystems listed
- Size, used, available, usage% present

---

### TC-013: system_network_interfaces - Interface Enumeration
**Priority:** Medium  
**Category:** system  
**Prerequisites:** Network interfaces present

**Test Steps:**
1. Get network interface information
2. Check for IP addresses and stats

**Expected Result:**
- Interface names listed
- IP addresses (v4/v6) present
- MAC addresses included
- RX/TX stats available

---

### TC-014: system_get_info - System Information
**Priority:** Low  
**Category:** system  
**Prerequisites:** None

**Test Steps:**
1. Get system info with detail_level=basic
2. Verify OS and hardware details

**Expected Result:**
- OS platform and version
- CPU information
- System manufacturer/model

---

---

## 🖼️ IMAGE PROCESSING (4 tools)

### TC-015: image_ocr - Text Recognition
**Priority:** High  
**Category:** image  
**Prerequisites:** Test image with text

**Test Steps:**
1. Create or use test image with known text
2. Run OCR on image
3. Verify text extracted

**Expected Result:**
- Text extracted from image
- Confidence score provided
- Word-level data available

---

### TC-016: image_resize - Resize Operation
**Priority:** High  
**Category:** image  
**Prerequisites:** Test image file

**Test Steps:**
1. Resize image to specific dimensions
2. Verify output file created
3. Check new dimensions

**Expected Result:**
- Resized image saved
- Dimensions match target
- File size information present

---

### TC-017: image_get_info - Metadata Extraction
**Priority:** Medium  
**Category:** image  
**Prerequisites:** Image file exists

**Test Steps:**
1. Get info for test image
2. Verify all metadata fields

**Expected Result:**
- Dimensions (width/height)
- Format type
- File size
- Color space info

---

### TC-018: image_convert - Format Conversion
**Priority:** Medium  
**Category:** image  
**Prerequisites:** Image file exists

**Test Steps:**
1. Convert image to different format (e.g., PNG to JPEG)
2. Verify output format

**Expected Result:**
- Image converted successfully
- New format detected
- Quality settings applied

---

---

## 🐳 DOCKER MANAGEMENT (6 tools)

### TC-019: docker_list_containers - Container Enumeration
**Priority:** Critical  
**Category:** docker  
**Prerequisites:** Docker daemon running

**Test Steps:**
1. List all containers
2. Verify response format

**Expected Result:**
- Container list returned (may be empty)
- Each entry has ID, name, image, status, ports
- No error if Docker running

---

### TC-020: docker_run_container - Create and Run
**Priority:** Critical  
**Category:** docker  
**Prerequisites:** Docker daemon running

**Test Steps:**
1. Run nginx container with name "test-nginx"
2. Map port 8080 to 80
3. Verify container started

**Expected Result:**
- Container created successfully
- Container ID returned
- Port mapping correct
- Status is "running"

---

### TC-021: docker_container_logs - Log Retrieval
**Priority:** High  
**Category:** docker  
**Prerequisites:** Running container

**Test Steps:**
1. Get logs from running container
2. Specify tail limit
3. Verify log content

**Expected Result:**
- Logs retrieved successfully
- Number of lines matches limit
- Content is readable

---

### TC-022: docker_container_action - Stop Container
**Priority:** High  
**Category:** docker  
**Prerequisites:** Running container

**Test Steps:**
1. Stop test container
2. Verify status changed

**Expected Result:**
- Stop command succeeds
- Container status updated

---

### TC-023: docker_container_action - Remove Container
**Priority:** High  
**Category:** docker  
**Prerequisites:** Stopped container

**Test Steps:**
1. Remove stopped container
2. Verify container no longer listed

**Expected Result:**
- Container removed successfully
- No longer appears in list

---

### TC-024: docker_inspect_container - Detailed Info
**Priority:** Medium  
**Category:** docker  
**Prerequisites:** Existing container

**Test Steps:**
1. Inspect running or stopped container
2. Verify detailed information

**Expected Result:**
- Full container config returned
- State information present
- Network settings included
- Mounts listed

---

### TC-025: docker_list_images - Image Enumeration
**Priority:** Medium  
**Category:** docker  
**Prerequisites:** Docker daemon running

**Test Steps:**
1. List Docker images
2. Verify image details

**Expected Result:**
- Image list returned
- Each has ID, tags, size, created date

---

---

## 🔌 WEBSOCKET CLIENT (4 tools)

### TC-026: ws_connect - Connection Establishment
**Priority:** Critical  
**Category:** websocket  
**Prerequisites:** WebSocket echo server available

**Test Steps:**
1. Connect to wss://echo.websocket.org
2. Verify connection ID returned

**Expected Result:**
- Connection established
- Connection ID generated
- Status is "connected"

---

### TC-027: ws_send - Message Transmission
**Priority:** Critical  
**Category:** websocket  
**Prerequisites:** Active WebSocket connection

**Test Steps:**
1. Send message through connection
2. Verify send confirmation

**Expected Result:**
- Message sent successfully
- Send confirmation received

---

### TC-028: ws_receive - Message Reception
**Priority:** Critical  
**Category:** websocket  
**Prerequisites:** Active connection with expected message

**Test Steps:**
1. Send message to echo server
2. Wait for response
3. Receive echoed message

**Expected Result:**
- Message received
- Content matches sent message
- Timestamp recorded

---

### TC-029: ws_close - Connection Termination
**Priority:** High  
**Category:** websocket  
**Prerequisites:** Active connection

**Test Steps:**
1. Close WebSocket connection
2. Verify connection removed

**Expected Result:**
- Connection closed gracefully
- Connection ID no longer valid
- Confirmation received

---

---

## 🌐 NETWORK TOOLS (4 tools)

### TC-030: network_ping - Host Reachability
**Priority:** Critical  
**Category:** network  
**Prerequisites:** Network connectivity

**Test Steps:**
1. Ping 8.8.8.8
2. Verify response statistics

**Expected Result:**
- Ping executes
- Reachability status
- Latency statistics (min/avg/max)
- Packet loss percentage

---

### TC-031: network_port_scan - Port Scanning
**Priority:** High  
**Category:** network  
**Prerequisites:** Target host with known open ports

**Test Steps:**
1. Scan localhost on common ports
2. Check for open ports

**Expected Result:**
- Port list scanned
- Open ports identified
- Service names detected

---

### TC-032: network_dns_lookup - DNS Resolution
**Priority:** Critical  
**Category:** network  
**Prerequisites:** DNS resolver available

**Test Steps:**
1. Lookup A records for google.com
2. Verify IP addresses returned

**Expected Result:**
- DNS records resolved
- Record type correct
- Values present

---

### TC-033: network_reverse_dns - Reverse Lookup
**Priority:** Medium  
**Category:** network  
**Prerequisites:** Known IP with PTR record

**Test Steps:**
1. Reverse lookup 8.8.8.8
2. Verify hostname returned

**Expected Result:**
- Hostname resolved
- Result is array of hostnames

---

---

## 🔔 NOTIFICATIONS (2 tools)

### TC-034: notify_desktop - Notification Display
**Priority:** Medium  
**Category:** notify  
**Prerequisites:** Desktop environment available

**Test Steps:**
1. Send desktop notification
2. Verify no errors (display may not be visible in headless)

**Expected Result:**
- Notification sent
- No runtime errors
- Confirmation returned

---

### TC-035: notify_beep - System Beep
**Priority:** Low  
**Category:** notify  
**Prerequisites:** Audio system (optional)

**Test Steps:**
1. Play beep sound
2. Verify execution

**Expected Result:**
- Beep command executed
- No errors

---

---

## 🔴 RED TEAM (4 tools)

### TC-036: cyber_subdomain_enum - Subdomain Discovery
**Priority:** Critical  
**Category:** red-team  
**Prerequisites:** Internet connection

**Test Steps:**
1. Enumerate subdomains for example.com
2. Verify results from certificate transparency

**Expected Result:**
- Subdomain list returned
- Sources identified
- Count present

---

### TC-037: cyber_dns_analyze - DNS Security Analysis
**Priority:** High  
**Category:** red-team  
**Prerequisites:** DNS resolver available

**Test Steps:**
1. Analyze DNS for domain
2. Check for security records (SPF, DKIM, DMARC)

**Expected Result:**
- DNS records enumerated
- Security analysis present
- Record types identified

---

### TC-038: cyber_whois - WHOIS Lookup
**Priority:** High  
**Category:** red-team  
**Prerequisites:** WHOIS command available

**Test Steps:**
1. Lookup WHOIS for domain
2. Parse registration info

**Expected Result:**
- WHOIS data retrieved
- Registrar info present
- Dates extracted
- Raw data available

---

### TC-039: cyber_headers_analyze - Security Header Analysis
**Priority:** Critical  
**Category:** red-team  
**Prerequisites:** Internet connection

**Test Steps:**
1. Analyze headers for https://example.com
2. Check security score
3. Verify recommendations

**Expected Result:**
- Headers analyzed
- Security score calculated
- Missing headers identified
- Recommendations provided

---

---

## 🔵 BLUE TEAM (5 tools)

### TC-040: cyber_threat_ip_lookup - IP Reputation
**Priority:** Critical  
**Category:** blue-team  
**Prerequisites:** Internet connection

**Test Steps:**
1. Lookup 8.8.8.8 reputation
2. Check geolocation data

**Expected Result:**
- IP info returned
- Geolocation present
- Risk score included

---

### TC-041: cyber_cve_lookup - Vulnerability Lookup
**Priority:** High  
**Category:** blue-team  
**Prerequisites:** Internet connection to NVD

**Test Steps:**
1. Lookup CVE-2021-44228 (Log4Shell)
2. Verify details returned

**Expected Result:**
- CVE found
- Description present
- Severity and CVSS score
- References included

---

### TC-042: cyber_cve_search - CVE Database Search
**Priority:** High  
**Category:** blue-team  
**Prerequisites:** NVD API accessible

**Test Steps:**
1. Search for "log4j"
2. Verify results returned

**Expected Result:**
- CVE list returned
- Descriptions truncated appropriately
- Severity indicated

---

### TC-043: cyber_threat_domain_lookup - Domain Analysis
**Priority:** Medium  
**Category:** blue-team  
**Prerequisites:** DNS available

**Test Steps:**
1. Analyze domain security indicators
2. Check DNS records

**Expected Result:**
- Domain info returned
- IP addresses listed
- Security indicators present

---

### TC-044: cyber_threat_hash_lookup - Hash Check
**Priority:** Medium  
**Category:** blue-team  
**Prerequisites:** None

**Test Steps:**
1. Check file hash
2. Verify hash type detection

**Expected Result:**
- Hash type identified (MD5/SHA1/SHA256)
- Status returned
- Note about VirusTotal if not configured

---

---

## 🟣 PURPLE TEAM (4 tools)

### TC-045: cyber_mitre_lookup - Technique Lookup
**Priority:** Critical  
**Category:** purple-team  
**Prerequisites:** None (local database)

**Test Steps:**
1. Lookup T1566 (Phishing)
2. Verify technique details

**Expected Result:**
- Technique found
- Name and description present
- Tactics listed
- Detection guidance included

---

### TC-046: cyber_mitre_search - Technique Search
**Priority:** High  
**Category:** purple-team  
**Prerequisites:** None

**Test Steps:**
1. Search for "credential"
2. Verify matching techniques returned

**Expected Result:**
- Matching techniques found
- IDs and names listed
- Tactics shown

---

### TC-047: cyber_exercise_create - Exercise Creation
**Priority:** High  
**Category:** purple-team  
**Prerequisites:** None

**Test Steps:**
1. Create purple team exercise
2. Add techniques to test
3. Verify exercise created

**Expected Result:**
- Exercise ID generated
- Name and description stored
- Techniques validated
- Status set to "planned"

---

### TC-048: cyber_coverage_map - Detection Coverage
**Priority:** Medium  
**Category:** purple-team  
**Prerequisites:** None

**Test Steps:**
1. Map coverage with sample detected techniques
2. Calculate coverage percentage

**Expected Result:**
- Coverage percentage calculated
- Detected vs total listed
- Gaps identified
- Tactic-level breakdown

---

## Test Execution Summary

| Category | Count | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Browser | 6 | 2 | 4 | 2 | 0 |
| System | 5 | 1 | 3 | 1 | 1 |
| Image | 4 | 0 | 2 | 2 | 0 |
| Docker | 6 | 2 | 4 | 2 | 0 |
| WebSocket | 4 | 3 | 1 | 0 | 0 |
| Network | 4 | 2 | 2 | 2 | 0 |
| Notify | 2 | 0 | 0 | 1 | 1 |
| Red Team | 4 | 1 | 3 | 0 | 0 |
| Blue Team | 5 | 1 | 3 | 2 | 0 |
| Purple Team | 4 | 2 | 2 | 1 | 0 |
| **TOTAL** | **44** | **14** | **24** | **13** | **3** |
