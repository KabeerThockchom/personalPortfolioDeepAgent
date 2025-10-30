"""
API Response Caching Utility

Provides in-memory and optional Redis-backed caching for API responses.
Supports TTL-based cache invalidation and graceful fallback.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional, Callable
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base class for cache backends."""

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in cache with TTL in seconds."""
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cached values."""
        raise NotImplementedError


class InMemoryCache(CacheBackend):
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if not expired."""
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value with expiry timestamp."""
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed items."""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now > expiry
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


class RedisCache(CacheBackend):
    """Redis-backed cache for production use."""

    def __init__(self, redis_client):
        """
        Initialize Redis cache.

        Args:
            redis_client: Redis client instance (e.g., from redis-py)
        """
        self.redis = redis_client

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis."""
        try:
            value = self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        """Store value in Redis with TTL."""
        try:
            serialized = json.dumps(value)
            self.redis.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str) -> None:
        """Delete key from Redis."""
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    def clear(self) -> None:
        """Clear all keys (use with caution!)."""
        try:
            self.redis.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")


class APICache:
    """
    API response cache with automatic key generation.

    Usage:
        cache = APICache(ttl=900)  # 15 minutes

        @cache.cached()
        def fetch_data(symbol: str):
            return api_call(symbol)
    """

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        ttl: int = 900,  # 15 minutes default
        key_prefix: str = "api_cache"
    ):
        """
        Initialize API cache.

        Args:
            backend: Cache backend (defaults to InMemoryCache)
            ttl: Time-to-live in seconds
            key_prefix: Prefix for all cache keys
        """
        self.backend = backend or InMemoryCache()
        self.default_ttl = ttl
        self.key_prefix = key_prefix

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key from function name and arguments."""
        # Create deterministic string from args and kwargs
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)

        # Hash the combined string
        combined = f"{func_name}:{args_str}:{kwargs_str}"
        hash_digest = hashlib.md5(combined.encode()).hexdigest()

        return f"{self.key_prefix}:{func_name}:{hash_digest}"

    def cached(self, ttl: Optional[int] = None):
        """
        Decorator to cache function results.

        Args:
            ttl: Optional TTL override (uses default if not specified)

        Example:
            @cache.cached(ttl=300)
            def get_stock_quote(symbol: str):
                return api_call(symbol)
        """
        cache_ttl = ttl or self.default_ttl

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(func.__name__, args, kwargs)

                # Try to get from cache
                cached_value = self.backend.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache HIT: {func.__name__}")
                    return cached_value

                # Cache miss - call function
                logger.debug(f"Cache MISS: {func.__name__}")
                result = func(*args, **kwargs)

                # Store in cache
                self.backend.set(cache_key, result, cache_ttl)

                return result

            return wrapper
        return decorator

    def invalidate(self, func_name: str, *args, **kwargs) -> None:
        """Invalidate specific cache entry."""
        cache_key = self._generate_key(func_name, args, kwargs)
        self.backend.delete(cache_key)

    def clear_all(self) -> None:
        """Clear entire cache."""
        self.backend.clear()


# Global cache instance for easy import
# Default: 15-minute TTL, in-memory storage
_global_cache = APICache(ttl=900)


def get_cache() -> APICache:
    """Get global cache instance."""
    return _global_cache


def configure_cache(
    backend: Optional[CacheBackend] = None,
    ttl: int = 900,
    key_prefix: str = "api_cache"
) -> None:
    """
    Configure global cache instance.

    Example:
        # Use Redis in production
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        configure_cache(
            backend=RedisCache(redis_client),
            ttl=900
        )
    """
    global _global_cache
    _global_cache = APICache(backend=backend, ttl=ttl, key_prefix=key_prefix)
