---
name: context-management
description: Intelligent context window management, summarization strategies, and relevance scoring for AI agents working with large codebases. Use when working with large files, complex multi-file changes, analyzing large codebases, prioritizing what to load into context, or when approaching context window limits.
---

# Context Management

Strategies for maximizing effectiveness within context window constraints.

## The Context Budget

Treat context window as a scarce resource:
- **System prompt**: ~10-20% of budget (instructions, skills)
- **Conversation history**: ~30-40% of budget (grows over time)
- **Active code/files**: ~30-40% of budget (your working set)
- **Reserve**: ~10-20% for generation and safety

## Context Management Workflow

### 1. Assess the Situation

**Calculate context pressure:**
```
pressure = (current_tokens / max_tokens) * 100

pressure < 50%: Relaxed - load generously
pressure 50-80%: Moderate - be selective
pressure > 80%: Critical - aggressive management
```

Use scripts/context-monitor.py:
```bash
python scripts/context-monitor.py --estimate
```

### 2. Prioritize Information

**Relevance hierarchy (highest to lowest):**

1. **User's current request** - Must understand completely
2. **Active file being edited** - Primary work area
3. **Direct dependencies** - Files imported by active file
4. **Test files** - Verification context
5. **Related configuration** - Build, lint, type configs
6. **Similar implementations** - Reference patterns
7. **Documentation** - How things should work
8. **Peripheral files** - Indirect dependencies
9. **Historical context** - Older conversation turns
10. **General knowledge** - Can rely on base model

### 3. Apply Compression Strategies

#### Summarization

Replace large files with summaries:

```
BEFORE (500 lines):
[Full file contents...]

AFTER (50 lines):
# File: src/services/user_service.py
# Summary: User management service with CRUD operations,
# authentication, and profile management.
# Key methods:
# - create_user(email, password) -> User
# - authenticate(email, password) -> Token
# - update_profile(user_id, data) -> User
# Dependencies: UserRepository, EmailService
```

Use scripts/smart-summarize.py:
```bash
python scripts/smart-summarize.py \
  --file src/large_module.py \
  --max-lines 50 \
  --include-signatures
```

#### Semantic Chunking

Break files into logical sections:

```
# Chunk: UserService class (lines 1-150)
- Handles user CRUD operations
- Key: create_user, get_user, update_user, delete_user
- Uses: UserRepository

# Chunk: Authentication methods (lines 151-280)
- Handles login/logout/token refresh
- Key: authenticate, refresh_token, invalidate_session
- Uses: TokenService, RedisCache

[Load only relevant chunks]
```

#### Hierarchical Collapse

Show structure without full content:

```
# Module: services/
├── user_service.py [COLLAPSED]
│   ├── class UserService
│   │   ├── create_user() [+20 lines]
│   │   └── authenticate() [+35 lines]
├── payment_service.py [EXPANDED]
│   └── [full content shown...]
└── notification_service.py [COLLAPSED]
```

### 4. Progressive Disclosure

Load context in waves:

**Wave 1 - Overview:**
- Directory structure
- Key file signatures
- Architecture summary

**Wave 2 - Focus Area:**
- Specific files for the task
- Their direct dependencies
- Relevant tests

**Wave 3 - Deep Dive:**
- Specific functions/methods
- Implementation details
- Edge cases

### 5. Maintain Context Currency

**When to refresh:**
- After significant file changes
- When switching tasks
- When context pressure > 80%
- When model seems confused

**How to refresh:**
- Re-read modified files
- Update summaries
- Re-verify assumptions

## Advanced Techniques

### Symbolic References

Reference code without including full text:

```
# See: src/models/user.py::User.validate_email()
# Expected behavior: Validates email format, raises ValueError on invalid

[Use reference to understand without loading full file]
```

### Differential Context

Show only what's changed:

```
# File: src/api/users.py
# Base version: abc123
# Changes:
+ Added rate limiting decorator
+ Modified error handling for 429 responses
- Removed deprecated endpoint
# [Full file not shown, apply diff mentally]
```

### Knowledge Externalization

Move stable knowledge out of context:

1. **To skill files**: Common patterns, domain knowledge
2. **To references**: API docs, schemas, guidelines
3. **To scripts**: Automated analysis tools
4. **To project docs**: Architecture decisions, conventions

## Codebase Analysis

### Understanding Large Codebases

Use scripts/codebase-mapper.py:

```bash
# Generate high-level map
python scripts/codebase-mapper.py \
  --root ./ \
  --output map.json \
  --include-dependencies

# Query the map
python scripts/codebase-mapper.py \
  --query "find all users of PaymentService" \
  --map map.json
```

### Dependency Graph Analysis

Identify what to load based on dependency graph:

```
UserController (active)
├── UserService [LOAD]
│   ├── UserRepository [LOAD]
│   └── EmailService [SUMMARIZE]
├── AuthMiddleware [LOAD]
└── ValidationSchemas [LOAD]
```

### Relevance Scoring

Score files by relevance to current task:

```python
score = (
    keyword_matches * 2 +
    import_distance * -1 +
    recent_changes * 1.5 +
    test_coverage * 0.5
)
```

Use scripts/relevance-scorer.py:
```bash
python scripts/relevance-scorer.py \
  --task "add user profile endpoint" \
  --files "src/**/*.py" \
  --top 10
```

## Conversation Management

### Selective History

Summarize older conversation turns:

```
[Earlier: Discussed database schema options, decided on PostgreSQL with 
UUID primary keys. User requested REST API for user management.]

[Recent - full detail:]
User: Add email verification to the registration endpoint
```

### Checkpointing

Create save points in long sessions:

```
--- CHECKPOINT: User service implementation complete ---
Files created: src/services/user.py, src/models/user.py, tests/...
Design decisions: Using repository pattern, bcrypt for hashing
Next: Email verification feature
---
```

## Language-Specific Context Tips

### Python
- Type hints convey intent (load type stubs if available)
- `__init__.py` shows module structure
- Decorators modify behavior (check implementations)

### JavaScript/TypeScript
- Type definitions (.d.ts) are high signal
- Package.json shows dependencies and scripts
- Import trees reveal architecture

### Java
- Interface definitions are contracts
- Annotations carry semantic weight
- Maven/Gradle files show dependencies

### Go
- Interface satisfaction is implicit
- Package structure is meaningful
- Error handling patterns repeat

## Crisis Management

### When Context Is Exhausted

1. **Immediate:** Summarize current state to user, ask for new session
2. **Short-term:** Use scripts/context-compact.py to compress
3. **Long-term:** Break task into smaller chunks

### Recovery Patterns

```
[Context lost or corrupted]

Recovery protocol:
1. Re-state current goal
2. Re-load essential files only
3. Verify understanding with user
4. Continue from last known good state
```

## Resources

- [summarization-patterns.md](references/summarization-patterns.md) - Summarization strategies
- [codebase-analysis.md](references/codebase-analysis.md) - Large codebase techniques
- [relevance-scoring.md](references/relevance-scoring.md) - Prioritization algorithms
