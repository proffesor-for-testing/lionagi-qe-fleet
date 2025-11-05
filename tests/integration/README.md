# Integration Tests - Real Database Testing

This directory contains **real integration tests** for PostgreSQL and Redis memory backends. Unlike the mocked unit tests, these tests use actual databases and verify end-to-end functionality.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Files](#test-files)
- [Setup Requirements](#setup-requirements)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Performance Benchmarks](#performance-benchmarks)
- [Troubleshooting](#troubleshooting)

## Overview

### What These Tests Do

1. **Real Database Operations**: Connect to actual PostgreSQL and Redis instances
2. **Integration Testing**: Test agents using real memory backends
3. **Concurrent Access**: Verify thread-safety and connection pooling
4. **Performance Testing**: Measure actual database performance
5. **End-to-End Scenarios**: Test complete agent coordination workflows

### What Makes These Different

| Aspect | Unit Tests (Mocked) | Integration Tests (Real) |
|--------|---------------------|--------------------------|
| **Database** | AsyncMock | Real PostgreSQL/Redis |
| **Speed** | Fast (<1s) | Slower (5-30s) |
| **Isolation** | Complete | Database-level |
| **Coverage** | API contracts | Actual behavior |
| **Dependencies** | None | Docker containers |

## Quick Start

```bash
# 1. Start test databases
docker-compose -f docker-compose-test.yml up -d

# 2. Wait for databases to be ready (5-10 seconds)
docker-compose -f docker-compose-test.yml ps

# 3. Run all integration tests
pytest tests/integration -v -m integration

# 4. Cleanup
docker-compose -f docker-compose-test.yml down -v
```

## Test Files

### `test_postgres_memory_integration.py`

Real PostgreSQL integration tests covering:

- **Basic Operations** (8 tests): Store, retrieve, delete, overwrite
- **TTL Expiration** (4 tests): Real-time TTL testing, expiration verification
- **Pattern Search** (4 tests): SQL LIKE patterns, wildcard matching
- **Partitions** (2 tests): Partition isolation, clearing
- **Key Listing** (2 tests): Prefix filtering, sorting
- **Statistics** (2 tests): Key counts, size calculations
- **Concurrency** (3 tests): Concurrent reads/writes, thread safety
- **Performance** (2 tests): Bulk operations, search performance
- **Namespace** (2 tests): Namespace enforcement
- **Cleanup** (1 test): Expired entry cleanup

**Total: 30 tests**

### `test_redis_memory_integration.py`

Real Redis integration tests covering:

- **Basic Operations** (8 tests): Store, retrieve, delete, complex data
- **TTL Expiration** (4 tests): Redis native TTL, auto-expiration
- **Pattern Search** (4 tests): Redis SCAN patterns, wildcard matching
- **Partitions** (2 tests): Partition metadata, clearing
- **Key Listing** (3 tests): Prefix filtering, sorting
- **Statistics** (2 tests): Memory usage, Redis INFO stats
- **Concurrency** (3 tests): Atomic operations, concurrent access
- **Performance** (3 tests): Write/read/search performance
- **Persistence** (2 tests): AOF persistence, metadata preservation
- **Connection Pool** (2 tests): Pool reuse, load handling
- **Cleanup** (2 tests): Auto-expiration, connection closing

**Total: 35 tests**

### `test_agent_memory_e2e.py`

End-to-end agent tests covering:

- **PostgreSQL E2E** (4 tests): Agent storage, coordination, fleet patterns, Q-learning
- **Redis E2E** (4 tests): High-frequency coordination, caching, sessions
- **Hybrid Memory** (2 tests): PostgreSQL + Redis together, data migration
- **Concurrent Agents** (3 tests): Multiple agents, shared data, work queues
- **Resilience** (2 tests): Error handling, backend isolation

**Total: 15 tests**

### `conftest.py`

Integration test fixtures:

- **Database Fixtures**: Real PostgreSQL and Redis connections
- **Performance Tracking**: Timing and metrics
- **Concurrent Executors**: Stress testing utilities
- **Health Checks**: Automatic database availability verification

## Setup Requirements

### Docker (Required)

```bash
# Verify Docker is installed
docker --version
docker-compose --version
```

### Python Dependencies

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock
pip install asyncpg redis  # Database drivers
```

### Database Schema

The PostgreSQL container automatically runs schema migrations:

1. `learning.sql` - Q-learning tables
2. `memory_extension.sql` - qe_memory table

### Ports

Ensure these ports are available:

- **5433**: PostgreSQL test instance
- **6380**: Redis test instance

## Running Tests

### Run All Integration Tests

```bash
pytest tests/integration -v -m integration
```

### Run PostgreSQL Tests Only

```bash
pytest tests/integration/test_postgres_memory_integration.py -v -m postgres
```

### Run Redis Tests Only

```bash
pytest tests/integration/test_redis_memory_integration.py -v -m redis
```

### Run E2E Tests

```bash
pytest tests/integration/test_agent_memory_e2e.py -v
```

### Run Specific Test Class

```bash
pytest tests/integration -v -k TestPostgresMemoryRealBasicOperations
```

### Skip Slow Tests

```bash
pytest tests/integration -v -m "integration and not slow"
```

### Run with Coverage

```bash
pytest tests/integration -v -m integration --cov=src/lionagi_qe/persistence --cov-report=html
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/integration -v -m integration -n auto
```

## Test Coverage

### What's Tested

#### PostgreSQL Backend

- [x] Store and retrieve operations
- [x] TTL expiration (real-time)
- [x] Pattern-based search (SQL LIKE)
- [x] Partition management
- [x] Key listing and filtering
- [x] Statistics and metrics
- [x] Concurrent access (100+ operations)
- [x] Connection pooling
- [x] Namespace enforcement
- [x] Cleanup operations
- [x] Performance under load

#### Redis Backend

- [x] Store and retrieve operations
- [x] Native TTL (auto-expiration)
- [x] Pattern-based search (SCAN)
- [x] Partition management
- [x] Key listing and sorting
- [x] Redis INFO statistics
- [x] Concurrent access (100+ operations)
- [x] Connection pooling
- [x] AOF persistence
- [x] Atomic operations
- [x] Performance benchmarks

#### Agent Integration

- [x] Agents store results in databases
- [x] Cross-agent coordination
- [x] Fleet coordination patterns
- [x] Q-learning persistence
- [x] High-frequency updates
- [x] Cache patterns
- [x] Session management
- [x] Hybrid PostgreSQL + Redis
- [x] Data migration
- [x] Work queue patterns
- [x] Error resilience
- [x] Backend isolation

### Coverage Report

Generate HTML coverage report:

```bash
pytest tests/integration -v -m integration \
  --cov=src/lionagi_qe/persistence \
  --cov-report=html

open htmlcov/index.html
```

Expected coverage: **85-95%** of persistence layer

## Performance Benchmarks

### Expected Performance (Approximate)

#### PostgreSQL

| Operation | Throughput | Latency |
|-----------|------------|---------|
| Write | 10-50 ops/s | 20-100ms |
| Read | 50-200 ops/s | 5-20ms |
| Search (50 keys) | N/A | <1s |
| Concurrent (50 ops) | N/A | 2-5s |

#### Redis

| Operation | Throughput | Latency |
|-----------|------------|---------|
| Write | 100-500 ops/s | 2-10ms |
| Read | 200-1000 ops/s | 1-5ms |
| Search (50 keys) | N/A | <0.5s |
| Concurrent (50 ops) | N/A | 1-2s |

### Running Performance Tests

```bash
# Run only performance tests
pytest tests/integration -v -m "integration and slow"

# Run with detailed output
pytest tests/integration -v -m "integration and slow" -s
```

### Benchmarking

```bash
# Create custom benchmark
pytest tests/integration/test_postgres_memory_integration.py::TestPostgresMemoryRealPerformance -v -s

# Time all tests
pytest tests/integration -v --durations=10
```

## Troubleshooting

### Tests Fail with Connection Error

**Problem**: Cannot connect to PostgreSQL or Redis

**Solution**:

```bash
# Check if containers are running
docker-compose -f docker-compose-test.yml ps

# Check container logs
docker-compose -f docker-compose-test.yml logs postgres-test
docker-compose -f docker-compose-test.yml logs redis-test

# Restart containers
docker-compose -f docker-compose-test.yml down -v
docker-compose -f docker-compose-test.yml up -d

# Wait for health checks
sleep 10
```

### Port Already in Use

**Problem**: Port 5433 or 6380 already in use

**Solution**:

```bash
# Find process using port
lsof -i :5433
lsof -i :6380

# Kill the process or change ports in docker-compose-test.yml
```

### Schema Not Found

**Problem**: PostgreSQL schema not initialized

**Solution**:

```bash
# Verify schema files exist
ls src/lionagi_qe/learning/schema/

# Recreate containers (will re-run schema)
docker-compose -f docker-compose-test.yml down -v
docker-compose -f docker-compose-test.yml up -d
```

### Tests Hang

**Problem**: Tests hang or timeout

**Solution**:

```bash
# Increase pytest timeout
pytest tests/integration -v --timeout=60

# Check for deadlocks in PostgreSQL
docker exec lionagi-qe-postgres-test psql -U qe_agent_test -d lionagi_qe_test -c "SELECT * FROM pg_stat_activity;"
```

### Cleanup Issues

**Problem**: Test data persists between runs

**Solution**:

```bash
# Use clean fixtures
# postgres_memory_clean auto-cleans aqe/test/* keys

# Manual cleanup
docker exec lionagi-qe-postgres-test psql -U qe_agent_test -d lionagi_qe_test -c "DELETE FROM qe_memory WHERE key LIKE 'aqe/test/%';"

docker exec lionagi-qe-redis-test redis-cli FLUSHDB
```

### Slow Test Execution

**Problem**: Tests take too long

**Solution**:

```bash
# Skip slow tests
pytest tests/integration -v -m "integration and not slow"

# Run in parallel
pytest tests/integration -v -m integration -n 4

# Profile tests
pytest tests/integration -v --durations=20
```

### Redis Connection Pool Exhausted

**Problem**: Too many connections to Redis

**Solution**:

```python
# Increase max_connections in fixtures
memory = RedisMemory(
    host=TEST_REDIS_HOST,
    port=TEST_REDIS_PORT,
    max_connections=20  # Increase from 10
)
```

### PostgreSQL Connection Pool Exhausted

**Problem**: Connection pool max size reached

**Solution**:

```python
# Increase pool size
db_manager = DatabaseManager(
    database_url=TEST_POSTGRES_URL,
    min_connections=2,
    max_connections=20  # Increase from 10
)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: qe_agent_test
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: lionagi_qe_test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6380:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install pytest pytest-asyncio pytest-mock asyncpg redis

      - name: Run integration tests
        run: pytest tests/integration -v -m integration --junitxml=results.xml

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: results.xml
```

## Additional Resources

- **PostgreSQL Docs**: [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- **Redis Docs**: [Redis Commands](https://redis.io/commands)
- **pytest-asyncio**: [Async Testing Guide](https://pytest-asyncio.readthedocs.io/)
- **Integration Testing**: [Martin Fowler's Guide](https://martinfowler.com/bliki/IntegrationTest.html)

## Contributing

When adding new integration tests:

1. Mark with `@pytest.mark.integration`
2. Mark database-specific tests with `@pytest.mark.postgres` or `@pytest.mark.redis`
3. Mark slow tests (>5s) with `@pytest.mark.slow`
4. Use appropriate fixtures (`postgres_memory_real`, `redis_memory_real`, etc.)
5. Clean up test data (fixtures handle this automatically)
6. Add docstrings explaining what's being tested
7. Include performance assertions where relevant

---

**Total Integration Test Count**: 80 real integration tests

**Test Execution Time**: ~60-120 seconds (depends on hardware)

**Database Coverage**: 85-95%
