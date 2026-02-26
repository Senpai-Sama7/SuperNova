# Dataset Schema (JSONL)

Each line is one JSON object.

Required fields:
- `id` (string): stable identifier
- `input` (string): user input to evaluate
- `expected` (string): expected output (label or text)

Optional fields:
- `metadata` (object): arbitrary metadata
- `group` (object): for fairness/bias checks (e.g., `{ "gender": "female" }`)

Examples:
```jsonl
{"id":"1","input":"My account is hacked. Please help.","expected":"urgent","group":{"region":"NA"}}
{"id":"2","input":"How do I change my billing address?","expected":"non-urgent","group":{"region":"EU"}}
```

Prediction outputs produced by `scripts/evaluate_prompt.py`:
- `id`, `input`, `expected`, `predicted`, `ok` (boolean), plus optional `raw_output`
