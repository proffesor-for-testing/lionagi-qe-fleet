# Quick Start Guide - Q-Learning Database

Get up and running with the Q-learning database in 5 minutes.

---

## 🚀 30-Second Setup (Docker)

```bash
# 1. Navigate to database directory
cd database

# 2. Start PostgreSQL + PgBouncer
docker-compose up -d

# 3. Verify
docker-compose exec postgres psql -U postgres -d qlearning_db -c "SELECT COUNT(*) FROM agent_types;"
# Expected output: 18 (agent types)
```

**Done!** Database is ready at:
- **PostgreSQL (direct):** `localhost:5432`
- **PgBouncer (pooled):** `localhost:6432` ← **Use this**

---

## 🔗 Connect from Python

```python
import asyncpg

# Create connection pool (PgBouncer)
pool = await asyncpg.create_pool(
    host='localhost',
    port=6432,  # Pooled connection
    user='postgres',
    password='changeme',
    database='qlearning_db',
    min_size=5,
    max_size=20
)

# Upsert Q-value
async with pool.acquire() as conn:
    q_value_id = await conn.fetchval(
        "SELECT upsert_q_value($1, $2, $3, $4, $5, $6)",
        'test-generator',  # agent_type
        'abc123',          # state_hash (SHA256 of state)
        '{"module": "auth", "coverage": 0.65}',  # state_data (JSON)
        'def456',          # action_hash (SHA256 of action)
        '{"action": "generate_unit_test"}',      # action_data (JSON)
        0.85               # q_value
    )
    print(f"Q-value ID: {q_value_id}")

# Get best action
async with pool.acquire() as conn:
    action = await conn.fetchrow(
        "SELECT * FROM get_best_action($1, $2)",
        'test-generator',
        'abc123'
    )
    print(f"Best action: {action['action_data']}")
    print(f"Q-value: {action['q_value']}")
```

---

## 🗄️ Core Operations

### 1. Insert Trajectory

```python
await conn.execute("""
    INSERT INTO trajectories (
        agent_type, session_id, task_id,
        initial_state, final_state,
        actions_taken, states_visited,
        step_rewards, total_reward, discounted_reward,
        execution_time_ms, success,
        started_at, completed_at
    ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
    )
""",
    'test-generator',
    session_id,
    'task-123',
    '{"coverage": 0.5}',  # initial_state
    '{"coverage": 0.75}',  # final_state
    '[{"action": "generate_test"}]',  # actions_taken
    '[{"coverage": 0.5}, {"coverage": 0.75}]',  # states_visited
    '[0.5, 0.25]',  # step_rewards
    0.75,  # total_reward
    0.7375,  # discounted_reward (gamma=0.95)
    1500,  # execution_time_ms
    True,  # success
    started_at,
    completed_at
)
```

### 2. Store Pattern

```python
await conn.execute("""
    INSERT INTO patterns (
        agent_type, pattern_name, pattern_type,
        pattern_data, trigger_conditions,
        expected_outcome
    ) VALUES ($1, $2, $3, $4, $5, $6)
""",
    'test-generator',
    'AAA Pattern',
    'test_template',
    '{"template": "def test_{}(): pass"}',
    '{"complexity": {"$lt": 5}}',
    '{"test_passes": true}'
)
```

### 3. Update Agent State

```python
await conn.execute("""
    INSERT INTO agent_states (
        agent_type, agent_instance_id,
        total_tasks, successful_tasks,
        total_reward, avg_reward,
        current_exploration_rate,
        current_learning_rate
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (agent_type, agent_instance_id)
    DO UPDATE SET
        total_tasks = agent_states.total_tasks + 1,
        successful_tasks = agent_states.successful_tasks + EXCLUDED.successful_tasks,
        total_reward = agent_states.total_reward + EXCLUDED.total_reward,
        avg_reward = (agent_states.total_reward + EXCLUDED.total_reward) / (agent_states.total_tasks + 1),
        last_activity = NOW()
""",
    'test-generator',
    'test-generator-1',
    1, 1,  # total_tasks, successful_tasks (increment)
    0.85, 0.85,  # total_reward, avg_reward
    0.15, 0.10  # exploration_rate, learning_rate
)
```

---

## 📊 Query Examples

### Top Patterns by Reward

```sql
SELECT
    agent_type,
    pattern_name,
    avg_reward,
    usage_count,
    confidence_score
FROM patterns
WHERE avg_reward > 0.5
ORDER BY avg_reward DESC, confidence_score DESC
LIMIT 10;
```

### Agent Performance Summary

```sql
SELECT * FROM agent_performance_summary
ORDER BY avg_reward DESC;
```

### Recent Trajectories

```sql
SELECT
    agent_type,
    task_id,
    total_reward,
    execution_time_ms,
    success,
    completed_at
FROM trajectories
WHERE completed_at > NOW() - INTERVAL '1 hour'
ORDER BY completed_at DESC;
```

### Q-Value Statistics

```sql
SELECT
    agent_type,
    COUNT(*) as q_value_count,
    AVG(q_value) as avg_q_value,
    MAX(q_value) as max_q_value,
    AVG(visit_count) as avg_visits
FROM q_values
GROUP BY agent_type
ORDER BY avg_q_value DESC;
```

---

## 🧪 Test Connection

```bash
# Run this command to verify everything works
docker-compose exec postgres psql -U postgres -d qlearning_db << 'EOF'
-- Test upsert_q_value function
SELECT upsert_q_value(
    'test-generator',
    'test_state_hash',
    '{"test": true}',
    'test_action_hash',
    '{"action": "test"}',
    0.99
);

-- Test get_best_action function
SELECT * FROM get_best_action('test-generator', 'test_state_hash');

-- Cleanup
DELETE FROM q_values WHERE state_hash = 'test_state_hash';
EOF
```

Expected output:
```
 upsert_q_value
----------------
             1

 action_data     | q_value | confidence_score
-----------------+---------+-----------------
 {"action": "test"} | 0.99    | 0.5000

DELETE 1
```

---

## 🛠️ Common Tasks

### View Logs

```bash
# PostgreSQL logs
docker-compose logs -f postgres

# PgBouncer logs
docker-compose logs -f pgbouncer
```

### Connect to Database

```bash
# Via PgBouncer (pooled)
psql postgresql://postgres:changeme@localhost:6432/qlearning_db

# Direct to PostgreSQL
psql postgresql://postgres:changeme@localhost:5432/qlearning_db
```

### Backup Database

```bash
# Dump schema + data
docker-compose exec postgres pg_dump -U postgres qlearning_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres qlearning_db < backup.sql
```

### Check Table Sizes

```bash
docker-compose exec postgres psql -U postgres -d qlearning_db -c "
    SELECT
        tablename,
        pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size('public.'||tablename) DESC;
"
```

### Run Cleanup (TTL Enforcement)

```bash
docker-compose exec postgres psql -U postgres -d qlearning_db -c "
    SELECT * FROM cleanup_expired_data();
"
```

---

## 🔧 Configuration

### Change Password

```bash
# 1. Edit .env
POSTGRES_PASSWORD=your-new-password

# 2. Recreate containers
docker-compose down
docker-compose up -d
```

### Enable pgAdmin (Database UI)

```bash
# Start with pgAdmin
docker-compose --profile tools up -d

# Access: http://localhost:5050
# Email: admin@qlearning.local
# Password: admin
```

### Enable Monitoring (Prometheus + Grafana)

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana: http://localhost:3000
# Username: admin
# Password: admin
```

---

## 🚨 Troubleshooting

### "Connection refused"

**Cause:** Database not started

**Solution:**
```bash
docker-compose up -d
docker-compose ps  # Check status
```

### "Too many connections"

**Cause:** Using direct connection (port 5432) instead of pooled (6432)

**Solution:**
```python
# Change port from 5432 to 6432
pool = await asyncpg.create_pool(port=6432)
```

### "Table does not exist"

**Cause:** Schema not initialized

**Solution:**
```bash
# Recreate database with schema
docker-compose down -v
docker-compose up -d
```

### Slow Queries

**Check query plan:**
```sql
EXPLAIN ANALYZE
SELECT * FROM q_values WHERE agent_type = 'test-generator' AND state_hash = 'abc';
```

**Expected:** "Index Scan using idx_q_values_lookup"

**If "Seq Scan":** Recreate indexes
```bash
docker-compose exec postgres psql -U postgres -d qlearning_db -c "REINDEX DATABASE qlearning_db;"
```

---

## 📚 Next Steps

- **Production Deployment:** See [Supabase Deployment Guide](docs/supabase_deployment.md)
- **Performance Tuning:** See [Performance Tuning Guide](docs/performance_tuning.md)
- **Schema Details:** See [ER Diagram](docs/er_diagram.txt)
- **Storage Planning:** See [Storage Calculator](docs/storage_calculator.md)

---

## 💡 Pro Tips

1. **Always use PgBouncer (port 6432)** for application connections
2. **Use `upsert_q_value()` function** instead of raw INSERT (handles conflicts)
3. **Set TTL on all data** to avoid unbounded growth
4. **Monitor table sizes weekly** to catch anomalies
5. **Run `cleanup_expired_data()` daily** via cron job

---

## 🆘 Support

- **Documentation:** [README.md](README.md)
- **Issues:** [GitHub Issues](https://github.com/lionagi/lionagi-qe-fleet/issues)
- **Schema Version:** 1.0.0

---

**Last Updated:** 2025-11-05
