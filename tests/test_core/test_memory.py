"""Unit tests for QEMemory - Shared memory namespace for agent coordination"""

import pytest
import asyncio
from datetime import datetime
from lionagi_qe.core.memory import QEMemory


class TestQEMemory:
    """Test QEMemory basic operations"""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test QEMemory initialization"""
        memory = QEMemory()
        assert memory._store == {}
        assert memory._locks == {}
        assert memory._access_log == []

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, qe_memory):
        """Test storing and retrieving values"""
        key = "aqe/test/key1"
        value = {"test": "data", "number": 42}

        await qe_memory.store(key, value)
        retrieved = await qe_memory.retrieve(key)

        assert retrieved == value

    @pytest.mark.asyncio
    async def test_store_with_partition(self, qe_memory):
        """Test storing with partition"""
        key = "aqe/test/partitioned"
        value = "test_value"
        partition = "test_partition"

        await qe_memory.store(key, value, partition=partition)

        # Check internal structure
        assert key in qe_memory._store
        assert qe_memory._store[key]["value"] == value
        assert qe_memory._store[key]["partition"] == partition

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, qe_memory):
        """Test storing with TTL expiration"""
        key = "aqe/test/ttl"
        value = "expires_soon"
        ttl = 1  # 1 second

        await qe_memory.store(key, value, ttl=ttl)

        # Should exist immediately
        retrieved = await qe_memory.retrieve(key)
        assert retrieved == value

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be None after expiration
        expired = await qe_memory.retrieve(key)
        assert expired is None

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_key(self, qe_memory):
        """Test retrieving non-existent key"""
        result = await qe_memory.retrieve("aqe/nonexistent/key")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, qe_memory):
        """Test searching memory by regex pattern"""
        # Store multiple keys
        await qe_memory.store("aqe/test-plan/unit", {"type": "unit"})
        await qe_memory.store("aqe/test-plan/integration", {"type": "integration"})
        await qe_memory.store("aqe/coverage/report", {"coverage": 85})
        await qe_memory.store("aqe/test-plan/e2e", {"type": "e2e"})

        # Search for test-plan keys
        results = await qe_memory.search(r"aqe/test-plan/.*")

        assert len(results) == 3
        assert "aqe/test-plan/unit" in results
        assert "aqe/test-plan/integration" in results
        assert "aqe/test-plan/e2e" in results
        assert "aqe/coverage/report" not in results

    @pytest.mark.asyncio
    async def test_search_excludes_expired(self, qe_memory):
        """Test search excludes expired keys"""
        # Store key with short TTL
        await qe_memory.store("aqe/test/expired", "value", ttl=1)
        await qe_memory.store("aqe/test/valid", "value")

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Search should only return valid key
        results = await qe_memory.search(r"aqe/test/.*")
        assert len(results) == 1
        assert "aqe/test/valid" in results
        assert "aqe/test/expired" not in results

    @pytest.mark.asyncio
    async def test_delete(self, qe_memory):
        """Test deleting keys"""
        key = "aqe/test/delete_me"
        await qe_memory.store(key, "value")

        # Verify exists
        assert await qe_memory.retrieve(key) == "value"

        # Delete
        await qe_memory.delete(key)

        # Verify deleted
        assert await qe_memory.retrieve(key) is None
        assert key not in qe_memory._store

    @pytest.mark.asyncio
    async def test_clear_partition(self, qe_memory):
        """Test clearing all keys in a partition"""
        # Store keys in different partitions
        await qe_memory.store("key1", "value1", partition="partition_a")
        await qe_memory.store("key2", "value2", partition="partition_a")
        await qe_memory.store("key3", "value3", partition="partition_b")

        # Clear partition_a
        await qe_memory.clear_partition("partition_a")

        # Verify partition_a is cleared
        assert await qe_memory.retrieve("key1") is None
        assert await qe_memory.retrieve("key2") is None

        # Verify partition_b is intact
        assert await qe_memory.retrieve("key3") == "value3"

    @pytest.mark.asyncio
    async def test_list_keys(self, qe_memory):
        """Test listing all keys"""
        await qe_memory.store("aqe/test/key1", "value1")
        await qe_memory.store("aqe/test/key2", "value2")
        await qe_memory.store("aqe/coverage/key3", "value3")

        # List all keys
        all_keys = await qe_memory.list_keys()
        assert len(all_keys) == 3
        assert "aqe/test/key1" in all_keys

    @pytest.mark.asyncio
    async def test_list_keys_with_prefix(self, qe_memory):
        """Test listing keys with prefix filter"""
        await qe_memory.store("aqe/test/key1", "value1")
        await qe_memory.store("aqe/test/key2", "value2")
        await qe_memory.store("aqe/coverage/key3", "value3")

        # List with prefix
        filtered_keys = await qe_memory.list_keys(prefix="aqe/test")
        assert len(filtered_keys) == 2
        assert "aqe/test/key1" in filtered_keys
        assert "aqe/test/key2" in filtered_keys
        assert "aqe/coverage/key3" not in filtered_keys

    @pytest.mark.asyncio
    async def test_get_stats(self, qe_memory):
        """Test getting memory statistics"""
        # Store keys in different partitions
        await qe_memory.store("key1", "value1", partition="test")
        await qe_memory.store("key2", "value2", partition="test")
        await qe_memory.store("key3", "value3", partition="coverage")

        # Retrieve to generate access log
        await qe_memory.retrieve("key1")

        stats = await qe_memory.get_stats()

        assert stats["total_keys"] == 3
        assert stats["partitions"]["test"] == 2
        assert stats["partitions"]["coverage"] == 1
        assert stats["total_accesses"] > 0

    @pytest.mark.asyncio
    async def test_access_log(self, qe_memory):
        """Test access logging"""
        key = "aqe/test/logged"

        # Store operation
        await qe_memory.store(key, "value", partition="test")
        assert len(qe_memory._access_log) == 1
        assert qe_memory._access_log[0]["operation"] == "store"
        assert qe_memory._access_log[0]["key"] == key

        # Retrieve operation
        await qe_memory.retrieve(key)
        assert len(qe_memory._access_log) == 2
        assert qe_memory._access_log[1]["operation"] == "retrieve"

    @pytest.mark.asyncio
    async def test_concurrent_access(self, qe_memory):
        """Test concurrent access to same key is thread-safe"""
        key = "aqe/test/concurrent"

        async def store_value(value):
            await qe_memory.store(key, value)

        # Concurrent stores
        await asyncio.gather(
            store_value("value1"),
            store_value("value2"),
            store_value("value3")
        )

        # Should have one of the values (last write wins)
        result = await qe_memory.retrieve(key)
        assert result in ["value1", "value2", "value3"]

    @pytest.mark.asyncio
    async def test_export_state(self, qe_memory):
        """Test exporting memory state"""
        # Store some data
        await qe_memory.store("key1", "value1", partition="test")
        await qe_memory.store("key2", "value2", ttl=1)

        # Wait for second key to expire
        await asyncio.sleep(1.1)

        # Export state
        state = await qe_memory.export_state()

        assert "store" in state
        assert "stats" in state

        # Expired key should not be in export
        assert "key1" in state["store"]
        assert "key2" not in state["store"]

    @pytest.mark.asyncio
    async def test_import_state(self, qe_memory):
        """Test importing memory state"""
        # Create state to import
        state = {
            "store": {
                "key1": {
                    "value": "imported_value1",
                    "timestamp": datetime.now().timestamp(),
                    "ttl": None,
                    "partition": "imported"
                },
                "key2": {
                    "value": "imported_value2",
                    "timestamp": datetime.now().timestamp(),
                    "ttl": None,
                    "partition": "imported"
                }
            }
        }

        # Import
        await qe_memory.import_state(state)

        # Verify imported data
        assert await qe_memory.retrieve("key1") == "imported_value1"
        assert await qe_memory.retrieve("key2") == "imported_value2"

    @pytest.mark.asyncio
    async def test_namespace_pattern(self, qe_memory):
        """Test aqe/* namespace pattern"""
        # Store in different namespaces
        await qe_memory.store("aqe/test-plan/unit", {"tests": 10})
        await qe_memory.store("aqe/coverage/report", {"coverage": 85})
        await qe_memory.store("aqe/quality/metrics", {"score": 90})
        await qe_memory.store("aqe/performance/benchmark", {"time": 1.5})
        await qe_memory.store("aqe/security/scan", {"issues": 0})
        await qe_memory.store("aqe/patterns/learned", {"count": 5})
        await qe_memory.store("aqe/swarm/coordination", {"agents": 3})

        # Search each namespace
        test_plan = await qe_memory.search(r"aqe/test-plan/.*")
        coverage = await qe_memory.search(r"aqe/coverage/.*")
        quality = await qe_memory.search(r"aqe/quality/.*")

        assert len(test_plan) == 1
        assert len(coverage) == 1
        assert len(quality) == 1

    @pytest.mark.asyncio
    async def test_memory_persistence_cycle(self, qe_memory):
        """Test full export/import cycle"""
        # Store complex data
        await qe_memory.store("aqe/test/complex", {
            "nested": {"data": [1, 2, 3]},
            "string": "test",
            "number": 42
        }, partition="test")

        # Export
        exported = await qe_memory.export_state()

        # Create new memory instance
        new_memory = QEMemory()

        # Import
        await new_memory.import_state(exported)

        # Verify data integrity
        retrieved = await new_memory.retrieve("aqe/test/complex")
        assert retrieved["nested"]["data"] == [1, 2, 3]
        assert retrieved["string"] == "test"
        assert retrieved["number"] == 42
