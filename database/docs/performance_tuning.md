# PostgreSQL Performance Tuning for Q-Learning Database

## Table of Contents

1. [Overview](#overview)
2. [PostgreSQL Configuration](#postgresql-configuration)
3. [Connection Pooling](#connection-pooling)
4. [Indexing Strategy](#indexing-strategy)
5. [Query Optimization](#query-optimization)
6. [Concurrency Control](#concurrency-control)
7. [Monitoring & Observability](#monitoring--observability)
8. [Supabase-Specific Considerations](#supabase-specific-considerations)
9. [Scaling Strategies](#scaling-strategies)

---

## Overview

This document provides production-ready tuning recommendations for the Agentic QE Fleet Q-learning database supporting **18 concurrent agents** with high-throughput writes and low-latency reads.

### Performance Goals

| Metric | Target | Rationale |
|--------|--------|-----------|
| Q-value lookup | < 5ms | Real-time action selection |
| Q-value update | < 2ms | High-frequency learning |
| Trajectory insert | < 3ms | Batch execution tracking |
| Concurrent agents | 18+ | Full fleet operation |
| Database uptime | 99.9% | Production reliability |

---

## PostgreSQL Configuration

### Memory Settings

```ini
# postgresql.conf

# ============================================================================
# Memory Configuration (8GB RAM system)
# ============================================================================

# Shared Buffers: 25% of total RAM
# Caches frequently accessed data (hot Q-values, patterns)
shared_buffers = 2GB

# Effective Cache Size: 75% of total RAM
# PostgreSQL optimizer uses this for query planning
effective_cache_size = 6GB

# Maintenance Work Memory: For index creation, vacuuming
maintenance_work_mem = 512MB

# Work Memory: Per-operation memory (sorts, hash joins)
# 18 agents × 4MB = 72MB (safe for concurrent ops)
work_mem = 64MB

# WAL Buffers: Write-ahead log buffers
wal_buffers = 16MB
```

### CPU & Parallelism

```ini
# ============================================================================
# CPU & Parallel Query Configuration
# ============================================================================

# Max Worker Processes: Total background workers
max_worker_processes = 8

# Max Parallel Workers Per Gather: For parallel queries
max_parallel_workers_per_gather = 4

# Max Parallel Workers: For all parallel operations
max_parallel_workers = 8

# Max Parallel Maintenance Workers: For index/vacuum
max_parallel_maintenance_workers = 4

# Effective I/O Concurrency: SSD-optimized (200 for NVMe)
effective_io_concurrency = 200
```

### Connection Settings

```ini
# ============================================================================
# Connection Configuration
# ============================================================================

# Max Connections: Use with PgBouncer (see below)
max_connections = 100

# Superuser Reserved Connections: For admin access
superuser_reserved_connections = 3

# Connection Timeout
tcp_keepalives_idle = 60
tcp_keepalives_interval = 10
tcp_keepalives_count = 10
```

### Write Performance (WAL)

```ini
# ============================================================================
# Write-Ahead Log (WAL) Configuration
# ============================================================================

# WAL Level: minimal for local, replica for replication
wal_level = replica

# Checkpoint Completion Target: Spread checkpoints over time
checkpoint_completion_target = 0.9

# Checkpoint Timeout: How often to force checkpoint
checkpoint_timeout = 15min

# Max WAL Size: Before triggering checkpoint
max_wal_size = 4GB

# Min WAL Size: Keep this much WAL
min_wal_size = 1GB

# Commit Delay: Group commits for better throughput
# (0 = disabled, 100-1000 microseconds for batching)
commit_delay = 0  # Start with 0, tune if needed
commit_siblings = 5
```

### Autovacuum Tuning

```ini
# ============================================================================
# Autovacuum Configuration (High Write Tables)
# ============================================================================

# Enable Autovacuum
autovacuum = on

# Autovacuum Max Workers: Concurrent vacuum operations
autovacuum_max_workers = 4

# Autovacuum Naptime: How often to check for vacuum
autovacuum_naptime = 30s

# Autovacuum Vacuum Scale Factor: % of table before vacuum
# Lower = more frequent vacuuming (good for high-write tables)
autovacuum_vacuum_scale_factor = 0.05  # 5% (default: 20%)

# Autovacuum Analyze Scale Factor: % before analyze
autovacuum_analyze_scale_factor = 0.025  # 2.5% (default: 10%)

# Autovacuum Cost Delay: Throttle vacuum I/O
autovacuum_vacuum_cost_delay = 10ms

# Autovacuum Cost Limit: Work units per delay
autovacuum_vacuum_cost_limit = 1000
```

### Query Statistics

```ini
# ============================================================================
# Statistics & Query Tracking
# ============================================================================

# Shared Preload Libraries: pg_stat_statements for query analysis
shared_preload_libraries = 'pg_stat_statements'

# Track Activity Query Size: For long queries
track_activity_query_size = 2048

# Default Statistics Target: Histogram buckets (higher = better estimates)
default_statistics_target = 100

# Enable pg_stat_statements
pg_stat_statements.track = all
pg_stat_statements.max = 10000
```

### SSD Optimization

```ini
# ============================================================================
# SSD-Specific Tuning
# ============================================================================

# Random Page Cost: Lower for SSDs (default: 4.0 for HDD)
random_page_cost = 1.1

# Sequential Page Cost: Baseline (always 1.0)
seq_page_cost = 1.0
```

---

## Connection Pooling

### Why PgBouncer?

**Problem:** 18 agents × 5 connections each = 90 connections → PostgreSQL overhead

**Solution:** PgBouncer connection pooler

- **Transaction pooling:** Reuse connections between transactions
- **18 agents → 10 PostgreSQL connections** (efficient multiplexing)
- **< 1ms connection overhead**

### PgBouncer Configuration

```ini
# pgbouncer.ini

[databases]
qlearning = host=localhost port=5432 dbname=qlearning_db

[pgbouncer]
# Listen Address
listen_addr = 127.0.0.1
listen_port = 6432

# Pool Mode: transaction (recommended for Q-learning)
pool_mode = transaction

# Connection Limits
max_client_conn = 200
default_pool_size = 20
reserve_pool_size = 5

# Timeouts
server_idle_timeout = 600
server_lifetime = 3600
server_connect_timeout = 15
query_timeout = 0

# Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Logging
log_connections = 1
log_disconnections = 1
stats_period = 60
```

### Application Connection String

```python
# Without PgBouncer (direct)
DATABASE_URL = "postgresql://user:pass@localhost:5432/qlearning_db"

# With PgBouncer (recommended)
DATABASE_URL = "postgresql://user:pass@localhost:6432/qlearning_db"
```

---

## Indexing Strategy

### Index Overview

All indexes are defined in the schema, but here's the rationale:

#### 1. Q-Value Lookups (Hot Path)

```sql
-- Primary lookup: agent + state → best action
CREATE INDEX idx_q_values_lookup ON q_values(
    agent_type, state_hash, q_value DESC
);

-- Covers query:
-- SELECT action_data, q_value FROM q_values
-- WHERE agent_type = 'test-generator' AND state_hash = '...'
-- ORDER BY q_value DESC LIMIT 1;
```

**Performance:** < 1ms with hot cache, < 5ms cold

#### 2. State-Action Uniqueness

```sql
-- Enforces unique constraint + fast upsert
CREATE UNIQUE INDEX uq_agent_state_action ON q_values(
    agent_type, state_hash, action_hash
);
```

**Performance:** Prevents duplicate Q-values, enables fast ON CONFLICT

#### 3. JSONB Search (GIN Indexes)

```sql
-- Fast JSONB containment queries
CREATE INDEX idx_q_values_state_data ON q_values USING GIN(state_data);
CREATE INDEX idx_patterns_data ON patterns USING GIN(pattern_data);
```

**Use Cases:**
- Pattern matching: `WHERE state_data @> '{"module": "auth"}'`
- Trigger search: `WHERE trigger_conditions @> '{"coverage": {"$lt": 80}}'`

**Performance:** 10-100x faster than full table scan

#### 4. Partial Indexes (Reduced Overhead)

```sql
-- Only index active sessions (hot data)
CREATE INDEX idx_sessions_status ON sessions(status)
WHERE status = 'active';

-- Only index Q-values with TTL
CREATE INDEX idx_q_values_expires ON q_values(expires_at)
WHERE expires_at IS NOT NULL;
```

**Benefit:** Smaller indexes = faster writes + less storage

#### 5. Trigram Indexes (Fuzzy Search)

```sql
-- Fuzzy pattern name search
CREATE INDEX idx_patterns_name ON patterns
USING GIN(pattern_name gin_trgm_ops);
```

**Use Cases:**
- Similarity search: `WHERE pattern_name % 'api_validtion'` (typo-tolerant)
- Pattern discovery: `SELECT * FROM patterns WHERE similarity(pattern_name, 'api') > 0.3`

### Index Maintenance

```sql
-- Monitor index usage (identify unused indexes)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;

-- Drop unused indexes (idx_scan = 0 after 30 days)
-- DROP INDEX IF EXISTS idx_unused;

-- Rebuild bloated indexes
REINDEX INDEX CONCURRENTLY idx_q_values_lookup;
```

---

## Query Optimization

### 1. Q-Value Upsert (Hot Path)

**Optimized Function:**

```sql
CREATE OR REPLACE FUNCTION upsert_q_value(
    p_agent_type VARCHAR(50),
    p_state_hash VARCHAR(64),
    p_state_data JSONB,
    p_action_hash VARCHAR(64),
    p_action_data JSONB,
    p_q_value DECIMAL(12,6),
    p_session_id UUID DEFAULT NULL
) RETURNS BIGINT AS $$
DECLARE
    v_q_value_id BIGINT;
BEGIN
    INSERT INTO q_values (
        agent_type, session_id, state_hash, state_data,
        action_hash, action_data, q_value, visit_count,
        expires_at
    ) VALUES (
        p_agent_type, p_session_id, p_state_hash, p_state_data,
        p_action_hash, p_action_data, p_q_value, 1,
        NOW() + INTERVAL '30 days'
    )
    ON CONFLICT (agent_type, state_hash, action_hash)
    DO UPDATE SET
        q_value = EXCLUDED.q_value,
        visit_count = q_values.visit_count + 1,
        last_updated = NOW(),
        confidence_score = LEAST(1.0, q_values.confidence_score + 0.01),
        uncertainty = GREATEST(0.0, q_values.uncertainty - 0.01)
    RETURNING q_value_id INTO v_q_value_id;

    RETURN v_q_value_id;
END;
$$ LANGUAGE plpgsql;
```

**Optimizations:**
- Single atomic operation (no race conditions)
- Uses unique index for fast conflict detection
- Minimal lock duration (< 1ms)

**Usage:**

```python
# Python example
q_value_id = await db.fetchval(
    "SELECT upsert_q_value($1, $2, $3, $4, $5, $6, $7)",
    agent_type, state_hash, state_data_json,
    action_hash, action_data_json, q_value, session_id
)
```

### 2. Best Action Selection (Exploitation)

**Optimized Query:**

```sql
-- Using function for encapsulation
SELECT * FROM get_best_action('test-generator', 'abc123...');

-- Equivalent raw query:
SELECT action_data, q_value, confidence_score
FROM q_values
WHERE agent_type = 'test-generator'
  AND state_hash = 'abc123...'
ORDER BY q_value DESC, confidence_score DESC
LIMIT 1;
```

**Execution Plan:**
```
QUERY PLAN
----------------------------------------------------------
Limit  (cost=0.43..8.45 rows=1 width=80)
  ->  Index Scan using idx_q_values_lookup on q_values
        Index Cond: (agent_type = 'test-generator' AND state_hash = 'abc123...')
        Sort: q_value DESC, confidence_score DESC
```

**Performance:** < 1ms (index-only scan)

### 3. Batch Trajectory Insert

**Optimized Batch Insert:**

```python
# Python asyncpg example
async def batch_insert_trajectories(trajectories: List[dict]):
    query = """
        INSERT INTO trajectories (
            agent_type, session_id, task_id, initial_state,
            final_state, actions_taken, states_visited,
            step_rewards, total_reward, discounted_reward,
            execution_time_ms, success, started_at,
            completed_at, expires_at
        )
        SELECT * FROM unnest(
            $1::varchar[], $2::uuid[], $3::varchar[], $4::jsonb[],
            $5::jsonb[], $6::jsonb[], $7::jsonb[], $8::jsonb[],
            $9::decimal[], $10::decimal[], $11::int[], $12::bool[],
            $13::timestamptz[], $14::timestamptz[], $15::timestamptz[]
        )
    """

    # Transpose list of dicts into arrays
    data = transpose_batch(trajectories)

    await db.execute(query, *data)
```

**Performance:**
- 10 trajectories: ~30ms (vs 10 × 3ms = 30ms individual)
- 100 trajectories: ~100ms (10x speedup)

### 4. Pattern Search

**Fuzzy Search:**

```sql
-- Find patterns similar to "api_validation" (typo-tolerant)
SELECT
    pattern_id,
    pattern_name,
    similarity(pattern_name, 'api_validtion') AS similarity_score
FROM patterns
WHERE pattern_name % 'api_validtion'  -- Trigram similarity operator
ORDER BY similarity_score DESC
LIMIT 10;
```

**Filtered Search:**

```sql
-- Find top-performing patterns for test-generator
SELECT
    pattern_name,
    avg_reward,
    usage_count,
    confidence_score
FROM patterns
WHERE agent_type = 'test-generator'
  AND avg_reward > 0.5
  AND usage_count > 10
ORDER BY avg_reward DESC, confidence_score DESC
LIMIT 20;
```

**Performance:** < 10ms (index-backed)

---

## Concurrency Control

### Isolation Levels

**Default:** Read Committed (PostgreSQL default)

```sql
-- Explicit isolation level (if needed)
BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- ... queries ...
COMMIT;
```

**Why not Serializable?**
- Q-learning updates are commutative (order doesn't matter)
- Lost updates are acceptable (Q-value convergence is iterative)
- Serializable = 10-100x slower (unnecessary for this use case)

### Lock Contention

**Problem:** Multiple agents updating same Q-value

**Solution:** Optimistic locking via `ON CONFLICT`

```sql
-- No explicit locks needed!
INSERT INTO q_values (agent_type, state_hash, action_hash, q_value)
VALUES ('test-gen', 'abc', '123', 0.5)
ON CONFLICT (agent_type, state_hash, action_hash)
DO UPDATE SET
    q_value = (q_values.q_value + EXCLUDED.q_value) / 2,  -- Average
    visit_count = q_values.visit_count + 1;
```

**Behavior:**
- First agent: Inserts new row
- Second agent (concurrent): Conflicts → averages Q-values
- No deadlocks, no explicit locking

### Deadlock Prevention

**Best Practices:**

1. **Consistent ordering:** Always access tables in same order
   ```python
   # Good: agent_types → sessions → q_values
   # Bad:  q_values → sessions → agent_types (can deadlock)
   ```

2. **Short transactions:** Keep transactions < 100ms
   ```python
   async with db.transaction():
       # Fast: Single upsert
       await upsert_q_value(...)
   ```

3. **Avoid nested transactions:** Use savepoints sparingly

4. **Monitor deadlocks:**
   ```sql
   SELECT * FROM pg_stat_database WHERE datname = 'qlearning_db';
   -- Check: deadlocks column
   ```

---

## Monitoring & Observability

### Key Metrics

#### 1. Query Performance (pg_stat_statements)

```sql
-- Top 10 slowest queries
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### 2. Table Statistics

```sql
-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### 3. Index Usage

```sql
-- Identify unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0  -- Never used
  AND indexrelname NOT LIKE '%_pkey'  -- Exclude primary keys
ORDER BY pg_relation_size(indexrelid) DESC;
```

#### 4. Vacuum Activity

```sql
-- Check autovacuum status
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup, 0), 2) AS dead_tuple_pct,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY dead_tuple_pct DESC NULLS LAST;
```

#### 5. Connection Stats

```sql
-- Current connections
SELECT
    datname,
    usename,
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity
WHERE datname = 'qlearning_db'
GROUP BY datname, usename, state
ORDER BY connection_count DESC;
```

### Alerts (Set up with Prometheus/Grafana)

| Alert | Threshold | Action |
|-------|-----------|--------|
| Query latency > 100ms | p95 | Investigate slow queries |
| Dead tuples > 10% | Any table | Force vacuum |
| Connection pool exhausted | > 90% | Scale PgBouncer |
| Table size > 5 GB | q_values, trajectories | Review TTL policy |
| Deadlocks > 10/hour | Any | Analyze lock contention |

---

## Supabase-Specific Considerations

### Overview

Supabase = Managed PostgreSQL + PostgREST API + Realtime subscriptions

### Connection Details

```python
# Supabase connection string
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5..."

# Direct PostgreSQL connection (for asyncpg)
DATABASE_URL = "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
```

### Supabase Advantages

1. **Built-in Pooler:** Supavisor (PgBouncer-like)
   - No need to deploy separate PgBouncer
   - Use port 6543 for pooled connections

2. **Row-Level Security (RLS):**
   ```sql
   -- Restrict agents to their own data
   ALTER TABLE q_values ENABLE ROW LEVEL SECURITY;

   CREATE POLICY agent_isolation ON q_values
       USING (agent_type = current_setting('app.agent_type')::varchar);
   ```

3. **Realtime Subscriptions:**
   ```javascript
   // Listen for Q-value updates (optional)
   const channel = supabase
       .channel('q_values_changes')
       .on('postgres_changes', {
           event: 'UPDATE',
           schema: 'public',
           table: 'q_values'
       }, (payload) => console.log(payload))
       .subscribe();
   ```

### Supabase Limitations

1. **No Extensions Control:**
   - `pg_stat_statements` may not be available
   - `pg_trgm` typically available (check first)

2. **Connection Limits:**
   - Free tier: 60 connections
   - Pro tier: 100+ connections
   - Use Supavisor pooler (port 6543)

3. **Autovacuum Settings:**
   - Cannot modify postgresql.conf directly
   - Supabase manages autovacuum (usually fine)

### Recommended Supabase Setup

```python
# Python asyncpg with Supabase
import asyncpg
import os

async def create_pool():
    return await asyncpg.create_pool(
        host='db.your-project.supabase.co',
        port=6543,  # Supavisor pooler (not 5432!)
        user='postgres',
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        database='postgres',
        min_size=5,
        max_size=20,
        command_timeout=60
    )

# Usage
pool = await create_pool()
async with pool.acquire() as conn:
    result = await conn.fetchval(
        "SELECT upsert_q_value($1, $2, $3, $4, $5, $6)",
        agent_type, state_hash, state_data, action_hash, action_data, q_value
    )
```

### Migration to Supabase

```bash
# 1. Export local schema
pg_dump -h localhost -U postgres -d qlearning_db -s -f schema.sql

# 2. Import to Supabase
psql "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres" < schema.sql

# 3. Run Alembic migration
alembic upgrade head
```

---

## Scaling Strategies

### Vertical Scaling (Scale Up)

**When:** < 1 million Q-values, < 100k trajectories/day

**Action:**
- Increase RAM: 8 GB → 16 GB → 32 GB
- Increase CPUs: 4 cores → 8 cores
- Upgrade to SSD/NVMe if not already

**Cost:** $50-200/month (Supabase Pro/Scale)

### Horizontal Scaling (Scale Out)

**When:** > 1 million Q-values, > 100k trajectories/day

#### Option 1: Read Replicas

```python
# Write to primary
await primary_pool.execute("SELECT upsert_q_value(...)")

# Read from replica (analytics)
trajectories = await replica_pool.fetch(
    "SELECT * FROM trajectories WHERE agent_type = $1", agent_type
)
```

**Benefit:** Offload analytics queries from primary

#### Option 2: Partitioning

```sql
-- Partition trajectories by month
CREATE TABLE trajectories (
    trajectory_id UUID PRIMARY KEY,
    completed_at TIMESTAMPTZ NOT NULL,
    -- ... other columns
) PARTITION BY RANGE (completed_at);

-- Create monthly partitions
CREATE TABLE trajectories_2025_11 PARTITION OF trajectories
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE trajectories_2025_12 PARTITION OF trajectories
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Automatically drop old partitions (efficient archival)
DROP TABLE trajectories_2024_10;
```

**Benefit:** Fast archival, reduced table bloat

#### Option 3: Sharding (Advanced)

**Strategy:** Shard by `agent_type`

```python
# Shard routing logic
def get_db_pool(agent_type: str):
    shard_id = hash(agent_type) % NUM_SHARDS
    return db_pools[shard_id]

# Usage
pool = get_db_pool('test-generator')
await pool.execute("SELECT upsert_q_value(...)")
```

**Sharding Layout:**

| Shard | Agent Types | Database |
|-------|-------------|----------|
| 0 | test-generator, coverage-analyzer, quality-gate | db-shard-0 |
| 1 | performance-tester, security-scanner, visual-tester | db-shard-1 |
| 2 | (remaining 12 agents) | db-shard-2 |

**Benefit:** Linear scalability (3x shards = 3x throughput)

### Caching Layer

**Strategy:** Redis for hot Q-values

```python
# Check Redis cache first
q_value = await redis.get(f"qval:{agent_type}:{state_hash}:{action_hash}")

if q_value is None:
    # Cache miss: Query PostgreSQL
    q_value = await db.fetchval(
        "SELECT q_value FROM q_values WHERE agent_type = $1 AND state_hash = $2 AND action_hash = $3",
        agent_type, state_hash, action_hash
    )

    # Populate cache (TTL: 5 minutes)
    await redis.setex(
        f"qval:{agent_type}:{state_hash}:{action_hash}",
        300,
        q_value
    )
```

**Benefit:**
- 10-100x faster reads (< 0.1ms)
- Reduces PostgreSQL load by 80-90%

**Trade-off:** Stale data (up to 5 minutes)

---

## Production Checklist

- [ ] PostgreSQL 14+ deployed
- [ ] `postgresql.conf` tuned (shared_buffers, work_mem, etc.)
- [ ] PgBouncer or Supavisor configured
- [ ] All indexes created (run schema.sql)
- [ ] Materialized views set up (refresh cron job)
- [ ] `pg_stat_statements` enabled
- [ ] Autovacuum tuned for high-write tables
- [ ] Monitoring dashboards configured (Grafana/Datadog)
- [ ] Alerts set up (query latency, deadlocks, connection exhaustion)
- [ ] Backup strategy implemented (daily snapshots + WAL archiving)
- [ ] TTL cleanup job scheduled (daily `cleanup_expired_data()`)
- [ ] Load testing completed (18 agents × 100 tasks/sec)
- [ ] Connection pooling validated (no "too many connections" errors)
- [ ] Query performance benchmarked (Q-value lookup < 5ms)

---

## References

- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [PgBouncer Documentation](https://www.pgbouncer.org/)
- [Supabase Database Guide](https://supabase.com/docs/guides/database)
- [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [asyncpg (Python PostgreSQL driver)](https://magicstack.github.io/asyncpg/current/)

---

**Last Updated:** 2025-11-05
**Schema Version:** 1.0.0
**Author:** Agentic QE Fleet
