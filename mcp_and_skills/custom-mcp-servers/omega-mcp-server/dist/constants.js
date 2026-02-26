/**
 * Constants for the Omni MCP Server
 */
/** Maximum response size in characters */
export const CHARACTER_LIMIT = 50000;
/** Default screenshot dimensions */
export const DEFAULT_VIEWPORT = { width: 1280, height: 720 };
/** Maximum screenshot dimensions */
export const MAX_VIEWPORT = { width: 3840, height: 2160 };
/** Browser timeout defaults (ms) */
export const BROWSER_TIMEOUT = 30000;
/** WebSocket default timeout (ms) */
export const WS_TIMEOUT = 10000;
/** Response format options */
export var ResponseFormat;
(function (ResponseFormat) {
    ResponseFormat["MARKDOWN"] = "markdown";
    ResponseFormat["JSON"] = "json";
})(ResponseFormat || (ResponseFormat = {}));
/** Docker default timeout (ms) */
export const DOCKER_TIMEOUT = 60000;
/** Maximum processes to list */
export const MAX_PROCESSES = 100;
//# sourceMappingURL=constants.js.map