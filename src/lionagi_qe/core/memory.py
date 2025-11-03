"""Shared memory namespace for agent coordination"""

from typing import Dict, Any, Optional, List
import asyncio
import re
from datetime import datetime


class QEMemory:
    """Shared memory namespace for QE agent coordination

    Implements the aqe/* namespace pattern from original fleet:
    - aqe/test-plan/*
    - aqe/coverage/*
    - aqe/quality/*
    - aqe/performance/*
    - aqe/security/*
    - aqe/patterns/*
    - aqe/swarm/coordination
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._access_log: List[Dict[str, Any]] = []

    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        partition: str = "default"
    ):
        """Store value in memory namespace

        Args:
            key: Memory key (e.g., "aqe/test-plan/generated")
            value: Value to store
            ttl: Time-to-live in seconds (None = no expiration)
            partition: Logical partition for organization
        """
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            self._store[key] = {
                "value": value,
                "timestamp": datetime.now().timestamp(),
                "ttl": ttl,
                "partition": partition,
            }

            # Log access
            self._access_log.append({
                "operation": "store",
                "key": key,
                "timestamp": datetime.now().isoformat(),
                "partition": partition,
            })

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from memory

        Args:
            key: Memory key to retrieve

        Returns:
            Stored value or None if not found/expired
        """
        if key in self._store:
            data = self._store[key]
            if self._is_expired(data):
                await self.delete(key)
                return None

            # Log access
            self._access_log.append({
                "operation": "retrieve",
                "key": key,
                "timestamp": datetime.now().isoformat(),
            })

            return data["value"]
        return None

    async def search(self, pattern: str) -> Dict[str, Any]:
        """Search memory by regex pattern

        Args:
            pattern: Regex pattern to match keys

        Returns:
            Dict of matching keys and values
        """
        regex = re.compile(pattern)
        results = {}

        for key, data in self._store.items():
            if regex.search(key) and not self._is_expired(data):
                results[key] = data["value"]

        return results

    async def delete(self, key: str):
        """Delete key from memory"""
        if key in self._store:
            del self._store[key]
        if key in self._locks:
            del self._locks[key]

    async def clear_partition(self, partition: str):
        """Clear all keys in a partition"""
        keys_to_delete = [
            k for k, v in self._store.items()
            if v.get("partition") == partition
        ]
        for key in keys_to_delete:
            await self.delete(key)

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys, optionally filtered by prefix"""
        if prefix:
            return [k for k in self._store.keys() if k.startswith(prefix)]
        return list(self._store.keys())

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        total_keys = len(self._store)
        partitions = {}

        for data in self._store.values():
            partition = data.get("partition", "default")
            partitions[partition] = partitions.get(partition, 0) + 1

        return {
            "total_keys": total_keys,
            "partitions": partitions,
            "total_accesses": len(self._access_log),
        }

    def _is_expired(self, data: Dict) -> bool:
        """Check if data has expired"""
        if data.get("ttl") is None:
            return False

        elapsed = datetime.now().timestamp() - data["timestamp"]
        return elapsed > data["ttl"]

    async def export_state(self) -> Dict[str, Any]:
        """Export complete memory state for persistence"""
        return {
            "store": {
                k: v for k, v in self._store.items()
                if not self._is_expired(v)
            },
            "stats": await self.get_stats(),
        }

    async def import_state(self, state: Dict[str, Any]):
        """Import memory state from export"""
        self._store = state.get("store", {})
