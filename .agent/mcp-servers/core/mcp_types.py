"""
Core MCP (Model Context Protocol) type definitions.
Base types used across all MCP servers.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class MCPErrorCode(Enum):
    """Standard MCP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Server-specific errors
    EXECUTION_TIMEOUT = -32000
    EXECUTION_FAILED = -32001
    RESOURCE_NOT_FOUND = -32002
    PERMISSION_DENIED = -32003
    SAFETY_VIOLATION = -32004
    VALIDATION_ERROR = -32005


@dataclass
class MCPError:
    """MCP error response."""
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.data:
            result["data"] = self.data
        return result


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPRequest:
    """MCP request message."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.id is not None:
            result["id"] = self.id
        if self.params:
            result["params"] = self.params
        return result


@dataclass
class MCPResponse:
    """MCP response message."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[MCPError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            result["id"] = self.id
        if self.error is not None:
            if hasattr(self.error, 'to_dict'):
                result["error"] = self.error.to_dict()
            else:
                result["error"] = {"code": -32603, "message": str(self.error)}
        else:
            result["result"] = self.result or {}
        return result
    
    @classmethod
    def success(cls, id: Optional[Union[str, int]], result: Dict[str, Any]) -> "MCPResponse":
        return cls(id=id, result=result)
    
    @classmethod
    def with_error(cls, id: Optional[Union[str, int]], error: MCPError) -> "MCPResponse":
        return cls(id=id, error=error)


@dataclass
class SafetyPolicy:
    """Safety policy definition."""
    name: str
    description: str
    condition: str  # Expression to evaluate
    action: str  # "allow", "deny", "require_approval"
    severity: str = "medium"  # "low", "medium", "high", "critical"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context passed with MCP requests."""
    session_id: str
    working_directory: str
    git_commit: Optional[str] = None
    user_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "working_directory": self.working_directory,
            "git_commit": self.git_commit,
            "user_id": self.user_id,
            "permissions": self.permissions,
            "environment": self.environment
        }
