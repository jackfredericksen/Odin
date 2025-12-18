"""
API Response Caching Utility
Provides in-memory caching with TTL support for API endpoints
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

from odin.utils.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    In-memory cache manager with TTL support and automatic cleanup.
    Thread-safe using asyncio locks.
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Initialize cache manager.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
            max_size: Maximum number of cache entries (default: 1000)
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, expires_at = self.cache[key]

            # Check if expired
            if time.time() > expires_at:
                del self.cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        async with self.lock:
            # Enforce max size with LRU eviction
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Remove oldest entry
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
                self.evictions += 1

            expires_at = time.time() + (ttl or self.default_ttl)
            self.cache[key] = (value, expires_at)

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed, False otherwise
        """
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        async with self.lock:
            count = len(self.cache)
            self.cache.clear()
            return count

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        async with self.lock:
            now = time.time()
            expired_keys = [
                key for key, (_, expires_at) in self.cache.items() if now > expires_at
            ]

            for key in expired_keys:
                del self.cache[key]

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(default_ttl: int = 300, max_size: int = 1000) -> CacheManager:
    """
    Get or create global cache manager instance.

    Args:
        default_ttl: Default TTL in seconds
        max_size: Maximum cache size

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(default_ttl=default_ttl, max_size=max_size)
        logger.info(
            f"Initialized cache manager with TTL={default_ttl}s, max_size={max_size}"
        )
    return _cache_manager


def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    skip_cache_on_error: bool = True,
):
    """
    Decorator to cache async function results.

    Args:
        ttl: Time-to-live in seconds (uses default if None)
        key_prefix: Custom cache key prefix (uses function name if None)
        skip_cache_on_error: Don't cache if function raises exception

    Example:
        @cached(ttl=60, key_prefix="price")
        async def get_price(symbol: str):
            return await fetch_price_from_api(symbol)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            prefix = key_prefix or func.__name__
            cache_key = cache._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(
                    f"Cache hit for {prefix}",
                    extra={"cache_key": cache_key[:8]},
                )
                return cached_value

            # Execute function
            try:
                result = await func(*args, **kwargs)

                # Cache successful result
                await cache.set(cache_key, result, ttl=ttl)
                logger.debug(
                    f"Cached result for {prefix}",
                    extra={"cache_key": cache_key[:8], "ttl": ttl or cache.default_ttl},
                )

                return result

            except Exception as e:
                # Don't cache errors
                logger.error(
                    f"Error in cached function {prefix}: {e}",
                    extra={"cache_key": cache_key[:8]},
                )
                raise

        return wrapper

    return decorator


async def start_cache_cleanup_task(interval: int = 300):
    """
    Background task to periodically clean up expired cache entries.

    Args:
        interval: Cleanup interval in seconds (default: 5 minutes)
    """
    cache = get_cache_manager()
    logger.info(f"Starting cache cleanup task (interval={interval}s)")

    while True:
        try:
            await asyncio.sleep(interval)
            removed = await cache.cleanup_expired()
            if removed > 0:
                logger.info(f"Cache cleanup: removed {removed} expired entries")
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")


# Cache preset configurations for different use cases
CACHE_PRESETS = {
    "realtime": 10,  # 10 seconds - for live price data
    "short": 60,  # 1 minute - for frequently updated data
    "medium": 300,  # 5 minutes - for moderate data
    "long": 3600,  # 1 hour - for rarely changing data
    "static": 86400,  # 24 hours - for static/reference data
}
