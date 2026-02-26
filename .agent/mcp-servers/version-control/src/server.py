"""
Version Control MCP Server

Provides Git operations, checkpoint management, and collaboration features.
"""

import asyncio
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))

from base_server import BaseMCPServer
from mcp_types import MCPTool


@dataclass
class GitStatus:
    branch: str
    ahead: int
    behind: int
    staged: List[str]
    unstaged: List[str]
    untracked: List[str]
    is_clean: bool


class VersionControlServer(BaseMCPServer):
    """MCP server for version control operations."""
    
    def __init__(self):
        super().__init__("version-control", "1.0.0")
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
    
    def _setup_tools(self) -> None:
        """Register version control tools."""
        
        self.register_tool(MCPTool(
            name="git/status",
            description="Get repository status",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Path to repository"}
                },
                "required": []
            }
        ), self._git_status)
        
        self.register_tool(MCPTool(
            name="git/diff",
            description="Show diff of changes",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "staged": {"type": "boolean", "default": False},
                    "file": {"type": "string"},
                    "commit": {"type": "string", "description": "Show diff for specific commit"}
                },
                "required": []
            }
        ), self._git_diff)
        
        self.register_tool(MCPTool(
            name="git/log",
            description="Show commit history",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "file": {"type": "string"},
                    "author": {"type": "string"},
                    "since": {"type": "string"},
                    "format": {"type": "string", "enum": ["short", "full", "oneline"], "default": "short"}
                },
                "required": []
            }
        ), self._git_log)
        
        self.register_tool(MCPTool(
            name="git/add",
            description="Stage files for commit",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "files": {"type": "array", "items": {"type": "string"}},
                    "all": {"type": "boolean", "default": False}
                },
                "required": []
            }
        ), self._git_add)
        
        self.register_tool(MCPTool(
            name="git/commit",
            description="Create a commit",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "message": {"type": "string"},
                    "files": {"type": "array", "items": {"type": "string"}},
                    "amend": {"type": "boolean", "default": False},
                    "auto_stage": {"type": "boolean", "default": False}
                },
                "required": ["message"]
            }
        ), self._git_commit)
        
        self.register_tool(MCPTool(
            name="git/branch",
            description="List, create, or switch branches",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "action": {"type": "string", "enum": ["list", "create", "switch", "delete"], "default": "list"},
                    "branch": {"type": "string"},
                    "base": {"type": "string"}
                },
                "required": []
            }
        ), self._git_branch)
        
        self.register_tool(MCPTool(
            name="git/checkout",
            description="Checkout a branch or file",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "target": {"type": "string"},
                    "create_branch": {"type": "boolean", "default": False}
                },
                "required": ["target"]
            }
        ), self._git_checkout)
        
        self.register_tool(MCPTool(
            name="git/reset",
            description="Reset changes",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "mode": {"type": "string", "enum": ["soft", "mixed", "hard"], "default": "mixed"},
                    "commit": {"type": "string", "default": "HEAD"}
                },
                "required": []
            }
        ), self._git_reset)
        
        self.register_tool(MCPTool(
            name="git/stash",
            description="Stash changes",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "action": {"type": "string", "enum": ["push", "pop", "list", "drop"], "default": "push"},
                    "message": {"type": "string"}
                },
                "required": []
            }
        ), self._git_stash)
        
        self.register_tool(MCPTool(
            name="git/blame",
            description="Show line annotations",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "file": {"type": "string"},
                    "lines": {"type": "string", "description": "Line range (e.g., '10,20')"}
                },
                "required": ["file"]
            }
        ), self._git_blame)
        
        self.register_tool(MCPTool(
            name="git/remote",
            description="Manage remotes",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "action": {"type": "string", "enum": ["list", "add", "remove", "set-url"], "default": "list"},
                    "name": {"type": "string"},
                    "url": {"type": "string"}
                },
                "required": []
            }
        ), self._git_remote)
        
        self.register_tool(MCPTool(
            name="checkpoint/create",
            description="Create a lightweight checkpoint",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name"]
            }
        ), self._create_checkpoint)
        
        self.register_tool(MCPTool(
            name="checkpoint/restore",
            description="Restore to a checkpoint",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"},
                    "checkpoint_id": {"type": "string"}
                },
                "required": ["checkpoint_id"]
            }
        ), self._restore_checkpoint)
        
        self.register_tool(MCPTool(
            name="checkpoint/list",
            description="List available checkpoints",
            input_schema={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string"}
                },
                "required": []
            }
        ), self._list_checkpoints)
    
    def _run_git(self, repo_path: str, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", repo_path] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if check and result.returncode != 0:
            raise Exception(f"Git command failed: {result.stderr}")
        
        return result
    
    def _git_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository status."""
        repo_path = args.get("repo_path", os.getcwd())
        
        try:
            # Check if git repo
            if not (Path(repo_path) / ".git").exists():
                return {"error": "Not a git repository", "is_git_repo": False}
            
            # Get branch
            branch_result = self._run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"], check=False)
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get ahead/behind
            ahead_behind = self._run_git(repo_path, ["rev-list", "--left-right", "--count", f"HEAD...@{u}"], check=False)
            ahead, behind = 0, 0
            if ahead_behind.returncode == 0:
                counts = ahead_behind.stdout.strip().split()
                if len(counts) == 2:
                    ahead, behind = int(counts[0]), int(counts[1])
            
            # Parse status
            status_result = self._run_git(repo_path, ["status", "--porcelain"], check=False)
            
            staged = []
            unstaged = []
            untracked = []
            
            for line in status_result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                status_code = line[:2]
                filename = line[3:]
                
                if status_code[0] in 'MADRC':
                    staged.append(filename)
                if status_code[1] in 'MD':
                    unstaged.append(filename)
                if status_code == '??':
                    untracked.append(filename)
            
            is_clean = len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0
            
            return {
                "is_git_repo": True,
                "branch": branch,
                "ahead": ahead,
                "behind": behind,
                "staged": staged,
                "unstaged": unstaged,
                "untracked": untracked,
                "is_clean": is_clean
            }
            
        except Exception as e:
            return {"error": str(e), "is_git_repo": False}
    
    def _git_diff(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Show diff."""
        repo_path = args.get("repo_path", os.getcwd())
        staged = args.get("staged", False)
        file = args.get("file")
        commit = args.get("commit")
        
        try:
            cmd = ["diff"]
            
            if commit:
                cmd = ["show", commit]
            elif staged:
                cmd.append("--staged")
            
            if file:
                cmd.append(file)
            
            result = self._run_git(repo_path, cmd, check=False)
            
            return {
                "success": result.returncode == 0,
                "diff": result.stdout,
                "has_changes": len(result.stdout) > 0
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_log(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Show commit history."""
        repo_path = args.get("repo_path", os.getcwd())
        limit = args.get("limit", 10)
        file = args.get("file")
        author = args.get("author")
        since = args.get("since")
        fmt = args.get("format", "short")
        
        try:
            format_str = {
                "short": "%h %s (%cr) <%an>",
                "full": "%H%n%an <%ae>%n%ad%n%s%n%b---",
                "oneline": "%h %s"
            }.get(fmt, "%h %s")
            
            cmd = ["log", f"--pretty=format:{format_str}", f"-n{limit}"]
            
            if author:
                cmd.extend(["--author", author])
            if since:
                cmd.extend(["--since", since])
            if file:
                cmd.append(file)
            
            result = self._run_git(repo_path, cmd)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    commits.append(line)
            
            return {
                "count": len(commits),
                "commits": commits
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_add(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stage files."""
        repo_path = args.get("repo_path", os.getcwd())
        files = args.get("files", [])
        all_files = args.get("all", False)
        
        try:
            if all_files:
                result = self._run_git(repo_path, ["add", "."])
            elif files:
                result = self._run_git(repo_path, ["add"] + files)
            else:
                return {"error": "No files specified and all=false"}
            
            return {
                "success": True,
                "staged": files if files else ["all files"]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_commit(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create commit."""
        repo_path = args.get("repo_path", os.getcwd())
        message = args["message"]
        files = args.get("files", [])
        amend = args.get("amend", False)
        auto_stage = args.get("auto_stage", False)
        
        try:
            cmd = ["commit", "-m", message]
            
            if amend:
                cmd.append("--amend")
            
            if auto_stage:
                cmd.append("-a")
            
            if files and not auto_stage:
                # Stage specific files first
                self._run_git(repo_path, ["add"] + files)
            
            result = self._run_git(repo_path, cmd)
            
            # Parse commit hash
            hash_result = self._run_git(repo_path, ["rev-parse", "HEAD"])
            commit_hash = hash_result.stdout.strip()
            
            return {
                "success": True,
                "commit_hash": commit_hash[:8],
                "message": message
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_branch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Branch operations."""
        repo_path = args.get("repo_path", os.getcwd())
        action = args.get("action", "list")
        branch = args.get("branch")
        base = args.get("base")
        
        try:
            if action == "list":
                result = self._run_git(repo_path, ["branch", "-vv"])
                branches = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        current = line.startswith('*')
                        name = line[2:].split()[0] if current else line.strip().split()[0]
                        branches.append({"name": name, "current": current})
                return {"branches": branches}
            
            elif action == "create":
                if not branch:
                    return {"error": "Branch name required"}
                cmd = ["checkout", "-b", branch]
                if base:
                    cmd.append(base)
                self._run_git(repo_path, cmd)
                return {"success": True, "created": branch}
            
            elif action == "switch":
                if not branch:
                    return {"error": "Branch name required"}
                self._run_git(repo_path, ["checkout", branch])
                return {"success": True, "switched_to": branch}
            
            elif action == "delete":
                if not branch:
                    return {"error": "Branch name required"}
                self._run_git(repo_path, ["branch", "-d", branch])
                return {"success": True, "deleted": branch}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_checkout(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Checkout files or branches."""
        repo_path = args.get("repo_path", os.getcwd())
        target = args["target"]
        create_branch = args.get("create_branch", False)
        
        try:
            cmd = ["checkout"]
            if create_branch:
                cmd.append("-b")
            cmd.append(target)
            
            self._run_git(repo_path, cmd)
            
            return {
                "success": True,
                "checked_out": target
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_reset(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reset changes."""
        repo_path = args.get("repo_path", os.getcwd())
        mode = args.get("mode", "mixed")
        commit = args.get("commit", "HEAD")
        
        try:
            cmd = ["reset"]
            
            if mode == "soft":
                cmd.append("--soft")
            elif mode == "hard":
                cmd.append("--hard")
            # mixed is default
            
            cmd.append(commit)
            
            self._run_git(repo_path, cmd)
            
            return {
                "success": True,
                "mode": mode,
                "commit": commit
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_stash(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stash operations."""
        repo_path = args.get("repo_path", os.getcwd())
        action = args.get("action", "push")
        message = args.get("message")
        
        try:
            if action == "push":
                cmd = ["stash", "push"]
                if message:
                    cmd.extend(["-m", message])
                self._run_git(repo_path, cmd)
                return {"success": True, "action": "pushed"}
            
            elif action == "pop":
                self._run_git(repo_path, ["stash", "pop"])
                return {"success": True, "action": "popped"}
            
            elif action == "list":
                result = self._run_git(repo_path, ["stash", "list"])
                stashes = result.stdout.strip().split('\n') if result.stdout else []
                return {"stashes": stashes}
            
            elif action == "drop":
                self._run_git(repo_path, ["stash", "drop"])
                return {"success": True, "action": "dropped"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_blame(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Show blame annotations."""
        repo_path = args.get("repo_path", os.getcwd())
        file = args["file"]
        lines = args.get("lines")
        
        try:
            cmd = ["blame", file]
            
            if lines:
                cmd.extend(["-L", lines])
            
            result = self._run_git(repo_path, cmd)
            
            annotations = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Parse: hash (author date line) content
                    match = re.match(r'^(\w+)\s+\(([^)]+)\)\s+(.*)$', line)
                    if match:
                        annotations.append({
                            "commit": match.group(1),
                            "info": match.group(2),
                            "line": match.group(3)
                        })
            
            return {
                "file": file,
                "annotations": annotations
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _git_remote(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remote operations."""
        repo_path = args.get("repo_path", os.getcwd())
        action = args.get("action", "list")
        name = args.get("name")
        url = args.get("url")
        
        try:
            if action == "list":
                result = self._run_git(repo_path, ["remote", "-v"])
                remotes = {}
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            remote_name = parts[0]
                            remote_url = parts[1]
                            remote_type = parts[2].strip('()') if len(parts) > 2 else 'fetch'
                            if remote_name not in remotes:
                                remotes[remote_name] = {}
                            remotes[remote_name][remote_type] = remote_url
                
                return {"remotes": remotes}
            
            elif action == "add":
                if not name or not url:
                    return {"error": "Name and URL required"}
                self._run_git(repo_path, ["remote", "add", name, url])
                return {"success": True, "added": name}
            
            elif action == "remove":
                if not name:
                    return {"error": "Name required"}
                self._run_git(repo_path, ["remote", "remove", name])
                return {"success": True, "removed": name}
            
            elif action == "set-url":
                if not name or not url:
                    return {"error": "Name and URL required"}
                self._run_git(repo_path, ["remote", "set-url", name, url])
                return {"success": True, "updated": name}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _create_checkpoint(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lightweight checkpoint using git stash."""
        repo_path = args.get("repo_path", os.getcwd())
        name = args["name"]
        description = args.get("description", "")
        
        try:
            # Create stash with name
            stash_message = f"checkpoint: {name}"
            if description:
                stash_message += f" - {description}"
            
            self._run_git(repo_path, ["stash", "push", "-m", stash_message, "-u"])
            
            # Get stash reference
            result = self._run_git(repo_path, ["stash", "list"])
            stash_ref = result.stdout.split('\n')[0].split(':')[0] if result.stdout else "stash@{0}"
            
            checkpoint_id = f"checkpoint-{name}-{int(datetime.now().timestamp())}"
            
            self.checkpoints[checkpoint_id] = {
                "id": checkpoint_id,
                "name": name,
                "description": description,
                "stash_ref": stash_ref,
                "created": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "message": f"Checkpoint '{name}' created"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _restore_checkpoint(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Restore to a checkpoint."""
        repo_path = args.get("repo_path", os.getcwd())
        checkpoint_id = args["checkpoint_id"]
        
        try:
            checkpoint = self.checkpoints.get(checkpoint_id)
            if not checkpoint:
                return {"error": f"Checkpoint {checkpoint_id} not found"}
            
            # Apply the stash
            self._run_git(repo_path, ["stash", "pop", checkpoint["stash_ref"]])
            
            return {
                "success": True,
                "restored": checkpoint_id,
                "name": checkpoint["name"]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _list_checkpoints(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available checkpoints."""
        repo_path = args.get("repo_path", os.getcwd())
        
        checkpoints = [
            {"id": k, **v}
            for k, v in self.checkpoints.items()
        ]
        
        return {
            "count": len(checkpoints),
            "checkpoints": checkpoints
        }


def main():
    server = VersionControlServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    import asyncio
    main()
