"""
CrewAI Artifact Cache Manager

Redis-based caching for pantry artifacts, preference artifacts, and recipe artifacts.
Provides automatic TTL management and serialization.
"""

from typing import Optional
import redis
import json
from datetime import datetime
import os

from .models import PantryArtifact, PreferenceArtifact, RecipeArtifact, CacheKey


class ArtifactCacheManager:
    """Redis-based cache manager for CrewAI artifacts"""
    
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
    
    def save_pantry_artifact(self, artifact: PantryArtifact) -> bool:
        """Save pantry artifact to cache"""
        try:
            key = CacheKey.pantry(artifact.user_id)
            json_data = artifact.to_json()
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
            return False