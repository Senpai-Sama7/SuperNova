#!/usr/bin/env python3
"""Minimal `predict_cmd` runner for OpenAI and Ollama stacks."""
import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List

import requests
import sys


DEFAULT_CRED_PATH = Path.home() / "Documents/.cred/cred.txt"


def parse_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        env[key] = value
    return env


def merged_env(env_file: Path) -> Dict[str, str]:
    env = parse_env_file(env_file)
    env.update(os.environ)
    return env


def sanitize_response(resp: Dict) -> str:
    if 'output' in resp:
        payload = resp['output']
        if isinstance(payload, list):
            return '\n'.join(segment.get('content', '') for segment in payload if isinstance(segment, dict))
        if isinstance(payload, str):
            return payload
    if 'choices' in resp:
        return '\n'.join(c.get('message', {}).get('content', '') for c in resp['choices'])
    return json.dumps(resp, indent=2)


def run_openai(args: argparse.Namespace, env: Dict[str, str]) -> Dict:
    api_key = env.get('OPENAI_API_KEY')
    if not api_key:
        raise SystemExit('OPENAI_API_KEY is required (set via ENV or cred file)')
    url = 'https://api.openai.com/v1/responses'
    payload: Dict = {'model': args.model, 'input': args.prompt}
    if args.temperature is not None:
        payload['temperature'] = args.temperature
    if args.top_p is not None:
        payload['top_p'] = args.top_p
    if args.max_tokens is not None:
        payload['max_tokens'] = args.max_tokens
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def run_ollama(args: argparse.Namespace, env: Dict[str, str]) -> Dict:
    base_url = args.ollama_url or env.get('OLLAMA_BASE_URL') or 'http://127.0.0.1:11434'
    api_key = env.get('OLLAMA_API_KEY')
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    payload: Dict = {
        'model': args.model,
        'prompt': args.prompt,
        'max_tokens': args.max_tokens or 2048,
        'temperature': args.temperature or 0.7,
    }
    if args.top_p is not None:
        payload['top_p'] = args.top_p
    url = f'{base_url.rstrip('/')}/api/v1/generate'
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run a lightweight predict_cmd for OpenAI or Ollama')
    parser.add_argument('--stack', choices=['openai', 'ollama'], required=True, help='Backend stack to query')
    parser.add_argument('--model', required=True, help='Model identifier (e.g., gpt-4o-mini, llama3.1)')
    parser.add_argument('--prompt', help='Prompt text (defaults to stdin)')
    parser.add_argument('--temperature', type=float, help='Sampling temperature')
    parser.add_argument('--top-p', type=float, help='Top-p probability mass')
    parser.add_argument('--max-tokens', type=int, help='Maximum tokens to request')
    parser.add_argument('--ollama-url', help='Override OLLAMA_BASE_URL')
    parser.add_argument('--env-file', type=Path, default=DEFAULT_CRED_PATH, help='Credentials file to source')
    parser.add_argument('--raw', action='store_true', help='Print raw JSON response instead of text content')
    return parser


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        return args.prompt
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit('Prompt is required; pass via --prompt or pipe text into the command.')


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    prompt = read_prompt(args)
    args.prompt = prompt
    env = merged_env(args.env_file)
    if args.stack == 'openai':
        result = run_openai(args, env)
    else:
        result = run_ollama(args, env)
    if args.raw:
        print(json.dumps(result, indent=2))
    else:
        print(sanitize_response(result))


if __name__ == '__main__':
    import sys

    main()
