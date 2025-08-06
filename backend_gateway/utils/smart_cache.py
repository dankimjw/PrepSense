"""
Smart Caching Utilities for PrepSense
Implements TTL-based caching with pantry state awareness
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SmartCache:
    """TTL-based cache with content-aware keys"""

    def __init__(self, default_ttl: int = 3600):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0

    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is expired"""
        return time.time() - timestamp > ttl

    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.default_ttl
        ]

        for key in expired_keys:
            del self.cache[key]

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.miss_count += 1
            return None

        value, timestamp = self.cache[key]
        cache_ttl = ttl or self.default_ttl

        if self._is_expired(timestamp, cache_ttl):
            del self.cache[key]
            self.miss_count += 1
            return None

        self.hit_count += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        # Periodic cleanup
        if len(self.cache) > 1000:  # Arbitrary limit
            self._cleanup_expired()

        self.cache[key] = (value, time.time())

    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


# Global cache instance
_global_cache = SmartCache()


def get_cache() -> SmartCache:
    """Get global cache instance"""
    return _global_cache


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    # Convert arguments to a stable string representation
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}

    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_with_pantry_state(ttl: int = 3600, include_pantry: bool = True):
    """
    Decorator for caching function results with pantry state awareness

    Args:
        ttl: Time to live in seconds
        include_pantry: Whether to include pantry state in cache key
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_parts = [func.__name__]

            # Add function arguments
            cache_key_parts.extend([str(arg) for arg in args])
            cache_key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            # Add pantry state if requested
            if include_pantry and "user_id" in kwargs:
                pantry_hash = await _get_pantry_hash(kwargs["user_id"])
                cache_key_parts.append(f"pantry={pantry_hash}")

            cache_key = "_".join(cache_key_parts)

            # Try to get from cache
            cache = get_cache()
            cached_result = cache.get(cache_key, ttl)

            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result

            # Execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_parts = [func.__name__]
            cache_key_parts.extend([str(arg) for arg in args])
            cache_key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            cache_key = "_".join(cache_key_parts)

            # Try to get from cache
            cache = get_cache()
            cached_result = cache.get(cache_key, ttl)

            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result

            # Execute function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _get_pantry_hash(user_id: int) -> str:
    """Get hash of user's pantry state for cache key"""
    try:
        from backend_gateway.config.database import get_database_service

        db_service = get_database_service()

        # Get pantry items with quantities and expiry dates
        query = """
            SELECT product_name, quantity, expiration_date, updated_at
            FROM pantry_items 
            WHERE user_id = %s AND quantity > 0
            ORDER BY product_name
        """

        items = db_service.execute_query(query, (user_id,))

        # Create hash of pantry state
        pantry_data = []
        for item in items:
            pantry_data.append(
                {
                    "name": item["product_name"],
                    "quantity": item["quantity"],
                    "expiry": str(item.get("expiration_date", "")),
                    "updated": str(item.get("updated_at", "")),
                }
            )

        pantry_string = json.dumps(pantry_data, sort_keys=True)
        return hashlib.md5(pantry_string.encode()).hexdigest()[:8]

    except Exception as e:
        logger.warning(f"Error getting pantry hash for user {user_id}: {str(e)}")
        return "unknown"


def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a specific user"""
    cache = get_cache()

    # Find all keys that contain this user_id
    keys_to_delete = []
    for key in cache.cache.keys():
        if f"user_id={user_id}" in key or f"args=({user_id}" in key:
            keys_to_delete.append(key)

    # Delete the keys
    for key in keys_to_delete:
        cache.delete(key)

    logger.info(f"Invalidated {len(keys_to_delete)} cache entries for user {user_id}")


def invalidate_pattern_cache(pattern: str):
    """Invalidate all cache entries matching a pattern"""
    cache = get_cache()

    keys_to_delete = []
    for key in cache.cache.keys():
        if pattern in key:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        cache.delete(key)

    logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")


class CacheStats:
    """Cache statistics and monitoring"""

    @staticmethod
    def get_global_stats() -> Dict[str, Any]:
        """Get global cache statistics"""
        cache = get_cache()
        stats = cache.get_stats()

        return {"cache_stats": stats, "timestamp": datetime.now().isoformat()}

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get approximate memory usage of cache"""
        import sys

        cache = get_cache()

        total_size = 0
        for key, (value, timestamp) in cache.cache.items():
            total_size += sys.getsizeof(key)
            total_size += sys.getsizeof(value)
            total_size += sys.getsizeof(timestamp)

        return {
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "entries": len(cache.cache),
            "timestamp": datetime.now().isoformat(),
        }


# Example usage decorators
def cache_recipe_search(ttl: int = 1800):  # 30 minutes
    """Cache recipe search results"""
    return cache_with_pantry_state(ttl=ttl, include_pantry=True)


def cache_user_preferences(ttl: int = 3600):  # 1 hour
    """Cache user preferences"""
    return cache_with_pantry_state(ttl=ttl, include_pantry=False)


def cache_recipe_scoring(ttl: int = 1800):  # 30 minutes
    """Cache recipe scoring results"""
    return cache_with_pantry_state(ttl=ttl, include_pantry=True)
