# PrepSense Comprehensive Caching Guide

## Overview

The PrepSense system uses multi-layered caching to achieve sub-3-second response times. This guide covers:
- **CrewAI Redis Caching**: For AI agent artifacts and computations
- **FastAPI Response Caching**: For HTTP endpoint optimization
- **Python Function Caching**: For computational performance
- **Database Query Caching**: For data access optimization

This document covers implementation strategies, common pitfalls, and debugging approaches.

## Architecture

### Core Components

1. **ArtifactCacheManager** (`cache_manager.py`)
   - Manages Redis connections
   - Handles serialization/deserialization
   - Implements TTL management
   - Provides cache statistics

2. **Cache Keys** (`models.py`)
   - Namespaced keys: `pantry:{user_id}`, `preferences:{user_id}`, `recipes:{user_id}:{context}`
   - Validation and parsing utilities
   - Context support for recipe caching

3. **Artifact Types**
   - **PantryArtifact**: 1-hour TTL, stores normalized items and expiry analysis
   - **PreferenceArtifact**: 24-hour TTL, stores preference vectors and dietary info
   - **RecipeArtifact**: 2-hour TTL, stores ranked recipes with embeddings

## Common Pitfalls & How to Avoid Them

### 1. Silent Cache Failures

**Problem**: Redis connection failures are caught but not raised, causing cache operations to silently fail.

```python
# This returns False/None on Redis failure without alerting
if not self.redis_client:
    return False
```

**Impact**: 
- Cache misses appear as normal behavior
- Performance degrades without obvious cause
- No alerts when Redis is down

**Solution**:
- Monitor `health_check()` status
- Log cache operation failures at WARNING level
- Implement metrics for cache hit/miss rates
- Add alerts for Redis connection failures

### 2. Dual TTL Enforcement

**Problem**: TTL is enforced both by Redis (`setex`) and artifact timestamp (`is_fresh()`).

```python
# Redis TTL
self.redis_client.setex(key, artifact.ttl_seconds, json_data)

# Application-level TTL check
def is_fresh(self) -> bool:
    return (datetime.now() - self.last_updated).total_seconds() < self.ttl_seconds
```

**Impact**:
- Confusing behavior if clocks are out of sync
- Stale data deleted on read, causing unexpected cache misses
- TTL mismatch between Redis and artifact can cause issues

**Solution**:
- Use Redis TTL as primary mechanism
- Keep artifact TTL as backup validation
- Ensure server clocks are synchronized
- Log when artifacts are deleted due to staleness

### 3. Context-Based Recipe Caching

**Problem**: Recipe cache keys can include optional context, making invalidation complex.

```python
# Keys can be:
# "recipes:123" or "recipes:123:breakfast" or "recipes:123:quick_meal"
```

**Impact**:
- Partial invalidation may miss context-specific entries
- Cache explosion with many contexts
- Difficult to track all cache entries for a user

**Solution**:
- Use wildcard patterns for invalidation: `recipes:{user_id}:*`
- Limit context values to predefined set
- Document all possible context values
- Consider TTL-based expiry instead of manual invalidation

### 4. Serialization Edge Cases

**Problem**: JSON serialization can fail with certain data types.

```python
# Datetime serialization
"last_updated": self.last_updated.isoformat()

# Complex objects in dictionaries
"learning_data": self.learning_data  # May contain non-serializable objects
```

**Impact**:
- Cache save failures with unclear error messages
- Data corruption if partial serialization succeeds
- Type errors on deserialization

**Solution**:
- Validate data before caching
- Use custom JSON encoders for complex types
- Add comprehensive error handling
- Test with edge cases (None, NaN, Infinity)

### 5. Cache Stampede

**Problem**: Multiple requests for expired data trigger simultaneous cache regeneration.

**Impact**:
- Database/API overload
- Increased latency spikes
- Wasted computation

**Solution**:
- Implement cache warming in background
- Use probabilistic early expiration
- Add request coalescing
- Consider "stale-while-revalidate" pattern

## Debugging Strategies

### 1. Enable Verbose Logging

```python
# Set logging level
logging.getLogger('prepsense_crew.cache_manager').setLevel(logging.DEBUG)
```

### 2. Monitor Cache Statistics

```python
stats = cache_manager.get_cache_stats()
print(f"Hit Rate: {stats['hit_rate']}%")
print(f"Hits: {stats['keyspace_hits']}")
print(f"Misses: {stats['keyspace_misses']}")
```

### 3. Redis CLI Debugging

```bash
# Check if keys exist
redis-cli KEYS "pantry:*"
redis-cli KEYS "preferences:*"
redis-cli KEYS "recipes:*"

# Check TTL
redis-cli TTL "pantry:123"

# Inspect content
redis-cli GET "pantry:123"
```

### 4. Common Debug Scenarios

**Cache Always Misses**:
1. Check Redis connection: `cache_manager.health_check()`
2. Verify key format: `CacheKey.is_valid(key)`
3. Check TTL settings
4. Verify serialization works

**Stale Data Returned**:
1. Check `is_fresh()` logic
2. Verify system time synchronization
3. Check TTL values in artifacts
4. Monitor deletion logs

**Performance Issues**:
1. Check cache hit rate
2. Monitor Redis memory usage
3. Verify network latency to Redis
4. Check for cache stampede patterns

### 5. Testing Cache Behavior

```python
# Test cache flow
artifact = PantryArtifact(...)
assert cache_manager.save_pantry_artifact(artifact)
retrieved = cache_manager.get_pantry_artifact(user_id)
assert retrieved is not None
assert retrieved.normalized_items == artifact.normalized_items
```

## Best Practices

1. **Always Check Cache Health**
   ```python
   if not cache_manager.health_check():
       logger.warning("Cache unavailable, falling back to direct computation")
   ```

2. **Use Appropriate TTLs**
   - Pantry: 1 hour (ingredients change infrequently)
   - Preferences: 24 hours (learning is gradual)
   - Recipes: 2 hours (balance freshness with computation cost)

3. **Implement Cache Warming**
   ```python
   # Warm cache after user updates
   await orchestrator.warm_cache_for_user(user_id)
   ```

4. **Monitor Cache Metrics**
   - Hit rate should be >80% for warm users
   - Track cache operation latencies
   - Alert on connection failures

5. **Handle Failures Gracefully**
   - Always have fallback logic
   - Don't let cache failures break functionality
   - Log failures for debugging

## Troubleshooting Checklist

- [ ] Redis service running and accessible?
- [ ] Correct Redis connection parameters?
- [ ] Keys following naming convention?
- [ ] TTL values reasonable?
- [ ] Serialization working for all data types?
- [ ] Clock synchronization between servers?
- [ ] Adequate Redis memory?
- [ ] Network latency acceptable?
- [ ] Error handling in place?
- [ ] Monitoring and alerting configured?

## Future Improvements

1. **Circuit Breaker Pattern**: Temporarily disable cache after repeated failures
2. **Cache Preloading**: Warm cache for active users during off-peak hours
3. **Compression**: Reduce memory usage for large artifacts
4. **Multi-tier Caching**: Add local in-memory cache layer
5. **Cache Analytics**: Track usage patterns to optimize TTLs

## FastAPI Caching Strategies

### 1. fastapi-cache Integration

For endpoint-level caching, use the `fastapi-cache2` library:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="prepsense-api-cache")
    yield

app = FastAPI(lifespan=lifespan)

# Cache recipe searches for 5 minutes
@app.get("/api/v1/recipes/search")
@cache(expire=300, key_builder=recipe_search_key_builder)
async def search_recipes(user_id: int, query: str, dietary_restrictions: list = None):
    return await recipe_service.search(user_id, query, dietary_restrictions)

# Custom key builder for user-specific caching
def recipe_search_key_builder(func, namespace: str = "", *, request=None, **kwargs):
    user_id = kwargs.get('user_id', 'anonymous')
    query = kwargs.get('query', '')
    restrictions = sorted(kwargs.get('dietary_restrictions', []))
    return f"{namespace}:recipe_search:{user_id}:{query}:{','.join(restrictions)}"
```

### 2. Dependency-Level Caching with lru_cache

Cache expensive dependency computations:

```python
from functools import lru_cache
from fastapi import Depends

@lru_cache(maxsize=128)
def get_user_preferences_cached(user_id: int) -> UserPreferences:
    """Cache user preferences for 15 minutes in memory"""
    return UserPreferences.load_from_db(user_id)

# Disable caching when preferences might be stale
@app.get("/api/v1/preferences/fresh")
async def get_fresh_preferences(
    user_id: int,
    prefs: UserPreferences = Depends(get_user_preferences_cached, use_cache=False)
):
    return prefs

# Use cached version for performance
@app.get("/api/v1/recommendations")
async def get_recommendations(
    user_id: int,
    prefs: UserPreferences = Depends(get_user_preferences_cached)
):
    return await recipe_service.get_recommendations(user_id, prefs)
```

### 3. HTTP Cache Headers

Implement proper HTTP caching for static-ish content:

```python
from fastapi import Response
from datetime import datetime, timedelta

@app.get("/api/v1/ingredients/{ingredient_id}")
async def get_ingredient(ingredient_id: int, response: Response):
    ingredient = await ingredient_service.get(ingredient_id)
    
    # Cache ingredient data for 1 hour (ingredients rarely change)
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["Expires"] = (
        datetime.utcnow() + timedelta(hours=1)
    ).strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    return ingredient

@app.get("/api/v1/pantry/{user_id}")
async def get_pantry(user_id: int, response: Response):
    pantry = await pantry_service.get_user_pantry(user_id)
    
    # Short cache for frequently changing data
    response.headers["Cache-Control"] = "private, max-age=300"
    response.headers["Last-Modified"] = pantry.last_updated.strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    
    return pantry
```

### 4. Advanced Caching with Custom Coders

For complex data structures, use custom serialization:

```python
import orjson
from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder

class ORJsonCoder(Coder):
    @classmethod
    def encode(cls, value) -> bytes:
        return orjson.dumps(
            value,
            default=jsonable_encoder,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
        )

    @classmethod
    def decode(cls, value: bytes):
        return orjson.loads(value)

# Use for performance-critical endpoints with complex data
@app.get("/api/v1/analytics/complex")
@cache(expire=1800, coder=ORJsonCoder)  # 30 minutes
async def get_complex_analytics(user_id: int):
    return await analytics_service.get_complex_data(user_id)
```

### 5. Conditional Caching

Cache based on specific conditions:

```python
@app.get("/api/v1/recipes/{recipe_id}")
@cache(
    expire=600,
    condition=lambda *args, **kwargs: kwargs.get("use_cache", True)
)
async def get_recipe(recipe_id: int, use_cache: bool = True):
    return await recipe_service.get(recipe_id)

# Skip cache for admin users who need fresh data
@app.get("/api/v1/admin/pantry/{user_id}")
@cache(
    expire=300,
    condition=lambda *args, **kwargs: not kwargs.get("is_admin", False)
)
async def admin_get_pantry(user_id: int, current_user = Depends(get_current_user)):
    is_admin = current_user.role == "admin"
    return await pantry_service.get_user_pantry(user_id)
```

## Python Function Caching Best Practices

### 1. functools.lru_cache for Pure Functions

```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def calculate_nutrition_score(ingredients: tuple, portions: tuple) -> float:
    """Cache nutrition calculations - expensive but deterministic"""
    # Convert to tuple for hashability
    return nutrition_engine.calculate_score(ingredients, portions)

# Usage in service
def get_recipe_nutrition(recipe):
    ingredients = tuple(recipe.ingredients)
    portions = tuple(recipe.portions)
    return calculate_nutrition_score(ingredients, portions)
```

### 2. TTL-based Caching with cachetools

```python
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
import time

# Cache with 10-minute TTL
spoonacular_cache = TTLCache(maxsize=1000, ttl=600)

@cached(cache=spoonacular_cache, key=hashkey)
def get_spoonacular_recipe(recipe_id: int):
    """Cache external API calls to avoid rate limits"""
    return spoonacular_client.get_recipe(recipe_id)

# Thread-safe cache for concurrent access
from threading import RLock
thread_safe_cache = TTLCache(maxsize=500, ttl=300)
cache_lock = RLock()

@cached(cache=thread_safe_cache, lock=cache_lock)
def expensive_ai_computation(prompt: str, context: dict):
    """Cache AI/ML computations that are expensive"""
    return ai_service.generate_response(prompt, context)
```

### 3. Memory-Aware Caching

```python
import sys
from cachetools import LRUCache

class MemoryAwareLRUCache(LRUCache):
    def __init__(self, maxsize, max_memory_mb=50):
        super().__init__(maxsize, getsizeof=sys.getsizeof)
        self.max_memory = max_memory_mb * 1024 * 1024

    def __setitem__(self, key, value):
        new_size = sys.getsizeof(value)
        while self.currsize + new_size > self.max_memory and self:
            self.popitem()
        super().__setitem__(key, value)

# Use for large data structures
image_cache = MemoryAwareLRUCache(maxsize=100, max_memory_mb=100)

@cached(cache=image_cache)
def process_recipe_image(image_url: str):
    """Cache processed images with memory limits"""
    return image_processor.process_url(image_url)
```

## Performance Monitoring and Metrics

### 1. Cache Performance Tracking

```python
from typing import Dict, Any
import time
from dataclasses import dataclass

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_time: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def avg_time(self) -> float:
        total_ops = self.hits + self.misses
        return self.total_time / total_ops if total_ops > 0 else 0.0

class MonitoredCache:
    def __init__(self, backend):
        self.backend = backend
        self.stats = CacheStats()
    
    async def get(self, key: str):
        start_time = time.time()
        try:
            result = await self.backend.get(key)
            if result is not None:
                self.stats.hits += 1
            else:
                self.stats.misses += 1
            return result
        except Exception as e:
            self.stats.errors += 1
            raise
        finally:
            self.stats.total_time += time.time() - start_time

# Metrics endpoint for monitoring
@app.get("/api/v1/admin/cache/stats")
async def get_cache_stats():
    return {
        "hit_rate": cache.stats.hit_rate,
        "total_hits": cache.stats.hits,
        "total_misses": cache.stats.misses,
        "errors": cache.stats.errors,
        "avg_response_time": cache.stats.avg_time,
        "redis_info": await get_redis_info()
    }
```

### 2. Cache Warming Strategies

```python
from fastapi import BackgroundTasks

class CacheWarmer:
    def __init__(self, cache_manager, recipe_service):
        self.cache = cache_manager
        self.recipe_service = recipe_service
    
    async def warm_user_cache(self, user_id: int):
        """Pre-populate cache for active user"""
        try:
            # Warm pantry cache
            pantry = await pantry_service.get_user_pantry(user_id)
            await self.cache.set(f"pantry:{user_id}", pantry, ttl=3600)
            
            # Warm preferences cache
            prefs = await preference_service.get_preferences(user_id)
            await self.cache.set(f"preferences:{user_id}", prefs, ttl=86400)
            
            # Pre-generate popular recipe searches
            popular_queries = ["breakfast", "quick", "healthy", "vegetarian"]
            for query in popular_queries:
                recipes = await self.recipe_service.search(user_id, query)
                cache_key = f"recipes:{user_id}:{query}"
                await self.cache.set(cache_key, recipes, ttl=1800)
                
        except Exception as e:
            logger.error(f"Cache warming failed for user {user_id}: {e}")

@app.post("/api/v1/users/{user_id}/cache/warm")
async def warm_user_cache(user_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(cache_warmer.warm_user_cache, user_id)
    return {"message": "Cache warming started"}
```

## Cache Invalidation Strategies

### 1. Tag-Based Invalidation

```python
from collections import defaultdict
from typing import Set

class TaggedCacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.tag_mappings = defaultdict(set)  # tag -> set of keys
    
    async def set_with_tags(self, key: str, value, tags: Set[str], ttl: int = 3600):
        """Store value with associated tags for bulk invalidation"""
        await self.redis.setex(key, ttl, value)
        
        # Store tag mappings
        for tag in tags:
            await self.redis.sadd(f"tag:{tag}", key)
            await self.redis.expire(f"tag:{tag}", ttl + 300)  # Tags expire later
    
    async def invalidate_by_tag(self, tag: str):
        """Invalidate all keys associated with a tag"""
        keys = await self.redis.smembers(f"tag:{tag}")
        if keys:
            await self.redis.delete(*keys)
            await self.redis.delete(f"tag:{tag}")

# Usage for user-specific invalidation
await cache.set_with_tags(
    f"recipes:{user_id}:breakfast",
    recipes,
    tags={f"user:{user_id}", "recipes", "breakfast"},
    ttl=1800
)

# Invalidate all user data when preferences change
await cache.invalidate_by_tag(f"user:{user_id}")
```

### 2. Event-Driven Cache Invalidation

```python
from fastapi import APIRouter
from typing import List

# Cache invalidation router
cache_router = APIRouter(prefix="/api/v1/cache")

@cache_router.post("/invalidate/user/{user_id}")
async def invalidate_user_cache(user_id: int, cache_types: List[str] = None):
    """Invalidate specific cache types for a user"""
    cache_types = cache_types or ["pantry", "preferences", "recipes"]
    
    for cache_type in cache_types:
        pattern = f"{cache_type}:{user_id}*"
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    
    return {"invalidated_types": cache_types, "user_id": user_id}

@cache_router.post("/invalidate/recipes")
async def invalidate_all_recipe_caches():
    """Global recipe cache invalidation (use sparingly)"""
    keys = await redis_client.keys("recipes:*")
    if keys:
        await redis_client.delete(*keys)
    return {"invalidated_keys": len(keys)}

# Auto-invalidation on data changes
@app.put("/api/v1/pantry/{user_id}/items")
async def update_pantry_items(user_id: int, items: List[PantryItem]):
    # Update data
    await pantry_service.update_items(user_id, items)
    
    # Invalidate related caches
    await cache_manager.invalidate_by_tag(f"user:{user_id}")
    
    return {"updated": len(items)}
```

## Error Handling and Resilience

### 1. Circuit Breaker Pattern

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, bypass cache
    HALF_OPEN = "half_open" # Testing if cache is back

class CacheCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call_with_circuit_breaker(self, cache_operation):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                return None  # Bypass cache
        
        try:
            result = await cache_operation()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            logger.warning(f"Cache operation failed: {e}")
            return None  # Fallback to direct computation

# Usage
circuit_breaker = CacheCircuitBreaker()

async def get_with_fallback(key: str, fallback_func):
    # Try cache with circuit breaker
    cached = await circuit_breaker.call_with_circuit_breaker(
        lambda: cache_manager.get(key)
    )
    
    if cached is not None:
        return cached
    
    # Fallback to direct computation
    result = await fallback_func()
    
    # Try to cache result (might fail, but that's OK)
    try:
        await cache_manager.set(key, result)
    except Exception:
        pass  # Silent failure for cache writes
    
    return result
```

### 2. Graceful Degradation

```python
async def get_recipe_recommendations(user_id: int, fallback_to_popular=True):
    """Get recommendations with multiple fallback levels"""
    
    # Level 1: Try personalized cache
    try:
        cached = await cache_manager.get(f"recommendations:{user_id}")
        if cached:
            return cached
    except Exception as e:
        logger.warning(f"Personal recommendation cache failed: {e}")
    
    # Level 2: Try generating fresh recommendations
    try:
        recommendations = await recommendation_service.generate(user_id)
        
        # Try to cache for next time
        try:
            await cache_manager.set(
                f"recommendations:{user_id}", 
                recommendations, 
                ttl=1800
            )
        except Exception:
            pass  # Cache write failure is non-critical
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        
        if not fallback_to_popular:
            raise
    
    # Level 3: Fallback to popular recipes (cached globally)
    try:
        popular = await cache_manager.get("popular_recipes")
        if popular:
            return popular
    except Exception:
        pass
    
    # Level 4: Database fallback for popular recipes
    return await recipe_service.get_popular_recipes(limit=20)
```

## Testing Cache Behavior

### 1. Cache Integration Tests

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_recipe_cache_flow():
    """Test complete cache flow for recipe endpoints"""
    user_id = 123
    query = "breakfast"
    
    # Mock the underlying service
    with patch('recipe_service.search') as mock_search:
        mock_search.return_value = [{"id": 1, "name": "Pancakes"}]
        
        # First call should hit the service and cache result
        response1 = await search_recipes(user_id, query)
        assert mock_search.call_count == 1
        
        # Second call should hit cache
        response2 = await search_recipes(user_id, query)
        assert mock_search.call_count == 1  # No additional calls
        assert response1 == response2

@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test cache invalidation when data changes"""
    user_id = 123
    
    # Cache some data
    await cache_manager.set(f"pantry:{user_id}", {"items": []})
    
    # Verify cached
    cached = await cache_manager.get(f"pantry:{user_id}")
    assert cached is not None
    
    # Trigger invalidation
    await invalidate_user_cache(user_id, ["pantry"])
    
    # Verify cache is cleared
    cached = await cache_manager.get(f"pantry:{user_id}")
    assert cached is None

@pytest.mark.asyncio
async def test_cache_failure_resilience():
    """Test that cache failures don't break functionality"""
    user_id = 123
    
    # Mock cache to always fail
    with patch.object(cache_manager, 'get', side_effect=Exception("Redis down")):
        with patch.object(cache_manager, 'set', side_effect=Exception("Redis down")):
            
            # Should still work via fallback
            result = await get_with_fallback(
                f"test:{user_id}",
                lambda: {"fallback": "data"}
            )
            
            assert result == {"fallback": "data"}
```

### 2. Cache Performance Tests

```python
import time
import asyncio

async def test_cache_performance():
    """Test cache performance under load"""
    user_id = 123
    
    # Warm the cache
    await cache_manager.set(f"test:{user_id}", {"data": "test"})
    
    # Time cache hits
    start_time = time.time()
    tasks = [cache_manager.get(f"test:{user_id}") for _ in range(100)]
    results = await asyncio.gather(*tasks)
    cache_time = time.time() - start_time
    
    # All should be cache hits
    assert all(r is not None for r in results)
    assert cache_time < 0.1  # Should be very fast
    
    print(f"100 cache operations took {cache_time:.4f} seconds")
```

## References

- [FastAPI Cache Documentation](https://github.com/long2ice/fastapi-cache)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
- [Preventing Cache Stampede](https://en.wikipedia.org/wiki/Cache_stampede)
- [HTTP Caching Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)
- [cachetools Documentation](https://cachetools.readthedocs.io/)
