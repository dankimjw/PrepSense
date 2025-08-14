"""
CrewAI ML Utilities

Machine learning utilities for preference learning and recommendation systems.
"""

import math
from typing import Any, Dict, List


def build_preference_vector(interactions: List[Dict[str, Any]]) -> List[float]:
    """
    Build user preference vector from interaction history.

    This is a simplified implementation for testing purposes.
    In production, this would use more sophisticated ML techniques.
    """
    if not interactions:
        return [0.5, 0.5, 0.5, 0.5, 0.5]  # Neutral preferences

    # Initialize preference dimensions
    # [cuisine_variety, spice_preference, healthy_preference, complexity_preference, novelty_preference]
    preferences = [0.0, 0.0, 0.0, 0.0, 0.0]
    total_interactions = len(interactions)

    for interaction in interactions:
        rating = interaction.get("rating", "neutral")
        cuisine_type = interaction.get("cuisine_type", "")
        dietary_tags = interaction.get("dietary_tags", [])

        # Weight positive interactions more than negative
        weight = 1.0 if rating == "thumbs_up" else -0.5 if rating == "thumbs_down" else 0.0

        # Cuisine variety preference
        if cuisine_type and cuisine_type not in ["american", "comfort"]:
            preferences[0] += weight * 0.2

        # Spice preference
        if "spicy" in dietary_tags or "indian" in cuisine_type.lower():
            preferences[1] += weight * 0.3

        # Healthy preference
        if any(tag in dietary_tags for tag in ["vegetarian", "vegan", "healthy", "low-carb"]):
            preferences[2] += weight * 0.3

        # Complexity preference (based on cuisine type)
        complex_cuisines = ["french", "japanese", "thai", "indian"]
        if any(cuisine in cuisine_type.lower() for cuisine in complex_cuisines):
            preferences[3] += weight * 0.2

        # Novelty preference (assume newer cuisine types indicate novelty preference)
        exotic_cuisines = ["korean", "ethiopian", "peruvian", "moroccan"]
        if any(cuisine in cuisine_type.lower() for cuisine in exotic_cuisines):
            preferences[4] += weight * 0.25

    # Normalize preferences to [0, 1] range
    for i in range(len(preferences)):
        # Apply sigmoid normalization
        preferences[i] = 1 / (1 + math.exp(-preferences[i]))

    return preferences


def calculate_recipe_similarity(
    recipe_vector: List[float], preference_vector: List[float]
) -> float:
    """
    Calculate similarity between recipe embedding and user preference vector.

    Returns a similarity score between 0 and 1.
    """
    if len(recipe_vector) != len(preference_vector):
        return 0.0

    # Calculate cosine similarity
    dot_product = sum(a * b for a, b in zip(recipe_vector, preference_vector))
    magnitude_a = math.sqrt(sum(a * a for a in recipe_vector))
    magnitude_b = math.sqrt(sum(b * b for b in preference_vector))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    similarity = dot_product / (magnitude_a * magnitude_b)

    # Normalize to [0, 1] range
    return max(0.0, min(1.0, (similarity + 1) / 2))


def rank_recipes_by_preference(
    recipes: List[Dict[str, Any]], preference_vector: List[float]
) -> List[Dict[str, Any]]:
    """
    Rank recipes by user preference similarity.

    Returns recipes sorted by preference score (highest first).
    """
    scored_recipes = []

    for recipe in recipes:
        # Get recipe embedding (mock implementation)
        recipe_vector = recipe.get("embedding", [0.5] * len(preference_vector))

        # Calculate similarity score
        similarity = calculate_recipe_similarity(recipe_vector, preference_vector)

        # Add score to recipe
        recipe_with_score = recipe.copy()
        recipe_with_score["preference_score"] = similarity
        scored_recipes.append(recipe_with_score)

    # Sort by preference score (descending)
    scored_recipes.sort(key=lambda x: x["preference_score"], reverse=True)

    return scored_recipes
