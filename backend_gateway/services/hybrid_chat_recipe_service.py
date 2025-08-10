"""Hybrid Chat Recipe Service
Integrates enhanced OpenAI recipe generation with existing chat functionality.
Ensures consistent rich data structure between demo recipes, mock recipes, and OpenAI recipes.
"""

import logging
from enum import Enum
from typing import Any, Optional

from backend_gateway.fixtures.mock_recipes import (
    get_enhanced_mock_recipes,
    get_mock_recipes_for_ingredients,
)
from backend_gateway.RemoteControl_7 import is_chat_recipes_mock_enabled
from backend_gateway.services.enhanced_openai_recipe_service import EnhancedOpenAIRecipeService

logger = logging.getLogger(__name__)


class RecipeSource(Enum):
    """Enum for recipe sources"""

    OPENAI_ENHANCED = "openai_enhanced"
    MOCK_ENHANCED = "mock_enhanced"
    SPOONACULAR = "spoonacular"
    DATABASE = "database"
    FALLBACK = "fallback"


class HybridChatRecipeService:
    """Service that provides unified recipe generation across multiple sources"""

    def __init__(self):
        """Initialize the hybrid service with all recipe sources"""
        self.openai_service = EnhancedOpenAIRecipeService()
        self._recipe_cache = {}

    def generate_recipes_for_chat(
        self,
        user_message: str,
        available_ingredients: list[str],
        user_preferences: Optional[dict[str, Any]] = None,
        max_recipes: int = 3,
        preferred_source: Optional[RecipeSource] = None,
    ) -> list[dict[str, Any]]:
        """
        Generate recipes for chat interface with consistent rich data structure.

        Args:
            user_message: User's chat message requesting recipes
            available_ingredients: List of ingredients available to user
            user_preferences: User dietary preferences and allergens
            max_recipes: Maximum number of recipes to generate
            preferred_source: Preferred recipe source (optional)

        Returns:
            List of rich recipe objects with Spoonacular-compatible structure
        """
        try:
            # Check if mock mode is enabled
            if is_chat_recipes_mock_enabled():
                logger.info("Mock mode enabled, using enhanced mock recipes")
                return self._get_mock_recipes(available_ingredients, max_recipes)

            # Extract recipe preferences from user message
            recipe_context = self._parse_user_message(user_message)

            # Merge user preferences
            preferences = self._merge_preferences(user_preferences, recipe_context)

            # Determine the best recipe source
            source = preferred_source or self._determine_best_source(
                available_ingredients, preferences
            )

            # Generate recipes based on source
            if source == RecipeSource.OPENAI_ENHANCED:
                return self._generate_openai_recipes(
                    recipe_context, available_ingredients, preferences, max_recipes
                )
            elif source == RecipeSource.MOCK_ENHANCED:
                return self._get_mock_recipes(available_ingredients, max_recipes)
            else:
                # Fallback to mock recipes
                logger.warning(f"Unsupported source {source}, falling back to mock recipes")
                return self._get_mock_recipes(available_ingredients, max_recipes)

        except Exception as e:
            logger.error(f"Error generating recipes for chat: {str(e)}")
            return self._get_fallback_recipes(available_ingredients, max_recipes)

    def generate_single_recipe(
        self,
        recipe_name: str,
        available_ingredients: list[str],
        user_preferences: Optional[dict[str, Any]] = None,
        source: Optional[RecipeSource] = None,
    ) -> dict[str, Any]:
        """
        Generate a single recipe with rich data structure.

        Args:
            recipe_name: Name of the recipe to generate
            available_ingredients: Available ingredients
            user_preferences: User preferences and restrictions
            source: Recipe source to use

        Returns:
            Rich recipe object with Spoonacular-compatible structure
        """
        try:
            # Check mock mode first
            if is_chat_recipes_mock_enabled():
                mock_recipes = self._get_mock_recipes(available_ingredients, 1)
                if mock_recipes:
                    return mock_recipes[0]

            # Use OpenAI enhanced service
            if source != RecipeSource.MOCK_ENHANCED:
                dietary_restrictions = (
                    user_preferences.get("dietary_preferences", []) if user_preferences else []
                )
                allergens = user_preferences.get("allergens", []) if user_preferences else []

                recipe = self.openai_service.generate_enhanced_recipe(
                    recipe_name=recipe_name,
                    available_ingredients=available_ingredients,
                    dietary_restrictions=dietary_restrictions,
                    allergens=allergens,
                )

                if recipe and recipe.get("id"):
                    return recipe

            # Fallback to mock recipes
            mock_recipes = self._get_mock_recipes(available_ingredients, 1)
            return mock_recipes[0] if mock_recipes else self._create_emergency_fallback(recipe_name)

        except Exception as e:
            logger.error(f"Error generating single recipe: {str(e)}")
            return self._create_emergency_fallback(recipe_name)

    def get_recipe_suggestions(
        self,
        available_ingredients: list[str],
        user_preferences: Optional[dict[str, Any]] = None,
        cuisine_types: Optional[list[str]] = None,
        max_suggestions: int = 5,
    ) -> list[str]:
        """
        Get recipe name suggestions based on available ingredients.

        Returns:
            List of recipe name suggestions
        """
        suggestions = []

        try:
            # Check mock mode
            if is_chat_recipes_mock_enabled():
                mock_recipes = get_mock_recipes_for_ingredients(
                    available_ingredients, max_suggestions
                )
                return [recipe["title"] for recipe in mock_recipes]

            # Generate suggestions based on ingredients
            ingredient_groups = self._group_ingredients(available_ingredients)

            # Create suggestions based on ingredient combinations
            if "protein" in ingredient_groups:
                for protein in ingredient_groups["protein"][:2]:
                    if "vegetables" in ingredient_groups:
                        for veg in ingredient_groups["vegetables"][:2]:
                            suggestions.append(f"{protein.title()} and {veg.title()} Stir Fry")
                            suggestions.append(f"Roasted {protein.title()} with {veg.title()}")

            if "pasta" in ingredient_groups.get("grains", []):
                suggestions.append("Classic Pasta Primavera")
                suggestions.append("Creamy Pasta Alfredo")

            if "rice" in ingredient_groups.get("grains", []):
                suggestions.append("Fried Rice Special")
                suggestions.append("Rice Bowl with Vegetables")

            # Add cuisine-specific suggestions
            if cuisine_types:
                for cuisine in cuisine_types:
                    if cuisine.lower() == "italian":
                        suggestions.extend(["Spaghetti Carbonara", "Chicken Parmesan"])
                    elif cuisine.lower() == "asian":
                        suggestions.extend(["Teriyaki Chicken", "Vegetable Lo Mein"])
                    elif cuisine.lower() == "mexican":
                        suggestions.extend(["Chicken Quesadillas", "Bean and Rice Burrito"])

            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Error getting recipe suggestions: {str(e)}")
            return [
                "Quick Stir Fry",
                "Simple Pasta Dish",
                "Roasted Vegetables",
                "Rice Bowl",
                "Soup with Available Ingredients",
            ][:max_suggestions]

    def validate_recipe_compatibility(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """
        Validate that a recipe has the required structure for frontend compatibility.

        Args:
            recipe: Recipe object to validate

        Returns:
            Validation result with compatibility status
        """
        try:
            validation = self.openai_service.validate_recipe_structure(recipe)

            # Additional checks for frontend compatibility
            frontend_compatibility = {
                "has_spoonacular_format": all(
                    field in recipe
                    for field in ["id", "title", "extendedIngredients", "analyzedInstructions"]
                ),
                "has_chat_format": all(
                    field in recipe for field in ["name", "ingredients", "instructions"]
                ),
                "has_nutrition_data": "nutrition" in recipe
                and "nutrients" in recipe.get("nutrition", {}),
                "has_caloric_breakdown": "nutrition" in recipe
                and "caloricBreakdown" in recipe.get("nutrition", {}),
                "has_safety_data": "safety_status" in recipe,
            }

            overall_compatibility = all(frontend_compatibility.values())

            return {
                "structure_valid": validation["valid"],
                "structure_issues": validation["issues"],
                "structure_score": validation["score"],
                "frontend_compatible": overall_compatibility,
                "compatibility_details": frontend_compatibility,
                "recommendation": (
                    "Ready for frontend" if overall_compatibility else "Needs enhancement"
                ),
            }

        except Exception as e:
            return {
                "structure_valid": False,
                "error": str(e),
                "frontend_compatible": False,
                "recommendation": "Recipe validation failed",
            }

    def enhance_existing_recipe(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """
        Enhance an existing recipe to have full Spoonacular compatibility.

        Args:
            recipe: Existing recipe object (potentially incomplete)

        Returns:
            Enhanced recipe with full structure
        """
        try:
            enhanced_recipe = recipe.copy()

            # Ensure required IDs
            if "id" not in enhanced_recipe:
                enhanced_recipe["id"] = self.openai_service.recipe_id_counter
                self.openai_service.recipe_id_counter += 1

            # Ensure dual naming for compatibility
            if "title" in enhanced_recipe and "name" not in enhanced_recipe:
                enhanced_recipe["name"] = enhanced_recipe["title"]
            elif "name" in enhanced_recipe and "title" not in enhanced_recipe:
                enhanced_recipe["title"] = enhanced_recipe["name"]

            # Enhance ingredients if needed
            if "extendedIngredients" not in enhanced_recipe and "ingredients" in enhanced_recipe:
                enhanced_recipe["extendedIngredients"] = self._convert_simple_ingredients(
                    enhanced_recipe["ingredients"]
                )

            # Enhance instructions if needed
            if "analyzedInstructions" not in enhanced_recipe and "instructions" in enhanced_recipe:
                enhanced_recipe["analyzedInstructions"] = self._convert_simple_instructions(
                    enhanced_recipe["instructions"]
                )

            # Ensure nutrition data exists
            if "nutrition" not in enhanced_recipe:
                enhanced_recipe["nutrition"] = self.openai_service._create_default_nutrition()

            # Ensure safety data exists
            for safety_field in [
                "safety_status",
                "safety_violations",
                "safety_warnings",
                "allergen_risks",
            ]:
                if safety_field not in enhanced_recipe:
                    enhanced_recipe[safety_field] = (
                        []
                        if "violations" in safety_field
                        or "warnings" in safety_field
                        or "risks" in safety_field
                        else "SAFE"
                    )

            # Ensure metadata exists
            for field, default in [
                ("cuisines", ["American"]),
                ("dishTypes", ["main course"]),
                ("diets", []),
                ("occasions", ["casual"]),
                ("readyInMinutes", 30),
                ("servings", 4),
                ("source", "hybrid_enhanced"),
            ]:
                enhanced_recipe.setdefault(field, default)

            return enhanced_recipe

        except Exception as e:
            logger.error(f"Error enhancing recipe: {str(e)}")
            return recipe  # Return original if enhancement fails

    # Private helper methods

    def _get_mock_recipes(
        self, available_ingredients: list[str], max_recipes: int
    ) -> list[dict[str, Any]]:
        """Get enhanced mock recipes"""
        try:
            if available_ingredients:
                recipes = get_mock_recipes_for_ingredients(available_ingredients, max_recipes)
            else:
                recipes = get_enhanced_mock_recipes()[:max_recipes]

            # Ensure all recipes have the required structure
            return [self.enhance_existing_recipe(recipe) for recipe in recipes]

        except Exception as e:
            logger.error(f"Error getting mock recipes: {str(e)}")
            return self._get_fallback_recipes(available_ingredients, max_recipes)

    def _generate_openai_recipes(
        self,
        recipe_context: dict[str, Any],
        available_ingredients: list[str],
        preferences: dict[str, Any],
        max_recipes: int,
    ) -> list[dict[str, Any]]:
        """Generate recipes using OpenAI enhanced service"""
        try:
            recipes = []

            # Generate multiple recipe variations
            recipe_names = recipe_context.get("suggested_names", ["Delicious Recipe"])

            for _i, recipe_name in enumerate(recipe_names[:max_recipes]):
                recipe = self.openai_service.generate_enhanced_recipe(
                    recipe_name=recipe_name,
                    available_ingredients=available_ingredients,
                    dietary_restrictions=preferences.get("dietary_preferences", []),
                    allergens=preferences.get("allergens", []),
                    cuisine_type=recipe_context.get("cuisine_type"),
                    cooking_time=recipe_context.get("cooking_time"),
                    servings=recipe_context.get("servings", 4),
                )

                if recipe and recipe.get("id"):
                    recipes.append(recipe)

                # Stop if we have enough recipes
                if len(recipes) >= max_recipes:
                    break

            # Fill remaining slots with mock recipes if needed
            if len(recipes) < max_recipes:
                remaining_needed = max_recipes - len(recipes)
                mock_recipes = self._get_mock_recipes(available_ingredients, remaining_needed)
                recipes.extend(mock_recipes)

            return recipes[:max_recipes]

        except Exception as e:
            logger.error(f"Error generating OpenAI recipes: {str(e)}")
            return self._get_mock_recipes(available_ingredients, max_recipes)

    def _parse_user_message(self, message: str) -> dict[str, Any]:
        """Parse user message to extract recipe context"""
        message_lower = message.lower()

        context = {
            "suggested_names": [],
            "cuisine_type": None,
            "cooking_time": None,
            "meal_type": "dinner",
            "servings": 4,
        }

        # Extract cuisine preferences
        if "italian" in message_lower:
            context["cuisine_type"] = "Italian"
            context["suggested_names"].append("Italian Pasta Dish")
        elif "asian" in message_lower or "chinese" in message_lower:
            context["cuisine_type"] = "Asian"
            context["suggested_names"].append("Asian Stir Fry")
        elif "mexican" in message_lower:
            context["cuisine_type"] = "Mexican"
            context["suggested_names"].append("Mexican Bowl")
        elif "mediterranean" in message_lower:
            context["cuisine_type"] = "Mediterranean"
            context["suggested_names"].append("Mediterranean Bowl")

        # Extract time preferences
        if "quick" in message_lower or "fast" in message_lower:
            context["cooking_time"] = 20
            context["suggested_names"].append("Quick Meal")
        elif "slow" in message_lower:
            context["cooking_time"] = 90

        # Extract meal type
        if "breakfast" in message_lower:
            context["meal_type"] = "breakfast"
            context["suggested_names"].append("Breakfast Special")
        elif "lunch" in message_lower:
            context["meal_type"] = "lunch"
            context["suggested_names"].append("Lunch Bowl")
        elif "dinner" in message_lower:
            context["meal_type"] = "dinner"
            context["suggested_names"].append("Dinner Delight")

        # Default suggestions if none found
        if not context["suggested_names"]:
            context["suggested_names"] = ["Delicious Recipe", "Pantry Special", "Simple Meal"]

        return context

    def _merge_preferences(
        self, user_preferences: Optional[dict[str, Any]], recipe_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge user preferences with recipe context"""
        merged = {"dietary_preferences": [], "allergens": [], "cuisine_preferences": []}

        if user_preferences:
            merged["dietary_preferences"] = user_preferences.get("dietary_preferences", [])
            merged["allergens"] = user_preferences.get("allergens", [])

        if recipe_context.get("cuisine_type"):
            merged["cuisine_preferences"].append(recipe_context["cuisine_type"])

        return merged

    def _determine_best_source(
        self, available_ingredients: list[str], preferences: dict[str, Any]
    ) -> RecipeSource:
        """Determine the best recipe source based on context"""
        # For now, prefer OpenAI enhanced unless in mock mode
        if is_chat_recipes_mock_enabled():
            return RecipeSource.MOCK_ENHANCED

        # Use OpenAI if we have enough ingredients and preferences
        if len(available_ingredients) >= 3 or preferences.get("dietary_preferences"):
            return RecipeSource.OPENAI_ENHANCED

        return RecipeSource.MOCK_ENHANCED

    def _group_ingredients(self, ingredients: list[str]) -> dict[str, list[str]]:
        """Group ingredients by category"""
        groups = {"protein": [], "vegetables": [], "grains": [], "dairy": [], "spices": []}

        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()

            if any(
                protein in ingredient_lower
                for protein in ["chicken", "beef", "pork", "fish", "tofu", "eggs"]
            ):
                groups["protein"].append(ingredient)
            elif any(
                veg in ingredient_lower
                for veg in ["tomato", "onion", "carrot", "pepper", "broccoli", "spinach"]
            ):
                groups["vegetables"].append(ingredient)
            elif any(
                grain in ingredient_lower for grain in ["rice", "pasta", "bread", "flour", "quinoa"]
            ):
                groups["grains"].append(ingredient)
            elif any(dairy in ingredient_lower for dairy in ["milk", "cheese", "butter", "yogurt"]):
                groups["dairy"].append(ingredient)
            elif any(
                spice in ingredient_lower
                for spice in ["salt", "pepper", "garlic", "oregano", "basil"]
            ):
                groups["spices"].append(ingredient)

        return groups

    def _get_fallback_recipes(
        self, available_ingredients: list[str], max_recipes: int
    ) -> list[dict[str, Any]]:
        """Get fallback recipes when all else fails"""
        try:
            # Try to get mock recipes first
            return self._get_mock_recipes(available_ingredients, max_recipes)
        except Exception:
            # Emergency fallback
            return [self._create_emergency_fallback("Emergency Recipe") for _ in range(max_recipes)]

    def _create_emergency_fallback(self, recipe_name: str) -> dict[str, Any]:
        """Create an emergency fallback recipe"""
        return {
            "id": 9999,
            "title": recipe_name,
            "name": recipe_name,
            "summary": f"A simple {recipe_name.lower()} with available ingredients",
            "readyInMinutes": 30,
            "time": 30,
            "servings": 4,
            "cuisines": ["American"],
            "dishTypes": ["main course"],
            "diets": [],
            "occasions": ["casual"],
            "extendedIngredients": [],
            "analyzedInstructions": [
                {"steps": [{"number": 1, "step": "Combine ingredients and cook as desired."}]}
            ],
            "nutrition": self.openai_service._create_default_nutrition(),
            "ingredients": ["Available ingredients"],
            "instructions": ["Combine ingredients and cook as desired."],
            "available_ingredients": [],
            "missing_ingredients": [],
            "available_count": 0,
            "missing_count": 0,
            "match_score": 0.0,
            "safety_status": "SAFE",
            "safety_violations": [],
            "safety_warnings": [],
            "allergen_risks": [],
            "source": "emergency_fallback",
        }

    def _convert_simple_ingredients(self, ingredients: list[str]) -> list[dict[str, Any]]:
        """Convert simple ingredient strings to extended ingredient format"""
        extended_ingredients = []

        for i, ingredient in enumerate(ingredients):
            extended_ingredients.append(
                {
                    "id": i + 1,
                    "name": ingredient.split()[0] if ingredient else "ingredient",
                    "original": ingredient,
                    "amount": 1.0,
                    "unit": "item",
                    "aisle": "Unknown",
                    "meta": [],
                    "measures": {
                        "us": {"amount": 1.0, "unitShort": "item", "unitLong": "item"},
                        "metric": {"amount": 1.0, "unitShort": "item", "unitLong": "item"},
                    },
                }
            )

        return extended_ingredients

    def _convert_simple_instructions(self, instructions: list[str]) -> list[dict[str, Any]]:
        """Convert simple instruction strings to analyzed instruction format"""
        return [
            {
                "steps": [
                    {
                        "number": i + 1,
                        "step": instruction,
                        "ingredients": [],
                        "equipment": [],
                        "length": {"number": 5, "unit": "minutes"},
                    }
                    for i, instruction in enumerate(instructions)
                ]
            }
        ]


# Export the service
__all__ = ["HybridChatRecipeService", "RecipeSource"]
