/**
 * Shared formatting utilities for responses
 */
import { ResponseFormat } from "../constants.js";
import type { PaginationInfo } from "../types.js";
/**
 * Format content based on response format preference
 */
export declare function formatResponse<T>(data: T, format: ResponseFormat, markdownFormatter: (data: T) => string): {
    text: string;
    structured: T;
    truncated?: boolean;
};
/**
 * Format pagination info as markdown
 */
export declare function formatPagination(info: PaginationInfo): string;
/**
 * Format bytes to human readable string
 */
export declare function formatBytes(bytes: number): string;
/**
 * Format timestamp to human readable string
 */
export declare function formatTimestamp(timestamp: string | number | Date): string;
/**
 * Escape markdown special characters
 */
export declare function escapeMarkdown(text: string): string;
/**
 * Create a code block in markdown
 */
export declare function codeBlock(code: string, language?: string): string;
/**
 * Truncate text with ellipsis
 */
export declare function truncateText(text: string, maxLength: number): string;
//# sourceMappingURL=formatters.d.ts.map