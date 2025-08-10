"""
Preference Learning Service
Learn and adapt to user preferences over time based on interactions
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class PreferenceLearningService:
    """Learn and adapt to user preferences over time"""

    def __init__(self, db_service):
        self.db_service = db_service

        # Default scoring weights
        self._default_weights = {
            "favorite_ingredient_match": 3.0,
            "preferred_cuisine_match": 2.5,
            "dietary_restriction_match": 5.0,
            "cooking_time_match": 2.0,
            "highly_rated_similar": 4.0,
            "frequently_cooked_ingredient": 2.5,
            "seasonal_match": 1.5,
            "expiring_ingredient_use": 3.5,
            "nutritional_goal_match": 2.0,
            "disliked_cuisine": -4.0,
            "disliked_ingredient": -3.0,
            "too_complex": -2.0,
            "poor_rating_similar": -3.5,
            "allergen_present": -10.0,
            "missing_key_equipment": -2.5,
        }

        # Learning parameters
        self.min_interactions_for_preference = 3
        self.recency_weight = 0.8  # Recent interactions matter more
        self.learning_rate = 0.1  # How quickly to adapt

    async def track_recipe_interaction(
        self,
        user_id: int,
        recipe_id: str,
        action: str,
        context: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Track user interactions with recipes

        Args:
            user_id: User ID
            recipe_id: Recipe ID (can be from any source)
            action: Type of action (viewed, saved, cooked, rated, dismissed)
            context: Context information (time, location, etc.)
            metadata: Additional metadata (rating value, cook time, modifications)

        Returns:
            Success status
        """
        try:
            # Prepare interaction data
            interaction_data = {
                "user_id": user_id,
                "recipe_id": recipe_id,
                "action": action,
                "timestamp": datetime.now(),
                "context": json.dumps(context or {}),
                "metadata": json.dumps(metadata or {}),
            }

            # Store in database
            query = """
                INSERT INTO user_recipe_interactions
                (user_id, recipe_id, action, timestamp, context, metadata)
                VALUES (%(user_id)s, %(recipe_id)s, %(action)s, %(timestamp)s,
                        %(context)s, %(metadata)s)
            """

            self.db_service.execute_query(query, interaction_data)

            # Update preferences if significant action
            if action in ["saved", "cooked", "rated"]:
                await self._update_preferences_from_interaction(
                    user_id, recipe_id, action, metadata
                )

            logger.info(f"Tracked {action} interaction for user {user_id} on recipe {recipe_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}")
            return False

    async def get_personalized_weights(self, user_id: int) -> dict[str, float]:
        """
        Get personalized scoring weights based on user history

        Args:
            user_id: User ID

        Returns:
            Dictionary of personalized weights
        """
        # Get user's interaction history
        history = await self._get_user_history(user_id, days=30)

        # Start with default weights
        weights = self._default_weights.copy()

        if not history:
            return weights

        # Analyze user patterns
        patterns = self._analyze_user_patterns(history)

        # Adjust weights based on patterns

        # Health consciousness
        if patterns["health_score"] > 0.7:
            weights["nutritional_goal_match"] *= 1.5
            weights["dietary_restriction_match"] *= 1.2
            logger.info(f"User {user_id} appears health-conscious, boosting nutrition weights")

        # Time sensitivity
        if patterns["quick_meal_preference"] > 0.6:
            weights["cooking_time_match"] *= 1.8
            weights["too_complex"] *= 1.5
            logger.info(f"User {user_id} prefers quick meals, boosting time weights")

        # Cuisine exploration
        if patterns["cuisine_diversity"] > 0.7:
            weights["preferred_cuisine_match"] *= 0.8  # Less weight on known cuisines
            weights["seasonal_match"] *= 1.3  # More variety
            logger.info(f"User {user_id} likes variety, adjusting cuisine weights")

        # Ingredient loyalty
        if patterns["ingredient_consistency"] > 0.8:
            weights["favorite_ingredient_match"] *= 1.5
            weights["frequently_cooked_ingredient"] *= 1.3
            logger.info(f"User {user_id} has consistent ingredient preferences")

        # Recipe complexity preference
        if patterns["complexity_preference"] == "simple":
            weights["too_complex"] *= 2.0
        elif patterns["complexity_preference"] == "complex":
            weights["too_complex"] *= 0.5

        return weights

    async def suggest_new_preferences(self, user_id: int) -> list[dict]:
        """
        Suggest new preferences based on user behavior

        Args:
            user_id: User ID

        Returns:
            List of preference suggestions
        """
        suggestions = []

        # Get interaction history
        history = await self._get_user_history(user_id, days=60)
        if not history:
            return suggestions

        # Get current preferences
        current_prefs = await self._get_current_preferences(user_id)

        # Analyze frequently used ingredients
        ingredient_counts = await self._analyze_ingredient_frequency(user_id, history)
        top_ingredients = [
            ing
            for ing, count in ingredient_counts.most_common(20)
            if count >= self.min_interactions_for_preference
        ]

        # Suggest new favorite ingredients
        current_favorites = set(current_prefs.get("favorite_ingredients", []))
        for ingredient in top_ingredients:
            if ingredient not in current_favorites:
                suggestions.append(
                    {
                        "type": "favorite_ingredient",
                        "value": ingredient,
                        "confidence": min(ingredient_counts[ingredient] / 10, 1.0),
                        "reason": f"You've used {ingredient} in {ingredient_counts[ingredient]} recent recipes",
                    }
                )

        # Analyze cuisine patterns
        cuisine_counts = await self._analyze_cuisine_frequency(user_id, history)
        for cuisine, count in cuisine_counts.most_common(5):
            if count >= self.min_interactions_for_preference:
                if cuisine not in current_prefs.get("cuisine_preferences", []):
                    suggestions.append(
                        {
                            "type": "cuisine_preference",
                            "value": cuisine,
                            "confidence": min(count / 10, 1.0),
                            "reason": f"You've enjoyed {count} {cuisine} recipes recently",
                        }
                    )

        # Analyze cooking time preferences
        avg_cook_time = await self._analyze_cooking_time_preference(user_id, history)
        if avg_cook_time:
            time_pref = (
                "quick" if avg_cook_time < 25 else "medium" if avg_cook_time < 45 else "leisurely"
            )
            suggestions.append(
                {
                    "type": "cooking_time_preference",
                    "value": time_pref,
                    "confidence": 0.8,
                    "reason": f"Your average recipe takes {int(avg_cook_time)} minutes",
                }
            )

        # Detect dietary patterns
        dietary_patterns = await self._detect_dietary_patterns(history)
        for diet_type, confidence in dietary_patterns.items():
            if confidence > 0.7 and diet_type not in current_prefs.get("dietary_preferences", []):
                suggestions.append(
                    {
                        "type": "dietary_preference",
                        "value": diet_type,
                        "confidence": confidence,
                        "reason": f"Your recent recipes align with {diet_type} diet",
                    }
                )

        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions[:10]  # Return top 10 suggestions

    async def get_disliked_patterns(self, user_id: int) -> dict:
        """
        Identify patterns in recipes the user dislikes or dismisses

        Args:
            user_id: User ID

        Returns:
            Dictionary of disliked patterns
        """
        # Get negative interactions
        negative_history = await self._get_negative_interactions(user_id)

        patterns = {
            "disliked_ingredients": [],
            "disliked_cuisines": [],
            "avoided_cooking_methods": [],
            "complexity_threshold": None,
            "time_threshold": None,
        }

        if not negative_history:
            return patterns

        # Analyze disliked ingredients
        ingredient_counts = defaultdict(int)
        cuisine_counts = defaultdict(int)
        complexity_scores = []
        cook_times = []

        for interaction in negative_history:
            recipe_data = interaction.get("recipe_data", {})

            # Count ingredients
            for ingredient in recipe_data.get("ingredients", []):
                ingredient_counts[self._normalize_ingredient(ingredient)] += 1

            # Count cuisines
            cuisine = recipe_data.get("cuisine_type")
            if cuisine:
                cuisine_counts[cuisine] += 1

            # Track complexity and time
            if "instructions" in recipe_data:
                complexity_scores.append(len(recipe_data["instructions"]))

            if "time" in recipe_data:
                cook_times.append(recipe_data["time"])

        # Identify consistently disliked items
        total_negative = len(negative_history)

        for ingredient, count in ingredient_counts.items():
            if count >= 3 or (count >= 2 and count / total_negative > 0.3):
                patterns["disliked_ingredients"].append(
                    {
                        "ingredient": ingredient,
                        "frequency": count,
                        "confidence": min(count / 5, 1.0),
                    }
                )

        for cuisine, count in cuisine_counts.items():
            if count >= 2 or count / total_negative > 0.25:
                patterns["disliked_cuisines"].append(
                    {"cuisine": cuisine, "frequency": count, "confidence": min(count / 3, 1.0)}
                )

        # Determine thresholds
        if complexity_scores:
            avg_disliked_complexity = sum(complexity_scores) / len(complexity_scores)
            patterns["complexity_threshold"] = int(avg_disliked_complexity * 0.8)

        if cook_times:
            avg_disliked_time = sum(cook_times) / len(cook_times)
            patterns["time_threshold"] = int(avg_disliked_time * 1.2)

        return patterns

    async def _get_user_history(
        self, user_id: int, days: int = 30, actions: Optional[list[str]] = None
    ) -> list[dict]:
        """Get user's interaction history"""
        query = """
            SELECT
                uri.*,
                ur.recipe_data,
                ur.recipe_title,
                ur.cuisine_type
            FROM user_recipe_interactions uri
            LEFT JOIN user_recipes ur ON uri.recipe_id = ur.id::text
            WHERE uri.user_id = %(user_id)s
            AND uri.timestamp >= %(start_date)s
        """

        params = {"user_id": user_id, "start_date": datetime.now() - timedelta(days=days)}

        if actions:
            query += " AND uri.action IN %(actions)s"
            params["actions"] = tuple(actions)

        query += " ORDER BY uri.timestamp DESC"

        return self.db_service.execute_query(query, params)

    async def _get_negative_interactions(self, user_id: int) -> list[dict]:
        """Get recipes the user disliked or dismissed"""
        return await self._get_user_history(
            user_id, days=90, actions=["dismissed", "rated_negative", "removed"]
        )

    async def _analyze_user_patterns(self, history: list[dict]) -> dict:
        """Analyze user behavior patterns"""
        patterns = {
            "health_score": 0.0,
            "quick_meal_preference": 0.0,
            "cuisine_diversity": 0.0,
            "ingredient_consistency": 0.0,
            "complexity_preference": "medium",
        }

        if not history:
            return patterns

        # Analyze health consciousness
        health_keywords = ["healthy", "low calorie", "nutritious", "fresh", "light"]
        health_count = sum(
            1
            for item in history
            if any(kw in str(item.get("recipe_data", {})).lower() for kw in health_keywords)
        )
        patterns["health_score"] = health_count / len(history)

        # Analyze time preferences
        cook_times = [
            item["recipe_data"].get("time", 45) for item in history if item.get("recipe_data")
        ]
        if cook_times:
            avg_time = sum(cook_times) / len(cook_times)
            patterns["quick_meal_preference"] = 1.0 - min(avg_time / 60, 1.0)

        # Analyze cuisine diversity
        cuisines = [
            item["recipe_data"].get("cuisine_type")
            for item in history
            if item.get("recipe_data", {}).get("cuisine_type")
        ]
        if cuisines:
            unique_cuisines = len(set(cuisines))
            patterns["cuisine_diversity"] = min(unique_cuisines / 5, 1.0)

        # Analyze complexity preference
        instruction_counts = [
            len(item["recipe_data"].get("instructions", []))
            for item in history
            if item.get("recipe_data")
        ]
        if instruction_counts:
            avg_instructions = sum(instruction_counts) / len(instruction_counts)
            if avg_instructions < 5:
                patterns["complexity_preference"] = "simple"
            elif avg_instructions > 8:
                patterns["complexity_preference"] = "complex"

        return patterns

    async def _analyze_ingredient_frequency(self, user_id: int, history: list[dict]) -> Counter:
        """Analyze frequency of ingredients in user's recipes"""
        ingredient_counter = Counter()

        for item in history:
            if item.get("action") in ["cooked", "saved", "rated"] and item.get("recipe_data"):
                ingredients = item["recipe_data"].get("ingredients", [])
                for ingredient in ingredients:
                    normalized = self._normalize_ingredient(ingredient)
                    if normalized:
                        ingredient_counter[normalized] += 1

        return ingredient_counter

    async def _analyze_cuisine_frequency(self, user_id: int, history: list[dict]) -> Counter:
        """Analyze frequency of cuisines in user's recipes"""
        cuisine_counter = Counter()

        for item in history:
            if item.get("action") in ["cooked", "saved", "rated"]:
                cuisine = item.get("cuisine_type")
                if cuisine:
                    cuisine_counter[cuisine] += 1

        return cuisine_counter

    async def _analyze_cooking_time_preference(
        self, user_id: int, history: list[dict]
    ) -> Optional[float]:
        """Analyze average cooking time preference"""
        cook_times = []

        for item in history:
            if item.get("action") == "cooked" and item.get("recipe_data"):
                time = item["recipe_data"].get("time")
                if time:
                    cook_times.append(time)

        return sum(cook_times) / len(cook_times) if cook_times else None

    async def _detect_dietary_patterns(self, history: list[dict]) -> dict[str, float]:
        """Detect dietary patterns from recipe history"""
        patterns = {
            "vegetarian": 0.0,
            "vegan": 0.0,
            "gluten_free": 0.0,
            "dairy_free": 0.0,
            "low_carb": 0.0,
        }

        total_recipes = len([h for h in history if h.get("recipe_data")])
        if total_recipes == 0:
            return patterns

        # Count recipes matching each dietary pattern
        for pattern in patterns:
            matching = sum(
                1
                for item in history
                if item.get("recipe_data", {}).get("dietary_tags")
                and pattern.replace("_", "-") in item["recipe_data"]["dietary_tags"]
            )
            patterns[pattern] = matching / total_recipes

        return patterns

    async def _get_current_preferences(self, user_id: int) -> dict:
        """Get user's current preferences"""
        query = """
            SELECT preferences
            FROM user_preferences
            WHERE user_id = %(user_id)s
        """

        result = self.db_service.execute_query(query, {"user_id": user_id})
        if result and result[0].get("preferences"):
            return result[0]["preferences"]

        return {}

    async def _update_preferences_from_interaction(
        self, user_id: int, recipe_id: str, action: str, metadata: Optional[dict]
    ):
        """Update user preferences based on a significant interaction"""
        # This would implement the actual preference updates
        # For now, it's a placeholder for the learning logic
        pass

    def _normalize_ingredient(self, ingredient: str) -> Optional[str]:
        """Normalize ingredient name for consistency"""
        if not ingredient:
            return None

        # Remove quantities and units
        ingredient_lower = ingredient.lower()

        # Remove common measurements
        import re

        ingredient_clean = re.sub(
            r"\b\d+\.?\d*\s*(cup|tbsp|tsp|oz|lb|g|kg|ml|l)s?\b", "", ingredient_lower
        )

        # Remove common descriptors
        remove_words = [
            "fresh",
            "frozen",
            "canned",
            "dried",
            "chopped",
            "diced",
            "sliced",
            "minced",
            "ground",
        ]

        for word in remove_words:
            ingredient_clean = ingredient_clean.replace(word, "")

        # Clean up whitespace
        ingredient_clean = " ".join(ingredient_clean.split())

        # Extract the main ingredient
        # This is simplified - could be more sophisticated
        if ingredient_clean:
            return ingredient_clean.strip()

        return None

    async def export_user_profile(self, user_id: int) -> dict:
        """
        Export comprehensive user profile for debugging or analysis

        Args:
            user_id: User ID

        Returns:
            Complete user profile
        """
        profile = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "preferences": await self._get_current_preferences(user_id),
            "personalized_weights": await self.get_personalized_weights(user_id),
            "suggested_preferences": await self.suggest_new_preferences(user_id),
            "disliked_patterns": await self.get_disliked_patterns(user_id),
            "interaction_summary": await self._get_interaction_summary(user_id),
        }

        return profile

    async def _get_interaction_summary(self, user_id: int) -> dict:
        """Get summary of user interactions"""
        history = await self._get_user_history(user_id, days=90)

        summary = {
            "total_interactions": len(history),
            "recipes_cooked": len([h for h in history if h["action"] == "cooked"]),
            "recipes_saved": len([h for h in history if h["action"] == "saved"]),
            "recipes_rated": len([h for h in history if h["action"] == "rated"]),
            "most_recent_interaction": history[0]["timestamp"].isoformat() if history else None,
        }

        return summary
