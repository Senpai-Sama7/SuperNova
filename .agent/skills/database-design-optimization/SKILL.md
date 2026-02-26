---
name: database-design-optimization
description: Database schema design, query optimization, indexing strategies, and data modeling for relational and NoSQL databases. Use when designing database schemas, optimizing slow queries, choosing between database types, implementing migrations, tuning performance, or scaling data layers.
---

# Database Design & Optimization

Building efficient, scalable data layers.

## Database Selection

### When to Use Which

| Database Type | Best For | Examples |
|--------------|----------|----------|
| **PostgreSQL** | General purpose, complex queries, ACID | Applications, analytics |
| **MySQL** | Web applications, read-heavy | CMS, e-commerce |
| **MongoDB** | Flexible schema, document storage | Content management, catalogs |
| **Redis** | Caching, sessions, real-time | Caching, leaderboards |
| **Elasticsearch** | Search, log analytics | Search, monitoring |
| **Cassandra** | Write-heavy, time-series | IoT, messaging |
| **Neo4j** | Graph relationships | Recommendation engines |

## Schema Design

### Normalization vs Denormalization

**Normalize when:**
- Data integrity is critical
- Write-heavy workloads
- Frequent updates to shared data

**Denormalize when:**
- Read performance is critical
- Complex joins are too slow
- Data changes infrequently

### Primary Key Design

```sql
-- Auto-increment (simple, but limits scale)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- UUID (distributed-safe, but larger)
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- ULID (sortable, distributed-safe)
CREATE TABLE events (
    id ULID PRIMARY KEY,  -- Contains timestamp
    data JSONB
);
```

### Foreign Keys and Constraints

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    total DECIMAL(10,2) NOT NULL CHECK (total >= 0),
    status VARCHAR(20) NOT NULL 
        CHECK (status IN ('pending', 'paid', 'shipped', 'delivered')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE RESTRICT  -- Prevent deleting users with orders
);

-- Indexes for FK columns
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

## Indexing Strategy

### Index Types

| Type | Use Case | Query Pattern |
|------|----------|---------------|
| B-tree | Equality, range | `=`, `<`, `>`, `BETWEEN` |
| Hash | Exact match only | `=` (no range) |
| GiST | Geospatial, full-text | Geometric operators |
| GIN | Array, JSONB | `@>`, `?`, `?&` |
| BRIN | Large, ordered data | Time-series, sequential |

### Index Best Practices

```sql
-- Single column for high-cardinality filters
CREATE INDEX idx_users_email ON users(email);

-- Composite for multi-column filters (order matters!)
CREATE INDEX idx_orders_user_status 
    ON orders(user_id, status) 
    WHERE status != 'archived';  -- Partial index

-- Covering index (includes all queried columns)
CREATE INDEX idx_orders_covering 
    ON orders(user_id, status, total, created_at);

-- Expression index for computed values
CREATE INDEX idx_users_lower_email 
    ON users(LOWER(email));
```

**Column order in composite indexes:**
1. Equality filters first (`=`)
2. Range filters second (`<`, `>`, `BETWEEN`)
3. Low cardinality columns last

Use scripts/index-analyzer.py:
```bash
python scripts/index-analyzer.py \
  --database-url $DATABASE_URL \
  --queries queries.log \
  --recommendations
```

## Query Optimization

### EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC
LIMIT 10;
```

**Key metrics:**
- **Seq Scan**: Table scan (bad for large tables)
- **Index Scan**: Index lookup (good)
- **Bitmap Heap Scan**: Multiple index lookups
- **Nested Loop**: Join strategy
- **Cost**: Estimated work (arbitrary units)
- **Actual time**: Real execution time
- **Buffers**: Disk I/O (high = slow)

### Common Optimizations

**N+1 Query Problem:**
```python
# Bad: N+1 queries
for user in users:
    orders = session.query(Order).filter_by(user_id=user.id).all()

# Good: Single query with join
users_with_orders = session.query(User).options(
    joinedload(User.orders)
).all()
```

**Pagination:**
```sql
-- Bad for large offsets
SELECT * FROM orders 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 100000;

-- Good: Keyset pagination
SELECT * FROM orders 
WHERE created_at < $last_seen_date 
ORDER BY created_at DESC 
LIMIT 20;
```

**SELECT only needed columns:**
```sql
-- Bad
SELECT * FROM users WHERE id = 1;

-- Good
SELECT id, email, name FROM users WHERE id = 1;
```

## Transaction Design

### ACID Properties

**Atomicity**: All or nothing
**Consistency**: Valid state to valid state
**Isolation**: Concurrent transactions don't interfere
**Durability**: Committed data survives failures

### Isolation Levels

```sql
-- Read Committed (default, usually best)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Repeatable Read (prevents non-repeatable reads)
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Serializable (strictest, slowest)
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

### Transaction Patterns

```python
# Optimistic locking
@app.route('/update-inventory', methods=['POST'])
def update_inventory():
    with db.transaction():
        item = Item.query.with_for_update().get(item_id)
        if item.quantity < requested:
            raise InsufficientInventory()
        item.quantity -= requested
        db.session.commit()

# Pessimistic locking (for high contention)
with db.transaction():
    account = Account.query.with_for_update().get(account_id)
    account.balance -= amount
    db.session.commit()
```

## Migration Strategy

### Migration Principles

1. **Backward compatible**: Old code works with new schema
2. **Reversible**: Can rollback if issues
3. **Idempotent**: Safe to run multiple times
4. **Tested**: Verify in staging

### Zero-Downtime Migrations

**Adding a column:**
```sql
-- Step 1: Add nullable column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Step 2: Deploy code to write to both old and new
-- Step 3: Backfill data
UPDATE users SET phone = old_phone WHERE phone IS NULL;

-- Step 4: Make column NOT NULL (after all data migrated)
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- Step 5: Remove old column
ALTER TABLE users DROP COLUMN old_phone;
```

**Renaming a column:**
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN email_address VARCHAR(255);

-- Step 2: Create trigger to sync
CREATE TRIGGER sync_email 
    BEFORE UPDATE ON users
    FOR EACH ROW
    BEGIN
        NEW.email_address = NEW.email;
    END;

-- Step 3: Backfill
UPDATE users SET email_address = email;

-- Step 4: Deploy code using new column
-- Step 5: Drop old column and trigger
```

Use scripts/migration-validator.py:
```bash
python scripts/migration-validator.py \
  --migration migrations/001_add_user_column.sql \
  --check-backward-compatible
```

## Scaling Strategies

### Read Replicas

```python
# Separate read and write connections
write_db = connect_to_primary()
read_db = connect_to_replica()

# Writes go to primary
def create_user(data):
    return write_db.execute("INSERT INTO users ...")

# Reads go to replica
def get_user(user_id):
    return read_db.execute("SELECT * FROM users WHERE id = %s", user_id)
```

### Sharding

```python
# Consistent hashing for shard selection
def get_shard(user_id):
    return hash(user_id) % NUM_SHARDS

def get_user(user_id):
    shard = get_shard(user_id)
    db = shard_connections[shard]
    return db.query(User).get(user_id)
```

### Caching Layer

```python
# Cache frequently accessed data
def get_user(user_id):
    # Try cache first
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Fall back to database
    user = db.query(User).get(user_id)
    if user:
        redis.setex(f"user:{user_id}", 3600, json.dumps(user.to_dict()))
    
    return user
```

## NoSQL Patterns

### Document Design (MongoDB)

```javascript
// Embedded vs Reference decision tree
// Embed when:
// - Data is read together
// - Data doesn't grow unbounded
// - No need for independent queries

// User with embedded addresses (limited, accessed together)
{
    _id: ObjectId(),
    name: "John",
    addresses: [
        { street: "123 Main", city: "NYC", default: true },
        { street: "456 Oak", city: "LA" }
    ]
}

// Orders with reference to users (many, queried independently)
{
    _id: ObjectId(),
    user_id: ObjectId("..."),
    items: [...],
    total: 99.99
}
```

### Time-Series (TimescaleDB)

```sql
-- Hypertable for time-series data
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id TEXT NOT NULL,
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION
);

SELECT create_hypertable('metrics', 'time');

-- Automatic partitioning by time
-- Efficient recent queries, compressed old data
```

## Monitoring and Maintenance

### Query Performance Monitoring

```sql
-- Find slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table bloat detection
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Maintenance Tasks

```bash
# Vacuum and analyze
VACUUM ANALYZE;

# Reindex
REINDEX TABLE users;

# Update statistics
ANALYZE VERBOSE;
```

Use scripts/query-analyzer.py:
```bash
python scripts/query-analyzer.py \
  --slow-query-log /var/log/postgresql/slow.log \
  --threshold 1000 \
  --report report.html
```

## Resources

- [schema-patterns.md](references/schema-patterns.md) - Common schema designs
- [query-optimization.md](references/query-optimization.md) - Advanced optimization
- [scaling-strategies.md](references/scaling-strategies.md) - Database scaling
