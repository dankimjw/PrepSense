"""Enhanced OpenAI recipe generation service with advanced features"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import random
from ..core.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class EnhancedOpenAIRecipeService:
    """Advanced recipe generation using OpenAI with enhanced features"""
    
    def __init__(self):
        try:
            self.client = get_openai_client()
        except ValueError as e:
            logger.warning(f"OpenAI service disabled: {str(e)}")
            self.client = None
        
        # Recipe templates for variety
        self.cooking_styles = [
            "modern fusion", "traditional comfort food", "quick and easy",
            "gourmet restaurant-style", "healthy Mediterranean", "Asian-inspired",
            "rustic homestyle", "elegant fine dining", "street food style"
        ]
        
        # Flavor profiles for better recipes
        self.flavor_profiles = [
            "savory and aromatic", "bright and fresh", "rich and hearty",
            "spicy and bold", "sweet and savory", "tangy and zesty",
            "umami-rich", "herbaceous", "smoky and grilled"
        ]
    
    async def generate_enhanced_recipes(
        self,
        ingredients: List[str],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate enhanced recipes with detailed information
        
        Args:
            ingredients: Available ingredients
            context: Dict containing:
                - allergens: List of allergens to avoid
                - dietary_preferences: List of dietary restrictions
                - cuisine_preference: Preferred cuisine type
                - meal_type: breakfast/lunch/dinner/snack
                - cooking_time: max time in minutes
                - skill_level: beginner/intermediate/advanced
                - serving_size: number of servings needed
                - flavor_preference: preferred flavor profile
                - equipment: available cooking equipment
                
        Returns:
            List of detailed recipe dictionaries
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return []
        
        try:
            # Determine number of recipes based on context
            num_recipes = context.get('number', 3)
            
            # Generate recipes with enhanced prompting
            recipes = []
            
            # Use parallel generation for multiple recipes
            if num_recipes > 1:
                tasks = []
                for i in range(num_recipes):
                    # Vary the style for each recipe
                    recipe_context = context.copy()
                    recipe_context['style'] = random.choice(self.cooking_styles)
                    recipe_context['flavor'] = random.choice(self.flavor_profiles)
                    recipe_context['recipe_index'] = i
                    
                    task = self._generate_single_enhanced_recipe(
                        ingredients, recipe_context
                    )
                    tasks.append(task)
                
                # Generate recipes in parallel
                recipe_results = await asyncio.gather(*tasks)
                recipes = [r for r in recipe_results if r is not None]
            else:
                # Single recipe generation
                recipe = await self._generate_single_enhanced_recipe(
                    ingredients, context
                )
                if recipe:
                    recipes.append(recipe)
            
            # Post-process recipes
            for i, recipe in enumerate(recipes):
                recipe['id'] = f"openai_enhanced_{int(datetime.now().timestamp())}_{i}"
                recipe['source'] = 'openai_enhanced'
                recipe['generation_timestamp'] = datetime.now().isoformat()
                
                # Add quality score based on ingredient usage
                recipe['quality_score'] = self._calculate_quality_score(
                    recipe, ingredients, context
                )
            
            # Sort by quality score
            recipes.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            
            logger.info(f"Generated {len(recipes)} enhanced recipes using OpenAI")
            return recipes
            
        except Exception as e:
            logger.error(f"Error generating enhanced recipes: {str(e)}")
            return []
    
    async def _generate_single_enhanced_recipe(
        self,
        ingredients: List[str],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a single enhanced recipe"""
        
        try:
            # Build enhanced prompt
            prompt = self._build_enhanced_prompt(ingredients, context)
            
            # Use GPT-4 if available for better quality
            model = "gpt-4" if context.get('high_quality', False) else "gpt-3.5-turbo"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_enhanced_system_prompt()
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Slightly higher for creativity
                max_tokens=3000,  # More tokens for detailed recipes
                presence_penalty=0.3,  # Encourage variety
                frequency_penalty=0.2
            )
            
            # Parse and enhance the response
            content = response.choices[0].message.content
            recipe = self._parse_enhanced_response(content)
            
            if recipe:
                # Add additional metadata
                self._enhance_recipe_metadata(recipe, ingredients, context)
                
            return recipe
            
        except Exception as e:
            logger.error(f"Error generating single recipe: {str(e)}")
            return None
    
    def _get_enhanced_system_prompt(self) -> str:
        """Get an enhanced system prompt for better recipe generation"""
        
        return """You are a Michelin-starred chef and nutritionist with expertise in:
- Creating innovative, delicious recipes from available ingredients
- Ensuring perfect flavor balance and texture combinations
- Adapting recipes for dietary restrictions and allergens
- Providing clear, detailed cooking instructions for all skill levels
- Optimizing nutritional value while maintaining taste
- Suggesting creative substitutions and variations
- Understanding cultural authenticity in various cuisines

Your recipes should be:
1. Practical and achievable with common kitchen equipment
2. Detailed enough for beginners but interesting for experienced cooks
3. Nutritionally balanced and satisfying
4. Creative while respecting traditional techniques
5. Safe for all specified dietary restrictions

Always provide exact measurements, specific temperatures, and precise timing."""
    
    def _build_enhanced_prompt(
        self,
        ingredients: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Build an enhanced prompt for recipe generation"""
        
        # Start with available ingredients
        prompt = f"""Create a {context.get('style', 'delicious')} recipe using these available ingredients:
PRIMARY INGREDIENTS: {', '.join(ingredients[:15])}

RECIPE REQUIREMENTS:
"""
        
        # Add allergen requirements if any
        if context.get('allergens'):
            prompt += f"""
CRITICAL ALLERGEN RESTRICTIONS:
This recipe MUST NOT contain ANY of these allergens or derivatives:
{', '.join(context['allergens'])}
Double-check every ingredient for hidden allergens.
"""
        
        # Add dietary preferences
        if context.get('dietary_preferences'):
            prompt += f"""
DIETARY REQUIREMENTS: {', '.join(context['dietary_preferences'])}
"""
        
        # Add meal context
        meal_type = context.get('meal_type', 'any meal')
        prompt += f"""
MEAL TYPE: {meal_type}
COOKING TIME: Maximum {context.get('cooking_time', 45)} minutes
SERVINGS: {context.get('serving_size', 4)} people
SKILL LEVEL: {context.get('skill_level', 'intermediate')}
"""
        
        # Add flavor and cuisine preferences
        if context.get('cuisine_preference'):
            prompt += f"CUISINE STYLE: {context['cuisine_preference']}\n"
        
        if context.get('flavor'):
            prompt += f"FLAVOR PROFILE: {context['flavor']}\n"
        
        # Add specific instructions for JSON format
        prompt += """

Please provide a detailed recipe in the following JSON format:
{
    "title": "Creative Recipe Name",
    "tagline": "Enticing one-line description",
    "description": "Detailed 2-3 sentence description of the dish",
    "readyInMinutes": 30,
    "preparationMinutes": 10,
    "cookingMinutes": 20,
    "servings": 4,
    "difficulty": "intermediate",
    "cuisineType": ["cuisine1", "cuisine2"],
    "dishType": ["main course"],
    "dietaryInfo": {
        "vegetarian": false,
        "vegan": false,
        "glutenFree": true,
        "dairyFree": true,
        "allergenFree": ["dairy", "gluten"]
    },
    "flavorProfile": {
        "primary": "savory",
        "secondary": ["umami", "slightly spicy"],
        "aromatics": ["garlic", "ginger"]
    },
    "ingredients": [
        {
            "name": "chicken breast",
            "amount": 1.5,
            "unit": "pounds",
            "preparation": "cut into bite-sized pieces",
            "category": "protein",
            "optional": false
        }
    ],
    "equipment": ["large skillet", "cutting board", "knife"],
    "instructions": [
        {
            "step": 1,
            "action": "Prepare ingredients",
            "details": "Cut chicken into bite-sized pieces...",
            "duration": "5 minutes",
            "tips": "For even cooking, cut pieces uniformly"
        }
    ],
    "nutritionEstimate": {
        "calories": 350,
        "protein": 35,
        "carbs": 20,
        "fat": 15,
        "fiber": 3
    },
    "tips": {
        "storage": "Store in airtight container for up to 3 days",
        "reheating": "Reheat gently to avoid drying out",
        "serving": "Serve with rice or noodles",
        "variations": ["Add vegetables", "Try with tofu instead"]
    },
    "usedIngredients": ["chicken", "garlic", ...],
    "missingIngredients": ["soy sauce", ...],
    "winePairing": "Light white wine or sake",
    "seasonalNote": "Great for any season"
}

Make the recipe creative, delicious, and perfectly suited to the requirements!"""
        
        return prompt
    
    def _parse_enhanced_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse enhanced recipe response with better error handling"""
        
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                recipe = json.loads(json_str)
                
                # Validate and standardize format
                recipe = self._standardize_recipe_format(recipe)
                
                return recipe
            else:
                logger.error("No JSON found in response")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            # Try to fix common JSON errors
            try:
                # Remove trailing commas
                json_str = response[start_idx:end_idx]
                json_str = json_str.replace(',]', ']').replace(',}', '}')
                recipe = json.loads(json_str)
                return self._standardize_recipe_format(recipe)
            except:
                return None
        except Exception as e:
            logger.error(f"Error parsing enhanced response: {e}")
            return None
    
    def _standardize_recipe_format(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize recipe format for compatibility"""
        
        # Ensure required fields
        recipe['title'] = recipe.get('title', 'Delicious Recipe')
        recipe['readyInMinutes'] = recipe.get('readyInMinutes', 30)
        
        # Convert ingredients to both formats
        if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
            extended_ingredients = []
            
            for ing in recipe['ingredients']:
                if isinstance(ing, dict):
                    # Enhanced format
                    extended_ingredients.append({
                        'original': f"{ing.get('amount', '')} {ing.get('unit', '')} {ing.get('name', '')} {ing.get('preparation', '')}".strip(),
                        'name': ing.get('name', ''),
                        'amount': ing.get('amount', 0),
                        'unit': ing.get('unit', ''),
                        'meta': [ing.get('preparation', '')] if ing.get('preparation') else []
                    })
                else:
                    # Simple string format
                    extended_ingredients.append({'original': ing})
            
            recipe['extendedIngredients'] = extended_ingredients
        
        # Convert instructions
        if 'instructions' in recipe:
            if isinstance(recipe['instructions'], list):
                steps = []
                for i, inst in enumerate(recipe['instructions']):
                    if isinstance(inst, dict):
                        steps.append({
                            'number': inst.get('step', i+1),
                            'step': f"{inst.get('action', '')}: {inst.get('details', '')}".strip()
                        })
                    else:
                        steps.append({
                            'number': i+1,
                            'step': inst
                        })
                
                recipe['analyzedInstructions'] = [{'steps': steps}]
        
        # Add cuisine type if not present
        if 'cuisineType' not in recipe:
            recipe['cuisineType'] = ['International']
        
        # Ensure it's a list
        if isinstance(recipe.get('cuisineType'), str):
            recipe['cuisineType'] = [recipe['cuisineType']]
        
        return recipe
    
    def _enhance_recipe_metadata(
        self,
        recipe: Dict[str, Any],
        ingredients: List[str],
        context: Dict[str, Any]
    ):
        """Add additional metadata to enhance the recipe"""
        
        # Add allergen safety confirmation
        if context.get('allergens'):
            recipe['allergen_safe'] = True
            recipe['excluded_allergens'] = context['allergens']
        
        # Calculate ingredient match percentage
        used_ingredients = recipe.get('usedIngredients', [])
        if used_ingredients:
            match_percentage = len(used_ingredients) / len(ingredients) * 100
            recipe['ingredient_match'] = round(match_percentage, 1)
        
        # Add meal type tags
        recipe['mealTypes'] = [context.get('meal_type', 'main course')]
        
        # Add preparation difficulty
        if 'difficulty' not in recipe:
            total_time = recipe.get('readyInMinutes', 30)
            if total_time < 20:
                recipe['difficulty'] = 'easy'
            elif total_time < 45:
                recipe['difficulty'] = 'intermediate'
            else:
                recipe['difficulty'] = 'advanced'
        
        # Add seasonal information
        recipe['seasonal'] = self._determine_seasonality(recipe)
        
        # Add cost estimate
        recipe['costEstimate'] = self._estimate_cost(recipe)
    
    def _calculate_quality_score(
        self,
        recipe: Dict[str, Any],
        available_ingredients: List[str],
        context: Dict[str, Any]
    ) -> float:
        """Calculate a quality score for ranking recipes"""
        
        score = 0.0
        
        # Ingredient usage (max 30 points)
        used_count = len(recipe.get('usedIngredients', []))
        available_count = len(available_ingredients)
        if available_count > 0:
            score += (used_count / available_count) * 30
        
        # Nutritional balance (max 20 points)
        nutrition = recipe.get('nutritionEstimate', {})
        if nutrition:
            # Check for balanced macros
            protein = nutrition.get('protein', 0)
            if 20 <= protein <= 40:
                score += 10
            
            # Fiber content
            fiber = nutrition.get('fiber', 0)
            if fiber >= 3:
                score += 10
        
        # Time efficiency (max 20 points)
        cook_time = recipe.get('readyInMinutes', 60)
        max_time = context.get('cooking_time', 60)
        if cook_time <= max_time:
            score += 20 * (1 - cook_time / max_time)
        
        # Dietary compliance (max 15 points)
        if recipe.get('allergen_safe'):
            score += 15
        
        # Flavor complexity (max 15 points)
        flavor_profile = recipe.get('flavorProfile', {})
        if flavor_profile.get('secondary'):
            score += min(len(flavor_profile['secondary']) * 5, 15)
        
        return min(score, 100)  # Cap at 100
    
    def _determine_seasonality(self, recipe: Dict[str, Any]) -> str:
        """Determine seasonal appropriateness of recipe"""
        
        # Simple heuristic based on ingredients
        ingredients_str = ' '.join([
            ing.get('name', '') for ing in recipe.get('extendedIngredients', [])
        ]).lower()
        
        summer_keywords = ['tomato', 'basil', 'corn', 'zucchini', 'berries']
        winter_keywords = ['squash', 'potato', 'root', 'hearty', 'stew']
        
        summer_count = sum(1 for k in summer_keywords if k in ingredients_str)
        winter_count = sum(1 for k in winter_keywords if k in ingredients_str)
        
        if summer_count > winter_count:
            return "Best in summer"
        elif winter_count > summer_count:
            return "Perfect for winter"
        else:
            return "Year-round favorite"
    
    def _estimate_cost(self, recipe: Dict[str, Any]) -> str:
        """Estimate recipe cost category"""
        
        # Simple estimation based on ingredients
        expensive_ingredients = ['beef', 'salmon', 'shrimp', 'cheese', 'nuts']
        budget_ingredients = ['beans', 'rice', 'pasta', 'potato', 'chicken']
        
        ingredients_str = ' '.join([
            ing.get('name', '') for ing in recipe.get('extendedIngredients', [])
        ]).lower()
        
        expensive_count = sum(1 for ing in expensive_ingredients if ing in ingredients_str)
        budget_count = sum(1 for ing in budget_ingredients if ing in ingredients_str)
        
        if expensive_count >= 2:
            return "$$$ (Higher cost)"
        elif budget_count >= 2:
            return "$ (Budget-friendly)"
        else:
            return "$$ (Moderate)"
    
    async def generate_creative_variations(
        self,
        base_recipe: Dict[str, Any],
        variations_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate creative variations of a base recipe"""
        
        variations = []
        
        variation_types = [
            "vegetarian version",
            "spicier version",
            "low-carb adaptation",
            "fusion twist",
            "gourmet upgrade"
        ]
        
        for i in range(min(variations_count, len(variation_types))):
            prompt = f"""Create a {variation_types[i]} of this recipe:
Title: {base_recipe.get('title')}
Main ingredients: {', '.join(base_recipe.get('usedIngredients', [])[:5])}

Provide a brief JSON with:
- title: New recipe name
- changes: List of key modifications
- description: Why this variation is special
"""
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a creative chef."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.9,
                    max_tokens=500
                )
                
                variation_content = response.choices[0].message.content
                # Parse and add to variations
                # ... parsing logic ...
                
            except Exception as e:
                logger.error(f"Error generating variation: {e}")
        
        return variations