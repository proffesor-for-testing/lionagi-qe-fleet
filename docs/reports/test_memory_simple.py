"""
Simple unit test for memory initialization logic

Tests the _initialize_memory method without requiring full package installation.
"""

import sys
import warnings
from typing import Dict, Any, Optional

# Mock classes for testing
class MockQEMemory:
    """Mock QEMemory for testing"""
    pass


class MockPostgresMemory:
    """Mock PostgresMemory for testing"""
    def __init__(self, db_manager):
        self.db_manager = db_manager


class MockRedisMemory:
    """Mock RedisMemory for testing"""
    def __init__(self, host="localhost", port=6379, db=0, password=None):
        self.host = host
        self.port = port


class MockSession:
    """Mock Session for testing"""
    def __init__(self):
        self.context = {"type": "session_context"}


# Simplified agent for testing initialization logic only
class TestBaseQEAgent:
    """Test version of BaseQEAgent with only initialization logic"""

    def __init__(
        self,
        agent_id: str,
        memory: Optional[Any] = None,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.memory = self._initialize_memory(memory, memory_config)

    def _initialize_memory(
        self,
        memory: Optional[Any],
        memory_config: Optional[Dict[str, Any]]
    ) -> Any:
        """Initialize memory backend with backward compatibility"""
        # Case 1: Memory instance provided
        if memory is not None:
            if isinstance(memory, MockQEMemory):
                warnings.warn(
                    f"QEMemory is deprecated and lacks persistence. "
                    f"Consider using PostgresMemory or RedisMemory for production. "
                    f"Agent: {self.agent_id}",
                    DeprecationWarning,
                    stacklevel=3
                )
            return memory

        # Case 2: Auto-initialize from config
        if memory_config:
            backend_type = memory_config.get("type", "session")

            if backend_type == "postgres":
                db_manager = memory_config.get("db_manager")
                if not db_manager:
                    raise ValueError("PostgresMemory requires 'db_manager' in memory_config")
                return MockPostgresMemory(db_manager)

            elif backend_type == "redis":
                return MockRedisMemory(
                    host=memory_config.get("host", "localhost"),
                    port=memory_config.get("port", 6379),
                    db=memory_config.get("db", 0),
                    password=memory_config.get("password")
                )

            elif backend_type == "session":
                if not hasattr(self, '_session'):
                    self._session = MockSession()
                return self._session.context

            else:
                raise ValueError(f"Unknown memory backend type: {backend_type}")

        # Case 3: Default to Session.context
        if not hasattr(self, '_session'):
            self._session = MockSession()
        return self._session.context

    @property
    def memory_backend_type(self) -> str:
        """Get type of memory backend in use"""
        if hasattr(self.memory, '__class__'):
            class_name = self.memory.__class__.__name__
            if class_name == "MockPostgresMemory":
                return "postgres"
            elif class_name == "MockRedisMemory":
                return "redis"
            elif class_name == "MockQEMemory":
                return "qememory"
            elif isinstance(self.memory, dict) and self.memory.get("type") == "session_context":
                return "session"
        return "custom"


def test_qememory_backward_compat():
    """Test 1: QEMemory backward compatibility with deprecation warning"""
    print("\n=== Test 1: QEMemory Backward Compatibility ===")

    memory = MockQEMemory()

    # Capture deprecation warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        agent = TestBaseQEAgent(agent_id="test-compat", memory=memory)

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


def test_default_session_context():
    """Test 2: Default Session.context"""
    print("\n=== Test 2: Default Session.context ===")

    # No memory provided - should default to Session.context
    agent = TestBaseQEAgent(agent_id="test-default")

    assert agent.memory is not None, "Memory should be initialized"
    assert agent.memory_backend_type == "session"
    print(f"✅ Default Session.context works")
    print(f"   Backend type: {agent.memory_backend_type}")


def test_memory_config_session():
    """Test 3: Auto-init from config (session)"""
    print("\n=== Test 3: Memory Config - Session ===")

    # Auto-initialize from config
    agent = TestBaseQEAgent(
        agent_id="test-config-session",
        memory_config={"type": "session"}
    )

    assert agent.memory is not None, "Memory should be initialized"
    assert agent.memory_backend_type == "session"
    print(f"✅ Memory config auto-init works (session)")
    print(f"   Backend type: {agent.memory_backend_type}")


def test_memory_config_postgres():
    """Test 4: Auto-init from config (postgres)"""
    print("\n=== Test 4: Memory Config - PostgreSQL ===")

    class MockDBManager:
        pass

    db_manager = MockDBManager()

    # Auto-initialize from config
    agent = TestBaseQEAgent(
        agent_id="test-config-postgres",
        memory_config={"type": "postgres", "db_manager": db_manager}
    )

    assert agent.memory is not None, "Memory should be initialized"
    assert agent.memory_backend_type == "postgres"
    assert agent.memory.db_manager is db_manager
    print(f"✅ Memory config auto-init works (postgres)")
    print(f"   Backend type: {agent.memory_backend_type}")


def test_memory_config_redis():
    """Test 5: Auto-init from config (redis)"""
    print("\n=== Test 5: Memory Config - Redis ===")

    # Auto-initialize from config
    agent = TestBaseQEAgent(
        agent_id="test-config-redis",
        memory_config={"type": "redis", "host": "localhost", "port": 6379}
    )

    assert agent.memory is not None, "Memory should be initialized"
    assert agent.memory_backend_type == "redis"
    assert agent.memory.host == "localhost"
    assert agent.memory.port == 6379
    print(f"✅ Memory config auto-init works (redis)")
    print(f"   Backend type: {agent.memory_backend_type}")


def test_direct_postgres_memory():
    """Test 6: Direct PostgresMemory instance"""
    print("\n=== Test 6: Direct PostgresMemory Instance ===")

    class MockDBManager:
        pass

    db_manager = MockDBManager()
    memory = MockPostgresMemory(db_manager)

    agent = TestBaseQEAgent(agent_id="test-postgres", memory=memory)

    assert agent.memory is memory, "Memory should be the same instance"
    assert agent.memory_backend_type == "postgres"
    print(f"✅ Direct PostgresMemory works")
    print(f"   Backend type: {agent.memory_backend_type}")


def test_direct_redis_memory():
    """Test 7: Direct RedisMemory instance"""
    print("\n=== Test 7: Direct RedisMemory Instance ===")

    memory = MockRedisMemory(host="localhost", port=6379)

    agent = TestBaseQEAgent(agent_id="test-redis", memory=memory)

    assert agent.memory is memory, "Memory should be the same instance"
    assert agent.memory_backend_type == "redis"
    print(f"✅ Direct RedisMemory works")
    print(f"   Backend type: {agent.memory_backend_type}")


def test_error_handling():
    """Test 8: Error handling for invalid config"""
    print("\n=== Test 8: Error Handling ===")

    # Missing db_manager for postgres
    try:
        agent = TestBaseQEAgent(
            agent_id="test-error",
            memory_config={"type": "postgres"}  # Missing db_manager
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "db_manager" in str(e)
        print(f"✅ Correctly raises error for missing db_manager")

    # Unknown backend type
    try:
        agent = TestBaseQEAgent(
            agent_id="test-error2",
            memory_config={"type": "unknown_backend"}
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown memory backend type" in str(e)
        print(f"✅ Correctly raises error for unknown backend type")


def main():
    """Run all tests"""
    print("=" * 60)
    print("BaseQEAgent Memory Initialization Unit Tests")
    print("=" * 60)

    tests = [
        test_qememory_backward_compat,
        test_default_session_context,
        test_memory_config_session,
        test_memory_config_postgres,
        test_memory_config_redis,
        test_direct_postgres_memory,
        test_direct_redis_memory,
        test_error_handling,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
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
    success = main()
    sys.exit(0 if success else 1)
