"""
Code Intelligence MCP Server

Provides semantic code understanding, analysis, and transformation capabilities.
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))

from base_server import BaseMCPServer
from mcp_types import MCPTool


class CodeIntelligenceServer(BaseMCPServer):
    """MCP server for code intelligence."""
    
    def __init__(self):
        super().__init__("code-intelligence", "1.0.0")
        self._file_cache: Dict[str, str] = {}
        self._ast_cache: Dict[str, ast.AST] = {}
    
    def _setup_tools(self) -> None:
        """Register all code intelligence tools."""
        
        # Analysis tools
        self.register_tool(MCPTool(
            name="code/analyze_function",
            description="Analyze a function's complexity, dependencies, and risks",
            input_schema={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "Path to the file"},
                    "function": {"type": "string", "description": "Function name"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["basic", "full", "security"],
                        "default": "full"
                    }
                },
                "required": ["file", "function"]
            }
        ), self._analyze_function)
        
        self.register_tool(MCPTool(
            name="code/find_references",
            description="Find all references to a symbol",
            input_schema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Symbol name to search for"},
                    "path": {"type": "string", "description": "Directory or file to search"},
                    "language": {"type": "string", "default": "python"}
                },
                "required": ["symbol", "path"]
            }
        ), self._find_references)
        
        self.register_tool(MCPTool(
            name="code/detect_code_smells",
            description="Detect code smells and anti-patterns",
            input_schema={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "File to analyze"},
                    "severity": {
                        "type": "string",
                        "enum": ["all", "minor", "major", "critical"],
                        "default": "all"
                    }
                },
                "required": ["file"]
            }
        ), self._detect_code_smells)
        
        self.register_tool(MCPTool(
            name="code/calculate_complexity",
            description="Calculate cyclomatic complexity for code",
            input_schema={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "File to analyze"},
                    "function": {"type": "string", "description": "Specific function (optional)"}
                },
                "required": ["file"]
            }
        ), self._calculate_complexity)
        
        self.register_tool(MCPTool(
            name="code/get_structure",
            description="Get the structure of a source file",
            input_schema={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "File to analyze"},
                    "include_body": {"type": "boolean", "default": False}
                },
                "required": ["file"]
            }
        ), self._get_structure)
        
        self.register_tool(MCPTool(
            name="code/find_duplicates",
            description="Find duplicate or similar code blocks",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to search"},
                    "min_lines": {"type": "integer", "default": 5},
                    "threshold": {"type": "number", "default": 0.8}
                },
                "required": ["path"]
            }
        ), self._find_duplicates)
        
        self.register_tool(MCPTool(
            name="code/dependency_graph",
            description="Build import/module dependency graph",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Root directory"},
                    "format": {"type": "string", "enum": ["json", "dot"], "default": "json"}
                },
                "required": ["path"]
            }
        ), self._dependency_graph)
    
    def _get_file_content(self, filepath: str) -> str:
        """Get file content with caching."""
        abs_path = str(Path(filepath).resolve())
        if abs_path not in self._file_cache:
            with open(abs_path, 'r') as f:
                self._file_cache[abs_path] = f.read()
        return self._file_cache[abs_path]
    
    def _get_ast(self, filepath: str) -> ast.AST:
        """Get AST with caching."""
        abs_path = str(Path(filepath).resolve())
        if abs_path not in self._ast_cache:
            content = self._get_file_content(abs_path)
            self._ast_cache[abs_path] = ast.parse(content)
        return self._ast_cache[abs_path]
    
    def _analyze_function(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a function in detail."""
        filepath = args["file"]
        function_name = args["function"]
        analysis_type = args.get("analysis_type", "full")
        
        try:
            tree = self._get_ast(filepath)
            content = self._get_file_content(filepath)
        except Exception as e:
            return {"error": str(e)}
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    return self._analyze_function_node(node, content, analysis_type)
        
        return {"error": f"Function '{function_name}' not found"}
    
    def _analyze_function_node(self, node: ast.AST, content: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze a function AST node."""
        lines = content.split('\n')
        func_lines = node.end_lineno - node.lineno if node.end_lineno else 10
        
        # Basic metrics
        result = {
            "name": node.name,
            "lines": func_lines,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "parameters": len(node.args.args) + len(node.args.kwonlyargs),
            "has_varargs": node.args.vararg is not None,
            "has_kwargs": node.args.kwarg is not None,
        }
        
        # Complexity analysis
        complexity = self._calculate_cyclomatic_complexity(node)
        result["complexity"] = complexity
        
        if complexity > 10:
            result["complexity_warning"] = "High cyclomatic complexity (>10)"
        
        # Full analysis
        if analysis_type in ("full", "security"):
            # Find dependencies
            dependencies = self._find_dependencies(node)
            result["dependencies"] = dependencies
            
            # Find side effects
            side_effects = self._find_side_effects(node)
            result["side_effects"] = side_effects
            
            # Return statements
            returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
            result["return_points"] = len(returns)
            
            # Risks
            risks = []
            if complexity > 10:
                risks.append("high_complexity")
            if len(returns) > 3:
                risks.append("multiple_return_paths")
            if side_effects:
                risks.append("has_side_effects")
            if "database" in str(dependencies).lower():
                risks.append("database_dependency")
            
            result["risks"] = risks
            
            # Suggestions
            suggestions = []
            if complexity > 10:
                suggestions.append("Consider extracting helper functions to reduce complexity")
            if len(node.args.args) > 4:
                suggestions.append("Consider using a parameter object for multiple arguments")
            if not returns:
                suggestions.append("Function has no return statement - verify this is intentional")
            
            result["suggestions"] = suggestions
        
        return result
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _find_dependencies(self, node: ast.AST) -> List[str]:
        """Find external dependencies of a function."""
        dependencies = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                dependencies.add(child.attr)
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.add(child.func.id)
        return sorted(list(dependencies))
    
    def _find_side_effects(self, node: ast.AST) -> List[str]:
        """Find potential side effects."""
        side_effects = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    method_name = child.func.attr
                    if method_name in ('write', 'save', 'delete', 'update', 'insert', 'commit'):
                        side_effects.append(method_name)
        return side_effects
    
    def _find_references(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find all references to a symbol."""
        symbol = args["symbol"]
        path = args["path"]
        language = args.get("language", "python")
        
        references = []
        
        if os.path.isfile(path):
            files = [path]
        else:
            files = list(Path(path).rglob("*.py"))
        
        pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')
        
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern.search(line):
                            references.append({
                                "file": str(filepath),
                                "line": line_num,
                                "context": line.strip()[:80]
                            })
            except Exception:
                continue
        
        return {
            "symbol": symbol,
            "total_references": len(references),
            "references": references[:50]  # Limit results
        }
    
    def _detect_code_smells(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Detect code smells in a file."""
        filepath = args["file"]
        severity = args.get("severity", "all")
        
        try:
            tree = self._get_ast(filepath)
            content = self._get_file_content(filepath)
        except Exception as e:
            return {"error": str(e)}
        
        smells = []
        
        # Long function detection
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if lines > 50:
                    smells.append({
                        "type": "long_function",
                        "severity": "major",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' is {lines} lines (max recommended: 50)",
                        "suggestion": "Consider extracting helper functions"
                    })
                
                # Too many parameters
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if param_count > 5:
                    smells.append({
                        "type": "too_many_parameters",
                        "severity": "minor",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has {param_count} parameters",
                        "suggestion": "Consider using a parameter object"
                    })
                
                # High complexity
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    smells.append({
                        "type": "high_complexity",
                        "severity": "major",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has cyclomatic complexity of {complexity}",
                        "suggestion": "Simplify conditionals or extract methods"
                    })
        
        # Filter by severity
        severity_order = {"critical": 0, "major": 1, "minor": 2, "all": 3}
        if severity != "all":
            threshold = severity_order.get(severity, 3)
            smells = [s for s in smells if severity_order.get(s["severity"], 3) <= threshold]
        
        return {
            "file": filepath,
            "total_smells": len(smells),
            "smells": smells
        }
    
    def _calculate_complexity(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        filepath = args["file"]
        function_name = args.get("function")
        
        try:
            tree = self._get_ast(filepath)
        except Exception as e:
            return {"error": str(e)}
        
        complexities = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if function_name and node.name != function_name:
                    continue
                
                complexity = self._calculate_cyclomatic_complexity(node)
                complexities.append({
                    "function": node.name,
                    "line": node.lineno,
                    "complexity": complexity,
                    "risk": "high" if complexity > 10 else "medium" if complexity > 5 else "low"
                })
        
        return {
            "file": filepath,
            "functions_analyzed": len(complexities),
            "complexities": complexities
        }
    
    def _get_structure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get file structure."""
        filepath = args["file"]
        include_body = args.get("include_body", False)
        
        try:
            tree = self._get_ast(filepath)
        except Exception as e:
            return {"error": str(e)}
        
        structure = {
            "file": filepath,
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": []
        }
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    structure["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                structure["imports"].append(f"{module}: {', '.join(names)}")
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [self._get_name(base) for base in node.bases],
                    "methods": []
                }
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        class_info["methods"].append({
                            "name": item.name,
                            "line": item.lineno,
                            "is_async": isinstance(item, ast.AsyncFunctionDef)
                        })
                structure["classes"].append(class_info)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                structure["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })
        
        return structure
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _find_duplicates(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find duplicate code blocks."""
        path = args["path"]
        min_lines = args.get("min_lines", 5)
        
        blocks = []
        files = list(Path(path).rglob("*.py"))
        
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    # Extract function bodies for comparison
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            func_lines = lines[node.lineno:node.end_lineno if node.end_lineno else node.lineno + 10]
                            normalized = '\n'.join(l.strip() for l in func_lines if l.strip())
                            blocks.append({
                                "file": str(filepath),
                                "function": node.name,
                                "line": node.lineno,
                                "content": normalized,
                                "line_count": len(func_lines)
                            })
            except Exception:
                continue
        
        # Find similar blocks
        duplicates = []
        for i, block1 in enumerate(blocks):
            for block2 in blocks[i+1:]:
                if block1["line_count"] >= min_lines and block2["line_count"] >= min_lines:
                    similarity = self._calculate_similarity(block1["content"], block2["content"])
                    if similarity > 0.8:
                        duplicates.append({
                            "similarity": round(similarity, 2),
                            "block1": {k: v for k, v in block1.items() if k != "content"},
                            "block2": {k: v for k, v in block2.items() if k != "content"}
                        })
        
        return {
            "total_files_scanned": len(files),
            "potential_duplicates": len(duplicates),
            "duplicates": duplicates[:20]
        }
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple similarity between two strings."""
        # Tokenize and compare
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _dependency_graph(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Build dependency graph."""
        path = args["path"]
        format_type = args.get("format", "json")
        
        imports = defaultdict(list)
        
        files = list(Path(path).rglob("*.py"))
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    tree = ast.parse(f.read())
                
                module_name = str(filepath.relative_to(path)).replace('/', '.').replace('.py', '')
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[module_name].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports[module_name].append(node.module)
            except Exception:
                continue
        
        if format_type == "dot":
            dot_lines = ["digraph dependencies {"]
            for module, deps in imports.items():
                for dep in deps:
                    dot_lines.append(f'  "{module}" -> "{dep}";')
            dot_lines.append("}")
            return {"graph": '\n'.join(dot_lines)}
        
        return {"dependencies": dict(imports)}


def main():
    server = CodeIntelligenceServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    import asyncio
    main()
