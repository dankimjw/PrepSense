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

        return analysis

    def evaluate_recipe_fit(
        self,
        recipe: dict[str, Any],
        user_preferences: dict[str, Any],
        pantry_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate how well a recipe fits the user's needs"""
        evaluation = {
            "uses_expiring": False,
            "nutritional_balance": "unknown",
            "meal_variety": "standard",
            "cooking_complexity": "medium",
        }

        # Check if recipe uses expiring ingredients
        recipe_ingredients = " ".join(recipe.get("ingredients", [])).lower()
        for expiring in pantry_analysis["expiring_soon"]:
            if expiring["name"].lower() in recipe_ingredients:
                evaluation["uses_expiring"] = True
                break

        # Evaluate nutritional balance (simple check)
        if any(protein in recipe_ingredients for protein in pantry_analysis["protein_sources"]):
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

    def _generate_recipe_id(self, recipe: dict[str, Any], source: str) -> str:
        """Generate a unique ID for recipes that don't have one"""
        # Try to get existing ID first
        existing_id = None

        # For saved recipes, check multiple possible ID sources
        if source == "saved":
            # Check direct ID fields
            existing_id = recipe.get("id") or recipe.get("recipe_id")

            # Check recipe_data for external IDs
            if not existing_id and "recipe_data" in recipe:
                recipe_data = recipe["recipe_data"]
                existing_id = recipe_data.get("external_recipe_id") or recipe_data.get("id")

        # For Spoonacular recipes
        elif source == "spoonacular":
            existing_id = recipe.get("id") or recipe.get("recipe_id")

        # Use existing ID if found
        if existing_id:
            return str(existing_id)

        # Generate fallback ID based on recipe name and timestamp
        recipe_name = recipe.get("name") or recipe.get("title", "unknown")
        name_hash = hash(recipe_name) % 100000  # Get a reasonably short hash
        timestamp = int(datetime.now().timestamp()) % 10000  # Short timestamp

        fallback_id = f"{source}_{abs(name_hash)}_{timestamp}"
        logger.info(f"Generated fallback ID '{fallback_id}' for recipe '{recipe_name}'")
        return fallback_id

    def _is_demo_recipe(self, recipe: dict[str, Any]) -> bool:
        """Check if a recipe is a demo recipe (ID between 1001-1010)"""
        try:
            # Check multiple possible sources for recipe ID
            recipe_id = None

            # First check direct ID field
            if "id" in recipe:
                recipe_id = recipe["id"]

            # Check if it's a saved recipe with external_recipe_id
            elif "recipe_data" in recipe and isinstance(recipe["recipe_data"], dict):
                recipe_data = recipe["recipe_data"]
                recipe_id = recipe_data.get("external_recipe_id") or recipe_data.get("id")

            # Check if it's from Spoonacular with recipe_id
            elif "recipe_id" in recipe:
                recipe_id = recipe["recipe_id"]

            # Try to convert to int and check if it's in demo range
            if recipe_id is not None:
                try:
                    recipe_id_int = int(recipe_id)
                    return 1001 <= recipe_id_int <= 1010
                except (ValueError, TypeError):
                    pass

            return False
        except Exception:
            return False

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
                "cuisine_preference": prefs_data.get("cuisine_preference", []),
                "meal_types": prefs_data.get("meal_types", []),
                "cooking_time": prefs_data.get("cooking_time", "any"),
                "spice_level": prefs_data.get("spice_level", "medium"),
            }
            logger.info(f"✅ Loaded preferences: {list(preferences.keys())}")
            return preferences
        else:
            logger.info("ℹ️  No preferences found for user, using defaults")
            return {"dietary_preference": [], "allergens": [], "cuisine_preference": []}

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
                    "id": self._generate_recipe_id(recipe, "saved"),  # ✅ ADD MISSING ID
                    "name": recipe["title"],
                    "ingredients": recipe_data.get("ingredients", []),
                    "instructions": recipe_data.get("instructions", []),
                    "nutrition": recipe_data.get("nutrition", {"calories": 0, "protein": 0}),
                    "time": recipe_data.get("readyInMinutes", recipe_data.get("time", 30)),
                    "servings": recipe_data.get("servings", 4),
                    "image_url": recipe.get("image", ""),
                    "source": "saved",
                    "user_rating": recipe.get("rating", "neutral"),
                    "is_favorite": recipe.get("is_favorite", False),
                    "match_score": recipe.get("match_score", 0),
                    "missing_count": len(recipe.get("missing_ingredients", [])),
                    "missing_ingredients": recipe.get("missing_ingredients", []),
                    "can_make": recipe.get("can_make", False),
                    "recipe_data": recipe_data,
                    "is_demo_recipe": recipe.get("is_demo_recipe", False),
                }

                standardized_recipes.append(standardized)

            logger.info(f"✅ Standardized {len(standardized_recipes)} saved recipes with IDs")
            return standardized_recipes

        except Exception as e:
            logger.error(f"Error getting saved recipes: {str(e)}")
            return []

    def _filter_valid_items(self, pantry_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out expired pantry items and those with zero quantity."""
        from datetime import date, datetime

        today = date.today()
        valid_items = []

        for item in pantry_items:
            # Skip items with zero or negative available quantity
            available_qty = item.get("available_quantity", item.get("quantity", 0))
            if available_qty <= 0:
                continue

            # Check expiration date
            exp_date = item.get("expiration_date")
            if exp_date:
                # Handle both string and date objects
                if isinstance(exp_date, str):
                    exp_date = datetime.strptime(exp_date, "%Y-%m-%d").date()
                elif isinstance(exp_date, datetime):
                    exp_date = exp_date.date()

                # Skip expired items
                if exp_date < today:
                    continue

            valid_items.append(item)

        return valid_items

    async def _get_spoonacular_recipes(
        self,
        pantry_items: list[dict[str, Any]],
        message: str,
        user_preferences: dict[str, Any],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get recipe recommendations from Spoonacular API."""
        logger.info(f"🥄 Getting {limit} Spoonacular recipes...")

        try:
            # Extract ingredient names for search
            ingredient_names = []
            for item in pantry_items[:10]:  # Limit to avoid API limits
                name = item.get("product_name", "").strip()
                if name:
                    # Clean up ingredient name
                    cleaned_name = self._clean_ingredient_name(name)
                    if cleaned_name:
                        ingredient_names.append(cleaned_name)

            if not ingredient_names:
                logger.warning("⚠️  No valid ingredients found for Spoonacular search")
                return []

            # Use find_by_ingredients for pantry-based search
            ingredient_query = ",".join(ingredient_names)
            logger.info(f"🔍 Searching Spoonacular with ingredients: {ingredient_query[:100]}...")

            result = await self.spoonacular_service.find_by_ingredients(
                ingredients=ingredient_query,
                number=limit,
                ranking=2,  # Maximize used ingredients
                ignore_pantry=False,
            )

            if not result or "results" not in result:
                logger.warning("⚠️  No results from Spoonacular API")
                return []

            recipes = result["results"]
            logger.info(f"✅ Got {len(recipes)} recipes from Spoonacular")

            # Standardize recipe format
            standardized_recipes = []
            for recipe in recipes:
                # Get detailed recipe information if needed
                detailed_recipe = await self._get_recipe_details(recipe.get("id"))

                # Calculate missing ingredients count
                used_ingredients = recipe.get("usedIngredients", [])
                missed_ingredients = recipe.get("missedIngredients", [])
                recipe.get("unusedIngredients", [])

                missing_count = len(missed_ingredients)
                can_make = missing_count == 0

                standardized = {
                    "id": str(recipe.get("id")),  # ✅ ENSURE ID IS STRING
                    "name": recipe.get("title", "Unknown Recipe"),
                    "ingredients": self._extract_ingredients(detailed_recipe or recipe),
                    "instructions": self._extract_instructions(detailed_recipe or recipe),
                    "nutrition": self._extract_nutrition(detailed_recipe or recipe),
                    "time": detailed_recipe.get("readyInMinutes", 30) if detailed_recipe else 30,
                    "servings": detailed_recipe.get("servings", 4) if detailed_recipe else 4,
                    "image_url": recipe.get("image", ""),
                    "source": "spoonacular",
                    "recipe_id": recipe.get("id"),
                    "match_score": (
                        (len(used_ingredients) / (len(used_ingredients) + missing_count))
                        if (len(used_ingredients) + missing_count) > 0
                        else 0
                    ),
                    "missing_count": missing_count,
                    "missing_ingredients": [ing.get("name", "") for ing in missed_ingredients],
                    "can_make": can_make,
                    "used_ingredient_count": len(used_ingredients),
                    "likes": recipe.get("likes", 0),
                }

                standardized_recipes.append(standardized)

            logger.info(f"✅ Standardized {len(standardized_recipes)} Spoonacular recipes with IDs")
            return standardized_recipes

        except Exception as e:
            logger.error(f"Error getting Spoonacular recipes: {str(e)}")
            return []

    async def _get_recipe_details(self, recipe_id: int) -> dict[str, Any]:
        """Get detailed recipe information from Spoonacular."""
        try:
            if not recipe_id:
                return {}

            result = await self.spoonacular_service.get_recipe_information(
                recipe_id=recipe_id, include_nutrition=True
            )

            return result if result else {}

        except Exception as e:
            logger.warning(f"Could not get details for recipe {recipe_id}: {str(e)}")
            return {}

    def _extract_ingredients(self, recipe: dict[str, Any]) -> list[str]:
        """Extract ingredients list from recipe data."""
        # Try different possible ingredient fields
        if "extendedIngredients" in recipe:
            return [
                ing.get("original", ing.get("name", "")) for ing in recipe["extendedIngredients"]
            ]
        elif "ingredients" in recipe:
            return recipe["ingredients"]
        elif "usedIngredients" in recipe or "missedIngredients" in recipe:
            # Combine used and missed ingredients
            used = recipe.get("usedIngredients", [])
            missed = recipe.get("missedIngredients", [])
            all_ingredients = []
            for ing in used + missed:
                if isinstance(ing, dict):
                    all_ingredients.append(ing.get("name", ing.get("original", "")))
                else:
                    all_ingredients.append(str(ing))
            return all_ingredients
        return []

    def _extract_instructions(self, recipe: dict[str, Any]) -> list[str]:
        """Extract cooking instructions from recipe data."""
        # Try different possible instruction fields
        if "analyzedInstructions" in recipe and recipe["analyzedInstructions"]:
            steps = recipe["analyzedInstructions"][0].get("steps", [])
            return [step.get("step", "") for step in steps]
        elif "instructions" in recipe:
            return recipe["instructions"]
        return []

    def _extract_nutrition(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """Extract nutrition information from recipe data."""
        if "nutrition" in recipe and "nutrients" in recipe["nutrition"]:
            nutrients = recipe["nutrition"]["nutrients"]
            nutrition = {"calories": 0, "protein": 0}

            for nutrient in nutrients:
                name = nutrient.get("name", "").lower()
                amount = nutrient.get("amount", 0)

                if "calorie" in name:
                    nutrition["calories"] = amount
                elif "protein" in name:
                    nutrition["protein"] = amount

            return nutrition

        return {"calories": 0, "protein": 0}

    def _combine_recipe_sources(
        self, saved_recipes: list[dict[str, Any]], spoonacular_recipes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Combine recipes from different sources."""
        all_recipes = []

        # Add saved recipes first (they get priority)
        for recipe in saved_recipes:
            all_recipes.append(recipe)

        # Add Spoonacular recipes
        for recipe in spoonacular_recipes:
            # Avoid duplicates by checking recipe names
            existing_names = [r["name"].lower() for r in all_recipes]
            if recipe["name"].lower() not in existing_names:
                all_recipes.append(recipe)

        return all_recipes

    def _rank_recipes(
        self,
        recipes: list[dict[str, Any]],
        pantry_items: list[dict[str, Any]],
        user_preferences: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Rank recipes using advanced preference scoring system, prioritizing demo recipes."""
        logger.info(f"🏆 Ranking {len(recipes)} recipes with demo recipe priority...")

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

        # Enhanced ranking with demo recipe priority
        ranked = sorted(
            recipes,
            key=lambda r: (
                self._is_demo_recipe(r),  # HIGHEST PRIORITY: Demo recipes first
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

        # Log top 3 recipes with preference scores and demo status
        for i, recipe in enumerate(ranked[:3]):
            logger.info(f"  #{i+1}: {recipe['name']}")
            logger.info(f"      - Demo recipe: {'YES' if self._is_demo_recipe(recipe) else 'no'}")
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

        # Common allergen mappings
        allergen_keywords = {
            "nuts": [
                "nuts",
                "peanut",
                "almond",
                "walnut",
                "pecan",
                "cashew",
                "pistachio",
                "hazelnut",
            ],
            "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "lactose"],
            "eggs": ["egg"],
            "soy": ["soy", "soya", "tofu", "tempeh"],
            "gluten": ["wheat", "flour", "gluten", "bread", "pasta"],
            "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster", "mussel"],
            "fish": ["fish", "salmon", "tuna", "cod", "mackerel"],
        }

        # Check direct allergen match
        if allergen_lower in ingredient_lower:
            return True

        # Check allergen keywords
        keywords = allergen_keywords.get(allergen_lower, [allergen_lower])
        return any(keyword in ingredient_lower for keyword in keywords)

    def _format_response(
        self,
        recipes: list[dict[str, Any]],
        pantry_items: list[dict[str, Any]],
        message: str,
        user_preferences: dict[str, Any],
    ) -> str:
        """Format the response text based on found recipes and user context."""
        if not recipes:
            return "I couldn't find any recipes that match your current pantry items. Try adding more ingredients or let me know what specific dish you're craving!"

        # Check if we have demo recipes in the results
        demo_recipes = [r for r in recipes[:3] if self._is_demo_recipe(r)]
        response_parts = []

        if demo_recipes:
            response_parts.append(
                f"🌟 Great! I found {len(demo_recipes)} featured high-protein recipe{'s' if len(demo_recipes) > 1 else ''} that would be perfect for you!"
            )

        # Context-aware opening
        if "quick" in message.lower() or "fast" in message.lower():
            quick_recipes = [r for r in recipes[:3] if r.get("time", 999) <= 30]
            if quick_recipes:
                response_parts.append(
                    f"I found {len(quick_recipes)} quick recipe{'s' if len(quick_recipes) > 1 else ''} (30 min or less) using your pantry items."
                )
        elif "healthy" in message.lower():
            response_parts.append(
                "I've focused on nutritionally balanced recipes with good protein content."
            )
        elif "dinner" in message.lower():
            response_parts.append("Here are some great dinner options based on what you have:")
        else:
            response_parts.append(
                f"Based on your pantry items, I found {len(recipes)} recipe{'s' if len(recipes) > 1 else ''} you can make!"
            )

        # Ingredient availability info
        can_make_now = [r for r in recipes[:3] if r.get("can_make", False)]
        if can_make_now:
            response_parts.append(
                f"🎉 {len(can_make_now)} of these recipes can be made with ingredients you already have!"
            )

        # Expiring items priority
        expiring_recipes = [
            r for r in recipes[:3] if r.get("evaluation", {}).get("uses_expiring", False)
        ]
        if expiring_recipes:
            response_parts.append(
                f"💡 {len(expiring_recipes)} recipe{'s' if len(expiring_recipes) > 1 else ''} will help use up ingredients expiring soon."
            )

        return " ".join(response_parts)
