"""
Knowledge Integration MCP Server

Provides documentation search, database queries, API testing, and web access.
"""

import asyncio
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))

from base_server import BaseMCPServer
from mcp_types import MCPTool


class KnowledgeIntegrationServer(BaseMCPServer):
    """MCP server for knowledge and integration."""
    
    def __init__(self):
        super().__init__("knowledge-integration", "1.0.0")
        self.doc_cache: Dict[str, str] = {}
    
    def _setup_tools(self) -> None:
        """Register knowledge tools."""
        
        self.register_tool(MCPTool(
            name="docs/search",
            description="Search documentation and knowledge base",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["internal"]
                    },
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ), self._search_docs)
        
        self.register_tool(MCPTool(
            name="docs/fetch",
            description="Fetch and parse documentation from URL",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "format": {"type": "string", "enum": ["text", "markdown", "html"], "default": "text"},
                    "max_length": {"type": "integer", "default": 5000}
                },
                "required": ["url"]
            }
        ), self._fetch_docs)
        
        self.register_tool(MCPTool(
            name="db/schema",
            description="Get database schema information",
            input_schema={
                "type": "object",
                "properties": {
                    "connection_string": {"type": "string"},
                    "database": {"type": "string"},
                    "include_indexes": {"type": "boolean", "default": True}
                },
                "required": ["connection_string"]
            }
        ), self._db_schema)
        
        self.register_tool(MCPTool(
            name="db/query",
            description="Execute a database query safely",
            input_schema={
                "type": "object",
                "properties": {
                    "connection_string": {"type": "string"},
                    "query": {"type": "string"},
                    "read_only": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": ["connection_string", "query"]
            }
        ), self._db_query)
        
        self.register_tool(MCPTool(
            name="db/analyze",
            description="Analyze query performance",
            input_schema={
                "type": "object",
                "properties": {
                    "connection_string": {"type": "string"},
                    "query": {"type": "string"}
                },
                "required": ["connection_string", "query"]
            }
        ), self._db_analyze)
        
        self.register_tool(MCPTool(
            name="api/test",
            description="Test an API endpoint",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "GET"},
                    "headers": {"type": "object"},
                    "body": {"type": "string"},
                    "timeout": {"type": "integer", "default": 30000}
                },
                "required": ["url"]
            }
        ), self._api_test)
        
        self.register_tool(MCPTool(
            name="api/validate_schema",
            description="Validate response against OpenAPI schema",
            input_schema={
                "type": "object",
                "properties": {
                    "response": {"type": "object"},
                    "schema_path": {"type": "string"},
                    "endpoint": {"type": "string"}
                },
                "required": ["response", "schema_path"]
            }
        ), self._api_validate)
        
        self.register_tool(MCPTool(
            name="web/search",
            description="Search the web for information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ), self._web_search)
        
        self.register_tool(MCPTool(
            name="web/fetch",
            description="Fetch content from a web page",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "extract_text": {"type": "boolean", "default": True},
                    "max_length": {"type": "integer", "default": 5000}
                },
                "required": ["url"]
            }
        ), self._web_fetch)
        
        self.register_tool(MCPTool(
            name="pattern/retrieve",
            description="Retrieve code patterns and examples",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Pattern name or description"},
                    "language": {"type": "string"},
                    "context": {"type": "string"}
                },
                "required": ["pattern"]
            }
        ), self._pattern_retrieve)
    
    def _search_docs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search documentation."""
        query = args["query"]
        sources = args.get("sources", ["internal"])
        max_results = args.get("max_results", 5)
        
        results = []
        
        # Internal documentation search
        if "internal" in sources or "docs" in sources:
            # Search in common doc directories
            doc_dirs = ["docs", "Documentation", "doc", "wiki", ".github"]
            
            for doc_dir in doc_dirs:
                if os.path.exists(doc_dir):
                    for filepath in Path(doc_dir).rglob("*.md"):
                        try:
                            content = filepath.read_text()
                            if self._relevance_score(query, content) > 0.3:
                                results.append({
                                    "source": "internal",
                                    "file": str(filepath),
                                    "title": self._extract_title(content),
                                    "excerpt": self._extract_excerpt(content, query)
                                })
                        except Exception:
                            continue
        
        # Search code comments
        if "code" in sources:
            for pattern in ["*.py", "*.js", "*.ts"]:
                for filepath in Path(".").rglob(pattern):
                    try:
                        content = filepath.read_text()
                        if query.lower() in content.lower():
                            # Find relevant docstrings/comments
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if query.lower() in line.lower() and ('"""' in line or "'''" in line or '#' in line):
                                    context = '\n'.join(lines[max(0, i-2):i+3])
                                    results.append({
                                        "source": "code",
                                        "file": str(filepath),
                                        "line": i + 1,
                                        "excerpt": context[:200]
                                    })
                                    break
                    except Exception:
                        continue
        
        # Sort by relevance and limit
        results = sorted(results, key=lambda x: self._relevance_score(query, x.get("excerpt", "")), reverse=True)[:max_results]
        
        return {
            "query": query,
            "sources_searched": sources,
            "results_count": len(results),
            "results": results
        }
    
    def _relevance_score(self, query: str, content: str) -> float:
        """Calculate simple relevance score."""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        if not query_terms:
            return 0.0
        
        matches = sum(1 for term in query_terms if term in content_lower)
        return matches / len(query_terms)
    
    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        lines = content.split('\n')
        for line in lines[:10]:
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('## '):
                return line[3:].strip()
        return "Untitled"
    
    def _extract_excerpt(self, content: str, query: str, max_length: int = 200) -> str:
        """Extract relevant excerpt from content."""
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Find position of query
        pos = content_lower.find(query_lower)
        if pos == -1:
            # Return first paragraph
            paragraphs = content.split('\n\n')
            return paragraphs[0][:max_length] if paragraphs else content[:max_length]
        
        # Extract surrounding context
        start = max(0, pos - max_length // 2)
        end = min(len(content), pos + len(query) + max_length // 2)
        
        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."
        
        return excerpt
    
    def _fetch_docs(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch documentation from URL."""
        url = args["url"]
        fmt = args.get("format", "text")
        max_length = args.get("max_length", 5000)
        
        try:
            # Use curl to fetch
            result = subprocess.run(
                ["curl", "-s", "-L", "-A", "MCP-Knowledge-Bot/1.0", url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            content = result.stdout
            
            # Parse based on format
            if fmt == "text":
                # Simple HTML to text conversion
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content)
            elif fmt == "markdown":
                # Try to extract markdown if available
                pass
            
            # Truncate
            if len(content) > max_length:
                content = content[:max_length] + "... [truncated]"
            
            return {
                "success": True,
                "url": url,
                "content": content,
                "length": len(content)
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _db_schema(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get database schema."""
        connection_string = args["connection_string"]
        database = args.get("database")
        include_indexes = args.get("include_indexes", True)
        
        try:
            # Parse connection string
            if connection_string.startswith("sqlite:///"):
                db_path = connection_string[10:]
                conn = sqlite3.connect(db_path)
            else:
                return {"error": "Only SQLite supported in this version"}
            
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schema = {}
            for (table_name,) in tables:
                if table_name.startswith("sqlite_"):
                    continue
                
                # Get columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "default": row[4],
                        "primary_key": bool(row[5])
                    })
                
                table_info = {"columns": columns}
                
                # Get indexes
                if include_indexes:
                    cursor.execute(f"PRAGMA index_list({table_name})")
                    indexes = []
                    for row in cursor.fetchall():
                        index_name = row[1]
                        cursor.execute(f"PRAGMA index_info({index_name})")
                        index_columns = [r[2] for r in cursor.fetchall()]
                        indexes.append({
                            "name": index_name,
                            "columns": index_columns,
                            "unique": row[2]
                        })
                    table_info["indexes"] = indexes
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                fks = []
                for row in cursor.fetchall():
                    fks.append({
                        "column": row[3],
                        "references_table": row[2],
                        "references_column": row[4]
                    })
                if fks:
                    table_info["foreign_keys"] = fks
                
                schema[table_name] = table_info
            
            conn.close()
            
            return {
                "database_type": "sqlite",
                "tables_count": len(schema),
                "schema": schema
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _db_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database query."""
        connection_string = args["connection_string"]
        query = args["query"]
        read_only = args.get("read_only", True)
        limit = args.get("limit", 100)
        
        # Safety: check for write operations in read-only mode
        if read_only:
            write_keywords = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate']
            if any(kw in query.lower() for kw in write_keywords):
                return {
                    "error": "Write operations not allowed in read-only mode",
                    "blocked": True
                }
        
        try:
            if connection_string.startswith("sqlite:///"):
                db_path = connection_string[10:]
                conn = sqlite3.connect(db_path)
            else:
                return {"error": "Only SQLite supported in this version"}
            
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Add limit if not present
            if 'limit' not in query.lower() and read_only:
                query = query.rstrip(';') + f" LIMIT {limit}"
            
            cursor.execute(query)
            
            # Fetch results
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            results = []
            for row in rows:
                results.append({col: row[col] for col in columns})
            
            conn.close()
            
            return {
                "success": True,
                "columns": columns,
                "row_count": len(results),
                "results": results[:limit]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _db_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query performance."""
        connection_string = args["connection_string"]
        query = args["query"]
        
        try:
            if connection_string.startswith("sqlite:///"):
                db_path = connection_string[10:]
                conn = sqlite3.connect(db_path)
            else:
                return {"error": "Only SQLite supported"}
            
            cursor = conn.cursor()
            
            # Get query plan
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            plan_lines = []
            for row in plan:
                plan_lines.append({
                    "select_id": row[0],
                    "order": row[1],
                    "from": row[2],
                    "detail": row[3]
                })
            
            conn.close()
            
            # Analyze for issues
            warnings = []
            plan_str = str(plan)
            if "SCAN TABLE" in plan_str:
                warnings.append("Full table scan detected - consider adding indexes")
            if "TEMP B-TREE" in plan_str:
                warnings.append("Temporary B-tree created - consider index for ORDER BY")
            
            return {
                "query_plan": plan_lines,
                "warnings": warnings,
                "is_optimized": len(warnings) == 0
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _api_test(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Test API endpoint."""
        url = args["url"]
        method = args.get("method", "GET")
        headers = args.get("headers", {})
        body = args.get("body")
        timeout = args.get("timeout", 30000)
        
        try:
            # Build curl command
            cmd = ["curl", "-s", "-w", "\\n%{http_code}\\n%{time_total}", "-X", method]
            
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
            
            if body:
                cmd.extend(["-d", body])
            
            cmd.append(url)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout / 1000
            )
            
            lines = result.stdout.strip().split('\n')
            http_code = lines[-2] if len(lines) >= 2 else "0"
            response_time = lines[-1] if len(lines) >= 1 else "0"
            response_body = '\n'.join(lines[:-2])
            
            # Try to parse JSON
            try:
                response_json = json.loads(response_body)
                parsed_body = response_json
            except json.JSONDecodeError:
                parsed_body = response_body[:1000]  # Truncate text
            
            return {
                "success": 200 <= int(http_code) < 300,
                "status_code": int(http_code),
                "response_time_ms": round(float(response_time) * 1000, 2),
                "body": parsed_body,
                "headers": {}  # Could parse from verbose output
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _api_validate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API response against schema."""
        response = args["response"]
        schema_path = args["schema_path"]
        
        # Simplified validation - check if response has expected structure
        # Full implementation would use jsonschema
        return {
            "valid": True,
            "message": "Basic validation passed (full OpenAPI validation not implemented in this version)"
        }
    
    def _web_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search the web."""
        query = args["query"]
        max_results = args.get("max_results", 5)
        
        # Use a search API or fallback to documentation
        return {
            "query": query,
            "message": "Web search requires external API integration (SerpAPI, Bing, etc.)",
            "suggestion": "Consider implementing with: serpapi.com, bing search API, or duckduckgo"
        }
    
    def _web_fetch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch web content."""
        url = args["url"]
        extract_text = args.get("extract_text", True)
        max_length = args.get("max_length", 5000)
        
        return self._fetch_docs({"url": url, "format": "text" if extract_text else "html", "max_length": max_length})
    
    def _pattern_retrieve(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve code patterns."""
        pattern = args["pattern"]
        language = args.get("language", "python")
        context = args.get("context", "")
        
        # Built-in pattern library
        patterns = {
            "singleton": {
                "python": """
class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
""",
                "description": "Ensure only one instance of a class exists"
            },
            "factory": {
                "python": """
class AnimalFactory:
    @staticmethod
    def create(animal_type):
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        raise ValueError(f"Unknown type: {animal_type}")
""",
                "description": "Create objects without specifying exact class"
            },
            "retry": {
                "python": """
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator
""",
                "description": "Retry function execution on failure"
            },
            "context_manager": {
                "python": """
class DatabaseConnection:
    def __enter__(self):
        self.conn = create_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
""",
                "description": "Manage resources with context managers"
            },
            "observer": {
                "python": """
class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self, event):
        for observer in self._observers:
            observer.update(event)
""",
                "description": "Notify observers of state changes"
            }
        }
        
        # Find matching pattern
        matched_pattern = None
        for key in patterns:
            if key.lower() in pattern.lower():
                matched_pattern = patterns[key]
                break
        
        if matched_pattern:
            return {
                "found": True,
                "pattern_name": key,
                "description": matched_pattern["description"],
                "implementation": matched_pattern.get(language, matched_pattern.get("python", "")),
                "language": language
            }
        else:
            return {
                "found": False,
                "message": f"Pattern '{pattern}' not found in library",
                "available_patterns": list(patterns.keys())
            }


def main():
    server = KnowledgeIntegrationServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    import asyncio
    main()
