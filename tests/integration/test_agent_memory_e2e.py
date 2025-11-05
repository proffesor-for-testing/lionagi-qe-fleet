"""End-to-End Agent Memory Integration Tests

Tests real agents using real PostgreSQL and Redis backends.
Verifies agent coordination through shared memory and Q-learning persistence.

Run with:
    docker-compose -f docker-compose-test.yml up -d
    pytest tests/integration/test_agent_memory_e2e.py -v -m integration
"""

import pytest
import asyncio
from lionagi import iModel
from lionagi_qe.agents.test_generator import TestGeneratorAgent
from lionagi_qe.agents.test_executor import TestExecutorAgent
from lionagi_qe.agents.fleet_commander import FleetCommanderAgent
from lionagi_qe.agents.coverage_analyzer import CoverageAnalyzerAgent


@pytest.mark.integration
@pytest.mark.postgres
class TestAgentPostgresMemoryE2E:
    """Test agents with real PostgreSQL memory backend"""

    @pytest.mark.asyncio
    async def test_test_generator_stores_results(self, postgres_memory_clean):
        """Test that TestGeneratorAgent can store results in PostgreSQL"""
        # Create agent with real memory
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = TestGeneratorAgent(
            agent_id="test-gen-e2e",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Simulate storing test generation results
        key = "aqe/test-plan/e2e/generated"
        test_results = {
            "tests": [
                {"name": "test_add", "type": "unit"},
                {"name": "test_subtract", "type": "unit"}
            ],
            "framework": "pytest",
            "coverage_target": 0.95
        }

        await agent.memory_backend.store(key, test_results)

        # Verify stored
        result = await agent.memory_backend.retrieve(key)
        assert result is not None
        assert len(result["tests"]) == 2
        assert result["framework"] == "pytest"

    @pytest.mark.asyncio
    async def test_agent_coordination_via_memory(self, postgres_memory_clean):
        """Test two agents coordinating through shared PostgreSQL memory"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create two agents sharing same memory backend
        generator = TestGeneratorAgent(
            agent_id="generator-e2e",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        executor = TestExecutorAgent(
            agent_id="executor-e2e",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Generator stores test plan
        plan_key = "aqe/coordination/test-plan"
        test_plan = {
            "tests": ["test_one", "test_two", "test_three"],
            "status": "generated"
        }
        await generator.memory_backend.store(plan_key, test_plan)

        # Executor reads test plan
        plan = await executor.memory_backend.retrieve(plan_key)
        assert plan is not None
        assert plan["status"] == "generated"
        assert len(plan["tests"]) == 3

        # Executor stores execution results
        results_key = "aqe/coordination/test-results"
        execution_results = {
            "tests_run": 3,
            "passed": 3,
            "failed": 0,
            "status": "executed"
        }
        await executor.memory_backend.store(results_key, execution_results)

        # Generator reads execution results
        results = await generator.memory_backend.retrieve(results_key)
        assert results is not None
        assert results["tests_run"] == 3
        assert results["status"] == "executed"

    @pytest.mark.asyncio
    async def test_fleet_coordination_pattern(self, postgres_memory_clean):
        """Test fleet commander coordinating multiple agents"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create fleet commander
        commander = FleetCommanderAgent(
            agent_id="commander-e2e",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Create specialized agents
        generator = TestGeneratorAgent(
            agent_id="generator-fleet",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        executor = TestExecutorAgent(
            agent_id="executor-fleet",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Commander creates coordination plan
        coord_key = "aqe/fleet/coordination/plan"
        coordination_plan = {
            "agents": ["generator-fleet", "executor-fleet"],
            "workflow": ["generate", "execute", "analyze"],
            "status": "planning"
        }
        await commander.memory_backend.store(coord_key, coordination_plan)

        # Agents read coordination plan
        plan = await generator.memory_backend.retrieve(coord_key)
        assert plan is not None
        assert "generator-fleet" in plan["agents"]

        # Agents report status
        await generator.memory_backend.store(
            "aqe/fleet/status/generator-fleet",
            {"status": "ready", "task": "generate"}
        )

        await executor.memory_backend.store(
            "aqe/fleet/status/executor-fleet",
            {"status": "ready", "task": "execute"}
        )

        # Commander reads agent statuses
        gen_status = await commander.memory_backend.retrieve("aqe/fleet/status/generator-fleet")
        exec_status = await commander.memory_backend.retrieve("aqe/fleet/status/executor-fleet")

        assert gen_status["status"] == "ready"
        assert exec_status["status"] == "ready"

    @pytest.mark.asyncio
    async def test_q_learning_persistence(self, postgres_db_manager, postgres_memory_clean):
        """Test Q-learning state persists across agent restarts"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create agent with learning enabled
        agent1 = TestGeneratorAgent(
            agent_id="learner-e2e",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=True
        )

        # Store learning data
        learning_key = "aqe/learning/e2e/q-values"
        q_values = {
            "state_action_1": 0.85,
            "state_action_2": 0.92,
            "state_action_3": 0.78
        }
        await agent1.memory_backend.store(learning_key, q_values)

        # Simulate agent restart - create new instance
        agent2 = TestGeneratorAgent(
            agent_id="learner-e2e",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=True
        )

        # New agent should be able to retrieve learned values
        learned = await agent2.memory_backend.retrieve(learning_key)
        assert learned is not None
        assert learned["state_action_1"] == 0.85
        assert learned["state_action_2"] == 0.92


@pytest.mark.integration
@pytest.mark.redis
class TestAgentRedisMemoryE2E:
    """Test agents with real Redis memory backend"""

    @pytest.mark.asyncio
    async def test_test_executor_stores_results(self, redis_memory_real):
        """Test that TestExecutorAgent can store results in Redis"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = TestExecutorAgent(
            agent_id="executor-redis-e2e",
            model=model,
            memory_backend=redis_memory_real,
            enable_learning=False
        )

        # Store execution results
        key = "aqe/execution/e2e/results"
        execution_results = {
            "tests_run": 50,
            "passed": 48,
            "failed": 2,
            "duration": 12.5,
            "timestamp": "2024-01-01T00:00:00Z"
        }

        await agent.memory_backend.store(key, execution_results)

        # Verify stored
        result = await agent.memory_backend.retrieve(key)
        assert result is not None
        assert result["tests_run"] == 50
        assert result["passed"] == 48

    @pytest.mark.asyncio
    async def test_high_frequency_agent_coordination(self, redis_memory_real):
        """Test high-frequency coordination between agents using Redis"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create agents
        agents = [
            TestGeneratorAgent(
                agent_id=f"agent-{i}",
                model=model,
                memory_backend=redis_memory_real,
                enable_learning=False
            )
            for i in range(5)
        ]

        # Simulate high-frequency status updates
        async def agent_heartbeat(agent, iteration):
            key = f"aqe/heartbeat/{agent.agent_id}"
            await agent.memory_backend.store(
                key,
                {"status": "active", "iteration": iteration},
                ttl=10  # Short TTL for heartbeats
            )

        # Run 10 iterations of heartbeats
        for iteration in range(10):
            tasks = [agent_heartbeat(agent, iteration) for agent in agents]
            await asyncio.gather(*tasks)

        # Verify all agents have latest heartbeat
        for agent in agents:
            key = f"aqe/heartbeat/{agent.agent_id}"
            heartbeat = await agent.memory_backend.retrieve(key)
            assert heartbeat is not None
            assert heartbeat["iteration"] == 9

    @pytest.mark.asyncio
    async def test_agent_cache_pattern(self, redis_memory_real):
        """Test using Redis as cache for expensive operations"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = TestGeneratorAgent(
            agent_id="caching-agent",
            model=model,
            memory_backend=redis_memory_real,
            enable_learning=False
        )

        # Store cache with TTL
        cache_key = "aqe/cache/expensive-computation"
        computation_result = {
            "result": [1, 2, 3, 4, 5],
            "computation_time": 5.2,
            "cached": True
        }

        await agent.memory_backend.store(cache_key, computation_result, ttl=300)

        # Retrieve from cache
        cached = await agent.memory_backend.retrieve(cache_key)
        assert cached is not None
        assert cached["cached"] is True

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_session_based_coordination(self, redis_memory_real):
        """Test session-based coordination with TTL"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create session coordinator
        coordinator = FleetCommanderAgent(
            agent_id="session-coordinator",
            model=model,
            memory_backend=redis_memory_real,
            enable_learning=False
        )

        # Create session with short TTL
        session_key = "aqe/session/test-session-123"
        session_data = {
            "session_id": "test-session-123",
            "participants": ["agent-1", "agent-2"],
            "status": "active"
        }

        await coordinator.memory_backend.store(session_key, session_data, ttl=2)

        # Session should be active
        session = await coordinator.memory_backend.retrieve(session_key)
        assert session is not None
        assert session["status"] == "active"

        # Wait for session to expire
        await asyncio.sleep(3)

        # Session should be gone
        expired_session = await coordinator.memory_backend.retrieve(session_key)
        assert expired_session is None


@pytest.mark.integration
@pytest.mark.postgres
@pytest.mark.redis
class TestHybridMemoryE2E:
    """Test agents using both PostgreSQL and Redis"""

    @pytest.mark.asyncio
    async def test_postgres_for_persistence_redis_for_cache(
        self,
        postgres_memory_clean,
        redis_memory_real
    ):
        """Test using PostgreSQL for long-term storage and Redis for caching"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Agent with PostgreSQL for persistent data
        persistent_agent = TestGeneratorAgent(
            agent_id="persistent-agent",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Agent with Redis for temporary cache
        cache_agent = TestGeneratorAgent(
            agent_id="cache-agent",
            model=model,
            memory_backend=redis_memory_real,
            enable_learning=False
        )

        # Store long-term data in PostgreSQL
        persistent_key = "aqe/persistent/test-patterns"
        patterns = {
            "pattern1": {"template": "test_{method}", "count": 10},
            "pattern2": {"template": "test_{module}_{method}", "count": 25}
        }
        await persistent_agent.memory_backend.store(persistent_key, patterns, ttl=None)

        # Store temporary cache in Redis
        cache_key = "aqe/cache/recent-tests"
        recent = {
            "tests": ["test_a", "test_b", "test_c"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        await cache_agent.memory_backend.store(cache_key, recent, ttl=300)

        # Verify both storages
        persistent_data = await persistent_agent.memory_backend.retrieve(persistent_key)
        cached_data = await cache_agent.memory_backend.retrieve(cache_key)

        assert persistent_data is not None
        assert cached_data is not None

    @pytest.mark.asyncio
    async def test_data_migration_between_backends(
        self,
        postgres_memory_clean,
        redis_memory_real
    ):
        """Test migrating data from Redis to PostgreSQL"""
        # Store data in Redis (temporary)
        temp_key = "aqe/temp/migration-test"
        data = {
            "status": "processing",
            "items": [1, 2, 3, 4, 5]
        }
        await redis_memory_real.store(temp_key, data, ttl=60)

        # Read from Redis
        redis_data = await redis_memory_real.retrieve(temp_key)
        assert redis_data is not None

        # Migrate to PostgreSQL (permanent)
        permanent_key = "aqe/permanent/migrated-data"
        await postgres_memory_clean.store(permanent_key, redis_data, ttl=None)

        # Verify in PostgreSQL
        postgres_data = await postgres_memory_clean.retrieve(permanent_key)
        assert postgres_data == redis_data

        # Delete from Redis
        await redis_memory_real.delete(temp_key)

        # Verify migration successful
        assert await redis_memory_real.retrieve(temp_key) is None
        assert await postgres_memory_clean.retrieve(permanent_key) is not None


@pytest.mark.integration
@pytest.mark.postgres
class TestConcurrentAgentAccess:
    """Test multiple agents accessing memory concurrently"""

    @pytest.mark.asyncio
    async def test_multiple_agents_concurrent_writes(
        self,
        postgres_memory_clean,
        concurrent_executor
    ):
        """Test multiple agents writing concurrently"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create multiple agents
        agents = [
            TestGeneratorAgent(
                agent_id=f"concurrent-agent-{i}",
                model=model,
                memory_backend=postgres_memory_clean,
                enable_learning=False
            )
            for i in range(10)
        ]

        # Each agent writes its own data
        async def agent_write(agent, index):
            key = f"aqe/concurrent/agent/{agent.agent_id}"
            await agent.memory_backend.store(key, {"agent_id": agent.agent_id, "index": index})

        operations = [agent_write(agent, i) for i, agent in enumerate(agents)]

        # Execute concurrently
        results = await concurrent_executor.run_concurrent(operations)

        # All should succeed
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0

        # Verify all writes
        for agent in agents:
            key = f"aqe/concurrent/agent/{agent.agent_id}"
            data = await agent.memory_backend.retrieve(key)
            assert data is not None
            assert data["agent_id"] == agent.agent_id

    @pytest.mark.asyncio
    async def test_agents_reading_shared_data(self, postgres_memory_clean):
        """Test multiple agents reading shared data concurrently"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Store shared configuration
        config_key = "aqe/shared/configuration"
        config = {
            "framework": "pytest",
            "coverage_threshold": 0.80,
            "parallel": True
        }
        await postgres_memory_clean.store(config_key, config)

        # Create multiple agents
        agents = [
            TestGeneratorAgent(
                agent_id=f"reader-{i}",
                model=model,
                memory_backend=postgres_memory_clean,
                enable_learning=False
            )
            for i in range(20)
        ]

        # All agents read concurrently
        async def agent_read(agent):
            return await agent.memory_backend.retrieve(config_key)

        tasks = [agent_read(agent) for agent in agents]
        results = await asyncio.gather(*tasks)

        # All reads should succeed and return same data
        assert all(r is not None for r in results)
        assert all(r["framework"] == "pytest" for r in results)
        assert all(r["coverage_threshold"] == 0.80 for r in results)

    @pytest.mark.asyncio
    async def test_agent_work_queue_pattern(self, redis_memory_real):
        """Test work queue coordination pattern"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Create producer agent
        producer = FleetCommanderAgent(
            agent_id="producer",
            model=model,
            memory_backend=redis_memory_real,
            enable_learning=False
        )

        # Create consumer agents
        consumers = [
            TestExecutorAgent(
                agent_id=f"consumer-{i}",
                model=model,
                memory_backend=redis_memory_real,
                enable_learning=False
            )
            for i in range(3)
        ]

        # Producer creates work items
        work_items = []
        for i in range(10):
            work_key = f"aqe/workqueue/item-{i}"
            work_data = {
                "task": f"test_task_{i}",
                "status": "pending",
                "priority": i % 3
            }
            await producer.memory_backend.store(work_key, work_data)
            work_items.append(work_key)

        # Consumers process work items concurrently
        async def process_work(consumer, work_key):
            work = await consumer.memory_backend.retrieve(work_key)
            if work:
                # Mark as processed
                work["status"] = "completed"
                work["processed_by"] = consumer.agent_id
                await consumer.memory_backend.store(work_key, work)

        # Distribute work
        tasks = []
        for i, work_key in enumerate(work_items):
            consumer = consumers[i % len(consumers)]
            tasks.append(process_work(consumer, work_key))

        await asyncio.gather(*tasks)

        # Verify all work completed
        for work_key in work_items:
            work = await redis_memory_real.retrieve(work_key)
            assert work["status"] == "completed"
            assert "processed_by" in work


@pytest.mark.integration
@pytest.mark.postgres
@pytest.mark.slow
class TestMemoryResilience:
    """Test memory backend resilience and recovery"""

    @pytest.mark.asyncio
    async def test_agent_continues_after_memory_error(self, postgres_memory_clean):
        """Test agent handles memory errors gracefully"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")
        agent = TestGeneratorAgent(
            agent_id="resilient-agent",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Store valid data
        await agent.memory_backend.store("aqe/resilience/valid", {"data": "valid"})

        # Try to store invalid key (should raise error)
        try:
            await agent.memory_backend.store("invalid_key", {"data": "invalid"})
        except ValueError:
            pass  # Expected

        # Agent should still function after error
        result = await agent.memory_backend.retrieve("aqe/resilience/valid")
        assert result is not None
        assert result["data"] == "valid"

    @pytest.mark.asyncio
    async def test_memory_backend_isolation(self, postgres_memory_clean, redis_memory_real):
        """Test that memory backends are isolated"""
        model = iModel(provider="openai", model="gpt-3.5-turbo")

        # Agent using PostgreSQL
        pg_agent = TestGeneratorAgent(
            agent_id="pg-agent",
            model=model,
            memory_backend=postgres_memory_clean,
            enable_learning=False
        )

        # Agent using Redis
        redis_agent = TestGeneratorAgent(
            agent_id="redis-agent",
            model=model,
            memory_backend=redis_memory_real,
            enable_learning=False
        )

        # Store in PostgreSQL
        await pg_agent.memory_backend.store("aqe/isolation/pg-data", {"backend": "postgres"})

        # Store in Redis
        await redis_agent.memory_backend.store("aqe/isolation/redis-data", {"backend": "redis"})

        # Data should be isolated
        pg_data = await pg_agent.memory_backend.retrieve("aqe/isolation/pg-data")
        redis_data = await redis_agent.memory_backend.retrieve("aqe/isolation/redis-data")

        assert pg_data is not None
        assert redis_data is not None
        assert pg_data["backend"] == "postgres"
        assert redis_data["backend"] == "redis"

        # Cross-backend retrieval should fail
        assert await pg_agent.memory_backend.retrieve("aqe/isolation/redis-data") is None
        assert await redis_agent.memory_backend.retrieve("aqe/isolation/pg-data") is None
