#!/usr/bin/env python3
"""
Code Metrics Analyzer
Calculates cyclomatic complexity, cognitive complexity, and other metrics.
"""

import argparse
import ast
import json
import os
import re
from collections import defaultdict
from pathlib import Path


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity."""
    
    def __init__(self):
        self.complexity = 1  # Base complexity
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


def calculate_cyclomatic_complexity(source):
    """Calculate cyclomatic complexity of Python code."""
    try:
        tree = ast.parse(source)
        analyzer = ComplexityAnalyzer()
        analyzer.visit(tree)
        return analyzer.complexity
    except SyntaxError:
        return None


def calculate_function_metrics(source, filename):
    """Calculate metrics for each function in the source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    metrics = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_source = ast.get_source_segment(source, node) or ""
            
            # Basic metrics
            lines = len(func_source.split('\n'))
            
            # Complexity
            analyzer = ComplexityAnalyzer()
            analyzer.visit(node)
            complexity = analyzer.complexity
            
            # Parameters
            param_count = len(node.args.args) + len(node.args.kwonlyargs)
            if node.args.vararg:
                param_count += 1
            if node.args.kwarg:
                param_count += 1
            
            # Nesting depth
            max_depth = calculate_nesting_depth(node)
            
            # Return statements
            return_count = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
            
            metrics.append({
                'name': node.name,
                'file': filename,
                'line': node.lineno,
                'lines': lines,
                'complexity': complexity,
                'parameters': param_count,
                'nesting_depth': max_depth,
                'returns': return_count,
                'is_async': isinstance(node, ast.AsyncFunctionDef)
            })
    
    return metrics


def calculate_nesting_depth(node):
    """Calculate maximum nesting depth of a function."""
    max_depth = 0
    current_depth = 0
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            current_depth += 1
            max_depth = max(max_depth, current_depth)
    
    return max_depth


def calculate_file_metrics(filepath):
    """Calculate metrics for a single file."""
    source = Path(filepath).read_text()
    lines = source.split('\n')
    
    # Basic counts
    total_lines = len(lines)
    code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    blank_lines = len([l for l in lines if not l.strip()])
    comment_lines = len([l for l in lines if l.strip().startswith('#')])
    
    # Imports
    imports = len([l for l in lines if l.strip().startswith(('import ', 'from '))])
    
    # Classes and functions
    try:
        tree = ast.parse(source)
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        functions = len([n for n in ast.walk(tree) 
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
    except SyntaxError:
        classes = functions = 0
    
    # Function metrics
    function_metrics = calculate_function_metrics(source, str(filepath))
    
    return {
        'file': str(filepath),
        'total_lines': total_lines,
        'code_lines': code_lines,
        'blank_lines': blank_lines,
        'comment_lines': comment_lines,
        'imports': imports,
        'classes': classes,
        'functions': functions,
        'function_metrics': function_metrics
    }


def analyze_directory(path, exclude_patterns=None):
    """Analyze all Python files in a directory."""
    exclude_patterns = exclude_patterns or ['venv', '.venv', '__pycache__', '.git', 'node_modules']
    
    all_metrics = []
    
    for root, dirs, files in os.walk(path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_patterns and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                try:
                    metrics = calculate_file_metrics(filepath)
                    all_metrics.append(metrics)
                except Exception as e:
                    print(f"Error analyzing {filepath}: {e}")
    
    return all_metrics


def print_summary(metrics):
    """Print summary of code metrics."""
    total_files = len(metrics)
    total_lines = sum(m['total_lines'] for m in metrics)
    total_functions = sum(len(m['function_metrics']) for m in metrics)
    
    # Find high complexity functions
    all_functions = []
    for m in metrics:
        all_functions.extend(m['function_metrics'])
    
    high_complexity = [f for f in all_functions if f['complexity'] > 10]
    long_functions = [f for f in all_functions if f['lines'] > 50]
    many_params = [f for f in all_functions if f['parameters'] > 4]
    
    print("=" * 70)
    print("CODE METRICS SUMMARY")
    print("=" * 70)
    print(f"\nFiles analyzed: {total_files}")
    print(f"Total lines: {total_lines:,}")
    print(f"Total functions: {total_functions}")
    
    print("\n" + "-" * 70)
    print("COMPLEXITY ISSUES")
    print("-" * 70)
    print(f"Functions with complexity > 10: {len(high_complexity)}")
    for func in sorted(high_complexity, key=lambda x: x['complexity'], reverse=True)[:10]:
        print(f"  {func['complexity']:3d}  {func['file']}::{func['name']} (line {func['line']})")
    
    print("\n" + "-" * 70)
    print("LONG FUNCTIONS")
    print("-" * 70)
    print(f"Functions > 50 lines: {len(long_functions)}")
    for func in sorted(long_functions, key=lambda x: x['lines'], reverse=True)[:10]:
        print(f"  {func['lines']:4d}  {func['file']}::{func['name']} (line {func['line']})")
    
    print("\n" + "-" * 70)
    print("MANY PARAMETERS")
    print("-" * 70)
    print(f"Functions with > 4 parameters: {len(many_params)}")
    for func in sorted(many_params, key=lambda x: x['parameters'], reverse=True)[:10]:
        print(f"  {func['parameters']:2d}  {func['file']}::{func['name']} (line {func['line']})")


def main():
    parser = argparse.ArgumentParser(description='Analyze code metrics')
    parser.add_argument('--path', '-p', default='.', help='Path to analyze')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--exclude', '-e', nargs='+', help='Patterns to exclude')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    
    args = parser.parse_args()
    
    metrics = analyze_directory(args.path, args.exclude)
    
    if args.format == 'json':
        output = json.dumps(metrics, indent=2)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
    else:
        print_summary(metrics)
        
        if args.output:
            Path(args.output).write_text(json.dumps(metrics, indent=2))
            print(f"\nDetailed metrics saved to: {args.output}")


if __name__ == '__main__':
    main()
