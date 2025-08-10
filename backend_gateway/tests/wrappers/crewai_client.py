"""
CrewAI Client Wrapper for Testing

This wrapper provides a clean interface for testing the RecipeAdvisor (CrewAI) service
without direct dependencies on the actual implementation.
"""

import random
from datetime import datetime
from typing import Any, Optional


class MockCrewAIClient:
    """Mock implementation of CrewAI recipe advisor for testing"""

    def __init__(self):
        self.advisor_role = "Intelligent Recipe Advisor"
        self.advisor_goal = (
            "Recommend the best recipes based on pantry items, preferences, and context"
        )

    def analyze_pantry(self, pantry_items: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze pantry for insights like expiring items, common ingredients, etc.

        Args:
            pantry_items: List of pantry items with product_name, expiration_date, category

        Returns:
            Analysis dict with total_items, expiring_soon, expired, categories, etc.
        """
        today = datetime.now().date()

        analysis = {
            "total_items": len(pantry_items),
            "expiring_soon": [],
            "expired": [],
            "categories": {},
            "protein_sources": [],
            "staples": [],
        }

        for item in pantry_items:
            # Check expiration
            if item.get("expiration_date"):
                exp_date = datetime.strptime(str(item["expiration_date"]), "%Y-%m-%d").date()
                days_until = (exp_date - today).days

                if days_until < 0:
                    analysis["expired"].append(item)
                elif days_until <= 7:
                    analysis["expiring_soon"].append(
                        {
                            "name": item["product_name"],
                            "days": days_until,
                            "date": exp_date.isoformat(),
                        }
                    )

            # Categorize items
            product_name = item.get("product_name", "").lower()
            category = item.get("category", "other")

            if category not in analysis["categories"]:
                analysis["categories"][category] = []
            analysis["categories"][category].append(product_name)

            # Identify proteins
            if any(
                protein in product_name
                for protein in ["chicken", "beef", "pork", "fish", "tofu", "beans", "eggs"]
            ):
                analysis["protein_sources"].append(product_name)

            # Identify staples
            if any(
                staple in product_name for staple in ["rice", "pasta", "bread", "potato", "flour"]
            ):
                analysis["staples"].append(product_name)

        return analysis

    def evaluate_recipe_fit(
        self,
        recipe: dict[str, Any],
        user_preferences: dict[str, Any],
        pantry_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate how well a recipe fits the user's needs

        Args:
            recipe: Recipe dict with ingredients, instructions
            user_preferences: User dietary preferences, allergens, cuisine preferences
            pantry_analysis: Results from analyze_pantry

        Returns:
            Evaluation dict with uses_expiring, nutritional_balance, cooking_complexity
        """
        evaluation = {
            "uses_expiring": False,
            "nutritional_balance": "unknown",
            "meal_variety": "standard",
            "cooking_complexity": "medium",
        }

        # Check if recipe uses expiring ingredients
        recipe_ingredients = " ".join(recipe.get("ingredients", [])).lower()
        for expiring in pantry_analysis.get("expiring_soon", []):
            if expiring["name"].lower() in recipe_ingredients:
                evaluation["uses_expiring"] = True
                break

        # Evaluate nutritional balance
        protein_sources = pantry_analysis.get("protein_sources", [])
        if any(protein in recipe_ingredients for protein in protein_sources):
            if any(
                veg in recipe_ingredients
                for veg in ["vegetable", "salad", "broccoli", "carrot", "spinach"]
            ):
                evaluation["nutritional_balance"] = "good"
            else:
                evaluation["nutritional_balance"] = "fair"

        # Estimate cooking complexity
        instructions = recipe.get("instructions", [])
        if len(instructions) <= 4:
            evaluation["cooking_complexity"] = "easy"
        elif len(instructions) > 8:
            evaluation["cooking_complexity"] = "complex"

        return evaluation

    def generate_advice(
        self, recipes: list[dict[str, Any]], pantry_analysis: dict[str, Any], message: str
    ) -> str:
        """
        Generate contextual advice about the recipes

        Args:
            recipes: List of recommended recipes
            pantry_analysis: Results from analyze_pantry
            message: User's original message

        Returns:
            Advice string with contextual recommendations
        """
        advice_parts = []

        # Expiring items advice
        expiring_count = len(pantry_analysis.get("expiring_soon", []))
        if expiring_count > 0 and "expir" in message.lower():
            advice_parts.append(
                f"I found {expiring_count} items expiring soon and prioritized recipes using them."
            )

        # Variety advice
        cuisines = {r.get("cuisine_type", "various") for r in recipes[:3]}
        if len(cuisines) >= 3:
            advice_parts.append("I've included diverse cuisine options for variety.")

        # Quick meal advice
        quick_recipes = [r for r in recipes if r.get("time", 999) <= 20]
        if quick_recipes and any(word in message.lower() for word in ["quick", "fast", "easy"]):
            advice_parts.append(f"I found {len(quick_recipes)} quick recipes (20 min or less).")

        return (
            " ".join(advice_parts)
            if advice_parts
            else "Here are some recipe recommendations based on your pantry items."
        )

    def process_message(
        self,
        user_id: int,
        message: str,
        pantry_items: list[dict[str, Any]],
        user_preferences: Optional[dict[str, Any]] = None,
        available_recipes: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Process a chat message and return recipe recommendations

        Args:
            user_id: User ID
            message: User's message
            pantry_items: List of pantry items
            user_preferences: Optional user preferences
            available_recipes: Optional list of recipes to choose from

        Returns:
            Dict with response, recipes, pantry_items, analysis
        """
        # Analyze pantry
        pantry_analysis = self.analyze_pantry(pantry_items)

        # Generate mock recipes if none provided
        if not available_recipes:
            available_recipes = self._generate_mock_recipes(pantry_items)

        # Evaluate recipes
        evaluated_recipes = []
        for recipe in available_recipes:
            evaluation = self.evaluate_recipe_fit(recipe, user_preferences or {}, pantry_analysis)
            recipe_with_eval = recipe.copy()
            recipe_with_eval["evaluation"] = evaluation
            evaluated_recipes.append(recipe_with_eval)

        # Sort by evaluation (prioritize expiring ingredients)
        evaluated_recipes.sort(
            key=lambda r: (
                r["evaluation"]["uses_expiring"],
                r["evaluation"]["nutritional_balance"] == "good",
            ),
            reverse=True,
        )

        # Generate advice
        advice = self.generate_advice(evaluated_recipes[:5], pantry_analysis, message)

        return {
            "response": advice,
            "recipes": evaluated_recipes[:5],
            "pantry_items": pantry_items,
            "pantry_analysis": pantry_analysis,
            "user_preferences": user_preferences,
        }

    def _generate_mock_recipes(self, pantry_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate mock recipes based on pantry items"""
        recipes = []

        # Extract ingredient names
        ingredient_names = [item["product_name"] for item in pantry_items[:10]]

        # Generate 5 mock recipes
        for i in range(5):
            # Pick 3-5 random ingredients
            num_ingredients = random.randint(3, min(5, len(ingredient_names)))
            recipe_ingredients = random.sample(ingredient_names, num_ingredients)

            recipe = {
                "id": f"mock-recipe-{i+1}",
                "title": f"Recipe with {recipe_ingredients[0].title()}",
                "ingredients": recipe_ingredients,
                "instructions": [f"Step {j+1}" for j in range(random.randint(3, 8))],
                "time": random.choice([15, 20, 25, 30, 45, 60]),
                "cuisine_type": random.choice(
                    ["italian", "asian", "mexican", "american", "mediterranean"]
                ),
                "servings": random.choice([2, 4, 6]),
                "difficulty": random.choice(["easy", "medium", "hard"]),
            }
            recipes.append(recipe)

        return recipes


class CrewAIClientWrapper:
    """Wrapper for the actual CrewAI service"""

    def __init__(self, crew_ai_service=None):
        """
        Initialize wrapper with optional real service

        Args:
            crew_ai_service: Real CrewAI service instance or None for mock
        """
        self._service = crew_ai_service
        self._mock = MockCrewAIClient()

    def analyze_pantry(self, pantry_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze pantry items"""
        if self._service and hasattr(self._service.recipe_advisor, "analyze_pantry"):
            return self._service.recipe_advisor.analyze_pantry(pantry_items)
        return self._mock.analyze_pantry(pantry_items)

    def evaluate_recipe_fit(
        self,
        recipe: dict[str, Any],
        user_preferences: dict[str, Any],
        pantry_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate recipe fit"""
        if self._service and hasattr(self._service.recipe_advisor, "evaluate_recipe_fit"):
            return self._service.recipe_advisor.evaluate_recipe_fit(
                recipe, user_preferences, pantry_analysis
            )
        return self._mock.evaluate_recipe_fit(recipe, user_preferences, pantry_analysis)

    def generate_advice(
        self, recipes: list[dict[str, Any]], pantry_analysis: dict[str, Any], message: str
    ) -> str:
        """Generate advice"""
        if self._service and hasattr(self._service.recipe_advisor, "generate_advice"):
            return self._service.recipe_advisor.generate_advice(recipes, pantry_analysis, message)
        return self._mock.generate_advice(recipes, pantry_analysis, message)

    async def process_message(
        self, user_id: int, message: str, use_preferences: bool = True
    ) -> dict[str, Any]:
        """Process message through real service"""
        if self._service and hasattr(self._service, "process_message"):
            return await self._service.process_message(user_id, message, use_preferences)

        # Mock implementation
        pantry_items = [
            {"product_name": "Chicken Breast", "category": "meat", "expiration_date": "2024-01-25"},
            {"product_name": "Rice", "category": "grain", "expiration_date": "2024-06-01"},
            {"product_name": "Broccoli", "category": "vegetable", "expiration_date": "2024-01-22"},
        ]

        user_preferences = (
            {"dietary_preference": [], "allergens": [], "cuisine_preference": []}
            if use_preferences
            else None
        )

        return self._mock.process_message(user_id, message, pantry_items, user_preferences)


def get_crewai_client(service=None) -> CrewAIClientWrapper:
    """Factory function to get CrewAI client"""
    return CrewAIClientWrapper(service)
