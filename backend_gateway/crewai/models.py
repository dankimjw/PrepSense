"""
CrewAI Data Models

Data models for artifacts, states, and cache management in the CrewAI system.
Implements serialization, validation, and performance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json


@dataclass
class PantryArtifact:
    """Cached artifact from pantry analysis flow"""
    user_id: int
    normalized_items: List[Dict[str, Any]]
    expiry_analysis: Dict[str, Any]
    ingredient_vectors: List[float]
    last_updated: datetime
    ttl_seconds: int = 3600  # 1 hour default TTL
    
    def to_json(self) -> str:
        """Serialize artifact to JSON string"""
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
    def from_json(cls, json_str: str) -> 'PantryArtifact':
        """Deserialize artifact from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)
    
    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        return (datetime.now() - self.last_updated).total_seconds() < self.ttl_seconds


@dataclass
class PreferenceArtifact:
    """Cached artifact from preference learning flow"""
    user_id: int
    preference_vector: List[float]
    dietary_restrictions: List[str]
    allergens: List[str]
    cuisine_preferences: Dict[str, float]
    last_updated: datetime
    ttl_seconds: int = 86400  # 24 hours default TTL
    
    def to_json(self) -> str:
        """Serialize artifact to JSON string"""
        data = {
            "user_id": self.user_id,
            "preference_vector": self.preference_vector,
            "dietary_restrictions": self.dietary_restrictions,
            "allergens": self.allergens,
            "cuisine_preferences": self.cuisine_preferences,
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PreferenceArtifact':
        """Deserialize artifact from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)
    
    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        return (datetime.now() - self.last_updated).total_seconds() < self.ttl_seconds


@dataclass
class RecipeArtifact:
    """Cached artifact from recipe generation"""
    user_id: int
    recipe_cards: List[Dict[str, Any]]
    search_context: Dict[str, Any]
    generated_at: datetime
    ttl_seconds: int = 1800  # 30 minutes default TTL
    
    def to_json(self) -> str:
        """Serialize artifact to JSON string"""
        data = {
            "user_id": self.user_id,
            "recipe_cards": self.recipe_cards,
            "search_context": self.search_context,
            "generated_at": self.generated_at.isoformat(),
            "ttl_seconds": self.ttl_seconds
        }
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RecipeArtifact':
        """Deserialize artifact from JSON string"""
        data = json.loads(json_str)
        data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        return cls(**data)
    
    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        return (datetime.now() - self.generated_at).total_seconds() < self.ttl_seconds


@dataclass
class PantryState:
    """State object for PantryAnalysisFlow"""
    raw_pantry: List[Dict[str, Any]] = field(default_factory=list)
    normalized_items: List[Dict[str, Any]] = field(default_factory=list)
    expiry_analysis: Dict[str, Any] = field(default_factory=dict)
    ingredient_vectors: List[float] = field(default_factory=list)


@dataclass
class PreferenceState:
    """State object for PreferenceLearningFlow"""
    user_interactions: List[Dict[str, Any]] = field(default_factory=list)
    preference_vector: List[float] = field(default_factory=list)
    dietary_restrictions: List[str] = field(default_factory=list)
    allergens: List[str] = field(default_factory=list)
    cuisine_preferences: Dict[str, float] = field(default_factory=dict)


@dataclass
class RecipeState:
    """State object for real-time recipe crew"""
    pantry_context: Optional[PantryArtifact] = None
    preference_context: Optional[PreferenceArtifact] = None
    search_query: str = ""
    candidate_recipes: List[Dict[str, Any]] = field(default_factory=list)
    final_recipes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CrewInput:
    """Input to CrewAI crew execution"""
    user_id: int
    search_query: str
    pantry_items: List[Dict[str, Any]] = field(default_factory=list)
    dietary_restrictions: List[str] = field(default_factory=list)
    max_recipes: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CrewAI input"""
        return {
            "user_id": self.user_id,
            "search_query": self.search_query,
            "pantry_items": self.pantry_items,
            "dietary_restrictions": self.dietary_restrictions,
            "max_recipes": self.max_recipes
        }


@dataclass
class CrewOutput:
    """Output from CrewAI crew execution"""
    response_text: str
    recipe_cards: List[Dict[str, Any]]
    processing_time_ms: int
    agents_used: List[str]
    cache_hit: bool = False
    
    def meets_performance_target(self, target_ms: int = 3000) -> bool:
        """Check if processing time meets performance target"""
        return self.processing_time_ms <= target_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "response_text": self.response_text,
            "recipe_cards": self.recipe_cards,
            "processing_time_ms": self.processing_time_ms,
            "agents_used": self.agents_used,
            "cache_hit": self.cache_hit,
            "meets_performance_target": self.meets_performance_target()
        }


class CacheKey:
    """Redis cache key generation utilities"""
    
    @staticmethod
    def pantry(user_id: int) -> str:
        """Generate cache key for pantry artifact"""
        return f"pantry_artifact:{user_id}"
    
    @staticmethod
    def preference(user_id: int) -> str:
        """Generate cache key for preference artifact"""
        return f"preference_artifact:{user_id}"
    
    @staticmethod
    def recipe(user_id: int, search_hash: str) -> str:
        """Generate cache key for recipe artifact"""
        return f"recipe_artifact:{user_id}:{search_hash}"
    
    @staticmethod
    def crew_session(user_id: int, session_id: str) -> str:
        """Generate cache key for crew session"""
        return f"crew_session:{user_id}:{session_id}"