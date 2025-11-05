# Storage Estimation Calculator

## Overview

This document provides detailed storage calculations for the Q-learning database based on different workload scenarios.

---

## Formula Reference

### Base Row Sizes

```
agent_types:     ~500 bytes  (JSONB metadata)
sessions:        ~300 bytes  (JSONB metadata)
q_values:        ~500 bytes  (state_data + action_data JSONB)
trajectories:    ~2 KB       (actions_taken, states_visited arrays)
rewards:         ~200 bytes  (minimal JSONB)
patterns:        ~1 KB       (pattern_data JSONB)
agent_states:    ~500 bytes  (JSONB metadata)
```

### Index Overhead

**Rule of Thumb:** Indexes = 3x table size (conservative estimate)

- B-tree indexes: ~100-150% of indexed columns
- GIN indexes (JSONB): ~200-300% of indexed columns
- Partial indexes: Proportional to filtered rows

---

## Scenario Calculations

### Scenario 1: Development (Light Usage)

**Parameters:**
- Agents: 5 active agents
- Tasks: 10 tasks/day per agent
- Duration: 30 days (TTL)
- Q-values: 500 unique state-action pairs per agent
- Patterns: 10 patterns per agent

**Calculations:**

```python
# Q-values
q_values_rows = 5 * 500
q_values_size = q_values_rows * 500  # bytes
q_values_total = q_values_size * 3   # with indexes

# Trajectories
trajectories_rows = 5 * 10 * 30
trajectories_size = trajectories_rows * 2048  # 2 KB per row
trajectories_total = trajectories_size * 3

# Rewards (10 rewards per trajectory)
rewards_rows = trajectories_rows * 10
rewards_size = rewards_rows * 200
rewards_total = rewards_size * 3

# Patterns
patterns_rows = 5 * 10
patterns_size = patterns_rows * 1024
patterns_total = patterns_size * 3

# Sessions (1 session per 10 tasks)
sessions_rows = trajectories_rows / 10
sessions_size = sessions_rows * 300
sessions_total = sessions_size * 3

# Agent states
agent_states_rows = 5
agent_states_size = agent_states_rows * 500
agent_states_total = agent_states_size * 3

# Total
total_bytes = (
    q_values_total + trajectories_total + rewards_total +
    patterns_total + sessions_total + agent_states_total
)
total_mb = total_bytes / 1024 / 1024
```

**Results:**

| Table | Rows | Table Size | With Indexes | Total |
|-------|------|------------|--------------|-------|
| q_values | 2,500 | 1.2 MB | 3.6 MB | 3.6 MB |
| trajectories | 1,500 | 3.0 MB | 9.0 MB | 9.0 MB |
| rewards | 15,000 | 3.0 MB | 9.0 MB | 9.0 MB |
| patterns | 50 | 50 KB | 150 KB | 0.15 MB |
| sessions | 150 | 45 KB | 135 KB | 0.14 MB |
| agent_states | 5 | 2.5 KB | 7.5 KB | 0.01 MB |

**Total Storage:** ~22 MB

**Database Tier:** Free tier (500 MB limit) ✅

---

### Scenario 2: Production (Moderate Usage)

**Parameters:**
- Agents: 18 agents
- Tasks: 100 tasks/day per agent
- Duration: 30 days (TTL)
- Q-values: 1,000 unique state-action pairs per agent
- Patterns: 50 patterns per agent

**Calculations:**

```python
# Q-values
q_values_rows = 18 * 1000
q_values_size = q_values_rows * 500
q_values_total = q_values_size * 3

# Trajectories
trajectories_rows = 18 * 100 * 30
trajectories_size = trajectories_rows * 2048
trajectories_total = trajectories_size * 3

# Rewards
rewards_rows = trajectories_rows * 10
rewards_size = rewards_rows * 200
rewards_total = rewards_size * 3

# Patterns
patterns_rows = 18 * 50
patterns_size = patterns_rows * 1024
patterns_total = patterns_size * 3

# Sessions
sessions_rows = trajectories_rows / 10
sessions_size = sessions_rows * 300
sessions_total = sessions_size * 3

# Agent states
agent_states_rows = 18 * 2  # 2 instances per agent
agent_states_size = agent_states_rows * 500
agent_states_total = agent_states_size * 3

total_bytes = (
    q_values_total + trajectories_total + rewards_total +
    patterns_total + sessions_total + agent_states_total
)
total_mb = total_bytes / 1024 / 1024
```

**Results:**

| Table | Rows | Table Size | With Indexes | Total |
|-------|------|------------|--------------|-------|
| q_values | 18,000 | 9 MB | 27 MB | 27 MB |
| trajectories | 54,000 | 108 MB | 324 MB | 324 MB |
| rewards | 540,000 | 108 MB | 324 MB | 324 MB |
| patterns | 900 | 900 KB | 2.7 MB | 2.7 MB |
| sessions | 5,400 | 1.6 MB | 4.8 MB | 4.8 MB |
| agent_states | 36 | 18 KB | 54 KB | 0.05 MB |

**Total Storage:** ~683 MB

**Growth Rate:** ~23 MB/day (trajectories + rewards)

**Database Tier:** Pro tier (8 GB limit) ✅

---

### Scenario 3: High Traffic

**Parameters:**
- Agents: 50 agents
- Tasks: 500 tasks/day per agent
- Duration: 30 days (TTL)
- Q-values: 5,000 unique state-action pairs per agent
- Patterns: 100 patterns per agent

**Calculations:**

```python
# Q-values
q_values_rows = 50 * 5000
q_values_size = q_values_rows * 500
q_values_total = q_values_size * 3

# Trajectories
trajectories_rows = 50 * 500 * 30
trajectories_size = trajectories_rows * 2048
trajectories_total = trajectories_size * 3

# Rewards
rewards_rows = trajectories_rows * 10
rewards_size = rewards_rows * 200
rewards_total = rewards_size * 3

# Patterns
patterns_rows = 50 * 100
patterns_size = patterns_rows * 1024
patterns_total = patterns_size * 3

# Sessions
sessions_rows = trajectories_rows / 10
sessions_size = sessions_rows * 300
sessions_total = sessions_size * 3

# Agent states
agent_states_rows = 50 * 3
agent_states_size = agent_states_rows * 500
agent_states_total = agent_states_size * 3

total_bytes = (
    q_values_total + trajectories_total + rewards_total +
    patterns_total + sessions_total + agent_states_total
)
total_gb = total_bytes / 1024 / 1024 / 1024
```

**Results:**

| Table | Rows | Table Size | With Indexes | Total |
|-------|------|------------|--------------|-------|
| q_values | 250,000 | 125 MB | 375 MB | 375 MB |
| trajectories | 750,000 | 1.5 GB | 4.5 GB | 4.5 GB |
| rewards | 7,500,000 | 1.5 GB | 4.5 GB | 4.5 GB |
| patterns | 5,000 | 5 MB | 15 MB | 15 MB |
| sessions | 75,000 | 22.5 MB | 67.5 MB | 67.5 MB |
| agent_states | 150 | 75 KB | 225 KB | 0.22 MB |

**Total Storage:** ~9.5 GB

**Growth Rate:** ~320 MB/day

**Database Tier:** Team/Scale tier (16-256 GB) ✅

---

## Storage Optimization Strategies

### 1. Reduce TTL (Aggressive Cleanup)

```sql
-- Default: 30 days
-- Reduced: 7 days (saves 76% storage)

UPDATE q_values SET expires_at = NOW() + INTERVAL '7 days';
UPDATE trajectories SET expires_at = NOW() + INTERVAL '7 days';
UPDATE patterns SET expires_at = NOW() + INTERVAL '7 days';
```

**Impact (Scenario 2):**
- Before: 683 MB (30 days)
- After: 164 MB (7 days)
- **Savings:** 76%

### 2. Compress JSONB Data

```sql
-- Store only essential fields, compress verbose data

-- Before (verbose):
'{"module": "authentication", "file": "/src/auth/login.py", "complexity": 5, "coverage": 0.65, "lines": 150, "functions": 8}'

-- After (compressed):
'{"m": "auth", "f": "auth/login.py", "cx": 5, "cv": 0.65}'

-- Saves: ~40% JSONB storage
```

**Impact (Scenario 2):**
- Q-values: 27 MB → 16 MB (40% reduction)
- Trajectories: 324 MB → 194 MB (40% reduction)
- **Savings:** ~140 MB (21%)

### 3. Archive Old Trajectories

```sql
-- Move trajectories > 7 days to cold storage (S3)

-- 1. Export to S3
COPY (
    SELECT * FROM trajectories WHERE completed_at < NOW() - INTERVAL '7 days'
) TO PROGRAM 'aws s3 cp - s3://qlearning-archive/trajectories/2025-11.csv'
WITH CSV HEADER;

-- 2. Delete archived data
DELETE FROM trajectories WHERE completed_at < NOW() - INTERVAL '7 days';

-- 3. Vacuum to reclaim space
VACUUM FULL trajectories;
```

**Impact (Scenario 2):**
- Active data: 7 days (76 MB)
- Archived data: S3 ($0.023/GB/month)
- **Savings:** 248 MB database space

### 4. Partition Trajectories by Month

```sql
-- Partition trajectories table for efficient archival

ALTER TABLE trajectories PARTITION BY RANGE (completed_at);

CREATE TABLE trajectories_2025_11 PARTITION OF trajectories
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE trajectories_2025_12 PARTITION OF trajectories
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- Drop old partitions (instant, no vacuum needed)
DROP TABLE trajectories_2025_10;
```

**Benefit:** Instant archival (no DELETE + VACUUM overhead)

### 5. Sample Rewards (Not All)

```sql
-- Store only 10% of rewards (statistical sampling)

-- Before: 10 rewards per trajectory = 540,000 rows
-- After: 1 reward per trajectory (terminal only) = 54,000 rows

-- Savings: 90% (291 MB)
```

**Trade-off:** Less granular reward analysis, but sufficient for Q-learning

---

## Cost Estimation

### Supabase Pricing

| Tier | Storage | Price | Suitable For |
|------|---------|-------|--------------|
| Free | 500 MB | $0 | Development (< 22 MB) |
| Pro | 8 GB | $25/mo | Production (< 683 MB) |
| Team | 16 GB | $599/mo | High traffic (< 9.5 GB) |
| Scale | 256 GB | Custom | Enterprise (> 10 GB) |

### Self-Hosted Pricing

**Assumptions:**
- AWS RDS PostgreSQL
- db.t3.medium (2 vCPU, 4 GB RAM)
- 100 GB SSD storage

| Component | Cost/Month |
|-----------|------------|
| Compute (db.t3.medium) | $60 |
| Storage (100 GB SSD) | $10 |
| Backup (50 GB) | $5 |
| **Total** | **$75/mo** |

**Cost Comparison (Scenario 2):**
- Supabase Pro: $25/mo (managed)
- Self-hosted: $75/mo (unmanaged)
- **Savings:** $50/mo with Supabase

---

## Monitoring Storage Growth

### Daily Check

```sql
-- Table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size,
    pg_total_relation_size('public.'||tablename) AS bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY bytes DESC;
```

### Weekly Trend

```sql
-- Growth rate (7-day comparison)
WITH current_size AS (
    SELECT SUM(pg_total_relation_size('public.'||tablename)) AS bytes
    FROM pg_tables WHERE schemaname = 'public'
),
historical_size AS (
    -- Stored in monitoring table (create via cron job)
    SELECT bytes FROM storage_history
    WHERE recorded_at = NOW() - INTERVAL '7 days'
)
SELECT
    pg_size_pretty(c.bytes) AS current_size,
    pg_size_pretty(h.bytes) AS size_7d_ago,
    pg_size_pretty(c.bytes - h.bytes) AS growth,
    ROUND((c.bytes - h.bytes) / h.bytes * 100, 2) AS growth_pct
FROM current_size c, historical_size h;
```

### Alert Thresholds

| Condition | Action |
|-----------|--------|
| Storage > 80% of limit | Review TTL, archive old data |
| Growth > 50 MB/day (expected 23 MB) | Investigate anomaly |
| Index bloat > 50% | REINDEX CONCURRENTLY |

---

## Interactive Calculator

Use this Python script to estimate storage for your workload:

```python
#!/usr/bin/env python3
"""
Storage Estimation Calculator for Q-Learning Database
"""

def calculate_storage(
    num_agents: int,
    tasks_per_day: int,
    ttl_days: int,
    q_values_per_agent: int,
    patterns_per_agent: int,
    instances_per_agent: int = 2,
    rewards_per_trajectory: int = 10,
    tasks_per_session: int = 10
):
    """Calculate total storage requirements"""

    # Row counts
    q_values_rows = num_agents * q_values_per_agent
    trajectories_rows = num_agents * tasks_per_day * ttl_days
    rewards_rows = trajectories_rows * rewards_per_trajectory
    patterns_rows = num_agents * patterns_per_agent
    sessions_rows = trajectories_rows / tasks_per_session
    agent_states_rows = num_agents * instances_per_agent

    # Row sizes (bytes)
    q_values_size = 500
    trajectories_size = 2048
    rewards_size = 200
    patterns_size = 1024
    sessions_size = 300
    agent_states_size = 500

    # Table sizes (with 3x index overhead)
    q_values_total = q_values_rows * q_values_size * 3
    trajectories_total = trajectories_rows * trajectories_size * 3
    rewards_total = rewards_rows * rewards_size * 3
    patterns_total = patterns_rows * patterns_size * 3
    sessions_total = sessions_rows * sessions_size * 3
    agent_states_total = agent_states_rows * agent_states_size * 3

    # Total
    total_bytes = (
        q_values_total + trajectories_total + rewards_total +
        patterns_total + sessions_total + agent_states_total
    )

    # Convert to human-readable
    total_mb = total_bytes / 1024 / 1024
    total_gb = total_mb / 1024

    # Growth rate (per day)
    growth_per_day_bytes = (
        (num_agents * tasks_per_day * trajectories_size * 3) +
        (num_agents * tasks_per_day * rewards_per_trajectory * rewards_size * 3)
    )
    growth_per_day_mb = growth_per_day_bytes / 1024 / 1024

    # Print results
    print("=" * 60)
    print("Q-LEARNING DATABASE STORAGE ESTIMATION")
    print("=" * 60)
    print(f"\nWorkload Parameters:")
    print(f"  Agents: {num_agents}")
    print(f"  Tasks per day: {tasks_per_day}")
    print(f"  TTL: {ttl_days} days")
    print(f"  Q-values per agent: {q_values_per_agent:,}")
    print(f"  Patterns per agent: {patterns_per_agent}")
    print(f"\nStorage Breakdown:")
    print(f"  Q-values:     {q_values_total / 1024 / 1024:>10.2f} MB ({q_values_rows:,} rows)")
    print(f"  Trajectories: {trajectories_total / 1024 / 1024:>10.2f} MB ({int(trajectories_rows):,} rows)")
    print(f"  Rewards:      {rewards_total / 1024 / 1024:>10.2f} MB ({int(rewards_rows):,} rows)")
    print(f"  Patterns:     {patterns_total / 1024 / 1024:>10.2f} MB ({patterns_rows:,} rows)")
    print(f"  Sessions:     {sessions_total / 1024 / 1024:>10.2f} MB ({int(sessions_rows):,} rows)")
    print(f"  Agent States: {agent_states_total / 1024 / 1024:>10.2f} MB ({agent_states_rows} rows)")
    print(f"\nTotal Storage:")
    if total_gb > 1:
        print(f"  {total_gb:.2f} GB")
    else:
        print(f"  {total_mb:.2f} MB")
    print(f"\nGrowth Rate:")
    print(f"  {growth_per_day_mb:.2f} MB/day")
    print(f"  {growth_per_day_mb * 30:.2f} MB/month")
    print(f"\nRecommended Tier:")
    if total_mb < 500:
        print("  ✅ Free tier (500 MB limit)")
    elif total_gb < 8:
        print("  ✅ Pro tier (8 GB limit, $25/mo)")
    elif total_gb < 16:
        print("  ✅ Team tier (16 GB limit, $599/mo)")
    else:
        print("  ⚠️  Scale tier (custom pricing)")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    # Example usage
    if len(sys.argv) > 1:
        # Parse arguments
        num_agents = int(sys.argv[1])
        tasks_per_day = int(sys.argv[2])
        ttl_days = int(sys.argv[3])
        q_values_per_agent = int(sys.argv[4])
        patterns_per_agent = int(sys.argv[5])
    else:
        # Default: Scenario 2 (Production)
        num_agents = 18
        tasks_per_day = 100
        ttl_days = 30
        q_values_per_agent = 1000
        patterns_per_agent = 50

    calculate_storage(
        num_agents=num_agents,
        tasks_per_day=tasks_per_day,
        ttl_days=ttl_days,
        q_values_per_agent=q_values_per_agent,
        patterns_per_agent=patterns_per_agent
    )
```

**Usage:**

```bash
# Default (Scenario 2)
python storage_calculator.py

# Custom workload
python storage_calculator.py 50 500 30 5000 100
```

---

## Summary

### Key Takeaways

1. **Development:** ~22 MB (Free tier) ✅
2. **Production:** ~683 MB (Pro tier, $25/mo) ✅
3. **High Traffic:** ~9.5 GB (Team tier, $599/mo) ✅

### Optimization Priority

1. **Reduce TTL:** 30 days → 7 days (76% savings)
2. **Archive Trajectories:** Move old data to S3 (70% savings)
3. **Compress JSONB:** Shorten field names (21% savings)
4. **Sample Rewards:** 10x → 1x per trajectory (90% savings)

### Monitoring

- **Daily:** Check table sizes
- **Weekly:** Review growth trends
- **Monthly:** Archive old data

---

**Last Updated:** 2025-11-05
**Schema Version:** 1.0.0
