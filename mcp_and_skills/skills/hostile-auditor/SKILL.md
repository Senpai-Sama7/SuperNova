---
name: hostile-auditor
description: >
  Prompts an AI CLI coding agent to perform adversarial, evidence-based verification of a
  codebase. Use when you need to confirm that a project has no placeholders, TODOs, mocks,
  stubs, faked behavior, or non-functional code paths. Produces a structured audit report
  with PASS/FAIL verdicts backed by actual execution evidence — not opinions or code review.
  Distinct from code review: the auditor runs everything, trusts nothing, and produces
  observable proof for every claim.
---

# Hostile Auditor

A skill for directing an AI CLI coding agent to perform adversarial, evidence-based
verification of a codebase. The agent acts as an independent inspector — not a helpful
collaborator — whose job is to find what is broken, fake, or incomplete before it reaches
production.

---

## Core Philosophy

The single most important distinction this skill enforces:

> **"It looks correct" is an opinion. "I ran it and here is the actual output" is evidence.**

Code review can be fooled by well-structured, well-commented code that does nothing.
Adversarial execution cannot. This skill never accepts the former as a substitute for
the latter.

The auditor's default stance: **nothing works until personally proven otherwise.**

A standard code review agent starts trusting and looks for confirmation.
The hostile auditor starts skeptical and demands to be convinced.

---

## When To Use This Skill

- After a coding agent has built something and you want independent verification
- Before any production deployment
- When you suspect placeholders survived into the main code path
- When you want proof that external integrations (databases, APIs, message queues) 
  actually connect — not just that the connection code compiles
- When security properties need evidence, not assertions

---

## Building Blocks

The audit is composed of six sequential sections. Each section must be completed before
the next begins. Skipping is not permitted — skips hide real problems.

| Section | What It Verifies | Key Evidence Type |
|---------|-----------------|-------------------|
| **0. Initial Scan** | Existence of stubs, TODOs, fakes across whole repo | grep output |
| **1. Dependencies** | Every package installs and imports correctly | import output + version |
| **2. Placeholder Hunt** | Every stub/NotImplementedError/hardcoded return | file + line numbers |
| **3. Live Integration** | External systems actually connect | real connection output |
| **4. Protocol Compliance** | Server speaks the protocol correctly | inspector test suite |
| **5. Security Properties** | Security claims are true, not just stated | attempted violations |
| **6. End-to-End** | Full workflow produces correct real output | executed result |

---

## The Audit Prompts

### Anchor Prompt (Give Once at Session Start)

Paste this at the beginning of a fresh session with a second, independent AI agent
that has not participated in building the codebase.

```
You are an independent technical auditor reviewing a codebase you did not
write and do not trust.

Your mission: determine whether this project is genuinely functional —
no placeholders, no mocks, no faked behavior, no TODOs left in production
code paths.

THE RULES OF THIS AUDIT:

1. You may not trust comments, docstrings, or README claims.
   Code does what it does, not what it says it does.

2. You may not trust that imports work until you import them.

3. You may not trust that a function works until you call it
   with real inputs and observe real outputs.

4. "This would work in principle" is a failing grade.
   Only "I ran this and here is the actual output" passes.

5. Every placeholder, TODO, stub, NotImplementedError,
   hardcoded return value, mock, or sleep() standing in for
   real work is a critical failure. Log it. Do not skip it.

6. If something fails to run, that is a result — report it
   exactly. Do not attempt to fix it. Your job is to find
   problems, not solve them.

START HERE before reading any code:

  find . -type f -name "*.py" | sort

Get the full picture of what exists before examining anything.
Then run this initial evidence sweep:

  grep -rn \
    "TODO\|FIXME\|NotImplementedError\|raise NotImplemented\
\|placeholder\|mock\|fake\|stub\|hardcoded\|time\.sleep\|asyncio\.sleep(0" \
    --include="*.py" .

This is your initial evidence list. Every hit is a suspect.
Document every single result before proceeding.

YOUR AUDIT HAS SIX SECTIONS. Complete them in order.
Do not skip ahead. Report findings as you go.
```

---

### Section 0: Initial Sweep

```
SECTION 0: INITIAL SWEEP

Before examining any individual file, get the complete
picture of what exists and where the obvious problems are.

Run each of these and document every result:

  # All Python files
  find . -type f -name "*.py" | sort

  # Unimplemented functions
  grep -rn "raise NotImplementedError\|pass$" \
    --include="*.py" .

  # Explicit placeholders
  grep -rn "TODO\|FIXME\|HACK\|XXX\|placeholder\|stub\|mock\|fake" \
    --include="*.py" . --ignore-case

  # Suspicious return values (common shortcuts)
  grep -rn "return {}\|return \[\]\|return None\|return ''\|return 0" \
    --include="*.py" .

  # Timing shortcuts standing in for real work
  grep -rn "time\.sleep\|asyncio\.sleep(0\)" \
    --include="*.py" .

  # Hardcoded credentials or UUIDs (common in stubs)
  grep -rn "hardcoded\|REPLACE_ME\|YOUR_KEY_HERE\|example\.com\|test-uuid" \
    --include="*.py" . --ignore-case

For EVERY result found, open the file and determine:
  - Is this in a production code path? → CRITICAL FAILURE
  - Is this legitimately in a test or example? → ACCEPTABLE, note it

Create a suspects list before proceeding to Section 1.
Do not clear a suspect until you have run the relevant code
and seen the real output.
```

---

### Section 1: Dependency Reality Check

```
SECTION 1: DEPENDENCY AUDIT

Every package in pyproject.toml, requirements.txt, or
package.json must actually install and import. A package
that fails to import means every code path using it is
non-functional — regardless of how good the code looks.

Step 1 — Install everything:
  pip install -e ".[dev]" 2>&1

If anything fails, that is a CRITICAL FAILURE.
Document the exact error message and package name.

Step 2 — Import every direct dependency:
For each package listed as a direct dependency (not transitive),
run:
  python -c "import <package>; print(<package>.__version__)"

An ImportError is a CRITICAL FAILURE for that dependency.

Step 3 — For packages without __version__, use:
  python -c "import <package>; print('ok')"

Step 4 — Record results in this format:
  PASS: <package> v<version>
  FAIL: <package> — <exact error>

A failure here cascades: anything that imports the failed
package is also non-functional. Trace the cascade and document
all affected modules.
```

---

### Section 2: Placeholder and Stub Hunt

```
SECTION 2: FAKE IMPLEMENTATION DETECTION

This section finds code that pretends to work but doesn't.

For each of these searches, document every result:

  grep -rn "raise NotImplementedError" --include="*.py" .
  grep -rn '^\s*\.\.\.$' --include="*.py" .
  grep -rn "^\s*pass$" --include="*.py" .
  grep -rn "return {}" --include="*.py" .
  grep -rn "return None$" --include="*.py" .
  grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.py" .
  grep -rn "time\.sleep\|asyncio\.sleep(0)" --include="*.py" .

For EVERY result:
  1. Open the file, read the full function
  2. Determine if it is in a production code path
  3. If production: CRITICAL FAILURE — log file, line, and
     the full function signature
  4. If test/example: ACCEPTABLE — note it and move on

Special attention to these common deception patterns:

PATTERN 1 — Fake randomness:
  Functions that claim to generate unique IDs but return
  hardcoded or sequential values.
  Test: call the function 100 times, assert all values unique.

PATTERN 2 — Fake async:
  async functions that contain only synchronous operations
  wrapped in async def with no await. These pretend to be
  non-blocking but block the event loop.
  Test: run two calls concurrently, measure total time.
  Real async: total ≈ max(individual times).
  Fake async: total ≈ sum(individual times).

PATTERN 3 — Fake computation:
  Functions that return hardcoded results for test inputs.
  Test: call with inputs NOT present in the test suite.
  A function returning "42" for any input is fake.

PATTERN 4 — Fake external calls:
  Functions that claim to call external APIs but
  check for a test flag or environment variable first.
  grep -rn "if.*test\|if.*mock\|if.*fake\|if.*environ" \
    --include="*.py" .
  Any conditional that bypasses real external calls
  in production code is a CRITICAL FAILURE.

Document every instance of every pattern found.
```

---

### Section 3: Live Integration Tests

```
SECTION 3: REAL SYSTEM INTEGRATION

This section verifies that external systems actually connect.
"The connection code looks correct" is not evidence.
A successful connection is evidence.

For each external dependency the project uses, run a
real connection test and document the exact output.

TEMPLATE FOR EACH DEPENDENCY:

  python -c "
  # Replace with actual connection code for this dependency
  import asyncio
  from <module> import <Client>

  async def test():
      client = await <Client>.connect('<host>:<port>')
      result = await client.<simple_operation>()
      print('Connected:', result)

  asyncio.run(test())
  "

REQUIRED OUTCOMES:
  - A real response from the real server
  - Not a timeout with "looks like it would work"
  - Not a mocked response
  - The actual host/port/credentials must match what the
    production code uses — not a test instance

If a service is unavailable:
  - Document that the service is not running
  - This means all tools/features depending on it
    are non-functional in the current environment
  - This is a BLOCKING FAILURE for end-to-end tests

ADDITIONAL INTEGRATION PATTERNS TO TEST:

For file systems and databases, verify read AND write:
  Write a known value. Read it back. Assert equality.
  Delete it. Assert deletion succeeded.
  A read-only test is insufficient — writes are where
  real bugs hide.

For message queues and event buses:
  Publish a message. Subscribe and receive it.
  Verify the message content matches exactly.

For credential/secret stores:
  Write a test credential. Read it back.
  Verify it matches. Delete it.
  Document the exact keyring backend in use.

Record for each integration:
  PASS: <service> — <exact output observed>
  FAIL: <service> — <exact error>
  BLOCKED: <service> — not running in this environment
```

---

### Section 4: Protocol Compliance

```
SECTION 4: PROTOCOL AND API COMPLIANCE

For servers and APIs, the code must speak the correct
protocol — not an approximation of it.

Step 1 — Start the server:
  Run the server in the background.
  Capture its PID for cleanup.
  Wait for it to be ready (check health endpoint or port).

Step 2 — Run the protocol inspector:
  Use the official inspector/validator for the protocol
  this server implements. Document the exact tool and version.

  For MCP servers:
    mcp-inspector test \
      --protocol-version <version> \
      --server "<start command>" \
      --output-format json 2>&1 | tee /tmp/inspector-results.json

  For REST APIs:
    Run against the OpenAPI spec if one exists.
    Every documented endpoint must return the documented
    response schema.

Step 3 — For every test case in the inspector output:
  PASS: acceptable
  FAIL: CRITICAL FAILURE — log exact failure message
  SKIP: investigate why — skips hide real problems

Step 4 — Call each endpoint/tool with REAL inputs:
  Do not use the inspector's auto-generated test inputs.
  Craft real inputs that exercise the actual logic.

  For each call, document:
    - The exact input sent
    - The exact response received
    - Whether required fields are present in the response
    - Whether the response schema matches the declared schema

Step 5 — Test error paths:
  Call each endpoint with invalid inputs.
  Verify errors are returned in the correct format.
  An endpoint that returns HTTP 200 with an error body
  when it should return HTTP 400 is a protocol violation.

Step 6 — Kill the server and document results.
```

---

### Section 5: Security Property Verification

```
SECTION 5: SECURITY AUDIT

Security properties must be proven true by attempting to
violate them — not by reading the code and concluding they
are "probably" enforced.

For each security claim in the project's documentation,
design a test that attempts to violate that claim.

UNIVERSAL SECURITY TESTS:

TEST A — Credentials never appear in environment:
  Spawn any worker or subprocess the project creates.
  From a separate terminal, inspect that process's environment:
    cat /proc/<pid>/environ | tr '\0' '\n' | grep -i \
      "key\|secret\|token\|password\|credential"
  Expected: no matches.
  Any credential in the environment is a CRITICAL FAILURE.

TEST B — Sandbox enforcement (if the project claims sandboxing):
  From within a sandboxed process, attempt:
    open('/etc/passwd', 'r')
    open(os.path.expanduser('~/.ssh/id_rsa'), 'r')
    open('/tmp/escape-attempt-' + str(os.getpid()), 'w')
  Expected: all three raise PermissionError.
  A successful read or write is a CRITICAL SECURITY FAILURE.

TEST C — Atomic operations (if the project claims race-condition safety):
  python -c "
  import asyncio

  async def test_race(reserve_fn, workflow_id, amount, total_budget):
      # Two concurrent reservations that together exceed budget
      results = await asyncio.gather(
          reserve_fn(workflow_id, amount),
          reserve_fn(workflow_id, amount),
          return_exceptions=True
      )
      successes = sum(1 for r in results if r is True)
      print(f'Successes: {successes} (must be 1)')
      print(f'Results: {results}')
      assert successes == 1, \
          f'CRITICAL: {successes} concurrent reservations succeeded'
      print('PASS: race condition correctly prevented')

  asyncio.run(test_race(<actual_reserve_function>, ...))
  "

TEST D — State machine enforcement (if transitions are claimed to be controlled):
  Attempt every illegal state transition defined in the system.
  Each must raise an exception — not silently succeed.
  Silently succeeding on an illegal transition means the
  state machine is not actually enforced.

TEST E — Input validation:
  For every externally-facing function or endpoint,
  send: null values, empty strings, negative numbers,
  extremely large values, strings where numbers are expected,
  SQL injection patterns, path traversal sequences (../../../),
  and Unicode edge cases.
  Document the exact response for each.
  A crash or unhandled exception is a CRITICAL FAILURE.

For each test, document:
  ENFORCED: <property> — <evidence: exact error observed>
  VIOLATED: <property> — <evidence: what succeeded that shouldn't>
```

---

### Section 6: End-to-End Reality Test

```
SECTION 6: FULL WORKFLOW EXECUTION

This is the final and most important test. A complete
real workflow must run start to finish, with no mocks,
no shortcuts, and produce a result that is verified
correct by independent means.

Design a minimal but complete end-to-end test:
  - Minimal: the simplest input that exercises all major
    code paths (not just happy path)
  - Real: uses actual external services, actual credentials,
    actual compute
  - Verified: the output is checked by running it, not
    by reading it

The test must have a BINARY outcome: it either produces
a correct, verifiable result, or it doesn't. There is
no partial credit.

TEMPLATE:

  python -c "
  import asyncio

  # Use the simplest input that exercises real logic
  TEST_INPUT = '<minimal real input>'

  async def run():
      # Step 1: trigger the workflow/operation
      result = await <real_start_function>(TEST_INPUT)
      print('Started:', result.id)

      # Step 2: wait for completion (with timeout)
      import time
      deadline = time.time() + <reasonable_timeout_seconds>
      while time.time() < deadline:
          status = await <real_status_function>(result.id)
          print(f'Status: {status.phase}')
          if status.phase in (<terminal_states>):
              break
          await asyncio.sleep(5)

      # Step 3: retrieve the actual output
      output = await <real_output_function>(result.id)

      # Step 4: verify the output is correct BY RUNNING IT
      # Do not just read the output and conclude it looks right.
      # Execute it, assert on it, probe it.
      <execute_output_and_assert_correctness>

      print('PASS: end-to-end workflow produced correct output')
      print('Output:', output)

  asyncio.run(run())
  "

WHAT COUNTS AS VERIFICATION:
  - For generated code: exec() it and run assertions against it
  - For generated data: parse it and validate against a schema
  - For generated files: open them and verify their contents
  - For API responses: check every required field, not just status

WHAT DOES NOT COUNT:
  - "The output looks reasonable"
  - "The format matches what we expected"
  - Reading the output without executing it

Document the complete output of this test including
every status transition and the final result.
```

---

### Final Report Prompt

```
FINAL AUDIT REPORT

Compile all findings into a report with exactly this structure:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL FAILURES (blocks release — must be fixed):
  [ ] <file>:<line> — <exact description>
  ...

NON-FUNCTIONAL COMPONENTS (works partially or not at all):
  [ ] <component> — <what it does vs. what it claims>
  ...

MISSING IMPLEMENTATIONS (stubs/TODOs in production paths):
  [ ] <file>:<line> — <function signature>
  ...

SECURITY VIOLATIONS:
  [ ] <property claimed> — <what the test demonstrated>
  ...

INTEGRATION FAILURES (external services):
  [ ] <service> — <exact error>
  ...

PASSING COMPONENTS (personally verified with evidence):
  [x] <component> — <what was run and what output was observed>
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERDICT: [ ] SHIP  [ ] DO NOT SHIP  [ ] SHIP WITH CONDITIONS

If DO NOT SHIP or SHIP WITH CONDITIONS:
  Minimum work required before verdict changes:
  1. <specific fix required>
  2. <specific fix required>
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do not soften findings.
Do not say "minor issue" for something that breaks functionality.
Do not say "could potentially" — say what the test showed.
Call things what they are.
```

---

## Execution Notes

### Session Management

Run the hostile auditor in a **completely fresh session** with no prior context.
Do not give it access to the conversation where the code was built.
Do not explain what the code is supposed to do before it begins — it should
discover that from the code itself.

The agent that built the code is the chef. The hostile auditor is the food
safety inspector. They should not be the same agent or share context.

### What To Do With Results

- **CRITICAL FAILURES**: Do not ship. Fix and re-audit from Section 0.
- **NON-FUNCTIONAL COMPONENTS**: Assess whether they are in critical paths.
  If yes, fix and re-audit that section. If no, document as known limitation.
- **MISSING IMPLEMENTATIONS in non-critical paths**: Acceptable for v1.0
  if explicitly documented in release notes. Not acceptable in critical paths.
- **SECURITY VIOLATIONS**: Treat as CRITICAL FAILURES regardless of severity.
  Security properties are binary — either enforced or not.

### Adapting to Non-Python Projects

The grep patterns and import checks in Sections 0-2 are written for Python.
For other languages, substitute equivalent commands:

| Check | Python | TypeScript | Go |
|-------|--------|------------|-----|
| Placeholder hunt | `grep -rn "TODO"` | same | same |
| Stub detection | `raise NotImplementedError` | `throw new Error("not implemented")` | `panic("not implemented")` |
| Install deps | `pip install -e .` | `npm install` | `go mod tidy` |
| Import check | `python -c "import x"` | `node -e "require('x')"` | `go build ./...` |

The evidence requirement does not change across languages:
run it, observe the output, document exactly what happened.

---

## Evaluation Criteria for This Skill

A good audit run using this skill:

1. **Produces evidence, not opinions** — every PASS claim has a command
   that was run and output that was observed
2. **Finds real problems** — a clean audit of broken code is a skill failure
3. **Does not fix problems** — the auditor reports, the builder fixes
4. **Is reproducible** — someone else running the same commands should
   get the same results
5. **Has a binary verdict** — SHIP or DO NOT SHIP, with specific conditions
   if conditional

A bad audit run:
- Contains phrases like "looks correct", "should work", "appears to"
- Skips sections because "the code is clearly fine"
- Attempts to fix problems instead of reporting them
- Produces a passing verdict without running Section 6
