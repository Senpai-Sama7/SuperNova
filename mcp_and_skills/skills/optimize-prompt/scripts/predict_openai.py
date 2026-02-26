#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Read prompt from stdin and call OpenAI via REST.")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--api-base", default="https://api.openai.com/v1")
    args = parser.parse_args()

    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY__OPENAI")
    if not key:
        parser.error("OPENAI_API_KEY environment variable is required")

    prompt = sys.stdin.read()
    if not prompt:
        parser.error("Prompt must be passed via stdin")

    payload: dict[str, Any] = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }

    req = urllib.request.Request(
        f"{args.api_base.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    choices = body.get("choices", [])
    if not choices:
        print("", end="")
        return 0
    content = choices[0].get("message", {}).get("content", "")
    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
