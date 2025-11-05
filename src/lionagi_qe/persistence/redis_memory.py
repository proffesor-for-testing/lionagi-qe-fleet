"""
Redis-based Persistent Memory

Provides an alternative memory backend using Redis. This is a standalone
implementation that does not require PostgreSQL.

Key Features:
- High-performance in-memory storage
- Native TTL support
- Connection pooling
- Atomic operations
- Pattern-based searches
- Cross-agent coordination

Use Cases:
- High-frequency reads/writes
- Low-latency requirements
- Simple key-value storage
- Session-based coordination
- Temporary caching with persistence

Architecture:
- Storage: Redis (in-memory with optional persistence)
- Connection Pool: redis-py ConnectionPool
- Performance: O(1) for get/set, O(N) for pattern searches
- TTL: Native Redis expiration
"""

import json
import logging
from typing import Any, Dict, Optional, List

try:
    import redis
except ImportError:
    redis = None


class RedisMemory:
    """
    Redis-backed persistent memory storage.

    Provides high-performance key-value storage with native TTL support.
    Alternative to PostgresMemory for scenarios requiring low latency.

    Benefits:
    - Sub-millisecond read/write latency
    - Native TTL support (automatic expiration)
    - Horizontal scalability
    - Pub/Sub for real-time coordination
    - Simple setup

    Requirements:
    - redis>=5.0.0 package
    - Redis server (local or remote)

    Example:
        ```python
        from lionagi_qe.persistence import RedisMemory

        # Create memory backend
        memory = RedisMemory(
            host="localhost",
            port=6379,
            db=0,
            max_connections=10
        )

        # Store data with TTL
        await memory.store("aqe/test-plan/results", test_results, ttl=3600)

        # Retrieve data
        results = await memory.retrieve("aqe/test-plan/results")

        # Search by pattern
        all_plans = await memory.search("aqe/test-plan/*")

        # Get statistics
        stats = await memory.get_stats()

        # Cleanup
        memory.close()
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10
    ):
        """
        Initialize Redis connection with connection pooling.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number (0-15)
            password: Redis password (optional)
            max_connections: Connection pool size

        Raises:
            ImportError: If redis package is not installed
        """
        if redis is None:
            raise ImportError(
                "redis package is required for RedisMemory. "
                "Install with: pip install redis>=5.0.0"
            )

        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=True  # Automatically decode bytes to strings
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self.logger = logging.getLogger("lionagi_qe.persistence.redis")

        # Test connection
        try:
            self.client.ping()
            self.logger.info(f"Connected to Redis at {host}:{port} (db={db})")
        except redis.ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 3600,
        partition: str = "default"
    ):
        """
        Store value with optional TTL.

        Args:
            key: Storage key (e.g., 'aqe/test-plan/generated')
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds (None = never expire)
            partition: Logical partition for organization

        Example:
            ```python
            # Store with 1-hour TTL
            await memory.store("aqe/test-plan/v1", test_plan, ttl=3600)

            # Store permanently
            await memory.store("aqe/config/settings", config, ttl=None)

            # Store in specific partition
            await memory.store("aqe/coverage/gaps", gaps, partition="coverage")
            ```
        """
        # Wrap value with metadata
        data = {
            "value": value,
            "partition": partition,
            "created_at": self.client.time()[0]  # Redis server timestamp
        }

        serialized = json.dumps(data)

        # Store with TTL
        if ttl:
            self.client.setex(key, ttl, serialized)
            self.logger.debug(f"Stored key '{key}' with TTL {ttl}s")
        else:
            self.client.set(key, serialized)
            self.logger.debug(f"Stored key '{key}' (no expiration)")

    async def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve value from Redis.

        Args:
            key: Storage key

        Returns:
            Stored value or None if not found

        Example:
            ```python
            # Retrieve value
            test_plan = await memory.retrieve("aqe/test-plan/v1")

            if test_plan is None:
                print("Not found or expired")
            else:
                print(f"Found: {test_plan}")
            ```
        """
        data = self.client.get(key)

        if data:
            parsed = json.loads(data)
            self.logger.debug(f"Retrieved key '{key}'")
            return parsed["value"]

        self.logger.debug(f"Key '{key}' not found")
        return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """
        Search keys by Redis pattern.

        Args:
            pattern: Redis pattern (e.g., 'aqe/coverage/*', 'aqe/test-plan/?')
                    * matches any characters
                    ? matches single character
                    [ae] matches a or e

        Returns:
            Dict of matching keys and values

        Warning:
            This operation is O(N) where N is the total number of keys.
            Use sparingly on large datasets.

        Example:
            ```python
            # Find all test plans
            plans = await memory.search("aqe/test-plan/*")
            # Returns: {"aqe/test-plan/v1": {...}, "aqe/test-plan/v2": {...}}

            # Find specific versions
            v1_items = await memory.search("aqe/*/v1")
            ```
        """
        keys = self.client.keys(pattern)
        results = {}

        for key in keys:
            value = await self.retrieve(key)
            if value is not None:
                results[key] = value

        self.logger.debug(
            f"Search pattern '{pattern}' returned {len(results)} results"
        )

        return results

    async def delete(self, key: str):
        """
        Delete key from storage.

        Args:
            key: Storage key to delete

        Example:
            ```python
            await memory.delete("aqe/test-plan/v1")
            ```
        """
        deleted = self.client.delete(key)

        self.logger.debug(f"Deleted key '{key}' (existed: {deleted > 0})")

    async def clear_partition(self, partition: str):
        """
        Clear all keys in a partition.

        Args:
            partition: Partition name to clear

        Warning:
            This is an O(N) operation that scans all keys.

        Example:
            ```python
            # Clear all test plans
            await memory.clear_partition("test-plan")

            # Clear all coverage data
            await memory.clear_partition("coverage")
            ```
        """
        # Get all keys and filter by partition
        all_keys = self.client.keys("*")
        to_delete = []

        for key in all_keys:
            data = self.client.get(key)
            if data:
                try:
                    parsed = json.loads(data)
                    if parsed.get("partition") == partition:
                        to_delete.append(key)
                except (json.JSONDecodeError, KeyError):
                    # Skip malformed data
                    continue

        # Delete in batch
        if to_delete:
            deleted = self.client.delete(*to_delete)
            self.logger.info(
                f"Cleared partition '{partition}' ({deleted} keys deleted)"
            )
        else:
            self.logger.info(f"Partition '{partition}' is already empty")

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys with optional prefix filter.

        Args:
            prefix: Optional prefix to filter keys (e.g., 'aqe/test-plan/')

        Returns:
            List of matching keys (sorted alphabetically)

        Warning:
            This is an O(N) operation. Use prefix to reduce scan scope.

        Example:
            ```python
            # List all keys
            all_keys = await memory.list_keys()

            # List keys with prefix
            test_keys = await memory.list_keys("aqe/test-plan/")
            # Returns: ["aqe/test-plan/v1", "aqe/test-plan/v2"]
            ```
        """
        if prefix:
            keys = self.client.keys(f"{prefix}*")
        else:
            keys = self.client.keys("*")

        # Sort for consistent ordering
        sorted_keys = sorted(keys)

        self.logger.debug(
            f"List keys with prefix '{prefix}': {len(sorted_keys)} found"
        )

        return sorted_keys

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics:
            - total_keys: Total number of keys in database
            - memory_used: Human-readable memory usage
            - memory_peak: Peak memory usage
            - connected_clients: Number of connected clients
            - keyspace_info: Detailed keyspace statistics

        Example:
            ```python
            stats = await memory.get_stats()
            print(f"Total keys: {stats['total_keys']}")
            print(f"Memory used: {stats['memory_used']}")
            # Output:
            # Total keys: 42
            # Memory used: 1.2M
            ```
        """
        info = self.client.info()
        keyspace = info.get("keyspace", {})
        memory = info.get("memory", {})

        # Extract database stats (e.g., db0: keys=100, expires=20)
        db_stats = {}
        for key, value in keyspace.items():
            if key.startswith("db"):
                db_stats[key] = value

        return {
            "total_keys": self.client.dbsize(),
            "memory_used": memory.get("used_memory_human", "unknown"),
            "memory_peak": memory.get("used_memory_peak_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "keyspace_info": db_stats
        }

    async def cleanup_expired(self) -> int:
        """
        Manually trigger cleanup of expired entries.

        Returns:
            Number of deleted entries

        Note:
            Redis automatically removes expired keys. This method is provided
            for interface compatibility with PostgresMemory but is a no-op.

        Example:
            ```python
            # No-op in Redis (automatic expiration)
            deleted = await memory.cleanup_expired()
            print(f"Redis automatically handles expiration: {deleted} keys")
            ```
        """
        self.logger.debug(
            "Redis automatically handles expiration. No manual cleanup needed."
        )
        return 0

    def close(self):
        """
        Close Redis connection pool.

        Example:
            ```python
            memory = RedisMemory()
            # ... use memory ...
            memory.close()
            ```
        """
        self.pool.disconnect()
        self.logger.info("Redis connection pool closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
