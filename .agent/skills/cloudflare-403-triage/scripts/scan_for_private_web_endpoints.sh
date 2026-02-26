#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"

if ! command -v rg >/dev/null 2>&1; then
  echo "error: ripgrep (rg) not found on PATH" >&2
  exit 2
fi

echo "Scanning: ${root}"
echo

# NOTE: This script is for diagnostics. It intentionally does not provide or
# implement any techniques to bypass security challenges.
patterns=(
  'chatgpt\.com/backend-api'
  'chat\.openai\.com/backend-api'
  '/backend-api/'
  'connectors/directory/list'
  '__cf_chl'
  'challenge-platform'
  'Just a moment\.\.\.'
  'cf-ray'
)

for p in "${patterns[@]}"; do
  echo "== rg -n \"${p}\" ${root}"
  rg -n --no-heading --hidden --glob '!.git/**' "${p}" "${root}" || true
  echo
done
