"""
CrewAI Embeddings Module

Utilities for creating embeddings for ingredients and recipes.
"""

import hashlib
from typing import Any, Dict, List


def create_ingredient_embeddings(normalized_items: List[Dict[str, Any]]) -> List[float]:
    """
    Create embeddings for normalized ingredients.

    This is a mock implementation for testing purposes.
    In production, this would use a proper embedding model.
    """
    # Simple mock embedding based on ingredient names
    if not normalized_items:
        return []

    # Create a simple hash-based embedding
    combined_names = " ".join([item.get("clean_name", "") for item in normalized_items])
    hash_bytes = hashlib.md5(combined_names.encode()).digest()

    # Convert to float vector (mock embedding of size 5)
    embedding = [float(b) / 255.0 for b in hash_bytes[:5]]

    return embedding


def create_recipe_embeddings(recipes: List[Dict[str, Any]]) -> Dict[int, List[float]]:
    """
    Create embeddings for recipes.

    This is a mock implementation for testing purposes.
    In production, this would use a proper embedding model.
    """
    embeddings = {}

    for recipe in recipes:
        recipe_id = recipe.get("id")
        if not recipe_id:
            continue

        # Create mock embedding based on recipe name and ingredients
        text = f"{recipe.get('name', '')} {' '.join(recipe.get('ingredients', []))}"
        hash_bytes = hashlib.md5(text.encode()).digest()

        # Convert to float vector (mock embedding of size 3)
        embedding = [float(b) / 255.0 for b in hash_bytes[:3]]
        embeddings[recipe_id] = embedding

    return embeddings
