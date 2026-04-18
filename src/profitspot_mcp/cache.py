"""
ProfitSpot MCP — In-Memory TTL Cache
Lightweight caching layer for DeFiLlama API responses.
Supports per-key TTL and automatic expiration.
"""
import time
import threading
from typing import Any, Optional


class Cache:
    """Thread-safe in-memory cache with per-key TTL."""

    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self._ttls: dict[str, int] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._store:
                return None
            ttl = self._ttls.get(key, self._default_ttl)
            if time.time() - self._timestamps[key] > ttl:
                del self._store[key]
                del self._timestamps[key]
                del self._ttls[key]
                return None
            return self._store[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional custom TTL."""
        with self._lock:
            self._store[key] = value
            self._timestamps[key] = time.time()
            self._ttls[key] = ttl if ttl is not None else self._default_ttl

    def get_age(self, key: str) -> Optional[float]:
        """Get age of cached entry in seconds, or None if not cached."""
        with self._lock:
            if key in self._timestamps:
                return time.time() - self._timestamps[key]
        return None

    def clear(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._store.clear()
            self._timestamps.clear()
            self._ttls.clear()


# Global cache instance — 5 min default TTL
cache = Cache(default_ttl=300)
