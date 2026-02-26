#!/usr/bin/env python3
"""
Log Analyzer for debugging and root cause analysis.
Analyzes log files to find error patterns, frequency, and correlations.
"""

import argparse
import re
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def parse_log_line(line, pattern=None):
    """Parse a log line extracting timestamp, level, and message."""
    # Common log patterns
    patterns = [
        # ISO timestamp with level
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\.,]?\d*)\s+(INFO|WARN|WARNING|ERROR|DEBUG|TRACE)\s+(.*)',
        # Standard format
        r'\[(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})\]\s+(INFO|WARN|WARNING|ERROR|DEBUG|TRACE)\s+(.*)',
        # Simple level prefix
        r'(INFO|WARN|WARNING|ERROR|DEBUG|TRACE):?\s+(.*)',
    ]
    
    for p in patterns:
        match = re.match(p, line.strip())
        if match:
            groups = match.groups()
            if len(groups) == 3:
                return {
                    'timestamp': groups[0],
                    'level': groups[1].upper(),
                    'message': groups[2]
                }
            elif len(groups) == 2:
                return {
                    'timestamp': None,
                    'level': groups[0].upper(),
                    'message': groups[1]
                }
    
    # Fallback: return raw message
    return {
        'timestamp': None,
        'level': 'UNKNOWN',
        'message': line.strip()
    }


def analyze_errors(log_file, error_pattern=None, time_window=None):
    """Analyze log file for errors and patterns."""
    errors = []
    error_counts = Counter()
    error_messages = defaultdict(list)
    timeline = []
    
    # Compile error pattern if provided
    error_re = re.compile(error_pattern, re.IGNORECASE) if error_pattern else None
    
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            parsed = parse_log_line(line)
            
            # Check if it's an error
            is_error = parsed['level'] in ('ERROR', 'CRITICAL', 'FATAL')
            
            # Or matches error pattern
            if error_re and error_re.search(parsed['message']):
                is_error = True
            
            if is_error:
                error_info = {
                    'line': line_num,
                    'timestamp': parsed['timestamp'],
                    'level': parsed['level'],
                    'message': parsed['message']
                }
                errors.append(error_info)
                
                # Extract error type/message pattern
                error_key = extract_error_signature(parsed['message'])
                error_counts[error_key] += 1
                error_messages[error_key].append(error_info)
                
                timeline.append({
                    'time': parsed['timestamp'],
                    'type': error_key
                })
    
    return {
        'total_errors': len(errors),
        'error_types': dict(error_counts.most_common(20)),
        'error_details': {k: v[:5] for k, v in error_messages.items()},  # First 5 of each
        'timeline': timeline,
        'first_error': errors[0] if errors else None,
        'last_error': errors[-1] if errors else None
    }


def extract_error_signature(message):
    """Extract a signature for error clustering."""
    # Remove variable parts (IDs, timestamps, numbers)
    signature = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', message)
    signature = re.sub(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', '<TIMESTAMP>', signature)
    signature = re.sub(r'0x[0-9a-f]+', '<ADDR>', signature)
    signature = re.sub(r'\d+', '<N>', signature)
    signature = re.sub(r"'[^']+'", "'<STR>'", signature)
    signature = re.sub(r'"[^"]+"', '"<STR>"', signature)
    
    # Extract exception type if present
    exception_match = re.search(r'(\w+Error|Exception):', signature)
    if exception_match:
        return exception_match.group(1)
    
    return signature[:100]  # Truncate long signatures


def find_correlations(errors, window_minutes=5):
    """Find correlated errors occurring close together."""
    correlations = defaultdict(lambda: defaultdict(int))
    
    # Group errors by time window
    for i, err1 in enumerate(errors):
        for err2 in errors[i+1:]:
            # In a real implementation, parse timestamps and compare
            # For now, assume sequential proximity indicates temporal proximity
            correlations[err1['type']][err2['type']] += 1
    
    return correlations


def print_report(analysis):
    """Print formatted analysis report."""
    print("=" * 60)
    print("LOG ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nTotal Errors: {analysis['total_errors']}")
    
    if analysis['first_error']:
        print(f"\nFirst Error: Line {analysis['first_error']['line']}")
        print(f"  {analysis['first_error']['message'][:80]}")
    
    if analysis['last_error']:
        print(f"\nLast Error: Line {analysis['last_error']['line']}")
        print(f"  {analysis['last_error']['message'][:80]}")
    
    print("\n" + "-" * 60)
    print("TOP ERROR TYPES")
    print("-" * 60)
    for error_type, count in analysis['error_types'].items():
        print(f"  {count:5d}  {error_type[:70]}")
    
    print("\n" + "-" * 60)
    print("ERROR EXAMPLES")
    print("-" * 60)
    for error_type, details in list(analysis['error_details'].items())[:5]:
        print(f"\n{error_type[:70]}")
        for detail in details[:2]:
            print(f"  Line {detail['line']}: {detail['message'][:60]}...")


def main():
    parser = argparse.ArgumentParser(description='Analyze log files for errors and patterns')
    parser.add_argument('--file', '-f', required=True, help='Log file to analyze')
    parser.add_argument('--error-pattern', '-e', help='Regex pattern to identify errors')
    parser.add_argument('--time-window', '-t', type=int, help='Time window in minutes')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    
    args = parser.parse_args()
    
    analysis = analyze_errors(args.file, args.error_pattern, args.time_window)
    
    if args.format == 'json':
        output = json.dumps(analysis, indent=2)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
    else:
        print_report(analysis)
        
        if args.output:
            Path(args.output).write_text(json.dumps(analysis, indent=2))
            print(f"\nFull analysis saved to: {args.output}")


if __name__ == '__main__':
    main()
