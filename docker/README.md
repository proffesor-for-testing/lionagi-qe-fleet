# Docker Compose Setup for LionAGI QE Fleet Q-Learning Development

This directory contains a complete Docker Compose configuration for local Q-Learning development with PostgreSQL, pgAdmin, and optional Redis caching.

## Quick Start

### Prerequisites

- Docker Desktop or Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB free disk space
- Ports 5432, 5050 available (6379 if using Redis)

### One-Command Setup

```bash
# Navigate to docker directory
cd docker

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Verify all services are healthy
docker-compose ps

# View logs
docker-compose logs -f postgres
```

Expected output:
```
NAME                  COMMAND                  SERVICE      STATUS
lionagi-qe-postgres   "docker-entrypoint..."   postgres     Up (healthy)
lionagi-qe-pgadmin    "/entrypoint.sh"         pgadmin      Up (healthy)
```

## Services Overview

### PostgreSQL 16

**Container**: `lionagi-qe-postgres`

The main database for Q-Learning development. Includes:

- **Database**: `lionagi_qe_learning`
- **User**: `qe_agent` (full permissions)
- **Port**: 5432 (exposed)
- **Storage**: `postgres_data` volume (persistent)

**Connection String**:
```
postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
```

**Schemas**:
- `public`: Default schema for application data
- `qlearning`: Q-Learning specific tables (states, episodes, patterns, metrics)
- `qlearning_archive`: Archive storage for historical data

**Key Tables**:
- `qlearning.q_values`: Learned Q-values for test selection
- `qlearning.test_execution_history`: Every test execution record
- `qlearning.agent_learning_episodes`: Agent learning sessions
- `qlearning.test_patterns`: Reusable test patterns
- `qlearning.coverage_snapshots`: Code coverage over time
- `qlearning.agent_performance_metrics`: Agent-level KPIs
- `qlearning.error_log`: Error tracking and diagnostics

### pgAdmin 4

**Container**: `lionagi-qe-pgadmin`

Web-based PostgreSQL management interface.

- **URL**: http://localhost:5050/pgadmin
- **Login**: admin@lionagi.dev / admin_secure_123
- **Port**: 5050 (exposed)
- **Storage**: `pgadmin_data` volume (persistent)

The database is pre-configured and auto-connects on startup.

### Redis (Optional)

**Container**: `lionagi-qe-redis` (profile: `with-redis`)

High-speed cache for Q-values and performance metrics.

- **Port**: 6379 (exposed)
- **Password**: redis_secure_password_123
- **Storage**: `redis_data` volume (persistent)
- **Persistence**: AOF (Append-Only File)

To enable Redis:
```bash
docker-compose --profile with-redis up -d
```

## Configuration

### Environment Variables

Copy and customize `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_DB` | `lionagi_qe_learning` | Database name |
| `POSTGRES_USER` | `qe_agent` | Database user |
| `POSTGRES_PASSWORD` | `qe_secure_password_123` | Database password |
| `POSTGRES_PORT` | `5432` | Exposed port |
| `PGADMIN_EMAIL` | `admin@lionagi.dev` | pgAdmin login |
| `PGADMIN_PASSWORD` | `admin_secure_123` | pgAdmin password |
| `REDIS_PASSWORD` | `redis_secure_password_123` | Redis password |
| `ENABLE_LEARNING` | `true` | Enable Q-Learning |

### Docker Compose Overrides

`docker-compose.override.yml` automatically applies for local development:

- Increased logging verbosity
- Larger log file limits
- Additional development schemas

For production, use explicit composition:
```bash
docker-compose -f docker-compose.yml up -d
```

## Common Commands

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (careful!)
docker-compose down -v

# Restart specific service
docker-compose restart postgres
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail 100 postgres

# With timestamps
docker-compose logs -f -t postgres
```

### Database Access

```bash
# Connect with psql inside container
docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning

# Connect from host (requires psql installed)
psql -h localhost -U qe_agent -d lionagi_qe_learning

# Run SQL file
docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning -f /path/to/query.sql

# Backup database
docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning
```

### Redis Access

```bash
# Connect to Redis (requires with-redis profile)
docker-compose --profile with-redis exec redis redis-cli -a redis_secure_password_123

# Check Redis stats
docker-compose --profile with-redis exec redis redis-cli -a redis_secure_password_123 info

# Flush all data (careful!)
docker-compose --profile with-redis exec redis redis-cli -a redis_secure_password_123 FLUSHALL
```

### Health Checks

```bash
# Check service health
docker-compose ps

# Detailed health status
docker inspect lionagi-qe-postgres | jq '.[] | .State.Health'

# Manual postgres check
docker-compose exec postgres pg_isready -U qe_agent -d lionagi_qe_learning
```

## Python Integration

### SQLAlchemy Connection

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

# Connection string from Docker
DATABASE_URL = "postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    poolclass=NullPool  # Use for connection pooling
)

# Test connection
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print("Database connected!")
```

### Async SQLAlchemy

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Async connection string
DATABASE_URL = "postgresql+asyncpg://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

# Session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Use in async context
async with async_session() as session:
    # Query database
    result = await session.execute("SELECT 1")
```

### Environment Variables in Python

```python
import os
from dotenv import load_dotenv

# Load from parent .env or docker/.env
load_dotenv('../.env')
load_dotenv('.env')

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'lionagi_qe_learning')
DB_USER = os.getenv('POSTGRES_USER', 'qe_agent')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'qe_secure_password_123')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

### Redis Connection (Optional)

```python
import redis
import json

# Connect to Redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    password='redis_secure_password_123',
    db=0,
    decode_responses=True
)

# Store Q-value
q_value = {'agent_id': 'test-gen', 'state': 's1', 'values': [0.5, 0.3, 0.2]}
redis_client.set(f"q_value:{q_value['agent_id']}:{q_value['state']}", json.dumps(q_value))

# Retrieve Q-value
stored = redis_client.get(f"q_value:test-gen:s1")
q_value = json.loads(stored)

# Set expiration (24 hours)
redis_client.expire(f"q_value:test-gen:s1", 86400)
```

## Database Queries

### View Q-Learning Data

```sql
-- All Q-values for an agent
SELECT agent_id, test_category, test_framework,
       action_run_all, action_run_critical, action_run_regression,
       visits, updates, updated_at
FROM qlearning.q_values
WHERE agent_id = 'qe-test-generator'
ORDER BY updated_at DESC;

-- Recent test executions
SELECT test_name, status, duration_ms, started_at
FROM qlearning.test_execution_history
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 50;

-- Agent learning progress
SELECT episode_number, tests_executed, tests_passed,
       ROUND(tests_passed::DECIMAL / tests_executed * 100, 2) as pass_rate,
       coverage_achieved, total_reward, started_at
FROM qlearning.agent_learning_episodes
WHERE agent_id = 'qe-test-generator'
AND status = 'completed'
ORDER BY episode_number DESC
LIMIT 20;

-- Test failure analysis
SELECT test_name, test_category,
       COUNT(*) as failures,
       ROUND(AVG(duration_ms), 2) as avg_duration_ms
FROM qlearning.test_execution_history
WHERE status = 'failed'
AND created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY test_name, test_category
ORDER BY failures DESC;

-- Coverage trends
SELECT snapshot_date, coverage_percentage,
       LAG(coverage_percentage) OVER (ORDER BY snapshot_date) as prev_coverage,
       ROUND(coverage_percentage - LAG(coverage_percentage) OVER (ORDER BY snapshot_date), 2) as delta
FROM qlearning.coverage_snapshots
WHERE agent_id = 'qe-test-generator'
ORDER BY snapshot_date DESC
LIMIT 30;
```

### Admin Operations

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('lionagi_qe_learning')) as database_size;

-- Check table sizes
SELECT relname as table_name,
       pg_size_pretty(pg_total_relation_size(relid)) as size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- View active connections
SELECT datname, count(*) as connections
FROM pg_stat_activity
GROUP BY datname
ORDER BY connections DESC;

-- Check schema objects
SELECT schema_name, COUNT(*) as object_count
FROM information_schema.schemata s
LEFT JOIN information_schema.tables t ON s.schema_name = t.table_schema
GROUP BY schema_name;

-- Get recent slow queries (requires log_min_duration_statement)
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Development Utilities

```sql
-- Reset development database
SELECT qlearning.dev_reset_database(false);  -- Keep patterns
SELECT qlearning.dev_reset_database(true);   -- Remove everything

-- Get recent stats (last 24 hours)
SELECT * FROM qlearning.get_recent_stats(24);

-- View helpful query examples
SELECT query_name, category, description, sql_query
FROM qlearning.dev_query_examples
ORDER BY category, query_name;

-- Archive old data (keep last 90 days)
CALL qlearning.archive_old_data(90);

-- Clean ineffective patterns
CALL qlearning.cleanup_ineffective_patterns(20.0);
```

## Performance Tuning

### PostgreSQL Performance

The compose file includes recommended defaults:

```yaml
POSTGRES_INITDB_ARGS: "-c shared_buffers=256MB -c max_connections=200"
```

For different environments, customize `.env`:

**Development**:
```
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_MAX_CONNECTIONS=200
```

**Production**:
```
POSTGRES_SHARED_BUFFERS=1GB
POSTGRES_MAX_CONNECTIONS=500
```

### Connection Pooling

Recommended settings for applications:

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Size of pool to keep
    max_overflow=20,        # How many additional beyond pool_size
    pool_recycle=3600,      # Recycle connections every hour
    pool_pre_ping=True      # Test connections before use
)
```

### Redis Performance

For high-speed Q-value caching:

```bash
# Monitor Redis memory
docker-compose --profile with-redis exec redis redis-cli -a redis_secure_password_123 info memory

# Set max memory policy
docker-compose --profile with-redis exec redis redis-cli -a redis_secure_password_123 CONFIG SET maxmemory-policy allkeys-lru
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs postgres

# Common issues:
# - Port already in use: Change POSTGRES_PORT in .env
# - Insufficient disk space: Clean up with 'docker system prune'
# - Permission denied: Run with 'sudo' or fix Docker daemon
```

### Database Connection Issues

```bash
# Test connectivity
docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT 1"

# Check network
docker network inspect docker_lionagi-qe-network

# Verify credentials
echo $POSTGRES_USER $POSTGRES_PASSWORD
```

### Performance Issues

```bash
# Check active connections
docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "\du"

# Kill long-running queries
docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'lionagi_qe_learning' AND pid != pg_backend_pid();"

# Analyze tables
docker-compose exec postgres psql -U qe_agent -d lionagi_qe_learning -c "ANALYZE;"
```

### pgAdmin Not Accessible

```bash
# Check pgAdmin health
docker-compose exec pgadmin wget --spider -q http://localhost/pgadmin/misc/ping

# Check logs
docker-compose logs pgadmin

# Restart service
docker-compose restart pgadmin
```

## Data Backup and Restore

### Backup

```bash
# Full database backup
docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Schema only
docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning --schema-only > schema_$(date +%Y%m%d_%H%M%S).sql

# Data only (no schema)
docker-compose exec -T postgres pg_dump -U qe_agent -d lionagi_qe_learning --data-only > data_$(date +%Y%m%d_%H%M%S).sql
```

### Restore

```bash
# From SQL file
cat backup.sql | docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning

# From compressed backup
zcat backup.sql.gz | docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_learning

# Into new database
docker-compose exec postgres createdb -U qe_agent lionagi_qe_test
cat backup.sql | docker-compose exec -T postgres psql -U qe_agent -d lionagi_qe_test
```

## Directory Structure

```
docker/
├── docker-compose.yml          # Main compose file
├── docker-compose.override.yml # Development overrides
├── .env.example                # Environment template
├── README.md                    # This file
├── postgres/
│   ├── init.sql               # PostgreSQL initialization
│   ├── schema.sql             # Q-Learning schema
│   └── dev-schema.sql         # Development tables
├── pgadmin/
│   └── servers.json           # pgAdmin server config
└── Makefile                    # Optional convenience commands
```

## Advanced Usage

### Custom Docker Network

Connect external services to the same network:

```bash
# List containers on network
docker network inspect docker_lionagi-qe-network

# Connect external container
docker network connect docker_lionagi-qe-network my-container
```

### Scaling PostgreSQL

For multi-instance setup, use `docker-compose` service extensions:

```yaml
postgres-replica:
  image: postgres:16-alpine
  environment:
    POSTGRES_REPLICATION_MODE: slave
    POSTGRES_REPLICATION_USER: replicator
    POSTGRES_REPLICATION_PASSWORD: secret
```

### Monitoring with Prometheus

Add a Prometheus service for metrics collection:

```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://qe_agent:password@postgres:5432/lionagi_qe_learning?sslmode=disable"
  ports:
    - "9187:9187"
```

## Production Considerations

1. **Security**:
   - Change all default passwords
   - Use strong credentials (min 16 chars, mixed case, numbers, special)
   - Disable pgAdmin for production
   - Enable SSL/TLS for connections

2. **Data**:
   - Enable regular backups
   - Use external volume drivers for persistence
   - Set up replication for HA
   - Monitor storage usage

3. **Performance**:
   - Tune PostgreSQL parameters for workload
   - Use separate volumes for logs and data
   - Implement connection pooling at app level
   - Monitor slow query logs

4. **Maintenance**:
   - Schedule regular VACUUM and ANALYZE
   - Archive old test execution data quarterly
   - Monitor application error logs
   - Plan capacity for growth

## Support and Documentation

- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/)
- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [LionAGI QE Fleet Documentation](../README.md)

## License

This Docker configuration is part of the LionAGI QE Fleet project. See LICENSE for details.
