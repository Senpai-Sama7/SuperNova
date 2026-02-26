#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Read prompt from stdin and call Ollama HTTP API.")
    parser.add_argument("--model", default="llama3", help="Ollama model name.")
    parser.add_argument("--host", default="http://127.0.0.1:11434", help="Ollama server URL.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    prompt = sys.stdin.read()
    if not prompt:
        parser.error("Prompt must be provided via stdin")

    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": prompt,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }

    req = urllib.request.Request(
        f"{args.host.rstrip('/')}/run",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    output = ""
    if isinstance(body.get("output"), list):
        output = "\n".join(str(x) for x in body["output"])
    elif isinstance(body.get("output"), str):
        output = body["output"]

    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
