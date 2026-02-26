/**
 * GitHub API client with authentication and rate limiting
 */
import axios from "axios";
import { GITHUB_API_BASE } from "../constants.js";
class GitHubClient {
    client;
    constructor(token) {
        const headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        this.client = axios.create({
            baseURL: GITHUB_API_BASE,
            headers,
            timeout: 30000
        });
    }
    /**
     * Search repositories
     */
    async searchRepos(query, sort, order, perPage = 30, page = 1) {
        const response = await this.client.get("/search/repositories", {
            params: { q: query, sort, order, per_page: perPage, page }
        });
        return {
            total_count: response.data.total_count,
            items: response.data.items.map((item) => this.transformRepo(item))
        };
    }
    /**
     * Get repository details
     */
    async getRepo(owner, repo) {
        const response = await this.client.get(`/repos/${owner}/${repo}`);
        return this.transformRepo(response.data);
    }
    /**
     * List repository issues
     */
    async listIssues(owner, repo, state, labels, assignee, perPage = 30, page = 1) {
        const params = {
            per_page: perPage,
            page,
            sort: "created",
            direction: "desc"
        };
        if (state && state !== "all")
            params.state = state;
        if (labels && labels.length > 0)
            params.labels = labels.join(",");
        if (assignee)
            params.assignee = assignee;
        const response = await this.client.get(`/repos/${owner}/${repo}/issues`, { params });
        return response.data.map((item) => this.transformIssue(item));
    }
    /**
     * Create a new issue
     */
    async createIssue(owner, repo, title, body, labels, assignees) {
        const data = { title };
        if (body)
            data.body = body;
        if (labels)
            data.labels = labels;
        if (assignees)
            data.assignees = assignees;
        const response = await this.client.post(`/repos/${owner}/${repo}/issues`, data);
        return this.transformIssue(response.data);
    }
    /**
     * Update an issue
     */
    async updateIssue(owner, repo, issueNumber, updates) {
        const response = await this.client.patch(`/repos/${owner}/${repo}/issues/${issueNumber}`, updates);
        return this.transformIssue(response.data);
    }
    /**
     * List pull requests
     */
    async listPullRequests(owner, repo, state, head, base, perPage = 30, page = 1) {
        const params = {
            per_page: perPage,
            page,
            sort: "created",
            direction: "desc"
        };
        if (state && state !== "all")
            params.state = state;
        if (head)
            params.head = head;
        if (base)
            params.base = base;
        const response = await this.client.get(`/repos/${owner}/${repo}/pulls`, { params });
        return response.data.map((item) => this.transformPullRequest(item));
    }
    /**
     * Get pull request details
     */
    async getPullRequest(owner, repo, pullNumber) {
        const response = await this.client.get(`/repos/${owner}/${repo}/pulls/${pullNumber}`);
        return this.transformPullRequest(response.data);
    }
    /**
     * Create pull request review
     */
    async createPullRequestReview(owner, repo, pullNumber, event, body, comments) {
        const data = { event };
        if (body)
            data.body = body;
        if (comments)
            data.comments = comments;
        const response = await this.client.post(`/repos/${owner}/${repo}/pulls/${pullNumber}/reviews`, data);
        return response.data;
    }
    /**
     * Get repository contents
     */
    async getContents(owner, repo, path = "", ref) {
        const params = {};
        if (ref)
            params.ref = ref;
        const response = await this.client.get(`/repos/${owner}/${repo}/contents/${path}`, { params });
        return response.data;
    }
    /**
     * List commits
     */
    async listCommits(owner, repo, sha, path, author, perPage = 30, page = 1) {
        const params = {
            per_page: perPage,
            page
        };
        if (sha)
            params.sha = sha;
        if (path)
            params.path = path;
        if (author)
            params.author = author;
        const response = await this.client.get(`/repos/${owner}/${repo}/commits`, { params });
        return response.data;
    }
    // Transformers
    transformRepo(data) {
        return {
            id: data.id,
            name: data.name,
            full_name: data.full_name,
            description: data.description,
            url: data.html_url,
            stars: data.stargazers_count,
            forks: data.forks_count,
            open_issues: data.open_issues_count,
            language: data.language,
            created_at: data.created_at,
            updated_at: data.updated_at,
            is_private: data.private
        };
    }
    transformIssue(data) {
        return {
            number: data.number,
            title: data.title,
            body: data.body,
            state: data.state,
            user: data.user?.login || "unknown",
            labels: data.labels?.map((l) => l.name) || [],
            created_at: data.created_at,
            updated_at: data.updated_at,
            closed_at: data.closed_at,
            url: data.html_url
        };
    }
    transformPullRequest(data) {
        return {
            number: data.number,
            title: data.title,
            body: data.body,
            state: data.merged ? "merged" : data.state,
            user: data.user?.login || "unknown",
            head_branch: data.head?.ref || "unknown",
            base_branch: data.base?.ref || "unknown",
            created_at: data.created_at,
            updated_at: data.updated_at,
            merged_at: data.merged_at,
            url: data.html_url
        };
    }
}
// Singleton instance
let githubClient = null;
export function getGitHubClient() {
    if (!githubClient) {
        const token = process.env.GITHUB_TOKEN;
        githubClient = new GitHubClient(token);
    }
    return githubClient;
}
export function resetGitHubClient() {
    githubClient = null;
}
// Re-export handleApiError for convenience
export { handleApiError } from "./errors.js";
//# sourceMappingURL=github.js.map