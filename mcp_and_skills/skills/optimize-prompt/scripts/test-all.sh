#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -c "import json; print('python ok')"

tmp="$(mktemp -d /tmp/optimize-prompt.XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

cat >"$tmp/base.txt" <<'EOF'
Task: Classify the INPUT as urgent or non-urgent.
Output: one label only: urgent or non-urgent.

INPUT:
{input}
EOF

cat >"$tmp/data.jsonl" <<'EOF'
{"id":"1","input":"My account is hacked.","expected":"urgent","group":{"region":"NA"}}
{"id":"2","input":"How do I change my billing address?","expected":"non-urgent","group":{"region":"EU"}}
EOF

python3 "$root/scripts/generate_variations.py" \
  --base-prompt "$tmp/base.txt" \
  --out-dir "$tmp/vars" \
  --techniques role,output_contract,self_check \
  --num-variations 2 \
  --seed 1 >/dev/null

# "Predict" by emitting the expected label based on a dumb heuristic (contains 'hacked' => urgent).
predict_cmd='python3 -c "import sys,re; s=sys.stdin.read().lower(); print(\"urgent\" if \"hacked\" in s else \"non-urgent\")"'

python3 "$root/scripts/evaluate_prompt.py" \
  --prompt "$tmp/base.txt" \
  --data "$tmp/data.jsonl" \
  --out "$tmp/results.jsonl" \
  --predict-cmd "$predict_cmd" >/dev/null

python3 "$root/scripts/calculate_metrics.py" \
  --results "$tmp/results.jsonl" \
  --task classification \
  --out "$tmp/metrics.json" >/dev/null

python3 "$root/scripts/bias_audit.py" \
  --results "$tmp/results.jsonl" \
  --attribute region \
  --out "$tmp/bias.md" >/dev/null

python3 "$root/scripts/injection_test.py" \
  --prompt "$tmp/base.txt" \
  --adversarial "$root/references/adversarial-examples.txt" \
  --predict-cmd "$predict_cmd" \
  --expected-regex '^(urgent|non-urgent)$' \
  --out "$tmp/injection.json" >/dev/null || true

echo "ok: smoke tests completed"

