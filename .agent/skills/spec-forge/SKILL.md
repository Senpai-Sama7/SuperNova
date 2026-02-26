---
name: spec-forge
description: Transforms vague requirements into precise, implementable specifications through structured decomposition, quality validation, and context management. Use when creating technical specifications, validating requirements quality, managing reusable context packs, or generating prompt variants for testing.
---

# Spec Forge MCP Server

## Overview

Spec Forge is an MCP server that transforms vague requirements into precise, implementable specifications through structured decomposition, quality validation, and context management. It bridges the gap between ambiguous user intent and actionable development artifacts.

**Core Capabilities:**
- Convert natural language requirements into structured specifications
- Validate specifications against quality gates (completeness, clarity, testability)
- Maintain persistent context packs for cross-session consistency
- Generate prompt variants optimized for different reasoning styles
- Decompose complex tasks into dependency-ordered subtasks

## Installation

```bash
# Clone or extract the server
cd spec-forge-mcp-server
npm install
npm run build

# Test the server
npm test
```

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spec-forge": {
      "command": "node",
      "args": ["/absolute/path/to/spec-forge-mcp-server/dist/index.js"]
    }
  }
}
```

---

## Tools Reference

### 1. spec_forge_create_spec

Transforms natural language intent into a structured, implementable specification.

**When to Use:**
- User describes a feature, system, or requirement in plain language
- Need to formalize vague ideas into actionable specs
- Starting a new project or feature from scratch

**Input Schema:**
```typescript
{
  intent: string;           // Required. Natural language description (10-5000 chars)
  domain?: string;          // Optional. Technical domain for context
  constraints?: string[];   // Optional. Known limitations or requirements
  context_pack_id?: string; // Optional. Reference existing context pack
}
```

**Output Structure:**
```typescript
{
  success: boolean;
  spec: {
    id: string;
    title: string;           // Generated from intent
    description: string;     // Expanded description
    requirements: {
      functional: string[];
      non_functional: string[];
    };
    acceptance_criteria: string[];
    assumptions: string[];
    out_of_scope: string[];
    technical_notes: string[];
    created_at: string;
  };
  quality_score: number;     // 0-100
  suggestions: string[];     // Improvement recommendations
}
```

**Example:**
```json
{
  "intent": "Users should be able to reset their password via email",
  "domain": "authentication",
  "constraints": ["Must complete within 15 minutes", "Single-use tokens only"]
}
```

---

### 2. spec_forge_quality_gate

Validates specifications or code against quality criteria. Returns actionable findings with severity levels.

**When to Use:**
- Before finalizing a specification
- Code review automation
- Checking for security issues, clarity problems, or missing elements

**Input Schema:**
```typescript
{
  content: string;          // Required. Specification or code to validate (10-50000 chars)
  content_type?: string;    // Optional. "specification" | "code" | "requirements" (default: "specification")
  strictness?: string;      // Optional. "lenient" | "standard" | "strict" (default: "standard")
}
```

**Output Structure:**
```typescript
{
  success: boolean;
  gate_result: {
    passed: boolean;
    score: number;          // 0-100
    findings: Array<{
      id: string;
      severity: "error" | "warning" | "info";
      category: string;     // "clarity" | "completeness" | "security" | "testability" | "consistency"
      message: string;
      location?: string;
      suggestion?: string;
    }>;
    summary: {
      total_findings: number;
      errors: number;
      warnings: number;
      info: number;
    };
    recommendations: string[];
  };
}
```

**Example:**
```json
{
  "content": "function login(user, pass) { if(pass == 'admin123') return true; }",
  "content_type": "code",
  "strictness": "strict"
}
```

**Detection Capabilities:**
- Hardcoded secrets/credentials → `error`
- SQL injection patterns → `error`
- Vague/ambiguous language → `warning`
- Missing error handling → `warning`
- TODO/FIXME comments → `info`
- Console.log statements → `info`

---

### 3. spec_forge_create_context_pack

Creates a reusable context pack for maintaining consistency across multiple specifications and sessions.

**When to Use:**
- Starting a new project with established constraints
- Documenting architectural decisions
- Capturing domain knowledge for reuse
- Building a knowledge base for consistent spec generation

**Input Schema:**
```typescript
{
  name: string;             // Required. Pack name (1-100 chars)
  description?: string;     // Optional. What this pack covers
  items: Array<{            // Required. At least one item
    type: "requirement" | "constraint" | "assumption" | "decision" | "context";
    content: string;        // The actual content (1-2000 chars)
    rationale?: string;     // Why this item exists
    source?: string;        // Where this came from
    confidence?: number;    // 0-1 confidence level
  }>;
  tags?: string[];          // Optional. Organization tags
}
```

**Output Structure:**
```typescript
{
  success: boolean;
  context_pack: {
    id: string;             // Use this ID to reference the pack
    name: string;
    items: Array<{
      id: string;
      type: string;
      content: string;
      confidence: number;
      timestamp: string;
    }>;
    tags: string[];
    created_at: string;
    updated_at: string;
  };
  usage_hint: string;
}
```

**Example:**
```json
{
  "name": "E-Commerce Platform Standards",
  "description": "Core constraints for all e-commerce features",
  "items": [
    {
      "type": "constraint",
      "content": "All prices must be stored in cents to avoid floating point errors",
      "rationale": "Prevents rounding issues in financial calculations"
    },
    {
      "type": "decision",
      "content": "Use Stripe for all payment processing",
      "rationale": "Corporate standard, existing integration"
    }
  ],
  "tags": ["payments", "architecture"]
}
```

---

### 4. spec_forge_update_context_pack

Adds, removes, or modifies items in an existing context pack.

**When to Use:**
- New constraints discovered during development
- Updating decisions based on learnings
- Removing obsolete context items
- Evolving project knowledge over time

**Input Schema:**
```typescript
{
  pack_id: string;          // Required. ID of pack to update
  operations: Array<{       // Required. At least one operation
    action: "add" | "update" | "remove";
    item_id?: string;       // Required for update/remove
    item?: {                // Required for add/update
      type: "requirement" | "constraint" | "assumption" | "decision" | "context";
      content: string;
      rationale?: string;
      source?: string;
      confidence?: number;
    };
  }>;
}
```

**Example:**
```json
{
  "pack_id": "abc-123-def",
  "operations": [
    {
      "action": "add",
      "item": {
        "type": "constraint",
        "content": "API rate limit: 100 requests per minute per user",
        "rationale": "Infrastructure limitation discovered in load testing"
      }
    },
    {
      "action": "remove",
      "item_id": "old-item-id"
    }
  ]
}
```

---

### 5. spec_forge_get_context_packs

Retrieves context packs by ID or searches by tags.

**When to Use:**
- Loading context for a new specification
- Finding relevant existing context
- Auditing what context packs exist

**Input Schema:**
```typescript
{
  pack_ids?: string[];      // Optional. Specific pack IDs to retrieve
  tags?: string[];          // Optional. Filter by tags (OR logic)
  include_items?: boolean;  // Optional. Include full item details (default: true)
}
```

**Output Structure:**
```typescript
{
  success: boolean;
  packs: Array<ContextPack>;
  total_count: number;
}
```

---

### 6. spec_forge_prompt_variants

Generates multiple prompt variants optimized for different reasoning styles and use cases.

**When to Use:**
- A/B testing different prompt approaches
- Optimizing prompts for specific models or tasks
- Exploring alternative framings of a problem
- Creating prompts for different audience expertise levels

**Input Schema:**
```typescript
{
  base_prompt: string;      // Required. Original prompt (10+ chars)
  task_description: string; // Required. What the prompt should accomplish (10+ chars)
  styles?: Array<           // Optional. Desired styles (default: all)
    "concise" | "detailed" | "structured" | 
    "conversational" | "technical" | "step_by_step"
  >;
  count?: number;           // Optional. Variants per style (1-5, default: 1)
  include_reasoning?: boolean; // Optional. Include style rationale (default: true)
}
```

**Output Structure:**
```typescript
{
  success: boolean;
  variants: Array<{
    id: string;
    style: string;
    prompt: string;
    reasoning: string;      // Why this style might be effective
    use_case: string;       // Best scenarios for this variant
  }>;
  recommendation: {
    best_for_accuracy: string;    // variant ID
    best_for_creativity: string;  // variant ID
    best_for_speed: string;       // variant ID
  };
}
```

**Example:**
```json
{
  "base_prompt": "Explain how OAuth 2.0 works",
  "task_description": "Help developers understand OAuth for API integration",
  "styles": ["technical", "step_by_step", "conversational"],
  "count": 1
}
```

---

## Usage Patterns

### Pattern 1: Full Specification Workflow

```
1. Create context pack with project constraints
2. Generate spec from intent (referencing context pack)
3. Run quality gate on generated spec
4. Iterate based on findings
5. Update context pack with new learnings
```

### Pattern 2: Code Review Pipeline

```
1. Receive code for review
2. Run quality_gate with strictness="strict"
3. Present findings organized by severity
4. Provide actionable remediation suggestions
```

### Pattern 3: Requirement Refinement

```
1. User provides vague requirement
2. Generate initial spec with create_spec
3. Quality gate identifies gaps
4. Prompt user for clarification on specific items
5. Regenerate with additional constraints
```

### Pattern 4: Context-Aware Multi-Spec Generation

```
1. Create master context pack for project
2. Generate feature specs referencing the pack
3. Each spec inherits project constraints automatically
4. Update pack as architectural decisions evolve
```

---

## Quality Gate Categories

| Category | What It Checks |
|----------|----------------|
| **clarity** | Vague language, ambiguous terms, undefined acronyms |
| **completeness** | Missing acceptance criteria, undefined edge cases |
| **security** | Hardcoded secrets, injection vulnerabilities, auth gaps |
| **testability** | Unmeasurable requirements, missing success criteria |
| **consistency** | Contradictory statements, conflicting requirements |

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **error** | Critical issue, must fix | Blocks approval |
| **warning** | Significant concern | Should address |
| **info** | Suggestion for improvement | Nice to have |

---

## Best Practices

1. **Always provide domain context** - Specs are more accurate with domain hints
2. **Use context packs for consistency** - Especially for multi-feature projects
3. **Run quality gates iteratively** - Catch issues early, not at review time
4. **Start lenient, finish strict** - Use lenient mode for drafts, strict for finals
5. **Preserve rationale** - Always include `rationale` in context items for future reference
6. **Tag strategically** - Use consistent tags across context packs for easy retrieval

---

## Error Handling

All tools return consistent error structures:

```typescript
{
  success: false;
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable description
    details?: any;          // Additional context
  };
}
```

Common error codes:
- `VALIDATION_ERROR` - Invalid input parameters
- `NOT_FOUND` - Referenced resource doesn't exist
- `INTERNAL_ERROR` - Server-side processing failure

---

## Evaluation

Run the included evaluation suite:

```bash
./eval.sh
```

Tests validate:
- Quality gate issue detection accuracy
- Score calculation correctness
- Context pack type preservation
- Spec generation from intent
- Security finding severity classification
