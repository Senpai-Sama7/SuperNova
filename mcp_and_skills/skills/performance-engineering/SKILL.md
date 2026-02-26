---
name: performance-engineering
description: Performance profiling, optimization strategies, caching patterns, and scalability techniques for high-performance software systems. Use when optimizing slow code, designing for scale, implementing caching, reducing latency, profiling applications, or diagnosing performance bottlenecks.
---

# Performance Engineering

Building fast, scalable, efficient systems.

## Performance Principles

1. **Measure first**: Don't optimize without data
2. **Optimize for the common case**: 80/20 rule
3. **Avoid premature optimization**: Correct then fast
4. **Understand trade-offs**: Speed vs memory vs complexity
5. **Test under load**: Real conditions reveal issues

## Performance Workflow

### 1. Establish Baseline

Measure current performance:
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Resource usage (CPU, memory, I/O)
- Error rates

Use scripts/perf-benchmark.py:
```bash
python scripts/perf-benchmark.py \
  --endpoint http://api/users \
  --duration 60 \
  --concurrency 100 \
  --output baseline.json
```

### 2. Profile to Find Bottlenecks

**CPU Profiling:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = process_data(large_dataset)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Memory Profiling:**
```python
from memory_profiler import profile

@profile
def process_large_file():
    data = load_file('huge.csv')  # Memory spike here
    return analyze(data)
```

Use scripts/profile-analyzer.py:
```bash
# Generate flame graph
python scripts/profile-analyzer.py \
  --command "python app.py" \
  --duration 60 \
  --output profile.svg
```

### 3. Identify Optimization Targets

**Common bottlenecks:**

| Symptom | Likely Cause | Quick Check |
|---------|-------------|-------------|
| High CPU | Algorithm complexity | Profile for hot functions |
| High memory | Memory leaks, large allocations | Memory profile |
| Slow I/O | Blocking operations, N+1 queries | Check for awaits |
| High latency | Network, serialization | Distributed trace |
| Low throughput | Locks, contention | Thread/blocking analysis |

### 4. Implement Optimization

### 5. Verify Improvement

Compare before/after:
```bash
python scripts/perf-compare.py \
  --before baseline.json \
  --after optimized.json \
  --threshold 10  # % improvement required
```

## Algorithm Optimization

### Time Complexity

```python
# O(n²) - Nested loops
def find_duplicates_bad(items):
    for i, x in enumerate(items):
        for j, y in enumerate(items):
            if i != j and x == y:
                return (i, j)

# O(n) - Set lookup
def find_duplicates_good(items):
    seen = {}
    for i, x in enumerate(items):
        if x in seen:
            return (seen[x], i)
        seen[x] = i
```

### Data Structure Selection

| Operation | List | Dict | Set | Deque |
|-----------|------|------|-----|-------|
| Access by index | O(1) | - | - | O(1) |
| Search | O(n) | O(1) | O(1) | O(n) |
| Insert/Delete end | O(1) | O(1) | O(1) | O(1) |
| Insert/Delete middle | O(n) | O(1) | O(1) | O(n) |

## Caching Strategies

### Cache Levels

```
CPU Cache (L1/L2) → Memory Cache (Redis) → Disk Cache → Source
      <1ms              1-5ms                10-100ms     Variable
```

### Cache Patterns

**Cache-Aside (Lazy Loading):**
```python
async def get_user(user_id):
    # Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Load from DB
    user = await db.fetch_one("SELECT * FROM users WHERE id = :id", {"id": user_id})
    
    # Populate cache
    if user:
        await redis.setex(f"user:{user_id}", 3600, json.dumps(dict(user)))
    
    return user
```

**Write-Through:**
```python
async def update_user(user_id, data):
    # Update DB
    await db.execute("UPDATE users SET ... WHERE id = :id", {"id": user_id, **data})
    
    # Update cache
    await redis.setex(f"user:{user_id}", 3600, json.dumps(data))
```

**Write-Behind (Async):**
```python
async def update_user(user_id, data):
    # Update cache immediately
    await redis.setex(f"user:{user_id}", 3600, json.dumps(data))
    
    # Queue DB update
    await queue.publish("user_updates", {"user_id": user_id, "data": data})
```

### Cache Invalidation

```python
# Key-based invalidation
async def invalidate_user(user_id):
    await redis.delete(f"user:{user_id}")
    await redis.delete(f"user:{user_id}:orders")

# Pattern-based invalidation
async def invalidate_user_patterns(user_id):
    keys = await redis.keys(f"user:{user_id}:*")
    if keys:
        await redis.delete(*keys)

# TTL-based (simplest, but stale data possible)
await redis.setex(key, 300, value)  # 5 minute TTL
```

### Cache Warming

```python
async def warm_cache():
    """Pre-populate cache on startup."""
    popular_users = await db.fetch_all(
        "SELECT * FROM users ORDER BY last_login DESC LIMIT 1000"
    )
    
    pipe = redis.pipeline()
    for user in popular_users:
        pipe.setex(f"user:{user['id']}", 3600, json.dumps(dict(user)))
    await pipe.execute()
```

## Concurrency & Parallelism

### Async/Await (I/O Bound)

```python
import asyncio
import aiohttp

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_one(session, url):
    async with session.get(url) as response:
        return await response.json()

# Fetch 100 URLs concurrently
results = await fetch_all(urls)
```

### Multiprocessing (CPU Bound)

```python
from multiprocessing import Pool
import numpy as np

def process_chunk(chunk):
    # CPU-intensive work
    return np.fft.fft(chunk)

def parallel_fft(data, num_workers=4):
    chunks = np.array_split(data, num_workers)
    
    with Pool(num_workers) as pool:
        results = pool.map(process_chunk, chunks)
    
    return np.concatenate(results)
```

### Threading (I/O with CPU)

```python
from concurrent.futures import ThreadPoolExecutor
import requests

def download_image(url):
    response = requests.get(url)
    return process_image(response.content)

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(download_image, urls))
```

## Database Optimization

### Query Optimization

See [database-design-optimization](database-design-optimization/) for detailed guidance.

Quick wins:
```sql
-- Add indexes for WHERE clauses
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Covering indexes for common queries
CREATE INDEX idx_orders_covering ON orders(user_id, status, total);

-- Avoid SELECT *
SELECT id, name, email FROM users WHERE id = 1;

-- Use connection pooling
-- Batch inserts
INSERT INTO users (name, email) VALUES 
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com');
```

### Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # Base connections
    max_overflow=20,        # Extra under load
    pool_timeout=30,        # Wait for available
    pool_recycle=3600,      # Recycle after 1 hour
)
```

## Network Optimization

### Compression

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### HTTP/2 & Keep-Alive

```python
import httpx

# HTTP/2 client with connection pooling
client = httpx.AsyncClient(
    http2=True,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)
```

### Request Batching

```python
# Bad: N requests
for user_id in user_ids:
    user = await fetch_user(user_id)

# Good: 1 batch request
users = await fetch_users_batch(user_ids)
```

## Memory Optimization

### Generators for Large Data

```python
# Bad: Loads all into memory
def get_large_dataset():
    return [process(x) for x in range(1000000)]

# Good: Streams data
def get_large_dataset():
    for x in range(1000000):
        yield process(x)

# Usage
for item in get_large_dataset():
    save(item)
```

### Object Pooling

```python
class ConnectionPool:
    def __init__(self, max_size=10):
        self.pool = queue.Queue(maxsize=max_size)
        self.max_size = max_size
    
    def acquire(self):
        try:
            return self.pool.get(block=False)
        except queue.Empty:
            return self.create_connection()
    
    def release(self, conn):
        try:
            self.pool.put(conn, block=False)
        except queue.Full:
            conn.close()
```

## Load Testing

### locust

```python
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def get_user(self):
        self.client.get("/api/users/1")
    
    @task(1)
    def create_order(self):
        self.client.post("/api/orders", json={
            "user_id": "1",
            "items": [{"product_id": "1", "qty": 1}]
        })
```

Run: `locust -f load_test.py --host http://localhost:8000`

Use scripts/load-test-orchestrator.py:
```bash
python scripts/load-test-orchestrator.py \
  --scenario scenarios/api-test.yaml \
  --ramp-up 60 \
  --duration 300 \
  --max-users 1000
```

## Performance Budgets

Define and enforce limits:

```yaml
performance_budgets:
  api_response_time:
    p50: 100ms
    p95: 500ms
    p99: 1000ms
  
  page_load_time:
    first_contentful_paint: 1.5s
    largest_contentful_paint: 2.5s
  
  bundle_size:
    javascript: 200kb
    images: 500kb
```

Use scripts/budget-enforcer.py:
```bash
python scripts/budget-enforcer.py \
  --budget performance-budget.yaml \
  --metrics metrics.json
```

## Resources

- [profiling-guides.md](references/profiling-guides.md) - Language-specific profiling
- [caching-patterns.md](references/caching-patterns.md) - Advanced caching strategies
- [scaling-patterns.md](references/scaling-patterns.md) - Horizontal/vertical scaling
