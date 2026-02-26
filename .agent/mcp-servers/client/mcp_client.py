"""
MCP Client for Agentic AI Coding CLI

Unified client that manages connections to all MCP servers with safety integration.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'safety-layer', 'src'))

from mcp_types import MCPRequest, MCPResponse, ExecutionContext
from policy_engine import PolicyEngine, SafetyMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str]
    enabled: bool = True


class MCPClient:
    """
    Unified MCP client for agentic coding CLI.
    Manages multiple MCP server connections with safety middleware.
    """
    
    DEFAULT_SERVERS = [
        ServerConfig(
            name="code-intelligence",
            command="python",
            args=["code-intelligence/src/server.py"]
        ),
        ServerConfig(
            name="execution-engine",
            command="python",
            args=["execution-engine/src/server.py"]
        ),
        ServerConfig(
            name="version-control",
            command="python",
            args=["version-control/src/server.py"]
        ),
        ServerConfig(
            name="quality-assurance",
            command="python",
            args=["quality-assurance/src/server.py"]
        ),
        ServerConfig(
            name="knowledge-integration",
            command="python",
            args=["knowledge-integration/src/server.py"]
        ),
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.servers: Dict[str, subprocess.Popen] = {}
        self.server_configs: Dict[str, ServerConfig] = {}
        self.policy_engine = PolicyEngine()
        self.safety_middleware = SafetyMiddleware(self.policy_engine)
        self.execution_context: Optional[ExecutionContext] = None
        
        # Load configuration
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        else:
            self._load_default_servers()
    
    def _load_default_servers(self) -> None:
        """Load default server configurations."""
        for config in self.DEFAULT_SERVERS:
            self.server_configs[config.name] = config
    
    def _load_config(self, config_path: str) -> None:
        """Load server configuration from file."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        for server_config in config.get("servers", []):
            sc = ServerConfig(
                name=server_config["name"],
                command=server_config["command"],
                args=server_config["args"],
                enabled=server_config.get("enabled", True)
            )
            self.server_configs[sc.name] = sc
    
    async def start_servers(self) -> None:
        """Start all configured MCP servers."""
        base_path = Path(__file__).parent.parent
        
        for name, config in self.server_configs.items():
            if not config.enabled:
                logger.info(f"Server {name} is disabled, skipping")
                continue
            
            try:
                # Adjust path to be relative to mcp-servers directory
                env = os.environ.copy()
                env['PYTHONPATH'] = f"{base_path}:{base_path}/core:{base_path}/safety-layer/src"
                
                process = subprocess.Popen(
                    [config.command] + config.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    cwd=str(base_path),
                    env=env
                )
                
                self.servers[name] = process
                logger.info(f"Started server: {name} (PID: {process.pid})")
                
                # Send initialize request
                init_request = MCPRequest(
                    id=1,
                    method="initialize",
                    params={"clientInfo": {"name": "agentic-cli", "version": "1.0.0"}}
                )
                
                response = await self._send_request_to_server(name, init_request)
                if response and not response.error:
                    logger.info(f"Server {name} initialized successfully")
                else:
                    logger.warning(f"Server {name} initialization may have failed")
                
            except Exception as e:
                logger.error(f"Failed to start server {name}: {e}")
    
    async def stop_servers(self) -> None:
        """Stop all running servers."""
        for name, process in self.servers.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Stopped server: {name}")
            except Exception as e:
                logger.warning(f"Error stopping server {name}: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        self.servers.clear()
    
    async def call_tool(self, server_name: str, tool_name: str, 
                       arguments: Dict[str, Any], 
                       check_safety: bool = True) -> Dict[str, Any]:
        """
        Call a tool on a specific server with optional safety checks.
        """
        # Safety check
        if check_safety and self.execution_context:
            context_dict = self.execution_context.to_dict()
            safety_result = self.safety_middleware.wrap_request(
                context_dict, server_name, tool_name, arguments
            )
            
            if not safety_result.allowed:
                return {
                    "success": False,
                    "error": "Safety check failed",
                    "safety_result": {
                        "allowed": False,
                        "action": safety_result.action.value,
                        "messages": safety_result.messages,
                        "risk_score": safety_result.risk_score
                    }
                }
            
            if safety_result.action.value == "warn":
                logger.warning(f"Safety warning for {server_name}/{tool_name}: {safety_result.messages}")
        
        # Make the actual request
        request = MCPRequest(
            id=self._generate_request_id(),
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        response = await self._send_request_to_server(server_name, request)
        
        if response.error:
            return {
                "success": False,
                "error": response.error.message,
                "error_code": response.error.code
            }
        
        return response.result or {"success": True}
    
    async def _send_request_to_server(self, server_name: str, request: MCPRequest) -> Optional[MCPResponse]:
        """Send a request to a specific server."""
        process = self.servers.get(server_name)
        if not process:
            logger.error(f"Server {server_name} not running")
            return None
        
        try:
            # Send request
            request_json = json.dumps(request.to_dict()) + '\n'
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if not response_line:
                logger.error(f"No response from server {server_name}")
                return None
            
            response_data = json.loads(response_line.strip())
            return MCPResponse(
                jsonrpc=response_data.get("jsonrpc", "2.0"),
                id=response_data.get("id"),
                result=response_data.get("result"),
                error=response_data.get("error")
            )
            
        except Exception as e:
            logger.exception(f"Error communicating with server {server_name}")
            return None
    
    def _generate_request_id(self) -> int:
        """Generate unique request ID."""
        import time
        return int(time.time() * 1000)
    
    async def discover_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Discover available tools on a server."""
        request = MCPRequest(
            id=self._generate_request_id(),
            method="tools/list"
        )
        
        response = await self._send_request_to_server(server_name, request)
        
        if response and response.result:
            return response.result.get("tools", [])
        
        return []
    
    def set_execution_context(self, context: ExecutionContext) -> None:
        """Set the current execution context."""
        self.execution_context = context
        logger.info(f"Set execution context: {context.session_id}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all servers."""
        health = {}
        
        for name in self.server_configs:
            if name in self.servers:
                process = self.servers[name]
                health[name] = process.poll() is None
            else:
                health[name] = False
        
        return health


class AgenticWorkflow:
    """High-level workflow orchestrator using MCP servers."""
    
    def __init__(self, client: MCPClient):
        self.client = client
    
    async def analyze_and_refactor(self, file_path: str) -> Dict[str, Any]:
        """Analyze code and suggest refactorings."""
        results = {}
        
        # Get structure
        structure = await self.client.call_tool(
            "code-intelligence",
            "code/get_structure",
            {"file": file_path}
        )
        results["structure"] = structure
        
        # Detect smells
        smells = await self.client.call_tool(
            "code-intelligence",
            "code/detect_code_smells",
            {"file": file_path}
        )
        results["smells"] = smells
        
        # Calculate complexity
        complexity = await self.client.call_tool(
            "code-intelligence",
            "code/calculate_complexity",
            {"file": file_path}
        )
        results["complexity"] = complexity
        
        # Generate recommendations
        recommendations = []
        
        if smells.get("total_smells", 0) > 0:
            recommendations.append(f"Address {smells['total_smells']} code smells")
        
        high_complexity = [c for c in complexity.get("complexities", []) if c.get("complexity", 0) > 10]
        if high_complexity:
            recommendations.append(f"Refactor {len(high_complexity)} high-complexity functions")
        
        results["recommendations"] = recommendations
        
        return results
    
    async def safe_commit(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Safely commit changes with pre-commit checks."""
        results = {"steps": []}
        
        # Security scan
        scan = await self.client.call_tool(
            "quality-assurance",
            "qa/security_scan",
            {"path": ".", "severity_threshold": "medium"}
        )
        results["steps"].append({"name": "security_scan", "result": scan})
        
        if scan.get("should_block"):
            return {
                "success": False,
                "error": "Security scan failed",
                "details": results
            }
        
        # Run tests
        tests = await self.client.call_tool(
            "execution-engine",
            "execution/test",
            {"framework": "auto"}
        )
        results["steps"].append({"name": "tests", "result": tests})
        
        if not tests.get("success"):
            return {
                "success": False,
                "error": "Tests failed",
                "details": results
            }
        
        # Lint
        lint = await self.client.call_tool(
            "quality-assurance",
            "qa/lint",
            {"path": ".", "linter": "auto"}
        )
        results["steps"].append({"name": "lint", "result": lint})
        
        # Commit
        commit = await self.client.call_tool(
            "version-control",
            "git/commit",
            {"message": message, "files": files or [], "auto_stage": True}
        )
        results["steps"].append({"name": "commit", "result": commit})
        
        results["success"] = commit.get("success", False)
        
        return results


async def main():
    """Demo the MCP client."""
    client = MCPClient()
    
    try:
        # Start servers
        await client.start_servers()
        
        # Set context
        context = ExecutionContext(
            session_id="demo-session",
            working_directory=os.getcwd(),
            user_id="demo-user"
        )
        client.set_execution_context(context)
        
        # Health check
        health = await client.health_check()
        print("Server Health:")
        for name, status in health.items():
            print(f"  {name}: {'✓' if status else '✗'}")
        
        # Discover tools
        if health.get("code-intelligence"):
            tools = await client.discover_tools("code-intelligence")
            print(f"\nCode Intelligence Tools ({len(tools)}):")
            for tool in tools[:5]:
                print(f"  - {tool['name']}")
        
    finally:
        # Stop servers
        await client.stop_servers()


if __name__ == "__main__":
    asyncio.run(main())
