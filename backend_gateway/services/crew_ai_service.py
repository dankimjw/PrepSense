import os
import logging
from typing import List, Dict, Any
from datetime import datetime
import openai

# Try to import CrewAI, but don't fail if it's not installed
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = Process = None

from backend_gateway.services.bigquery_service import BigQueryService
from backend_gateway.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)

class CrewAIService:
    def __init__(self):
        """Initialize the CrewAI service with necessary components."""
        self.bq_service = BigQueryService()
        self.recipe_service = RecipeService()
        
        # Initialize OpenAI
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize agents only if CrewAI is available
        if CREWAI_AVAILABLE:
            self._initialize_agents()
        else:
            logger.warning("CrewAI not installed. Using simplified chat service.")
    
    def _initialize_agents(self):
        """Initialize all the CrewAI agents."""
        
        # Pantry Scan Agent
        self.pantry_scan_agent = Agent(
            role='Pantry Scanner',
            goal='Fetch and identify all available items in the user\'s pantry',
            backstory='You are an expert at quickly scanning and cataloging pantry items.',
            verbose=True,
            allow_delegation=False
        )
        
        # Filter Agent
        self.filter_agent = Agent(
            role='Expiration Checker',
            goal='Filter out expired items from the pantry list',
            backstory='You are meticulous about food safety and expiration dates.',
            verbose=True,
            allow_delegation=False
        )
        
        # Recipe Search Agent
        self.recipe_search_agent = Agent(
            role='Recipe Finder',
            goal='Find recipes that can be made with available pantry items',
            backstory='You are a culinary expert who can suggest creative recipes.',
            verbose=True,
            allow_delegation=False
        )
        
        # Nutritional Agent
        self.nutritional_agent = Agent(
            role='Nutritionist',
            goal='Evaluate the nutritional content of recipes',
            backstory='You are a certified nutritionist focused on balanced meals.',
            verbose=True,
            allow_delegation=False
        )
        
        # Preference Agent
        self.preference_agent = Agent(
            role='Dietary Preference Checker',
            goal='Ensure recipes match user dietary preferences',
            backstory='You understand various dietary restrictions and preferences.',
            verbose=True,
            allow_delegation=False
        )
        
        # Decision Agent
        self.decision_agent = Agent(
            role='Recipe Recommender',
            goal='Select and format the best recipe recommendations',
            backstory='You are an expert at making final recipe recommendations.',
            verbose=True,
            allow_delegation=False
        )
    
    async def process_message(self, user_id: int, message: str, use_preferences: bool = True) -> Dict[str, Any]:
        """
        Process a chat message and return recipe recommendations.
        
        Args:
            user_id: The user's ID
            message: The user's message
            
        Returns:
            Dict containing response, recipes, and pantry items
        """
        if not CREWAI_AVAILABLE:
            # Use simplified fallback implementation
            logger.info("Using fallback chat implementation")
            return await self._fallback_process_message(user_id, message)
            
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
            
            # Step 3: Search for recipes based on message context and preferences
            recipes = await self._search_recipes(valid_items, message, user_preferences)
            
            # Step 4: Evaluate and rank recipes with enjoyment scores
            ranked_recipes = self._rank_recipes(recipes, valid_items, user_preferences)
            
            # Step 5: Format response
            response = self._format_response(ranked_recipes, valid_items, message, user_preferences)
            
            return {
                "response": response,
                "recipes": ranked_recipes[:5],  # Top 5 recipes for more variety
                "pantry_items": valid_items,
                "user_preferences": user_preferences
            }
            
        except Exception as e:
            logger.error(f"Error in CrewAI service: {str(e)}")
            raise
    
    async def _fetch_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch pantry items from BigQuery."""
        logger.info(f"Fetching pantry items for user_id: {user_id}")
        
        query = """
            SELECT *
            FROM `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
            WHERE user_id = @user_id
            ORDER BY expiration_date ASC
        """
        params = {"user_id": user_id}
        
        results = self.bq_service.execute_query(query, params)
        logger.info(f"Found {len(results)} pantry items for user {user_id}")
        
        # Log the product names for debugging
        if results:
            product_names = [item.get('product_name', 'Unknown') for item in results[:5]]
            logger.info(f"Sample items: {product_names}")
        
        return results
    
    async def _fetch_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Fetch user preferences from BigQuery."""
        logger.info(f"Fetching preferences for user_id: {user_id}")
        
        query = """
            SELECT *
            FROM `adsp-34002-on02-prep-sense.Inventory.user_preference`
            WHERE user_id = @user_id
            LIMIT 1
        """
        params = {"user_id": user_id}
        
        results = self.bq_service.execute_query(query, params)
        if results:
            preferences = results[0]
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
    
    async def _search_recipes(self, pantry_items: List[Dict[str, Any]], message: str, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recipes dynamically using OpenAI based on pantry items, user message, and preferences."""
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
        prompt = f"""
        You are a creative chef. Generate 5-8 recipes based on ONLY these available ingredients:
        {', '.join(available_ingredients)}
        
        User request: {message}
        
        IMPORTANT User Preferences:
        - Dietary restrictions: {', '.join(dietary_prefs) if dietary_prefs else 'None'}
        - Allergens to avoid: {', '.join(allergens) if allergens else 'None'}
        - Favorite cuisines: {', '.join(cuisine_prefs) if cuisine_prefs else 'Any'}
        
        CRITICAL INSTRUCTIONS:
        1. Create at least 2-3 recipes that use ONLY ingredients from the available list above
        2. Create 3-4 recipes that need 1-3 additional common ingredients (specify exactly what's needed)
        3. DO NOT assume common pantry items are available unless they're in the list
        4. For recipes needing extra ingredients, be specific (e.g., "eggs", "flour", "garlic cloves")
        
        Return a JSON array of recipes. Each recipe should have:
        - name: string (creative recipe name)
        - ingredients: array of strings (ONLY use exact ingredients from the available list, or clearly specify additional needed items)
        - nutrition: object with calories (number) and protein (number in grams)
        - time: number (cooking time in minutes)
        - meal_type: string (breakfast, lunch, dinner, or snack)
        - cuisine_type: string (e.g., italian, mexican, asian, american)
        - dietary_tags: array of strings (e.g., vegetarian, vegan, gluten-free)
        
        Example format:
        - For available ingredient: "Chicken Breast" (exactly as shown in list)
        - For missing ingredient: "eggs" (specific item needed)
        
        CRITICAL: Exclude any recipes containing allergens the user must avoid.
        Focus on recipes that match dietary preferences and favorite cuisines when possible.
        
        Return ONLY the JSON array, no other text.
        """
        
        try:
            # Use OpenAI to generate recipes
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful chef that creates recipes. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            # Parse the response
            import json
            recipes_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON if there's extra text
            if recipes_text.startswith('```json'):
                recipes_text = recipes_text[7:]
            if recipes_text.endswith('```'):
                recipes_text = recipes_text[:-3]
            
            all_recipes = json.loads(recipes_text)
            logger.info(f"Generated {len(all_recipes)} recipes using OpenAI")
            
        except Exception as e:
            logger.error(f"Error generating recipes with OpenAI: {str(e)}")
            # Fallback to some basic recipes if OpenAI fails
            all_recipes = [
            # Breakfast recipes
            {
                'name': 'Banana Smoothie',
                'ingredients': ['bananas', 'milk'],
                'nutrition': {'calories': 200, 'protein': 8},
                'time': 5,
                'meal_type': 'breakfast'
            },
            {
                'name': 'Chicken and Milk Scramble',
                'ingredients': ['chicken breast', 'milk', 'eggs'],
                'nutrition': {'calories': 350, 'protein': 30},
                'time': 15,
                'meal_type': 'breakfast'
            },
            # Lunch/Dinner recipes
            {
                'name': 'Simple Grilled Chicken',
                'ingredients': ['chicken breast', 'salt', 'pepper'],
                'nutrition': {'calories': 300, 'protein': 35},
                'time': 20,
                'meal_type': 'dinner'
            },
            {
                'name': 'Chicken Milk Soup',
                'ingredients': ['chicken breast', 'milk', 'onion'],
                'nutrition': {'calories': 250, 'protein': 25},
                'time': 25,
                'meal_type': 'dinner'
            },
            {
                'name': 'Banana Chicken Stir-fry',
                'ingredients': ['chicken breast', 'bananas', 'soy sauce'],
                'nutrition': {'calories': 400, 'protein': 30},
                'time': 18,
                'meal_type': 'dinner'
            },
            # More complex recipes
            {
                'name': 'Pasta with Tomato Sauce',
                'ingredients': ['pasta', 'tomatoes', 'garlic', 'olive oil'],
                'nutrition': {'calories': 450, 'protein': 15},
                'time': 30,
                'meal_type': 'dinner'
            },
            {
                'name': 'Chicken Caesar Salad',
                'ingredients': ['chicken breast', 'lettuce', 'parmesan', 'caesar dressing'],
                'nutrition': {'calories': 350, 'protein': 28},
                'time': 15,
                'meal_type': 'lunch'
            },
            {
                'name': 'Pancakes',
                'ingredients': ['milk', 'flour', 'eggs', 'sugar'],
                'nutrition': {'calories': 300, 'protein': 10},
                'time': 20,
                'meal_type': 'breakfast'
            },
            # Additional recipes with common ingredients
            {
                'name': 'Scrambled Eggs',
                'ingredients': ['eggs', 'butter', 'milk'],
                'nutrition': {'calories': 180, 'protein': 12},
                'time': 10,
                'meal_type': 'breakfast'
            },
            {
                'name': 'Rice Bowl',
                'ingredients': ['rice', 'vegetables', 'soy sauce'],
                'nutrition': {'calories': 350, 'protein': 8},
                'time': 25,
                'meal_type': 'dinner'
            },
            {
                'name': 'Vegetable Stir Fry',
                'ingredients': ['vegetables', 'oil', 'garlic', 'soy sauce'],
                'nutrition': {'calories': 200, 'protein': 5},
                'time': 15,
                'meal_type': 'dinner'
            },
            {
                'name': 'Fruit Salad',
                'ingredients': ['apples', 'bananas', 'oranges'],
                'nutrition': {'calories': 150, 'protein': 2},
                'time': 10,
                'meal_type': 'breakfast'
            },
            {
                'name': 'Toast with Butter',
                'ingredients': ['bread', 'butter'],
                'nutrition': {'calories': 150, 'protein': 4},
                'time': 5,
                'meal_type': 'breakfast'
            },
            {
                'name': 'Simple Omelette',
                'ingredients': ['eggs', 'cheese', 'butter'],
                'nutrition': {'calories': 250, 'protein': 18},
                'time': 10,
                'meal_type': 'breakfast'
            }
            ]
        
        # Filter recipes based on message context if needed
        filtered_recipes = []
        message_lower = message.lower()
        
        # If user specified a meal type, filter accordingly
        if 'breakfast' in message_lower:
            filtered_recipes = [r for r in all_recipes if r.get('meal_type') == 'breakfast']
        elif 'lunch' in message_lower:
            filtered_recipes = [r for r in all_recipes if r.get('meal_type') == 'lunch']
        elif 'dinner' in message_lower:
            filtered_recipes = [r for r in all_recipes if r.get('meal_type') == 'dinner']
        else:
            # Return all recipes if no specific meal mentioned
            filtered_recipes = all_recipes
        
        # If no recipes match the filter, return all recipes
        if not filtered_recipes:
            filtered_recipes = all_recipes
            
        return filtered_recipes
    
    def _rank_recipes(self, recipes: List[Dict[str, Any]], pantry_items: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank recipes based on available ingredients, preferences, and calculate enjoyment score."""
        pantry_names = {item['product_name'].lower() for item in pantry_items if item.get('product_name')}
        
        # Get user preferences
        dietary_prefs = set(p.lower() for p in user_preferences.get('dietary_preference', []))
        cuisine_prefs = set(c.lower() for c in user_preferences.get('cuisine_preference', []))
        allergens = set(a.lower() for a in user_preferences.get('allergens', []))
        
        # Log pantry items for debugging
        logger.info(f"Pantry items for matching: {list(pantry_names)[:10]}")
        
        for recipe in recipes:
            recipe_ingredients = recipe.get('ingredients', [])
            available_ingredients = []
            missing_ingredients = []
            
            for ingredient in recipe_ingredients:
                ingredient_lower = ingredient.lower()
                
                # Check for exact match or partial match
                found = False
                for pantry_item in pantry_names:
                    # First check for exact match (case-insensitive)
                    if ingredient_lower == pantry_item:
                        available_ingredients.append(ingredient)
                        found = True
                        break
                    # Then check if ingredient is in pantry item name or vice versa
                    elif (ingredient_lower in pantry_item or 
                          pantry_item in ingredient_lower or
                          self._is_similar_ingredient(ingredient_lower, pantry_item)):
                        available_ingredients.append(ingredient)
                        found = True
                        break
                
                if not found:
                    missing_ingredients.append(ingredient)
            
            recipe['available_ingredients'] = available_ingredients
            recipe['missing_ingredients'] = missing_ingredients
            recipe['missing_count'] = len(missing_ingredients)
            recipe['available_count'] = len(available_ingredients)
            recipe['match_score'] = len(available_ingredients) / len(recipe_ingredients) if recipe_ingredients else 0
            
            # Calculate expected joy score (0-100)
            joy_score = 50  # Base score
            
            # Boost if it matches cuisine preferences
            recipe_cuisine = recipe.get('cuisine_type', '').lower()
            if recipe_cuisine and recipe_cuisine in cuisine_prefs:
                joy_score += 20
            
            # Boost if it matches dietary preferences
            recipe_dietary = set(tag.lower() for tag in recipe.get('dietary_tags', []))
            if dietary_prefs and recipe_dietary.intersection(dietary_prefs):
                joy_score += 15
            
            # Penalty if it contains allergens
            recipe_ingredients_lower = set(ing.lower() for ing in recipe_ingredients)
            contains_allergens = [allergen for allergen in allergens if any(allergen in ing for ing in recipe_ingredients_lower)]
            if contains_allergens:
                joy_score -= 50  # Major penalty for allergens
                recipe['allergens_present'] = contains_allergens
            else:
                recipe['allergens_present'] = []
            
            # Boost based on ingredient availability
            joy_score += int(recipe['match_score'] * 15)
            
            # Ensure score is between 0 and 100
            recipe['expected_joy'] = max(0, min(100, joy_score))
            
            # Track which preferences were matched
            recipe['matched_preferences'] = []
            if recipe_cuisine and recipe_cuisine in cuisine_prefs:
                recipe['matched_preferences'].append(f"{recipe_cuisine} cuisine")
            if dietary_prefs and recipe_dietary.intersection(dietary_prefs):
                recipe['matched_preferences'].extend(list(recipe_dietary.intersection(dietary_prefs)))
        
        # Sort by joy score first, then by missing ingredients
        return sorted(recipes, key=lambda x: (-x.get('expected_joy', 0), x.get('missing_count', 999)))
    
    def _is_similar_ingredient(self, ingredient1: str, ingredient2: str) -> bool:
        """Check if two ingredients are similar (e.g., 'chicken' and 'chicken breast')."""
        # Common ingredient variations
        similar_pairs = [
            ('chicken', 'chicken breast'),
            ('chicken', 'chicken thigh'),
            ('milk', 'whole milk'),
            ('milk', '2% milk'),
            ('banana', 'bananas'),
            ('egg', 'eggs'),
            ('onion', 'onions'),
            ('salt', 'sea salt'),
            ('pepper', 'black pepper'),
            ('rice', 'long-grain white rice'),
            ('beans', 'black beans'),
            ('olive oil', 'extra-virgin olive oil'),
            ('oil', 'olive oil'),
        ]
        
        # Check direct pairs
        for pair in similar_pairs:
            if (ingredient1 in pair and ingredient2 in pair) or \
               (ingredient2 in pair and ingredient1 in pair):
                return True
        
        # Check if one is a substring of the other (for things like "black beans – 15 oz")
        if ingredient1 in ingredient2 or ingredient2 in ingredient1:
            return True
        
        return False
    
    def _format_response(self, recipes: List[Dict[str, Any]], items: List[Dict[str, Any]], message: str, user_preferences: Dict[str, Any]) -> str:
        """Format the final response message with preference info."""
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
        
        if wants_available_only:
            # Filter for recipes with no missing ingredients
            perfect_match_recipes = [r for r in recipes if r.get('missing_count', 0) == 0]
            if perfect_match_recipes:
                response = f"Here are recipes you can make with only your current pantry items!{pref_text}"
            else:
                response = f"No recipes can be made with only your current ingredients. Here are the recipes requiring the fewest additional items.{pref_text}"
        else:
            response = f"Based on your pantry items, here are my recommendations!{pref_text}"
        
        return response
    
    async def _fallback_process_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """Fallback implementation when CrewAI is not available."""
        try:
            # Fetch pantry items
            pantry_items = await self._fetch_pantry_items(user_id)
            
            # Get some recipe suggestions based on message
            if not pantry_items:
                return {
                    "response": "I notice your pantry is empty. Would you like me to suggest some essential items to stock up on?",
                    "recipes": [],
                    "pantry_items": []
                }
            
            # Simple keyword matching for dinner suggestions
            message_lower = message.lower()
            if any(word in message_lower for word in ['dinner', 'lunch', 'breakfast', 'meal', 'cook', 'make']):
                # Get ingredient names
                ingredients = []
                for item in pantry_items[:10]:  # Limit to 10 items
                    if item.get('product_name'):
                        ingredients.append(item['product_name'])
                
                # Generate simple response
                response = f"Based on your pantry items, you could make something with: {', '.join(ingredients[:5])}. "
                response += "Try combining these ingredients for a quick meal!"
                
                # Return simplified recipe suggestions
                simple_recipes = [
                    {
                        "name": "Quick Stir-fry",
                        "description": "Combine your vegetables and proteins in a pan",
                        "ingredients": ingredients[:3]
                    },
                    {
                        "name": "Simple Pasta",
                        "description": "Use your pasta and any vegetables or sauces",
                        "ingredients": ingredients[:4]
                    }
                ]
                
                return {
                    "response": response,
                    "recipes": simple_recipes,
                    "pantry_items": pantry_items[:10]
                }
            else:
                # General response
                return {
                    "response": f"You currently have {len(pantry_items)} items in your pantry. What would you like to know about them?",
                    "recipes": [],
                    "pantry_items": pantry_items[:10]
                }
                
        except Exception as e:
            logger.error(f"Error in fallback chat: {str(e)}")
            return {
                "response": "I'm having trouble accessing your pantry data. Please try again later.",
                "recipes": [],
                "pantry_items": []
            }