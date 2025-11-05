"""
Memory Backends Comparison Example

This example demonstrates all 3 memory backends available for BaseQEAgent:

1. PostgresMemory (recommended for production):
   - Reuses Q-learning database infrastructure
   - Full persistence with ACID guarantees
   - Best for: Production deployments, multi-agent coordination

2. RedisMemory (high-speed cache):
   - Sub-millisecond latency
   - Optional persistence (RDB/AOF)
   - Best for: High-frequency operations, temporary caching

3. Session.context (default, in-memory):
   - Zero setup, automatic
   - No persistence (lost on restart)
   - Best for: Development, testing, single-agent workflows

Usage:
    python examples/memory_backends_comparison.py
"""

import asyncio
from lionagi import iModel
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.task import QETask


# Example agent implementation
class ExampleTestGenerator(BaseQEAgent):
    """Example test generator agent"""

    def get_system_prompt(self) -> str:
        return """You are a test generator agent that creates comprehensive test suites.
        You analyze code and generate unit tests, integration tests, and edge case tests."""

    async def execute(self, task: QETask):
        """Generate tests for the given module"""
        module_path = task.context.get("module_path", "unknown")
        framework = task.context.get("framework", "pytest")

        # Simulate test generation
        tests = [
            f"test_{module_path.replace('/', '_')}_basic",
            f"test_{module_path.replace('/', '_')}_edge_cases",
            f"test_{module_path.replace('/', '_')}_integration"
        ]

        result = {
            "success": True,
            "tests_generated": len(tests),
            "tests": tests,
            "framework": framework,
            "module": module_path
        }

        # Store result in shared memory
        await self.store_result("generated_tests", result)

        return result


async def example_1_postgres_memory():
    """Example 1: PostgresMemory (Production-Ready)"""
    print("\n" + "=" * 70)
    print("Example 1: PostgresMemory - Production-Ready Persistent Storage")
    print("=" * 70)

    try:
        from lionagi_qe.learning import DatabaseManager
        from lionagi_qe.persistence import PostgresMemory

        # Setup: Initialize database connection
        db_manager = DatabaseManager(
            database_url="postgresql://qe_agent:password@localhost:5432/lionagi_qe_learning",
            min_connections=2,
            max_connections=10
        )

        print("\n1. Connecting to PostgreSQL database...")
        await db_manager.connect()
        print("   ✅ Connected to PostgreSQL")

        # Create memory backend (reuses same connection pool as Q-learning!)
        print("\n2. Creating PostgresMemory backend...")
        memory = PostgresMemory(db_manager)
        print("   ✅ PostgresMemory initialized (reuses Q-learning connection pool)")

        # Create agent with PostgresMemory
        print("\n3. Creating agent with PostgresMemory...")
        model = iModel(provider="openai", model="gpt-4o-mini")
        agent = ExampleTestGenerator(
            agent_id="test-generator-postgres",
            model=model,
            memory=memory
        )
        print(f"   ✅ Agent created with backend: {agent.memory_backend_type}")

        # Use the agent
        print("\n4. Using agent with persistent memory...")

        # Store some data
        await agent.store_memory(
            "aqe/test-plan/module_a",
            {
                "module": "user_service",
                "tests_needed": ["auth", "profile", "settings"],
                "priority": "high"
            },
            ttl=3600  # 1 hour
        )
        print("   ✅ Stored test plan in PostgreSQL")

        # Retrieve data
        test_plan = await agent.get_memory("aqe/test-plan/module_a")
        print(f"   ✅ Retrieved test plan: {test_plan}")

        # Search patterns
        all_plans = await agent.search_memory("aqe/test-plan/.*")
        print(f"   ✅ Found {len(all_plans)} test plans")

        # Get stats
        stats = await memory.get_stats()
        print(f"\n5. Memory Statistics:")
        print(f"   Total keys: {stats['total_keys']}")
        print(f"   Storage size: {stats['size_mb']} MB")
        print(f"   Partitions: {stats['partitions']}")

        # Cleanup
        await db_manager.close()
        print("\n✅ PostgreSQL example complete")

    except ImportError as e:
        print(f"\n⚠️  PostgreSQL example skipped: {e}")
        print("   Install with: pip install lionagi-qe-fleet")

    except Exception as e:
        print(f"\n❌ PostgreSQL example failed: {e}")
        print("   Ensure PostgreSQL is running and credentials are correct")


async def example_2_redis_memory():
    """Example 2: RedisMemory (High-Speed Cache)"""
    print("\n" + "=" * 70)
    print("Example 2: RedisMemory - High-Speed In-Memory Cache")
    print("=" * 70)

    try:
        from lionagi_qe.persistence import RedisMemory

        # Setup: Initialize Redis connection
        print("\n1. Connecting to Redis...")
        memory = RedisMemory(
            host="localhost",
            port=6379,
            db=0,
            max_connections=10
        )
        print("   ✅ Connected to Redis")

        # Create agent with RedisMemory
        print("\n2. Creating agent with RedisMemory...")
        model = iModel(provider="openai", model="gpt-4o-mini")
        agent = ExampleTestGenerator(
            agent_id="test-generator-redis",
            model=model,
            memory=memory
        )
        print(f"   ✅ Agent created with backend: {agent.memory_backend_type}")

        # Use the agent
        print("\n3. Using agent with Redis memory...")

        # Store some data with TTL
        await agent.store_memory(
            "aqe/coverage/module_a",
            {
                "module": "user_service",
                "line_coverage": 85.5,
                "branch_coverage": 78.2,
                "uncovered_lines": [42, 43, 89]
            },
            ttl=300  # 5 minutes
        )
        print("   ✅ Stored coverage data in Redis (TTL: 5 min)")

        # Retrieve data
        coverage = await agent.get_memory("aqe/coverage/module_a")
        print(f"   ✅ Retrieved coverage: {coverage}")

        # Search patterns
        all_coverage = await agent.search_memory("aqe/coverage/*")
        print(f"   ✅ Found {len(all_coverage)} coverage reports")

        # Get stats
        stats = await memory.get_stats()
        print(f"\n4. Memory Statistics:")
        print(f"   Total keys: {stats['total_keys']}")
        print(f"   Memory used: {stats['memory_used']}")
        print(f"   Connected clients: {stats['connected_clients']}")

        # Cleanup
        memory.close()
        print("\n✅ Redis example complete")

    except ImportError as e:
        print(f"\n⚠️  Redis example skipped: {e}")
        print("   Install with: pip install lionagi-qe-fleet[persistence]")

    except Exception as e:
        print(f"\n❌ Redis example failed: {e}")
        print("   Ensure Redis is running: docker run -d -p 6379:6379 redis:7-alpine")


async def example_3_session_context():
    """Example 3: Session.context (Default In-Memory)"""
    print("\n" + "=" * 70)
    print("Example 3: Session.context - Default In-Memory Storage")
    print("=" * 70)

    # Setup: No setup needed! Session.context is automatic
    print("\n1. Creating agent with default memory (Session.context)...")
    model = iModel(provider="openai", model="gpt-4o-mini")

    agent = ExampleTestGenerator(
        agent_id="test-generator-session",
        model=model
        # No memory parameter - defaults to Session.context
    )
    print(f"   ✅ Agent created with backend: {agent.memory_backend_type}")
    print("   ℹ️  No setup required - Session.context is automatic!")

    # Use the agent
    print("\n2. Using agent with in-memory storage...")

    # Store some data
    await agent.store_memory(
        "aqe/quality/metrics",
        {
            "total_tests": 120,
            "passing": 118,
            "failing": 2,
            "coverage": 92.5,
            "quality_score": 95.2
        }
    )
    print("   ✅ Stored quality metrics in memory")

    # Retrieve data
    metrics = await agent.get_memory("aqe/quality/metrics")
    print(f"   ✅ Retrieved metrics: {metrics}")

    print("\n3. Memory characteristics:")
    print("   - ✅ Zero setup required")
    print("   - ✅ Fast in-memory access")
    print("   - ⚠️  No persistence (lost on restart)")
    print("   - ⚠️  Single-process only")

    print("\n✅ Session.context example complete")


async def example_4_auto_init_from_config():
    """Example 4: Auto-initialization from config"""
    print("\n" + "=" * 70)
    print("Example 4: Auto-initialization from memory_config")
    print("=" * 70)

    # Option 1: Session.context via config
    print("\n1. Auto-init with Session.context...")
    model = iModel(provider="openai", model="gpt-4o-mini")

    agent1 = ExampleTestGenerator(
        agent_id="test-gen-config-session",
        model=model,
        memory_config={"type": "session"}
    )
    print(f"   ✅ Created agent with backend: {agent1.memory_backend_type}")

    # Option 2: PostgreSQL via config
    print("\n2. Auto-init with PostgreSQL...")
    try:
        from lionagi_qe.learning import DatabaseManager

        db_manager = DatabaseManager(
            database_url="postgresql://qe_agent:password@localhost:5432/lionagi_qe_learning"
        )

        agent2 = ExampleTestGenerator(
            agent_id="test-gen-config-postgres",
            model=model,
            memory_config={"type": "postgres", "db_manager": db_manager}
        )
        print(f"   ✅ Created agent with backend: {agent2.memory_backend_type}")

    except Exception as e:
        print(f"   ⚠️  PostgreSQL auto-init skipped: {e}")

    # Option 3: Redis via config
    print("\n3. Auto-init with Redis...")
    try:
        agent3 = ExampleTestGenerator(
            agent_id="test-gen-config-redis",
            model=model,
            memory_config={
                "type": "redis",
                "host": "localhost",
                "port": 6379,
                "db": 0
            }
        )
        print(f"   ✅ Created agent with backend: {agent3.memory_backend_type}")

        # Cleanup
        if hasattr(agent3.memory, 'close'):
            agent3.memory.close()

    except Exception as e:
        print(f"   ⚠️  Redis auto-init skipped: {e}")

    print("\n✅ Auto-initialization example complete")


async def example_5_migration_from_qememory():
    """Example 5: Migrating from QEMemory (deprecated)"""
    print("\n" + "=" * 70)
    print("Example 5: Migrating from QEMemory (Deprecated)")
    print("=" * 70)

    import warnings
    from lionagi_qe.core.memory import QEMemory

    # Old way (deprecated)
    print("\n1. Old approach (QEMemory - deprecated)...")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        old_memory = QEMemory()
        model = iModel(provider="openai", model="gpt-4o-mini")

        old_agent = ExampleTestGenerator(
            agent_id="test-gen-old",
            model=model,
            memory=old_memory
        )

        if w:
            print(f"   ⚠️  Deprecation warning: {w[0].message}")
        print(f"   Backend: {old_agent.memory_backend_type}")

    # New way (recommended)
    print("\n2. New approach (PostgresMemory - recommended)...")
    print("   # Option 1: PostgreSQL (production)")
    print("   from lionagi_qe.persistence import PostgresMemory")
    print("   memory = PostgresMemory(db_manager)")
    print("   agent = ExampleTestGenerator(..., memory=memory)")
    print("")
    print("   # Option 2: Redis (high-speed)")
    print("   from lionagi_qe.persistence import RedisMemory")
    print("   memory = RedisMemory(host='localhost')")
    print("   agent = ExampleTestGenerator(..., memory=memory)")
    print("")
    print("   # Option 3: Default (development)")
    print("   agent = ExampleTestGenerator(...)  # Uses Session.context")

    print("\n✅ Migration example complete")


async def main():
    """Run all examples"""
    print("=" * 70)
    print("Memory Backends Comparison Examples")
    print("=" * 70)
    print("\nThis example demonstrates 3 memory backends for BaseQEAgent:")
    print("1. PostgresMemory (production-ready)")
    print("2. RedisMemory (high-speed cache)")
    print("3. Session.context (default, development)")

    examples = [
        example_3_session_context,      # Run first (no deps)
        example_4_auto_init_from_config,  # Config examples
        example_5_migration_from_qememory,  # Migration guide
        example_1_postgres_memory,      # PostgreSQL (may fail if not running)
        example_2_redis_memory,         # Redis (may fail if not running)
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\n❌ Example failed: {example.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Use PostgresMemory for production (persistence + ACID)")
    print("  2. Use RedisMemory for high-speed operations (sub-ms latency)")
    print("  3. Use Session.context for development (zero setup)")
    print("  4. All backends share the same interface")
    print("  5. QEMemory is deprecated - migrate to persistent backends")


if __name__ == "__main__":
    asyncio.run(main())
