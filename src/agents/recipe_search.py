
import logging
from src.tools.spoonacular_api import search_by_ingredients, get_recipe_information

logger = logging.getLogger(__name__)

class RecipeSearch:
    name = "recipe_search"

    async def run(self, fresh_items: list[dict], max_recipes: int = 20):
        """
        Input: [{'canonical_name': 'chicken breast', 'category': 'Poultry', 'qty_canon': Decimal('0.907'), 'canon_unit': 'kilogram'}...]
        Output: [{'recipe_id': 123, 'title': 'Chicken Stir Fry', 'ingredients': [...], 'nutrition': {...}}...]
        """
        if not fresh_items:
            logger.warning("No fresh items provided for recipe search")
            return []

        try:
            # Extract ingredient names for search
            ingredient_names = []
            for item in fresh_items:
                canonical_name = item.get("canonical_name", "")
                if canonical_name:
                    # Clean up name for better search results
                    cleaned_name = self._clean_ingredient_name(canonical_name)
                    ingredient_names.append(cleaned_name)

            if not ingredient_names:
                logger.warning("No valid ingredient names found")
                return []

            # Search for recipes using Spoonacular API
            logger.info(f"Searching recipes with ingredients: {ingredient_names[:5]}...")  # Log first 5
            search_results = await search_by_ingredients(ingredient_names, number=max_recipes)
            
            if not search_results:
                logger.warning("No recipes found from search")
                return []

            # Get detailed information for each recipe
            detailed_recipes = []
            for recipe in search_results:
                try:
                    recipe_id = recipe.get("id")
                    if not recipe_id:
                        continue

                    # Get full recipe information including nutrition
                    recipe_info = await get_recipe_information(recipe_id)
                    
                    # Extract key information
                    detailed_recipe = {
                        "recipe_id": recipe_id,
                        "title": recipe_info.get("title", ""),
                        "ready_in_minutes": recipe_info.get("readyInMinutes", 0),
                        "servings": recipe_info.get("servings", 1),
                        "source_url": recipe_info.get("sourceUrl", ""),
                        "image": recipe_info.get("image", ""),
                        "summary": recipe_info.get("summary", ""),
                        "instructions": self._extract_instructions(recipe_info),
                        "ingredients": self._extract_ingredients(recipe_info),
                        "nutrition": self._extract_nutrition(recipe_info),
                        "diet_tags": recipe_info.get("diets", []),
                        "cuisine": recipe_info.get("cuisines", []),
                        "dish_types": recipe_info.get("dishTypes", []),
                        "used_ingredients": recipe.get("usedIngredients", []),
                        "missed_ingredients": recipe.get("missedIngredients", []),
                        "unused_ingredients": recipe.get("unusedIngredients", []),
                        "likes": recipe.get("likes", 0)
                    }
                    
                    detailed_recipes.append(detailed_recipe)

                except Exception as e:
                    logger.error(f"Error getting details for recipe {recipe.get('id')}: {e}")
                    continue

            logger.info(f"Retrieved detailed information for {len(detailed_recipes)} recipes")
            return detailed_recipes

        except Exception as e:
            logger.error(f"Recipe search failed: {e}")
            return []

    def _clean_ingredient_name(self, name: str) -> str:
        """Clean ingredient name for better search results"""
        # Remove common prefixes/suffixes that might confuse search
        name = name.lower().strip()
        
        # Remove descriptors that are too specific
        remove_words = ['raw', 'fresh', 'organic', 'lean', 'boneless', 'skinless']
        words = name.split()
        cleaned_words = [w for w in words if w not in remove_words]
        
        return ' '.join(cleaned_words) if cleaned_words else name

    def _extract_instructions(self, recipe_info: dict) -> list[str]:
        """Extract cooking instructions from recipe"""
        instructions = []
        
        # Try analyzed instructions first (more structured)
        analyzed_instructions = recipe_info.get("analyzedInstructions", [])
        if analyzed_instructions and len(analyzed_instructions) > 0:
            steps = analyzed_instructions[0].get("steps", [])
            for step in steps:
                instruction = step.get("step", "").strip()
                if instruction:
                    instructions.append(instruction)
        
        # Fallback to raw instructions
        if not instructions:
            raw_instructions = recipe_info.get("instructions", "")
            if raw_instructions:
                # Simple split by sentence/period
                sentences = raw_instructions.split('. ')
                instructions = [s.strip() for s in sentences if s.strip()]
        
        return instructions

    def _extract_ingredients(self, recipe_info: dict) -> list[dict]:
        """Extract ingredients from recipe"""
        ingredients = []
        
        extended_ingredients = recipe_info.get("extendedIngredients", [])
        for ing in extended_ingredients:
            ingredient = {
                "id": ing.get("id"),
                "name": ing.get("name", ""),
                "original": ing.get("original", ""),
                "amount": ing.get("amount", 0),
                "unit": ing.get("unit", ""),
                "aisle": ing.get("aisle", ""),
                "consistency": ing.get("consistency", ""),
                "image": ing.get("image", "")
            }
            ingredients.append(ingredient)
        
        return ingredients

    def _extract_nutrition(self, recipe_info: dict) -> dict:
        """Extract nutrition information from recipe"""
        nutrition = {}
        
        nutrition_info = recipe_info.get("nutrition", {})
        if nutrition_info:
            # Get nutrients array
            nutrients = nutrition_info.get("nutrients", [])
            for nutrient in nutrients:
                name = nutrient.get("name", "").lower()
                amount = nutrient.get("amount", 0)
                unit = nutrient.get("unit", "")
                
                # Map common nutrients
                if "calorie" in name:
                    nutrition["calories"] = amount
                elif "fat" in name and "saturated" not in name and "trans" not in name:
                    nutrition["fat_g"] = amount
                elif "saturated fat" in name:
                    nutrition["saturated_fat_g"] = amount
                elif "carbohydrate" in name:
                    nutrition["carbs_g"] = amount
                elif "protein" in name:
                    nutrition["protein_g"] = amount
                elif "fiber" in name:
                    nutrition["fiber_g"] = amount
                elif "sugar" in name:
                    nutrition["sugar_g"] = amount
                elif "sodium" in name:
                    nutrition["sodium_mg"] = amount
        
        return nutrition