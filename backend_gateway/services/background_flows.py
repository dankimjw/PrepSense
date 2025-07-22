"""
Background Flows for PrepSense
Handles deterministic tasks that can be pre-computed and cached
"""

import os
import json
import logging
import pickle
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class InventoryItem:
    """Normalized inventory item structure"""
    name: str
    category: str
    quantity: float
    unit: str
    expiration_date: Optional[datetime]
    days_until_expiry: Optional[int]
    confidence_score: float = 1.0

@dataclass
class ExpiringItem:
    """Item that's expiring soon"""
    name: str
    days_left: int
    expiration_date: datetime
    urgency_score: float  # 0-1, higher = more urgent

@dataclass
class UserPreferenceVector:
    """User preference vector for fast matching"""
    cuisine_weights: Dict[str, float]
    ingredient_preferences: Dict[str, float]  # positive/negative scores
    nutritional_goals: Dict[str, float]
    cooking_time_preference: float  # minutes
    complexity_preference: float  # 0-1, higher = more complex
    dietary_restrictions: List[str]
    allergens: List[str]
    last_updated: datetime


class BackgroundFlowManager:
    """Manages background flows for pre-computing data"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache file paths
        self.inventory_cache = self.cache_dir / "current_inventory.json"
        self.expiry_cache = self.cache_dir / "expiring_items.json"
        self.preference_cache = self.cache_dir / "user_preferences.pkl"
        self.recipe_index_cache = self.cache_dir / "recipe_embeddings.pkl"
        
    async def run_pantry_scan_flow(self, user_id: int, db_service) -> Dict[str, Any]:
        """
        Pantry Scan Flow - fetch & normalize items
        Triggers: User opens app, pantry updates
        """
        try:
            logger.info(f"Running pantry scan flow for user {user_id}")
            
            # Fetch raw pantry items
            query = """
                SELECT product_name, category, quantity, unit_of_measurement, expiration_date, 
                       created_at, updated_at
                FROM pantry_items 
                WHERE quantity > 0
            """
            raw_items = db_service.execute_query(query, {})
            
            # Normalize items
            normalized_items = []
            for item in raw_items:
                normalized = self._normalize_pantry_item(item)
                # Convert to dict with JSON-serializable values
                item_dict = normalized.__dict__.copy()
                if item_dict.get('expiration_date'):
                    item_dict['expiration_date'] = item_dict['expiration_date'].isoformat()
                normalized_items.append(item_dict)
            
            # Cache results
            inventory_data = {
                'user_id': user_id,
                'items': normalized_items,
                'last_updated': datetime.now().isoformat(),
                'total_items': len(normalized_items)
            }
            
            with open(self.inventory_cache, 'w') as f:
                json.dump(inventory_data, f, indent=2)
            
            logger.info(f"Cached {len(normalized_items)} normalized pantry items")
            return inventory_data
            
        except Exception as e:
            logger.error(f"Error in pantry scan flow: {str(e)}")
            raise

    async def run_expiry_auditor_flow(self, user_id: int) -> Dict[str, Any]:
        """
        Expiry Auditor Flow - compute days-left scores
        Triggers: Same as pantry scan
        """
        try:
            logger.info(f"Running expiry auditor flow for user {user_id}")
            
            # Load current inventory
            if not self.inventory_cache.exists():
                raise FileNotFoundError("Inventory cache not found - run pantry scan first")
                
            with open(self.inventory_cache, 'r') as f:
                inventory_data = json.load(f)
            
            # Calculate expiry urgency
            today = datetime.now().date()
            expiring_items = []
            
            for item in inventory_data['items']:
                if item.get('expiration_date'):
                    exp_date = datetime.fromisoformat(item['expiration_date']).date()
                    days_left = (exp_date - today).days
                    
                    # Only include items expiring in next 14 days
                    if days_left <= 14:
                        urgency_score = self._calculate_urgency_score(days_left)
                        expiring_items.append({
                            'name': item['name'],
                            'days_left': days_left,
                            'expiration_date': item['expiration_date'],
                            'urgency_score': urgency_score,
                            'category': item['category']
                        })
            
            # Sort by urgency
            expiring_items.sort(key=lambda x: x['urgency_score'], reverse=True)
            
            # Cache results
            expiry_data = {
                'user_id': user_id,
                'expiring_items': expiring_items,
                'last_updated': datetime.now().isoformat(),
                'total_expiring': len(expiring_items)
            }
            
            with open(self.expiry_cache, 'w') as f:
                json.dump(expiry_data, f, indent=2)
            
            logger.info(f"Cached {len(expiring_items)} expiring items")
            return expiry_data
            
        except Exception as e:
            logger.error(f"Error in expiry auditor flow: {str(e)}")
            raise

    async def run_preference_vector_builder(self, user_id: int, db_service) -> UserPreferenceVector:
        """
        Preference Vector Builder - from profile & past ratings
        Triggers: Rating changes, settings save
        """
        try:
            logger.info(f"Building preference vector for user {user_id}")
            
            # Get explicit preferences
            explicit_prefs = {}
            try:
                prefs_query = """
                    SELECT preferences FROM user_preferences WHERE user_id = %(user_id)s
                """
                prefs_result = db_service.execute_query(prefs_query, {'user_id': user_id})
                explicit_prefs = prefs_result[0]['preferences'] if prefs_result else {}
            except Exception as e:
                logger.warning(f"Could not load user preferences (table may not exist): {str(e)}")
                explicit_prefs = {}
            
            # Get interaction history for implicit preferences
            history = []
            try:
                history_query = """
                    SELECT recipe_id, action, metadata, timestamp
                    FROM user_recipe_interactions 
                    WHERE user_id = %(user_id)s AND timestamp >= %(since_date)s
                    ORDER BY timestamp DESC
                """
                
                # Look at last 90 days of interactions
                since_date = datetime.now() - timedelta(days=90)
                history = db_service.execute_query(history_query, {'user_id': user_id, 'since_date': since_date})
            except Exception as e:
                logger.warning(f"Could not load interaction history (table may not exist): {str(e)}")
                history = []
            
            # Build preference vector
            preference_vector = self._build_preference_vector(explicit_prefs, history)
            
            # Cache results
            with open(self.preference_cache, 'wb') as f:
                pickle.dump(preference_vector, f)
            
            logger.info(f"Built and cached preference vector for user {user_id}")
            return preference_vector
            
        except Exception as e:
            logger.error(f"Error building preference vector: {str(e)}")
            raise

    def _normalize_pantry_item(self, raw_item: Dict[str, Any]) -> InventoryItem:
        """Normalize a raw pantry item"""
        # Calculate days until expiry
        days_until_expiry = None
        exp_date = None
        
        if raw_item.get('expiration_date'):
            exp_date = datetime.strptime(str(raw_item['expiration_date']), '%Y-%m-%d')
            days_until_expiry = (exp_date.date() - datetime.now().date()).days
        
        return InventoryItem(
            name=raw_item['product_name'].lower().strip(),
            category=raw_item.get('category', 'other'),
            quantity=float(raw_item.get('quantity', 0)),
            unit=raw_item.get('unit_of_measurement', 'unit'),
            expiration_date=exp_date,
            days_until_expiry=days_until_expiry
        )

    def _calculate_urgency_score(self, days_left: int) -> float:
        """Calculate urgency score for expiring items (0-1, higher = more urgent)"""
        if days_left <= 0:
            return 1.0  # Expired - highest urgency
        elif days_left <= 2:
            return 0.9  # Very urgent
        elif days_left <= 5:
            return 0.7  # Urgent
        elif days_left <= 7:
            return 0.5  # Moderate
        elif days_left <= 14:
            return 0.3  # Low urgency
        else:
            return 0.1  # Very low urgency

    def _build_preference_vector(self, explicit_prefs: Dict, history: List[Dict]) -> UserPreferenceVector:
        """Build preference vector from explicit preferences and interaction history"""
        
        # Start with explicit preferences
        cuisine_weights = {}
        ingredient_preferences = {}
        nutritional_goals = {}
        
        # Process explicit preferences
        if 'cuisine_preferences' in explicit_prefs:
            for cuisine in explicit_prefs['cuisine_preferences']:
                cuisine_weights[cuisine] = 1.0
        
        if 'favorite_ingredients' in explicit_prefs:
            for ingredient in explicit_prefs['favorite_ingredients']:
                ingredient_preferences[ingredient] = 1.0
        
        if 'disliked_ingredients' in explicit_prefs:
            for ingredient in explicit_prefs['disliked_ingredients']:
                ingredient_preferences[ingredient] = -1.0
        
        # Learn from interaction history
        for interaction in history:
            if interaction['action'] in ['rated_positive', 'cooked', 'saved']:
                # Positive signal - extract preferences
                metadata = json.loads(interaction.get('metadata', '{}'))
                
                # Boost cuisine preferences
                if 'cuisine' in metadata:
                    cuisine = metadata['cuisine']
                    cuisine_weights[cuisine] = cuisine_weights.get(cuisine, 0) + 0.1
                
                # Boost ingredient preferences
                if 'ingredients' in metadata:
                    for ingredient in metadata['ingredients']:
                        ingredient_preferences[ingredient] = ingredient_preferences.get(ingredient, 0) + 0.1
            
            elif interaction['action'] in ['rated_negative', 'dismissed']:
                # Negative signal - reduce preferences
                metadata = json.loads(interaction.get('metadata', '{}'))
                
                if 'cuisine' in metadata:
                    cuisine = metadata['cuisine']
                    cuisine_weights[cuisine] = cuisine_weights.get(cuisine, 0) - 0.1
                
                if 'ingredients' in metadata:
                    for ingredient in metadata['ingredients']:
                        ingredient_preferences[ingredient] = ingredient_preferences.get(ingredient, 0) - 0.1
        
        # Normalize weights
        cuisine_weights = {k: max(-1, min(1, v)) for k, v in cuisine_weights.items()}
        ingredient_preferences = {k: max(-1, min(1, v)) for k, v in ingredient_preferences.items()}
        
        return UserPreferenceVector(
            cuisine_weights=cuisine_weights,
            ingredient_preferences=ingredient_preferences,
            nutritional_goals=nutritional_goals,
            cooking_time_preference=explicit_prefs.get('cooking_time_preference', 30),
            complexity_preference=explicit_prefs.get('complexity_preference', 0.5),
            dietary_restrictions=explicit_prefs.get('dietary_restrictions', []),
            allergens=explicit_prefs.get('allergens', []),
            last_updated=datetime.now()
        )

    def load_cached_inventory(self) -> Optional[Dict[str, Any]]:
        """Load cached inventory data"""
        if self.inventory_cache.exists():
            with open(self.inventory_cache, 'r') as f:
                return json.load(f)
        return None

    def load_cached_expiry(self) -> Optional[Dict[str, Any]]:
        """Load cached expiry data"""
        if self.expiry_cache.exists():
            with open(self.expiry_cache, 'r') as f:
                return json.load(f)
        return None

    def load_cached_preferences(self) -> Optional[UserPreferenceVector]:
        """Load cached preference vector"""
        if self.preference_cache.exists():
            with open(self.preference_cache, 'rb') as f:
                return pickle.load(f)
        return None

    def is_cache_fresh(self, cache_file: Path, max_age_hours: int = 24) -> bool:
        """Check if cache is still fresh"""
        if not cache_file.exists():
            return False
        
        modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - modified_time).total_seconds() / 3600
        
        return age_hours < max_age_hours


class CacheManager:
    """Manages cache lifecycle and invalidation"""
    
    def __init__(self, flow_manager: BackgroundFlowManager):
        self.flow_manager = flow_manager
    
    async def ensure_fresh_cache(self, user_id: int, db_service, force_refresh: bool = False):
        """Ensure all caches are fresh, refresh if needed"""
        tasks = []
        
        # Check inventory cache
        if force_refresh or not self.flow_manager.is_cache_fresh(self.flow_manager.inventory_cache, 6):
            tasks.append(self.flow_manager.run_pantry_scan_flow(user_id, db_service))
        
        # Check expiry cache
        if force_refresh or not self.flow_manager.is_cache_fresh(self.flow_manager.expiry_cache, 6):
            tasks.append(self.flow_manager.run_expiry_auditor_flow(user_id))
        
        # Check preference cache
        if force_refresh or not self.flow_manager.is_cache_fresh(self.flow_manager.preference_cache, 24):
            tasks.append(self.flow_manager.run_preference_vector_builder(user_id, db_service))
        
        # Run tasks in parallel
        if tasks:
            await asyncio.gather(*tasks)
    
    def invalidate_cache(self, cache_type: str = 'all'):
        """Invalidate specific or all caches"""
        if cache_type in ['all', 'inventory']:
            self.flow_manager.inventory_cache.unlink(missing_ok=True)
        
        if cache_type in ['all', 'expiry']:
            self.flow_manager.expiry_cache.unlink(missing_ok=True)
        
        if cache_type in ['all', 'preferences']:
            self.flow_manager.preference_cache.unlink(missing_ok=True)