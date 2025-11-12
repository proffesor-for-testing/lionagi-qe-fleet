"""
Caching layer for badge generation.

Provides 5-minute TTL cache to reduce API calls and improve response times.
"""

import time
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass
from threading import Lock


@dataclass
class CacheEntry:
    """Cache entry with TTL."""

    value: str
    timestamp: float
    ttl: int  # seconds
    project_id: str  # Store for reverse lookup
    badge_type: str  # Store for reverse lookup

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


class BadgeCache:
    """
    Thread-safe badge cache with TTL.

    Attributes:
        default_ttl: Default TTL in seconds (300 = 5 minutes)
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize badge cache.

        Args:
            default_ttl: Default TTL in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()

    def _make_key(self, project_id: str, badge_type: str, **params) -> str:
        """
        Generate cache key from parameters.

        Args:
            project_id: Project identifier
            badge_type: Type of badge (coverage, quality, security, tests)
            **params: Additional parameters (style, color, label)

        Returns:
            Cache key hash
        """
        # Sort params for consistent keys
        param_str = ''.join(f"{k}={v}" for k, v in sorted(params.items()))
        key_str = f"{project_id}:{badge_type}:{param_str}"

        # Use hash for shorter keys
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, project_id: str, badge_type: str, **params) -> Optional[str]:
        """
        Get cached badge SVG.

        Args:
            project_id: Project identifier
            badge_type: Type of badge
            **params: Additional parameters

        Returns:
            Cached SVG string or None if not found/expired
        """
        key = self._make_key(project_id, badge_type, **params)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.value

    def set(
        self,
        project_id: str,
        badge_type: str,
        value: str,
        ttl: Optional[int] = None,
        **params
    ) -> None:
        """
        Cache badge SVG.

        Args:
            project_id: Project identifier
            badge_type: Type of badge
            value: SVG string to cache
            ttl: Custom TTL (uses default if None)
            **params: Additional parameters
        """
        key = self._make_key(project_id, badge_type, **params)
        ttl = ttl if ttl is not None else self.default_ttl

        with self._lock:
            self._cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                project_id=project_id,
                badge_type=badge_type
            )

    def invalidate(self, project_id: str, badge_type: Optional[str] = None) -> int:
        """
        Invalidate cached badges for a project.

        Args:
            project_id: Project identifier
            badge_type: Specific badge type (or None for all)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = []

            for key, entry in self._cache.items():
                if entry.project_id == project_id:
                    if badge_type is None or entry.badge_type == badge_type:
                        keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

            return len(keys_to_delete)

    def clear(self) -> None:
        """Clear all cached badges."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of expired entries removed
        """
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for v in self._cache.values() if v.is_expired())

            return {
                'total_entries': total,
                'active_entries': total - expired,
                'expired_entries': expired,
                'default_ttl': self.default_ttl,
            }


# Global cache instance
_global_cache: Optional[BadgeCache] = None


def get_cache() -> BadgeCache:
    """
    Get global badge cache instance.

    Returns:
        Global BadgeCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = BadgeCache()
    return _global_cache
