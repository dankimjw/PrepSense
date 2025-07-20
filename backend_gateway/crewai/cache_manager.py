"""
<<<<<<< HEAD
Redis-based cache manager for CrewAI artifacts
Handles caching and retrieval of pantry analysis, preferences, and recipe data
"""
import redis
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
=======
CrewAI Artifact Cache Manager

Redis-based caching for pantry artifacts, preference artifacts, and recipe artifacts.
Provides automatic TTL management and serialization.
Handles caching and retrieval of pantry analysis, preferences, and recipe data
"""

from typing import Optional, List, Dict, Any
import redis
import json
import logging
from datetime import datetime
import os
>>>>>>> 36bb269d0cdb24db95429518c20bc1653cd1b434

from .models import PantryArtifact, PreferenceArtifact, RecipeArtifact, CacheKey

logger = logging.getLogger(__name__)

<<<<<<< HEAD

class ArtifactCacheManager:
    """Redis-based cache manager for CrewAI artifacts"""
    
=======
class ArtifactCacheManager:
    """Redis-based cache manager for CrewAI artifacts"""
    
<<<<<<< HEAD
    def __init__(self, redis_host: str = None, redis_port: int = None, redis_db: int = None):
        """Initialize cache manager with Redis connection"""
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = redis_db or int(os.getenv("REDIS_DB", "0"))
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True
        )
=======
>>>>>>> 36bb269d0cdb24db95429518c20bc1653cd1b434
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """Initialize cache manager with Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            raise
<<<<<<< HEAD
=======
>>>>>>> 5b3757d41db2e2108a7bf1bcbae76c4a41c99cd2
>>>>>>> 36bb269d0cdb24db95429518c20bc1653cd1b434
    
    def save_pantry_artifact(self, artifact: PantryArtifact) -> bool:
        """Save pantry artifact to cache"""
        try:
            key = CacheKey.pantry(artifact.user_id)
            json_data = artifact.to_json()
<<<<<<< HEAD
=======
<<<<<<< HEAD
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            return bool(result)
        except Exception as e:
            print(f"Error saving pantry artifact: {e}")
            return False
    
    def get_pantry_artifact(self, user_id: int) -> Optional[PantryArtifact]:
        """Get pantry artifact from cache"""
        try:
            key = CacheKey.pantry(user_id)
            cached_data = self.redis_client.get(key)
            
            if cached_data is None:
                return None
            
            artifact = PantryArtifact.from_json(cached_data)
            
            # Check if artifact is still fresh
            if not artifact.is_fresh():
                self.delete_pantry_artifact(user_id)
                return None
            
            return artifact
        except Exception as e:
            print(f"Error getting pantry artifact: {e}")
            return None
    
    def delete_pantry_artifact(self, user_id: int) -> bool:
        """Delete pantry artifact from cache"""
        try:
            key = CacheKey.pantry(user_id)
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            print(f"Error deleting pantry artifact: {e}")
            return False
    
    def save_preference_artifact(self, artifact: PreferenceArtifact) -> bool:
        """Save preference artifact to cache"""
        try:
            key = CacheKey.preference(artifact.user_id)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            return bool(result)
        except Exception as e:
            print(f"Error saving preference artifact: {e}")
            return False
    
    def get_preference_artifact(self, user_id: int) -> Optional[PreferenceArtifact]:
        """Get preference artifact from cache"""
        try:
            key = CacheKey.preference(user_id)
            cached_data = self.redis_client.get(key)
            
            if cached_data is None:
                return None
            
            artifact = PreferenceArtifact.from_json(cached_data)
            
            # Check if artifact is still fresh
            if not artifact.is_fresh():
                self.delete_preference_artifact(user_id)
                return None
            
            return artifact
        except Exception as e:
            print(f"Error getting preference artifact: {e}")
            return None
    
    def delete_preference_artifact(self, user_id: int) -> bool:
        """Delete preference artifact from cache"""
        try:
            key = CacheKey.preference(user_id)
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            print(f"Error deleting preference artifact: {e}")
            return False
    
    def save_recipe_artifact(self, artifact: RecipeArtifact, search_hash: str) -> bool:
        """Save recipe artifact to cache"""
        try:
            key = CacheKey.recipe(artifact.user_id, search_hash)
            json_data = artifact.to_json()
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            return bool(result)
        except Exception as e:
            print(f"Error saving recipe artifact: {e}")
            return False
    
    def get_recipe_artifact(self, user_id: int, search_hash: str) -> Optional[RecipeArtifact]:
        """Get recipe artifact from cache"""
        try:
            key = CacheKey.recipe(user_id, search_hash)
            cached_data = self.redis_client.get(key)
            
            if cached_data is None:
                return None
            
            artifact = RecipeArtifact.from_json(cached_data)
            
            # Check if artifact is still fresh
            if not artifact.is_fresh():
                self.delete_recipe_artifact(user_id, search_hash)
                return None
            
            return artifact
        except Exception as e:
            print(f"Error getting recipe artifact: {e}")
            return None
    
    def delete_recipe_artifact(self, user_id: int, search_hash: str) -> bool:
        """Delete recipe artifact from cache"""
        try:
            key = CacheKey.recipe(user_id, search_hash)
            result = self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            print(f"Error deleting recipe artifact: {e}")
            return False
    
    def clear_user_cache(self, user_id: int) -> bool:
        """Clear all cached artifacts for a user"""
        try:
            # Get all keys matching user patterns
            pantry_key = CacheKey.pantry(user_id)
            preference_key = CacheKey.preference(user_id)
            recipe_pattern = f"recipe_artifact:{user_id}:*"
            
            # Delete pantry and preference artifacts
            deleted_count = 0
            deleted_count += self.redis_client.delete(pantry_key)
            deleted_count += self.redis_client.delete(preference_key)
            
            # Delete all recipe artifacts for user
            recipe_keys = self.redis_client.keys(recipe_pattern)
            if recipe_keys:
                deleted_count += self.redis_client.delete(*recipe_keys)
            
            return deleted_count > 0
        except Exception as e:
            print(f"Error clearing user cache: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Redis health check failed: {e}")
=======
>>>>>>> 36bb269d0cdb24db95429518c20bc1653cd1b434
            
            # Set with TTL
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            
            if result:
                logger.info(f"Saved pantry artifact for user {artifact.user_id}")
                return True
            else:
                logger.error(f"Failed to save pantry artifact for user {artifact.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving pantry artifact for user {artifact.user_id}: {e}")
            return False
    
    def get_pantry_artifact(self, user_id: int) -> Optional[PantryArtifact]:
        """Retrieve pantry artifact from cache"""
        try:
            key = CacheKey.pantry(user_id)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = PantryArtifact.from_json(json_data)
                
                # Check if artifact is still fresh
                if artifact.is_fresh():
                    logger.info(f"Retrieved fresh pantry artifact for user {user_id}")
                    return artifact
                else:
                    logger.info(f"Pantry artifact for user {user_id} is stale, removing")
                    self.redis_client.delete(key)
                    return None
            else:
                logger.debug(f"No pantry artifact found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving pantry artifact for user {user_id}: {e}")
            return None
    
    def save_preference_artifact(self, artifact: PreferenceArtifact) -> bool:
        """Save preference artifact to cache"""
        try:
            key = CacheKey.preferences(artifact.user_id)
            json_data = artifact.to_json()
            
            # Set with TTL
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            
            if result:
                logger.info(f"Saved preference artifact for user {artifact.user_id}")
                return True
            else:
                logger.error(f"Failed to save preference artifact for user {artifact.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving preference artifact for user {artifact.user_id}: {e}")
            return False
    
    def get_preference_artifact(self, user_id: int) -> Optional[PreferenceArtifact]:
        """Retrieve preference artifact from cache"""
        try:
            key = CacheKey.preferences(user_id)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = PreferenceArtifact.from_json(json_data)
                
                # Check if artifact is still fresh
                if artifact.is_fresh():
                    logger.info(f"Retrieved fresh preference artifact for user {user_id}")
                    return artifact
                else:
                    logger.info(f"Preference artifact for user {user_id} is stale, removing")
                    self.redis_client.delete(key)
                    return None
            else:
                logger.debug(f"No preference artifact found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving preference artifact for user {user_id}: {e}")
            return None
    
    def save_recipe_artifact(self, artifact: RecipeArtifact, context: Optional[str] = None) -> bool:
        """Save recipe artifact to cache"""
        try:
            key = CacheKey.recipes(artifact.user_id, context)
            json_data = artifact.to_json()
            
            # Set with TTL
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            
            if result:
                logger.info(f"Saved recipe artifact for user {artifact.user_id} (context: {context})")
                return True
            else:
                logger.error(f"Failed to save recipe artifact for user {artifact.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving recipe artifact for user {artifact.user_id}: {e}")
            return False
    
    def get_recipe_artifact(self, user_id: int, context: Optional[str] = None) -> Optional[RecipeArtifact]:
        """Retrieve recipe artifact from cache"""
        try:
            key = CacheKey.recipes(user_id, context)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = RecipeArtifact.from_json(json_data)
                
                # Check if artifact is still fresh
                if artifact.is_fresh():
                    logger.info(f"Retrieved fresh recipe artifact for user {user_id} (context: {context})")
                    return artifact
                else:
                    logger.info(f"Recipe artifact for user {user_id} is stale, removing")
                    self.redis_client.delete(key)
                    return None
            else:
                logger.debug(f"No recipe artifact found for user {user_id} (context: {context})")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving recipe artifact for user {user_id}: {e}")
            return None
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cached artifacts for a user"""
        try:
            keys_to_delete = [
                CacheKey.pantry(user_id),
                CacheKey.preferences(user_id),
                CacheKey.recipes(user_id)
            ]
            
            # Find additional recipe keys with context
            pattern = f"recipes:{user_id}:*"
            context_keys = self.redis_client.keys(pattern)
            keys_to_delete.extend(context_keys)
            
            # Delete all keys
            if keys_to_delete:
                deleted_count = self.redis_client.delete(*keys_to_delete)
                logger.info(f"Invalidated {deleted_count} cached artifacts for user {user_id}")
                return deleted_count
            else:
                logger.debug(f"No cached artifacts found for user {user_id}")
                return 0
                
        except Exception as e:
            logger.error(f"Error invalidating cache for user {user_id}: {e}")
            return 0
    
    def is_artifact_fresh(self, artifact: Any) -> bool:
        """Check if an artifact is still fresh (within TTL)"""
        try:
            return artifact.is_fresh()
        except Exception as e:
            logger.error(f"Error checking artifact freshness: {e}")
            return False
    
    def has_fresh_data(self, user_id: int) -> bool:
        """Check if user has fresh cached data for all artifact types"""
        try:
            pantry_artifact = self.get_pantry_artifact(user_id)
            preference_artifact = self.get_preference_artifact(user_id)
            
            # User needs both pantry and preference data to be considered "fresh"
            return pantry_artifact is not None and preference_artifact is not None
            
        except Exception as e:
            logger.error(f"Error checking fresh data for user {user_id}: {e}")
            return False
    
    def warm_cache_for_users(self, user_ids: List[int]) -> Dict[int, bool]:
        """Warm cache for multiple users (trigger background flows)"""
        results = {}
        
        for user_id in user_ids:
            try:
                # This would trigger the background flows for each user
                # For now, we'll just check if they need cache warming
                has_fresh = self.has_fresh_data(user_id)
                results[user_id] = has_fresh
                
                if not has_fresh:
                    logger.info(f"User {user_id} needs cache warming")
                    # TODO: Trigger background flows here
                    # from .flows import PantryAnalysisFlow, PreferenceLearningFlow
                    # pantry_flow = PantryAnalysisFlow()
                    # pantry_flow.kickoff(inputs={"user_id": user_id})
                
            except Exception as e:
                logger.error(f"Error warming cache for user {user_id}: {e}")
                results[user_id] = False
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health info"""
        try:
            info = self.redis_client.info()
            
            stats = {
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
            # Calculate hit rate
            hits = stats["keyspace_hits"]
            misses = stats["keyspace_misses"]
            total_requests = hits + misses
            
            if total_requests > 0:
                stats["hit_rate"] = round((hits / total_requests) * 100, 2)
            else:
                stats["hit_rate"] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            response = self.redis_client.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
<<<<<<< HEAD
=======
>>>>>>> 5b3757d41db2e2108a7bf1bcbae76c4a41c99cd2
>>>>>>> 36bb269d0cdb24db95429518c20bc1653cd1b434
            return False