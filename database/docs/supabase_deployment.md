# Supabase Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Schema Migration](#schema-migration)
5. [Connection Configuration](#connection-configuration)
6. [Row-Level Security (RLS)](#row-level-security-rls)
7. [Realtime Integration](#realtime-integration)
8. [Edge Functions (Optional)](#edge-functions-optional)
9. [Monitoring & Logs](#monitoring--logs)
10. [Cost Estimation](#cost-estimation)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying the Q-learning database to **Supabase**, a managed PostgreSQL platform with built-in APIs and connection pooling.

### Why Supabase?

- **Managed PostgreSQL 15+**: No server management
- **Built-in Pooler (Supavisor)**: Connection pooling without PgBouncer
- **Row-Level Security**: Multi-tenant isolation
- **PostgREST API**: Auto-generated REST API
- **Realtime**: WebSocket subscriptions for live updates
- **Free Tier**: 500 MB database + 2 GB bandwidth

---

## Prerequisites

1. **Supabase Account**
   - Sign up at [supabase.com](https://supabase.com)
   - Free tier available (sufficient for development)

2. **Supabase CLI** (optional but recommended)
   ```bash
   npm install -g supabase
   supabase login
   ```

3. **PostgreSQL Client** (for direct connections)
   ```bash
   # macOS
   brew install postgresql

   # Ubuntu/Debian
   sudo apt install postgresql-client

   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

4. **Python Dependencies**
   ```bash
   pip install asyncpg python-dotenv supabase-py
   ```

---

## Initial Setup

### 1. Create Supabase Project

**Via Web UI:**
1. Go to [app.supabase.com](https://app.supabase.com)
2. Click "New Project"
3. Configure:
   - **Name:** `qlearning-fleet`
   - **Database Password:** (generate strong password)
   - **Region:** Choose closest to agents (e.g., `us-east-1`)
   - **Pricing Plan:** Free tier for dev, Pro ($25/mo) for production

**Via CLI:**
```bash
supabase projects create qlearning-fleet \
    --org-id your-org-id \
    --db-password "$(openssl rand -base64 32)" \
    --region us-east-1
```

### 2. Save Connection Details

After creation, save these values:

```bash
# .env file
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Direct PostgreSQL connection (for asyncpg)
SUPABASE_DB_HOST=db.your-project-id.supabase.co
SUPABASE_DB_PORT=6543  # Pooled connection (Supavisor)
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-strong-password
SUPABASE_DB_NAME=postgres
```

**Important:** Use port **6543** (pooled) not 5432 (direct) for production!

---

## Schema Migration

### Option 1: SQL Migration (Recommended)

```bash
# 1. Navigate to database directory
cd database/schema

# 2. Connect to Supabase
psql "postgresql://postgres:password@db.your-project-id.supabase.co:5432/postgres"

# 3. Run schema
\i qlearning_schema.sql

# 4. Verify tables
\dt

# Expected output:
#              List of relations
#  Schema |      Name       | Type  |  Owner
# --------+-----------------+-------+----------
#  public | agent_states    | table | postgres
#  public | agent_types     | table | postgres
#  public | patterns        | table | postgres
#  public | q_values        | table | postgres
#  public | rewards         | table | postgres
#  public | sessions        | table | postgres
#  public | trajectories    | table | postgres
```

### Option 2: Alembic Migration (Python)

```bash
# 1. Install Alembic
pip install alembic asyncpg

# 2. Initialize Alembic (if not done)
alembic init alembic

# 3. Configure alembic.ini
# Edit: sqlalchemy.url = postgresql+asyncpg://postgres:password@db.your-project-id.supabase.co:5432/postgres

# 4. Copy migration file
cp database/migrations/alembic_migration_qlearning.py alembic/versions/001_qlearning_initial.py

# 5. Run migration
alembic upgrade head
```

### Option 3: Supabase Dashboard (Manual)

1. Go to **SQL Editor** in Supabase dashboard
2. Copy contents of `database/schema/qlearning_schema.sql`
3. Paste and click **Run**
4. Verify in **Table Editor**

---

## Connection Configuration

### Python (asyncpg)

```python
# database/supabase_client.py
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def create_supabase_pool():
    """Create connection pool to Supabase PostgreSQL"""
    return await asyncpg.create_pool(
        host=os.getenv('SUPABASE_DB_HOST'),
        port=int(os.getenv('SUPABASE_DB_PORT', 6543)),  # Pooled!
        user=os.getenv('SUPABASE_DB_USER'),
        password=os.getenv('SUPABASE_DB_PASSWORD'),
        database=os.getenv('SUPABASE_DB_NAME'),
        min_size=5,
        max_size=20,
        command_timeout=60,
        ssl='require'  # Supabase requires SSL
    )

# Usage
async def main():
    pool = await create_supabase_pool()

    # Upsert Q-value
    async with pool.acquire() as conn:
        q_value_id = await conn.fetchval(
            "SELECT upsert_q_value($1, $2, $3, $4, $5, $6, $7)",
            'test-generator',  # agent_type
            'abc123',          # state_hash
            '{"module": "auth"}',  # state_data (JSON)
            'def456',          # action_hash
            '{"action": "generate_unit_test"}',  # action_data
            0.75,              # q_value
            None               # session_id
        )
        print(f"Q-value ID: {q_value_id}")

    await pool.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### Node.js (Supabase JS Client)

```javascript
// database/supabaseClient.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY

export const supabase = createClient(supabaseUrl, supabaseKey)

// Usage: Insert trajectory
async function insertTrajectory(trajectory) {
    const { data, error } = await supabase
        .from('trajectories')
        .insert({
            agent_type: 'test-executor',
            session_id: trajectory.sessionId,
            task_id: trajectory.taskId,
            initial_state: trajectory.initialState,
            final_state: trajectory.finalState,
            actions_taken: trajectory.actions,
            states_visited: trajectory.states,
            step_rewards: trajectory.rewards,
            total_reward: trajectory.totalReward,
            discounted_reward: trajectory.discountedReward,
            execution_time_ms: trajectory.executionTime,
            success: trajectory.success,
            started_at: trajectory.startedAt,
            completed_at: new Date().toISOString()
        })

    if (error) throw error
    return data
}
```

---

## Row-Level Security (RLS)

### Enable RLS for Multi-Agent Isolation

```sql
-- Enable RLS on all tables
ALTER TABLE agent_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE q_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE trajectories ENABLE ROW LEVEL SECURITY;
ALTER TABLE rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_states ENABLE ROW LEVEL SECURITY;

-- Create policies

-- 1. Each agent can only access its own data
CREATE POLICY agent_isolation_q_values ON q_values
    FOR ALL
    USING (agent_type = current_setting('app.agent_type')::varchar);

CREATE POLICY agent_isolation_trajectories ON trajectories
    FOR ALL
    USING (agent_type = current_setting('app.agent_type')::varchar);

CREATE POLICY agent_isolation_patterns ON patterns
    FOR ALL
    USING (agent_type = current_setting('app.agent_type')::varchar);

-- 2. Read-only access for analytics (special role)
CREATE POLICY analytics_read_all ON trajectories
    FOR SELECT
    TO analytics_role
    USING (true);

-- 3. Service role bypasses RLS (full access)
-- (Supabase service_role key automatically bypasses RLS)
```

### Set Agent Context in Application

```python
# Set agent_type for RLS policy
async with pool.acquire() as conn:
    # Set session variable
    await conn.execute("SET app.agent_type = 'test-generator'")

    # All subsequent queries filtered by RLS
    q_values = await conn.fetch(
        "SELECT * FROM q_values WHERE state_hash = $1",
        state_hash
    )
    # Returns only test-generator's Q-values
```

**Security Benefit:** Even if SQL injection occurs, agents can't access each other's data.

---

## Realtime Integration

### Subscribe to Q-Value Updates

```javascript
// Enable Realtime for q_values table
// (In Supabase Dashboard: Database > Replication > Enable for q_values)

// Subscribe to updates
const channel = supabase
    .channel('q-values-changes')
    .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'q_values',
        filter: 'agent_type=eq.test-generator'
    }, (payload) => {
        console.log('Q-value updated:', payload.new)
        // Update UI, trigger notifications, etc.
    })
    .subscribe()

// Usage: Live dashboard showing agent learning progress
```

### Realtime Fleet Status

```javascript
// Subscribe to agent_states for live fleet monitoring
const fleetChannel = supabase
    .channel('fleet-status')
    .on('postgres_changes', {
        event: '*',  // All events (INSERT, UPDATE, DELETE)
        schema: 'public',
        table: 'agent_states'
    }, (payload) => {
        console.log('Fleet status changed:', payload)
        updateDashboard(payload.new)
    })
    .subscribe()
```

**Use Cases:**
- Live dashboard showing agent learning progress
- Real-time alerts when agents fail
- Collaborative debugging (multiple devs watching same agent)

---

## Edge Functions (Optional)

Deploy serverless functions for Q-learning operations:

### Example: Q-Value Lookup Edge Function

```typescript
// supabase/functions/get-best-action/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
    const { agent_type, state_hash } = await req.json()

    const supabase = createClient(
        Deno.env.get('SUPABASE_URL')!,
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Call get_best_action function
    const { data, error } = await supabase.rpc('get_best_action', {
        p_agent_type: agent_type,
        p_state_hash: state_hash
    })

    if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        })
    }

    return new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' }
    })
})
```

**Deploy:**
```bash
supabase functions deploy get-best-action

# Test
curl -X POST https://your-project-id.supabase.co/functions/v1/get-best-action \
    -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
    -d '{"agent_type": "test-generator", "state_hash": "abc123"}'
```

**Benefit:** Expose Q-learning APIs without managing servers

---

## Monitoring & Logs

### 1. Query Performance

**Via Dashboard:**
- Go to **Database** > **Query Performance**
- View slowest queries, connection stats

**Via SQL:**
```sql
-- Top 10 slowest queries (requires pg_stat_statements)
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### 2. Database Logs

**Via Dashboard:**
- Go to **Logs** > **Postgres Logs**
- Filter by severity: ERROR, WARNING

**Via CLI:**
```bash
supabase logs --level error --tail
```

### 3. Connection Stats

```sql
-- Current active connections
SELECT
    state,
    COUNT(*) as count
FROM pg_stat_activity
WHERE datname = 'postgres'
GROUP BY state;
```

### 4. Table Statistics

```sql
-- Table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Cost Estimation

### Free Tier (Development)

| Resource | Limit | Sufficient For |
|----------|-------|----------------|
| Database | 500 MB | ~500k Q-values, 50k trajectories |
| Bandwidth | 2 GB/month | 1-2 agents, light usage |
| Pooled Connections | 60 | 5-10 concurrent agents |
| Realtime | Unlimited | All agents |

**Cost:** $0/month

### Pro Tier (Production)

| Resource | Limit | Sufficient For |
|----------|-------|----------------|
| Database | 8 GB | ~8M Q-values, 400k trajectories |
| Bandwidth | 50 GB/month | 18 agents, moderate usage |
| Pooled Connections | 200 | 18+ concurrent agents |
| Realtime | Unlimited | All agents |
| Daily Backups | Included | Disaster recovery |

**Cost:** $25/month

### Team/Scale Tier (High Traffic)

| Resource | Limit | Sufficient For |
|----------|-------|----------------|
| Database | Customizable (16-256 GB) | Unlimited Q-values |
| Bandwidth | 250 GB/month | 50+ agents, high traffic |
| Pooled Connections | Customizable | 100+ agents |
| Read Replicas | Available | Analytics offloading |

**Cost:** $599+/month

### Estimate Your Usage

```python
# Storage estimation
q_values = 18 * 1000 * 500  # 18 agents × 1000 pairs × 500 bytes
trajectories = 18 * 100 * 30 * 2000  # 18 agents × 100/day × 30 days × 2KB
total_mb = (q_values + trajectories) / 1024 / 1024

print(f"Estimated storage: {total_mb:.2f} MB")
# Output: ~430 MB (fits in Free tier)
```

**Recommendation:**
- Development: Free tier
- Production (< 50k tasks/month): Pro tier ($25/mo)
- Production (> 50k tasks/month): Team tier ($599/mo)

---

## Troubleshooting

### Issue 1: "Too many connections"

**Cause:** Not using pooled connections (port 6543)

**Solution:**
```python
# Wrong: Direct connection (port 5432)
# host='db.project.supabase.co', port=5432

# Correct: Pooled connection (port 6543)
host='db.project.supabase.co', port=6543
```

### Issue 2: "Extension not available"

**Cause:** Trying to install unsupported extension

**Solution:**
```sql
-- Check available extensions
SELECT * FROM pg_available_extensions WHERE installed_version IS NOT NULL;

-- Commonly available on Supabase:
-- ✅ uuid-ossp, pg_trgm, btree_gin, pgcrypto
-- ❌ pg_stat_statements (requires superuser)
```

### Issue 3: Slow queries

**Cause:** Missing indexes or inefficient queries

**Solution:**
```sql
-- Check query execution plan
EXPLAIN ANALYZE
SELECT * FROM q_values WHERE agent_type = 'test-generator' AND state_hash = 'abc';

-- Expected: "Index Scan using idx_q_values_agent_state"
-- If "Seq Scan": Index missing, recreate schema
```

### Issue 4: RLS blocking queries

**Cause:** Row-Level Security enabled but policy not set

**Solution:**
```python
# Set session variable before query
await conn.execute("SET app.agent_type = 'test-generator'")

# Or use service_role key (bypasses RLS)
supabase = createClient(url, SERVICE_ROLE_KEY)
```

### Issue 5: Supavisor connection failures

**Cause:** Exceeding connection pool limit

**Solution:**
```python
# Reduce max_size in application pool
pool = await asyncpg.create_pool(
    max_size=10,  # Was 20 (too high for Free tier)
    min_size=2
)
```

### Issue 6: JSONB query not using GIN index

**Cause:** Query syntax incompatible with GIN

**Solution:**
```sql
-- Wrong: JSON_EXTRACT (doesn't use index)
SELECT * FROM q_values WHERE state_data::json->>'module' = 'auth';

-- Correct: JSONB containment (uses GIN index)
SELECT * FROM q_values WHERE state_data @> '{"module": "auth"}';
```

---

## Migration Checklist

- [ ] Supabase project created
- [ ] Connection details saved in `.env`
- [ ] Schema migrated (`qlearning_schema.sql`)
- [ ] Tables verified in dashboard
- [ ] Connection pooling tested (port 6543)
- [ ] RLS policies enabled (if multi-tenant)
- [ ] Realtime enabled for required tables
- [ ] Python/Node.js client tested
- [ ] Monitoring dashboard bookmarked
- [ ] Backup strategy confirmed (Supabase auto-backups)
- [ ] Cost estimation reviewed
- [ ] Load testing completed (18 agents)

---

## Next Steps

1. **Integrate with Agents:**
   - Update `src/lionagi_qe/core/memory.py` to use Supabase client
   - Test Q-value upsert from agents

2. **Set Up Monitoring:**
   - Create Grafana dashboard (Supabase metrics API)
   - Set up alerts (PagerDuty/Slack integration)

3. **Implement Backup Strategy:**
   - Supabase auto-backups (daily, 7-day retention)
   - Export critical data to S3 (optional)

4. **Optimize Performance:**
   - Review query performance dashboard
   - Add missing indexes if needed
   - Tune connection pool sizes

---

## References

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli/introduction)
- [PostgreSQL RLS Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Realtime](https://supabase.com/docs/guides/realtime)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)

---

**Last Updated:** 2025-11-05
**Schema Version:** 1.0.0
**Author:** Agentic QE Fleet
