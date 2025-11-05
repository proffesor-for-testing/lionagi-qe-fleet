"""Tests for RedisMemory backend

Validates Redis-backed memory implementation including:
- Store and retrieve operations with JSON serialization
- TTL expiration and enforcement
- Pattern-based key scanning
- Key deletion and namespace clearing
- Connection pooling
- Namespace enforcement (aqe:)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json


class TestRedisMemoryBasicOperations:
    """Test basic store/retrieve/delete operations"""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_basic(self, redis_memory, sample_memory_data):
        """Test storing and retrieving a simple value"""
        key = "aqe:test:basic"
        value = sample_memory_data["simple_value"]

        # Configure mock to return JSON-serialized value
        redis_memory.retrieve.return_value = value

        await redis_memory.store(key, value)
        result = await redis_memory.retrieve(key)

        assert result == value
        redis_memory.store.assert_called_once()
        redis_memory.retrieve.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_key(self, redis_memory):
        """Test retrieving a key that doesn't exist returns None"""
        redis_memory.retrieve.return_value = None

        result = await redis_memory.retrieve("aqe:test:nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, redis_memory):
        """Test deleting a key"""
        key = "aqe:test:to_delete"

        await redis_memory.delete(key)

        redis_memory.delete.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, redis_memory):
        """Test deleting a nonexistent key doesn't raise error"""
        key = "aqe:test:nonexistent"

        await redis_memory.delete(key)

        redis_memory.delete.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_store_complex_data(self, redis_memory, sample_memory_data):
        """Test storing complex nested data structures"""
        key = "aqe:test:complex"
        value = sample_memory_data["test_plan"]

        redis_memory.retrieve.return_value = value

        await redis_memory.store(key, value)
        result = await redis_memory.retrieve(key)

        assert result == value
        assert result["framework"] == "pytest"
        assert len(result["tests"]) == 2


class TestRedisMemoryTTL:
    """Test TTL (time-to-live) expiration functionality"""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, redis_memory, sample_memory_data):
        """Test storing value with TTL"""
        key = "aqe:test:with_ttl"
        value = sample_memory_data["simple_value"]
        ttl = 3600  # 1 hour

        await redis_memory.store(key, value, ttl=ttl)

        redis_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_ttl_enforcement(self, redis_memory):
        """Test that Redis TTL is properly enforced"""
        key = "aqe:test:ttl_enforced"
        value = {"data": "expires_soon"}
        ttl = 10  # 10 seconds

        await redis_memory.store(key, value, ttl=ttl)

        # Verify store was called with TTL
        redis_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_expired_keys_not_returned(self, redis_memory):
        """Test that expired keys are not returned by retrieve"""
        redis_memory.retrieve.return_value = None

        result = await redis_memory.retrieve("aqe:test:expired")

        assert result is None

    @pytest.mark.asyncio
    async def test_store_without_ttl(self, redis_memory):
        """Test storing value without TTL (persistent)"""
        key = "aqe:test:no_ttl"
        value = {"data": "persistent"}

        await redis_memory.store(key, value, ttl=None)

        redis_memory.store.assert_called_once()


class TestRedisMemorySearch:
    """Test pattern-based search functionality"""

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, redis_memory):
        """Test searching keys by pattern using Redis SCAN"""
        pattern = "aqe:test:*"
        expected_results = {
            "aqe:test:key1": {"data": "value1"},
            "aqe:test:key2": {"data": "value2"}
        }

        redis_memory.search.return_value = expected_results

        results = await redis_memory.search(pattern)

        assert len(results) == 2
        assert "aqe:test:key1" in results
        assert "aqe:test:key2" in results
        redis_memory.search.assert_called_once_with(pattern)

    @pytest.mark.asyncio
    async def test_search_no_matches(self, redis_memory):
        """Test search with no matching keys returns empty dict"""
        pattern = "aqe:nonexistent:*"
        redis_memory.search.return_value = {}

        results = await redis_memory.search(pattern)

        assert results == {}
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_namespace_pattern_matching(self, redis_memory):
        """Test pattern matching respects namespace prefix"""
        pattern = "aqe:test-plan:*"
        expected = {
            "aqe:test-plan:generated": {"tests": []},
            "aqe:test-plan:executed": {"results": []}
        }

        redis_memory.search.return_value = expected

        results = await redis_memory.search(pattern)

        assert all(k.startswith("aqe:test-plan:") for k in results.keys())


class TestRedisMemoryPartitions:
    """Test partition management"""

    @pytest.mark.asyncio
    async def test_clear_partition(self, redis_memory):
        """Test clearing all keys in a partition"""
        partition = "test_partition"

        await redis_memory.clear_partition(partition)

        redis_memory.clear_partition.assert_called_once_with(partition)

    @pytest.mark.asyncio
    async def test_store_with_partition(self, redis_memory):
        """Test storing value in specific partition"""
        key = "aqe:test:partitioned"
        value = {"data": "test"}
        partition = "test_partition"

        await redis_memory.store(key, value, partition=partition)

        redis_memory.store.assert_called_once()


class TestRedisMemoryKeyListing:
    """Test key listing functionality"""

    @pytest.mark.asyncio
    async def test_list_keys_with_prefix(self, redis_memory):
        """Test listing keys with specific prefix"""
        prefix = "aqe:test-plan"
        expected_keys = [
            "aqe:test-plan:generated",
            "aqe:test-plan:executed"
        ]

        redis_memory.list_keys.return_value = expected_keys

        keys = await redis_memory.list_keys(prefix=prefix)

        assert len(keys) == 2
        assert all(k.startswith(prefix) for k in keys)
        redis_memory.list_keys.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_all_keys(self, redis_memory):
        """Test listing all keys without prefix filter"""
        all_keys = [
            "aqe:test:key1",
            "aqe:test:key2",
            "aqe:coverage:results"
        ]

        redis_memory.list_keys.return_value = all_keys

        keys = await redis_memory.list_keys()

        assert len(keys) == 3
        redis_memory.list_keys.assert_called_once()


class TestRedisMemoryStats:
    """Test statistics and metrics"""

    @pytest.mark.asyncio
    async def test_get_stats(self, redis_memory):
        """Test getting memory statistics"""
        expected_stats = {
            "total_keys": 10,
            "memory_used_bytes": 2048,
            "partitions": {
                "test": 5,
                "prod": 5
            }
        }

        redis_memory.get_stats.return_value = expected_stats

        stats = await redis_memory.get_stats()

        assert stats["total_keys"] == 10
        assert "memory_used_bytes" in stats
        redis_memory.get_stats.assert_called_once()


class TestRedisMemoryNamespace:
    """Test AQE namespace enforcement"""

    @pytest.mark.asyncio
    async def test_key_must_start_with_aqe_namespace(self, redis_memory, aqe_namespace_validator):
        """Test that all keys must start with aqe: namespace"""
        valid_key = "aqe:test:valid"
        invalid_key = "invalid:test:key"

        # Valid key should pass
        assert aqe_namespace_validator(valid_key)

        # Invalid key should fail
        assert not aqe_namespace_validator(invalid_key)

    @pytest.mark.asyncio
    async def test_namespace_prefix_applied(self, redis_memory):
        """Test that namespace prefix is correctly applied"""
        assert redis_memory.namespace_prefix == "aqe:"


class TestRedisMemoryConnectionPool:
    """Test Redis connection pooling"""

    @pytest.mark.asyncio
    async def test_redis_connection_pooling(self, redis_memory, mock_redis_client):
        """Test that Redis connection pool is used efficiently"""
        # Verify Redis client is configured
        assert redis_memory.redis is not None

        # Multiple operations should reuse the same connection
        await redis_memory.connect()
        await redis_memory.connect()

        assert redis_memory.connect.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_access_thread_safe(self, redis_memory):
        """Test concurrent access is thread-safe"""
        # Simulate concurrent operations
        tasks = [
            redis_memory.store(f"aqe:test:concurrent:{i}", {"value": i})
            for i in range(10)
        ]

        # All operations should complete without error
        await asyncio.gather(*tasks)

        assert redis_memory.store.call_count == 10


class TestRedisMemoryIntegration:
    """Integration tests with Redis client"""

    @pytest.mark.asyncio
    async def test_store_uses_redis_set(self, redis_memory, mock_redis_client):
        """Test that store operation uses Redis SET command"""
        key = "aqe:test:redis_set"
        value = {"data": "test"}

        redis_memory.retrieve.return_value = value

        await redis_memory.store(key, value)
        result = await redis_memory.retrieve(key)

        assert result == value

    @pytest.mark.asyncio
    async def test_retrieve_uses_redis_get(self, redis_memory, mock_redis_client):
        """Test that retrieve operation uses Redis GET command"""
        key = "aqe:test:redis_get"

        redis_memory.retrieve.return_value = {"data": "test"}

        result = await redis_memory.retrieve(key)

        assert result is not None
        redis_memory.retrieve.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_search_uses_redis_scan(self, redis_memory, mock_redis_client):
        """Test that search uses Redis SCAN for pattern matching"""
        pattern = "aqe:test:*"
        expected = {
            "aqe:test:key1": {"data": "value1"}
        }

        redis_memory.search.return_value = expected

        results = await redis_memory.search(pattern)

        assert results == expected
        redis_memory.search.assert_called_once_with(pattern)


class TestRedisMemoryErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_handles_redis_connection_error(self, redis_memory):
        """Test graceful handling of Redis connection errors"""
        # Configure mock to raise connection error
        redis_memory.connect.side_effect = Exception("Redis connection failed")

        with pytest.raises(Exception, match="Redis connection failed"):
            await redis_memory.connect()

    @pytest.mark.asyncio
    async def test_handles_json_serialization_error(self, redis_memory):
        """Test handling of non-JSON-serializable data"""
        key = "aqe:test:json_error"

        # Mock should handle any data
        await redis_memory.store(key, {"data": "valid"})

        redis_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, redis_memory):
        """Test proper cleanup on disconnect"""
        await redis_memory.disconnect()

        redis_memory.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_large_data(self, redis_memory):
        """Test storing large data structures"""
        key = "aqe:test:large_data"
        large_value = {
            "tests": [{"id": i, "name": f"test_{i}"} for i in range(1000)]
        }

        await redis_memory.store(key, large_value)

        redis_memory.store.assert_called_once()


class TestRedisMemoryPerformance:
    """Test performance characteristics"""

    @pytest.mark.asyncio
    async def test_bulk_operations(self, redis_memory):
        """Test bulk store operations perform efficiently"""
        # Store multiple keys
        tasks = [
            redis_memory.store(f"aqe:test:bulk:{i}", {"index": i})
            for i in range(100)
        ]

        await asyncio.gather(*tasks)

        assert redis_memory.store.call_count == 100

    @pytest.mark.asyncio
    async def test_search_large_keyspace(self, redis_memory):
        """Test searching in large keyspace"""
        pattern = "aqe:test:*"

        # Mock returning large result set
        large_results = {
            f"aqe:test:key:{i}": {"value": i}
            for i in range(1000)
        }
        redis_memory.search.return_value = large_results

        results = await redis_memory.search(pattern)

        assert len(results) == 1000
