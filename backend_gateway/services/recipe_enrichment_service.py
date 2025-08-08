"""
Recipe Enrichment Service

This service enriches chat-generated recipes to match Spoonacular data structure,
providing comprehensive nutrition data, structured ingredients, and enhanced metadata.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RecipeEnrichmentService:
    """Service to enrich chat-generated recipes with Spoonacular-style data structure"""

    def __init__(self):
        self.nutrition_estimates = {
            # Basic nutrition estimates per 100g for common ingredients
            'chicken': {'calories': 239, 'protein': 27, 'carbs': 0, 'fat': 14},
            'beef': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 17},
            'pork': {'calories': 242, 'protein': 27, 'carbs': 0, 'fat': 14},
            'fish': {'calories': 206, 'protein': 22, 'carbs': 0, 'fat': 12},
            'salmon': {'calories': 208, 'protein': 25, 'carbs': 0, 'fat': 12},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3},
            'pasta': {'calories': 131, 'protein': 5, 'carbs': 25, 'fat': 1.1},
            'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2},
            'egg': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11},
            'milk': {'calories': 42, 'protein': 3.4, 'carbs': 5, 'fat': 1},
            'cheese': {'calories': 113, 'protein': 7, 'carbs': 1, 'fat': 9},
            'butter': {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81},
            'oil': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100},
            'potato': {'calories': 77, 'protein': 2, 'carbs': 17, 'fat': 0.1},
            'onion': {'calories': 40, 'protein': 1.1, 'carbs': 9, 'fat': 0.1},
            'garlic': {'calories': 149, 'protein': 6.4, 'carbs': 33, 'fat': 0.5},
            'tomato': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2},
            'carrot': {'calories': 41, 'protein': 0.9, 'carbs': 10, 'fat': 0.2},
            'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4},
            'spinach': {'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4},
            'beans': {'calories': 127, 'protein': 8.7, 'carbs': 23, 'fat': 0.5},
        }

    def enrich_recipe(self, recipe: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Enrich a chat-generated recipe to match Spoonacular data structure
        """
        try:
            logger.info(f"Enriching recipe: {recipe.get('name', 'Unknown')}")
            
            enriched_recipe = dict(recipe)
            
            # Normalize basic fields to match Spoonacular structure
            enriched_recipe = self._normalize_basic_fields(enriched_recipe)
            
            # Parse and structure ingredients 
            enriched_recipe = self._structure_ingredients(enriched_recipe)
            
            # Parse and structure instructions
            enriched_recipe = self._structure_instructions(enriched_recipe)
            
            # Estimate nutrition data
            enriched_recipe = self._estimate_nutrition(enriched_recipe)
            
            # Add metadata
            enriched_recipe = self._add_metadata(enriched_recipe, user_id)
            
            # Add Spoonacular-style fields
            enriched_recipe = self._add_spoonacular_fields(enriched_recipe)
            
            logger.info(f"✅ Recipe enriched with Spoonacular-style structure")
            return enriched_recipe
            
        except Exception as e:
            logger.error(f"Error enriching recipe: {e}")
            return recipe  # Return original if enrichment fails

    def _normalize_basic_fields(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize basic fields to match Spoonacular naming"""
        
        # Ensure title field (Spoonacular uses 'title', chat uses 'name')
        if 'name' in recipe and 'title' not in recipe:
            recipe['title'] = recipe['name']
        elif 'title' not in recipe and 'name' not in recipe:
            recipe['title'] = "Untitled Recipe"
            recipe['name'] = recipe['title']
        
        # Normalize time fields
        if 'time' in recipe and 'readyInMinutes' not in recipe:
            recipe['readyInMinutes'] = recipe['time']
        elif 'readyInMinutes' not in recipe:
            recipe['readyInMinutes'] = 30  # Default
        
        # Add servings if missing
        if 'servings' not in recipe:
            recipe['servings'] = 4  # Default
        
        # Add basic image if missing
        if 'image' not in recipe:
            recipe['image'] = f"https://via.placeholder.com/556x370.png/40E0D0/000000?text={recipe['title'][:20]}"
        
        return recipe

    def _structure_ingredients(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ingredients into Spoonacular's extendedIngredients format"""
        
        ingredients = recipe.get('ingredients', [])
        if not ingredients:
            return recipe
        
        extended_ingredients = []
        
        for i, ingredient in enumerate(ingredients):
            if isinstance(ingredient, str):
                # Parse string ingredient into structured format
                parsed = self._parse_ingredient_string(ingredient, i + 1)
                extended_ingredients.append(parsed)
            elif isinstance(ingredient, dict):
                # Convert existing dict format to Spoonacular format
                parsed = self._normalize_ingredient_dict(ingredient, i + 1)
                extended_ingredients.append(parsed)
        
        recipe['extendedIngredients'] = extended_ingredients
        return recipe

    def _parse_ingredient_string(self, ingredient_str: str, ingredient_id: int) -> Dict[str, Any]:
        """Parse an ingredient string into Spoonacular format"""
        
        # Try to extract quantity, unit, and name
        # Pattern: "2 cups flour" or "1 lb chicken breast" or "salt to taste"
        
        patterns = [
            r'^(\d+(?:\.\d+)?(?:\s+\d+/\d+)?)\s+(cups?|cup|tablespoons?|tbsp|teaspoons?|tsp|pounds?|lbs?|lb|ounces?|oz|grams?|g|kilograms?|kg|pieces?|pc|cloves?|slices?)\s+(.+)$',
            r'^(\d+(?:\.\d+)?(?:\s+\d+/\d+)?)\s+(.+)$',  # Just number and ingredient
            r'^(.+)$'  # Just ingredient name
        ]
        
        amount = None
        unit = ""
        name = ingredient_str.strip()
        
        for pattern in patterns:
            match = re.match(pattern, ingredient_str.strip(), re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # quantity, unit, name
                    amount = self._parse_amount(groups[0])
                    unit = groups[1].lower()
                    name = groups[2].strip()
                elif len(groups) == 2:  # quantity, name
                    amount = self._parse_amount(groups[0])
                    name = groups[1].strip()
                break
        
        return {
            'id': ingredient_id,
            'name': name,
            'original': ingredient_str,
            'amount': amount,
            'unit': unit
        }

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            # Handle fractions like "1 1/2"
            if '/' in amount_str:
                parts = amount_str.split()
                if len(parts) == 2 and '/' in parts[1]:
                    whole = float(parts[0])
                    frac_parts = parts[1].split('/')
                    fraction = float(frac_parts[0]) / float(frac_parts[1])
                    return whole + fraction
                elif '/' in amount_str:
                    frac_parts = amount_str.split('/')
                    return float(frac_parts[0]) / float(frac_parts[1])
            else:
                return float(amount_str)
        except:
            return None

    def _normalize_ingredient_dict(self, ingredient: Dict[str, Any], ingredient_id: int) -> Dict[str, Any]:
        """Normalize ingredient dict to Spoonacular format"""
        
        return {
            'id': ingredient.get('id', ingredient_id),
            'name': ingredient.get('name', ingredient.get('ingredient_name', 'Unknown')),
            'original': ingredient.get('original', ingredient.get('name', ingredient.get('ingredient_name', 'Unknown'))),
            'amount': ingredient.get('amount', ingredient.get('quantity')),
            'unit': ingredient.get('unit', '')
        }

    def _structure_instructions(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Parse instructions into Spoonacular's analyzedInstructions format"""
        
        instructions = recipe.get('instructions', [])
        if not instructions:
            return recipe
        
        steps = []
        
        if isinstance(instructions, list):
            for i, instruction in enumerate(instructions):
                if isinstance(instruction, str):
                    steps.append({
                        'number': i + 1,
                        'step': instruction.strip(),
                        'ingredients': [],
                        'equipment': []
                    })
                elif isinstance(instruction, dict):
                    steps.append({
                        'number': instruction.get('number', i + 1),
                        'step': instruction.get('step', instruction.get('instruction', str(instruction))),
                        'ingredients': instruction.get('ingredients', []),
                        'equipment': instruction.get('equipment', [])
                    })
        elif isinstance(instructions, str):
            # Split string by common delimiters
            instruction_list = re.split(r'\d+\.\s*', instructions)
            instruction_list = [inst.strip() for inst in instruction_list if inst.strip()]
            
            for i, instruction in enumerate(instruction_list):
                steps.append({
                    'number': i + 1,
                    'step': instruction.strip(),
                    'ingredients': [],
                    'equipment': []
                })
        
        recipe['analyzedInstructions'] = [{
            'name': '',
            'steps': steps
        }]
        
        return recipe

    def _estimate_nutrition(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate nutrition data based on ingredients"""
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        extended_ingredients = recipe.get('extendedIngredients', [])
        servings = recipe.get('servings', 4)
        
        for ingredient in extended_ingredients:
            ingredient_name = ingredient.get('name', '').lower()
            amount = ingredient.get('amount', 0) or 0
            
            # Find matching nutrition data (rough estimates)
            for key, nutrition in self.nutrition_estimates.items():
                if key in ingredient_name:
                    # Rough conversion based on amount (assuming 100g portions)
                    multiplier = max(0.5, amount / 100) if amount > 0 else 0.5
                    
                    total_calories += nutrition['calories'] * multiplier
                    total_protein += nutrition['protein'] * multiplier
                    total_carbs += nutrition['carbs'] * multiplier
                    total_fat += nutrition['fat'] * multiplier
                    break
        
        # If no ingredients matched, provide default values
        if total_calories == 0:
            total_calories = 250  # Default per serving
            total_protein = 15
            total_carbs = 30
            total_fat = 8
        
        # Calculate per-serving values
        calories_per_serving = total_calories / servings
        protein_per_serving = total_protein / servings
        carbs_per_serving = total_carbs / servings
        fat_per_serving = total_fat / servings
        
        # Create Spoonacular-style nutrition object
        recipe['nutrition'] = {
            'calories': round(calories_per_serving),
            'protein': round(protein_per_serving, 1),
            'carbs': round(carbs_per_serving, 1),
            'fat': round(fat_per_serving, 1),
            'fiber': round(carbs_per_serving * 0.1, 1),  # Estimate
            'sugar': round(carbs_per_serving * 0.3, 1),  # Estimate
            'nutrients': [
                {
                    'name': 'Calories',
                    'amount': round(calories_per_serving),
                    'unit': 'kcal',
                    'percentOfDailyNeeds': round((calories_per_serving / 2000) * 100, 1)
                },
                {
                    'name': 'Protein',
                    'amount': round(protein_per_serving, 1),
                    'unit': 'g',
                    'percentOfDailyNeeds': round((protein_per_serving / 50) * 100, 1)
                },
                {
                    'name': 'Carbohydrates',
                    'amount': round(carbs_per_serving, 1),
                    'unit': 'g',
                    'percentOfDailyNeeds': round((carbs_per_serving / 300) * 100, 1)
                },
                {
                    'name': 'Fat',
                    'amount': round(fat_per_serving, 1),
                    'unit': 'g',
                    'percentOfDailyNeeds': round((fat_per_serving / 65) * 100, 1)
                }
            ]
        }
        
        return recipe

    def _add_metadata(self, recipe: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Add metadata fields"""
        
        # Estimate price per serving (rough estimate based on ingredients)
        estimated_price = 0
        extended_ingredients = recipe.get('extendedIngredients', [])
        
        # Very rough price estimates per ingredient
        price_estimates = {
            'chicken': 3.0, 'beef': 4.0, 'pork': 3.5, 'fish': 5.0,
            'rice': 0.5, 'pasta': 1.0, 'bread': 0.3, 'egg': 0.25,
            'milk': 0.5, 'cheese': 2.0, 'butter': 0.5, 'oil': 0.3
        }
        
        for ingredient in extended_ingredients:
            ingredient_name = ingredient.get('name', '').lower()
            for key, price in price_estimates.items():
                if key in ingredient_name:
                    estimated_price += price
                    break
            else:
                estimated_price += 1.0  # Default
        
        servings = recipe.get('servings', 4)
        price_per_serving = (estimated_price / servings) * 100  # Convert to cents
        
        recipe['pricePerServing'] = round(price_per_serving)
        
        # Add cuisine and diet info (basic estimation)
        recipe['cuisines'] = recipe.get('cuisines', [])
        recipe['diets'] = recipe.get('diets', [])
        recipe['dishTypes'] = recipe.get('dishTypes', ['main course'])
        
        return recipe

    def _add_spoonacular_fields(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Add additional Spoonacular-compatible fields"""
        
        # Add sourceUrl (placeholder)
        recipe['sourceUrl'] = f"https://prepsense.ai/chat-recipe/{recipe.get('id', 'unknown')}"
        
        # Add summary if missing
        if 'summary' not in recipe:
            ingredients_count = len(recipe.get('extendedIngredients', []))
            time = recipe.get('readyInMinutes', 30)
            recipe['summary'] = f"A delicious recipe with {ingredients_count} ingredients, ready in {time} minutes. Perfect for a satisfying meal!"
        
        # Ensure ID is set
        if 'id' not in recipe:
            recipe['id'] = hash(recipe['title']) % 100000  # Generate pseudo-ID
        
        return recipe

    def enrich_saved_recipes_batch(self, recipes: List[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
        """Enrich multiple saved recipes in batch"""
        
        enriched_recipes = []
        for recipe in recipes:
            try:
                # Only enrich chat-generated recipes that lack structure
                recipe_data = recipe.get('recipe_data', {})
                source = recipe.get('source', '')
                
                if source == 'chat' or source == 'openai':
                    # Check if recipe needs enrichment
                    if not recipe_data.get('extendedIngredients') or not recipe_data.get('nutrition'):
                        logger.info(f"Enriching saved recipe: {recipe.get('recipe_title', 'Unknown')}")
                        enriched_data = self.enrich_recipe(recipe_data, user_id)
                        recipe['recipe_data'] = enriched_data
                
                enriched_recipes.append(recipe)
                
            except Exception as e:
                logger.error(f"Error enriching saved recipe: {e}")
                enriched_recipes.append(recipe)  # Include original if enrichment fails
        
        return enriched_recipes