"""
CrewAI Background Flows

Implementation of background analysis flows using CrewAI Flow framework.
Includes pantry analysis, preference learning, and recipe intelligence flows.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from crewai.flow.flow import Flow, listen, start, router
from pydantic import BaseModel

from .models import (
    PantryState, PreferenceState, RecipeState,
    PantryArtifact, PreferenceArtifact
)
from .cache_manager import ArtifactCacheManager


class PantryAnalysisFlow(Flow[PantryState]):
    """Background flow for analyzing pantry contents and creating embeddings"""
    
    def __init__(self):
        """Initialize the pantry analysis flow"""
        super().__init__()
        self.cache_manager = ArtifactCacheManager()
        
        # Import database service here to avoid circular imports
        try:
            from backend_gateway.config.database import get_database_service
            self.db_service = get_database_service()
        except ImportError:
            self.db_service = None
    
    @start()
    def fetch_pantry_data(self) -> str:
        """Fetch raw pantry data from database"""
        if not self.db_service:
            print("Database service not available, using mock data")
            # Use mock data for testing
            self.state.raw_pantry = [
                {
                    "pantry_item_id": 1,
                    "product_name": "Chicken Breast – 2 lbs",
                    "quantity": 2,
                    "unit_of_measurement": "lbs",
                    "expiration_date": (datetime.now() + timedelta(days=2)).date(),
                    "category": "protein"
                }
            ]
            return "data_fetched"
        
        # Get user_id from kickoff inputs
        user_id = getattr(self, '_user_id', 111)  # Default demo user
        
        # Query pantry data
        query = """
        SELECT pantry_item_id, product_name, quantity, unit_of_measurement, 
               expiration_date, category
        FROM user_pantry_full 
        WHERE user_id = %(user_id)s
        """
        
        try:
            self.state.raw_pantry = self.db_service.execute_query(query, {"user_id": user_id})
            return "data_fetched"
        except Exception as e:
            print(f"Error fetching pantry data: {e}")
            self.state.raw_pantry = []
            return "data_fetched"
    
    @listen(fetch_pantry_data)
    def normalize_ingredients(self, previous_result: str) -> str:
        """Normalize ingredient names and categorize items"""
        normalized_items = []
        
        for item in self.state.raw_pantry:
            # Clean item name - remove size/quantity info
            clean_name = self._clean_item_name(item.get("product_name", ""))
            
            normalized_item = {
                "clean_name": clean_name,
                "category": item.get("category", "other"),
                "expiration_date": item.get("expiration_date"),
                "original_name": item.get("product_name"),
                "quantity": item.get("quantity", 1),
                "unit": item.get("unit_of_measurement", "each")
            }
            
            normalized_items.append(normalized_item)
        
        self.state.normalized_items = normalized_items
        return "normalized"
    
    @listen(normalize_ingredients)
    def analyze_expiry(self, previous_result: str) -> str:
        """Analyze expiration dates and categorize by urgency"""
        now = datetime.now().date()
        
        expiring_soon = []
        expired = []
        urgency_scores = {}
        
        for item in self.state.normalized_items:
            exp_date = item.get("expiration_date")
            if not exp_date:
                continue
            
            # Convert to date if it's a datetime
            if hasattr(exp_date, 'date'):
                exp_date = exp_date.date()
            
            days_until_expiry = (exp_date - now).days
            
            if days_until_expiry < 0:
                expired.append({
                    "name": item["clean_name"],
                    "days": abs(days_until_expiry),
                    "original_name": item["original_name"]
                })
            elif days_until_expiry <= 7:  # Expiring within a week
                expiring_soon.append({
                    "name": item["clean_name"],
                    "days": days_until_expiry,
                    "original_name": item["original_name"]
                })
            
            # Calculate urgency score (higher = more urgent)
            if days_until_expiry < 0:
                urgency_scores[item["clean_name"]] = 100  # Expired
            elif days_until_expiry == 0:
                urgency_scores[item["clean_name"]] = 90   # Expires today
            elif days_until_expiry <= 3:
                urgency_scores[item["clean_name"]] = 70   # Expires soon
            elif days_until_expiry <= 7:
                urgency_scores[item["clean_name"]] = 40   # Expires this week
            else:
                urgency_scores[item["clean_name"]] = 10   # Still fresh
        
        self.state.expiry_analysis = {
            "expiring_soon": expiring_soon,
            "expired": expired,
            "urgency_scores": urgency_scores
        }
        
        return "expiry_analyzed"
    
    @listen(analyze_expiry)
    def create_vectors(self, previous_result: str) -> str:
        """Create ingredient embeddings and cache the artifact"""
        # Import embeddings here to avoid circular imports
        try:
            from backend_gateway.crewai.embeddings import create_ingredient_embeddings
            self.state.ingredient_vectors = create_ingredient_embeddings(self.state.normalized_items)
        except ImportError:
            # Mock embeddings for testing
            self.state.ingredient_vectors = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Create and cache pantry artifact
        user_id = getattr(self, '_user_id', 111)  # Default demo user
        
        artifact = PantryArtifact(
            user_id=user_id,
            normalized_items=self.state.normalized_items,
            expiry_analysis=self.state.expiry_analysis,
            ingredient_vectors=self.state.ingredient_vectors,
            last_updated=datetime.now(),
            ttl_seconds=3600  # 1 hour TTL
        )
        
        # Save to cache
        self.cache_manager.save_pantry_artifact(artifact)
        
        return "complete"
    
    def _clean_item_name(self, name: str) -> str:
        """Clean item name by removing size/quantity information"""
        if not name:
            return "unknown item"
        
        # Remove common size patterns like "– 2 lbs", "- 1 bag", etc.
        cleaned = re.sub(r'\s*[–-]\s*\d+\s*(lbs?|oz|gal|bag|pack|count|units?).*$', '', name, flags=re.IGNORECASE)
        
        # Remove brand names and simplify (this is basic - could be enhanced)
        cleaned = cleaned.strip().lower()
        
        return cleaned


class PreferenceLearningFlow(Flow[PreferenceState]):
    """Background flow for learning user preferences from interactions"""
    
    def __init__(self):
        """Initialize the preference learning flow"""
        super().__init__()
        self.cache_manager = ArtifactCacheManager()
        
        # Import database service here to avoid circular imports
        try:
            from backend_gateway.config.database import get_database_service
            self.db_service = get_database_service()
        except ImportError:
            self.db_service = None
    
    @start()
    def gather_interactions(self) -> str:
        """Gather user interaction data from database"""
        if not self.db_service:
            print("Database service not available, using mock data")
            # Use mock interactions for testing
            self.state.user_interactions = [
                {
                    "recipe_id": 1,
                    "rating": "thumbs_up",
                    "cuisine_type": "italian",
                    "dietary_tags": ["vegetarian"],
                    "interaction_date": datetime.now() - timedelta(days=1)
                }
            ]
            return "interactions_gathered"
        
        # Get user_id from kickoff inputs
        user_id = getattr(self, '_user_id', 111)  # Default demo user
        
        # Query user interactions (ratings, recipe views, etc.)
        query = """
        SELECT recipe_id, rating, cuisine_type, dietary_tags, interaction_date
        FROM user_recipe_interactions 
        WHERE user_id = %(user_id)s
        ORDER BY interaction_date DESC
        LIMIT 100
        """
        
        try:
            self.state.user_interactions = self.db_service.execute_query(query, {"user_id": user_id})
            return "interactions_gathered"
        except Exception as e:
            print(f"Error gathering interactions: {e}")
            self.state.user_interactions = []
            return "interactions_gathered"
    
    @listen(gather_interactions)
    def build_preference_vector(self, previous_result: str) -> str:
        """Build user preference vector from interactions"""
        # Import ML utilities here to avoid circular imports
        try:
            from backend_gateway.crewai.ml import build_preference_vector
            self.state.preference_vector = build_preference_vector(self.state.user_interactions)
        except ImportError:
            # Mock preference vector for testing
            self.state.preference_vector = [0.7, 0.3, 0.9, 0.1, 0.5]
        
        # Extract dietary restrictions and allergens from interactions
        self._extract_dietary_info()
        
        return "preferences_updated"
    
    @listen(build_preference_vector)
    def cache_preferences(self, previous_result: str) -> str:
        """Cache the preference artifact"""
        user_id = getattr(self, '_user_id', 111)  # Default demo user
        
        artifact = PreferenceArtifact(
            user_id=user_id,
            preference_vector=self.state.preference_vector,
            dietary_restrictions=self.state.dietary_restrictions,
            allergens=self.state.allergens,
            cuisine_preferences=self.state.cuisine_preferences,
            last_updated=datetime.now(),
            ttl_seconds=86400  # 24 hour TTL
        )
        
        # Save to cache
        self.cache_manager.save_preference_artifact(artifact)
        
        return "preferences_cached"
    
    def _extract_dietary_info(self):
        """Extract dietary restrictions and cuisine preferences from interactions"""
        dietary_restrictions = set()
        allergens = set()
        cuisine_scores = {}
        
        for interaction in self.state.user_interactions:
            # Extract dietary tags
            tags = interaction.get("dietary_tags", [])
            if tags:
                dietary_restrictions.update(tags)
            
            # Build cuisine preference scores
            cuisine = interaction.get("cuisine_type")
            rating = interaction.get("rating")
            if cuisine and rating:
                score_modifier = 1 if rating == "thumbs_up" else -0.5
                cuisine_scores[cuisine] = cuisine_scores.get(cuisine, 0) + score_modifier
        
        self.state.dietary_restrictions = list(dietary_restrictions)
        self.state.allergens = list(allergens)  # Would need allergen detection logic
        self.state.cuisine_preferences = cuisine_scores


class RecipeIntelligenceFlow(Flow[RecipeState]):
    """Background flow for updating recipe embeddings and intelligence"""
    
    def __init__(self):
        """Initialize the recipe intelligence flow"""
        super().__init__()
        
        # Import database service here to avoid circular imports
        try:
            from backend_gateway.config.database import get_database_service
            self.db_service = get_database_service()
        except ImportError:
            self.db_service = None
    
    @start()
    def update_recipe_embeddings(self) -> str:
        """Update recipe embeddings from database"""
        if not self.db_service:
            print("Database service not available, using mock data")
            # Mock recipes for testing
            recipes = [
                {"id": 1, "name": "Pasta Carbonara", "ingredients": ["pasta", "eggs", "bacon"]},
                {"id": 2, "name": "Chicken Stir Fry", "ingredients": ["chicken", "vegetables", "soy sauce"]}
            ]
        else:
            # Query all recipes
            query = """
            SELECT id, name, ingredients
            FROM recipes
            WHERE updated_at > NOW() - INTERVAL '1 day'
            """
            
            try:
                recipes = self.db_service.execute_query(query)
            except Exception as e:
                print(f"Error querying recipes: {e}")
                recipes = []
        
        # Create embeddings for recipes
        try:
            from backend_gateway.crewai.embeddings import create_recipe_embeddings
            recipe_embeddings = create_recipe_embeddings(recipes)
        except ImportError:
            # Mock embeddings for testing
            recipe_embeddings = {
                recipe["id"]: [0.1, 0.2, 0.3] for recipe in recipes
            }
        
        # Store embeddings in state
        if hasattr(self.state, 'recipe_embeddings'):
            self.state.recipe_embeddings = recipe_embeddings
        else:
            # For testing when state might not have this attribute
            setattr(self.state, 'recipe_embeddings', recipe_embeddings)
        
        return "embeddings_updated"