"""
CrewAI Background Flows

Background flows that run deterministically or opportunistically ahead of time.
These flows pre-compute artifacts for the real-time crew to reuse.
Implements the background/foreground pattern for optimal latency.
"""

from crewai.flow.flow import Flow, start, listen
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .models import PantryState, PreferenceState, PantryArtifact, PreferenceArtifact
from .cache_manager import ArtifactCacheManager

logger = logging.getLogger(__name__)


@dataclass 
class PantryFlowInput:
    """Input for pantry analysis background flow"""
    user_id: int
    trigger_reason: str = "scheduled"  # scheduled, pantry_updated, app_launch


@dataclass
class PreferenceFlowInput:
    """Input for preference learning background flow"""
    user_id: int
    trigger_reason: str = "scheduled"  # scheduled, rating_changed, diet_updated


class PantryAnalysisFlow(Flow[PantryState]):
    """
    Background flow for pantry analysis.
    
    This flow:
    1. Fetches raw pantry data from database
    2. Normalizes and cleans the data
    3. Computes expiry scores and ingredient vectors
    4. Persists the artifact for the hot path to use
    
    Triggers:
    - App launch (cold-start)
    - Pantry CRUD operations
    - Scheduled batch (nightly)
    """
    
    def __init__(self):
        super().__init__()
        self.cache_manager = ArtifactCacheManager()
    
    @start()
    def fetch_pantry_data(self):
        """Fetch raw pantry items from database"""
        try:
            user_id = self.args.user_id
            logger.info(f"Starting pantry analysis for user {user_id} - trigger: {self.args.trigger_reason}")
            
            # TODO: Replace with actual database service
            # from backend_gateway.config.database import get_database_service
            # db_service = get_database_service()
            # raw_items = await db_service.get_user_pantry_items(user_id)
            
            # Mock data for now
            self.state.raw_pantry = [
                {"id": 1, "name": "Milk", "quantity": 1, "unit": "gallon", "expiry": "2024-01-25"},
                {"id": 2, "name": "Bread", "quantity": 2, "unit": "loaf", "expiry": "2024-01-22"},
                {"id": 3, "name": "Apples", "quantity": 6, "unit": "each", "expiry": "2024-01-30"}
            ]
            
            logger.info(f"Fetched {len(self.state.raw_pantry)} pantry items for user {user_id}")
            return "pantry_fetched"
            
        except Exception as e:
            logger.error(f"Failed to fetch pantry data for user {self.args.user_id}: {e}")
            return "fetch_failed"
    
    @listen(fetch_pantry_data)
    def normalize_items(self, trigger_result):
        """Normalize and clean pantry items"""
        if trigger_result == "fetch_failed":
            return "normalization_skipped"
            
        try:
            normalized = []
            for item in self.state.raw_pantry:
                # Normalize item data
                normalized_item = {
                    "id": item["id"],
                    "name": item["name"].strip().title(),
                    "quantity": float(item["quantity"]),
                    "unit": item["unit"].lower(),
                    "expiry_date": item["expiry"],
                    "category": self._categorize_item(item["name"]),
                    "days_until_expiry": self._calculate_days_until_expiry(item["expiry"])
                }
                normalized.append(normalized_item)
            
            self.state.normalized_items = normalized
            logger.info(f"Normalized {len(normalized)} items")
            return "items_normalized"
            
        except Exception as e:
            logger.error(f"Failed to normalize items: {e}")
            return "normalization_failed"
    
    @listen(normalize_items)
    def compute_expiry_analysis(self, trigger_result):
        """Compute expiry scores and analysis"""
        if trigger_result in ["normalization_skipped", "normalization_failed"]:
            return "expiry_analysis_skipped"
            
        try:
            expiry_analysis = {
                "expiring_soon": [],  # < 3 days
                "expiring_this_week": [],  # 3-7 days
                "fresh": [],  # > 7 days
                "expired": [],  # < 0 days
                "total_items": len(self.state.normalized_items),
                "urgency_score": 0.0
            }
            
            for item in self.state.normalized_items:
                days = item["days_until_expiry"]
                
                if days < 0:
                    expiry_analysis["expired"].append(item)
                elif days <= 3:
                    expiry_analysis["expiring_soon"].append(item)
                elif days <= 7:
                    expiry_analysis["expiring_this_week"].append(item)
                else:
                    expiry_analysis["fresh"].append(item)
            
            # Calculate urgency score (0-1, higher = more urgent)
            total = expiry_analysis["total_items"]
            if total > 0:
                urgent_count = len(expiry_analysis["expired"]) + len(expiry_analysis["expiring_soon"])
                expiry_analysis["urgency_score"] = urgent_count / total
            
            self.state.expiry_analysis = expiry_analysis
            logger.info(f"Computed expiry analysis - {len(expiry_analysis['expiring_soon'])} items expiring soon")
            return "expiry_computed"
            
        except Exception as e:
            logger.error(f"Failed to compute expiry analysis: {e}")
            return "expiry_failed"
    
    @listen(compute_expiry_analysis)
    def generate_ingredient_vectors(self, trigger_result):
        """Generate ingredient embeddings for recipe matching"""
        if trigger_result in ["expiry_analysis_skipped", "expiry_failed"]:
            return "vectors_skipped"
            
        try:
            # TODO: Replace with actual embedding service
            # For now, create mock vectors
            ingredient_vectors = []
            for item in self.state.normalized_items:
                # Mock 384-dimensional embedding
                vector = [0.1] * 384  # Would use actual embedding model
                ingredient_vectors.append(vector)
            
            self.state.ingredient_vectors = ingredient_vectors
            logger.info(f"Generated {len(ingredient_vectors)} ingredient vectors")
            return "vectors_generated"
            
        except Exception as e:
            logger.error(f"Failed to generate ingredient vectors: {e}")
            return "vectors_failed"
    
    @listen(generate_ingredient_vectors)
    def persist_artifact(self, trigger_result):
        """Persist the pantry artifact to cache for hot path"""
        if trigger_result in ["vectors_skipped", "vectors_failed"]:
            logger.warning("Persisting artifact with incomplete data")
        
        try:
            # Create pantry artifact
            artifact = PantryArtifact(
                user_id=self.args.user_id,
                normalized_items=self.state.normalized_items or [],
                expiry_analysis=self.state.expiry_analysis or {},
                ingredient_vectors=self.state.ingredient_vectors or [],
                last_updated=datetime.now(),
                ttl_seconds=3600  # 1 hour TTL
            )
            
            # Save to cache
            success = self.cache_manager.save_pantry_artifact(artifact)
            
            if success:
                logger.info(f"Successfully persisted pantry artifact for user {self.args.user_id}")
                return "artifact_persisted"
            else:
                logger.error(f"Failed to persist pantry artifact for user {self.args.user_id}")
                return "persist_failed"
                
        except Exception as e:
            logger.error(f"Failed to persist pantry artifact: {e}")
            return "persist_failed"
    
    def _categorize_item(self, item_name: str) -> str:
        """Simple categorization logic"""
        item_lower = item_name.lower()
        
        if any(word in item_lower for word in ["milk", "cheese", "yogurt", "butter"]):
            return "Dairy"
        elif any(word in item_lower for word in ["bread", "bagel", "muffin"]):
            return "Bakery" 
        elif any(word in item_lower for word in ["apple", "banana", "orange", "berry"]):
            return "Produce"
        elif any(word in item_lower for word in ["chicken", "beef", "pork", "fish"]):
            return "Meat"
        else:
            return "Pantry"
    
    def _calculate_days_until_expiry(self, expiry_str: str) -> int:
        """Calculate days until expiry from date string"""
        try:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            return (expiry_date - today).days
        except:
            return 7  # Default to 7 days if parsing fails


class PreferenceLearningFlow(Flow[PreferenceState]):
    """
    Background flow for learning user preferences.
    
    This flow:
    1. Fetches user interaction data (ratings, recipe views, etc.)
    2. Analyzes dietary restrictions and allergens
    3. Builds preference vectors and cuisine preferences
    4. Persists the preference artifact for hot path
    
    Triggers:
    - User rates a recipe
    - User changes dietary restrictions
    - Scheduled batch (nightly)
    """
    
    def __init__(self):
        super().__init__()
        self.cache_manager = ArtifactCacheManager()
    
    @start()
    def fetch_user_interactions(self):
        """Fetch user interaction data"""
        try:
            user_id = self.args.user_id
            logger.info(f"Starting preference learning for user {user_id} - trigger: {self.args.trigger_reason}")
            
            # TODO: Replace with actual database queries
            # Mock interaction data
            self.state.user_interactions = [
                {"recipe_id": 1, "rating": 5, "cuisine": "Italian", "viewed_at": "2024-01-20"},
                {"recipe_id": 2, "rating": 3, "cuisine": "Mexican", "viewed_at": "2024-01-19"},
                {"recipe_id": 3, "rating": 4, "cuisine": "Italian", "viewed_at": "2024-01-18"}
            ]
            
            logger.info(f"Fetched {len(self.state.user_interactions)} user interactions")
            return "interactions_fetched"
            
        except Exception as e:
            logger.error(f"Failed to fetch user interactions for user {self.args.user_id}: {e}")
            return "fetch_failed"
    
    @listen(fetch_user_interactions)
    def analyze_dietary_preferences(self, trigger_result):
        """Analyze dietary restrictions and allergens"""
        if trigger_result == "fetch_failed":
            return "analysis_skipped"
            
        try:
            # TODO: Get from user profile
            self.state.dietary_restrictions = ["vegetarian"]
            self.state.allergens = ["nuts", "shellfish"]
            
            logger.info(f"Analyzed dietary preferences: {self.state.dietary_restrictions}")
            return "preferences_analyzed"
            
        except Exception as e:
            logger.error(f"Failed to analyze dietary preferences: {e}")
            return "analysis_failed"
    
    @listen(analyze_dietary_preferences)
    def build_preference_vector(self, trigger_result):
        """Build preference vector from interactions"""
        if trigger_result in ["analysis_skipped", "analysis_failed"]:
            return "vector_skipped"
            
        try:
            # Simple preference vector based on ratings
            # In reality, this would use ML models
            preference_scores = {
                "spicy": 0.7,
                "sweet": 0.3,
                "savory": 0.8,
                "healthy": 0.9,
                "quick": 0.6,
                "complex": 0.4
            }
            
            # Convert to list for vector storage
            self.state.preference_vector = list(preference_scores.values())
            
            # Analyze cuisine preferences from interactions
            cuisine_counts = {}
            total_interactions = len(self.state.user_interactions)
            
            for interaction in self.state.user_interactions:
                cuisine = interaction["cuisine"]
                rating = interaction["rating"]
                
                if cuisine not in cuisine_counts:
                    cuisine_counts[cuisine] = {"count": 0, "total_rating": 0}
                
                cuisine_counts[cuisine]["count"] += 1
                cuisine_counts[cuisine]["total_rating"] += rating
            
            # Calculate cuisine preference scores
            cuisine_preferences = {}
            for cuisine, data in cuisine_counts.items():
                avg_rating = data["total_rating"] / data["count"]
                frequency = data["count"] / total_interactions
                # Combine rating and frequency
                cuisine_preferences[cuisine] = (avg_rating / 5.0) * 0.7 + frequency * 0.3
            
            self.state.cuisine_preferences = cuisine_preferences
            
            logger.info(f"Built preference vector and cuisine preferences: {cuisine_preferences}")
            return "vector_built"
            
        except Exception as e:
            logger.error(f"Failed to build preference vector: {e}")
            return "vector_failed"
    
    @listen(build_preference_vector)
    def persist_preference_artifact(self, trigger_result):
        """Persist the preference artifact to cache"""
        if trigger_result in ["vector_skipped", "vector_failed"]:
            logger.warning("Persisting preference artifact with incomplete data")
        
        try:
            # Create preference artifact
            artifact = PreferenceArtifact(
                user_id=self.args.user_id,
                preference_vector=self.state.preference_vector or [0.5] * 6,
                dietary_restrictions=self.state.dietary_restrictions or [],
                allergens=self.state.allergens or [],
                cuisine_preferences=self.state.cuisine_preferences or {},
                learning_data={
                    "total_interactions": len(self.state.user_interactions or []),
                    "last_analysis": datetime.now().isoformat(),
                    "trigger_reason": self.args.trigger_reason
                },
                last_updated=datetime.now(),
                ttl_seconds=86400  # 24 hours TTL
            )
            
            # Save to cache
            success = self.cache_manager.save_preference_artifact(artifact)
            
            if success:
                logger.info(f"Successfully persisted preference artifact for user {self.args.user_id}")
                return "artifact_persisted"
            else:
                logger.error(f"Failed to persist preference artifact for user {self.args.user_id}")
                return "persist_failed"
                
        except Exception as e:
            logger.error(f"Failed to persist preference artifact: {e}")
            return "persist_failed"


# Background Flow Orchestrator
class BackgroundFlowOrchestrator:
    """Orchestrates background flows for cache warming"""
    
    def __init__(self):
        self.cache_manager = ArtifactCacheManager()
    
    async def warm_user_cache(self, user_id: int, trigger_reason: str = "manual") -> Dict[str, bool]:
        """Warm cache for a user by running background flows"""
        results = {}
        
        try:
            # Run pantry analysis flow
            pantry_flow = PantryAnalysisFlow()
            pantry_result = pantry_flow.kickoff(
                inputs=PantryFlowInput(user_id=user_id, trigger_reason=trigger_reason)
            )
            results["pantry_flow"] = "artifact_persisted" in str(pantry_result)
            
            # Run preference learning flow  
            preference_flow = PreferenceLearningFlow()
            preference_result = preference_flow.kickoff(
                inputs=PreferenceFlowInput(user_id=user_id, trigger_reason=trigger_reason)
            )
            results["preference_flow"] = "artifact_persisted" in str(preference_result)
            
            logger.info(f"Cache warming completed for user {user_id}: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to warm cache for user {user_id}: {e}")
            return {"pantry_flow": False, "preference_flow": False}
    
    def should_warm_cache(self, user_id: int) -> bool:
        """Check if user needs cache warming"""
        return not self.cache_manager.has_fresh_data(user_id)