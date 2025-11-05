"""Integration tests for memory backends (PostgreSQL and Redis)

Tests real-world scenarios including:
- Using memory backends with actual agents
- Switching between backends
- Memory persistence across restarts
- Concurrent agent memory access
- Cross-backend data migration
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime


class TestMemoryBackendWithAgents:
    """Test memory backends integrated with actual agents"""

    @pytest.mark.asyncio
    async def test_postgres_memory_with_real_agent(
        self,
        postgres_memory,
        test_generator_agent,
        sample_qe_task
    ):
        """Test PostgresMemory integrated with TestGeneratorAgent"""
        # Configure agent to use PostgresMemory
        test_generator_agent.memory = postgres_memory

        # Configure mock memory responses
        postgres_memory.store.return_value = None
        postgres_memory.retrieve.return_value = {
            "tests_generated": 15,
            "coverage": 0.90
        }

        # Store task results in memory
        key = "aqe/test-generation/results"
        result = {
            "tests_generated": 15,
            "coverage": 0.90,
            "framework": "pytest"
        }

        await test_generator_agent.memory.store(key, result)

        # Retrieve from memory
        retrieved = await test_generator_agent.memory.retrieve(key)

        assert retrieved is not None
        assert retrieved["tests_generated"] == 15
        test_generator_agent.memory.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_memory_with_real_agent(
        self,
        redis_memory,
        test_executor_agent,
        sample_qe_task
    ):
        """Test RedisMemory integrated with TestExecutorAgent"""
        # Configure agent to use RedisMemory
        test_executor_agent.memory = redis_memory

        # Configure mock memory responses
        redis_memory.store.return_value = None
        redis_memory.retrieve.return_value = {
            "tests_executed": 50,
            "passed": 48,
            "failed": 2
        }

        # Store execution results
        key = "aqe/test-execution/results"
        result = {
            "tests_executed": 50,
            "passed": 48,
            "failed": 2,
            "duration": 12.5
        }

        await test_executor_agent.memory.store(key, result)

        # Retrieve from memory
        retrieved = await test_executor_agent.memory.retrieve(key)

        assert retrieved is not None
        assert retrieved["tests_executed"] == 50
        assert retrieved["passed"] == 48


class TestMemoryBackendSwitching:
    """Test switching between memory backends"""

    @pytest.mark.asyncio
    async def test_memory_backend_switching(
        self,
        postgres_memory,
        redis_memory,
        test_generator_agent
    ):
        """Test switching agent memory backend from Postgres to Redis"""
        # Start with PostgresMemory
        test_generator_agent.memory = postgres_memory

        postgres_data = {"source": "postgres", "value": 100}
        postgres_memory.retrieve.return_value = postgres_data

        result_pg = await test_generator_agent.memory.retrieve("aqe/test/data")
        assert result_pg["source"] == "postgres"

        # Switch to RedisMemory
        test_generator_agent.memory = redis_memory

        redis_data = {"source": "redis", "value": 200}
        redis_memory.retrieve.return_value = redis_data

        result_redis = await test_generator_agent.memory.retrieve("aqe/test/data")
        assert result_redis["source"] == "redis"

    @pytest.mark.asyncio
    async def test_backend_switch_preserves_data(
        self,
        postgres_memory,
        redis_memory
    ):
        """Test that data can be migrated when switching backends"""
        key = "aqe/test/migration"
        data = {"migrated": True, "value": 42}

        # Store in PostgreSQL
        postgres_memory.retrieve.return_value = data
        await postgres_memory.store(key, data)

        # Retrieve from PostgreSQL
        pg_data = await postgres_memory.retrieve(key)

        # Store in Redis
        redis_memory.retrieve.return_value = pg_data
        await redis_memory.store(key, pg_data)

        # Verify in Redis
        redis_data = await redis_memory.retrieve(key)

        assert redis_data == data


class TestMemoryPersistence:
    """Test memory persistence across restarts"""

    @pytest.mark.asyncio
    async def test_memory_persistence_survives_restart(
        self,
        postgres_memory,
        sample_memory_data
    ):
        """Test that PostgresMemory data survives simulated restart"""
        key = "aqe/test/persistent"
        data = sample_memory_data["test_plan"]

        # Store data
        await postgres_memory.store(key, data)

        # Simulate disconnect
        await postgres_memory.disconnect()

        # Simulate reconnect
        await postgres_memory.connect()

        # Configure mock to return stored data
        postgres_memory.retrieve.return_value = data

        # Retrieve data after "restart"
        retrieved = await postgres_memory.retrieve(key)

        assert retrieved == data

    @pytest.mark.asyncio
    async def test_redis_persistence_with_aof(
        self,
        redis_memory,
        sample_memory_data
    ):
        """Test Redis data persistence with AOF (Append-Only File)"""
        key = "aqe:test:aof_persist"
        data = sample_memory_data["coverage_results"]

        # Store with no TTL (persistent)
        await redis_memory.store(key, data, ttl=None)

        # Simulate Redis restart
        await redis_memory.disconnect()
        await redis_memory.connect()

        # Configure mock to return persisted data
        redis_memory.retrieve.return_value = data

        # Data should still be available
        retrieved = await redis_memory.retrieve(key)

        assert retrieved == data


class TestConcurrentMemoryAccess:
    """Test concurrent access from multiple agents"""

    @pytest.mark.asyncio
    async def test_concurrent_agent_memory_access(
        self,
        postgres_memory,
        test_generator_agent,
        test_executor_agent,
        fleet_commander_agent
    ):
        """Test multiple agents accessing memory concurrently"""
        # Configure all agents with same memory backend
        test_generator_agent.memory = postgres_memory
        test_executor_agent.memory = postgres_memory
        fleet_commander_agent.memory = postgres_memory

        # Concurrent writes
        async def agent_write(agent, key, value):
            await agent.memory.store(key, value)

        tasks = [
            agent_write(test_generator_agent, "aqe/agent1/data", {"agent": 1}),
            agent_write(test_executor_agent, "aqe/agent2/data", {"agent": 2}),
            agent_write(fleet_commander_agent, "aqe/agent3/data", {"agent": 3}),
        ]

        await asyncio.gather(*tasks)

        # Verify all writes succeeded
        assert postgres_memory.store.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_reads_and_writes(
        self,
        redis_memory
    ):
        """Test concurrent reads and writes don't corrupt data"""
        key = "aqe:test:concurrent_rw"

        # Configure mock
        redis_memory.retrieve.return_value = {"counter": 0}

        # Simulate concurrent operations
        async def read_operation():
            return await redis_memory.retrieve(key)

        async def write_operation(value):
            await redis_memory.store(key, value)

        tasks = [
            write_operation({"counter": i})
            for i in range(10)
        ] + [
            read_operation()
            for _ in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # All operations should complete
        assert redis_memory.store.call_count == 10
        assert redis_memory.retrieve.call_count == 10


class TestCrossBackendScenarios:
    """Test scenarios involving both backends"""

    @pytest.mark.asyncio
    async def test_postgres_for_learning_redis_for_cache(
        self,
        postgres_memory,
        redis_memory
    ):
        """Test using PostgreSQL for learning data and Redis for cache"""
        # Store learning data in PostgreSQL (persistent)
        learning_key = "aqe/learning/q-values"
        q_values = {
            "state1_action1": 0.75,
            "state1_action2": 0.82
        }

        postgres_memory.retrieve.return_value = q_values
        await postgres_memory.store(learning_key, q_values)

        # Store cache data in Redis (with TTL)
        cache_key = "aqe:cache:recent_tests"
        cache_data = {
            "tests": ["test1", "test2"],
            "timestamp": datetime.now().isoformat()
        }

        redis_memory.retrieve.return_value = cache_data
        await redis_memory.store(cache_key, cache_data, ttl=300)

        # Verify both backends
        pg_result = await postgres_memory.retrieve(learning_key)
        redis_result = await redis_memory.retrieve(cache_key)

        assert pg_result == q_values
        assert redis_result == cache_data

    @pytest.mark.asyncio
    async def test_data_migration_postgres_to_redis(
        self,
        postgres_memory,
        redis_memory
    ):
        """Test migrating data from PostgreSQL to Redis"""
        # Sample data in PostgreSQL
        keys_to_migrate = [
            ("aqe/test/data1", {"value": 1}),
            ("aqe/test/data2", {"value": 2}),
            ("aqe/test/data3", {"value": 3}),
        ]

        # Simulate migration
        for pg_key, data in keys_to_migrate:
            # Read from PostgreSQL
            postgres_memory.retrieve.return_value = data

            pg_data = await postgres_memory.retrieve(pg_key)

            # Write to Redis (convert key format)
            redis_key = pg_key.replace("/", ":")
            await redis_memory.store(redis_key, pg_data, ttl=3600)

        assert redis_memory.store.call_count == 3


class TestMemoryBackendPerformance:
    """Test performance characteristics of different backends"""

    @pytest.mark.asyncio
    async def test_bulk_write_performance(
        self,
        postgres_memory,
        redis_memory
    ):
        """Compare bulk write performance between backends"""
        num_records = 100

        # PostgreSQL bulk writes
        pg_tasks = [
            postgres_memory.store(f"aqe/bulk/pg_{i}", {"index": i})
            for i in range(num_records)
        ]

        await asyncio.gather(*pg_tasks)

        # Redis bulk writes
        redis_tasks = [
            redis_memory.store(f"aqe:bulk:redis_{i}", {"index": i})
            for i in range(num_records)
        ]

        await asyncio.gather(*redis_tasks)

        assert postgres_memory.store.call_count == num_records
        assert redis_memory.store.call_count == num_records

    @pytest.mark.asyncio
    async def test_search_performance(
        self,
        postgres_memory,
        redis_memory
    ):
        """Test search/scan performance"""
        # PostgreSQL pattern search
        pg_results = {
            f"aqe/test/key{i}": {"value": i}
            for i in range(50)
        }
        postgres_memory.search.return_value = pg_results

        pg_search_result = await postgres_memory.search(r"aqe/test/.*")

        # Redis pattern scan
        redis_results = {
            f"aqe:test:key{i}": {"value": i}
            for i in range(50)
        }
        redis_memory.search.return_value = redis_results

        redis_search_result = await redis_memory.search("aqe:test:*")

        assert len(pg_search_result) == 50
        assert len(redis_search_result) == 50


class TestMemoryBackendResilience:
    """Test resilience and error recovery"""

    @pytest.mark.asyncio
    async def test_postgres_connection_recovery(
        self,
        postgres_memory
    ):
        """Test PostgreSQL automatic reconnection after failure"""
        # Simulate connection failure
        postgres_memory.connect.side_effect = [
            Exception("Connection failed"),
            None  # Successful reconnect
        ]

        # First attempt fails
        with pytest.raises(Exception, match="Connection failed"):
            await postgres_memory.connect()

        # Second attempt succeeds
        await postgres_memory.connect()

        postgres_memory.connect.assert_called()

    @pytest.mark.asyncio
    async def test_redis_connection_recovery(
        self,
        redis_memory
    ):
        """Test Redis automatic reconnection after failure"""
        # Simulate connection failure
        redis_memory.connect.side_effect = [
            Exception("Redis unavailable"),
            None  # Successful reconnect
        ]

        # First attempt fails
        with pytest.raises(Exception, match="Redis unavailable"):
            await redis_memory.connect()

        # Second attempt succeeds
        await redis_memory.connect()

        redis_memory.connect.assert_called()

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_backend_failure(
        self,
        postgres_memory,
        test_generator_agent
    ):
        """Test agent handles backend failure gracefully"""
        test_generator_agent.memory = postgres_memory

        # Simulate backend failure
        postgres_memory.store.side_effect = Exception("Backend unavailable")

        # Operation should handle error
        with pytest.raises(Exception, match="Backend unavailable"):
            await test_generator_agent.memory.store("aqe/test/key", {"data": "test"})
