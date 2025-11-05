"""
PostgreSQL-based Persistent Memory

Provides general-purpose memory storage that reuses the existing Q-learning
database infrastructure. This module extends the lionagi_qe_learning database
with a qe_memory table for storing arbitrary key-value pairs.

Key Features:
- Reuses existing DatabaseManager connection pool (no additional connections!)
- Shares infrastructure with Q-learning system
- TTL support for automatic expiration
- Namespace enforcement (all keys must start with 'aqe/')
- Partition-based organization
- Efficient prefix-based searches

Architecture:
- Database: lionagi_qe_learning (same as Q-learning)
- Table: qe_memory (added via memory_extension.sql)
- Connection Pool: Shared with Q-learning (efficient resource usage)
- Performance: O(1) for get/set, O(log n) for prefix searches
"""

import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from lionagi_qe.learning.db_manager import DatabaseManager


class PostgresMemory:
    """
    PostgreSQL-backed persistent memory storage.

    Reuses the existing DatabaseManager and connection pool from Q-learning.
    All operations use the same PostgreSQL database: lionagi_qe_learning.

    Benefits:
    - No additional database setup needed
    - Shares connection pool (efficient resource usage)
    - Same infrastructure for Q-learning and general memory
    - Production-ready (already tested with Q-learning)
    - ACID guarantees from PostgreSQL

    Example:
        ```python
        from lionagi_qe.learning import DatabaseManager
        from lionagi_qe.persistence import PostgresMemory

        # Reuse existing Q-learning database connection
        db_manager = DatabaseManager(
            database_url="postgresql://qe_agent:password@localhost:5432/lionagi_qe_learning",
            min_connections=2,
            max_connections=10
        )
        await db_manager.connect()

        # Create memory backend (reuses same connection pool!)
        memory = PostgresMemory(db_manager)

        # Store data with TTL
        await memory.store("aqe/test-plan/results", test_results, ttl=3600)

        # Retrieve data
        results = await memory.retrieve("aqe/test-plan/results")

        # Search by pattern
        all_plans = await memory.search("aqe/test-plan/*")

        # Get statistics
        stats = await memory.get_stats()
        ```
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize with existing DatabaseManager.

        Args:
            db_manager: Existing DatabaseManager instance (from Q-learning)

        Note:
            The DatabaseManager must already be connected via db_manager.connect()
            before using PostgresMemory.
        """
        self.db = db_manager
        self.logger = logging.getLogger("lionagi_qe.persistence.postgres")

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
            key: Storage key (must start with 'aqe/')
            value: Value to store (will be JSON serialized)
            ttl: Time-to-live in seconds (None = never expire)
            partition: Logical partition for organization

        Raises:
            ValueError: If key doesn't start with 'aqe/' namespace

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
        if not key.startswith("aqe/"):
            raise ValueError(
                f"Key must start with 'aqe/' namespace. Got: {key}"
            )

        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO qe_memory (key, value, partition, expires_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    partition = EXCLUDED.partition,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
                """,
                key,
                json.dumps(value),
                partition,
                expires_at
            )

        self.logger.debug(
            f"Stored key '{key}' in partition '{partition}' "
            f"(ttl={ttl}s, expires_at={expires_at})"
        )

    async def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve value from PostgreSQL.

        Args:
            key: Storage key

        Returns:
            Stored value or None if not found/expired

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
        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT value FROM qe_memory
                WHERE key = $1
                AND (expires_at IS NULL OR expires_at > NOW())
                """,
                key
            )

            if row:
                value = json.loads(row["value"])
                self.logger.debug(f"Retrieved key '{key}'")
                return value

            self.logger.debug(f"Key '{key}' not found or expired")
            return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """
        Search keys by SQL pattern.

        Args:
            pattern: Pattern to match (e.g., 'aqe/coverage/*', 'aqe/test-plan/?')
                    * matches any characters
                    ? matches single character

        Returns:
            Dict of matching keys and values

        Example:
            ```python
            # Find all test plans
            plans = await memory.search("aqe/test-plan/*")
            # Returns: {"aqe/test-plan/v1": {...}, "aqe/test-plan/v2": {...}}

            # Find specific versions
            v1_items = await memory.search("aqe/*/v1")
            ```
        """
        # Convert glob pattern to SQL LIKE pattern
        sql_pattern = pattern.replace("*", "%").replace("?", "_")

        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT key, value FROM qe_memory
                WHERE key LIKE $1
                AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY key
                """,
                sql_pattern
            )

            results = {
                row["key"]: json.loads(row["value"])
                for row in rows
            }

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
        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM qe_memory WHERE key = $1",
                key
            )

            # Extract row count from result status (e.g., "DELETE 1")
            deleted_count = int(result.split()[-1]) if result else 0

            self.logger.debug(f"Deleted key '{key}' (rows affected: {deleted_count})")

    async def clear_partition(self, partition: str):
        """
        Clear all keys in a partition.

        Args:
            partition: Partition name to clear

        Example:
            ```python
            # Clear all test plans
            await memory.clear_partition("test-plan")

            # Clear all coverage data
            await memory.clear_partition("coverage")
            ```
        """
        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM qe_memory WHERE partition = $1",
                partition
            )

            # Extract row count from result status
            deleted_count = int(result.split()[-1]) if result else 0

            self.logger.info(
                f"Cleared partition '{partition}' ({deleted_count} keys deleted)"
            )

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys with optional prefix filter.

        Args:
            prefix: Optional prefix to filter keys (e.g., 'aqe/test-plan/')

        Returns:
            List of matching keys (sorted alphabetically)

        Example:
            ```python
            # List all keys
            all_keys = await memory.list_keys()

            # List keys with prefix
            test_keys = await memory.list_keys("aqe/test-plan/")
            # Returns: ["aqe/test-plan/v1", "aqe/test-plan/v2"]
            ```
        """
        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            if prefix:
                rows = await conn.fetch(
                    """
                    SELECT key FROM qe_memory
                    WHERE key LIKE $1
                    AND (expires_at IS NULL OR expires_at > NOW())
                    ORDER BY key
                    """,
                    f"{prefix}%"
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT key FROM qe_memory
                    WHERE expires_at IS NULL OR expires_at > NOW()
                    ORDER BY key
                    """
                )

            keys = [row["key"] for row in rows]

            self.logger.debug(
                f"List keys with prefix '{prefix}': {len(keys)} found"
            )

            return keys

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics:
            - total_keys: Total number of keys
            - total_expired: Number of expired keys (not cleaned up yet)
            - partitions: Dict of partition names and their key counts
            - size_estimate: Estimated storage size in bytes

        Example:
            ```python
            stats = await memory.get_stats()
            print(f"Total keys: {stats['total_keys']}")
            print(f"Partitions: {stats['partitions']}")
            # Output:
            # Total keys: 42
            # Partitions: {"test-plan": 10, "coverage": 15, "quality": 17}
            ```
        """
        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            # Get total keys (excluding expired)
            total = await conn.fetchval(
                """
                SELECT COUNT(*) FROM qe_memory
                WHERE expires_at IS NULL OR expires_at > NOW()
                """
            )

            # Get expired keys count
            expired = await conn.fetchval(
                """
                SELECT COUNT(*) FROM qe_memory
                WHERE expires_at IS NOT NULL AND expires_at <= NOW()
                """
            )

            # Get partition breakdown
            partition_rows = await conn.fetch(
                """
                SELECT partition, COUNT(*) as count
                FROM qe_memory
                WHERE expires_at IS NULL OR expires_at > NOW()
                GROUP BY partition
                ORDER BY count DESC
                """
            )

            # Get size estimate (JSONB size in bytes)
            size = await conn.fetchval(
                """
                SELECT COALESCE(SUM(pg_column_size(value)), 0)
                FROM qe_memory
                WHERE expires_at IS NULL OR expires_at > NOW()
                """
            )

            return {
                "total_keys": total,
                "total_expired": expired,
                "partitions": {
                    row["partition"]: row["count"]
                    for row in partition_rows
                },
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2) if size else 0.0
            }

    async def cleanup_expired(self) -> int:
        """
        Manually trigger cleanup of expired entries.

        Returns:
            Number of deleted entries

        Note:
            This is automatically called periodically if pg_cron is configured.
            Manual calls are useful for immediate cleanup or testing.

        Example:
            ```python
            deleted = await memory.cleanup_expired()
            print(f"Cleaned up {deleted} expired entries")
            ```
        """
        if self.db.pool is None:
            await self.db.connect()

        async with self.db.pool.acquire() as conn:
            deleted_count = await conn.fetchval(
                "SELECT * FROM cleanup_expired_memory()"
            )

            self.logger.info(f"Cleaned up {deleted_count} expired entries")

            return deleted_count
