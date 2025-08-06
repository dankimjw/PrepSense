import logging
import os

import asyncpg

from src.tools.preference_score import score

logger = logging.getLogger(__name__)


class UserPreferences:
    name = "user_preferences"

    async def run(self, nutrition_scored_recipes: list[dict], user_id: str = None):
        """
        Input: [{'recipe_id': 123, 'title': 'Chicken Stir Fry', 'nutrition_score': 0.8, 'cuisine': ['Asian']}...]
        Output: Same recipes enriched with user preference scores and rankings
        """
        if not nutrition_scored_recipes:
            return []

        # Get user preferences from database
        user_prefs = await self._get_user_preferences(user_id) if user_id else {}

        # If no user preferences found, use defaults
        if not user_prefs:
            logger.info(f"No preferences found for user {user_id}, using defaults")
            user_prefs = self._get_default_preferences()

        enriched_recipes = []
        for recipe in nutrition_scored_recipes:
            try:
                # Calculate preference score using the existing scoring function
                preference_result = score(recipe, user_prefs)
                pref_score = (
                    preference_result
                    if isinstance(preference_result, (int, float))
                    else preference_result[0]
                )
                explanation = (
                    preference_result[1] if isinstance(preference_result, tuple) else "basic match"
                )

                # Calculate detailed preference breakdown
                pref_breakdown = self._calculate_preference_breakdown(recipe, user_prefs)

                # Calculate combined score (nutrition + preferences)
                nutrition_score = recipe.get("nutrition_score", 0.5)
                combined_score = (nutrition_score * 0.6) + (
                    pref_score * 0.4
                )  # Weight nutrition slightly higher

                enriched_recipe = {
                    **recipe,
                    "preference_score": round(pref_score, 3),
                    "preference_explanation": explanation,
                    "preference_breakdown": pref_breakdown,
                    "combined_score": round(combined_score, 3),
                    "user_preferences_applied": True,
                }

                enriched_recipes.append(enriched_recipe)

            except Exception as e:
                logger.error(f"Error applying preferences to recipe {recipe.get('recipe_id')}: {e}")
                # Include recipe without preference scoring
                enriched_recipes.append(
                    {
                        **recipe,
                        "preference_error": str(e),
                        "preference_score": 0.5,
                        "combined_score": recipe.get("nutrition_score", 0.5),
                    }
                )

        # Sort by combined score (highest first)
        enriched_recipes.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        logger.info(f"Applied user preferences to {len(enriched_recipes)} recipes")
        return enriched_recipes

    async def _get_user_preferences(self, user_id: str) -> dict:
        """Get user preferences from database"""
        if not user_id:
            return {}

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return {}

        try:
            conn = await asyncpg.connect(db_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {}

        try:
            preferences = {}

            # Get basic user preferences
            user_prefs = await conn.fetchrow(
                """
                SELECT calorie_target, max_prep_time, preferred_meal_types, health_goals
                FROM user_preferences 
                WHERE user_id = $1
            """,
                int(user_id),
            )

            if user_prefs:
                preferences.update(
                    {
                        "calorie_target": user_prefs["calorie_target"],
                        "max_prep_time": user_prefs["max_prep_time"],
                        "preferred_meal_types": user_prefs["preferred_meal_types"] or [],
                        "health_goals": user_prefs["health_goals"] or [],
                    }
                )

            # Get dietary restrictions/allergens
            allergens = await conn.fetch(
                """
                SELECT allergen_name FROM user_allergens WHERE user_id = $1
            """,
                int(user_id),
            )
            preferences["allergens"] = [row["allergen_name"] for row in allergens]

            # Get cuisine preferences
            cuisines = await conn.fetch(
                """
                SELECT cuisine_name FROM user_cuisine_preferences WHERE user_id = $1
            """,
                int(user_id),
            )
            preferences["cuisines"] = [row["cuisine_name"] for row in cuisines]

            # Get dietary preferences (vegetarian, vegan, etc.)
            dietary_prefs = await conn.fetch(
                """
                SELECT preference_type FROM user_dietary_preferences WHERE user_id = $1
            """,
                int(user_id),
            )
            preferences["dietary_restrictions"] = [row["preference_type"] for row in dietary_prefs]

            # Get ingredient preferences from interaction history
            ingredient_prefs = await conn.fetch(
                """
                SELECT ingredient_name, preference_score
                FROM user_ingredient_preferences 
                WHERE user_id = $1 AND preference_score != 0
                ORDER BY preference_score DESC
                LIMIT 50
            """,
                int(user_id),
            )

            preferences["liked_ingredients"] = [
                row["ingredient_name"] for row in ingredient_prefs if row["preference_score"] > 0
            ]
            preferences["disliked_ingredients"] = [
                row["ingredient_name"] for row in ingredient_prefs if row["preference_score"] < 0
            ]

            logger.info(f"Loaded preferences for user {user_id}: {len(preferences)} categories")
            return preferences

        except Exception as e:
            logger.error(f"Error fetching user preferences: {e}")
            return {}
        finally:
            await conn.close()

    def _get_default_preferences(self) -> dict:
        """Get sensible default preferences"""
        return {
            "calorie_target": 600,  # Per meal
            "max_prep_time": 45,  # Minutes
            "cuisines": [],  # No cuisine preference
            "allergens": [],  # No known allergens
            "dietary_restrictions": [],  # No dietary restrictions
            "preferred_meal_types": ["dinner", "lunch"],
            "health_goals": ["balanced"],
            "liked_ingredients": [],
            "disliked_ingredients": [],
        }

    def _calculate_preference_breakdown(self, recipe: dict, user_prefs: dict) -> dict:
        """Calculate detailed breakdown of preference scoring"""
        breakdown = {
            "cuisine_match": 0,
            "dietary_compliance": 0,
            "allergen_safety": 1,  # Start with safe assumption
            "prep_time_fit": 0,
            "calorie_target_fit": 0,
            "ingredient_preference": 0.5,  # Neutral if no ingredient prefs
        }

        # Cuisine matching
        recipe_cuisines = recipe.get("cuisine", [])
        user_cuisines = user_prefs.get("cuisines", [])
        if user_cuisines and recipe_cuisines:
            if any(
                cuisine.lower() in [uc.lower() for uc in user_cuisines]
                for cuisine in recipe_cuisines
            ):
                breakdown["cuisine_match"] = 1.0
        elif not user_cuisines:  # No preference = neutral
            breakdown["cuisine_match"] = 0.5

        # Dietary compliance
        recipe_diets = recipe.get("diet_tags", [])
        user_restrictions = user_prefs.get("dietary_restrictions", [])
        if user_restrictions:
            compliance_count = 0
            for restriction in user_restrictions:
                if restriction.lower() in [diet.lower() for diet in recipe_diets]:
                    compliance_count += 1
            breakdown["dietary_compliance"] = compliance_count / len(user_restrictions)
        else:
            breakdown["dietary_compliance"] = 0.5  # No restrictions = neutral

        # Allergen safety
        recipe_ingredients = [ing.get("name", "").lower() for ing in recipe.get("ingredients", [])]
        user_allergens = [allergen.lower() for allergen in user_prefs.get("allergens", [])]

        for allergen in user_allergens:
            if any(allergen in ingredient for ingredient in recipe_ingredients):
                breakdown["allergen_safety"] = 0  # Recipe contains allergen
                break

        # Prep time fit
        recipe_time = recipe.get("ready_in_minutes", 0)
        max_time = user_prefs.get("max_prep_time", 60)
        if recipe_time <= max_time:
            breakdown["prep_time_fit"] = 1.0 - (recipe_time / max_time) * 0.3  # Bonus for faster
        else:
            breakdown["prep_time_fit"] = max(0, 1.0 - (recipe_time - max_time) / max_time)

        # Calorie target fit
        recipe_calories = recipe.get("nutrition", {}).get("calories", 0)
        target_calories = user_prefs.get("calorie_target", 600)
        if recipe_calories > 0:
            calorie_diff = abs(recipe_calories - target_calories)
            breakdown["calorie_target_fit"] = max(0, 1.0 - calorie_diff / target_calories)
        else:
            breakdown["calorie_target_fit"] = 0.5

        # Ingredient preferences
        liked_ingredients = user_prefs.get("liked_ingredients", [])
        disliked_ingredients = user_prefs.get("disliked_ingredients", [])

        if liked_ingredients or disliked_ingredients:
            ingredient_score = 0.5  # Start neutral
            ingredient_matches = 0
            total_ingredients = len(recipe_ingredients)

            for ingredient in recipe_ingredients:
                if any(liked in ingredient for liked in liked_ingredients):
                    ingredient_matches += 1
                elif any(disliked in ingredient for disliked in disliked_ingredients):
                    ingredient_matches -= 1

            if total_ingredients > 0:
                ingredient_score = 0.5 + (ingredient_matches / total_ingredients) * 0.5
                breakdown["ingredient_preference"] = max(0, min(1, ingredient_score))

        return breakdown
