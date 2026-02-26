# Testing Patterns Reference

## Test Doubles

### Stub
Returns canned answers. No behavior.

```python
class EmailServiceStub:
    def __init__(self):
        self.sent_emails = []
    
    def send(self, to, subject, body):
        self.sent_emails.append({"to": to, "subject": subject})
        return True

def test_order_confirmation():
    email_stub = EmailServiceStub()
    service = OrderService(email_stub)
    
    service.create_order(user_id="123", items=[...])
    
    assert len(email_stub.sent_emails) == 1
    assert email_stub.sent_emails[0]["to"] == "user@example.com"
```

### Mock
Verifies behavior (method calls).

```python
from unittest.mock import Mock

def test_payment_processing():
    payment_gateway = Mock()
    payment_gateway.charge.return_value = {"status": "approved"}
    
    service = PaymentService(payment_gateway)
    service.process_payment(amount=100)
    
    payment_gateway.charge.assert_called_once_with(
        amount=100,
        currency="USD"
    )
```

### Fake
Working implementation, but simplified.

```python
class InMemoryUserRepository:
    """Fake: No real database, but behaves correctly."""
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    def save(self, user):
        user.id = self.next_id
        self.users[user.id] = user
        self.next_id += 1
        return user
    
    def find_by_id(self, user_id):
        return self.users.get(user_id)
    
    def find_by_email(self, email):
        for user in self.users.values():
            if user.email == email:
                return user
        return None
```

### Spy
Records interactions for later verification.

```python
class AuditLoggerSpy:
    def __init__(self):
        self.logged_events = []
    
    def log(self, event, user_id, data):
        self.logged_events.append({
            "event": event,
            "user_id": user_id,
            "data": data
        })

def test_audit_logging():
    logger = AuditLoggerSpy()
    service = UserService(logger=logger)
    
    service.delete_user(user_id="123")
    
    assert any(
        e["event"] == "user_deleted" and e["user_id"] == "123"
        for e in logger.logged_events
    )
```

## Test Patterns

### Arrange-Act-Assert (AAA)

```python
def test_withdraw_sufficient_funds():
    # Arrange
    account = Account(balance=100)
    
    # Act
    account.withdraw(70)
    
    # Assert
    assert account.balance == 30
```

### Given-When-Then (BDD Style)

```python
def test_withdraw_insufficient_funds():
    # Given an account with $50
    account = Account(balance=50)
    
    # When the user tries to withdraw $100
    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(100)
    
    # Then an error is raised
    assert exc_info.value.amount_needed == 50
```

### Builder Pattern for Test Data

```python
class UserBuilder:
    def __init__(self):
        self.email = "test@example.com"
        self.name = "Test User"
        self.verified = True
    
    def with_email(self, email):
        self.email = email
        return self
    
    def unverified(self):
        self.verified = False
        return self
    
    def build(self):
        return User(email=self.email, name=self.name, verified=self.verified)

def test_unverified_user_cannot_order():
    user = UserBuilder().unverified().build()
    # ... test logic
```

### Table-Driven Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("WORLD", "WORLD"),
    ("", ""),
    ("123", "123"),
])
def test_to_uppercase(input, expected):
    assert to_uppercase(input) == expected
```

### Contract Tests

Verify interface contracts between services:

```python
def test_payment_gateway_contract():
    """This test runs against both stub and real implementation."""
    implementations = [
        PaymentGatewayStub(),
        PaymentGatewayReal(api_key=TEST_KEY)
    ]
    
    for gateway in implementations:
        # Contract: charge returns dict with transaction_id
        result = gateway.charge(amount=10.00, currency="USD")
        assert "transaction_id" in result
        assert isinstance(result["transaction_id"], str)
        
        # Contract: declined cards raise DeclinedError
        with pytest.raises(DeclinedError):
            gateway.charge(amount=999999.00, currency="USD")  # Test decline
```

## Async Testing

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_operation():
    result = await async_service.fetch_data()
    assert result is not None

@pytest.mark.asyncio
async def test_async_with_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            slow_operation(),
            timeout=0.1
        )

@pytest.mark.asyncio
async def test_async_mock():
    mock_service = AsyncMock()
    mock_service.fetch_data.return_value = {"key": "value"}
    
    result = await mock_service.fetch_data()
    assert result["key"] == "value"
```

## Snapshot Testing

```python
import pytest

def test_api_response_format(snapshot):
    response = api.get_user(user_id="123")
    assert response == snapshot
    # First run saves snapshot, subsequent runs compare

def test_html_output(snapshot):
    html = renderer.render(component)
    assert html == snapshot
```

## Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(lst):
    """Sorting doesn't change list length."""
    assert len(sorted(lst)) == len(lst)

@given(st.text(), st.text())
def test_concatenation_length(s1, s2):
    """Length of concatenation is sum of lengths."""
    assert len(s1 + s2) == len(s1) + len(s2)

@given(st.dictionaries(st.text(), st.integers()))
def test_json_roundtrip(data):
    """JSON serialization is reversible."""
    import json
    assert json.loads(json.dumps(data)) == data
```

## Database Testing

```python
@pytest.fixture
db_session():
    # Create test database
    engine = create_engine(TEST_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.rollback()
    session.close()

def test_user_repository(db_session):
    repo = UserRepository(db_session)
    
    user = User(email="test@example.com")
    saved = repo.save(user)
    
    found = repo.find_by_id(saved.id)
    assert found.email == "test@example.com"
```

## Web API Testing

```python
def test_create_user(client):
    response = client.post("/api/users", json={
        "email": "test@example.com",
        "name": "Test User"
    })
    
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()
    assert "password" not in response.json()  # Security check

def test_get_user_not_found(client):
    response = client.get("/api/users/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"
```
