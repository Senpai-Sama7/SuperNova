#!/usr/bin/env node
/**
 * OMEGA MCP Server v2.0
 *
 * THE ULTIMATE COMBINATION:
 *
 * 🌐 OMNICAPABILITIES (31 tools):
 * - Browser Automation (6): Puppeteer-based web automation
 * - System Monitoring (5): Real-time CPU/memory/disk metrics
 * - Image Processing (4): OCR, resize, convert
 * - Docker Management (6): Container control
 * - WebSocket Client (4): Persistent connections
 * - Network Tools (4): Port scanning, ping, DNS
 * - Notifications (2): Desktop alerts
 *
 * 🛡️ PURPLESHIELD CYBERSECURITY (13 tools):
 * - Red Team (4): Subdomain enum, DNS analysis, WHOIS, header analysis
 * - Blue Team (5): Threat intel, IP/domain/hash lookup, CVE search
 * - Purple Team (4): MITRE ATT&CK, exercise management, coverage mapping
 *
 * TOTAL: 44 TOOLS
 *
 * Environment Variables:
 *   VIRUSTOTAL_API_KEY - For VirusTotal threat intel lookups
 *   TRANSPORT - 'stdio' (default) or 'http'
 *   PORT - HTTP port when using http transport (default: 3000)
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import express from "express";
// Omni Tools
import { registerBrowserTools } from "./tools/browser.js";
import { registerSystemTools } from "./tools/system.js";
import { registerImageTools } from "./tools/image.js";
import { registerDockerTools } from "./tools/docker.js";
import { registerWebSocketTools } from "./tools/websocket.js";
import { registerNetworkTools } from "./tools/network.js";
import { registerNotificationTools } from "./tools/notify.js";
// PurpleShield Cyber Tools
import { registerRedTeamTools } from "./tools/cyber-redteam.js";
import { registerBlueTeamTools } from "./tools/cyber-blueteam.js";
import { registerPurpleTeamTools } from "./tools/cyber-purpleteam.js";
// Server metadata
const SERVER_NAME = "omega-mcp-server";
const SERVER_VERSION = "2.0.0";
/**
 * Create and configure the MCP server with ALL tools
 */
function createServer() {
    const server = new McpServer({
        name: SERVER_NAME,
        version: SERVER_VERSION
    });
    // ============================================
    // OMNICAPABILITIES (31 tools)
    // ============================================
    registerBrowserTools(server); // 6 tools
    registerSystemTools(server); // 5 tools
    registerImageTools(server); // 4 tools
    registerDockerTools(server); // 6 tools
    registerWebSocketTools(server); // 4 tools
    registerNetworkTools(server); // 4 tools
    registerNotificationTools(server); // 2 tools
    // ============================================
    // PURPLESHIELD CYBERSECURITY (13 tools)
    // ============================================
    registerRedTeamTools(server); // 4 tools
    registerBlueTeamTools(server); // 5 tools
    registerPurpleTeamTools(server); // 4 tools
    return server;
}
/**
 * Run server with stdio transport (for local use)
 */
async function runStdio() {
    const server = createServer();
    const transport = new StdioServerTransport();
    await server.connect(transport);
    // Log to stderr (stdout is reserved for MCP protocol)
    console.error(`╔══════════════════════════════════════════════════════════════╗`);
    console.error(`║  🚀 OMEGA MCP Server v${SERVER_VERSION}                          ║`);
    console.error(`║  The Ultimate AI Supercomputer Interface                      ║`);
    console.error(`╠══════════════════════════════════════════════════════════════╣`);
    console.error(`║  🌐 Omni Capabilities (31):                                  ║`);
    console.error(`║     Browser(6) System(5) Image(4) Docker(6)                  ║`);
    console.error(`║     WebSocket(4) Network(4) Notify(2)                        ║`);
    console.error(`║                                                              ║`);
    console.error(`║  🛡️  PurpleShield Cyber (13):                                ║`);
    console.error(`║     Red Team(4) Blue Team(5) Purple Team(4)                  ║`);
    console.error(`║                                                              ║`);
    console.error(`║  TOTAL: 44 Tools                                             ║`);
    console.error(`╚══════════════════════════════════════════════════════════════╝`);
}
/**
 * Run server with HTTP transport (for remote use)
 */
async function runHTTP() {
    const server = createServer();
    const app = express();
    app.use(express.json());
    // Health check endpoint
    app.get("/health", (_req, res) => {
        res.json({
            status: "healthy",
            server: SERVER_NAME,
            version: SERVER_VERSION,
            capabilities: {
                omni: {
                    browser: 6,
                    system: 5,
                    image: 4,
                    docker: 6,
                    websocket: 4,
                    network: 4,
                    notify: 2,
                    total: 31
                },
                cybersecurity: {
                    red_team: 4,
                    blue_team: 5,
                    purple_team: 4,
                    total: 13
                },
                grand_total: 44
            },
            timestamp: new Date().toISOString()
        });
    });
    // MCP endpoint
    app.post("/mcp", async (req, res) => {
        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
            enableJsonResponse: true
        });
        res.on("close", () => transport.close());
        await server.connect(transport);
        await transport.handleRequest(req, res, req.body);
    });
    const port = parseInt(process.env.PORT || "3000", 10);
    app.listen(port, () => {
        console.error(`╔══════════════════════════════════════════════════════════════╗`);
        console.error(`║  🚀 OMEGA MCP Server v${SERVER_VERSION} - HTTP Mode                 ║`);
        console.error(`╠══════════════════════════════════════════════════════════════╣`);
        console.error(`║  Endpoint: http://localhost:${port}/mcp                          ║`);
        console.error(`║  Health:   http://localhost:${port}/health                       ║`);
        console.error(`╚══════════════════════════════════════════════════════════════╝`);
    });
}
/**
 * Main entry point
 */
async function main() {
    const transport = process.env.TRANSPORT || "stdio";
    try {
        if (transport === "http") {
            await runHTTP();
        }
        else {
            await runStdio();
        }
    }
    catch (error) {
        console.error("Failed to start server:", error);
        process.exit(1);
    }
}
// Handle uncaught errors
process.on("uncaughtException", (error) => {
    console.error("Uncaught exception:", error);
    process.exit(1);
});
process.on("unhandledRejection", (reason) => {
    console.error("Unhandled rejection:", reason);
    process.exit(1);
});
// Start the server
main();
//# sourceMappingURL=index.js.map