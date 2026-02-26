---
name: test-driven-development
description: Comprehensive test-driven development including unit, integration, and end-to-end testing strategies. Use when writing tests for new features, refactoring legacy code, designing testable architectures, improving code coverage, debugging through tests, or establishing testing standards for a project.
---

# Test-Driven Development

Systematic approach to writing tests that drive design and ensure correctness.

## TDD Cycle

1. **Red**: Write a failing test that defines desired behavior
2. **Green**: Write minimal code to pass the test
3. **Refactor**: Improve code quality while keeping tests green
4. **Repeat**: Next behavior, next test

## Test Pyramid Strategy

Balance your test suite:

```
      /\
     /  \
    / E2E \        (Few, slow, high confidence)
   /--------\
  / Integration \  (Medium, medium speed)
 /--------------\
/     Unit       \ (Many, fast, targeted)
------------------
```

**Guidelines:**
- Unit tests: 70-80% of suite, <10ms each, no I/O
- Integration tests: 15-25% of suite, test component interactions
- E2E tests: 5-10% of suite, critical user journeys only

## Unit Testing Principles

### FIRST Properties

Tests should be:
- **Fast**: Run in milliseconds
- **Isolated**: No shared state between tests
- **Repeatable**: Same result every time
- **Self-validating**: Boolean pass/fail, no manual inspection
- **Timely**: Written with production code

### Test Structure (Arrange-Act-Assert)

```python
def test_user_can_withdraw_funds():
    # Arrange
    account = Account(balance=100)
    
    # Act
    account.withdraw(30)
    
    # Assert
    assert account.balance == 70
```

### What to Test

Focus on:
- **Happy paths**: Normal operation scenarios
- **Edge cases**: Boundaries, empty inputs, maximum values
- **Error cases**: Exceptions, failures, invalid inputs
- **State transitions**: Before/after conditions

Avoid:
- Testing implementation details (private methods)
- Testing third-party libraries
- Duplicate coverage across test levels

Reference [testing-patterns.md](references/testing-patterns.md) for comprehensive patterns.

## Integration Testing

### Scope Decisions

Test at these boundaries:
- Database layer (repository tests)
- External APIs (with mocking/stubbing)
- Message queues (produce/consume cycles)
- File system operations

### Test Database Strategy

1. Use separate test database (in-memory or ephemeral)
2. Reset state between tests (transactions or cleanup)
3. Seed with minimal test data
4. Avoid sharing test data between tests

### External Service Mocking

```python
# Use contracts, not implementation details
@responses.activate
def test_payment_gateway_integration():
    responses.add(
        responses.POST,
        "https://api.payment.com/charge",
        json={"status": "approved", "id": "txn_123"},
        status=200
    )
    
    result = payment_service.charge(100.00)
    
    assert result.approved is True
    assert result.transaction_id == "txn_123"
```

## Test Data Management

### Fixtures and Factories

Use scripts/test-data-generator.py:
```bash
python scripts/test-data-generator.py \
  --schema models/user.yaml \
  --count 100 \
  --output tests/fixtures/users.json
```

**Factory pattern benefits:**
- Centralized test data creation
- Sensible defaults with override capability
- Reduced test boilerplate

Reference [test-data-patterns.md](references/test-data-patterns.md).

## Advanced Testing Techniques

### Property-Based Testing

Generate test cases automatically:

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a
```

### Mutation Testing

Verify test quality by introducing bugs:
```bash
python scripts/mutation-test.py --src src/ --tests tests/
```

Target: >80% mutation score (tests catch artificial bugs).

### Contract Testing

Verify API contracts between services:
```bash
# Consumer generates contract
python scripts/contract-test.py --mode consumer --spec api-schema.yaml

# Provider verifies against contract
python scripts/contract-test.py --mode provider --contract consumer-contract.json
```

## Coverage Strategy

**Meaningful coverage targets:**
- Line coverage: 80% minimum
- Branch coverage: 70% minimum
- Critical paths: 100% coverage

Use scripts/coverage-analyzer.py:
```bash
python scripts/coverage-analyzer.py \
  --report coverage.xml \
  --critical-paths "src/auth/*,src/payments/*"
```

**Coverage anti-patterns:**
- Testing getters/setters just for coverage
- Ignoring uncovered critical logic
- Treating coverage as a goal, not a tool

## Language-Specific Testing

Reference [language-testing-guides.md](references/language-testing-guides.md):

- **Python**: pytest, unittest, hypothesis, factory_boy
- **JavaScript**: Jest, Vitest, Cypress, Playwright
- **Java**: JUnit, TestNG, Mockito, Spring Test
- **Go**: testing, testify, gomock
- **Rust**: built-in test framework, proptest

## Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_models.py
│   └── test_services.py
├── integration/             # Component interaction tests
│   ├── test_database.py
│   └── test_external_apis.py
├── e2e/                     # Full workflow tests
│   └── test_user_journey.py
├── fixtures/                # Test data
│   └── users.yaml
└── conftest.py             # Shared fixtures
```

## CI/CD Integration

**Pre-commit:**
```bash
# Run fast tests first
pytest tests/unit/ -x --tb=short
```

**Pull request:**
```bash
# Full test suite
pytest tests/ --cov=src --cov-report=xml
```

**Main branch:**
```bash
# Full suite + mutation testing
pytest tests/
python scripts/mutation-test.py --fail-under=80
```

## Resources

- [testing-patterns.md](references/testing-patterns.md) - Comprehensive test patterns
- [test-data-patterns.md](references/test-data-patterns.md) - Test data management
- [language-testing-guides.md](references/language-testing-guides.md) - Language specifics
