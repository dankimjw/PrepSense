"""
CrewAI Integration Module

This module provides real CrewAI implementation to replace the fake CrewAIService.
Includes background flows, real-time crews, and artifact caching.
"""

__version__ = "1.0.0"

from .cache_manager import ArtifactCacheManager

# Import main components for easier access
from .models import (
    CacheKey,
    CrewInput,
    CrewOutput,
    PantryArtifact,
    PreferenceArtifact,
    RecipeArtifact,
)

__all__ = [
    "PantryArtifact",
    "PreferenceArtifact",
    "RecipeArtifact",
    "CrewInput",
    "CrewOutput",
    "CacheKey",
    "ArtifactCacheManager",
]
