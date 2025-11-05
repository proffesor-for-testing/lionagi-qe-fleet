"""Shared pytest fixtures for persistence tests

This module provides fixtures for testing PostgreSQL and Redis memory backends:
- Database connection pools and managers
- Memory backend instances
- Sample test data
- Cleanup utilities
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, timedelta


# ============================================================================
# PostgreSQL Fixtures
# ============================================================================

@pytest.fixture
def mock_asyncpg_pool(mocker):
    """Mock asyncpg connection pool for PostgresMemory tests"""
    pool = mocker.AsyncMock()

    # Mock connection context manager
    conn = mocker.AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.fetchval = AsyncMock(return_value=None)

    # Pool acquire context manager
    pool.acquire = Mock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=conn), __aexit__=AsyncMock()))
    pool.close = AsyncMock()

    return pool


@pytest.fixture
async def mock_db_manager_for_memory(mocker, mock_asyncpg_pool):
    """Mock DatabaseManager for memory backend tests"""
    # Create a mock DatabaseManager without importing
    manager = mocker.Mock()
    manager.database_url = "postgresql://test:test@localhost:5432/test_db"
    manager.pool = mock_asyncpg_pool
    manager.connect = AsyncMock()
    manager.disconnect = AsyncMock()
    manager.get_q_value = AsyncMock(return_value=None)
    manager.upsert_q_value = AsyncMock(return_value=1)

    return manager


@pytest.fixture
def postgres_memory_config():
    """Configuration for PostgresMemory"""
    return {
        "database_url": "postgresql://test:test@localhost:5432/test_db",
        "min_connections": 2,
        "max_connections": 10,
        "command_timeout": 60,
        "namespace_prefix": "aqe/"
    }


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture
def mock_redis_client(mocker):
    """Mock Redis client for RedisMemory tests"""
    redis = mocker.AsyncMock()

    # Mock Redis commands
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.keys = AsyncMock(return_value=[])
    redis.scan = AsyncMock(return_value=(0, []))
    redis.dbsize = AsyncMock(return_value=0)
    redis.info = AsyncMock(return_value={"used_memory": 1024})
    redis.close = AsyncMock()

    return redis


@pytest.fixture
def redis_memory_config():
    """Configuration for RedisMemory"""
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,
        "namespace_prefix": "aqe:",
        "decode_responses": True
    }


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_memory_data():
    """Sample data for memory storage tests"""
    return {
        "simple_value": {"test": "data", "count": 42},
        "test_plan": {
            "framework": "pytest",
            "tests": ["test_add", "test_subtract"],
            "coverage_target": 0.95
        },
        "coverage_results": {
            "total_lines": 100,
            "covered_lines": 85,
            "percentage": 0.85,
            "uncovered_files": ["module_a.py", "module_b.py"]
        },
        "quality_metrics": {
            "complexity": 5,
            "maintainability": 0.8,
            "test_count": 50,
            "mutation_score": 0.75
        }
    }


@pytest.fixture
def sample_aqe_keys():
    """Sample AQE namespace keys for testing"""
    return [
        "aqe/test-plan/generated",
        "aqe/test-plan/executed",
        "aqe/coverage/analysis",
        "aqe/coverage/gaps",
        "aqe/quality/metrics",
        "aqe/quality/gates",
        "aqe/performance/benchmarks",
        "aqe/security/scan-results",
        "aqe/patterns/test-generation",
        "aqe/swarm/coordination"
    ]


@pytest.fixture
def expired_memory_data():
    """Sample data with expired TTL for testing expiration"""
    return {
        "value": {"data": "should_expire"},
        "timestamp": (datetime.now() - timedelta(seconds=3600)).timestamp(),
        "ttl": 1800,  # 30 minutes, already expired
        "partition": "test"
    }


@pytest.fixture
def active_memory_data():
    """Sample data that has not expired"""
    return {
        "value": {"data": "still_active"},
        "timestamp": datetime.now().timestamp(),
        "ttl": 3600,  # 1 hour, not expired
        "partition": "test"
    }


# ============================================================================
# Memory Backend Instances (Mocked)
# ============================================================================

@pytest.fixture
async def postgres_memory(mocker, mock_db_manager_for_memory):
    """Create mocked PostgresMemory instance

    Note: Since PostgresMemory doesn't exist yet, this creates
    a mock that matches the expected interface
    """
    memory = mocker.Mock()
    memory.db_manager = mock_db_manager_for_memory
    memory.namespace_prefix = "aqe/"

    # Mock core methods
    memory.store = AsyncMock()
    memory.retrieve = AsyncMock(return_value=None)
    memory.search = AsyncMock(return_value={})
    memory.delete = AsyncMock()
    memory.clear_partition = AsyncMock()
    memory.list_keys = AsyncMock(return_value=[])
    memory.get_stats = AsyncMock(return_value={"total_keys": 0})
    memory.connect = AsyncMock()
    memory.disconnect = AsyncMock()

    return memory


@pytest.fixture
async def redis_memory(mocker, mock_redis_client):
    """Create mocked RedisMemory instance

    Note: Since RedisMemory doesn't exist yet, this creates
    a mock that matches the expected interface
    """
    memory = mocker.Mock()
    memory.redis = mock_redis_client
    memory.namespace_prefix = "aqe:"

    # Mock core methods
    memory.store = AsyncMock()
    memory.retrieve = AsyncMock(return_value=None)
    memory.search = AsyncMock(return_value={})
    memory.delete = AsyncMock()
    memory.clear_partition = AsyncMock()
    memory.list_keys = AsyncMock(return_value=[])
    memory.get_stats = AsyncMock(return_value={"total_keys": 0})
    memory.connect = AsyncMock()
    memory.disconnect = AsyncMock()

    return memory


# ============================================================================
# Cleanup Utilities
# ============================================================================

@pytest.fixture
async def cleanup_test_keys(postgres_memory, redis_memory):
    """Cleanup test keys after test completion"""
    test_keys = []

    def register_key(key: str):
        """Register a key for cleanup"""
        test_keys.append(key)

    yield register_key

    # Cleanup
    for key in test_keys:
        try:
            await postgres_memory.delete(key)
        except:
            pass
        try:
            await redis_memory.delete(key)
        except:
            pass


@pytest.fixture
def aqe_namespace_validator():
    """Validator for AQE namespace compliance"""
    def validate(key: str) -> bool:
        """Check if key starts with aqe/ or aqe:"""
        return key.startswith("aqe/") or key.startswith("aqe:")

    return validate


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_test_keys(count: int = 10, prefix: str = "aqe/test") -> list:
    """Generate multiple test keys"""
    return [f"{prefix}/key_{i}" for i in range(count)]


def generate_memory_entries(count: int = 5) -> Dict[str, Any]:
    """Generate multiple memory entries"""
    return {
        f"aqe/test/entry_{i}": {
            "data": f"value_{i}",
            "index": i,
            "timestamp": datetime.now().isoformat()
        }
        for i in range(count)
    }


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_valid_aqe_key(key: str):
    """Assert key follows AQE namespace convention"""
    assert key.startswith("aqe/") or key.startswith("aqe:"), \
        f"Key '{key}' does not start with aqe/ or aqe:"


def assert_ttl_valid(ttl: int):
    """Assert TTL is positive"""
    assert ttl > 0, f"TTL must be positive, got {ttl}"


def assert_memory_stats_valid(stats: Dict[str, Any]):
    """Assert memory stats have required fields"""
    assert "total_keys" in stats
    assert isinstance(stats["total_keys"], int)
    assert stats["total_keys"] >= 0
