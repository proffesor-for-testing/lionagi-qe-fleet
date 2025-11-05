"""Storage Modes Example - Environment-based Backend Selection

This example demonstrates automatic storage backend selection based on
environment mode:

1. Development Mode (DEV):
   - Backend: Session.context (in-memory)
   - Setup: Zero configuration required
   - Persistence: None (lost on restart)
   - Use case: Local development, experimentation

2. Testing Mode (TEST):
   - Backend: Session.context (isolated in-memory)
   - Setup: Zero configuration required
   - Persistence: None (clean slate per test)
   - Use case: Unit tests, CI/CD pipelines

3. Production Mode (PROD):
   - Backend: PostgresMemory (persistent)
   - Setup: PostgreSQL database required
   - Persistence: Full ACID guarantees
   - Use case: Production deployments, multi-agent coordination

Usage:
    # Development mode (default)
    python examples/storage_modes_example.py

    # Testing mode
    export AQE_STORAGE_MODE=testing
    python examples/storage_modes_example.py

    # Production mode
    export AQE_STORAGE_MODE=production
    export DATABASE_URL=postgresql://user:pass@localhost:5432/db
    python examples/storage_modes_example.py

Docker Production Setup:
    # Start PostgreSQL
    cd docker
    docker-compose up -d postgres

    # Run in production mode
    export AQE_STORAGE_MODE=production
    export DATABASE_URL=postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning
    python examples/storage_modes_example.py
"""

import asyncio
import os
from lionagi import iModel
from lionagi_qe.core.orchestrator import QEOrchestrator
from lionagi_qe.config import StorageConfig, StorageMode


async def example_1_development_mode():
    """Example 1: Development Mode (Default)

    Uses Session.context with zero setup required.
    Perfect for local development and quick experimentation.
    """
    print("\n" + "=" * 70)
    print("Example 1: Development Mode (Session.context)")
    print("=" * 70)

    # Option 1: Auto-detect (defaults to DEV if no environment variables)
    print("\n1. Creating orchestrator with auto-detection...")
    orchestrator = QEOrchestrator()

    print(f"   Mode: {orchestrator.storage_config.mode.value}")
    print(f"   Description:\n{orchestrator.storage_config.get_description()}")

    # Option 2: Explicit development mode
    print("\n2. Creating orchestrator with explicit DEV mode...")
    orchestrator = QEOrchestrator(mode="development")

    # Option 3: Using StorageConfig
    print("\n3. Creating orchestrator from StorageConfig...")
    config = StorageConfig.for_development()
    orchestrator = QEOrchestrator.from_config(config)

    # Use the orchestrator
    print("\n4. Testing memory operations...")

    # Store data in memory
    await orchestrator.memory.store(
        "aqe/test-plan/example",
        {
            "module": "user_service",
            "tests_needed": ["auth", "profile", "settings"],
            "priority": "high"
        },
        ttl=3600
    )
    print("   ✅ Stored test plan in memory")

    # Retrieve data
    test_plan = await orchestrator.memory.retrieve("aqe/test-plan/example")
    print(f"   ✅ Retrieved test plan: {test_plan}")

    # Get stats
    stats = await orchestrator.memory.get_stats()
    print(f"\n5. Memory statistics:")
    print(f"   Total keys: {stats.get('total_keys', 0)}")
    print(f"   Partitions: {stats.get('partitions', {})}")

    print("\n✅ Development mode example complete")
    print("\nKey takeaways:")
    print("  - Zero setup required")
    print("  - Fast in-memory operations")
    print("  - No persistence (data lost on restart)")
    print("  - Perfect for development and prototyping")


async def example_2_testing_mode():
    """Example 2: Testing Mode

    Uses Session.context with isolated in-memory storage.
    Perfect for unit tests and CI/CD pipelines.
    """
    print("\n" + "=" * 70)
    print("Example 2: Testing Mode (Isolated In-Memory)")
    print("=" * 70)

    # Create orchestrator in testing mode
    print("\n1. Creating orchestrator for testing...")
    orchestrator = QEOrchestrator(mode="test")

    print(f"   Mode: {orchestrator.storage_config.mode.value}")
    print(f"   Description:\n{orchestrator.storage_config.get_description()}")

    # Simulate test scenario
    print("\n2. Simulating test scenario...")

    # Each test gets clean slate
    await orchestrator.memory.store(
        "aqe/coverage/test_run_1",
        {
            "module": "auth_service",
            "line_coverage": 85.5,
            "branch_coverage": 78.2
        }
    )
    print("   ✅ Stored test run 1 coverage")

    # Verify isolation
    coverage = await orchestrator.memory.retrieve("aqe/coverage/test_run_1")
    print(f"   ✅ Retrieved coverage: {coverage}")

    print("\n3. Testing mode characteristics:")
    print("   - ✅ Zero setup required")
    print("   - ✅ Isolated per test (no cross-test contamination)")
    print("   - ✅ Fast execution")
    print("   - ⚠️  No persistence (clean slate per test run)")

    print("\n✅ Testing mode example complete")


async def example_3_production_mode():
    """Example 3: Production Mode

    Uses PostgresMemory with full ACID guarantees and persistence.
    Requires PostgreSQL database setup.
    """
    print("\n" + "=" * 70)
    print("Example 3: Production Mode (PostgresMemory)")
    print("=" * 70)

    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("\n⚠️  Production mode requires DATABASE_URL environment variable")
        print("\nTo run this example:")
        print("  1. Start PostgreSQL:")
        print("     cd docker && docker-compose up -d postgres")
        print("")
        print("  2. Set environment variables:")
        print("     export DATABASE_URL=postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning")
        print("")
        print("  3. Run again:")
        print("     python examples/storage_modes_example.py")
        print("\n⏭️  Skipping production mode example")
        return

    try:
        # Option 1: Auto-detect from environment
        print("\n1. Creating orchestrator from environment...")
        print(f"   DATABASE_URL: {database_url[:50]}...")

        orchestrator = QEOrchestrator(
            mode="production",
            database_url=database_url
        )

        print(f"   Mode: {orchestrator.storage_config.mode.value}")
        print(f"   Description:\n{orchestrator.storage_config.get_description()}")

        # Connect to database
        print("\n2. Connecting to PostgreSQL database...")
        await orchestrator.connect()
        print("   ✅ Database connection established")

        # Use the orchestrator
        print("\n3. Testing persistent memory operations...")

        # Store data (persists across restarts)
        await orchestrator.memory.store(
            "aqe/quality/production_metrics",
            {
                "total_tests": 1250,
                "passing": 1245,
                "failing": 5,
                "coverage": 94.5,
                "quality_score": 98.2,
                "last_updated": "2025-11-05T12:00:00Z"
            },
            ttl=86400,  # 24 hours
            partition="production_metrics"
        )
        print("   ✅ Stored production metrics (persisted to PostgreSQL)")

        # Retrieve data
        metrics = await orchestrator.memory.retrieve("aqe/quality/production_metrics")
        print(f"   ✅ Retrieved metrics: {metrics}")

        # Search patterns
        all_quality = await orchestrator.memory.search("aqe/quality/.*")
        print(f"   ✅ Found {len(all_quality)} quality metrics")

        # Get stats
        stats = await orchestrator.memory.get_stats()
        print(f"\n4. PostgreSQL memory statistics:")
        print(f"   Total keys: {stats.get('total_keys', 0)}")
        print(f"   Storage size: {stats.get('size_mb', 0):.2f} MB")
        print(f"   Partitions: {stats.get('partitions', {})}")

        # Cleanup
        await orchestrator.disconnect()
        print("\n5. Database connection closed")

        print("\n✅ Production mode example complete")
        print("\nKey takeaways:")
        print("  - Full ACID guarantees")
        print("  - Data persists across restarts")
        print("  - Supports multi-agent coordination")
        print("  - Requires PostgreSQL setup")
        print("  - Best for production deployments")

    except Exception as e:
        print(f"\n❌ Production mode example failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running:")
        print("     docker-compose ps")
        print("")
        print("  2. Check database connection:")
        print("     psql postgresql://qe_agent:qe_secure_password_123@localhost:5432/lionagi_qe_learning")
        print("")
        print("  3. Verify DATABASE_URL format:")
        print("     postgresql://user:password@host:port/database")


async def example_4_environment_auto_detection():
    """Example 4: Automatic Environment Detection

    Demonstrates how the system automatically detects the environment
    and selects the appropriate storage backend.
    """
    print("\n" + "=" * 70)
    print("Example 4: Automatic Environment Detection")
    print("=" * 70)

    # Show current environment
    print("\n1. Current environment variables:")
    print(f"   AQE_STORAGE_MODE: {os.getenv('AQE_STORAGE_MODE', 'not set')}")
    print(f"   ENVIRONMENT: {os.getenv('ENVIRONMENT', 'not set')}")
    print(f"   NODE_ENV: {os.getenv('NODE_ENV', 'not set')}")
    print(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'not set')[:50] + '...' if os.getenv('DATABASE_URL') else 'not set'}")

    # Auto-detect configuration
    print("\n2. Auto-detecting storage configuration...")
    config = StorageConfig.from_environment()

    print(f"\n3. Detected configuration:")
    print(f"   Mode: {config.mode.value}")
    print(f"   Description:\n{config.get_description()}")

    # Create orchestrator
    print("\n4. Creating orchestrator from detected config...")
    orchestrator = QEOrchestrator.from_environment()

    print(f"   ✅ Orchestrator created with mode: {orchestrator.storage_config.mode.value}")

    print("\n5. Environment detection priority:")
    print("   1. AQE_STORAGE_MODE (explicit override)")
    print("   2. ENVIRONMENT (common in Docker/cloud)")
    print("   3. NODE_ENV (Node.js convention)")
    print("   4. Default to 'development' if none set")

    print("\n✅ Auto-detection example complete")


async def example_5_migration_guide():
    """Example 5: Migrating from QEMemory to Environment-based Storage

    Shows how to migrate existing code to use the new storage configuration.
    """
    print("\n" + "=" * 70)
    print("Example 5: Migration Guide")
    print("=" * 70)

    print("\n1. Old approach (manual memory management):")
    print("   ```python")
    print("   from lionagi_qe.core.memory import QEMemory")
    print("   from lionagi_qe.core.router import ModelRouter")
    print("   ")
    print("   memory = QEMemory()")
    print("   router = ModelRouter()")
    print("   orchestrator = QEOrchestrator(memory=memory, router=router)")
    print("   ```")

    print("\n2. New approach (environment-based):")
    print("   ```python")
    print("   # Development (default)")
    print("   orchestrator = QEOrchestrator()")
    print("   ")
    print("   # Testing")
    print("   orchestrator = QEOrchestrator(mode='test')")
    print("   ")
    print("   # Production")
    print("   orchestrator = QEOrchestrator(")
    print("       mode='prod',")
    print("       database_url=os.getenv('DATABASE_URL')")
    print("   )")
    print("   await orchestrator.connect()")
    print("   ```")

    print("\n3. Best practices:")
    print("   ✅ Use environment variables for configuration")
    print("   ✅ Auto-detect mode in production (QEOrchestrator.from_environment())")
    print("   ✅ Explicit mode in tests (QEOrchestrator(mode='test'))")
    print("   ✅ Remember to call connect() for production mode")
    print("   ✅ Use disconnect() in finally blocks for cleanup")

    print("\n4. Backward compatibility:")
    print("   The old approach still works - no breaking changes!")
    print("   But the new approach is recommended for better environment handling.")

    print("\n✅ Migration guide complete")


async def main():
    """Run all storage mode examples"""
    print("=" * 70)
    print("Storage Modes Example - Environment-based Backend Selection")
    print("=" * 70)
    print("\nThis example demonstrates automatic storage backend selection")
    print("based on environment mode (DEV, TEST, PROD)")

    examples = [
        ("Development Mode", example_1_development_mode),
        ("Testing Mode", example_2_testing_mode),
        ("Environment Auto-detection", example_4_environment_auto_detection),
        ("Migration Guide", example_5_migration_guide),
        ("Production Mode", example_3_production_mode),  # Run last (may fail if no DB)
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70)

    print("\n🎯 Quick Reference:")
    print("\n1. Development (default):")
    print("   orchestrator = QEOrchestrator()")

    print("\n2. Testing:")
    print("   orchestrator = QEOrchestrator(mode='test')")

    print("\n3. Production:")
    print("   export DATABASE_URL=postgresql://user:pass@localhost:5432/db")
    print("   orchestrator = QEOrchestrator(mode='prod', database_url=os.getenv('DATABASE_URL'))")
    print("   await orchestrator.connect()")

    print("\n4. Auto-detect from environment:")
    print("   export ENVIRONMENT=production")
    print("   export DATABASE_URL=postgresql://...")
    print("   orchestrator = QEOrchestrator.from_environment()")
    print("   await orchestrator.connect()")

    print("\n📚 Documentation:")
    print("   - Storage Config: src/lionagi_qe/config/storage_config.py")
    print("   - Orchestrator: src/lionagi_qe/core/orchestrator.py")
    print("   - Docker Setup: docker/docker-compose.yml")
    print("   - Env Variables: .env.example")


if __name__ == "__main__":
    asyncio.run(main())
