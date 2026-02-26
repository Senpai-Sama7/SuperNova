# Common Failure Patterns

## Logic Errors

### Off-by-One Errors
```python
# Wrong
for i in range(len(items)):
    if i == len(items):  # Never true
        process_last(items[i])

# Right
for i in range(len(items)):
    if i == len(items) - 1:
        process_last(items[i])
```

### Null/None Handling
```python
# Wrong
user_name = user.get_profile().name  # May throw if no profile

# Right
profile = user.get_profile()
user_name = profile.name if profile else None
```

### Floating Point Precision
```python
# Wrong
if (a + b) == 0.3:  # May be 0.29999999999999999
    pass

# Right
if abs((a + b) - 0.3) < 1e-9:
    pass
```

## Concurrency Issues

### Race Conditions
```python
# Thread-unsafe
counter = 0

def increment():
    counter += 1  # Read-Modify-Write race

# Thread-safe
from threading import Lock
lock = Lock()

def increment_safe():
    with lock:
        counter += 1
```

### Deadlocks
```
Thread A: Lock X → waiting for Lock Y
Thread B: Lock Y → waiting for Lock X
```

**Prevention:**
- Lock ordering (always X then Y)
- Try-lock with timeout
- Avoid holding multiple locks

### Starvation
- Low-priority threads never get resources
- Solution: Fair locks, priority inheritance

## Resource Issues

### Memory Leaks

**Python:**
```python
# Leak: Circular reference with __del__
class Node:
    def __init__(self):
        self.parent = None
        self.children = []
    
    def __del__(self):
        print("Cleaning up")  # Prevents GC

# Fix: Use weakref
import weakref
self.parent = weakref.ref(parent)
```

**JavaScript:**
```javascript
// Leak: Event listener not removed
element.addEventListener('click', handler);
// Forgot: element.removeEventListener('click', handler);

// Leak: Closure capturing large scope
function process() {
    const hugeData = loadHugeData();
    return function() {
        return hugeData.id;  // Keeps all of hugeData in memory
    };
}
```

### Connection Pool Exhaustion
```python
# Wrong: Not returning connection
def get_data():
    conn = pool.get_connection()
    return conn.query("SELECT * FROM data")
    # Connection never returned!

# Right: Context manager
def get_data():
    with pool.get_connection() as conn:
        return conn.query("SELECT * FROM data")
```

### File Descriptor Leaks
```python
# Wrong
file = open('data.txt')
data = file.read()
# Forgot to close!

# Right
with open('data.txt') as file:
    data = file.read()
```

## Integration Failures

### Timeout Cascades
```
Service A (timeout: 30s)
  → Service B (timeout: 30s)
    → Service C (timeout: 30s)
      → Slow Database

Total wait: 90s before failure!
```

**Fix:** Decreasing timeout chain: 30s → 10s → 5s

### Circuit Breaker Not Tripping
```python
# Wrong: No circuit breaker
result = requests.get('http://unhealthy-service')

# Right: Circuit breaker pattern
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
def call_service():
    return requests.get('http://unhealthy-service')
```

### API Version Mismatch
```
Client expects: {"user_id": "123", "name": "John"}
Server returns: {"id": "123", "full_name": "John"}

Result: AttributeError or undefined behavior
```

## Configuration Issues

### Environment-Specific Bugs
```python
# Works locally, fails in prod
if os.environ.get('DEBUG'):  # Truthy check
    enable_debug_mode()

# Prod has DEBUG=False (string), which is truthy!
```

### Feature Flag Drift
```python
# Feature flag enabled for months
if feature_flags.is_enabled('new_checkout'):
    new_checkout()
else:
    old_checkout()  # Untested, may be broken
```

### Default Value Changes
```python
# Library update changes default
requests.get(url, timeout=30)  # Was infinite in old version
```

## Data Issues

### Encoding Problems
```python
# UnicodeDecodeError
with open('file.txt', 'r') as f:  # Default encoding varies by OS
    content = f.read()

# Explicit encoding
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()
```

### Timezone Assumptions
```python
# Wrong: Naive datetime
created_at = datetime.now()  # Local time

# Right: UTC
created_at = datetime.now(timezone.utc)
```

### Schema Migration Failures
- Adding NOT NULL column without default
- Renaming column used by old code
- Dropping column still referenced
- Index creation locking table

## Security-Related Failures

### Authentication Bypass
```python
# Wrong: Timing attack vulnerable
if user.password == input_password:
    login()

# Right: Constant-time comparison
import hmac
if hmac.compare_digest(user.password, hash(input_password)):
    login()
```

### Rate Limiting Bypass
- Client retries with different IPs
- Distributed attack from many sources
- Cache bypassing unique query params

## Performance Degradation Patterns

### N+1 Query
```python
# Wrong: N+1
users = db.query("SELECT * FROM users")
for user in users:
    orders = db.query(f"SELECT * FROM orders WHERE user_id = {user['id']}")

# Right: Join
users_with_orders = db.query("""
    SELECT u.*, o.* 
    FROM users u 
    LEFT JOIN orders o ON u.id = o.user_id
""")
```

### Cache Stampede
```
T0: Cache expires
T1: 1000 requests arrive simultaneously
T2: All 1000 hit database
T3: Cache repopulated 1000 times
```

**Fix:** Cache warming, probabilistic early expiration, mutex

### Thundering Herd
Similar to cache stampede but for any shared resource (locks, connections).
