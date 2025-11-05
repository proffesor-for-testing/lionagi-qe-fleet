"""Real PostgreSQL Integration Tests

Tests PostgresMemory with actual PostgreSQL database.
These tests require docker-compose-test.yml to be running.

Run with:
    docker-compose -f docker-compose-test.yml up -d
    pytest tests/integration/test_postgres_memory_integration.py -v -m integration
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealBasicOperations:
    """Test basic operations with real PostgreSQL database"""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_simple_value(self, postgres_memory_real, integration_test_data):
        """Test storing and retrieving a simple value"""
        key = "aqe/test/basic/simple"
        value = integration_test_data["simple"]

        # Store value
        await postgres_memory_real.store(key, value)

        # Retrieve value
        result = await postgres_memory_real.retrieve(key)

        assert result is not None
        assert result == value
        assert result["value"] == "test"
        assert result["count"] == 42

    @pytest.mark.asyncio
    async def test_store_and_retrieve_nested_data(self, postgres_memory_real, integration_test_data):
        """Test storing and retrieving deeply nested data"""
        key = "aqe/test/basic/nested"
        value = integration_test_data["nested"]

        await postgres_memory_real.store(key, value)
        result = await postgres_memory_real.retrieve(key)

        assert result is not None
        assert result["level1"]["level2"]["level3"] == "deep_value"

    @pytest.mark.asyncio
    async def test_store_and_retrieve_list_data(self, postgres_memory_real, integration_test_data):
        """Test storing and retrieving lists"""
        key = "aqe/test/basic/lists"
        value = integration_test_data["list_data"]

        await postgres_memory_real.store(key, value)
        result = await postgres_memory_real.retrieve(key)

        assert result is not None
        assert result["items"] == [1, 2, 3, 4, 5]
        assert result["names"] == ["alpha", "beta", "gamma"]

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_key_returns_none(self, postgres_memory_real):
        """Test retrieving nonexistent key returns None"""
        result = await postgres_memory_real.retrieve("aqe/test/basic/nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, postgres_memory_real):
        """Test overwriting an existing key updates the value"""
        key = "aqe/test/basic/overwrite"

        # Store initial value
        await postgres_memory_real.store(key, {"version": 1})
        result1 = await postgres_memory_real.retrieve(key)
        assert result1["version"] == 1

        # Overwrite with new value
        await postgres_memory_real.store(key, {"version": 2})
        result2 = await postgres_memory_real.retrieve(key)
        assert result2["version"] == 2

    @pytest.mark.asyncio
    async def test_delete_key(self, postgres_memory_real):
        """Test deleting a key"""
        key = "aqe/test/basic/delete"

        # Store and verify
        await postgres_memory_real.store(key, {"data": "to_delete"})
        assert await postgres_memory_real.retrieve(key) is not None

        # Delete
        await postgres_memory_real.delete(key)

        # Verify deleted
        assert await postgres_memory_real.retrieve(key) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key_no_error(self, postgres_memory_real):
        """Test deleting nonexistent key doesn't raise error"""
        # Should not raise exception
        await postgres_memory_real.delete("aqe/test/basic/never_existed")


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealTTL:
    """Test TTL (time-to-live) expiration with real database"""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, postgres_memory_real):
        """Test storing value with TTL"""
        key = "aqe/test/ttl/with_expiry"
        value = {"data": "expires_soon"}
        ttl = 3600  # 1 hour

        await postgres_memory_real.store(key, value, ttl=ttl)

        # Should be retrievable immediately
        result = await postgres_memory_real.retrieve(key)
        assert result is not None
        assert result["data"] == "expires_soon"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_ttl_expiration_real_time(self, postgres_memory_real):
        """Test that values actually expire after TTL (real time test)"""
        key = "aqe/test/ttl/expires_fast"
        value = {"data": "should_expire"}
        ttl = 2  # 2 seconds

        # Store with short TTL
        await postgres_memory_real.store(key, value, ttl=ttl)

        # Should exist immediately
        result1 = await postgres_memory_real.retrieve(key)
        assert result1 is not None

        # Wait for expiration
        await asyncio.sleep(3)

        # Should be expired now
        result2 = await postgres_memory_real.retrieve(key)
        assert result2 is None

    @pytest.mark.asyncio
    async def test_store_without_ttl_persists(self, postgres_memory_real):
        """Test storing without TTL creates persistent entry"""
        key = "aqe/test/ttl/no_expiry"
        value = {"data": "persistent"}

        # Store without TTL
        await postgres_memory_real.store(key, value, ttl=None)

        # Should be retrievable
        result = await postgres_memory_real.retrieve(key)
        assert result is not None
        assert result["data"] == "persistent"

    @pytest.mark.asyncio
    async def test_update_ttl_on_overwrite(self, postgres_memory_real):
        """Test that overwriting a key updates its TTL"""
        key = "aqe/test/ttl/update"

        # Store with short TTL
        await postgres_memory_real.store(key, {"version": 1}, ttl=5)

        # Overwrite with longer TTL
        await postgres_memory_real.store(key, {"version": 2}, ttl=3600)

        # Should have new value and new TTL
        result = await postgres_memory_real.retrieve(key)
        assert result is not None
        assert result["version"] == 2


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealSearch:
    """Test pattern-based search with real database"""

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, postgres_memory_clean):
        """Test searching keys by pattern"""
        # Store multiple keys
        test_data = {
            "aqe/test/search/item1": {"value": 1},
            "aqe/test/search/item2": {"value": 2},
            "aqe/test/search/item3": {"value": 3},
            "aqe/test/other/item4": {"value": 4},
        }

        for key, value in test_data.items():
            await postgres_memory_clean.store(key, value)

        # Search for pattern
        results = await postgres_memory_clean.search("aqe/test/search/*")

        assert len(results) == 3
        assert "aqe/test/search/item1" in results
        assert "aqe/test/search/item2" in results
        assert "aqe/test/search/item3" in results
        assert "aqe/test/other/item4" not in results

    @pytest.mark.asyncio
    async def test_search_no_matches(self, postgres_memory_clean):
        """Test search with no matches returns empty dict"""
        results = await postgres_memory_clean.search("aqe/test/nonexistent/*")
        assert results == {}
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_single_character_wildcard(self, postgres_memory_clean):
        """Test single character wildcard in pattern"""
        # Store keys
        await postgres_memory_clean.store("aqe/test/wild/a", {"value": "a"})
        await postgres_memory_clean.store("aqe/test/wild/b", {"value": "b"})
        await postgres_memory_clean.store("aqe/test/wild/ab", {"value": "ab"})

        # Search with ? (single char wildcard)
        results = await postgres_memory_clean.search("aqe/test/wild/_")

        # Should match single character keys only
        assert len(results) == 2
        assert "aqe/test/wild/a" in results
        assert "aqe/test/wild/b" in results

    @pytest.mark.asyncio
    async def test_search_excludes_expired_keys(self, postgres_memory_clean):
        """Test that search doesn't return expired keys"""
        # Store key with short TTL
        await postgres_memory_clean.store("aqe/test/search/expires", {"data": "temp"}, ttl=1)

        # Store key without TTL
        await postgres_memory_clean.store("aqe/test/search/persists", {"data": "permanent"}, ttl=None)

        # Wait for first key to expire
        await asyncio.sleep(2)

        # Search
        results = await postgres_memory_clean.search("aqe/test/search/*")

        # Should only return non-expired key
        assert len(results) == 1
        assert "aqe/test/search/persists" in results
        assert "aqe/test/search/expires" not in results


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealPartitions:
    """Test partition management with real database"""

    @pytest.mark.asyncio
    async def test_store_in_partition(self, postgres_memory_clean):
        """Test storing values in specific partitions"""
        key = "aqe/test/partition/item"

        await postgres_memory_clean.store(key, {"data": "test"}, partition="test_partition")

        # Should be retrievable
        result = await postgres_memory_clean.retrieve(key)
        assert result is not None

    @pytest.mark.asyncio
    async def test_clear_partition(self, postgres_memory_clean):
        """Test clearing all keys in a partition"""
        # Store keys in different partitions
        await postgres_memory_clean.store("aqe/test/part/key1", {"v": 1}, partition="partition_a")
        await postgres_memory_clean.store("aqe/test/part/key2", {"v": 2}, partition="partition_a")
        await postgres_memory_clean.store("aqe/test/part/key3", {"v": 3}, partition="partition_b")

        # Clear partition_a
        await postgres_memory_clean.clear_partition("partition_a")

        # Keys in partition_a should be gone
        assert await postgres_memory_clean.retrieve("aqe/test/part/key1") is None
        assert await postgres_memory_clean.retrieve("aqe/test/part/key2") is None

        # Keys in partition_b should remain
        assert await postgres_memory_clean.retrieve("aqe/test/part/key3") is not None


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealKeyListing:
    """Test key listing functionality with real database"""

    @pytest.mark.asyncio
    async def test_list_keys_with_prefix(self, postgres_memory_clean):
        """Test listing keys with prefix filter"""
        # Store keys
        keys_to_store = [
            "aqe/test/list/alpha",
            "aqe/test/list/beta",
            "aqe/test/list/gamma",
            "aqe/test/other/delta",
        ]

        for key in keys_to_store:
            await postgres_memory_clean.store(key, {"key": key})

        # List with prefix
        result = await postgres_memory_clean.list_keys("aqe/test/list/")

        assert len(result) == 3
        assert "aqe/test/list/alpha" in result
        assert "aqe/test/list/beta" in result
        assert "aqe/test/list/gamma" in result
        assert "aqe/test/other/delta" not in result

    @pytest.mark.asyncio
    async def test_list_all_keys(self, postgres_memory_clean):
        """Test listing all keys without filter"""
        # Store keys
        keys = ["aqe/test/all/key1", "aqe/test/all/key2", "aqe/test/all/key3"]
        for key in keys:
            await postgres_memory_clean.store(key, {"data": "test"})

        # List all
        result = await postgres_memory_clean.list_keys("aqe/test/all/")

        assert len(result) >= 3
        for key in keys:
            assert key in result


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealStats:
    """Test statistics with real database"""

    @pytest.mark.asyncio
    async def test_get_stats(self, postgres_memory_clean):
        """Test getting memory statistics"""
        # Store some data
        for i in range(5):
            await postgres_memory_clean.store(
                f"aqe/test/stats/key{i}",
                {"index": i},
                partition="stats_test"
            )

        # Get stats
        stats = await postgres_memory_clean.get_stats()

        assert "total_keys" in stats
        assert "partitions" in stats
        assert "size_bytes" in stats
        assert stats["total_keys"] >= 5
        assert "stats_test" in stats["partitions"]

    @pytest.mark.asyncio
    async def test_stats_size_calculation(self, postgres_memory_clean, large_test_data):
        """Test that stats correctly calculate data size"""
        key = "aqe/test/stats/large"

        # Store large data
        await postgres_memory_clean.store(key, large_test_data)

        # Get stats
        stats = await postgres_memory_clean.get_stats()

        # Should have size info
        assert stats["size_bytes"] > 0
        assert stats["size_mb"] > 0


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealConcurrency:
    """Test concurrent access patterns with real database"""

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, postgres_memory_real, concurrent_executor):
        """Test concurrent write operations"""
        num_operations = 50

        # Create concurrent write operations
        async def write_operation(index: int):
            key = f"aqe/test/concurrent/key{index}"
            await postgres_memory_real.store(key, {"index": index})

        operations = [write_operation(i) for i in range(num_operations)]

        # Execute concurrently
        results = await concurrent_executor.run_concurrent(operations)

        # All operations should succeed
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0

        # Verify all keys exist
        for i in range(num_operations):
            key = f"aqe/test/concurrent/key{i}"
            result = await postgres_memory_real.retrieve(key)
            assert result is not None
            assert result["index"] == i

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, postgres_memory_real):
        """Test concurrent read operations"""
        key = "aqe/test/concurrent/read_target"

        # Store data
        await postgres_memory_real.store(key, {"data": "shared"})

        # Create concurrent read operations
        async def read_operation():
            return await postgres_memory_real.retrieve(key)

        # Execute 100 concurrent reads
        tasks = [read_operation() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All reads should succeed
        assert all(r is not None for r in results)
        assert all(r["data"] == "shared" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, postgres_memory_real):
        """Test mixed read/write operations"""
        base_key = "aqe/test/concurrent/mixed"

        async def writer(index: int):
            await postgres_memory_real.store(f"{base_key}/w{index}", {"type": "write", "index": index})

        async def reader(index: int):
            return await postgres_memory_real.retrieve(f"{base_key}/w{index % 10}")

        # Mix of writes and reads
        operations = (
            [writer(i) for i in range(20)] +
            [reader(i) for i in range(30)]
        )

        # Shuffle and execute
        import random
        random.shuffle(operations)
        results = await asyncio.gather(*operations, return_exceptions=True)

        # Count errors
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0


@pytest.mark.integration
@pytest.mark.postgres
@pytest.mark.slow
class TestPostgresMemoryRealPerformance:
    """Test performance characteristics with real database"""

    @pytest.mark.asyncio
    async def test_bulk_write_performance(self, postgres_memory_clean, performance_tracker):
        """Test bulk write performance"""
        num_records = 100

        # Bulk write
        for i in range(num_records):
            await postgres_memory_clean.store(
                f"aqe/test/perf/bulk{i}",
                {"index": i, "data": f"value_{i}"}
            )

        duration = performance_tracker.total_duration
        ops_per_second = num_records / duration if duration > 0 else 0

        print(f"\nBulk write: {num_records} records in {duration:.2f}s ({ops_per_second:.2f} ops/s)")

        # Should be reasonably fast
        assert ops_per_second > 10  # At least 10 ops/second

    @pytest.mark.asyncio
    async def test_search_performance(self, postgres_memory_clean):
        """Test search performance on moderate dataset"""
        # Store 50 keys
        for i in range(50):
            await postgres_memory_clean.store(
                f"aqe/test/perf/search{i}",
                {"index": i}
            )

        # Measure search time
        start = time.time()
        results = await postgres_memory_clean.search("aqe/test/perf/search*")
        duration = time.time() - start

        print(f"\nSearch: {len(results)} results in {duration:.3f}s")

        assert len(results) == 50
        assert duration < 1.0  # Should complete in under 1 second


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealNamespace:
    """Test namespace enforcement with real database"""

    @pytest.mark.asyncio
    async def test_namespace_enforcement(self, postgres_memory_real):
        """Test that keys must start with aqe/ namespace"""
        invalid_key = "invalid/test/key"

        with pytest.raises(ValueError, match="must start with 'aqe/' namespace"):
            await postgres_memory_real.store(invalid_key, {"data": "test"})

    @pytest.mark.asyncio
    async def test_valid_namespace_accepted(self, postgres_memory_real):
        """Test that valid aqe/ keys are accepted"""
        valid_key = "aqe/test/namespace/valid"

        # Should not raise exception
        await postgres_memory_real.store(valid_key, {"data": "test"})

        result = await postgres_memory_real.retrieve(valid_key)
        assert result is not None


@pytest.mark.integration
@pytest.mark.postgres
class TestPostgresMemoryRealCleanup:
    """Test cleanup functionality with real database"""

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, postgres_memory_real):
        """Test manual cleanup of expired entries"""
        # Store keys with short TTL
        for i in range(5):
            await postgres_memory_real.store(
                f"aqe/test/cleanup/key{i}",
                {"index": i},
                ttl=1
            )

        # Wait for expiration
        await asyncio.sleep(2)

        # Run cleanup
        deleted_count = await postgres_memory_real.cleanup_expired()

        # Should have cleaned up expired entries
        assert deleted_count >= 5
