"""
Execution Engine MCP Server

Provides safe command execution, build orchestration, and environment management.
"""

import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))

from base_server import BaseMCPServer
from mcp_types import MCPTool, MCPError, MCPErrorCode


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    pid: Optional[int] = None


class ExecutionEngineServer(BaseMCPServer):
    """MCP server for safe command execution."""
    
    # Allowed commands whitelist
    ALLOWED_COMMANDS = {
        'git', 'npm', 'yarn', 'pip', 'python', 'python3', 'pytest',
        'make', 'cmake', 'gcc', 'g++', 'go', 'cargo', 'rustc',
        'docker', 'docker-compose', 'kubectl', 'helm',
        'curl', 'wget', 'tar', 'zip', 'unzip',
        'cat', 'ls', 'pwd', 'echo', 'head', 'tail', 'grep', 'find',
        'mkdir', 'touch', 'rm', 'cp', 'mv', 'chmod', 'chown',
        'node', 'deno', 'bun', 'npx',
        'java', 'javac', 'mvn', 'gradle',
        'ruby', 'gem', 'bundle',
        'php', 'composer',
        'rustc', 'cargo', 'rustup',
    }
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'>\s*/dev/sda',
        r':\(\)\{\s*:\|:&\s*\};:',
        r'curl\s+.*\|\s*sh',
        r'wget\s+.*\|\s*sh',
        r'eval\s*\$',
        r'`.*rm.*`',
        r'\$\(.*rm.*\)',
    ]
    
    def __init__(self):
        super().__init__("execution-engine", "1.0.0")
        self.active_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def _setup_tools(self) -> None:
        """Register execution tools."""
        
        self.register_tool(MCPTool(
            name="execution/execute",
            description="Execute a command with safety controls",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "working_dir": {"type": "string", "description": "Working directory"},
                    "timeout": {"type": "integer", "default": 30000, "description": "Timeout in milliseconds"},
                    "env": {"type": "object", "description": "Environment variables"},
                    "capture_output": {"type": "boolean", "default": True},
                    "sandbox": {
                        "type": "object",
                        "properties": {
                            "network": {"type": "string", "enum": ["allowed", "isolated", "proxy"]},
                            "filesystem": {"type": "string", "enum": ["readonly", "workspace", "full"]},
                            "memory_limit": {"type": "string"},
                            "cpu_limit": {"type": "integer"}
                        }
                    }
                },
                "required": ["command"]
            }
        ), self._execute_command)
        
        self.register_tool(MCPTool(
            name="execution/execute_pipeline",
            description="Execute a pipeline of commands",
            input_schema={
                "type": "object",
                "properties": {
                    "commands": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Commands to pipe together"
                    },
                    "working_dir": {"type": "string"},
                    "timeout": {"type": "integer", "default": 60000}
                },
                "required": ["commands"]
            }
        ), self._execute_pipeline)
        
        self.register_tool(MCPTool(
            name="execution/build",
            description="Execute build commands for various build systems",
            input_schema={
                "type": "object",
                "properties": {
                    "system": {
                        "type": "string",
                        "enum": ["auto", "npm", "yarn", "make", "maven", "gradle", "cargo", "go"],
                        "default": "auto"
                    },
                    "target": {"type": "string", "default": "build"},
                    "working_dir": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}}
                },
                "required": []
            }
        ), self._build)
        
        self.register_tool(MCPTool(
            name="execution/test",
            description="Run tests with result parsing",
            input_schema={
                "type": "object",
                "properties": {
                    "framework": {
                        "type": "string",
                        "enum": ["auto", "pytest", "jest", "mocha", "unittest", "cargo"],
                        "default": "auto"
                    },
                    "pattern": {"type": "string", "description": "Test file pattern"},
                    "working_dir": {"type": "string"},
                    "coverage": {"type": "boolean", "default": True},
                    "parallel": {"type": "boolean", "default": True}
                },
                "required": []
            }
        ), self._run_tests)
        
        self.register_tool(MCPTool(
            name="execution/watch",
            description="Watch files for changes and run commands",
            input_schema={
                "type": "object",
                "properties": {
                    "paths": {"type": "array", "items": {"type": "string"}},
                    "command": {"type": "string"},
                    "patterns": {"type": "array", "items": {"type": "string"}},
                    "debounce": {"type": "integer", "default": 500}
                },
                "required": ["paths", "command"]
            }
        ), self._watch_files)
        
        self.register_tool(MCPTool(
            name="execution/kill",
            description="Kill a running process",
            input_schema={
                "type": "object",
                "properties": {
                    "pid": {"type": "integer"},
                    "signal": {"type": "string", "default": "SIGTERM"}
                },
                "required": ["pid"]
            }
        ), self._kill_process)
        
        self.register_tool(MCPTool(
            name="execution/get_status",
            description="Get status of a running or completed execution",
            input_schema={
                "type": "object",
                "properties": {
                    "execution_id": {"type": "string"}
                },
                "required": ["execution_id"]
            }
        ), self._get_status)
    
    def _validate_command(self, command: str) -> Optional[str]:
        """Validate command for safety."""
        # Extract command name
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return "Empty command"
        
        cmd_name = cmd_parts[0]
        
        # Check if command is in whitelist
        base_cmd = cmd_name.split('/')[-1]  # Handle full paths
        if base_cmd not in self.ALLOWED_COMMANDS:
            return f"Command '{base_cmd}' not in allowed list"
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return f"Command matches dangerous pattern"
        
        return None
    
    def _sanitize_output(self, output: str) -> str:
        """Sanitize output to remove secrets."""
        # Patterns to mask
        secret_patterns = [
            (r'(password|passwd|pwd)\s*=\s*\S+', r'\1=***'),
            (r'(api[_-]?key|token|secret)\s*=\s*["\']?\S+["\']?', r'\1=***'),
            (r'-----BEGIN\s+\w+\s+PRIVATE\s+KEY-----.*?-----END', '***PRIVATE_KEY_REDACTED***'),
            (r'sk-\w{20,}', 'sk-***'),
            (r'ghp_\w{30,}', 'ghp-***'),
        ]
        
        for pattern, replacement in secret_patterns:
            output = re.sub(pattern, replacement, output, flags=re.IGNORECASE | re.DOTALL)
        
        return output
    
    def _execute_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command safely."""
        command = args["command"]
        working_dir = args.get("working_dir", os.getcwd())
        timeout = args.get("timeout", 30000)  # Default 30s
        env_vars = args.get("env", {})
        capture_output = args.get("capture_output", True)
        
        # Validate command
        validation_error = self._validate_command(command)
        if validation_error:
            return {
                "success": False,
                "error": validation_error,
                "exit_code": -1
            }
        
        # Prepare environment
        env = os.environ.copy()
        env.update(env_vars)
        
        # Ensure working directory exists
        working_path = Path(working_dir)
        if not working_path.exists():
            return {
                "success": False,
                "error": f"Working directory does not exist: {working_dir}",
                "exit_code": -1
            }
        
        try:
            start_time = time.time()
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_path,
                env=env,
                capture_output=capture_output,
                text=True,
                timeout=timeout / 1000  # Convert ms to seconds
            )
            
            duration = int((time.time() - start_time) * 1000)
            
            # Sanitize output
            stdout = self._sanitize_output(result.stdout) if result.stdout else ""
            stderr = self._sanitize_output(result.stderr) if result.stderr else ""
            
            # Log execution
            execution_record = {
                "timestamp": time.time(),
                "command": command,
                "working_dir": working_dir,
                "exit_code": result.returncode,
                "duration_ms": duration
            }
            self.execution_history.append(execution_record)
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": duration
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout}ms",
                "exit_code": -1,
                "duration_ms": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exit_code": -1
            }
    
    def _execute_pipeline(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a pipeline of commands."""
        commands = args["commands"]
        working_dir = args.get("working_dir", os.getcwd())
        timeout = args.get("timeout", 60000)
        
        if not commands:
            return {"success": False, "error": "No commands provided"}
        
        # Validate all commands
        for cmd in commands:
            error = self._validate_command(cmd)
            if error:
                return {"success": False, "error": f"Validation failed for '{cmd}': {error}"}
        
        # Build pipeline
        pipeline = " | ".join(commands)
        
        return self._execute_command({
            "command": pipeline,
            "working_dir": working_dir,
            "timeout": timeout
        })
    
    def _build(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute build for detected or specified build system."""
        system = args.get("system", "auto")
        target = args.get("target", "build")
        working_dir = args.get("working_dir", os.getcwd())
        extra_args = args.get("args", [])
        
        working_path = Path(working_dir)
        
        # Auto-detect build system
        if system == "auto":
            if (working_path / "package.json").exists():
                system = "npm"
            elif (working_path / "Cargo.toml").exists():
                system = "cargo"
            elif (working_path / "pom.xml").exists():
                system = "maven"
            elif (working_path / "build.gradle").exists():
                system = "gradle"
            elif (working_path / "Makefile").exists():
                system = "make"
            elif (working_path / "go.mod").exists():
                system = "go"
            else:
                return {
                    "success": False,
                    "error": "Could not auto-detect build system"
                }
        
        # Build command based on system
        commands = {
            "npm": f"npm run {target}",
            "yarn": f"yarn {target}",
            "cargo": f"cargo {target}",
            "maven": f"mvn {target}",
            "gradle": f"gradle {target}",
            "make": f"make {target}",
            "go": f"go build {' '.join(extra_args)}",
        }
        
        command = commands.get(system)
        if not command:
            return {"success": False, "error": f"Unknown build system: {system}"}
        
        if extra_args and system != "go":
            command += " " + " ".join(extra_args)
        
        return self._execute_command({
            "command": command,
            "working_dir": working_dir,
            "timeout": 120000  # 2 minutes for builds
        })
    
    def _run_tests(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests with result parsing."""
        framework = args.get("framework", "auto")
        pattern = args.get("pattern")
        working_dir = args.get("working_dir", os.getcwd())
        coverage = args.get("coverage", True)
        parallel = args.get("parallel", True)
        
        working_path = Path(working_dir)
        
        # Auto-detect framework
        if framework == "auto":
            if (working_path / "pytest.ini").exists() or list(working_path.glob("test_*.py")):
                framework = "pytest"
            elif (working_path / "package.json").exists():
                framework = "jest"
            elif (working_path / "Cargo.toml").exists():
                framework = "cargo"
            elif list(working_path.glob("*_test.go")):
                framework = "go"
        
        # Build test command
        if framework == "pytest":
            cmd_parts = ["pytest"]
            if pattern:
                cmd_parts.append(pattern)
            if coverage:
                cmd_parts.append("--cov")
            if parallel:
                cmd_parts.append("-n auto")
            cmd_parts.append("--tb=short")
            cmd_parts.append("-v")
        elif framework == "jest":
            cmd_parts = ["npm test"]
            if coverage:
                cmd_parts.append("--coverage")
        elif framework == "cargo":
            cmd_parts = ["cargo test"]
            if pattern:
                cmd_parts.append(pattern)
        elif framework == "go":
            cmd_parts = ["go test"]
            if pattern:
                cmd_parts.append(pattern)
            else:
                cmd_parts.append("./...")
            cmd_parts.append("-v")
        else:
            return {"success": False, "error": f"Unknown test framework: {framework}"}
        
        command = " ".join(cmd_parts)
        
        return self._execute_command({
            "command": command,
            "working_dir": working_dir,
            "timeout": 300000  # 5 minutes for tests
        })
    
    def _watch_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Set up file watching (simplified version)."""
        # Note: Full implementation would require async file watching
        # This is a simplified synchronous version
        return {
            "success": True,
            "message": "File watching requires async mode. Use execution/execute with appropriate watch tools.",
            "suggestion": "Consider using: npm run watch, or pytest-watch, or entr"
        }
    
    def _kill_process(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Kill a running process."""
        pid = args["pid"]
        signal = args.get("signal", "SIGTERM")
        
        try:
            import signal as sigmodule
            sig = getattr(sigmodule, signal, sigmodule.SIGTERM)
            os.kill(pid, sig)
            return {
                "success": True,
                "message": f"Sent {signal} to process {pid}"
            }
        except ProcessLookupError:
            return {
                "success": False,
                "error": f"Process {pid} not found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution status."""
        execution_id = args.get("execution_id")
        
        # In a real implementation, track by ID
        # For now, return last execution
        if self.execution_history:
            last = self.execution_history[-1]
            return {
                "found": True,
                "execution": last
            }
        
        return {
            "found": False,
            "error": "No execution history found"
        }


def main():
    server = ExecutionEngineServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    import asyncio
    main()
