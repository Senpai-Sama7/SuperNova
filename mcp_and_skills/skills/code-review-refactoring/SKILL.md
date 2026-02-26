---
name: code-review-refactoring
description: Code quality analysis, review automation, and systematic refactoring techniques. Use when reviewing code for quality issues, refactoring legacy code, improving code maintainability, identifying technical debt, applying design patterns, or establishing code quality standards.
---

# Code Review & Refactoring

Systematic approach to improving code quality through review and refactoring.

## Code Review Philosophy

**Purpose of code review:**
1. Catch defects before they reach production
2. Share knowledge across the team
3. Maintain consistency and standards
4. Identify opportunities for improvement

**Review mindset:**
- Be constructive, not critical
- Explain the "why", not just the "what"
- Distinguish between blockers and suggestions
- Approve with comments for non-blocking issues

## Review Checklist

### Correctness
- [ ] Logic handles edge cases (null, empty, max values)
- [ ] Error cases are handled appropriately
- [ ] Concurrency issues considered (if applicable)
- [ ] Resource cleanup (files, connections, locks)

### Maintainability
- [ ] Functions are focused and single-purpose
- [ ] Names reveal intent (variables, functions, classes)
- [ ] Complexity is appropriate (cyclomatic < 10)
- [ ] No duplicated logic (DRY principle)

### Testability
- [ ] Dependencies are injectable
- [ ] Side effects are isolated
- [ ] Tests exist and are meaningful
- [ ] Edge cases are covered

### Performance
- [ ] No obvious inefficiencies (N+1 queries, nested loops)
- [ ] Resource usage is reasonable
- [ ] Asynchronous operations where appropriate

### Security
- [ ] Input validation on all boundaries
- [ ] No secrets in code
- [ ] Authorization checks in place
- [ ] Injection risks addressed

Use scripts/review-checklist.py for automated checks:
```bash
python scripts/review-checklist.py --diff HEAD~1
```

## Automated Analysis

### Static Analysis

Run language-specific linters and analyzers:

```bash
# Python
ruff check src/
mypy src/
bandit -r src/

# JavaScript
eslint src/
prettier --check src/

# Java
sonar-scanner
spotbugs src/
```

### Code Metrics

Use scripts/code-metrics.py:
```bash
python scripts/code-metrics.py --path src/ --format json
```

**Key metrics to watch:**
- Cyclomatic complexity (keep < 10)
- Cognitive complexity (keep < 15)
- Lines per function (keep < 50)
- Code duplication (keep < 3%)
- Dependency coupling (limit fan-in/fan-out)

## Refactoring Patterns

### When to Refactor

**Green light:**
- Preparing to add a feature (make change easy, then make easy change)
- Code review feedback
- Understanding code while fixing a bug

**Yellow light:**
- Dedicated refactoring sprints (coordinate with team)

**Red light:**
- Before a release deadline
- Without tests covering the area
- When requirements are unstable

### Refactoring Techniques

#### 1. Composing Methods
- **Extract Method**: Move code block to new method
- **Inline Method**: Replace method call with body (opposite)
- **Replace Temp with Query**: Convert variable to method

#### 2. Moving Features
- **Move Method**: Relocate method to appropriate class
- **Move Field**: Relocate field to appropriate class
- **Extract Class**: Split large class into smaller ones

#### 3. Organizing Data
- **Replace Primitive with Object**: Wrap primitives in domain types
- **Replace Type Code with Subclasses**: Use polymorphism
- **Introduce Parameter Object**: Group related parameters

#### 4. Simplifying Conditionals
- **Decompose Conditional**: Extract complex conditions
- **Consolidate Conditional Expression**: Merge duplicate conditions
- **Replace Conditional with Polymorphism**: Strategy pattern

Reference [refactoring-catalog.md](references/refactoring-catalog.md) for 60+ patterns.

### Safe Refactoring Steps

1. **Ensure tests exist** (add characterization tests if needed)
2. **Make small changes** (one refactoring at a time)
3. **Run tests after each change**
4. **Commit frequently** (after each green test run)
5. **Verify no behavior changes** (tests pass, no diff in outputs)

## Code Smells Catalog

### Bloaters (Too Large)
- **Long Method**: > 50 lines
- **Large Class**: > 300 lines
- **Primitive Obsession**: Using primitives instead of domain types
- **Long Parameter List**: > 4 parameters

### Tool Abusers (Wrong Patterns)
- **Switch Statements**: Missed polymorphism opportunity
- **Temporary Field**: Field only used in some circumstances
- **Refused Bequest**: Subclass doesn't use parent behavior
- **Alternative Classes**: Different interfaces, same functionality

### Change Preventers
- **Divergent Change**: One class changes for many reasons
- **Shotgun Surgery**: One change requires many class edits
- **Parallel Inheritance**: New subclass requires another

### Dispensables
- **Duplicate Code**: Copy-paste programming
- **Lazy Class**: Class doing too little
- **Data Class**: Class with only fields and getters/setters
- **Dead Code**: Unused methods/variables

### Couplers
- **Feature Envy**: Method more interested in other class
- **Inappropriate Intimacy**: Classes too tightly coupled
- **Message Chains**: `a.getB().getC().doSomething()`
- **Middle Man**: Class only delegates to another

Reference [code-smells.md](references/code-smells.md) for detection and remedies.

## Legacy Code Strategies

### Characterization Tests

Before refactoring untested code:

```python
def test_characterization_current_behavior():
    """Document existing behavior before changes."""
    result = legacy_function(input_data)
    # Run once, record output, verify it doesn't change
    assert result == expected_output  # From observation
```

### Seam Identification

Find places to inject testability:
- Constructor injection points
- Method overrides for testing
- Configuration hooks
- Environment variable checks

### Incremental Improvement

1. Add characterization tests
2. Extract seams for testability
3. Refactor small sections
4. Verify no regression
5. Repeat

See [legacy-refactoring.md](references/legacy-refactoring.md).

## Review Automation

### Automated Review Comments

Use scripts/auto-review.py:
```bash
python scripts/auto-review.py \
  --pr 123 \
  --rules rules/review-rules.yaml
```

Rules can flag:
- Security issues (secrets, SQL injection risks)
- Performance issues (N+1 queries, unnecessary allocations)
- Style violations (inconsistent naming, formatting)
- Architecture violations (circular dependencies)

### Review Templates

```markdown
## Summary
Brief description of changes

## Changes
- [ ] Feature implementation
- [ ] Bug fix
- [ ] Refactoring
- [ ] Documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] No breaking changes (or documented)
- [ ] Documentation updated
- [ ] Security considerations addressed
```

## Resources

- [refactoring-catalog.md](references/refactoring-catalog.md) - 60+ refactoring patterns
- [code-smells.md](references/code-smells.md) - Code smell detection
- [legacy-refactoring.md](references/legacy-refactoring.md) - Working with untested code
