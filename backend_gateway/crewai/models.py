"""
Data models for CrewAI-based recipe recommendation system
These models define the structure for cached artifacts, flow states, and crew I/O
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import json
import re


@dataclass
class PantryArtifact:
    """Cached pantry analysis artifact"""
    user_id: int
    normalized_items: List[Dict[str, Any]]
    expiry_analysis: Dict[str, Any]
    ingredient_vectors: List[float]
    last_updated: datetime
    ttl_seconds: int
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        data = {
            "user_id": self.user_id,
            "normalized_items": self.normalized_items,
            "expiry_analysis": self.expiry_analysis,
            "ingredient_vectors": self.ingredient_vectors,
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PantryArtifact":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)
    
    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        age_seconds = (datetime.now() - self.last_updated).total_seconds()
        return age_seconds < self.ttl_seconds


@dataclass  
class PreferenceArtifact:
    """Cached user preference artifact"""
    user_id: int
    dietary_restrictions: List[str]
    allergens: List[str]
    cuisine_preferences: List[str]
    preference_vector: List[float]
    learning_data: Dict[str, Any]
    last_updated: datetime
    ttl_seconds: int
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        data = {
            "user_id": self.user_id,
            "dietary_restrictions": self.dietary_restrictions,
            "allergens": self.allergens,
            "cuisine_preferences": self.cuisine_preferences,
            "preference_vector": self.preference_vector,
            "learning_data": self.learning_data,
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PreferenceArtifact":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)
    
    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        age_seconds = (datetime.now() - self.last_updated).total_seconds()
        return age_seconds < self.ttl_seconds
    
    def is_valid_preference_vector(self) -> bool:
        """Validate preference vector values are between 0 and 1"""
        return all(0.0 <= val <= 1.0 for val in self.preference_vector)


@dataclass
class RecipeArtifact:
    """Cached recipe recommendations artifact"""
    user_id: int
    ranked_recipes: List[Dict[str, Any]]
    embeddings_index: Dict[str, List[float]]
    context_metadata: Dict[str, Any]
    last_updated: datetime
    ttl_seconds: int
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        data = {
            "user_id": self.user_id,
            "ranked_recipes": self.ranked_recipes,
            "embeddings_index": self.embeddings_index,
            "context_metadata": self.context_metadata,
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "RecipeArtifact":
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)
    
    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        age_seconds = (datetime.now() - self.last_updated).total_seconds()
        return age_seconds < self.ttl_seconds
    
    def is_properly_ranked(self) -> bool:
        """Check if recipes are sorted by rank_score in descending order"""
        if len(self.ranked_recipes) <= 1:
            return True
        
        for i in range(len(self.ranked_recipes) - 1):
            current_score = self.ranked_recipes[i].get("rank_score", 0)
            next_score = self.ranked_recipes[i + 1].get("rank_score", 0)
            if current_score < next_score:
                return False
        return True


# Flow State Objects (for CrewAI Flows)
@dataclass
class PantryState:
    """State object for PantryAnalysisFlow"""
    raw_pantry: Optional[List[Dict[str, Any]]] = None
    normalized_items: Optional[List[Dict[str, Any]]] = None
    expiry_analysis: Optional[Dict[str, Any]] = None
    ingredient_vectors: Optional[List[float]] = None


@dataclass
class PreferenceState:
    """State object for PreferenceLearningFlow"""
    user_interactions: Optional[List[Dict[str, Any]]] = None
    preference_vector: Optional[List[float]] = None
    dietary_restrictions: Optional[List[str]] = None
    allergens: Optional[List[str]] = None


@dataclass
class RecipeState:
    """State object for RecipeIntelligenceFlow"""
    recipe_candidates: Optional[List[Dict[str, Any]]] = None
    ranked_recipes: Optional[List[Dict[str, Any]]] = None
    nutrition_approved: Optional[List[Dict[str, Any]]] = None
    recipe_embeddings: Optional[Dict[str, List[float]]] = None


# Crew Input/Output Models
@dataclass
class CrewInput:
    """Input data for the recipe recommendation crew"""
    user_message: str
    user_id: int
    pantry_artifact: Optional[PantryArtifact] = None
    preference_artifact: Optional[PreferenceArtifact] = None
    recipe_candidates: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrewOutput:
    """Output from the recipe recommendation crew"""
    response_text: str
    recipe_cards: List[Dict[str, Any]]
    processing_time_ms: int
    agents_used: List[str]
    cache_hit: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def meets_performance_target(self, target_ms: int = 3000) -> bool:
        """Check if processing time meets performance target"""
        return self.processing_time_ms <= target_ms


# Cache Key Utilities
class CacheKey:
    """Utility class for generating and validating cache keys"""
    
    @staticmethod
    def pantry(user_id: int) -> str:
        """Generate pantry cache key"""
        return f"pantry:{user_id}"
    
    @staticmethod
    def preferences(user_id: int) -> str:
        """Generate preferences cache key"""
        return f"preferences:{user_id}"
    
    @staticmethod
    def recipes(user_id: int, context: Optional[str] = None) -> str:
        """Generate recipes cache key with optional context"""
        if context:
            return f"recipes:{user_id}:{context}"
        return f"recipes:{user_id}"
    
    @staticmethod
    def is_valid(key: str) -> bool:
        """Validate cache key format"""
        if not key or not isinstance(key, str):
            return False
        
        # Valid patterns: "type:user_id" or "type:user_id:context"
        pattern = r"^(pantry|preferences|recipes):\d+(:[\w]+)?$"
        return bool(re.match(pattern, key))
    
    @staticmethod
    def parse(key: str) -> tuple:
        """Parse cache key to extract components"""
        if not CacheKey.is_valid(key):
            raise ValueError(f"Invalid cache key format: {key}")
        
        parts = key.split(":")
        key_type = parts[0]
        user_id = parts[1]
        return key_type, user_id
    
    @staticmethod
    def parse_with_context(key: str) -> tuple:
        """Parse cache key including context"""
        if not CacheKey.is_valid(key):
            raise ValueError(f"Invalid cache key format: {key}")
        
        parts = key.split(":")
        key_type = parts[0]
        user_id = parts[1]
        context = parts[2] if len(parts) > 2 else None
        return key_type, user_id, context