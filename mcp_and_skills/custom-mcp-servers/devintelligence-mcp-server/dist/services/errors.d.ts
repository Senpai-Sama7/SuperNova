/**
 * Error handling utilities
 */
/**
 * Handle API errors with actionable messages
 */
export declare function handleApiError(error: unknown): string;
/**
 * Handle shell command errors
 */
export declare function handleShellError(error: unknown, command: string): string;
/**
 * Handle file system errors
 */
export declare function handleFsError(error: unknown, path: string): string;
/**
 * Handle database errors
 */
export declare function handleDbError(error: unknown, query?: string): string;
//# sourceMappingURL=errors.d.ts.map