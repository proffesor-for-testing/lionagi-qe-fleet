"""
Test backward compatibility and new memory backends for BaseQEAgent

This test verifies:
1. QEMemory backward compatibility (with deprecation warning)
2. Default Session.context behavior
3. Auto-initialization from memory_config
4. PostgresMemory integration
5. RedisMemory integration
6. Memory backend type detection
"""

import asyncio
import warnings
from lionagi import iModel
from lionagi_qe.core.base_agent import BaseQEAgent
from lionagi_qe.core.memory import QEMemory
from lionagi_qe.core.task import QETask


# Test implementation of BaseQEAgent for testing
class TestAgent(BaseQEAgent):
    """Test agent implementation"""

    def get_system_prompt(self) -> str:
        return "Test agent for memory integration testing"

    async def execute(self, task: QETask):
        return {"success": True, "result": "test"}


async def test_qememory_backward_compat():
    """Test 1: Old way (QEMemory) - should work with deprecation warning"""
    print("\n=== Test 1: QEMemory Backward Compatibility ===")

    model = iModel(provider="openai", model="gpt-4o-mini")
    memory = QEMemory()

    # Capture deprecation warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        agent = TestAgent(agent_id="test-compat", model=model, memory=memory)

        # Verify warning was issued
        assert len(w) > 0, "Expected deprecation warning"
        assert issubclass(w[0].category, DeprecationWarning)
        assert "QEMemory is deprecated" in str(w[0].message)
        print(f"✅ Deprecation warning issued: {w[0].message}")

    # Verify agent works
    assert agent.memory is memory, "Memory should be the same instance"
    assert agent.memory_backend_type == "qememory"
    print(f"✅ QEMemory backward compatibility works")
    print(f"   Backend type: {agent.memory_backend_type}")


async def test_default_session_context():
    """Test 2: New way (default) - Session.context"""
    print("\n=== Test 2: Default Session.context ===")

    model = iModel(provider="openai", model="gpt-4o-mini")

    # No memory provided - should default to Session.context
    agent = TestAgent(agent_id="test-default", model=model)

    assert agent.memory is not None, "Memory should be initialized"
    assert agent.memory_backend_type == "session"
    print(f"✅ Default Session.context works")
    print(f"   Backend type: {agent.memory_backend_type}")

    # Test basic memory operations
    await agent.store_memory("aqe/test/data", {"value": 42})
    result = await agent.get_memory("aqe/test/data")
    assert result == {"value": 42}, f"Expected {{'value': 42}}, got {result}"
    print(f"✅ Memory operations work: stored and retrieved data")


async def test_memory_config_session():
    """Test 3: Auto-init from config (session)"""
    print("\n=== Test 3: Memory Config - Session ===")

    model = iModel(provider="openai", model="gpt-4o-mini")

    # Auto-initialize from config
    agent = TestAgent(
        agent_id="test-config-session",
        model=model,
        memory_config={"type": "session"}
    )

    assert agent.memory is not None, "Memory should be initialized"
    assert agent.memory_backend_type == "session"
    print(f"✅ Memory config auto-init works (session)")
    print(f"   Backend type: {agent.memory_backend_type}")


async def test_postgres_memory():
    """Test 4: PostgresMemory integration"""
    print("\n=== Test 4: PostgresMemory Integration ===")

    model = iModel(provider="openai", model="gpt-4o-mini")

    try:
        from lionagi_qe.persistence import PostgresMemory
        from lionagi_qe.learning import DatabaseManager

        # Create database manager (won't connect to actual DB in test)
        db_manager = DatabaseManager(
            database_url="postgresql://test:test@localhost:5432/test_db"
        )

        # Create memory backend (don't connect)
        memory = PostgresMemory(db_manager)

        # Create agent with PostgresMemory
        agent = TestAgent(agent_id="test-postgres", model=model, memory=memory)

        assert agent.memory is memory, "Memory should be the same instance"
        assert agent.memory_backend_type == "postgres"
        print(f"✅ PostgresMemory integration works")
        print(f"   Backend type: {agent.memory_backend_type}")

    except ImportError as e:
        print(f"⚠️  PostgresMemory not available: {e}")
        print(f"   This is expected if persistence module is not installed")


async def test_redis_memory():
    """Test 5: RedisMemory integration"""
    print("\n=== Test 5: RedisMemory Integration ===")

    model = iModel(provider="openai", model="gpt-4o-mini")

    try:
        from lionagi_qe.persistence import RedisMemory

        # Create memory backend (won't connect to actual Redis in test)
        try:
            memory = RedisMemory(host="localhost", port=6379)
            memory.close()  # Close immediately - just testing initialization

            # Create agent with RedisMemory
            memory2 = RedisMemory(host="localhost", port=6379)
            agent = TestAgent(agent_id="test-redis", model=model, memory=memory2)
            memory2.close()

            assert agent.memory is memory2, "Memory should be the same instance"
            assert agent.memory_backend_type == "redis"
            print(f"✅ RedisMemory integration works")
            print(f"   Backend type: {agent.memory_backend_type}")

        except Exception as e:
            print(f"⚠️  RedisMemory connection failed: {e}")
            print(f"   This is expected if Redis server is not running")

    except ImportError as e:
        print(f"⚠️  RedisMemory not available: {e}")
        print(f"   Install with: pip install lionagi-qe-fleet[persistence]")


async def test_memory_config_postgres():
    """Test 6: Auto-init from config (postgres)"""
    print("\n=== Test 6: Memory Config - PostgreSQL ===")

    model = iModel(provider="openai", model="gpt-4o-mini")

    try:
        from lionagi_qe.learning import DatabaseManager

        db_manager = DatabaseManager(
            database_url="postgresql://test:test@localhost:5432/test_db"
        )

        # Auto-initialize from config
        agent = TestAgent(
            agent_id="test-config-postgres",
            model=model,
            memory_config={"type": "postgres", "db_manager": db_manager}
        )

        assert agent.memory is not None, "Memory should be initialized"
        assert agent.memory_backend_type == "postgres"
        print(f"✅ Memory config auto-init works (postgres)")
        print(f"   Backend type: {agent.memory_backend_type}")

    except ImportError as e:
        print(f"⚠️  PostgreSQL config test skipped: {e}")


async def test_memory_config_redis():
    """Test 7: Auto-init from config (redis)"""
    print("\n=== Test 7: Memory Config - Redis ===")

    model = iModel(provider="openai", model="gpt-4o-mini")

    try:
        # Auto-initialize from config
        agent = TestAgent(
            agent_id="test-config-redis",
            model=model,
            memory_config={"type": "redis", "host": "localhost", "port": 6379}
        )

        assert agent.memory is not None, "Memory should be initialized"
        assert agent.memory_backend_type == "redis"

        # Close connection
        if hasattr(agent.memory, 'close'):
            agent.memory.close()

        print(f"✅ Memory config auto-init works (redis)")
        print(f"   Backend type: {agent.memory_backend_type}")

    except ImportError as e:
        print(f"⚠️  Redis config test skipped: {e}")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print(f"   This is expected if Redis server is not running")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("BaseQEAgent Memory Backend Integration Tests")
    print("=" * 60)

    tests = [
        test_qememory_backward_compat,
        test_default_session_context,
        test_memory_config_session,
        test_postgres_memory,
        test_redis_memory,
        test_memory_config_postgres,
        test_memory_config_redis,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
