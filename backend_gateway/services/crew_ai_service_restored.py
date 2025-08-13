import json
import logging
from datetime import datetime
from typing import Any

import openai

from backend_gateway.config.database import get_database_service
from backend_gateway.services.openai_recipe_service import OpenAIRecipeService
from backend_gateway.services.recipe_preference_scorer import RecipePreferenceScorer
from backend_gateway.services.recipe_service import RecipeService
from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.services.user_recipes_service import UserRecipesService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RecipeAdvisor:
    """Single agent that combines recipe recommendation logic"""

    def __init__(self):
        self.role = "Intelligent Recipe Advisor"
        self.goal = "Recommend the best recipes based on pantry items, preferences, and context"

    def analyze_pantry(self, pantry_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze pantry for insights like expiring items, common ingredients, etc."""
        from datetime import datetime

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
                        {"name": item["product_name"], "days": days_until, "date": exp_date}
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

            # Identify vegetables
            if any(
                vegetable in product_name
                for vegetable in [
                    "carrot",
                    "broccoli",
                    "spinach",
                    "tomato",
                    "cucumber",
                    "bell pepper",
                ]
            ):
                analysis["vegetables"].append(product_name)

            # Identify carbs
            if any(
                carb in product_name
                for carb in ["pasta", "rice", "bread", "potato", "flour", "cereals"]
            ):
                analysis["carbs"].append(product_name)

        return analysis

    def evaluate_recipe_fit(
        self,
        recipe: dict[str, Any],
        user_preferences: dict[str, Any],
        pantry_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evaluate how well a recipe fits the user's needs.
        
        Args:
            recipe (dict[str, Any]): Recipe object with structure:
                {
                    "ingredients": list[str] or list[dict],  # Can be strings or dicts
                    "readyInMinutes": int,
                    "name" or "title": str,
                    "cuisines": list[str],
                    "diets": list[str]
                }
                If ingredients are dicts, they should have "name" field:
                [{"name": "chicken", "amount": 1, "unit": "lb"}, ...]
                
            user_preferences (dict[str, Any]): User preferences with:
                {
                    "dietary_preference": list[str],  # e.g., ["vegetarian"]
                    "allergens": list[str],          # e.g., ["peanuts"]
                    "cuisine_preference": list[str]  # e.g., ["italian"]
                }
                
            pantry_analysis (dict[str, Any]): Pantry analysis with:
                {
                    "expiring_soon": list[dict],     # Items expiring soon
                    "protein_sources": list[str],    # Available proteins
                    "vegetables": list[str],         # Available vegetables
                    "carbs": list[str]              # Available carbs
                }
                
        Returns:
            dict[str, Any]: Evaluation metrics
        """
        evaluation = {
            "uses_expiring": False,
            "nutritional_balance": "unknown",
            "meal_variety": "standard",
            "cooking_complexity": "medium",
        }

        # Check if recipe uses expiring ingredients
        ingredients = recipe.get("ingredients", [])
        
        # CRITICAL: Handle both string and dict ingredient formats to avoid TypeError
        # ingredients can be:
        # 1. list[str]: ["chicken breast", "tomatoes", "onions"]
        # 2. list[dict]: [{"name": "chicken breast", "amount": 1}, ...]
        ingredient_strings = []
        for ing in ingredients:
            if isinstance(ing, dict):
                # Extract name from dict format - prevents "expected str, dict found" error
                name = ing.get("name", "")
                if name:
                    ingredient_strings.append(name)
            else:
                # Handle string format directly
                ingredient_strings.append(str(ing))
        recipe_ingredients = " ".join(ingredient_strings).lower()
        for expiring in pantry_analysis["expiring_soon"]:
            if expiring["name"].lower() in recipe_ingredients:
                evaluation["uses_expiring"] = True
                break

        # Evaluate nutritional balance (simple check)
        if any(protein in recipe_ingredients for protein in pantry_analysis["protein_sources"]):
            if any(
                veg in recipe_ingredients
                for veg in pantry_analysis["vegetables"]
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
        """Generate contextual advice about the recipes"""
        advice_parts = []

        # Expiring items advice
        if pantry_analysis["expiring_soon"] and "expir" in message.lower():
            advice_parts.append(
                f"I found {len(pantry_analysis['expiring_soon'])} items expiring soon and prioritized recipes using them."
            )

        # Variety advice
        if len({r.get("cuisine_type", "various") for r in recipes[:3]}) >= 3:
            advice_parts.append("I've included diverse cuisine options for variety.")

        # Quick meal advice
        quick_recipes = [r for r in recipes if r.get("time", 999) <= 20]
        if quick_recipes and any(word in message.lower() for word in ["quick", "fast", "easy"]):
            advice_parts.append(f"I found {len(quick_recipes)} quick recipes (20 min or less).")

        return " ".join(advice_parts)


class CrewAIService:
    def __init__(self):
        """Initialize the AI recipe service."""
        self.db_service = get_database_service()
        self.recipe_service = RecipeService()
        self.user_recipes_service = UserRecipesService(self.db_service)
        self.spoonacular_service = SpoonacularService()
        self.openai_service = OpenAIRecipeService()
        self.preference_scorer = RecipePreferenceScorer(self.db_service)
        self.recipe_advisor = RecipeAdvisor()

        # Initialize OpenAI
        from backend_gateway.core.config_utils import get_openai_api_key

        openai.api_key = get_openai_api_key()

    async def process_message(
        self, user_id: int, message: str, use_preferences: bool = True
    ) -> dict[str, Any]:
        """
        Process a chat message and return recipe recommendations.

        Args:
            user_id: The user's ID
            message: The user's message
            use_preferences: Whether to use user preferences

        Returns:
            Dict containing response, recipes, and pantry items
        """
        logger.info("=" * 60)
        logger.info(f"🚀 STARTING CHAT PROCESS for user {user_id}")
        logger.info(f"📝 Message: '{message}'")
        logger.info(f"⚙️  Use preferences: {use_preferences}")
        logger.info("=" * 60)

        try:
            # Step 1: Fetch pantry items and user preferences
            logger.info("\n📦 STEP 1: Fetching pantry items...")
            pantry_items = await self._fetch_pantry_items(user_id)
            logger.info(f"✅ Found {len(pantry_items)} total pantry items")

            # Only fetch preferences if we're using them
            if use_preferences:
                logger.info("\n👤 Fetching user preferences...")
                user_preferences = await self._fetch_user_preferences(user_id)
                logger.info(f"✅ Preferences loaded: {user_preferences}")
            else:
                logger.info("\n⏭️  Skipping user preferences (use_preferences=False)")
                user_preferences = {
                    "dietary_preference": [],
                    "allergens": [],
                    "cuisine_preference": [],
                }

            # Step 2: Filter non-expired items
            logger.info("\n🔍 STEP 2: Filtering valid (non-expired) items...")
            valid_items = self._filter_valid_items(pantry_items)
            logger.info(f"✅ {len(valid_items)} valid items out of {len(pantry_items)} total")

            # Step 3: Use RecipeAdvisor to analyze pantry
            logger.info("\n🧠 STEP 3: Analyzing pantry with RecipeAdvisor...")
            pantry_analysis = self.recipe_advisor.analyze_pantry(pantry_items)
            logger.info("✅ Analysis complete:")
            logger.info(f"   - Expiring soon: {len(pantry_analysis['expiring_soon'])} items")
            logger.info(f"   - Expired: {len(pantry_analysis['expired'])} items")
            logger.info(f"   - Protein sources: {len(pantry_analysis['protein_sources'])} items")
            logger.info(f"   - Staples: {len(pantry_analysis['staples'])} items")
            logger.info(f"   - Vegetables: {len(pantry_analysis['vegetables'])} items")
            logger.info(f"   - Carbs: {len(pantry_analysis['carbs'])} items")

            # Step 4: Check saved recipes first
            logger.info("\n💾 STEP 4: Checking saved recipes...")
            saved_recipes = await self._get_matching_saved_recipes(user_id, valid_items)
            logger.info(f"✅ Found {len(saved_recipes)} matching saved recipes")

            # Step 5: Get Spoonacular recipes (fewer if we have saved matches)
            num_spoon_recipes = 10 - len(saved_recipes) if len(saved_recipes) < 5 else 5
            logger.info(f"\n🥄 STEP 5: Fetching {num_spoon_recipes} Spoonacular recipes...")
            spoonacular_recipes = await self._get_spoonacular_recipes(
                valid_items, message, user_preferences, num_spoon_recipes
            )
            logger.info(f"✅ Found {len(spoonacular_recipes)} Spoonacular recipes")

            # Step 6: Combine and rank all recipes
            logger.info("\n🔀 STEP 6: Combining recipe sources...")
            all_recipes = self._combine_recipe_sources(saved_recipes, spoonacular_recipes)
            logger.info(
                f"✅ Combined: {len(saved_recipes)} saved + {len(spoonacular_recipes)} Spoonacular = {len(all_recipes)} total"
            )

            # Step 7: Evaluate recipes with advisor
            logger.info("\n📊 STEP 7: Evaluating recipes...")
            for recipe in all_recipes:
                recipe["evaluation"] = self.recipe_advisor.evaluate_recipe_fit(
                    recipe, user_preferences, pantry_analysis
                )
            logger.info(f"✅ Evaluated all {len(all_recipes)} recipes")

            logger.info("\n🏆 STEP 8: Ranking recipes...")
            ranked_recipes = self._rank_recipes(all_recipes, valid_items, user_preferences)
            if ranked_recipes:
                logger.info(
                    f"✅ Top recipe: '{ranked_recipes[0]['name']}' (score: {ranked_recipes[0].get('match_score', 0):.2f})"
                )

            # Step 9: Generate advice and format response
            logger.info("\n💬 STEP 9: Formatting response...")
            advice = self.recipe_advisor.generate_advice(ranked_recipes, pantry_analysis, message)
            response = self._format_response(ranked_recipes, valid_items, message, user_preferences)

            if advice:
                response = f"{response}\n\n💡 {advice}"
                logger.info(f"✅ Added advice: {advice}")

            logger.info(f"\n🎯 FINAL: Returning {len(ranked_recipes)} recipes to user")
            logger.info("=" * 60)

            return {
                "response": response,
                "recipes": ranked_recipes[:5],  # Top 5 recipes
                "pantry_items": valid_items,
                "user_preferences": user_preferences,
            }

        except Exception as e:
            logger.error(f"Error in AI recipe service: {str(e)}")
            raise

    async def _fetch_pantry_items(self, user_id: int) -> list[dict[str, Any]]:
        """Fetch pantry items from database."""
        logger.info(f"🔍 Fetching pantry items for user_id: {user_id}")

        query = """
            SELECT *
            FROM user_pantry_full
            WHERE user_id = %(user_id)s
            ORDER BY expiration_date ASC
        """
        params = {"user_id": user_id}
        logger.info(f"📤 Executing query: user_pantry_full for user {user_id}")

        results = self.db_service.execute_query(query, params)
        logger.info(f"📦 Found {len(results)} pantry items for user {user_id}")

        # Log the product names for debugging
        if results:
            product_names = [item.get("product_name", "Unknown") for item in results[:10]]
            logger.info(f"📋 Sample items: {', '.join(product_names)}")

            # Log categories
            categories = {}
            for item in results:
                cat = item.get("category", "Unknown")
                categories[cat] = categories.get(cat, 0) + 1
            logger.info(f"📊 Categories: {categories}")
        else:
            logger.warning(f"⚠️  No pantry items found for user {user_id}")

        return results

    async def _fetch_user_preferences(self, user_id: int) -> dict[str, Any]:
        """Fetch user preferences from database."""
        logger.info(f"👤 Fetching preferences for user_id: {user_id}")

        query = """
            SELECT *
            FROM user_preferences
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        params = {"user_id": user_id}
        logger.info(f"📤 Executing query: user_preferences for user {user_id}")

        results = self.db_service.execute_query(query, params)
        if results and results[0].get("preferences"):
            # Extract preferences from JSONB column
            prefs_data = results[0]["preferences"]
            preferences = {
                "dietary_preference": prefs_data.get("dietary_restrictions", []),
                "allergens": prefs_data.get("allergens", []),
                "cuisine_preference": prefs_data.get("cuisine_preferences", []),
            }
            logger.info("✅ Found preferences:")
            logger.info(f"   - Dietary: {preferences.get('dietary_preference', [])}")
            logger.info(f"   - Allergens: {preferences.get('allergens', [])}")
            logger.info(f"   - Cuisines: {preferences.get('cuisine_preference', [])}")
            return preferences
        else:
            logger.warning(f"⚠️  No preferences found for user {user_id}, using defaults")
            return {"dietary_preference": [], "allergens": [], "cuisine_preference": []}

    def _filter_valid_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out expired items."""
        today = datetime.now().date()
        valid_items = []

        for item in items:
            if item.get("expiration_date"):
                exp_date = datetime.strptime(str(item["expiration_date"]), "%Y-%m-%d").date()
                if exp_date >= today:
                    valid_items.append(item)
            else:
                # If no expiration date, assume it's valid
                valid_items.append(item)

        return valid_items

    async def _get_matching_saved_recipes(
        self, user_id: int, pantry_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Get user's saved recipes that match current pantry items."""
        try:
            # Get matching recipes from saved collection
            matched_recipes = await self.user_recipes_service.match_recipes_with_pantry(
                user_id=user_id, pantry_items=pantry_items, limit=5
            )

            # Convert to standard recipe format
            standardized_recipes = []
            for recipe in matched_recipes:
                recipe_data = recipe.get("recipe_data", {})

                # Extract relevant fields from saved recipe
                standardized = {
                    "name": recipe["title"],
                    "ingredients": recipe_data.get("ingredients", []),
                    "instructions": recipe_data.get("instructions", []),
                    "nutrition": recipe_data.get("nutrition", {"calories": 0, "protein": 0}),
                    "time": recipe_data.get("time", 30),
                    "meal_type": recipe_data.get("meal_type", "dinner"),
                    "cuisine_type": recipe_data.get("cuisine_type", "various"),
                    "dietary_tags": recipe_data.get("dietary_tags", []),
                    "available_ingredients": recipe["matched_ingredients"],
                    "missing_ingredients": recipe["missing_ingredients"],
                    "missing_count": len(recipe["missing_ingredients"]),
                    "available_count": len(recipe["matched_ingredients"]),
                    "match_score": recipe["match_score"],
                    "allergens_present": [],
                    "matched_preferences": [],
                    "source": "saved",
                    "saved_recipe_id": recipe["id"],
                    "is_favorite": recipe["is_favorite"],
                    "user_rating": recipe["rating"],
                }

                standardized_recipes.append(standardized)

            logger.info(f"Found {len(standardized_recipes)} matching saved recipes")
            return standardized_recipes

        except Exception as e:
            logger.error(f"Error getting saved recipes: {str(e)}")
            return []

    async def _get_spoonacular_recipes(
        self,
        pantry_items: list[dict[str, Any]],
        message: str,
        user_preferences: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get recipe recommendations from Spoonacular API.
        
        Args:
            pantry_items (list[dict[str, Any]]): List of pantry items with:
                [
                    {
                        "pantry_item_id": int,
                        "product_name": str,        # Used for ingredient search
                        "quantity": float,
                        "unit_of_measurement": str,
                        "expiration_date": str,
                        "category": str
                    }
                ]
            user_preferences (dict[str, Any]): User preferences (same as evaluate_recipe_fit)
            limit (int): Maximum number of recipes to return
            
        Returns:
            list[dict[str, Any]]: List of Spoonacular recipe objects
        """ 
        logger.info("🥄 Fetching Spoonacular recipes")
        logger.info(f"📝 User message: '{message}'")

        try:
            # Extract ingredient names from pantry
            ingredient_names = [
                item["product_name"] for item in pantry_items if item.get("product_name")
            ]

            # If asking about expiring items, prioritize those
            message_lower = message.lower()
            if any(
                phrase in message_lower
                for phrase in ["expiring", "expire", "going bad", "use soon"]
            ):
                from datetime import datetime

                today = datetime.now().date()
                expiring_items = []

                for item in pantry_items:
                    if item.get("expiration_date") and item.get("product_name"):
                        exp_date = datetime.strptime(
                            str(item["expiration_date"]), "%Y-%m-%d"
                        ).date()
                        days_until_expiry = (exp_date - today).days
                        if 0 <= days_until_expiry <= 7:
                            expiring_items.append(item["product_name"])

                # Put expiring items first
                if expiring_items:
                    ingredient_names = expiring_items + [
                        i for i in ingredient_names if i not in expiring_items
                    ]

            # Get user allergens from preferences
            allergens = user_preferences.get("allergens", [])

            # Search for recipes using Spoonacular with allergen filtering
            spoon_recipes = await self.spoonacular_service.search_recipes_by_ingredients(
                ingredients=ingredient_names[:10],  # Limit to top 10 ingredients
                number=num_recipes,
                ranking=1,  # Minimize missing ingredients
                ignore_pantry=True,
                intolerances=allergens if allergens else None,
            )

            # Convert Spoonacular format to our standard format
            processed_recipes = []
            for spoon_recipe in spoon_recipes:
                # Get detailed recipe information
                try:
                    detailed = await self.spoonacular_service.get_recipe_information(
                        recipe_id=spoon_recipe["id"], include_nutrition=True
                    )

                    # Extract ingredients with quantities
                    ingredients = []
                    for ing in detailed.get("extendedIngredients", []):
                        amount = ing.get("amount", 1)
                        unit = ing.get("unit", "")
                        name = ing.get("name", "")
                        ingredients.append(f"{amount} {unit} {name}".strip())

                    # Extract instructions
                    instructions = []
                    if "analyzedInstructions" in detailed and detailed["analyzedInstructions"]:
                        for instruction_group in detailed["analyzedInstructions"]:
                            for step in instruction_group.get("steps", []):
                                instructions.append(step.get("step", ""))

                    # Build our standard recipe format
                    recipe = {
                        "name": detailed.get("title", spoon_recipe.get("title", "Unknown Recipe")),
                        "ingredients": ingredients,
                        "instructions": (
                            instructions if instructions else ["No instructions available"]
                        ),
                        "nutrition": {
                            "calories": detailed.get("nutrition", {})
                            .get("nutrients", [{}])[0]
                            .get("amount", 0),
                            "protein": next(
                                (
                                    n["amount"]
                                    for n in detailed.get("nutrition", {}).get("nutrients", [])
                                    if n.get("name") == "Protein"
                                ),
                                0,
                            ),
                        },
                        "time": detailed.get("readyInMinutes", 30),
                        "meal_type": self._detect_meal_type(detailed.get("title", ""), message),
                        "cuisine_type": (
                            detailed.get("cuisines", ["various"])[0]
                            if detailed.get("cuisines")
                            else "various"
                        ),
                        "dietary_tags": detailed.get("diets", []),
                        "spoonacular_id": spoon_recipe["id"],
                        "image": detailed.get("image", spoon_recipe.get("image")),
                        "source": "spoonacular",
                        "source_url": detailed.get("sourceUrl", ""),
                        "servings": detailed.get("servings", 4),
                        "missed_ingredients": spoon_recipe.get("missedIngredients", []),
                        "used_ingredients": spoon_recipe.get("usedIngredients", []),
                    }

                    processed_recipes.append(recipe)

                except Exception as e:
                    logger.error(
                        f"Error getting detailed recipe info for {spoon_recipe['id']}: {str(e)}"
                    )
                    # Still include basic recipe info
                    recipe = {
                        "name": spoon_recipe.get("title", "Unknown Recipe"),
                        "ingredients": [
                            f"{ing['original']}"
                            for ing in spoon_recipe.get("missedIngredients", [])
                            + spoon_recipe.get("usedIngredients", [])
                        ],
                        "instructions": ["Please visit Spoonacular for detailed instructions"],
                        "nutrition": {"calories": 0, "protein": 0},
                        "time": 30,
                        "meal_type": self._detect_meal_type(spoon_recipe.get("title", ""), message),
                        "cuisine_type": "various",
                        "dietary_tags": [],
                        "spoonacular_id": spoon_recipe["id"],
                        "image": spoon_recipe.get("image"),
                        "source": "spoonacular",
                    }
                    processed_recipes.append(recipe)

            # Process recipes to identify available vs missing ingredients (similar to AI recipes)
            for recipe in processed_recipes:
                available_ingredients = []
                missing_ingredients = []
                pantry_item_matches = {}

                # Check each recipe ingredient against pantry
                for ingredient in recipe.get("ingredients", []):
                    found = False
                    matching_items = []

                    for pantry_item in pantry_items:
                        if pantry_item.get("product_name"):
                            cleaned_pantry_name = self._clean_ingredient_name(
                                pantry_item["product_name"]
                            )
                            if self._is_similar_ingredient(cleaned_pantry_name, ingredient):
                                matching_items.append(
                                    {
                                        "pantry_item_id": pantry_item.get("pantry_item_id"),
                                        "product_name": pantry_item.get("product_name"),
                                        "quantity": pantry_item.get("quantity", 0),
                                        "unit": pantry_item.get("unit_of_measurement", "unit"),
                                    }
                                )
                                found = True

                    if found:
                        available_ingredients.append(ingredient)
                        pantry_item_matches[ingredient] = matching_items
                    else:
                        missing_ingredients.append(ingredient)

                # Calculate match score
                total_ingredients = len(recipe.get("ingredients", []))
                available_count = len(available_ingredients)
                missing_count = len(missing_ingredients)
                match_score = available_count / total_ingredients if total_ingredients > 0 else 0

                # Add extra fields
                recipe["available_ingredients"] = available_ingredients
                recipe["missing_ingredients"] = missing_ingredients
                recipe["missing_count"] = missing_count
                recipe["available_count"] = available_count
                recipe["match_score"] = round(match_score, 2)
                recipe["pantry_item_matches"] = pantry_item_matches
                recipe["allergens_present"] = []  # Spoonacular provides allergen info differently
                recipe["matched_preferences"] = []

            return processed_recipes

        except Exception as e:
            logger.error(f"Error fetching Spoonacular recipes: {str(e)}")
            # Return empty list on error
            return []

    def _detect_meal_type(self, recipe_title: str, user_message: str) -> str:
        """Detect meal type from recipe title and user message."""
        title_lower = recipe_title.lower()
        message_lower = user_message.lower()

        # Check user message first
        if any(word in message_lower for word in ["breakfast", "morning", "brunch"]):
            return "breakfast"
        elif any(word in message_lower for word in ["lunch", "midday", "noon"]):
            return "lunch"
        elif any(word in message_lower for word in ["dinner", "supper", "evening"]):
            return "dinner"
        elif any(word in message_lower for word in ["snack", "appetizer", "treat"]):
            return "snack"
        elif any(word in message_lower for word in ["dessert", "sweet", "cake", "cookie"]):
            return "dessert"

        # Then check recipe title
        if any(
            word in title_lower
            for word in ["pancake", "waffle", "omelette", "egg", "breakfast", "cereal", "oatmeal"]
        ):
            return "breakfast"
        elif any(word in title_lower for word in ["sandwich", "salad", "soup", "wrap"]):
            return "lunch"
        elif any(
            word in title_lower
            for word in ["dessert", "cake", "cookie", "ice cream", "pie", "pudding"]
        ):
            return "dessert"
        elif any(word in title_lower for word in ["snack", "dip", "chips", "popcorn"]):
            return "snack"

        return "dinner"  # Default

    async def _generate_recipes(
        self,
        pantry_items: list[dict[str, Any]],
        message: str,
        user_preferences: dict[str, Any],
        num_recipes: int = 5,
    ) -> list[dict[str, Any]]:
        """DEPRECATED: Generate recipes using OpenAI. Use _get_spoonacular_recipes instead."""
        logger.warning("⚠️ _generate_recipes is deprecated. Use _get_spoonacular_recipes instead.")
        return []

        # Detect meal type from user message
        message_lower = message.lower()
        meal_type = "dinner"  # default

        if any(word in message_lower for word in ["breakfast", "morning", "brunch"]):
            meal_type = "breakfast"
        elif any(word in message_lower for word in ["lunch", "midday", "noon"]):
            meal_type = "lunch"
        elif any(word in message_lower for word in ["dinner", "supper", "evening"]):
            meal_type = "dinner"
        elif any(word in message_lower for word in ["snack", "appetizer", "treat"]):
            meal_type = "snack"
        elif any(word in message_lower for word in ["dessert", "sweet", "cake", "cookie"]):
            meal_type = "dessert"

        logger.info(f"🍽️ Detected meal type: {meal_type}")

        # Check if this is an expiring items query
        is_expiring_query = any(
            phrase in message_lower
            for phrase in ["expiring", "expire", "going bad", "use soon", "about to expire"]
        )
        logger.info(f"🕒 Is expiring query: {is_expiring_query}")

        # If asking about expiring items, prioritize those
        if is_expiring_query:
            from datetime import datetime

            today = datetime.now().date()
            expiring_items = []
            other_items = []

            for item in pantry_items:
                if item.get("expiration_date") and item.get("product_name"):
                    exp_date = datetime.strptime(str(item["expiration_date"]), "%Y-%m-%d").date()
                    days_until_expiry = (exp_date - today).days
                    if 0 <= days_until_expiry <= 7:
                        expiring_items.append(item["product_name"])
                    else:
                        other_items.append(item["product_name"])
                elif item.get("product_name"):
                    other_items.append(item["product_name"])

            # Put expiring items first
            available_ingredients = expiring_items + other_items
            logger.info(f"Expiring items to use: {expiring_items}")
        else:
            # Extract ingredient names from pantry
            available_ingredients = [
                item["product_name"] for item in pantry_items if item.get("product_name")
            ]

        logger.info(f"Available ingredients in pantry: {available_ingredients}")

        # Create a normalized ingredient list for the prompt
        normalized_ingredients = []
        for ing in available_ingredients:
            # Remove size/weight info for cleaner prompts
            clean_name = ing.split("–")[0].strip() if "–" in ing else ing
            normalized_ingredients.append(clean_name)

        # Extract preferences
        dietary_prefs = user_preferences.get("dietary_preference", [])
        allergens = user_preferences.get("allergens", [])
        cuisine_prefs = user_preferences.get("cuisine_preference", [])

        # Create a prompt for OpenAI to generate recipes
        expiring_instruction = ""
        if is_expiring_query and expiring_items:
            expiring_instruction = f"""
        URGENT: These ingredients are EXPIRING SOON and should be used first:
        {', '.join(expiring_items[:10])}

        Please prioritize recipes that use these expiring ingredients!
        """

        # Add meal type instruction
        meal_type_instruction = ""
        if meal_type != "dinner":  # Only add specific instruction if not default
            meal_type_examples = {
                "breakfast": "Focus on breakfast dishes like eggs, pancakes, smoothies, oatmeal, breakfast sandwiches, etc.",
                "lunch": "Focus on lunch dishes like sandwiches, salads, soups, wraps, light pasta dishes, etc.",
                "snack": "Focus on snacks and appetizers like dips, finger foods, small bites, energy balls, etc.",
                "dessert": "Focus on desserts like cakes, cookies, puddings, fruit-based sweets, ice cream, etc.",
            }
            meal_type_instruction = f"\nIMPORTANT: User is looking for {meal_type.upper()} recipes! {meal_type_examples.get(meal_type, '')}\n"

        prompt = f"""
        You are a creative chef. Generate {num_recipes} recipes based on ONLY these available ingredients:
        {', '.join(available_ingredients)}

        User request: {message}
        {meal_type_instruction}{expiring_instruction}

        IMPORTANT User Preferences:
        - Dietary restrictions: {', '.join(dietary_prefs) if dietary_prefs else 'None'}
        - Allergens to avoid: {', '.join(allergens) if allergens else 'None'}
        - Favorite cuisines: {', '.join(cuisine_prefs) if cuisine_prefs else 'Any'}

        CRITICAL INSTRUCTIONS:
        1. Create at least 2-3 recipes that use ONLY ingredients from the available list above
        2. Create 3-4 recipes that need 1-3 additional common ingredients (specify exactly what's needed)
        3. DO NOT assume common pantry items are available unless they're in the list
        4. For recipes needing extra ingredients, be specific (e.g., "eggs", "flour", "garlic cloves")
        5. If there are expiring items mentioned above, prioritize using them in your recipes
        6. ALL recipes should be appropriate for {meal_type} time

        Return a JSON array of recipes. Each recipe should have:
        - name: string (creative recipe name appropriate for {meal_type})
        - ingredients: array of strings with quantities (e.g., "2 cups rice", "1 lb chicken breast", "3 cloves garlic")
        - instructions: array of strings (5-8 detailed step-by-step cooking instructions)
        - nutrition: object with calories (number) and protein (number in grams)
        - time: number (cooking time in minutes)
        - meal_type: string (should be "{meal_type}" for all recipes)
        - cuisine_type: string (e.g., italian, mexican, asian, american)
        - dietary_tags: array of strings (e.g., vegetarian, vegan, gluten-free)

        IMPORTANT for ingredients:
        - Include exact quantities (e.g., "2 cups", "1 lb", "3 tablespoons")
        - Be specific about preparation (e.g., "diced", "sliced", "minced")
        - List all ingredients, including those from the pantry

        Return ONLY the JSON array, no other text or markdown.
        """

        try:
            # Call OpenAI to generate recipes
            logger.info("📞 Calling OpenAI API...")
            logger.info(f"🔑 API key available: {bool(openai.api_key)}")
            logger.info(f"📋 Prompt length: {len(prompt)} characters")

            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative chef who generates recipes in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_completion_tokens=2000,
            )

            logger.info("✅ OpenAI API call successful")
            recipes_text = response.choices[0].message.content.strip()
            logger.info(f"📄 Response length: {len(recipes_text)} characters")

            # Clean up the response if it has markdown code blocks
            if recipes_text.startswith("```json"):
                recipes_text = recipes_text[7:]
            if recipes_text.endswith("```"):
                recipes_text = recipes_text[:-3]

            all_recipes = json.loads(recipes_text)
            logger.info(f"✅ Generated {len(all_recipes)} recipes using OpenAI")

            # Log first recipe to check if instructions are included
            if all_recipes:
                first_recipe = all_recipes[0]
                logger.info(f"First recipe sample: {first_recipe.get('name', 'Unknown')}")
                logger.info(f"Has instructions: {'instructions' in first_recipe}")
                if "instructions" in first_recipe:
                    logger.info(f"Instructions count: {len(first_recipe['instructions'])}")

        except Exception as e:
            logger.error(f"Error generating recipes with OpenAI: {str(e)}")
            # Fallback to some basic recipes if OpenAI fails
            # Create meal-type appropriate fallback recipes
            if meal_type == "breakfast":
                all_recipes = [
                    {
                        "name": "Scrambled Eggs with Toast",
                        "ingredients": [
                            "3 eggs",
                            "2 slices bread",
                            "1 tbsp butter",
                            "salt and pepper",
                        ],
                        "instructions": [
                            "Crack eggs into a bowl and whisk with salt and pepper",
                            "Heat butter in a non-stick pan over medium-low heat",
                            "Pour in eggs and stir gently with a spatula",
                            "Continue stirring until eggs are softly set",
                            "Meanwhile, toast bread slices",
                            "Serve eggs on toast immediately",
                        ],
                        "nutrition": {"calories": 320, "protein": 18},
                        "time": 10,
                        "meal_type": "breakfast",
                        "cuisine_type": "american",
                        "dietary_tags": [],
                    },
                    {
                        "name": "Quick Oatmeal Bowl",
                        "ingredients": ["1 cup oats", "2 cups milk", "1 banana", "2 tbsp honey"],
                        "instructions": [
                            "Bring milk to a simmer in a saucepan",
                            "Add oats and reduce heat to low",
                            "Cook for 5 minutes, stirring occasionally",
                            "Slice banana while oats cook",
                            "Remove from heat and stir in honey",
                            "Top with sliced banana and serve",
                        ],
                        "nutrition": {"calories": 380, "protein": 12},
                        "time": 10,
                        "meal_type": "breakfast",
                        "cuisine_type": "american",
                        "dietary_tags": ["vegetarian"],
                    },
                ]
            elif meal_type == "lunch":
                all_recipes = [
                    {
                        "name": "Turkey Sandwich",
                        "ingredients": [
                            "4 slices bread",
                            "6 oz turkey",
                            "2 lettuce leaves",
                            "1 tomato",
                            "2 tbsp mayo",
                        ],
                        "instructions": [
                            "Toast bread slices if desired",
                            "Spread mayo on two slices",
                            "Layer turkey on one slice",
                            "Add lettuce and sliced tomato",
                            "Top with remaining bread slices",
                            "Cut diagonally and serve",
                        ],
                        "nutrition": {"calories": 350, "protein": 25},
                        "time": 5,
                        "meal_type": "lunch",
                        "cuisine_type": "american",
                        "dietary_tags": [],
                    },
                    {
                        "name": "Garden Salad",
                        "ingredients": [
                            "4 cups mixed greens",
                            "1 cucumber",
                            "2 tomatoes",
                            "2 tbsp dressing",
                        ],
                        "instructions": [
                            "Wash and dry salad greens",
                            "Dice cucumber and tomatoes",
                            "Combine greens and vegetables in a bowl",
                            "Drizzle with dressing",
                            "Toss well and serve",
                        ],
                        "nutrition": {"calories": 150, "protein": 3},
                        "time": 10,
                        "meal_type": "lunch",
                        "cuisine_type": "american",
                        "dietary_tags": ["vegetarian", "vegan"],
                    },
                ]
            else:  # Default dinner recipes
                all_recipes = [
                    {
                        "name": "Simple Chicken Dinner",
                        "ingredients": [
                            "2 chicken breasts",
                            "2 cups vegetables",
                            "2 tbsp olive oil",
                            "salt and pepper",
                        ],
                        "instructions": [
                            "Preheat oven to 375°F (190°C)",
                            "Season chicken breasts with salt and pepper",
                            "Heat olive oil in an oven-safe skillet over medium-high heat",
                            "Sear chicken for 3-4 minutes per side until golden",
                            "Add vegetables around chicken and transfer to oven",
                            "Bake for 15-20 minutes until chicken reaches 165°F internally",
                            "Let rest 5 minutes before serving",
                        ],
                        "nutrition": {"calories": 350, "protein": 35},
                        "time": 30,
                        "meal_type": meal_type,
                        "cuisine_type": "american",
                        "dietary_tags": ["gluten-free"],
                    },
                    {
                        "name": "Quick Pasta with Vegetables",
                        "ingredients": [
                            "8 oz pasta",
                            "2 cups mixed vegetables",
                            "3 cloves garlic",
                            "3 tbsp olive oil",
                        ],
                        "instructions": [
                            "Bring a large pot of salted water to boil",
                            "Cook pasta according to package directions",
                            "Meanwhile, heat olive oil in a large skillet",
                            "Add minced garlic and cook until fragrant",
                            "Add vegetables and sauté until tender-crisp",
                            "Drain pasta and toss with vegetables",
                            "Season with salt, pepper, and herbs",
                        ],
                        "nutrition": {"calories": 400, "protein": 12},
                        "time": 20,
                        "meal_type": meal_type,
                        "cuisine_type": "italian",
                        "dietary_tags": ["vegetarian"],
                    },
                    {
                        "name": "Hearty Vegetable Stir-Fry",
                        "ingredients": [
                            "3 cups mixed vegetables",
                            "2 tbsp oil",
                            "2 tbsp soy sauce",
                            "1 tsp ginger",
                        ],
                        "instructions": [
                            "Heat oil in a wok or large skillet over high heat",
                            "Add harder vegetables first (carrots, broccoli)",
                            "Stir-fry for 2-3 minutes",
                            "Add softer vegetables (peppers, mushrooms)",
                            "Add ginger and stir-fry another 2 minutes",
                            "Add soy sauce and toss to coat",
                            "Serve immediately over rice",
                        ],
                        "nutrition": {"calories": 250, "protein": 8},
                        "time": 15,
                        "meal_type": meal_type,
                        "cuisine_type": "asian",
                        "dietary_tags": ["vegetarian", "vegan"],
                    },
                ]

        # Process recipes to identify available vs missing ingredients
        processed_recipes = []

        for recipe in all_recipes:
            available_ingredients = []
            missing_ingredients = []
            pantry_item_matches = {}  # Map ingredient to matching pantry items

            # Check each recipe ingredient against pantry
            for ingredient in recipe.get("ingredients", []):
                found = False
                matching_items = []

                for pantry_item in pantry_items:
                    if pantry_item.get("product_name"):
                        cleaned_pantry_name = self._clean_ingredient_name(
                            pantry_item["product_name"]
                        )
                        if self._is_similar_ingredient(cleaned_pantry_name, ingredient):
                            matching_items.append(
                                {
                                    "pantry_item_id": pantry_item.get("pantry_item_id"),
                                    "product_name": pantry_item.get("product_name"),
                                    "quantity": pantry_item.get("quantity", 0),
                                    "unit": pantry_item.get("unit_of_measurement", "unit"),
                                }
                            )
                            found = True

                if found:
                    available_ingredients.append(ingredient)
                    pantry_item_matches[ingredient] = matching_items
                else:
                    missing_ingredients.append(ingredient)

            # Calculate match score and expected joy
            total_ingredients = len(recipe.get("ingredients", []))
            available_count = len(available_ingredients)
            missing_count = len(missing_ingredients)
            match_score = available_count / total_ingredients if total_ingredients > 0 else 0

            # Check for allergens
            allergens_present = []
            for allergen in allergens:
                for ingredient in recipe.get("ingredients", []):
                    if self._is_allergen_in_ingredient(allergen, ingredient):
                        allergens_present.append(allergen)
                        break

            # Add extra fields
            recipe["available_ingredients"] = available_ingredients
            recipe["missing_ingredients"] = missing_ingredients
            recipe["missing_count"] = missing_count
            recipe["available_count"] = available_count
            recipe["match_score"] = round(match_score, 2)
            recipe["allergens_present"] = allergens_present
            recipe["pantry_item_matches"] = pantry_item_matches  # Include pantry item mapping

            # Check matched preferences
            matched_prefs = []
            if recipe.get("cuisine_type", "").lower() in [c.lower() for c in cuisine_prefs]:
                matched_prefs.append(f"Cuisine: {recipe['cuisine_type']}")
            for tag in recipe.get("dietary_tags", []):
                if tag.lower() in [d.lower() for d in dietary_prefs]:
                    matched_prefs.append(f"Diet: {tag}")
            recipe["matched_preferences"] = matched_prefs

            processed_recipes.append(recipe)

        return processed_recipes

    def _combine_recipe_sources(
        self, saved_recipes: list[dict[str, Any]], ai_recipes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Combine saved and AI-generated recipes, removing duplicates."""
        all_recipes = []
        recipe_names = set()

        # Add saved recipes first (they're personalized)
        for recipe in saved_recipes:
            recipe_name_lower = recipe["name"].lower().strip()
            if recipe_name_lower not in recipe_names:
                recipe_names.add(recipe_name_lower)
                all_recipes.append(recipe)

        # Add AI recipes if they're not duplicates
        for recipe in ai_recipes:
            recipe_name_lower = recipe["name"].lower().strip()
            # Check for similar names
            is_duplicate = False
            for existing_name in recipe_names:
                if recipe_name_lower in existing_name or existing_name in recipe_name_lower:
                    is_duplicate = True
                    break

            if not is_duplicate:
                recipe_names.add(recipe_name_lower)
                if "source" not in recipe:
                    recipe["source"] = "spoonacular"
                all_recipes.append(recipe)

        return all_recipes

    def _rank_recipes(
        self,
        recipes: list[dict[str, Any]],
        pantry_items: list[dict[str, Any]],
        user_preferences: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Rank recipes using advanced preference scoring system."""
        logger.info(f"🏆 Ranking {len(recipes)} recipes with preference scorer...")

        # Get user ID from preferences or pantry items
        user_id = user_preferences.get("user_id")
        if not user_id and pantry_items:
            # Try to get user_id from pantry items (they should have it)
            user_id = 111  # Default for now, should be passed properly

        # Score each recipe using the preference scorer
        for recipe in recipes:
            try:
                score_result = self.preference_scorer.calculate_comprehensive_score(
                    recipe=recipe,
                    user_id=user_id,
                    pantry_items=pantry_items,
                    context={"season": "current", "meal_type": "any"},
                )

                # Add scoring results to recipe
                recipe["preference_score"] = score_result["score"]
                recipe["score_reasoning"] = score_result["reasoning"]
                recipe["recommendation_level"] = score_result["recommendation_level"]
                recipe["score_components"] = score_result["components"]

            except Exception as e:
                logger.warning(f"Could not score recipe {recipe.get('name', 'unknown')}: {e}")
                recipe["preference_score"] = 50.0  # Default middle score

        # Enhanced ranking with preference scores
        ranked = sorted(
            recipes,
            key=lambda r: (
                r.get("preference_score", 0),  # Primary: Comprehensive preference score
                r.get("source") == "saved"
                and r.get("user_rating") == "thumbs_up",  # User's liked recipes
                r.get("evaluation", {}).get(
                    "uses_expiring", False
                ),  # Prioritize expiring ingredients
                r.get("missing_count", 999) == 0,  # Recipes you can make now
                r.get("match_score", 0),  # High ingredient match
                -r.get("missing_count", 999),  # Fewer missing ingredients
            ),
            reverse=True,
        )

        # Log top 3 recipes with preference scores
        for i, recipe in enumerate(ranked[:3]):
            logger.info(f"  #{i+1}: {recipe['name']}")
            logger.info(f"      - Preference score: {recipe.get('preference_score', 0):.1f}/100")
            logger.info(f"      - Recommendation: {recipe.get('recommendation_level', 'Unknown')}")
            logger.info(f"      - Source: {recipe.get('source', 'unknown')}")
            logger.info(f"      - Missing items: {recipe.get('missing_count', 0)}")
            if recipe.get("score_reasoning"):
                logger.info(f"      - Why: {'; '.join(recipe['score_reasoning'][:2])}")

        return ranked

    def _clean_ingredient_name(self, ingredient: str) -> str:
        """Clean ingredient name for better matching."""
        # Remove brand info, sizes, etc.
        cleaned = ingredient.lower().strip()

        # Remove size/weight patterns
        import re

        cleaned = re.sub(
            r"\d+\.?\d*\s*(oz|lbs?|g|kg|ml|l|cups?|tsp|tbsp|tablespoons?|teaspoons?)", "", cleaned
        )
        cleaned = re.sub(r"–.*", "", cleaned)  # Remove anything after dash
        cleaned = re.sub(r"\(.*?\)", "", cleaned)  # Remove parentheses

        # Remove common modifiers
        modifiers = [
            "fresh",
            "frozen",
            "dried",
            "canned",
            "organic",
            "chopped",
            "diced",
            "sliced",
            "minced",
            "whole",
        ]
        for mod in modifiers:
            cleaned = cleaned.replace(mod, "")

        # Clean up extra whitespace
        cleaned = " ".join(cleaned.split())

        return cleaned.strip()

    def _is_allergen_in_ingredient(self, allergen: str, ingredient: str) -> bool:
        """Check if an allergen is present in an ingredient."""
        allergen_lower = allergen.lower()
        ingredient_lower = ingredient.lower()

        # Map common allergens to ingredient patterns
        allergen_patterns = {
            "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "whey", "casein", "lactose"],
            "nuts": [
                "almond",
                "walnut",
                "pecan",
                "cashew",
                "pistachio",
                "hazelnut",
                "macadamia",
                "pine nut",
            ],
            "peanuts": ["peanut"],
            "eggs": ["egg"],
            "soy": ["soy", "tofu", "tempeh", "edamame", "miso"],
            "gluten": ["wheat", "flour", "bread", "pasta", "barley", "rye", "couscous", "bulgur"],
            "shellfish": ["shrimp", "crab", "lobster", "scallop", "oyster", "clam", "mussel"],
            "fish": ["salmon", "tuna", "cod", "tilapia", "bass", "trout", "sardine", "anchovy"],
        }

        # Check direct match or pattern match
        if allergen_lower in ingredient_lower:
            return True

        # Check mapped patterns
        patterns = allergen_patterns.get(allergen_lower, [])
        return any(pattern in ingredient_lower for pattern in patterns)

    def _is_similar_ingredient(self, ingredient1: str, ingredient2: str) -> bool:
        """Check if two ingredients are similar enough to be considered the same."""
        # Clean both ingredients
        clean1 = self._clean_ingredient_name(ingredient1)
        clean2 = self._clean_ingredient_name(ingredient2)

        # Direct match
        if clean1 == clean2:
            return True

        # Check if one contains the other
        if clean1 in clean2 or clean2 in clean1:
            return True

        # Check common variations
        variations = {
            "chicken": ["chicken breast", "chicken thigh", "chicken wing"],
            "beef": ["ground beef", "beef steak", "beef roast"],
            "tomato": ["tomatoes", "cherry tomatoes", "roma tomatoes"],
            "onion": ["onions", "red onion", "yellow onion", "white onion"],
        }

        for base, variants in variations.items():
            if (base in clean1 or any(v in clean1 for v in variants)) and (
                base in clean2 or any(v in clean2 for v in variants)
            ):
                return True

        return False

    def _format_response(
        self,
        recipes: list[dict[str, Any]],
        items: list[dict[str, Any]],
        message: str,
        user_preferences: dict[str, Any],
    ) -> str:
        """Format a natural language response based on the recipes found."""
        # Check if this is an expiring items query
        is_expiring_query = any(
            phrase in message.lower()
            for phrase in ["expiring", "expire", "going bad", "use soon", "about to expire"]
        )

        if is_expiring_query:
            # Find items expiring within 7 days
            from datetime import datetime

            today = datetime.now().date()
            expiring_items = []

            for item in items:
                if item.get("expiration_date") and item.get("product_name"):
                    exp_date = datetime.strptime(str(item["expiration_date"]), "%Y-%m-%d").date()
                    days_until_expiry = (exp_date - today).days
                    if 0 <= days_until_expiry <= 7:
                        expiring_items.append(
                            {
                                "name": item["product_name"],
                                "date": exp_date.strftime("%b %d"),
                                "days": days_until_expiry,
                            }
                        )

            if expiring_items:
                # Sort by days until expiry
                expiring_items.sort(key=lambda x: x["days"])

                # Remove duplicates based on name
                seen_names = set()
                unique_expiring = []
                for item in expiring_items:
                    if item["name"] not in seen_names:
                        seen_names.add(item["name"])
                        unique_expiring.append(item)

                response = f"⚠️ You have {len(unique_expiring)} items expiring soon:\n\n"

                # Show up to 10 items
                for item in unique_expiring[:10]:
                    if item["days"] == 0:
                        response += f"• {item['name']} - Expires TODAY!\n"
                    else:
                        response += (
                            f"• {item['name']} - Expires in {item['days']} days ({item['date']})\n"
                        )

                if len(unique_expiring) > 10:
                    response += f"\n...and {len(unique_expiring) - 10} more items.\n"

                response += "\n💡 Here are recipes to use these items before they expire:"
                return response
            else:
                return "Great news! 🎉 You don't have any items expiring in the next 7 days. Your pantry is well-managed!"

        if not recipes:
            logger.error("❌ NO RECIPES FOUND! This shouldn't happen.")
            logger.error(f"   - Valid items: {len(items)}")
            logger.error(f"   - Message: '{message}'")
            return "I couldn't find any recipes matching your request with your current pantry items. Would you like some shopping suggestions?"

        # Check if user wants recipes with only available ingredients
        wants_available_only = any(
            phrase in message.lower()
            for phrase in [
                "only ingredients i have",
                "what i have",
                "without shopping",
                "available ingredients",
                "no missing",
                "dont need to buy",
            ]
        )

        # Build preference info text
        pref_parts = []
        if user_preferences.get("dietary_preference"):
            pref_parts.append(
                f"dietary preferences ({', '.join(user_preferences['dietary_preference'])})"
            )
        if user_preferences.get("cuisine_preference"):
            pref_parts.append(
                f"cuisine preferences ({', '.join(user_preferences['cuisine_preference'])})"
            )

        allergen_text = ""
        if user_preferences.get("allergens"):
            allergen_text = (
                f" while excluding allergens ({', '.join(user_preferences['allergens'])})"
            )

        pref_text = ""
        if pref_parts or allergen_text:
            if pref_parts:
                pref_text = f" I've considered your {' and '.join(pref_parts)}"
            pref_text += allergen_text + "."

        # Check if we have saved recipes
        saved_recipe_count = sum(1 for r in recipes if r.get("source") == "saved")

        if wants_available_only:
            # Filter for recipes with no missing ingredients
            perfect_match_recipes = [r for r in recipes if r.get("missing_count", 0) == 0]
            if perfect_match_recipes:
                response = (
                    f"Here are recipes you can make with only your current pantry items!{pref_text}"
                )
            else:
                response = f"No recipes can be made with only your current ingredients. Here are the recipes requiring the fewest additional items.{pref_text}"
        else:
            response = f"Based on your pantry items, here are my recommendations!{pref_text}"

        # Add note about saved recipes
        if saved_recipe_count > 0:
            response += f"\n\n✨ Including {saved_recipe_count} recipe{'s' if saved_recipe_count > 1 else ''} from your saved collection!"

        return response
