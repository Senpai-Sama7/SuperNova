/**
 * RALPH Test Runner
 * Direct tool testing for OMEGA MCP Server
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// Import all tool modules
import { registerSystemTools } from "../../src/tools/system.js";
import { registerNetworkTools } from "../../src/tools/network.js";
import { registerBrowserTools } from "../../src/tools/browser.js";
import { registerDockerTools } from "../../src/tools/docker.js";
import { registerImageTools } from "../../src/tools/image.js";
import { registerWebSocketTools } from "../../src/tools/websocket.js";
import { registerNotificationTools } from "../../src/tools/notify.js";
import { registerRedTeamTools } from "../../src/tools/cyber-redteam.js";
import { registerBlueTeamTools } from "../../src/tools/cyber-blueteam.js";
import { registerPurpleTeamTools } from "../../src/tools/cyber-purpleteam.js";

// Test configuration
const TEST_CONFIG = {
  timeout: 30000,
  buildDir: "../../dist"
};

// Test result type
interface TestResult {
  tc: string;
  name: string;
  status: "pass" | "fail" | "knownIssue";
  duration: number;
  error?: string;
  notes?: string;
}

// Create test server
function createTestServer(): McpServer {
  return new McpServer({
    name: "omega-test-server",
    version: "2.0.0"
  });
}

// Run specific test
async function runTest(tc: string, testFn: () => Promise<void>): Promise<TestResult> {
  const startTime = Date.now();
  try {
    await testFn();
    return {
      tc,
      name: tc,
      status: "pass",
      duration: Date.now() - startTime
    };
  } catch (error) {
    return {
      tc,
      name: tc,
      status: "fail",
      duration: Date.now() - startTime,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

// Export for use
export { createTestServer, runTest, TEST_CONFIG };
