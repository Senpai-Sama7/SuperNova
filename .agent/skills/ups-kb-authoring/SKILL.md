---
name: ups-kb-authoring
description: Defines a workflow for writing UPS-style knowledge base and playbook content with retrieval-friendly structure, route markers, glossaries, and test prompts for consistent agent behavior.
---

# UPS knowledge base authoring

PURPOSE
Produce LLM-ingestible prediction-system documentation that is:
- structured for retrieval (chunk markers, routes)
- explicit about contracts and required outputs
- safe to apply in production settings

FORMAT CONTRACT
- Include YAML front matter with: doc_id, doc_title, doc_type, audience, last_updated, license.
- Include chunking guidance (max chunk size; split markers; preserve code/formulas/tables).
- Use explicit route markers: [[ROUTE:...]] for common question types.
- If you include algorithms, include pseudo-code blocks and clear assumptions.

RETRIEVAL OPTIMIZATION
- Prefer stable section headers with consistent names across versions.
- Avoid splitting inside code blocks, tables, and formulas.
- Include small "decision trees" for model selection and debugging.

DELIVERABLES
1) A complete markdown KB document.
2) A "prompt contract" snippet suitable as a system or developer message.
3) A test suite: 10 prompts that should be answered correctly using the KB.

QUALITY BAR
- The contract must force probabilistic outputs and decision-theoretic framing.
- The KB must include evaluation + calibration + monitoring guidance.


---

REFERENCE ASSETS (in the skill pack root folder)
- ups_output_schema.json
- core_contract.txt
