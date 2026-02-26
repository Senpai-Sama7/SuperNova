# Benchmark Datasets (Pointers)

Use this as a pointer list when you need realistic evaluation sets. Prefer task-specific internal
data when available.

- Classification: build a labeled JSONL from your domain; include boundary cases.
- Extraction: include tricky formatting and missing-field examples.
- Reasoning/math: pick small representative sets and measure exact match.

Note: This skill intentionally avoids hardcoding external benchmark downloads. When needed, search
for the current dataset access instructions and licensing.
