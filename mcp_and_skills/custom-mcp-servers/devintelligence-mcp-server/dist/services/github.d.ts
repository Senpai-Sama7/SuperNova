/**
 * GitHub API client with authentication and rate limiting
 */
import type { GitHubRepo, GitHubIssue, GitHubPullRequest } from "../types.js";
declare class GitHubClient {
    private client;
    constructor(token?: string);
    /**
     * Search repositories
     */
    searchRepos(query: string, sort?: string, order?: string, perPage?: number, page?: number): Promise<{
        items: GitHubRepo[];
        total_count: number;
    }>;
    /**
     * Get repository details
     */
    getRepo(owner: string, repo: string): Promise<GitHubRepo>;
    /**
     * List repository issues
     */
    listIssues(owner: string, repo: string, state?: "open" | "closed" | "all", labels?: string[], assignee?: string, perPage?: number, page?: number): Promise<GitHubIssue[]>;
    /**
     * Create a new issue
     */
    createIssue(owner: string, repo: string, title: string, body?: string, labels?: string[], assignees?: string[]): Promise<GitHubIssue>;
    /**
     * Update an issue
     */
    updateIssue(owner: string, repo: string, issueNumber: number, updates: {
        title?: string;
        body?: string;
        state?: "open" | "closed";
        labels?: string[];
        assignees?: string[];
    }): Promise<GitHubIssue>;
    /**
     * List pull requests
     */
    listPullRequests(owner: string, repo: string, state?: "open" | "closed" | "all", head?: string, base?: string, perPage?: number, page?: number): Promise<GitHubPullRequest[]>;
    /**
     * Get pull request details
     */
    getPullRequest(owner: string, repo: string, pullNumber: number): Promise<GitHubPullRequest>;
    /**
     * Create pull request review
     */
    createPullRequestReview(owner: string, repo: string, pullNumber: number, event: "APPROVE" | "REQUEST_CHANGES" | "COMMENT", body?: string, comments?: Array<{
        path: string;
        position?: number;
        line?: number;
        body: string;
    }>): Promise<unknown>;
    /**
     * Get repository contents
     */
    getContents(owner: string, repo: string, path?: string, ref?: string): Promise<unknown>;
    /**
     * List commits
     */
    listCommits(owner: string, repo: string, sha?: string, path?: string, author?: string, perPage?: number, page?: number): Promise<unknown[]>;
    private transformRepo;
    private transformIssue;
    private transformPullRequest;
}
export declare function getGitHubClient(): GitHubClient;
export declare function resetGitHubClient(): void;
export { handleApiError } from "./errors.js";
//# sourceMappingURL=github.d.ts.map