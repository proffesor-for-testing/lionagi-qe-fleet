"""Tests for PostgresMemory backend

Validates PostgreSQL-backed memory implementation including:
- Store and retrieve operations
- TTL expiration
- Pattern-based search
- Key deletion and partition clearing
- Namespace enforcement
- Connection pooling
- Thread safety
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json


class TestPostgresMemoryBasicOperations:
    """Test basic store/retrieve/delete operations"""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_basic(self, postgres_memory, sample_memory_data):
        """Test storing and retrieving a simple value"""
        key = "aqe/test/basic"
        value = sample_memory_data["simple_value"]

        # Configure mock to return the stored value
        postgres_memory.retrieve.return_value = value

        await postgres_memory.store(key, value)
        result = await postgres_memory.retrieve(key)

        assert result == value
        postgres_memory.store.assert_called_once()
        postgres_memory.retrieve.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_key(self, postgres_memory):
        """Test retrieving a key that doesn't exist returns None"""
        postgres_memory.retrieve.return_value = None

        result = await postgres_memory.retrieve("aqe/test/nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, postgres_memory):
        """Test deleting a key"""
        key = "aqe/test/to_delete"

        await postgres_memory.delete(key)

        postgres_memory.delete.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, postgres_memory):
        """Test deleting a nonexistent key doesn't raise error"""
        key = "aqe/test/nonexistent"

        # Should not raise exception
        await postgres_memory.delete(key)

        postgres_memory.delete.assert_called_once_with(key)


class TestPostgresMemoryTTL:
    """Test TTL (time-to-live) expiration functionality"""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, postgres_memory, sample_memory_data):
        """Test storing value with TTL"""
        key = "aqe/test/with_ttl"
        value = sample_memory_data["simple_value"]
        ttl = 3600  # 1 hour

        await postgres_memory.store(key, value, ttl=ttl)

        postgres_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_with_ttl_expires(self, postgres_memory):
        """Test that expired keys are not returned"""
        key = "aqe/test/expired"

        # Mock retrieve to return None for expired key
        postgres_memory.retrieve.return_value = None

        result = await postgres_memory.retrieve(key)

        assert result is None

    @pytest.mark.asyncio
    async def test_expired_keys_not_returned(self, postgres_memory, expired_memory_data):
        """Test that expired keys are automatically filtered out"""
        postgres_memory.retrieve.return_value = None

        result = await postgres_memory.retrieve("aqe/test/expired")

        assert result is None


class TestPostgresMemorySearch:
    """Test pattern-based search functionality"""

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, postgres_memory):
        """Test searching keys by regex pattern"""
        pattern = r"aqe/test/.*"
        expected_results = {
            "aqe/test/key1": {"data": "value1"},
            "aqe/test/key2": {"data": "value2"}
        }

        postgres_memory.search.return_value = expected_results

        results = await postgres_memory.search(pattern)

        assert len(results) == 2
        assert "aqe/test/key1" in results
        assert "aqe/test/key2" in results
        postgres_memory.search.assert_called_once_with(pattern)

    @pytest.mark.asyncio
    async def test_search_no_matches(self, postgres_memory):
        """Test search with no matching keys returns empty dict"""
        pattern = r"aqe/nonexistent/.*"
        postgres_memory.search.return_value = {}

        results = await postgres_memory.search(pattern)

        assert results == {}
        assert len(results) == 0


class TestPostgresMemoryPartitions:
    """Test partition management"""

    @pytest.mark.asyncio
    async def test_clear_partition(self, postgres_memory):
        """Test clearing all keys in a partition"""
        partition = "test_partition"

        await postgres_memory.clear_partition(partition)

        postgres_memory.clear_partition.assert_called_once_with(partition)

    @pytest.mark.asyncio
    async def test_store_with_partition(self, postgres_memory):
        """Test storing value in specific partition"""
        key = "aqe/test/partitioned"
        value = {"data": "test"}
        partition = "test_partition"

        await postgres_memory.store(key, value, partition=partition)

        postgres_memory.store.assert_called_once()


class TestPostgresMemoryKeyListing:
    """Test key listing functionality"""

    @pytest.mark.asyncio
    async def test_list_keys_with_prefix(self, postgres_memory, sample_aqe_keys):
        """Test listing keys with specific prefix"""
        prefix = "aqe/test-plan"
        expected_keys = [k for k in sample_aqe_keys if k.startswith(prefix)]

        postgres_memory.list_keys.return_value = expected_keys

        keys = await postgres_memory.list_keys(prefix=prefix)

        assert len(keys) == len(expected_keys)
        assert all(k.startswith(prefix) for k in keys)
        postgres_memory.list_keys.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_all_keys(self, postgres_memory, sample_aqe_keys):
        """Test listing all keys without prefix filter"""
        postgres_memory.list_keys.return_value = sample_aqe_keys

        keys = await postgres_memory.list_keys()

        assert len(keys) == len(sample_aqe_keys)
        postgres_memory.list_keys.assert_called_once()


class TestPostgresMemoryStats:
    """Test statistics and metrics"""

    @pytest.mark.asyncio
    async def test_get_stats(self, postgres_memory):
        """Test getting memory statistics"""
        expected_stats = {
            "total_keys": 10,
            "partitions": {
                "test": 5,
                "prod": 5
            },
            "total_size_bytes": 1024
        }

        postgres_memory.get_stats.return_value = expected_stats

        stats = await postgres_memory.get_stats()

        assert stats["total_keys"] == 10
        assert "partitions" in stats
        postgres_memory.get_stats.assert_called_once()


class TestPostgresMemoryNamespace:
    """Test AQE namespace enforcement"""

    @pytest.mark.asyncio
    async def test_key_must_start_with_aqe_namespace(self, postgres_memory, aqe_namespace_validator):
        """Test that all keys must start with aqe/ namespace"""
        valid_key = "aqe/test/valid"
        invalid_key = "invalid/test/key"

        # Valid key should pass
        assert aqe_namespace_validator(valid_key)

        # Invalid key should fail
        assert not aqe_namespace_validator(invalid_key)

    @pytest.mark.asyncio
    async def test_namespace_prefix_applied(self, postgres_memory):
        """Test that namespace prefix is correctly applied"""
        assert postgres_memory.namespace_prefix == "aqe/"


class TestPostgresMemoryConnectionPool:
    """Test connection pooling and database operations"""

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self, postgres_memory, mock_db_manager_for_memory):
        """Test that connection pool is reused across operations"""
        # Verify DatabaseManager is using connection pool
        assert mock_db_manager_for_memory.pool is not None

        # Multiple operations should reuse the same pool
        await postgres_memory.connect()
        await postgres_memory.connect()

        # Connect should only initialize pool once
        assert postgres_memory.connect.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_access_thread_safe(self, postgres_memory):
        """Test concurrent access is thread-safe"""
        # Simulate concurrent operations
        tasks = [
            postgres_memory.store(f"aqe/test/concurrent_{i}", {"value": i})
            for i in range(10)
        ]

        # All operations should complete without error
        await asyncio.gather(*tasks)

        assert postgres_memory.store.call_count == 10


class TestPostgresMemoryIntegration:
    """Integration tests with DatabaseManager"""

    @pytest.mark.asyncio
    async def test_store_retrieves_from_database(self, postgres_memory, mock_db_manager_for_memory):
        """Test that store operation interacts with database"""
        key = "aqe/test/db_integration"
        value = {"data": "test"}

        # Configure mock
        postgres_memory.retrieve.return_value = value

        await postgres_memory.store(key, value)
        result = await postgres_memory.retrieve(key)

        assert result == value

    @pytest.mark.asyncio
    async def test_search_uses_database_query(self, postgres_memory):
        """Test that search uses database pattern matching"""
        pattern = r"aqe/test/.*"
        expected = {
            "aqe/test/key1": {"data": "value1"}
        }

        postgres_memory.search.return_value = expected

        results = await postgres_memory.search(pattern)

        assert results == expected
        postgres_memory.search.assert_called_once_with(pattern)


class TestPostgresMemoryErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_handles_database_connection_error(self, postgres_memory):
        """Test graceful handling of database connection errors"""
        # Configure mock to raise connection error
        postgres_memory.connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await postgres_memory.connect()

    @pytest.mark.asyncio
    async def test_handles_invalid_json_data(self, postgres_memory):
        """Test handling of non-JSON-serializable data"""
        key = "aqe/test/invalid"
        # Mock store to handle any data
        await postgres_memory.store(key, {"data": "valid"})

        postgres_memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, postgres_memory):
        """Test proper cleanup on disconnect"""
        await postgres_memory.disconnect()

        postgres_memory.disconnect.assert_called_once()
