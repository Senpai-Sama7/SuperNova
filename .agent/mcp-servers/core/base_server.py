"""
Base MCP server implementation.
All MCP servers inherit from this base class.
"""

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass

from mcp_types import MCPRequest, MCPResponse, MCPError, MCPTool, MCPErrorCode


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ToolHandler:
    """Handler for a specific tool."""
    tool: MCPTool
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]


class BaseMCPServer(ABC):
    """Base class for all MCP servers."""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools: Dict[str, ToolHandler] = {}
        self._setup_tools()
    
    @abstractmethod
    def _setup_tools(self) -> None:
        """Register all tools this server provides."""
        pass
    
    def register_tool(self, tool: MCPTool, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Register a tool and its handler."""
        self.tools[tool.name] = ToolHandler(tool=tool, handler=handler)
        logger.info(f"Registered tool: {tool.name}")
    
    def handle_request(self, request: MCPRequest) -> MCPResponse | None:
        """Handle an incoming MCP request.
        
        Returns None for notifications that don't require a response.
        """
        try:
            # Handle notifications (no response needed)
            if request.method == "notifications/initialized":
                logger.debug("Received initialized notification")
                return None
            elif request.method == "notifications/cancelled":
                logger.debug("Received cancelled notification")
                return None
            
            # Handle requests that require responses
            if request.method == "tools/list":
                return self._handle_tools_list(request)
            elif request.method == "tools/call":
                return self._handle_tool_call(request)
            elif request.method == "initialize":
                return self._handle_initialize(request)
            else:
                return MCPResponse.with_error(
                    request.id,
                    MCPError(
                        code=MCPErrorCode.METHOD_NOT_FOUND.value,
                        message=f"Method not found: {request.method}"
                    )
                )
        except Exception as e:
            logger.exception("Error handling request")
            return MCPResponse.with_error(
                request.id,
                MCPError(
                    code=MCPErrorCode.INTERNAL_ERROR.value,
                    message=str(e),
                    data={"traceback": str(e)}
                )
            )
    
    def _handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list request."""
        tools = [th.tool.to_dict() for th in self.tools.values()]
        return MCPResponse.success(request.id, {"tools": tools})
    
    def _handle_tool_call(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request."""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return MCPResponse.with_error(
                request.id,
                MCPError(
                    code=MCPErrorCode.INVALID_PARAMS.value,
                    message="Missing 'name' parameter"
                )
            )
        
        handler = self.tools.get(tool_name)
        if not handler:
            return MCPResponse.with_error(
                request.id,
                MCPError(
                    code=MCPErrorCode.METHOD_NOT_FOUND.value,
                    message=f"Tool not found: {tool_name}"
                )
            )
        
        # Validate arguments against schema
        validation_error = self._validate_arguments(arguments, handler.tool.input_schema)
        if validation_error:
            return MCPResponse.with_error(
                request.id,
                MCPError(
                    code=MCPErrorCode.INVALID_PARAMS.value,
                    message=f"Validation error: {validation_error}"
                )
            )
        
        # Execute handler
        try:
            result = handler.handler(arguments)
            return MCPResponse.success(request.id, result)
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            return MCPResponse.with_error(
                request.id,
                MCPError(
                    code=MCPErrorCode.EXECUTION_FAILED.value,
                    message=f"Tool execution failed: {str(e)}",
                    data={"tool": tool_name}
                )
            )
    
    def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialize request."""
        return MCPResponse.success(request.id, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.name,
                "version": self.version
            },
            "capabilities": {
                "tools": {}
            }
        })
    
    def _validate_arguments(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
        """Validate arguments against JSON schema."""
        required = schema.get("required", [])
        for field in required:
            if field not in arguments:
                return f"Missing required field: {field}"
        return None
    
    async def run_stdio(self) -> None:
        """Run server using stdio transport."""
        logger.info(f"Starting {self.name} v{self.version}")
        
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break
                
                # Parse request
                data = json.loads(line.decode().strip())
                request = MCPRequest.from_dict(data)
                
                # Handle request
                response = self.handle_request(request)
                
                # Only send response if there is one (notifications return None)
                if response is not None:
                    response_json = json.dumps(response.to_dict())
                    print(response_json, flush=True)
                
            except json.JSONDecodeError as e:
                error_response = MCPResponse.with_error(
                    None,
                    MCPError(
                        code=MCPErrorCode.PARSE_ERROR.value,
                        message=f"JSON parse error: {str(e)}"
                    )
                )
                print(json.dumps(error_response.to_dict()), flush=True)
            except Exception as e:
                logger.exception("Error in main loop")
                error_response = MCPResponse.with_error(
                    None,
                    MCPError(
                        code=MCPErrorCode.INTERNAL_ERROR.value,
                        message=str(e)
                    )
                )
                print(json.dumps(error_response.to_dict()), flush=True)
