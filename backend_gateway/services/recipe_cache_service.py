"""Service for caching and managing recipe recommendations to avoid repetition"""

import logging
from typing import List, Dict, Any, Set, Optional
from datetime import datetime, timedelta
import random
import hashlib
import json

logger = logging.getLogger(__name__)


class RecipeCacheService:
    """Manages recipe caching and ensures variety in recommendations"""
    
    def __init__(self):
        # In-memory cache for recipes per user
        # Structure: {user_id: {'recipes': [...], 'shown_ids': set(), 'last_refresh': datetime}}
        self._cache: Dict[int, Dict[str, Any]] = {}
        
        # Cache expiration time
        self.cache_duration = timedelta(hours=24)
        
        # Minimum number of recipes to keep in cache
        self.min_cache_size = 40
        
        # Number of recipes to show per request
        self.recipes_per_request = 5
    
    def _get_cache_key(self, user_id: int, pantry_hash: str) -> str:
        """Generate cache key based on user and pantry state"""
        return f"{user_id}_{pantry_hash}"
    
    def _hash_pantry_items(self, pantry_items: List[Dict[str, Any]]) -> str:
        """Create a hash of pantry items to detect changes"""
        # Sort items by name to ensure consistent hashing
        sorted_items = sorted(
            [(item.get('product_name', ''), item.get('quantity', 0)) 
             for item in pantry_items]
        )
        pantry_str = json.dumps(sorted_items, sort_keys=True)
        return hashlib.md5(pantry_str.encode()).hexdigest()[:8]
    
    def get_cached_recipes(
        self, 
        user_id: int, 
        pantry_items: List[Dict[str, Any]],
        exclude_shown: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get recipes from cache, excluding already shown ones
        
        Returns:
            List of recipes or None if cache miss/expired
        """
        pantry_hash = self._hash_pantry_items(pantry_items)
        cache_key = self._get_cache_key(user_id, pantry_hash)
        
        if cache_key not in self._cache:
            logger.info(f"Cache miss for user {user_id}")
            return None
        
        cache_data = self._cache[cache_key]
        
        # Check if cache expired
        if datetime.now() - cache_data['last_refresh'] > self.cache_duration:
            logger.info(f"Cache expired for user {user_id}")
            del self._cache[cache_key]
            return None
        
        # Get available recipes (not shown yet)
        all_recipes = cache_data['recipes']
        shown_ids = cache_data['shown_ids'] if exclude_shown else set()
        
        available_recipes = [
            recipe for recipe in all_recipes 
            if recipe.get('id') not in shown_ids
        ]
        
        # If we've shown most recipes, reset the shown list but keep some variety
        if len(available_recipes) < self.recipes_per_request:
            logger.info(f"Resetting shown recipes for user {user_id} (only {len(available_recipes)} left)")
            # Keep the last 10 shown to avoid immediate repetition
            recent_shown = list(shown_ids)[-10:] if len(shown_ids) > 10 else list(shown_ids)
            cache_data['shown_ids'] = set(recent_shown)
            
            # Recalculate available
            available_recipes = [
                recipe for recipe in all_recipes 
                if recipe.get('id') not in cache_data['shown_ids']
            ]
        
        # Shuffle for variety and take requested amount
        random.shuffle(available_recipes)
        selected_recipes = available_recipes[:self.recipes_per_request]
        
        # Mark these as shown
        for recipe in selected_recipes:
            cache_data['shown_ids'].add(recipe.get('id'))
        
        logger.info(f"Returning {len(selected_recipes)} recipes from cache (total: {len(all_recipes)}, shown: {len(cache_data['shown_ids'])})")
        
        return selected_recipes
    
    def cache_recipes(
        self, 
        user_id: int, 
        pantry_items: List[Dict[str, Any]], 
        recipes: List[Dict[str, Any]],
        merge_with_existing: bool = False
    ):
        """
        Cache recipes for a user
        
        Args:
            user_id: User ID
            pantry_items: Current pantry items
            recipes: Recipes to cache
            merge_with_existing: Whether to merge with existing cache
        """
        pantry_hash = self._hash_pantry_items(pantry_items)
        cache_key = self._get_cache_key(user_id, pantry_hash)
        
        if merge_with_existing and cache_key in self._cache:
            # Merge new recipes with existing ones
            existing_recipes = self._cache[cache_key]['recipes']
            existing_ids = {r.get('id') for r in existing_recipes}
            
            # Add only new recipes
            new_recipes = [r for r in recipes if r.get('id') not in existing_ids]
            all_recipes = existing_recipes + new_recipes
            
            logger.info(f"Merged {len(new_recipes)} new recipes with {len(existing_recipes)} existing")
        else:
            all_recipes = recipes
            logger.info(f"Cached {len(recipes)} recipes for user {user_id}")
        
        self._cache[cache_key] = {
            'recipes': all_recipes,
            'shown_ids': set(),
            'last_refresh': datetime.now(),
            'pantry_hash': pantry_hash
        }
    
    def mark_recipes_shown(self, user_id: int, pantry_items: List[Dict[str, Any]], recipe_ids: List[Any]):
        """Mark specific recipes as shown"""
        pantry_hash = self._hash_pantry_items(pantry_items)
        cache_key = self._get_cache_key(user_id, pantry_hash)
        
        if cache_key in self._cache:
            self._cache[cache_key]['shown_ids'].update(recipe_ids)
            logger.info(f"Marked {len(recipe_ids)} recipes as shown for user {user_id}")
    
    def clear_user_cache(self, user_id: int):
        """Clear all cached recipes for a user"""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del self._cache[key]
        logger.info(f"Cleared cache for user {user_id}")
    
    def get_cache_stats(self, user_id: int, pantry_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get cache statistics for debugging"""
        pantry_hash = self._hash_pantry_items(pantry_items)
        cache_key = self._get_cache_key(user_id, pantry_hash)
        
        if cache_key not in self._cache:
            return {'cached': False}
        
        cache_data = self._cache[cache_key]
        return {
            'cached': True,
            'total_recipes': len(cache_data['recipes']),
            'shown_recipes': len(cache_data['shown_ids']),
            'available_recipes': len(cache_data['recipes']) - len(cache_data['shown_ids']),
            'cache_age_minutes': (datetime.now() - cache_data['last_refresh']).seconds // 60,
            'pantry_hash': pantry_hash
        }