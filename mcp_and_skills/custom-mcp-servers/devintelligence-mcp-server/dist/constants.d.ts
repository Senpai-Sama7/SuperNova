/**
 * Constants for the DevIntelligence MCP Server
 */
/** Maximum response size in characters to prevent context overflow */
export declare const CHARACTER_LIMIT = 50000;
/** Default pagination limit */
export declare const DEFAULT_LIMIT = 20;
/** Maximum pagination limit */
export declare const MAX_LIMIT = 100;
/** Default timeout for shell commands (ms) */
export declare const DEFAULT_SHELL_TIMEOUT = 30000;
/** Maximum timeout for shell commands (ms) */
export declare const MAX_SHELL_TIMEOUT = 300000;
/** GitHub API base URL */
export declare const GITHUB_API_BASE = "https://api.github.com";
/** Common code file extensions for analysis */
export declare const CODE_EXTENSIONS: string[];
/** Response format options */
export declare enum ResponseFormat {
    MARKDOWN = "markdown",
    JSON = "json"
}
/** Shell command allowlist patterns (for safety) */
export declare const DANGEROUS_COMMANDS: RegExp[];
//# sourceMappingURL=constants.d.ts.map