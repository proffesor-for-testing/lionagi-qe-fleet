# Docker Q-Learning Setup - Quick Start Guide

## 5-Minute Setup

### Step 1: Copy Environment File (30 seconds)

```bash
cd docker
cp .env.example .env
```

### Step 2: Start Services (1 minute)

```bash
# Option A: Basic setup (PostgreSQL + pgAdmin)
docker-compose up -d

# Option B: Full setup (PostgreSQL + pgAdmin + Redis)
docker-compose --profile with-redis up -d
```

### Step 3: Verify Services (1 minute)

```bash
# Check if all services are running
docker-compose ps

# Wait for health checks (should show "healthy" status)
docker-compose ps | grep postgres
```

### Step 4: Access Services (1 minute)

**PostgreSQL** - Direct connection:
```bash
make psql
# Or: docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning
```

**pgAdmin** - Web UI:
```bash
# Opens browser automatically
make pgadmin

# Or visit: http://localhost:5050/pgadmin
# Login: admin@lionagi.dev / admin_secure_123
```

## Verification Checklist

- [ ] `docker-compose ps` shows 3 services (postgres, pgadmin, optionally redis)
- [ ] All services show "healthy" status
- [ ] PostgreSQL accepts connections: `make test-db`
- [ ] pgAdmin accessible at http://localhost:5050/pgadmin
- [ ] Can run SQL: `make psql-` followed by `SELECT 1;`

## Next Steps

### Option 1: Test Database Connectivity from Python

```bash
cd ..
python docker/python-examples.py test-postgres
```

### Option 2: Explore Database Schema

```bash
# View all Q-Learning tables
make psql-"SELECT tablename FROM pg_tables WHERE schemaname = 'qlearning';"

# Check database size
make psql-"SELECT pg_size_pretty(pg_database_size('lionagi_qe_learning'));"
```

### Option 3: Run Sample Queries

```bash
# View sample data loaded in dev-schema
make psql-"SELECT agent_id, test_category, test_framework, visits FROM qlearning.q_values;"

# Get recent stats function
make psql-"SELECT * FROM qlearning.get_recent_stats(24);"
```

## Troubleshooting

### Services Won't Start

**Error**: `Error response from daemon: driver failed programming external connectivity on endpoint...`

**Solution**: Port already in use
```bash
# Change port in .env
POSTGRES_PORT=5433  # Changed from 5432

# Restart services
docker-compose down
docker-compose up -d
```

### PostgreSQL Connection Refused

**Error**: `could not connect to server: Connection refused`

**Solution**: PostgreSQL not healthy yet
```bash
# Wait a bit longer
sleep 10
docker-compose ps  # Check health status

# View logs
docker-compose logs postgres
```

### pgAdmin Can't Connect to Database

**Error**: `unable to connect to server: could not translate host name "postgres"...`

**Solution**: Network issue (usually resolves itself)
```bash
# Restart pgAdmin
docker-compose restart pgadmin

# Check network
docker network inspect docker_lionagi-qe-network
```

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Just PostgreSQL
docker-compose logs -f postgres

# Just pgAdmin
docker-compose logs -f pgadmin
```

### Backup Database

```bash
# Simple backup
make backup

# Compressed backup (smaller file)
make backup-gz

# Schema only
make backup-schema
```

### Reset Database

```bash
# Clear test data (keep patterns)
make reset

# Clear everything (CAREFUL!)
make reset-all
```

### Stop Services

```bash
# Stop but keep data
docker-compose down

# Stop and delete everything
docker-compose down -v
```

## Connection Strings

### PostgreSQL

**Standard (psycopg2)**:
```
postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
```

**Async (asyncpg)**:
```
postgresql+asyncpg://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
```

**Command line (psql)**:
```bash
psql -h localhost -U qe_agent -d lionagi_qe_learning
# Password: qe_secure_password_123
```

### Redis (if enabled)

**Redis**:
```
redis://:redis_secure_password_123@localhost:6379/0
```

**Python redis-py**:
```python
import redis
r = redis.Redis(host='localhost', port=6379, password='redis_secure_password_123')
```

## Database Schemas Overview

### `public` (Default)
Standard PostgreSQL public schema for application data.

### `qlearning` (Main)
All Q-Learning tables:
- `q_values` - Learned Q-values for test selection
- `test_execution_history` - Test execution records
- `agent_learning_episodes` - Learning sessions
- `test_patterns` - Reusable patterns
- `coverage_snapshots` - Coverage trends
- `agent_performance_metrics` - Agent KPIs
- `error_log` - Error tracking

### `qlearning_archive`
Historical data archive (created on first archival).

### `dev_*` Tables (Development Only)
- `dev_test_runs` - Local test run logging
- `dev_query_examples` - Helpful query templates

## Sample Query

Get agent learning progress over last 10 episodes:

```sql
SELECT
    episode_number,
    tests_executed,
    tests_passed,
    ROUND(tests_passed::DECIMAL / tests_executed * 100, 2) as pass_rate,
    coverage_achieved,
    total_reward,
    started_at
FROM qlearning.agent_learning_episodes
WHERE agent_id = 'qe-test-generator'
AND status = 'completed'
ORDER BY episode_number DESC
LIMIT 10;
```

Run with:
```bash
docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning << EOF
[paste query here]
EOF
```

## Performance Tips

### PostgreSQL Performance

Current defaults are optimized for development. For better performance:

```bash
# Edit .env to increase:
POSTGRES_SHARED_BUFFERS=512MB    # For larger workloads
POSTGRES_MAX_CONNECTIONS=500     # For more concurrent connections
```

Then restart: `docker-compose restart postgres`

### Redis Performance

Monitor Redis memory:
```bash
docker-compose --profile with-redis exec redis redis-cli -a redis_secure_password_123 info memory
```

### Connection Pooling

Always use connection pooling in production code:

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Keep 10 connections in pool
    max_overflow=20,        # Allow up to 20 more
    pool_recycle=3600,      # Recycle every hour
    pool_pre_ping=True      # Test before use
)
```

## What's in Each File

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main service definitions |
| `docker-compose.override.yml` | Development overrides |
| `.env.example` | Environment template |
| `Makefile` | Convenience commands |
| `README.md` | Complete documentation |
| `postgres/init.sql` | Initial setup script |
| `postgres/schema.sql` | Q-Learning database schema |
| `postgres/dev-schema.sql` | Development utilities |
| `pgadmin/servers.json` | pgAdmin configuration |
| `python-examples.py` | Python connection examples |

## Getting Help

### View Logs
```bash
docker-compose logs [service-name]
```

### Check Health
```bash
docker-compose ps
```

### Run Direct Commands
```bash
docker-compose exec postgres [command]
docker-compose exec pgadmin [command]
```

### Full Documentation
See `README.md` for comprehensive documentation.

## Next: Integration with Your Code

After setup, integrate Q-Learning into your agents:

```python
from sqlalchemy import create_engine
from lionagi_qe.core.fleet import QEFleet

# Configure database
DATABASE_URL = "postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning"
engine = create_engine(DATABASE_URL, pool_size=10)

# Initialize fleet with learning enabled
fleet = QEFleet(enable_learning=True)
await fleet.initialize()

# Fleet now tracks all Q-values and learning episodes in the database
```

For more examples, see:
- `python-examples.py` - Connection examples
- `README.md` - Integration guide
- `CLAUDE.md` - Agent framework overview

---

**Stuck?** Check the Troubleshooting section in `README.md` or run:
```bash
make help
```
