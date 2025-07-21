"""
CrewAI Artifact Cache Manager

Redis-based caching for pantry artifacts, preference artifacts, and recipe artifacts.
Provides automatic TTL management and serialization.
"""

from typing import Optional, List, Dict, Any
import redis
import json
import logging
from datetime import datetime
import os

from .models import PantryArtifact, PreferenceArtifact, RecipeArtifact, CacheKey

logger = logging.getLogger(__name__)


class ArtifactCacheManager:
    """Redis-based cache manager for CrewAI artifacts"""
    
    def __init__(self, redis_host: str = None, redis_port: int = None, redis_db: int = None):
        """Initialize cache manager with Redis connection"""
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db or int(os.getenv("REDIS_DB", "0"))
        
        try:
            # Initialize Redis client
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Don't raise - allow cache manager to work without Redis
            self.redis_client = None
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            self.redis_client = None
    
    def save_pantry_artifact(self, artifact: PantryArtifact) -> bool:
        """Save pantry artifact to cache"""
        if not self.redis_client:
            return False
            
        try:
            key = CacheKey.pantry(artifact.user_id)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            logger.debug(f"Saved pantry artifact for user {artifact.user_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error saving pantry artifact: {e}")
            return False
    
    def get_pantry_artifact(self, user_id: int) -> Optional[PantryArtifact]:
        """Get pantry artifact from cache"""
        if not self.redis_client:
            return None
            
        try:
            key = CacheKey.pantry(user_id)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = PantryArtifact.from_json(json_data)
                if artifact.is_fresh():
                    logger.debug(f"Retrieved fresh pantry artifact for user {user_id}")
                    return artifact
                else:
                    logger.debug(f"Pantry artifact for user {user_id} is stale")
                    self.redis_client.delete(key)
                    
            return None
        except Exception as e:
            logger.error(f"Error getting pantry artifact: {e}")
            return None
    
    def save_preference_artifact(self, artifact: PreferenceArtifact) -> bool:
        """Save preference artifact to cache"""
        if not self.redis_client:
            return False
            
        try:
            key = CacheKey.preferences(artifact.user_id)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            logger.debug(f"Saved preference artifact for user {artifact.user_id}")
            return bool(result)
        except Exception as e:
            logger.error(f"Error saving preference artifact: {e}")
            return False
    
    def get_preference_artifact(self, user_id: int) -> Optional[PreferenceArtifact]:
        """Get preference artifact from cache"""
        if not self.redis_client:
            return None
            
        try:
            key = CacheKey.preferences(user_id)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = PreferenceArtifact.from_json(json_data)
                if artifact.is_fresh():
                    logger.debug(f"Retrieved fresh preference artifact for user {user_id}")
                    return artifact
                else:
                    logger.debug(f"Preference artifact for user {user_id} is stale")
                    self.redis_client.delete(key)
                    
            return None
        except Exception as e:
            logger.error(f"Error getting preference artifact: {e}")
            return None
    
    def save_recipe_artifact(self, artifact: RecipeArtifact, context: Optional[str] = None) -> bool:
        """Save recipe artifact to cache"""
        if not self.redis_client:
            return False
            
        try:
            key = CacheKey.recipes(artifact.user_id, context)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            logger.debug(f"Saved recipe artifact for user {artifact.user_id} with context '{context}'")
            return bool(result)
        except Exception as e:
            logger.error(f"Error saving recipe artifact: {e}")
            return False
    
    def get_recipe_artifact(self, user_id: int, context: Optional[str] = None) -> Optional[RecipeArtifact]:
        """Get recipe artifact from cache"""
        if not self.redis_client:
            return None
            
        try:
            key = CacheKey.recipes(user_id, context)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = RecipeArtifact.from_json(json_data)
                if artifact.is_fresh():
                    logger.debug(f"Retrieved fresh recipe artifact for user {user_id}")
                    return artifact
                else:
                    logger.debug(f"Recipe artifact for user {user_id} is stale")
                    self.redis_client.delete(key)
                    
            return None
        except Exception as e:
            logger.error(f"Error getting recipe artifact: {e}")
            return None
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache entries for a user"""
        if not self.redis_client:
            return 0
            
        try:
            patterns = [
                CacheKey.pantry(user_id),
                CacheKey.preferences(user_id),
                f"recipes:{user_id}:*"
            ]
            
            deleted = 0
            for pattern in patterns:
                if "*" in pattern:
                    # Use scan to find matching keys
                    for key in self.redis_client.scan_iter(match=pattern):
                        deleted += self.redis_client.delete(key)
                else:
                    deleted += self.redis_client.delete(pattern)
            
            logger.info(f"Invalidated {deleted} cache entries for user {user_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")
            return 0
    
    def warm_cache(self, user_id: int, pantry_data: List[Dict[str, Any]] = None,
                   preferences: Dict[str, Any] = None) -> Dict[str, bool]:
        """Pre-warm cache with user data"""
        results = {
            "pantry": False,
            "preferences": False
        }
        
        # Implementation would create artifacts from provided data
        # and save them to cache
        # This is a placeholder for the actual implementation
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {
                "connected": False,
                "error": "Redis not connected"
            }
            
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "connected": True,
                "error": str(e)
            }
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def health_check(self) -> bool:
        """Check if cache manager is healthy"""
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.ping()
        except Exception:
            return False