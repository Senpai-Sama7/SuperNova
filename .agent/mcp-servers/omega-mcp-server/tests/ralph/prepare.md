# RALPH Loop: Prepare Phase

## Purpose
Initialize the RALPH testing environment by generating status.json from the test plan.

## Input
- **Test Plan:** `tests/ralph/test_plan.md`

## Output
- **Status File:** `tests/ralph/status.json`
- **Results Log:** `tests/ralph/results.md` (initialized empty)

## Instructions

1. Read the test plan markdown file
2. Extract ALL test cases (format: TC-XXX)
3. For each test case, extract:
    - TC ID (e.g., "TC-001")
    - Name (the test case title)
    - Category (browser/system/image/docker/websocket/network/notify/red-team/blue-team/purple-team)
    - Priority (Critical/High/Medium/Low)
    - Prerequisites (what needs to be set up)
    - Test Steps
    - Expected Result

4. Generate a JSON file with this exact structure:

```json
{
  "metadata": {
    "testPlanSource": "tests/ralph/test_plan.md",
    "totalIterations": 0,
    "maxIterations": 100,
    "startedAt": null,
    "lastUpdatedAt": null,
    "summary": {
      "total": 44,
      "pending": 44,
      "pass": 0,
      "fail": 0,
      "knownIssue": 0
    }
  },
  "testCases": {
    "TC-XXX": {
      "name": "Test case name",
      "category": "category-name",
      "priority": "Critical|High|Medium|Low",
      "status": "pending",
      "fixAttempts": 0,
      "notes": "",
      "lastTestedAt": null,
      "errorLog": []
    }
  },
  "knownIssues": []
}
```

5. Initialize results.md with header:

```markdown
# RALPH Test Results: OMEGA MCP Server

## Test Run Information
- Started At: {timestamp}
- Test Plan: tests/ralph/test_plan.md
- Total Test Cases: 44

## Iteration Log

```

## Extraction Rules

- Test case IDs follow pattern: `TC-NNN` (3 digits)
- Categories match the tool category in test plan
- Priority is marked in test plan headers
- Default priority is "Medium" if not specified
