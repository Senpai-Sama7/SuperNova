"""
Quality Assurance MCP Server

Provides security scanning, performance analysis, and quality checks.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'core')))

from base_server import BaseMCPServer
from mcp_types import MCPTool


@dataclass
class SecurityFinding:
    severity: str
    category: str
    file: str
    line: int
    message: str
    code: Optional[str] = None


class QualityAssuranceServer(BaseMCPServer):
    """MCP server for quality assurance."""
    
    # Dangerous patterns for security scanning
    DANGEROUS_PATTERNS = [
        (r'eval\s*\(', "eval_usage", "critical", "Use of eval() can execute arbitrary code"),
        (r'exec\s*\(', "exec_usage", "critical", "Use of exec() can execute arbitrary code"),
        (r'pickle\.loads?\s*\(', "unsafe_deserialization", "high", "Pickle deserialization is unsafe with untrusted data"),
        (r'yaml\.load\s*\([^)]*\)(?!\s*#.*safe)', "yaml_unsafe_load", "high", "Use yaml.safe_load() instead"),
        (r'\binput\s*\(', "user_input", "medium", "Unvalidated user input"),
        (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "shell_injection", "high", "Shell=True with subprocess is dangerous"),
        (r'\.format\s*\([^)]*\)|f["\'].*\{.*\}.*["\']', "format_string", "low", "Potential format string issues"),
        (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded_password", "critical", "Potential hardcoded password"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "hardcoded_secret", "critical", "Potential hardcoded secret"),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "hardcoded_api_key", "critical", "Potential hardcoded API key"),
        (r'http://(?!localhost|127\.0\.0\.1)', "insecure_protocol", "medium", "Using HTTP instead of HTTPS"),
        (r'hashlib\.md5\s*\(', "weak_hash", "medium", "MD5 is cryptographically broken"),
        (r'hashlib\.sha1\s*\(', "weak_hash", "medium", "SHA1 is deprecated for security"),
        (r'random\.\w+\s*\(?!.*SystemRandom', "insecure_random", "low", "Use secrets module for security-sensitive randomness"),
        (r'debug\s*=\s*True|DEBUG\s*=\s*True', "debug_enabled", "medium", "Debug mode may be enabled in production"),
    ]
    
    def __init__(self):
        super().__init__("quality-assurance", "1.0.0")
    
    def _setup_tools(self) -> None:
        """Register QA tools."""
        
        self.register_tool(MCPTool(
            name="qa/security_scan",
            description="Scan code for security vulnerabilities",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to scan"},
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["secrets", "injection", "crypto", "config"]
                    },
                    "severity_threshold": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"}
                },
                "required": ["path"]
            }
        ), self._security_scan)
        
        self.register_tool(MCPTool(
            name="qa/lint",
            description="Run linters on code",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "linter": {"type": "string", "enum": ["auto", "pylint", "flake8", "ruff", "eslint", "prettier"], "default": "auto"},
                    "fix": {"type": "boolean", "default": False}
                },
                "required": ["path"]
            }
        ), self._run_linter)
        
        self.register_tool(MCPTool(
            name="qa/type_check",
            description="Run type checker",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "checker": {"type": "string", "enum": ["auto", "mypy", "pyright", "tsc"], "default": "auto"}
                },
                "required": ["path"]
            }
        ), self._type_check)
        
        self.register_tool(MCPTool(
            name="qa/coverage",
            description="Analyze test coverage",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "test_command": {"type": "string"},
                    "threshold": {"type": "number", "default": 80}
                },
                "required": ["path"]
            }
        ), self._coverage_analysis)
        
        self.register_tool(MCPTool(
            name="qa/dependency_audit",
            description="Audit dependencies for vulnerabilities",
            input_schema={
                "type": "object",
                "properties": {
                    "manifest": {"type": "string", "description": "Path to requirements.txt, package.json, etc."},
                    "lockfile": {"type": "string"}
                },
                "required": ["manifest"]
            }
        ), self._dependency_audit)
        
        self.register_tool(MCPTool(
            name="qa/complexity_report",
            description="Generate code complexity report",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "format": {"type": "string", "enum": ["summary", "detailed"], "default": "summary"}
                },
                "required": ["path"]
            }
        ), self._complexity_report)
    
    def _security_scan(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Scan for security issues."""
        path = args["path"]
        checks = args.get("checks", ["secrets", "injection", "crypto", "config"])
        threshold = args.get("severity_threshold", "medium")
        
        findings = []
        files_scanned = 0
        
        # Determine files to scan
        if os.path.isfile(path):
            files = [path]
        else:
            files = list(Path(path).rglob("*.py"))
            files.extend(Path(path).rglob("*.js"))
            files.extend(Path(path).rglob("*.ts"))
        
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                files_scanned += 1
                
                # Check each pattern
                for pattern, category, severity, message in self.DANGEROUS_PATTERNS:
                    # Skip based on checks filter
                    if category not in checks and "all" not in checks:
                        continue
                    
                    # Skip based on severity threshold
                    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                    if severity_order.get(severity, 3) > severity_order.get(threshold, 3):
                        continue
                    
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip comments
                            code_part = line.split('#')[0] if '#' in line else line
                            if re.search(pattern, code_part, re.IGNORECASE):
                                findings.append({
                                    "severity": severity,
                                    "category": category,
                                    "file": str(filepath),
                                    "line": line_num,
                                    "message": message,
                                    "code": line.strip()[:80]
                                })
                
                # AST-based checks for Python
                if str(filepath).endswith('.py'):
                    findings.extend(self._ast_security_check(filepath, content, checks))
                    
            except Exception as e:
                continue
        
        # Calculate risk score
        risk_weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
        risk_score = sum(risk_weights.get(f["severity"], 1) for f in findings)
        
        # Count by severity
        by_severity = {}
        for f in findings:
            by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
        
        return {
            "files_scanned": files_scanned,
            "findings_count": len(findings),
            "risk_score": risk_score,
            "by_severity": by_severity,
            "findings": sorted(findings, key=lambda x: risk_weights.get(x["severity"], 1), reverse=True)[:50],
            "should_block": risk_score > 50 or by_severity.get("critical", 0) > 0
        }
    
    def _ast_security_check(self, filepath: str, content: str, checks: List[str]) -> List[Dict]:
        """AST-based security checks."""
        findings = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings
        
        # Check for SQL injection
        if "injection" in checks or "all" in checks:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for .execute() with string concatenation
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'execute':
                        if node.args:
                            first_arg = node.args[0]
                            if isinstance(first_arg, ast.JoinedStr) or isinstance(first_arg, ast.BinOp):
                                findings.append({
                                    "severity": "critical",
                                    "category": "sql_injection",
                                    "file": filepath,
                                    "line": node.lineno,
                                    "message": "Potential SQL injection - use parameterized queries",
                                    "code": ast.get_source_segment(content, node)[:80] if hasattr(ast, 'get_source_segment') else "execute(...)"
                                })
        
        # Check for hardcoded secrets in assignments
        if "secrets" in checks or "all" in checks:
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id.lower()
                            if any(keyword in var_name for keyword in ['password', 'secret', 'token', 'key']):
                                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                    if len(node.value.value) > 3:
                                        findings.append({
                                            "severity": "high",
                                            "category": "hardcoded_secret",
                                            "file": filepath,
                                            "line": node.lineno,
                                            "message": f"Potential hardcoded secret in variable '{target.id}'",
                                            "code": f"{target.id} = '***'"
                                        })
        
        return findings
    
    def _run_linter(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run linters."""
        path = args["path"]
        linter = args.get("linter", "auto")
        fix = args.get("fix", False)
        
        # Auto-detect linter
        if linter == "auto":
            if list(Path(path).rglob("*.py")):
                # Check which linters are available
                if self._command_exists("ruff"):
                    linter = "ruff"
                elif self._command_exists("flake8"):
                    linter = "flake8"
                else:
                    linter = "pylint"
            elif list(Path(path).rglob("*.js")) or list(Path(path).rglob("*.ts")):
                linter = "eslint"
        
        # Build command
        commands = {
            "ruff": f"ruff check {'--fix' if fix else ''} {path}",
            "flake8": f"flake8 {path}",
            "pylint": f"pylint {path}",
            "eslint": f"eslint {'--fix' if fix else ''} {path}",
            "prettier": f"prettier {'--write' if fix else '--check'} {path}"
        }
        
        cmd = commands.get(linter)
        if not cmd:
            return {"error": f"Unknown linter: {linter}"}
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output (simplified)
            issues = []
            for line in result.stdout.split('\n') + result.stderr.split('\n'):
                if line.strip():
                    issues.append(line.strip())
            
            return {
                "linter": linter,
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "issues_count": len(issues),
                "issues": issues[:50],
                "fixed": fix and result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {"error": "Linter timed out"}
        except Exception as e:
            return {"error": str(e)}
    
    def _type_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run type checker."""
        path = args["path"]
        checker = args.get("checker", "auto")
        
        # Auto-detect
        if checker == "auto":
            if self._command_exists("mypy"):
                checker = "mypy"
            elif self._command_exists("pyright"):
                checker = "pyright"
        
        commands = {
            "mypy": f"mypy {path}",
            "pyright": f"pyright {path}",
            "tsc": f"tsc --noEmit {path}"
        }
        
        cmd = commands.get(checker)
        if not cmd:
            return {"error": f"Unknown type checker: {checker}"}
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            errors = []
            for line in result.stdout.split('\n') + result.stderr.split('\n'):
                if 'error' in line.lower() or line.strip().startswith(path):
                    errors.append(line.strip())
            
            return {
                "checker": checker,
                "success": result.returncode == 0,
                "errors_count": len(errors),
                "errors": errors[:30]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _coverage_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test coverage."""
        path = args["path"]
        test_command = args.get("test_command")
        threshold = args.get("threshold", 80)
        
        # Detect project type and run coverage
        if not test_command:
            if (Path(path) / "pytest.ini").exists() or list(Path(path).glob("test_*.py")):
                test_command = "pytest --cov --cov-report=term-missing"
            elif (Path(path) / "package.json").exists():
                test_command = "npm test -- --coverage"
        
        if not test_command:
            return {"error": "Could not auto-detect test command"}
        
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse coverage output (simplified)
            output = result.stdout + result.stderr
            
            # Extract coverage percentage
            coverage_match = re.search(r'(\d+)%', output)
            coverage = int(coverage_match.group(1)) if coverage_match else 0
            
            # Parse missing lines
            missing = []
            for line in output.split('\n'):
                if 'missing' in line.lower() or 'uncovered' in line.lower():
                    missing.append(line.strip())
            
            return {
                "coverage_percent": coverage,
                "threshold": threshold,
                "meets_threshold": coverage >= threshold,
                "missing_lines": missing[:20],
                "test_output": output[:2000] if result.returncode != 0 else None
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _dependency_audit(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Audit dependencies."""
        manifest = args["manifest"]
        lockfile = args.get("lockfile")
        
        findings = []
        
        # Python - safety
        if manifest.endswith("requirements.txt") or manifest.endswith(" Pipfile"):
            if self._command_exists("safety"):
                try:
                    result = subprocess.run(
                        f"safety check --file {manifest} --json",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.stdout:
                        vulnerabilities = json.loads(result.stdout)
                        for vuln in vulnerabilities:
                            findings.append({
                                "package": vuln.get("package_name", "unknown"),
                                "version": vuln.get("vulnerable_spec", ""),
                                "severity": vuln.get("severity", "unknown"),
                                "description": vuln.get("advisory", "")[:100]
                            })
                except Exception:
                    pass
            
            # pip-audit as fallback
            if self._command_exists("pip-audit") and not findings:
                try:
                    result = subprocess.run(
                        f"pip-audit -r {manifest}",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    for line in result.stdout.split('\n'):
                        if 'vulnerability' in line.lower():
                            findings.append({
                                "description": line.strip(),
                                "severity": "unknown"
                            })
                except Exception:
                    pass
        
        # Node.js - npm audit
        elif manifest.endswith("package.json"):
            try:
                result = subprocess.run(
                    "npm audit --json",
                    shell=True,
                    cwd=os.path.dirname(manifest) or '.',
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.stdout:
                    audit = json.loads(result.stdout)
                    vulnerabilities = audit.get("vulnerabilities", {})
                    
                    for pkg, info in vulnerabilities.items():
                        findings.append({
                            "package": pkg,
                            "severity": info.get("severity", "unknown"),
                            "via": info.get("via", [{}])[0].get("title", "")[:100]
                        })
            except Exception:
                pass
        
        return {
            "manifest": manifest,
            "vulnerabilities_found": len(findings),
            "findings": findings[:30]
        }
    
    def _complexity_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complexity report."""
        path = args["path"]
        fmt = args.get("format", "summary")
        
        complexities = []
        
        files = list(Path(path).rglob("*.py")) if os.path.isdir(path) else [Path(path)]
        
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Calculate complexity
                        complexity = 1
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                                complexity += 1
                            elif isinstance(child, ast.BoolOp):
                                complexity += len(child.values) - 1
                        
                        complexities.append({
                            "file": str(filepath),
                            "function": node.name,
                            "line": node.lineno,
                            "complexity": complexity,
                            "lines": node.end_lineno - node.lineno if node.end_lineno else 10
                        })
                        
            except Exception:
                continue
        
        # Calculate summary statistics
        if complexities:
            avg_complexity = sum(c["complexity"] for c in complexities) / len(complexities)
            high_complexity = [c for c in complexities if c["complexity"] > 10]
        else:
            avg_complexity = 0
            high_complexity = []
        
        if fmt == "summary":
            return {
                "files_analyzed": len(set(c["file"] for c in complexities)),
                "functions_analyzed": len(complexities),
                "average_complexity": round(avg_complexity, 2),
                "high_complexity_functions": len(high_complexity),
                "high_complexity_list": high_complexity[:10]
            }
        else:
            return {
                "files_analyzed": len(set(c["file"] for c in complexities)),
                "functions": sorted(complexities, key=lambda x: x["complexity"], reverse=True)
            }
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists."""
        return shutil.which(cmd) is not None


def main():
    server = QualityAssuranceServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    import asyncio
    main()
