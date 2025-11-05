"""Integration test fixtures for real PostgreSQL and Redis backends

These fixtures provide real database connections for integration testing.
They require docker-compose-test.yml to be running.

Usage:
    # Start test databases
    docker-compose -f docker-compose-test.yml up -d

    # Run integration tests
    pytest tests/integration -m integration

    # Cleanup
    docker-compose -f docker-compose-test.yml down -v
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from lionagi_qe.learning.db_manager import DatabaseManager
from lionagi_qe.persistence.postgres_memory import PostgresMemory
from lionagi_qe.persistence.redis_memory import RedisMemory


# ============================================================================
# Environment Configuration
# ============================================================================

TEST_POSTGRES_URL = os.getenv(
    "TEST_POSTGRES_URL",
    "postgresql://qe_agent_test:test_password@localhost:5433/lionagi_qe_test"
)

TEST_REDIS_HOST = os.getenv("TEST_REDIS_HOST", "localhost")
TEST_REDIS_PORT = int(os.getenv("TEST_REDIS_PORT", "6380"))
TEST_REDIS_DB = int(os.getenv("TEST_REDIS_DB", "0"))


# ============================================================================
# PostgreSQL Integration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def postgres_db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """Create real DatabaseManager for integration tests

    This is a session-scoped fixture that creates a single connection pool
    shared across all PostgreSQL integration tests.
    """
    db_manager = DatabaseManager(
        database_url=TEST_POSTGRES_URL,
        min_connections=2,
        max_connections=10
    )

    # Connect to database
    await db_manager.connect()

    yield db_manager

    # Cleanup
    await db_manager.disconnect()


@pytest.fixture
async def postgres_memory_real(postgres_db_manager) -> AsyncGenerator[PostgresMemory, None]:
    """Create real PostgresMemory instance for integration tests

    This fixture provides a clean PostgresMemory instance for each test.
    It cleans up all test data after the test completes.
    """
    memory = PostgresMemory(postgres_db_manager)

    # Track keys created during test for cleanup
    created_keys = []

    # Wrap store method to track keys
    original_store = memory.store

    async def tracking_store(key: str, *args, **kwargs):
        created_keys.append(key)
        return await original_store(key, *args, **kwargs)

    memory.store = tracking_store

    yield memory

    # Cleanup: delete all keys created during test
    for key in created_keys:
        try:
            await memory.delete(key)
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture
async def postgres_memory_clean(postgres_db_manager) -> AsyncGenerator[PostgresMemory, None]:
    """Create PostgresMemory with explicit cleanup of test namespace

    This fixture clears all keys matching 'aqe/test/%' before and after each test.
    Use this when you need a completely clean slate.
    """
    memory = PostgresMemory(postgres_db_manager)

    # Cleanup before test
    async with postgres_db_manager.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM qe_memory WHERE key LIKE 'aqe/test/%'"
        )

    yield memory

    # Cleanup after test
    async with postgres_db_manager.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM qe_memory WHERE key LIKE 'aqe/test/%'"
        )


# ============================================================================
# Redis Integration Fixtures
# ============================================================================

@pytest.fixture
async def redis_memory_real() -> AsyncGenerator[RedisMemory, None]:
    """Create real RedisMemory instance for integration tests

    This fixture provides a clean RedisMemory instance for each test.
    It uses a separate Redis database (configurable via TEST_REDIS_DB)
    and flushes it before and after each test.
    """
    memory = RedisMemory(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB,
        max_connections=10
    )

    # Flush database before test
    memory.client.flushdb()

    yield memory

    # Flush database after test
    memory.client.flushdb()

    # Close connection
    memory.close()


@pytest.fixture
async def redis_memory_persistent() -> AsyncGenerator[RedisMemory, None]:
    """Create RedisMemory that persists data across tests

    This fixture does NOT flush the database before/after tests.
    Use this for testing data persistence and cross-test coordination.
    """
    memory = RedisMemory(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB + 1,  # Use different DB to avoid conflicts
        max_connections=10
    )

    yield memory

    # Only close connection, don't flush
    memory.close()


# ============================================================================
# Shared Test Data
# ============================================================================

@pytest.fixture
def integration_test_data():
    """Sample data for integration tests"""
    return {
        "simple": {"value": "test", "count": 42},
        "nested": {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        },
        "list_data": {
            "items": [1, 2, 3, 4, 5],
            "names": ["alpha", "beta", "gamma"]
        },
        "complex": {
            "tests": [
                {"name": "test_one", "status": "passed"},
                {"name": "test_two", "status": "failed"}
            ],
            "metadata": {
                "framework": "pytest",
                "coverage": 0.85
            }
        }
    }


@pytest.fixture
def large_test_data():
    """Large dataset for performance testing"""
    return {
        "bulk_items": [
            {"id": i, "name": f"item_{i}", "value": i * 10}
            for i in range(1000)
        ]
    }


# ============================================================================
# Connection Health Checks
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
async def check_test_databases():
    """Verify test databases are available before running tests

    This fixture runs automatically at session start and verifies:
    - PostgreSQL is reachable and has required schema
    - Redis is reachable and responding

    If databases are not available, tests will be skipped with clear message.
    """
    errors = []

    # Check PostgreSQL
    try:
        db_manager = DatabaseManager(
            database_url=TEST_POSTGRES_URL,
            min_connections=1,
            max_connections=2
        )
        await db_manager.connect()

        # Verify qe_memory table exists
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'qe_memory'
                )
                """
            )
            if not result:
                errors.append(
                    "PostgreSQL: qe_memory table not found. "
                    "Run schema migrations."
                )

        await db_manager.disconnect()
    except Exception as e:
        errors.append(f"PostgreSQL connection failed: {e}")

    # Check Redis
    try:
        redis_memory = RedisMemory(
            host=TEST_REDIS_HOST,
            port=TEST_REDIS_PORT,
            db=TEST_REDIS_DB
        )
        redis_memory.client.ping()
        redis_memory.close()
    except Exception as e:
        errors.append(f"Redis connection failed: {e}")

    if errors:
        pytest.skip(
            "Integration test databases not available:\n" +
            "\n".join(f"  - {err}" for err in errors) +
            "\n\nStart databases with: docker-compose -f docker-compose-test.yml up -d"
        )


# ============================================================================
# Performance Monitoring
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Track test performance metrics"""
    import time

    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.operations = []

        def start(self):
            self.start_time = time.time()

        def end(self):
            self.end_time = time.time()

        def record_operation(self, name: str, duration: float):
            self.operations.append({"name": name, "duration": duration})

        @property
        def total_duration(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def report(self) -> dict:
            return {
                "total_duration": self.total_duration,
                "operations": self.operations,
                "operation_count": len(self.operations)
            }

    tracker = PerformanceTracker()
    tracker.start()

    yield tracker

    tracker.end()


# ============================================================================
# Concurrent Access Helpers
# ============================================================================

@pytest.fixture
def concurrent_executor():
    """Helper for running concurrent operations"""

    class ConcurrentExecutor:
        @staticmethod
        async def run_concurrent(operations: list, batch_size: int = 10):
            """Run operations concurrently in batches"""
            results = []
            for i in range(0, len(operations), batch_size):
                batch = operations[i:i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                results.extend(batch_results)
            return results

        @staticmethod
        async def stress_test(operation, iterations: int, concurrency: int):
            """Stress test an operation"""
            tasks = [operation() for _ in range(iterations)]

            # Run with limited concurrency
            semaphore = asyncio.Semaphore(concurrency)

            async def bounded_operation(op):
                async with semaphore:
                    return await op

            results = await asyncio.gather(
                *[bounded_operation(task) for task in tasks],
                return_exceptions=True
            )

            return results

    return ConcurrentExecutor()
