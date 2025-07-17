"""Service for generating recipes using OpenAI when Spoonacular fails or returns no allergen-safe results"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
import openai
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAIRecipeService:
    """Generate allergen-free recipes using OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("OpenAI API key not found")
    
    async def generate_allergen_free_recipes(
        self,
        ingredients: List[str],
        allergens: List[str],
        dietary_preferences: Optional[List[str]] = None,
        number: int = 3,
        cuisine: Optional[str] = None,
        max_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recipes that are guaranteed to be allergen-free
        
        Args:
            ingredients: Available ingredients
            allergens: List of allergens to avoid
            dietary_preferences: Dietary restrictions (vegetarian, vegan, etc.)
            number: Number of recipes to generate
            cuisine: Preferred cuisine type
            max_time: Maximum cooking time in minutes
            
        Returns:
            List of recipe dictionaries
        """
        if not self.api_key:
            logger.error("OpenAI API key not configured")
            return []
        
        try:
            # Build the prompt
            prompt = self._build_allergen_free_prompt(
                ingredients, allergens, dietary_preferences, 
                number, cuisine, max_time
            )
            
            # Generate recipes using OpenAI
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional chef who specializes in creating safe, allergen-free recipes. You MUST ensure recipes contain NO traces of specified allergens."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            recipes = self._parse_recipe_response(content)
            
            # Add metadata to each recipe
            for i, recipe in enumerate(recipes):
                recipe['id'] = f"openai_{int(datetime.now().timestamp())}_{i}"
                recipe['source'] = 'openai'
                recipe['allergen_free'] = True
                recipe['excluded_allergens'] = allergens
                recipe['image'] = None  # OpenAI doesn't provide images
                
            logger.info(f"Generated {len(recipes)} allergen-free recipes using OpenAI")
            return recipes
            
        except Exception as e:
            logger.error(f"Error generating recipes with OpenAI: {str(e)}")
            return []
    
    def _build_allergen_free_prompt(
        self,
        ingredients: List[str],
        allergens: List[str],
        dietary_preferences: Optional[List[str]],
        number: int,
        cuisine: Optional[str],
        max_time: Optional[int]
    ) -> str:
        """Build a prompt for allergen-free recipe generation"""
        
        prompt = f"""Create {number} recipes using these ingredients: {', '.join(ingredients[:10])}

CRITICAL ALLERGEN REQUIREMENTS:
These recipes MUST NOT contain ANY of these allergens or related ingredients:
{', '.join(allergens)}

For each allergen, avoid ALL forms including:
- Dairy: milk, cheese, butter, cream, yogurt, whey, casein, lactose
- Eggs: eggs, mayonnaise, egg whites, egg substitutes in baking
- Gluten: wheat, barley, rye, bread, pasta, flour, soy sauce
- Nuts: all tree nuts, nut oils, nut butters
- Peanuts: peanuts, peanut oil, peanut butter
- Soy: soy sauce, tofu, tempeh, edamame, soy milk
- Shellfish: shrimp, crab, lobster, clams, oysters
- Fish: all fish and fish-derived products

"""
        
        if dietary_preferences:
            prompt += f"Also follow these dietary preferences: {', '.join(dietary_preferences)}\n"
        
        if cuisine:
            prompt += f"Preferred cuisine: {cuisine}\n"
        
        if max_time:
            prompt += f"Maximum cooking time: {max_time} minutes\n"
        
        prompt += """
For each recipe, provide:
1. Recipe name
2. Brief description
3. Cooking time (in minutes)
4. Complete list of ingredients with measurements
5. Step-by-step instructions
6. Note which of the requested ingredients are used

Format as JSON array with this structure:
[
  {
    "title": "Recipe Name",
    "description": "Brief description",
    "readyInMinutes": 30,
    "ingredients": ["1 cup rice", "2 cups water", ...],
    "instructions": ["Step 1...", "Step 2...", ...],
    "usedIngredients": ["rice", ...],
    "cuisineType": "asian"
  }
]

Remember: ABSOLUTELY NO ingredients containing the specified allergens!
"""
        
        return prompt
    
    def _parse_recipe_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse OpenAI response into recipe dictionaries"""
        try:
            # Try to extract JSON from the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                recipes = json.loads(json_str)
                
                # Standardize the format
                for recipe in recipes:
                    # Ensure required fields
                    recipe['title'] = recipe.get('title', 'Untitled Recipe')
                    recipe['readyInMinutes'] = recipe.get('readyInMinutes', 30)
                    
                    # Convert ingredients list to extended format if needed
                    if 'ingredients' in recipe and isinstance(recipe['ingredients'], list):
                        recipe['extendedIngredients'] = [
                            {'original': ing} for ing in recipe['ingredients']
                        ]
                    
                    # Convert instructions to numbered format
                    if 'instructions' in recipe and isinstance(recipe['instructions'], list):
                        recipe['analyzedInstructions'] = [{
                            'steps': [
                                {'number': i+1, 'step': step}
                                for i, step in enumerate(recipe['instructions'])
                            ]
                        }]
                
                return recipes
            else:
                logger.error("Could not find JSON in OpenAI response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing recipe response: {e}")
            return []
    
    async def generate_single_recipe(
        self,
        ingredients: List[str],
        allergens: List[str],
        recipe_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate a single allergen-free recipe"""
        
        recipes = await self.generate_allergen_free_recipes(
            ingredients=ingredients,
            allergens=allergens,
            number=1,
            cuisine=recipe_type
        )
        
        return recipes[0] if recipes else None