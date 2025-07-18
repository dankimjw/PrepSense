import os
import logging
import json
from typing import List, Dict, Any
from datetime import datetime
import openai

from backend_gateway.services.recipe_service import RecipeService
from backend_gateway.services.user_recipes_service import UserRecipesService
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

class RecipeAdvisor:
    """Single agent that combines recipe recommendation logic"""
    
    def __init__(self):
        self.role = "Intelligent Recipe Advisor"
        self.goal = "Recommend the best recipes based on pantry items, preferences, and context"
        
    def analyze_pantry(self, pantry_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pantry for insights like expiring items, common ingredients, etc."""
        from datetime import datetime, timedelta
        today = datetime.now().date()
        
        analysis = {
            'total_items': len(pantry_items),
            'expiring_soon': [],
            'expired': [],
            'categories': {},
            'protein_sources': [],
            'staples': []
        }
        
        for item in pantry_items:
            # Check expiration
            if item.get('expiration_date'):
                exp_date = datetime.strptime(str(item['expiration_date']), '%Y-%m-%d').date()
                days_until = (exp_date - today).days
                
                if days_until < 0:
                    analysis['expired'].append(item)
                elif days_until <= 7:
                    analysis['expiring_soon'].append({
                        'name': item['product_name'],
                        'days': days_until,
                        'date': exp_date
                    })
            
            # Categorize items
            product_name = item.get('product_name', '').lower()
            category = item.get('category', 'other')
            
            if category not in analysis['categories']:
                analysis['categories'][category] = []
            analysis['categories'][category].append(product_name)
            
            # Identify proteins
            if any(protein in product_name for protein in ['chicken', 'beef', 'pork', 'fish', 'tofu', 'beans', 'eggs']):
                analysis['protein_sources'].append(product_name)
            
            # Identify staples
            if any(staple in product_name for staple in ['rice', 'pasta', 'bread', 'potato', 'flour']):
                analysis['staples'].append(product_name)
        
        return analysis
    
    def evaluate_recipe_fit(self, recipe: Dict[str, Any], user_preferences: Dict[str, Any], pantry_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate how well a recipe fits the user's needs"""
        evaluation = {
            'uses_expiring': False,
            'nutritional_balance': 'unknown',
            'meal_variety': 'standard',
            'cooking_complexity': 'medium'
        }
        
        # Check if recipe uses expiring ingredients
        recipe_ingredients = ' '.join(recipe.get('ingredients', [])).lower()
        for expiring in pantry_analysis['expiring_soon']:
            if expiring['name'].lower() in recipe_ingredients:
                evaluation['uses_expiring'] = True
                break
        
        # Evaluate nutritional balance (simple check)
        if any(protein in recipe_ingredients for protein in pantry_analysis['protein_sources']):
            if any(veg in recipe_ingredients for veg in ['vegetable', 'salad', 'broccoli', 'carrot', 'spinach']):
                evaluation['nutritional_balance'] = 'good'
            else:
                evaluation['nutritional_balance'] = 'fair'
        
        # Estimate cooking complexity
        instructions = recipe.get('instructions', [])
        if len(instructions) <= 4:
            evaluation['cooking_complexity'] = 'easy'
        elif len(instructions) > 8:
            evaluation['cooking_complexity'] = 'complex'
        
        return evaluation
    
    def generate_advice(self, recipes: List[Dict[str, Any]], pantry_analysis: Dict[str, Any], message: str) -> str:
        """Generate contextual advice about the recipes"""
        advice_parts = []
        
        # Expiring items advice
        if pantry_analysis['expiring_soon'] and 'expir' in message.lower():
            advice_parts.append(f"I found {len(pantry_analysis['expiring_soon'])} items expiring soon and prioritized recipes using them.")
        
        # Variety advice
        if len(set(r.get('cuisine_type', 'various') for r in recipes[:3])) >= 3:
            advice_parts.append("I've included diverse cuisine options for variety.")
        
        # Quick meal advice
        quick_recipes = [r for r in recipes if r.get('time', 999) <= 20]
        if quick_recipes and any(word in message.lower() for word in ['quick', 'fast', 'easy']):
            advice_parts.append(f"I found {len(quick_recipes)} quick recipes (20 min or less).")
        
        return " ".join(advice_parts)


class CrewAIService:
    def __init__(self):
        """Initialize the AI recipe service."""
        self.db_service = get_database_service()
        self.recipe_service = RecipeService()
        self.user_recipes_service = UserRecipesService(self.db_service)
        self.recipe_advisor = RecipeAdvisor()
        
        # Initialize OpenAI
        from backend_gateway.core.config_utils import get_openai_api_key
        openai.api_key = get_openai_api_key()
    
    async def process_message(self, user_id: int, message: str, use_preferences: bool = True) -> Dict[str, Any]:
        """
        Process a chat message and return recipe recommendations.
        
        Args:
            user_id: The user's ID
            message: The user's message
            use_preferences: Whether to use user preferences
            
        Returns:
            Dict containing response, recipes, and pantry items
        """
        try:
            # Step 1: Fetch pantry items and user preferences
            pantry_items = await self._fetch_pantry_items(user_id)
            
            # Only fetch preferences if we're using them
            if use_preferences:
                user_preferences = await self._fetch_user_preferences(user_id)
            else:
                user_preferences = {
                    'dietary_preference': [],
                    'allergens': [],
                    'cuisine_preference': []
                }
            
            # Step 2: Filter non-expired items
            valid_items = self._filter_valid_items(pantry_items)
            
            # Step 3: Use RecipeAdvisor to analyze pantry
            pantry_analysis = self.recipe_advisor.analyze_pantry(pantry_items)
            
            # Step 4: Check saved recipes first
            saved_recipes = await self._get_matching_saved_recipes(user_id, valid_items)
            
            # Step 5: Generate new recipes with AI (fewer if we have saved matches)
            num_ai_recipes = 5 - len(saved_recipes) if len(saved_recipes) < 5 else 2
            ai_recipes = await self._generate_recipes(valid_items, message, user_preferences, num_ai_recipes)
            
            # Step 6: Combine and rank all recipes
            all_recipes = self._combine_recipe_sources(saved_recipes, ai_recipes)
            
            # Step 7: Evaluate recipes with advisor
            for recipe in all_recipes:
                recipe['evaluation'] = self.recipe_advisor.evaluate_recipe_fit(recipe, user_preferences, pantry_analysis)
            
            ranked_recipes = self._rank_recipes(all_recipes, valid_items, user_preferences)
            
            # Step 8: Generate advice and format response
            advice = self.recipe_advisor.generate_advice(ranked_recipes, pantry_analysis, message)
            response = self._format_response(ranked_recipes, valid_items, message, user_preferences)
            
            if advice:
                response = f"{response}\n\n💡 {advice}"
            
            return {
                "response": response,
                "recipes": ranked_recipes[:5],  # Top 5 recipes
                "pantry_items": valid_items,
                "user_preferences": user_preferences
            }
            
        except Exception as e:
            logger.error(f"Error in AI recipe service: {str(e)}")
            raise
    
    async def _fetch_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch pantry items from database."""
        logger.info(f"Fetching pantry items for user_id: {user_id}")
        
        query = """
            SELECT *
            FROM user_pantry_full
            WHERE user_id = %(user_id)s
            ORDER BY expiration_date ASC
        """
        params = {"user_id": user_id}
        
        results = self.db_service.execute_query(query, params)
        logger.info(f"Found {len(results)} pantry items for user {user_id}")
        
        # Log the product names for debugging
        if results:
            product_names = [item.get('product_name', 'Unknown') for item in results[:5]]
            logger.info(f"Sample items: {product_names}")
        
        return results
    
    async def _fetch_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Fetch user preferences from database."""
        logger.info(f"Fetching preferences for user_id: {user_id}")
        
        query = """
            SELECT *
            FROM user_preferences
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        params = {"user_id": user_id}
        
        results = self.db_service.execute_query(query, params)
        if results and results[0].get('preferences'):
            # Extract preferences from JSONB column
            prefs_data = results[0]['preferences']
            preferences = {
                'dietary_preference': prefs_data.get('dietary_restrictions', []),
                'allergens': prefs_data.get('allergens', []),
                'cuisine_preference': prefs_data.get('cuisine_preferences', [])
            }
            logger.info(f"Found preferences: dietary={preferences.get('dietary_preference', [])}, allergens={preferences.get('allergens', [])}")
            return preferences
        else:
            logger.info(f"No preferences found for user {user_id}, using defaults")
            return {
                'dietary_preference': [],
                'allergens': [],
                'cuisine_preference': []
            }
    
    def _filter_valid_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out expired items."""
        today = datetime.now().date()
        valid_items = []
        
        for item in items:
            if item.get('expiration_date'):
                exp_date = datetime.strptime(str(item['expiration_date']), '%Y-%m-%d').date()
                if exp_date >= today:
                    valid_items.append(item)
            else:
                # If no expiration date, assume it's valid
                valid_items.append(item)
        
        return valid_items
    
    async def _get_matching_saved_recipes(self, user_id: int, pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get user's saved recipes that match current pantry items."""
        try:
            # Get matching recipes from saved collection
            matched_recipes = await self.user_recipes_service.match_recipes_with_pantry(
                user_id=user_id,
                pantry_items=pantry_items,
                limit=5
            )
            
            # Convert to standard recipe format
            standardized_recipes = []
            for recipe in matched_recipes:
                recipe_data = recipe.get('recipe_data', {})
                
                # Extract relevant fields from saved recipe
                standardized = {
                    'name': recipe['title'],
                    'ingredients': recipe_data.get('ingredients', []),
                    'instructions': recipe_data.get('instructions', []),
                    'nutrition': recipe_data.get('nutrition', {'calories': 0, 'protein': 0}),
                    'time': recipe_data.get('time', 30),
                    'meal_type': recipe_data.get('meal_type', 'dinner'),
                    'cuisine_type': recipe_data.get('cuisine_type', 'various'),
                    'dietary_tags': recipe_data.get('dietary_tags', []),
                    'available_ingredients': recipe['matched_ingredients'],
                    'missing_ingredients': recipe['missing_ingredients'],
                    'missing_count': len(recipe['missing_ingredients']),
                    'available_count': len(recipe['matched_ingredients']),
                    'match_score': recipe['match_score'],
                    'allergens_present': [],
                    'matched_preferences': [],
                    'source': 'saved',
                    'saved_recipe_id': recipe['id'],
                    'is_favorite': recipe['is_favorite'],
                    'user_rating': recipe['rating']
                }
                
                standardized_recipes.append(standardized)
            
            logger.info(f"Found {len(standardized_recipes)} matching saved recipes")
            return standardized_recipes
            
        except Exception as e:
            logger.error(f"Error getting saved recipes: {str(e)}")
            return []
    
    async def _generate_recipes(self, pantry_items: List[Dict[str, Any]], message: str, user_preferences: Dict[str, Any], num_recipes: int = 5) -> List[Dict[str, Any]]:
        """Generate recipes using OpenAI based on pantry items, user message, and preferences."""
        # Check if this is an expiring items query
        is_expiring_query = any(phrase in message.lower() for phrase in [
            'expiring', 'expire', 'going bad', 'use soon', 'about to expire'
        ])
        
        # If asking about expiring items, prioritize those
        if is_expiring_query:
            from datetime import datetime, timedelta
            today = datetime.now().date()
            expiring_items = []
            other_items = []
            
            for item in pantry_items:
                if item.get('expiration_date') and item.get('product_name'):
                    exp_date = datetime.strptime(str(item['expiration_date']), '%Y-%m-%d').date()
                    days_until_expiry = (exp_date - today).days
                    if 0 <= days_until_expiry <= 7:
                        expiring_items.append(item['product_name'])
                    else:
                        other_items.append(item['product_name'])
                elif item.get('product_name'):
                    other_items.append(item['product_name'])
            
            # Put expiring items first
            available_ingredients = expiring_items + other_items
            logger.info(f"Expiring items to use: {expiring_items}")
        else:
            # Extract ingredient names from pantry
            available_ingredients = [item['product_name'] for item in pantry_items if item.get('product_name')]
        
        logger.info(f"Available ingredients in pantry: {available_ingredients}")
        
        # Create a normalized ingredient list for the prompt
        normalized_ingredients = []
        for ing in available_ingredients:
            # Remove size/weight info for cleaner prompts
            clean_name = ing.split('–')[0].strip() if '–' in ing else ing
            normalized_ingredients.append(clean_name)
        
        # Extract preferences
        dietary_prefs = user_preferences.get('dietary_preference', [])
        allergens = user_preferences.get('allergens', [])
        cuisine_prefs = user_preferences.get('cuisine_preference', [])
        
        # Create a prompt for OpenAI to generate recipes
        expiring_instruction = ""
        if is_expiring_query and expiring_items:
            expiring_instruction = f"""
        URGENT: These ingredients are EXPIRING SOON and should be used first:
        {', '.join(expiring_items[:10])}
        
        Please prioritize recipes that use these expiring ingredients!
        """
        
        prompt = f"""
        You are a creative chef. Generate {num_recipes} recipes based on ONLY these available ingredients:
        {', '.join(available_ingredients)}
        
        User request: {message}
        {expiring_instruction}
        
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
        
        Return a JSON array of recipes. Each recipe should have:
        - name: string (creative recipe name)
        - ingredients: array of strings with quantities (e.g., "2 cups rice", "1 lb chicken breast", "3 cloves garlic")
        - instructions: array of strings (5-8 detailed step-by-step cooking instructions)
        - nutrition: object with calories (number) and protein (number in grams)
        - time: number (cooking time in minutes)
        - meal_type: string (breakfast, lunch, dinner, or snack)
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
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a creative chef who generates recipes in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            recipes_text = response.choices[0].message.content.strip()
            
            # Clean up the response if it has markdown code blocks
            if recipes_text.startswith('```json'):
                recipes_text = recipes_text[7:]
            if recipes_text.endswith('```'):
                recipes_text = recipes_text[:-3]
            
            all_recipes = json.loads(recipes_text)
            logger.info(f"Generated {len(all_recipes)} recipes using OpenAI")
            
            # Log first recipe to check if instructions are included
            if all_recipes:
                first_recipe = all_recipes[0]
                logger.info(f"First recipe sample: {first_recipe.get('name', 'Unknown')}")
                logger.info(f"Has instructions: {'instructions' in first_recipe}")
                if 'instructions' in first_recipe:
                    logger.info(f"Instructions count: {len(first_recipe['instructions'])}")
            
        except Exception as e:
            logger.error(f"Error generating recipes with OpenAI: {str(e)}")
            # Fallback to some basic recipes if OpenAI fails
            all_recipes = []
        
        # Process recipes to identify available vs missing ingredients
        processed_recipes = []
        pantry_names = [self._clean_ingredient_name(item['product_name']) for item in pantry_items if item.get('product_name')]
        
        for recipe in all_recipes:
            available_ingredients = []
            missing_ingredients = []
            
            # Check each recipe ingredient against pantry
            for ingredient in recipe.get('ingredients', []):
                found = False
                for pantry_item in pantry_names:
                    if self._is_similar_ingredient(pantry_item, ingredient):
                        available_ingredients.append(ingredient)
                        found = True
                        break
                
                if not found:
                    missing_ingredients.append(ingredient)
            
            # Calculate match score and expected joy
            total_ingredients = len(recipe.get('ingredients', []))
            available_count = len(available_ingredients)
            missing_count = len(missing_ingredients)
            match_score = available_count / total_ingredients if total_ingredients > 0 else 0
            
            # Check for allergens
            allergens_present = []
            for allergen in allergens:
                for ingredient in recipe.get('ingredients', []):
                    if self._is_allergen_in_ingredient(allergen, ingredient):
                        allergens_present.append(allergen)
                        break
            
            
            # Add extra fields
            recipe['available_ingredients'] = available_ingredients
            recipe['missing_ingredients'] = missing_ingredients
            recipe['missing_count'] = missing_count
            recipe['available_count'] = available_count
            recipe['match_score'] = round(match_score, 2)
            recipe['allergens_present'] = allergens_present
            
            # Check matched preferences
            matched_prefs = []
            if recipe.get('cuisine_type', '').lower() in [c.lower() for c in cuisine_prefs]:
                matched_prefs.append(f"Cuisine: {recipe['cuisine_type']}")
            for tag in recipe.get('dietary_tags', []):
                if tag.lower() in [d.lower() for d in dietary_prefs]:
                    matched_prefs.append(f"Diet: {tag}")
            recipe['matched_preferences'] = matched_prefs
            
            processed_recipes.append(recipe)
        
        return processed_recipes
    
    def _combine_recipe_sources(self, saved_recipes: List[Dict[str, Any]], ai_recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine saved and AI-generated recipes, removing duplicates."""
        all_recipes = []
        recipe_names = set()
        
        # Add saved recipes first (they're personalized)
        for recipe in saved_recipes:
            recipe_name_lower = recipe['name'].lower().strip()
            if recipe_name_lower not in recipe_names:
                recipe_names.add(recipe_name_lower)
                all_recipes.append(recipe)
        
        # Add AI recipes if they're not duplicates
        for recipe in ai_recipes:
            recipe_name_lower = recipe['name'].lower().strip()
            # Check for similar names
            is_duplicate = False
            for existing_name in recipe_names:
                if recipe_name_lower in existing_name or existing_name in recipe_name_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                recipe_names.add(recipe_name_lower)
                recipe['source'] = 'ai_generated'
                all_recipes.append(recipe)
        
        return all_recipes
    
    def _rank_recipes(self, recipes: List[Dict[str, Any]], pantry_items: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank recipes based on practical factors and advisor evaluation."""
        # Enhanced ranking with advisor insights:
        # 1. Saved recipes the user likes
        # 2. Recipes using expiring ingredients
        # 3. Recipes you can make without shopping
        # 4. Good nutritional balance
        # 5. High match score
        return sorted(recipes, key=lambda r: (
            r.get('source') == 'saved' and r.get('user_rating') == 'thumbs_up',  # User's liked recipes first
            r.get('source') == 'saved' and r.get('is_favorite', False),  # Then favorites
            r.get('evaluation', {}).get('uses_expiring', False),  # Prioritize expiring ingredients
            r.get('missing_count', 999) == 0,  # Recipes you can make now
            r.get('evaluation', {}).get('nutritional_balance') == 'good',  # Well-balanced meals
            r.get('match_score', 0),  # High ingredient match
            -r.get('missing_count', 999)  # Fewer missing ingredients
        ), reverse=True)
    
    
    def _clean_ingredient_name(self, ingredient: str) -> str:
        """Clean ingredient name for better matching."""
        # Remove brand info, sizes, etc.
        cleaned = ingredient.lower().strip()
        
        # Remove size/weight patterns
        import re
        cleaned = re.sub(r'\d+\.?\d*\s*(oz|lb|g|kg|ml|l|cups?|tsp|tbsp|tablespoons?|teaspoons?)', '', cleaned)
        cleaned = re.sub(r'–.*', '', cleaned)  # Remove anything after dash
        cleaned = re.sub(r'\(.*?\)', '', cleaned)  # Remove parentheses
        
        # Remove common modifiers
        modifiers = ['fresh', 'frozen', 'dried', 'canned', 'organic', 'chopped', 'diced', 'sliced', 'minced']
        for mod in modifiers:
            cleaned = cleaned.replace(mod, '')
        
        return cleaned.strip()
    
    def _is_allergen_in_ingredient(self, allergen: str, ingredient: str) -> bool:
        """Check if an allergen is present in an ingredient."""
        allergen_lower = allergen.lower()
        ingredient_lower = ingredient.lower()
        
        # Map common allergens to ingredient patterns
        allergen_patterns = {
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose'],
            'nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'macadamia', 'pine nut'],
            'peanuts': ['peanut'],
            'eggs': ['egg'],
            'soy': ['soy', 'tofu', 'tempeh', 'edamame', 'miso'],
            'gluten': ['wheat', 'flour', 'bread', 'pasta', 'barley', 'rye', 'couscous', 'bulgur'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'scallop', 'oyster', 'clam', 'mussel'],
            'fish': ['salmon', 'tuna', 'cod', 'tilapia', 'bass', 'trout', 'sardine', 'anchovy']
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
            'chicken': ['chicken breast', 'chicken thigh', 'chicken wing'],
            'beef': ['ground beef', 'beef steak', 'beef roast'],
            'tomato': ['tomatoes', 'cherry tomatoes', 'roma tomatoes'],
            'onion': ['onions', 'red onion', 'yellow onion', 'white onion']
        }
        
        for base, variants in variations.items():
            if (base in clean1 or any(v in clean1 for v in variants)) and \
               (base in clean2 or any(v in clean2 for v in variants)):
                return True
        
        return False
    
    def _format_response(self, recipes: List[Dict[str, Any]], items: List[Dict[str, Any]], message: str, user_preferences: Dict[str, Any]) -> str:
        """Format a natural language response based on the recipes found."""
        # Check if this is an expiring items query
        is_expiring_query = any(phrase in message.lower() for phrase in [
            'expiring', 'expire', 'going bad', 'use soon', 'about to expire'
        ])
        
        if is_expiring_query:
            # Find items expiring within 7 days
            from datetime import datetime, timedelta
            today = datetime.now().date()
            expiring_items = []
            
            for item in items:
                if item.get('expiration_date') and item.get('product_name'):
                    exp_date = datetime.strptime(str(item['expiration_date']), '%Y-%m-%d').date()
                    days_until_expiry = (exp_date - today).days
                    if 0 <= days_until_expiry <= 7:
                        expiring_items.append({
                            'name': item['product_name'],
                            'date': exp_date.strftime('%b %d'),
                            'days': days_until_expiry
                        })
            
            if expiring_items:
                # Sort by days until expiry
                expiring_items.sort(key=lambda x: x['days'])
                
                # Remove duplicates based on name
                seen_names = set()
                unique_expiring = []
                for item in expiring_items:
                    if item['name'] not in seen_names:
                        seen_names.add(item['name'])
                        unique_expiring.append(item)
                
                response = f"⚠️ You have {len(unique_expiring)} items expiring soon:\n\n"
                
                # Show up to 10 items
                for item in unique_expiring[:10]:
                    if item['days'] == 0:
                        response += f"• {item['name']} - Expires TODAY!\n"
                    else:
                        response += f"• {item['name']} - Expires in {item['days']} days ({item['date']})\n"
                
                if len(unique_expiring) > 10:
                    response += f"\n...and {len(unique_expiring) - 10} more items.\n"
                
                response += "\n💡 Here are recipes to use these items before they expire:"
                return response
            else:
                return "Great news! 🎉 You don't have any items expiring in the next 7 days. Your pantry is well-managed!"
        
        if not recipes:
            return "I couldn't find any recipes matching your request with your current pantry items. Would you like some shopping suggestions?"
        
        # Check if user wants recipes with only available ingredients
        wants_available_only = any(phrase in message.lower() for phrase in [
            'only ingredients i have', 'what i have', 'without shopping', 
            'available ingredients', 'no missing', 'dont need to buy'
        ])
        
        # Build preference info text
        pref_parts = []
        if user_preferences.get('dietary_preference'):
            pref_parts.append(f"dietary preferences ({', '.join(user_preferences['dietary_preference'])})")
        if user_preferences.get('cuisine_preference'):
            pref_parts.append(f"cuisine preferences ({', '.join(user_preferences['cuisine_preference'])})")
        
        allergen_text = ""
        if user_preferences.get('allergens'):
            allergen_text = f" while excluding allergens ({', '.join(user_preferences['allergens'])})"
        
        pref_text = ""
        if pref_parts or allergen_text:
            if pref_parts:
                pref_text = f" I've considered your {' and '.join(pref_parts)}"
            pref_text += allergen_text + "."
        
        # Check if we have saved recipes
        saved_recipe_count = sum(1 for r in recipes if r.get('source') == 'saved')
        
        if wants_available_only:
            # Filter for recipes with no missing ingredients
            perfect_match_recipes = [r for r in recipes if r.get('missing_count', 0) == 0]
            if perfect_match_recipes:
                response = f"Here are recipes you can make with only your current pantry items!{pref_text}"
            else:
                response = f"No recipes can be made with only your current ingredients. Here are the recipes requiring the fewest additional items.{pref_text}"
        else:
            response = f"Based on your pantry items, here are my recommendations!{pref_text}"
        
        # Add note about saved recipes
        if saved_recipe_count > 0:
            response += f"\n\n✨ Including {saved_recipe_count} recipe{'s' if saved_recipe_count > 1 else ''} from your saved collection!"
        
        return response