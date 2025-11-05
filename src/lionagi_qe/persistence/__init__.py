"""
Persistent Memory Backends for QE Fleet

This module provides persistent storage backends for agent coordination and state
management. Supports both PostgreSQL and Redis backends with a unified interface.

Architecture:
- PostgresMemory: Reuses Q-learning database infrastructure (recommended)
- RedisMemory: High-performance in-memory alternative

Features:
- Unified key-value interface
- TTL-based expiration
- Namespace enforcement (aqe/* prefix)
- Partition-based organization
- Efficient prefix searches
- Production-ready with connection pooling

Example:
    ```python
    from lionagi_qe.persistence import PostgresMemory, RedisMemory
    from lionagi_qe.learning import DatabaseManager

    # Option 1: PostgreSQL (reuses Q-learning infrastructure)
    db_manager = DatabaseManager(
        database_url="postgresql://qe_agent:password@localhost:5432/lionagi_qe_learning"
    )
    await db_manager.connect()
    memory = PostgresMemory(db_manager)

    # Option 2: Redis (high-performance alternative)
    memory = RedisMemory(host="localhost", port=6379, db=0)

    # Same interface for both backends
    await memory.store("aqe/test-plan/v1", test_plan, ttl=3600)
    test_plan = await memory.retrieve("aqe/test-plan/v1")
    all_plans = await memory.search("aqe/test-plan/*")
    stats = await memory.get_stats()
    ```

Backend Comparison:

| Feature              | PostgreSQL        | Redis            |
|---------------------|-------------------|------------------|
| Latency             | ~1-5ms            | <1ms             |
| Durability          | ACID guarantees   | Optional RDB/AOF |
| Setup               | Reuses existing   | Separate server  |
| Dependencies        | asyncpg           | redis>=5.0.0     |
| Query Complexity    | SQL-based         | Pattern-based    |
| Resource Sharing    | Same as Q-learning| Dedicated        |
| Best For            | Production use    | High-frequency   |

Installation:
    ```bash
    # PostgreSQL backend (included in base dependencies)
    pip install lionagi-qe-fleet

    # Redis backend (optional)
    pip install lionagi-qe-fleet[persistence]
    ```

Setup:
    ```bash
    # PostgreSQL: Apply migration to existing database
    sudo docker exec -i lionagi-qe-postgres psql -U qe_agent -d lionagi_qe_learning \\
      < database/schema/memory_extension.sql

    # Redis: Start Redis server
    docker run -d -p 6379:6379 redis:7-alpine
    ```
"""

from lionagi_qe.persistence.postgres_memory import PostgresMemory
from lionagi_qe.persistence.redis_memory import RedisMemory

__all__ = [
    "PostgresMemory",
    "RedisMemory",
]

__version__ = "1.0.0"
__author__ = "LionAGI QE Fleet Contributors"

# Module metadata
SUPPORTED_BACKENDS = ["postgres", "redis"]
DEFAULT_BACKEND = "postgres"
NAMESPACE_PREFIX = "aqe/"
