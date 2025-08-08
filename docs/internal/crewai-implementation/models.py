"""
CrewAI Data Models

Data models for artifacts, states, and cache management in the CrewAI system.
Implements serialization, validation, and performance tracking.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union


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
            "ttl_seconds": self.ttl_seconds,
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "PantryArtifact":
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
    learning_data: Dict[str, Any]
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
            "learning_data": self.learning_data,
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "PreferenceArtifact":
        """Deserialize artifact from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)

    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        return (datetime.now() - self.last_updated).total_seconds() < self.ttl_seconds

    def is_valid_preference_vector(self) -> bool:
        """Validate preference vector values are between 0 and 1"""
        return all(0.0 <= val <= 1.0 for val in self.preference_vector)


@dataclass
class RecipeArtifact:
    """Cached artifact from recipe generation"""

    user_id: int
    ranked_recipes: List[Dict[str, Any]]
    embeddings_index: Dict[str, List[float]]
    context_metadata: Dict[str, Any]
    last_updated: datetime
    ttl_seconds: int = 7200  # 2 hours default TTL

    def to_json(self) -> str:
        """Serialize artifact to JSON string"""
        data = {
            "user_id": self.user_id,
            "ranked_recipes": self.ranked_recipes,
            "embeddings_index": self.embeddings_index,
            "context_metadata": self.context_metadata,
            "last_updated": self.last_updated.isoformat(),
            "ttl_seconds": self.ttl_seconds,
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "RecipeArtifact":
        """Deserialize artifact from JSON string"""
        data = json.loads(json_str)
        data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)

    def is_fresh(self) -> bool:
        """Check if artifact is still within TTL"""
        return (datetime.now() - self.last_updated).total_seconds() < self.ttl_seconds

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
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

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
            "metadata": self.metadata,
            "meets_performance_target": self.meets_performance_target(),
        }


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
        user_id = int(parts[1])
        return key_type, user_id

    @staticmethod
    def parse_with_context(key: str) -> tuple:
        """Parse cache key including context"""
        if not CacheKey.is_valid(key):
            raise ValueError(f"Invalid cache key format: {key}")

        parts = key.split(":")
        key_type = parts[0]
        user_id = int(parts[1])
        context = parts[2] if len(parts) > 2 else None
        return key_type, user_id, context
