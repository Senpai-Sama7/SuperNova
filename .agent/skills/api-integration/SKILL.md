---
name: api-integration
description: REST API design, GraphQL implementation, gRPC services, authentication flows, and third-party API integration patterns. Use when designing APIs, consuming external services, handling authentication, implementing rate limiting, managing API versioning, or debugging integration issues.
---

# API Integration

Building and consuming robust APIs.

## API Design Principles

### RESTful Design

**Resources, not actions:**
```
GET    /users          # List users
GET    /users/{id}     # Get specific user
POST   /users          # Create user
PUT    /users/{id}     # Update user (full)
PATCH  /users/{id}     # Update user (partial)
DELETE /users/{id}     # Delete user
```

**Nesting for relationships:**
```
GET /users/{id}/orders       # User's orders
GET /users/{id}/orders/{oid} # Specific order
```

### Response Format

```json
{
  "data": {
    "id": "user-123",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-abc-123"
  }
}
```

### Error Responses

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "req-abc-123"
  }
}
```

**HTTP Status Codes:**
- 200 OK - Success
- 201 Created - Resource created
- 204 No Content - Success, no body
- 400 Bad Request - Client error
- 401 Unauthorized - Authentication required
- 403 Forbidden - No permission
- 404 Not Found - Resource doesn't exist
- 409 Conflict - Resource state conflict
- 422 Unprocessable - Validation failed
- 429 Too Many Requests - Rate limited
- 500 Server Error - Unexpected error
- 503 Service Unavailable - Temporarily down

## GraphQL

### Schema Design

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  orders: [Order!]!
  createdAt: DateTime!
}

type Order {
  id: ID!
  user: User!
  items: [OrderItem!]!
  total: Float!
  status: OrderStatus!
}

type Query {
  user(id: ID!): User
  users(limit: Int = 20, offset: Int = 0): [User!]!
  orders(
    userId: ID
    status: OrderStatus
    limit: Int = 20
  ): [Order!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
}

enum OrderStatus {
  PENDING
  PAID
  SHIPPED
  DELIVERED
}
```

### Resolver Implementation

```python
from ariadne import QueryType

query = QueryType()

@query.field("user")
async def resolve_user(_, info, id):
    # DataLoader batching
    return await info.context["user_loader"].load(id)

@query.field("users")
async def resolve_users(_, info, limit=20, offset=0):
    # Authorization check
    if not info.context["user"].can_list_users():
        raise PermissionDenied()
    
    return await UserService.list_users(limit=limit, offset=offset)
```

### N+1 Prevention (DataLoader)

```python
from aiographql_dataloader import DataLoader

class UserLoader(DataLoader):
    async def batch_load_fn(self, keys):
        users = await User.query.where(User.id.in_(keys)).gino.all()
        user_map = {u.id: u for u in users}
        return [user_map.get(k) for k in keys]

# Usage in resolvers
user = await context.user_loader.load(user_id)
```

## gRPC

### Service Definition

```protobuf
syntax = "proto3";

service PaymentService {
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse);
  rpc StreamTransactions (StreamRequest) returns (stream Transaction);
}

message PaymentRequest {
  string user_id = 1;
  double amount = 2;
  string currency = 3;
  string payment_method = 4;
}

message PaymentResponse {
  string transaction_id = 1;
  Status status = 2;
  
  enum Status {
    PENDING = 0;
    APPROVED = 1;
    DECLINED = 2;
  }
}
```

### Client Implementation

```python
import grpc
from payment_pb2 import PaymentRequest
from payment_pb2_grpc import PaymentServiceStub

channel = grpc.secure_channel('payments.api.com:443', 
                              grpc.ssl_channel_credentials())
stub = PaymentServiceStub(channel)

request = PaymentRequest(
    user_id="user-123",
    amount=99.99,
    currency="USD",
    payment_method="card"
)

try:
    response = stub.ProcessPayment(request, timeout=10)
    print(f"Transaction: {response.transaction_id}")
except grpc.RpcError as e:
    print(f"Error: {e.code()} - {e.details()}")
```

## Authentication Patterns

### OAuth 2.0 Flows

**Authorization Code (web apps):**
```
User ──→ Client ──→ Authorization Server ──→ Client
         └─ Code ─┘
         └──── Access Token ────┘
```

**Client Credentials (service-to-service):**
```python
import requests

response = requests.post(
    "https://auth.server.com/oauth/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": "api://my-api"
    }
)
token = response.json()["access_token"]
```

**JWT Validation:**
```python
import jwt
from jwt.exceptions import InvalidTokenError

def validate_token(token):
    try:
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience="my-api",
            issuer="auth-server"
        )
        return payload
    except InvalidTokenError as e:
        raise AuthenticationError(str(e))
```

### API Keys

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/data", dependencies=[Security(verify_api_key)])
async def get_data():
    return {"data": "sensitive"}
```

## Resilience Patterns

### Retry with Exponential Backoff

```python
import backoff
import requests

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException,),
    max_tries=5,
    giveup=lambda e: e.response is not None and e.response.status_code < 500
)
def call_external_api():
    return requests.get("https://api.example.com/data", timeout=30)
```

### Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
def call_payment_api(data):
    return requests.post("https://payments.api.com/charge", json=data)

# After 5 failures, circuit opens
# All calls fail fast until 30s recovery
```

### Timeout and Cancellation

```python
import asyncio

async def call_with_timeout():
    try:
        async with asyncio.timeout(10):
            return await external_api.call()
    except asyncio.TimeoutError:
        # Handle timeout
        raise ServiceUnavailable()
```

## Rate Limiting

### Client-Side Rate Limiting

```python
import time
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=60)  # 100 calls per minute
def call_api():
    return requests.get("https://api.example.com/data")
```

### Token Bucket (Server-Side)

```python
import redis

class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        pipe = self.redis.pipeline()
        now = time.time()
        
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        
        _, current_count, _, _ = pipe.execute()
        
        return current_count < limit
```

## API Versioning

### URL Versioning

```
/api/v1/users
/api/v2/users
```

### Header Versioning

```
Accept: application/vnd.api+json;version=2
```

### Deprecation Strategy

```http
HTTP/1.1 200 OK
Deprecation: Sun, 01 Jun 2024 00:00:00 GMT
Sunset: Sun, 01 Dec 2024 00:00:00 GMT
Link: </api/v2/users>; rel="successor-version"
```

## Webhooks

### Implementation

```python
import hmac
import hashlib

@app.post("/webhooks/payments")
async def handle_webhook(request: Request):
    # Verify signature
    signature = request.headers.get("X-Webhook-Signature")
    payload = await request.body()
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Invalid signature")
    
    # Process webhook
    data = await request.json()
    await process_webhook_event(data)
    
    return {"status": "processed"}
```

### Webhook Delivery

```python
async def send_webhook(url: str, event: dict, secret: str):
    payload = json.dumps(event)
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Event-Type": event["type"]
            },
            timeout=30
        )
    
    return response.status_code == 200
```

## Testing APIs

### Contract Testing

```python
import requests

def test_api_contract():
    """Verify API matches expected contract."""
    response = requests.get("/api/users/1")
    
    # Schema validation
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert isinstance(data["id"], str)
    
    # Response time SLA
    assert response.elapsed.total_seconds() < 0.5
```

Use scripts/api-test-generator.py:
```bash
python scripts/api-test-generator.py \
  --spec openapi.yaml \
  --output tests/api/
```

## Resources

- [rest-patterns.md](references/rest-patterns.md) - REST design patterns
- [graphql-patterns.md](references/graphql-patterns.md) - GraphQL best practices
- [auth-patterns.md](references/auth-patterns.md) - Authentication flows
