"""
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
            # Initialize Redis client with timeouts for robustness
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
            raise
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            raise
    
    def save_pantry_artifact(self, artifact: PantryArtifact) -> bool:
        """Save pantry artifact to cache"""
        try:
            key = CacheKey.pantry(artifact.user_id)
            json_data = artifact.to_json()
            
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
            key = CacheKey.preference(artifact.user_id)
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
            key = CacheKey.preference(user_id)
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
    
    def save_recipe_artifact(self, artifact: RecipeArtifact, search_hash: str) -> bool:
        """Save recipe artifact to cache"""
        try:
            key = CacheKey.recipe(artifact.user_id, search_hash)
            json_data = artifact.to_json()
            
            # Set with TTL
            result = self.redis_client.setex(key, artifact.ttl_seconds, json_data)
            
            if result:
                logger.info(f"Saved recipe artifact for user {artifact.user_id} (search_hash: {search_hash})")
                return True
            else:
                logger.error(f"Failed to save recipe artifact for user {artifact.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving recipe artifact for user {artifact.user_id}: {e}")
            return False
    
    def get_recipe_artifact(self, user_id: int, search_hash: str) -> Optional[RecipeArtifact]:
        """Retrieve recipe artifact from cache"""
        try:
            key = CacheKey.recipe(user_id, search_hash)
            json_data = self.redis_client.get(key)
            
            if json_data:
                artifact = RecipeArtifact.from_json(json_data)
                
                # Check if artifact is still fresh
                if artifact.is_fresh():
                    logger.info(f"Retrieved fresh recipe artifact for user {user_id} (search_hash: {search_hash})")
                    return artifact
                else:
                    logger.info(f"Recipe artifact for user {user_id} is stale, removing")
                    self.redis_client.delete(key)
                    return None
            else:
                logger.debug(f"No recipe artifact found for user {user_id} (search_hash: {search_hash})")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving recipe artifact for user {user_id}: {e}")
            return None
    
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
            
            logger.info(f"Cleared {deleted_count} cached artifacts for user {user_id}")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"Error clearing user cache: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            response = self.redis_client.ping()
            return response is True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False