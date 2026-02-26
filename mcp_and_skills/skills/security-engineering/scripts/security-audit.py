#!/usr/bin/env python3
"""
Security Audit Script
Scans code for common security vulnerabilities and misconfigurations.
"""

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
from collections import defaultdict


class SecurityVisitor(ast.NodeVisitor):
    """AST visitor to detect security issues."""
    
    def __init__(self, filename):
        self.filename = filename
        self.issues = []
    
    def add_issue(self, line, severity, category, message, code=None):
        self.issues.append({
            'file': self.filename,
            'line': line,
            'severity': severity,
            'category': category,
            'message': message,
            'code': code
        })
    
    def visit_Call(self, node):
        # Check for dangerous functions
        if isinstance(node.func, ast.Name):
            if node.func.id in ('eval', 'exec'):
                self.add_issue(
                    node.lineno, 'CRITICAL', 'Injection',
                    f"Dangerous function '{node.func.id}' detected. Avoid using eval/exec.",
                    ast.get_source_segment(self.source, node)
                )
            elif node.func.id == 'pickle':
                self.add_issue(
                    node.lineno, 'HIGH', 'Deserialization',
                    "Pickle usage detected. Ensure data is trusted or use safer alternatives.",
                    ast.get_source_segment(self.source, node)
                )
        
        # Check for SQL injection risks
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ('execute', 'executemany'):
                # Check if first argument is a formatted string
                if node.args and isinstance(node.args[0], ast.JoinedStr):
                    self.add_issue(
                        node.lineno, 'CRITICAL', 'SQL Injection',
                        "SQL query uses f-string formatting. Use parameterized queries.",
                        ast.get_source_segment(self.source, node)
                    )
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        # Check for request data access without validation
        if isinstance(node.value, ast.Attribute):
            if node.value.attr in ('args', 'form', 'json', 'data'):
                self.add_issue(
                    node.lineno, 'MEDIUM', 'Input Validation',
                    f"Direct access to {node.value.attr} without validation detected.",
                    ast.get_source_segment(self.source, node)
                )
        
        self.generic_visit(node)


def scan_python_file(filepath):
    """Scan a Python file for security issues."""
    source = Path(filepath).read_text()
    issues = []
    
    # AST-based checks
    try:
        tree = ast.parse(source)
        visitor = SecurityVisitor(str(filepath))
        visitor.source = source
        visitor.visit(tree)
        issues.extend(visitor.issues)
    except SyntaxError:
        pass
    
    # Regex-based checks
    lines = source.split('\n')
    
    patterns = {
        'Hardcoded Secret': [
            (r'password\s*=\s*["\'][^"\']+["\']', 'HIGH'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'HIGH'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'HIGH'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'MEDIUM'),
        ],
        'Insecure Hash': [
            (r'hashlib\.md5', 'MEDIUM'),
            (r'hashlib\.sha1', 'MEDIUM'),
        ],
        'Debug Mode': [
            (r'debug\s*=\s*True', 'MEDIUM'),
            (r'DEBUG\s*=\s*True', 'MEDIUM'),
        ],
        'Insecure Protocol': [
            (r'http://(?!localhost)', 'LOW'),
            (r'ftp://', 'LOW'),
        ],
    }
    
    for category, pattern_list in patterns.items():
        for pattern, severity in pattern_list:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if not in a comment
                    code_part = line.split('#')[0]
                    if re.search(pattern, code_part, re.IGNORECASE):
                        issues.append({
                            'file': str(filepath),
                            'line': line_num,
                            'severity': severity,
                            'category': category,
                            'message': f"Potential {category.lower()} detected",
                            'code': line.strip()[:80]
                        })
    
    return issues


def scan_dependencies(dependency_file):
    """Scan dependencies for known vulnerabilities."""
    issues = []
    
    if not Path(dependency_file).exists():
        return issues
    
    # Try to run safety check
    try:
        result = subprocess.run(
            ['safety', 'check', '--file', dependency_file, '--json'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            vulnerabilities = json.loads(result.stdout)
            for vuln in vulnerabilities:
                issues.append({
                    'file': dependency_file,
                    'line': 0,
                    'severity': 'HIGH',
                    'category': 'Dependency',
                    'message': f"{vuln['package_name']} {vuln['vulnerable_spec']} - {vuln['advisory'][:100]}",
                    'code': None
                })
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return issues


def calculate_risk_score(issues):
    """Calculate overall risk score."""
    weights = {'CRITICAL': 10, 'HIGH': 5, 'MEDIUM': 2, 'LOW': 1}
    return sum(weights.get(i['severity'], 1) for i in issues)


def print_report(all_issues):
    """Print formatted security report."""
    # Group by severity
    by_severity = defaultdict(list)
    for issue in all_issues:
        by_severity[issue['severity']].append(issue)
    
    risk_score = calculate_risk_score(all_issues)
    
    print("=" * 70)
    print("SECURITY AUDIT REPORT")
    print("=" * 70)
    print(f"\nTotal Issues: {len(all_issues)}")
    print(f"Risk Score: {risk_score}/100")
    print(f"  CRITICAL: {len(by_severity.get('CRITICAL', []))}")
    print(f"  HIGH: {len(by_severity.get('HIGH', []))}")
    print(f"  MEDIUM: {len(by_severity.get('MEDIUM', []))}")
    print(f"  LOW: {len(by_severity.get('LOW', []))}")
    
    # Print by severity
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if severity in by_severity:
            print(f"\n{'-' * 70}")
            print(f"{severity} SEVERITY")
            print(f"{'-' * 70}")
            
            for issue in by_severity[severity][:20]:  # Limit output
                print(f"\n[{issue['category']}] {issue['file']}:{issue['line']}")
                print(f"  {issue['message']}")
                if issue['code']:
                    print(f"  Code: {issue['code'][:60]}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    categories = set(i['category'] for i in all_issues)
    
    if 'Injection' in categories:
        print("\n[Injection] Use parameterized queries and avoid eval/exec.")
    if 'Hardcoded Secret' in categories:
        print("\n[Secrets] Move secrets to environment variables or secret management.")
    if 'Deserialization' in categories:
        print("\n[Deserialization] Use JSON instead of pickle for untrusted data.")
    if 'Insecure Hash' in categories:
        print("\n[Hashing] Use SHA-256 or bcrypt for passwords.")
    if 'Debug Mode' in categories:
        print("\n[Configuration] Disable debug mode in production.")


def main():
    parser = argparse.ArgumentParser(description='Security audit for codebases')
    parser.add_argument('--source', '-s', required=True, help='Source directory to scan')
    parser.add_argument('--dependencies', '-d', help='Dependency file (requirements.txt)')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    
    args = parser.parse_args()
    
    all_issues = []
    
    # Scan Python files
    source_path = Path(args.source)
    for py_file in source_path.rglob('*.py'):
        # Skip common non-source directories
        if any(part.startswith('.') or part in ('venv', '__pycache__') 
               for part in py_file.parts):
            continue
        
        try:
            issues = scan_python_file(py_file)
            all_issues.extend(issues)
        except Exception as e:
            print(f"Error scanning {py_file}: {e}")
    
    # Scan dependencies
    if args.dependencies:
        issues = scan_dependencies(args.dependencies)
        all_issues.extend(issues)
    
    # Output
    if args.format == 'json':
        output = json.dumps({
            'issues': all_issues,
            'summary': {
                'total': len(all_issues),
                'risk_score': calculate_risk_score(all_issues),
                'by_severity': {
                    sev: len([i for i in all_issues if i['severity'] == sev])
                    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
                }
            }
        }, indent=2)
        
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
    else:
        print_report(all_issues)
        
        if args.output:
            Path(args.output).write_text(json.dumps(all_issues, indent=2))


if __name__ == '__main__':
    main()
