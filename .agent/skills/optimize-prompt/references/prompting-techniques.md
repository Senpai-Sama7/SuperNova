# Prompting Techniques (Quick Index)

Load this when selecting techniques in Phase 3.

## Techniques (when-to-use + template)

1. **Output contract**
   - Use when: output must be machine-parseable.
   - Add: exact schema + allowed values + examples.

2. **Role + responsibility**
   - Use when: task benefits from consistent stance/criteria.
   - Add: "You are a X. Your job is to Y. You must Z."

3. **Few-shot examples**
   - Use when: classification/extraction has tricky edge cases.
   - Add: 3-8 examples, include contrasts near the decision boundary.

4. **Contrastive pairs**
   - Use when: model confuses two classes or styles.
   - Add: near-miss example pairs labeled differently.

5. **Rubric / scoring guide**
   - Use when: decisioning needs stable criteria.
   - Add: bullet rubric with weights or priorities.

6. **Step-back framing**
   - Use when: model misses the bigger task framing.
   - Add: "Before answering, restate the goal in one sentence."

7. **Decomposition**
   - Use when: multi-step reasoning is required.
   - Add: explicit steps; keep intermediate outputs internal if needed.

8. **Self-check**
   - Use when: format errors or missing constraints happen.
   - Add: "Check: output matches schema; no extra text; label in allowed set."

9. **Error-aware instructions**
   - Use when: known failure modes exist.
   - Add: "Common mistakes: ... Avoid: ..."

10. **Abstain / uncertainty option**
   - Use when: incorrect answers are expensive.
   - Add: "If uncertain, output 'unknown'." and define escalation path.

11. **Length + style constraints**
   - Use when: verbosity hurts latency/cost or UX.
   - Add: hard limits (characters/tokens/lines).

12. **Sanitization boundary**
   - Use when: untrusted input can inject instructions.
   - Add: treat user input as data, not instructions; delimit clearly.

## Minimal templates

### Classification (label-only)
```text
Task: Classify the INPUT into one of: <LABELS>.
Output: one label only, exactly as written in <LABELS>. No extra text.

INPUT:
{input}
```

### JSON extraction
```text
Extract fields from INPUT.
Output: JSON matching exactly this schema: {"fieldA": "...", "fieldB": "..."}.
Rules: no extra keys; use null for missing fields.

INPUT:
{input}
```
