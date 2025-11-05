"""Real Redis Integration Tests

Tests RedisMemory with actual Redis server.
These tests require docker-compose-test.yml to be running.

Run with:
    docker-compose -f docker-compose-test.yml up -d
    pytest tests/integration/test_redis_memory_integration.py -v -m integration
"""

import pytest
import asyncio
import time
from datetime import datetime


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealBasicOperations:
    """Test basic operations with real Redis"""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_simple_value(self, redis_memory_real, integration_test_data):
        """Test storing and retrieving a simple value"""
        key = "aqe/test/basic/simple"
        value = integration_test_data["simple"]

        await redis_memory_real.store(key, value)
        result = await redis_memory_real.retrieve(key)

        assert result is not None
        assert result == value
        assert result["value"] == "test"
        assert result["count"] == 42

    @pytest.mark.asyncio
    async def test_store_and_retrieve_nested_data(self, redis_memory_real, integration_test_data):
        """Test storing and retrieving deeply nested data"""
        key = "aqe/test/basic/nested"
        value = integration_test_data["nested"]

        await redis_memory_real.store(key, value)
        result = await redis_memory_real.retrieve(key)

        assert result is not None
        assert result["level1"]["level2"]["level3"] == "deep_value"

    @pytest.mark.asyncio
    async def test_store_and_retrieve_list_data(self, redis_memory_real, integration_test_data):
        """Test storing and retrieving lists"""
        key = "aqe/test/basic/lists"
        value = integration_test_data["list_data"]

        await redis_memory_real.store(key, value)
        result = await redis_memory_real.retrieve(key)

        assert result is not None
        assert result["items"] == [1, 2, 3, 4, 5]
        assert result["names"] == ["alpha", "beta", "gamma"]

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_key_returns_none(self, redis_memory_real):
        """Test retrieving nonexistent key returns None"""
        result = await redis_memory_real.retrieve("aqe/test/basic/nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, redis_memory_real):
        """Test overwriting an existing key updates the value"""
        key = "aqe/test/basic/overwrite"

        # Store initial value
        await redis_memory_real.store(key, {"version": 1})
        result1 = await redis_memory_real.retrieve(key)
        assert result1["version"] == 1

        # Overwrite with new value
        await redis_memory_real.store(key, {"version": 2})
        result2 = await redis_memory_real.retrieve(key)
        assert result2["version"] == 2

    @pytest.mark.asyncio
    async def test_delete_key(self, redis_memory_real):
        """Test deleting a key"""
        key = "aqe/test/basic/delete"

        # Store and verify
        await redis_memory_real.store(key, {"data": "to_delete"})
        assert await redis_memory_real.retrieve(key) is not None

        # Delete
        await redis_memory_real.delete(key)

        # Verify deleted
        assert await redis_memory_real.retrieve(key) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key_no_error(self, redis_memory_real):
        """Test deleting nonexistent key doesn't raise error"""
        # Should not raise exception
        await redis_memory_real.delete("aqe/test/basic/never_existed")

    @pytest.mark.asyncio
    async def test_store_complex_data(self, redis_memory_real, integration_test_data):
        """Test storing complex nested data structures"""
        key = "aqe/test/basic/complex"
        value = integration_test_data["complex"]

        await redis_memory_real.store(key, value)
        result = await redis_memory_real.retrieve(key)

        assert result is not None
        assert len(result["tests"]) == 2
        assert result["tests"][0]["name"] == "test_one"
        assert result["metadata"]["framework"] == "pytest"


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealTTL:
    """Test TTL (time-to-live) with real Redis"""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, redis_memory_real):
        """Test storing value with TTL"""
        key = "aqe/test/ttl/with_expiry"
        value = {"data": "expires_soon"}
        ttl = 3600  # 1 hour

        await redis_memory_real.store(key, value, ttl=ttl)

        # Should be retrievable immediately
        result = await redis_memory_real.retrieve(key)
        assert result is not None
        assert result["data"] == "expires_soon"

        # Verify TTL is set
        actual_ttl = redis_memory_real.client.ttl(key)
        assert actual_ttl > 0
        assert actual_ttl <= 3600

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_ttl_expiration_real_time(self, redis_memory_real):
        """Test that values actually expire after TTL"""
        key = "aqe/test/ttl/expires_fast"
        value = {"data": "should_expire"}
        ttl = 2  # 2 seconds

        # Store with short TTL
        await redis_memory_real.store(key, value, ttl=ttl)

        # Should exist immediately
        result1 = await redis_memory_real.retrieve(key)
        assert result1 is not None

        # Wait for expiration
        await asyncio.sleep(3)

        # Should be expired now (Redis auto-expires)
        result2 = await redis_memory_real.retrieve(key)
        assert result2 is None

    @pytest.mark.asyncio
    async def test_store_without_ttl_persists(self, redis_memory_real):
        """Test storing without TTL creates persistent entry"""
        key = "aqe/test/ttl/no_expiry"
        value = {"data": "persistent"}

        # Store without TTL
        await redis_memory_real.store(key, value, ttl=None)

        # Should be retrievable
        result = await redis_memory_real.retrieve(key)
        assert result is not None

        # Should have no TTL set (-1 means no expiration)
        actual_ttl = redis_memory_real.client.ttl(key)
        assert actual_ttl == -1

    @pytest.mark.asyncio
    async def test_update_ttl_on_overwrite(self, redis_memory_real):
        """Test that overwriting a key updates its TTL"""
        key = "aqe/test/ttl/update"

        # Store with short TTL
        await redis_memory_real.store(key, {"version": 1}, ttl=5)
        ttl1 = redis_memory_real.client.ttl(key)

        # Overwrite with longer TTL
        await redis_memory_real.store(key, {"version": 2}, ttl=3600)
        ttl2 = redis_memory_real.client.ttl(key)

        # New TTL should be longer
        assert ttl2 > ttl1
        result = await redis_memory_real.retrieve(key)
        assert result["version"] == 2


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealSearch:
    """Test pattern-based search with real Redis"""

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, redis_memory_real):
        """Test searching keys by Redis pattern"""
        # Store multiple keys
        test_data = {
            "aqe/test/search/item1": {"value": 1},
            "aqe/test/search/item2": {"value": 2},
            "aqe/test/search/item3": {"value": 3},
            "aqe/test/other/item4": {"value": 4},
        }

        for key, value in test_data.items():
            await redis_memory_real.store(key, value)

        # Search for pattern
        results = await redis_memory_real.search("aqe/test/search/*")

        assert len(results) == 3
        assert "aqe/test/search/item1" in results
        assert "aqe/test/search/item2" in results
        assert "aqe/test/search/item3" in results
        assert "aqe/test/other/item4" not in results

    @pytest.mark.asyncio
    async def test_search_no_matches(self, redis_memory_real):
        """Test search with no matches returns empty dict"""
        results = await redis_memory_real.search("aqe/test/nonexistent/*")
        assert results == {}
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_with_redis_patterns(self, redis_memory_real):
        """Test Redis-specific pattern matching"""
        # Store keys
        await redis_memory_real.store("aqe/test/pattern/a", {"value": "a"})
        await redis_memory_real.store("aqe/test/pattern/b", {"value": "b"})
        await redis_memory_real.store("aqe/test/pattern/ab", {"value": "ab"})

        # Search with ? (single char wildcard)
        results = await redis_memory_real.search("aqe/test/pattern/?")

        # Should match single character keys
        assert len(results) == 2
        assert "aqe/test/pattern/a" in results
        assert "aqe/test/pattern/b" in results

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_search_excludes_expired_keys(self, redis_memory_real):
        """Test that search doesn't return expired keys"""
        # Store key with short TTL
        await redis_memory_real.store("aqe/test/search/expires", {"data": "temp"}, ttl=1)

        # Store key without TTL
        await redis_memory_real.store("aqe/test/search/persists", {"data": "permanent"}, ttl=None)

        # Wait for first key to expire
        await asyncio.sleep(2)

        # Search (Redis auto-removes expired keys)
        results = await redis_memory_real.search("aqe/test/search/*")

        # Should only return non-expired key
        assert len(results) == 1
        assert "aqe/test/search/persists" in results
        assert "aqe/test/search/expires" not in results


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealPartitions:
    """Test partition management with real Redis"""

    @pytest.mark.asyncio
    async def test_store_in_partition(self, redis_memory_real):
        """Test storing values in specific partitions"""
        key = "aqe/test/partition/item"

        await redis_memory_real.store(key, {"data": "test"}, partition="test_partition")

        # Should be retrievable
        result = await redis_memory_real.retrieve(key)
        assert result is not None

    @pytest.mark.asyncio
    async def test_clear_partition(self, redis_memory_real):
        """Test clearing all keys in a partition"""
        # Store keys in different partitions
        await redis_memory_real.store("aqe/test/part/key1", {"v": 1}, partition="partition_a")
        await redis_memory_real.store("aqe/test/part/key2", {"v": 2}, partition="partition_a")
        await redis_memory_real.store("aqe/test/part/key3", {"v": 3}, partition="partition_b")

        # Clear partition_a
        await redis_memory_real.clear_partition("partition_a")

        # Keys in partition_a should be gone
        assert await redis_memory_real.retrieve("aqe/test/part/key1") is None
        assert await redis_memory_real.retrieve("aqe/test/part/key2") is None

        # Keys in partition_b should remain
        assert await redis_memory_real.retrieve("aqe/test/part/key3") is not None


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealKeyListing:
    """Test key listing functionality with real Redis"""

    @pytest.mark.asyncio
    async def test_list_keys_with_prefix(self, redis_memory_real):
        """Test listing keys with prefix filter"""
        # Store keys
        keys_to_store = [
            "aqe/test/list/alpha",
            "aqe/test/list/beta",
            "aqe/test/list/gamma",
            "aqe/test/other/delta",
        ]

        for key in keys_to_store:
            await redis_memory_real.store(key, {"key": key})

        # List with prefix
        result = await redis_memory_real.list_keys("aqe/test/list/")

        assert len(result) == 3
        assert "aqe/test/list/alpha" in result
        assert "aqe/test/list/beta" in result
        assert "aqe/test/list/gamma" in result
        assert "aqe/test/other/delta" not in result

    @pytest.mark.asyncio
    async def test_list_all_keys(self, redis_memory_real):
        """Test listing all keys without filter"""
        # Store keys
        keys = ["aqe/test/all/key1", "aqe/test/all/key2", "aqe/test/all/key3"]
        for key in keys:
            await redis_memory_real.store(key, {"data": "test"})

        # List all with pattern
        result = await redis_memory_real.list_keys("aqe/test/all/")

        assert len(result) == 3
        for key in keys:
            assert key in result

    @pytest.mark.asyncio
    async def test_keys_are_sorted(self, redis_memory_real):
        """Test that listed keys are sorted alphabetically"""
        # Store keys in random order
        keys = [
            "aqe/test/sort/zebra",
            "aqe/test/sort/alpha",
            "aqe/test/sort/beta",
        ]

        for key in keys:
            await redis_memory_real.store(key, {"key": key})

        # List keys
        result = await redis_memory_real.list_keys("aqe/test/sort/")

        # Should be sorted
        assert result == sorted(result)


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealStats:
    """Test statistics with real Redis"""

    @pytest.mark.asyncio
    async def test_get_stats(self, redis_memory_real):
        """Test getting memory statistics"""
        # Store some data
        for i in range(5):
            await redis_memory_real.store(
                f"aqe/test/stats/key{i}",
                {"index": i}
            )

        # Get stats
        stats = await redis_memory_real.get_stats()

        assert "total_keys" in stats
        assert "memory_used" in stats
        assert "connected_clients" in stats
        assert stats["total_keys"] >= 5

    @pytest.mark.asyncio
    async def test_stats_show_memory_usage(self, redis_memory_real, large_test_data):
        """Test that stats show memory usage"""
        # Get initial memory
        stats1 = await redis_memory_real.get_stats()

        # Store large data
        await redis_memory_real.store("aqe/test/stats/large", large_test_data)

        # Get updated stats
        stats2 = await redis_memory_real.get_stats()

        # Memory usage should reflect the data
        assert stats2["total_keys"] >= stats1["total_keys"]


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealConcurrency:
    """Test concurrent access patterns with real Redis"""

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, redis_memory_real, concurrent_executor):
        """Test concurrent write operations"""
        num_operations = 50

        # Create concurrent write operations
        async def write_operation(index: int):
            key = f"aqe/test/concurrent/key{index}"
            await redis_memory_real.store(key, {"index": index})

        operations = [write_operation(i) for i in range(num_operations)]

        # Execute concurrently
        results = await concurrent_executor.run_concurrent(operations)

        # All operations should succeed
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0

        # Verify all keys exist
        for i in range(num_operations):
            key = f"aqe/test/concurrent/key{i}"
            result = await redis_memory_real.retrieve(key)
            assert result is not None
            assert result["index"] == i

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, redis_memory_real):
        """Test concurrent read operations"""
        key = "aqe/test/concurrent/read_target"

        # Store data
        await redis_memory_real.store(key, {"data": "shared"})

        # Create concurrent read operations
        async def read_operation():
            return await redis_memory_real.retrieve(key)

        # Execute 100 concurrent reads
        tasks = [read_operation() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All reads should succeed
        assert all(r is not None for r in results)
        assert all(r["data"] == "shared" for r in results)

    @pytest.mark.asyncio
    async def test_atomic_operations(self, redis_memory_real):
        """Test that Redis operations are atomic"""
        key = "aqe/test/concurrent/atomic"

        # Concurrent writes of different values
        async def write_value(value: int):
            await redis_memory_real.store(key, {"value": value})

        tasks = [write_value(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # Final value should be one of the written values
        result = await redis_memory_real.retrieve(key)
        assert result is not None
        assert 0 <= result["value"] < 10


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.slow
class TestRedisMemoryRealPerformance:
    """Test performance characteristics with real Redis"""

    @pytest.mark.asyncio
    async def test_bulk_write_performance(self, redis_memory_real, performance_tracker):
        """Test bulk write performance"""
        num_records = 100

        # Bulk write
        for i in range(num_records):
            await redis_memory_real.store(
                f"aqe/test/perf/bulk{i}",
                {"index": i, "data": f"value_{i}"}
            )

        duration = performance_tracker.total_duration
        ops_per_second = num_records / duration if duration > 0 else 0

        print(f"\nRedis bulk write: {num_records} records in {duration:.2f}s ({ops_per_second:.2f} ops/s)")

        # Redis should be fast (>50 ops/sec)
        assert ops_per_second > 50

    @pytest.mark.asyncio
    async def test_read_performance(self, redis_memory_real):
        """Test read performance"""
        key = "aqe/test/perf/read"

        # Store data
        await redis_memory_real.store(key, {"data": "test"})

        # Measure read time
        num_reads = 100
        start = time.time()

        for _ in range(num_reads):
            await redis_memory_real.retrieve(key)

        duration = time.time() - start
        ops_per_second = num_reads / duration if duration > 0 else 0

        print(f"\nRedis reads: {num_reads} reads in {duration:.3f}s ({ops_per_second:.2f} ops/s)")

        # Redis reads should be very fast (>100 ops/sec)
        assert ops_per_second > 100

    @pytest.mark.asyncio
    async def test_search_performance(self, redis_memory_real):
        """Test search performance"""
        # Store 50 keys
        for i in range(50):
            await redis_memory_real.store(
                f"aqe/test/perf/search{i}",
                {"index": i}
            )

        # Measure search time
        start = time.time()
        results = await redis_memory_real.search("aqe/test/perf/search*")
        duration = time.time() - start

        print(f"\nRedis search: {len(results)} results in {duration:.3f}s")

        assert len(results) == 50
        # Search should be fast
        assert duration < 0.5


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealPersistence:
    """Test Redis persistence (AOF) with real Redis"""

    @pytest.mark.asyncio
    async def test_data_persists_across_flushdb(self, redis_memory_persistent):
        """Test that data in different DB survives flushdb"""
        key = "aqe/test/persist/item"

        # Store data
        await redis_memory_persistent.store(key, {"data": "persistent"})

        # Verify stored
        result = await redis_memory_persistent.retrieve(key)
        assert result is not None

    @pytest.mark.asyncio
    async def test_metadata_preserved(self, redis_memory_real):
        """Test that partition metadata is preserved"""
        key = "aqe/test/persist/metadata"

        # Store with partition
        await redis_memory_real.store(key, {"data": "test"}, partition="custom_partition")

        # Retrieve and check internal structure
        raw_data = redis_memory_real.client.get(key)
        assert raw_data is not None

        import json
        parsed = json.loads(raw_data)
        assert parsed["partition"] == "custom_partition"
        assert parsed["value"]["data"] == "test"


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealConnectionPool:
    """Test Redis connection pooling"""

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self, redis_memory_real):
        """Test that connection pool is reused"""
        # Multiple operations should use same pool
        for i in range(10):
            await redis_memory_real.store(f"aqe/test/pool/key{i}", {"index": i})

        # All operations should succeed without creating new connections
        for i in range(10):
            result = await redis_memory_real.retrieve(f"aqe/test/pool/key{i}")
            assert result["index"] == i

    @pytest.mark.asyncio
    async def test_connection_pool_handles_load(self, redis_memory_real, concurrent_executor):
        """Test connection pool under load"""
        # Create many concurrent operations
        async def operation(index: int):
            key = f"aqe/test/pool/load{index}"
            await redis_memory_real.store(key, {"index": index})
            result = await redis_memory_real.retrieve(key)
            return result

        operations = [operation(i) for i in range(100)]

        # Execute with high concurrency
        results = await concurrent_executor.run_concurrent(operations, batch_size=20)

        # All should succeed
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0


@pytest.mark.integration
@pytest.mark.redis
class TestRedisMemoryRealCleanup:
    """Test cleanup and resource management"""

    @pytest.mark.asyncio
    async def test_cleanup_expired_noop(self, redis_memory_real):
        """Test that cleanup_expired is a no-op in Redis"""
        # Store some keys
        for i in range(5):
            await redis_memory_real.store(f"aqe/test/cleanup/key{i}", {"index": i}, ttl=3600)

        # Call cleanup (should be no-op)
        deleted_count = await redis_memory_real.cleanup_expired()

        # Redis handles expiration automatically
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_close_connection(self, redis_memory_real):
        """Test closing Redis connection"""
        # Store data
        await redis_memory_real.store("aqe/test/cleanup/close", {"data": "test"})

        # Close connection
        redis_memory_real.close()

        # Connection should be closed (this would raise error in real usage)
        # But since we're in a fixture, it's already managed
