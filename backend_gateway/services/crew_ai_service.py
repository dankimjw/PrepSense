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

from backend_gateway.services.recipe_service import RecipeService
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

class CrewAIService:
    def __init__(self):
        """Initialize the CrewAI service with necessary components."""
        self.db_service = get_database_service()
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
        """Fetch user preferences from BigQuery."""
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
    
    async def _search_recipes(self, pantry_items: List[Dict[str, Any]], message: str, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recipes dynamically using OpenAI based on pantry items, user message, and preferences."""
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
        You are a creative chef. Generate 5-8 recipes based on ONLY these available ingredients:
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
        - Include realistic quantities/amounts for each ingredient
        - Use standard measurements (cups, tablespoons, pounds, ounces, etc.)
        - For items from pantry, estimate reasonable amounts
        - Example: "2 chicken breasts", "1 can (14 oz) diced tomatoes", "2 tablespoons olive oil"
        
        IMPORTANT: Instructions should be:
        - Specific with temperatures, times, and techniques
        - Include prep steps (chopping, measuring, etc.)
        - Mention cooking vessels and tools needed
        - Include visual/sensory cues (e.g., "until golden brown", "until fragrant")
        - Be actionable and easy to follow
        
        Example format:
        - For available ingredient: "Chicken Breast" (exactly as shown in list)
        - For missing ingredient: "eggs" (specific item needed)
        
        CRITICAL ALLERGEN RULES:
        - You MUST exclude ANY recipe that contains the allergens listed above
        - If allergens include "nuts", exclude ALL tree nuts and peanuts
        - If allergens include "dairy", exclude milk, cheese, yogurt, butter, cream
        - If allergens include "gluten", exclude wheat, bread, pasta, flour
        - Double-check every ingredient against the allergen list
        
        PREFERENCE RULES:
        - Prioritize recipes that match the user's favorite cuisines
        - Ensure recipes comply with dietary restrictions (e.g., if vegetarian, no meat)
        
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
            all_recipes = [
            # Breakfast recipes
            {
                'name': 'Banana Smoothie',
                'ingredients': ['2 ripe bananas', '1 cup milk', '1 tablespoon honey (optional)', 'pinch of cinnamon (optional)'],
                'instructions': [
                    "Peel 2 ripe bananas and break into chunks",
                    "Add banana chunks to blender with 1 cup of cold milk",
                    "Add 1 tablespoon honey and a pinch of cinnamon (optional)",
                    "Blend on high speed for 60-90 seconds until smooth and creamy",
                    "Pour into glasses and serve immediately",
                    "Optional: garnish with banana slices or a sprinkle of cinnamon"
                ],
                'nutrition': {'calories': 200, 'protein': 8},
                'time': 5,
                'meal_type': 'breakfast'
            },
            {
                'name': 'Chicken and Milk Scramble',
                'ingredients': ['4 oz chicken breast', '2 tablespoons milk', '3 large eggs', '1 tablespoon oil', 'salt and pepper to taste'],
                'instructions': [
                    "Dice chicken breast into small, bite-sized pieces",
                    "Beat 3 eggs with 2 tablespoons of milk in a bowl",
                    "Heat 1 tablespoon oil in a non-stick pan over medium heat",
                    "Cook chicken pieces for 4-5 minutes until fully cooked",
                    "Pour egg mixture over chicken and let sit for 30 seconds",
                    "Gently scramble with a spatula until eggs are just set",
                    "Season with salt and pepper, serve immediately"
                ],
                'nutrition': {'calories': 350, 'protein': 30},
                'time': 15,
                'meal_type': 'breakfast'
            },
            # Lunch/Dinner recipes
            {
                'name': 'Simple Grilled Chicken',
                'ingredients': ['2 chicken breasts (6 oz each)', '1 teaspoon salt', '1/2 teaspoon black pepper', '1 tablespoon olive oil'],
                'instructions': [
                    "Remove chicken breasts from refrigerator 15 minutes before cooking",
                    "Pat chicken dry with paper towels and season both sides with salt and pepper",
                    "Preheat grill or grill pan to medium-high heat (about 375-400°F)",
                    "Lightly oil the grill grates to prevent sticking",
                    "Place chicken on grill and cook for 6-7 minutes without moving",
                    "Flip chicken and cook for another 6-7 minutes until internal temp reaches 165°F",
                    "Remove from heat and let rest for 5 minutes before slicing",
                    "Serve with your favorite sides"
                ],
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
        # Create a mapping of lowercase names to original pantry items for cleaning
        pantry_map = {}
        for item in pantry_items:
            if item.get('product_name'):
                pantry_map[item['product_name'].lower()] = item['product_name']
        
        pantry_names = set(pantry_map.keys())
        
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
                
                # Extract the ingredient name from quantity string (e.g., "2 cups rice" -> "rice")
                # Remove common measurements
                ingredient_name = ingredient_lower
                for measure in ['cups', 'cup', 'tablespoons', 'tablespoon', 'tbsp', 'teaspoons', 'teaspoon', 'tsp', 
                               'pounds', 'pound', 'lbs', 'lb', 'ounces', 'ounce', 'oz', 'cloves', 'clove',
                               'cans', 'can', 'bunch', 'bunches', 'piece', 'pieces', 'large', 'medium', 'small']:
                    ingredient_name = ingredient_name.replace(measure, '')
                
                # Remove numbers and parentheses content
                import re
                ingredient_name = re.sub(r'\([^)]*\)', '', ingredient_name)  # Remove (6 oz each) etc
                ingredient_name = re.sub(r'\d+', '', ingredient_name)  # Remove numbers
                ingredient_name = ingredient_name.strip()
                
                # Check for exact match or partial match
                found = False
                for pantry_item in pantry_names:
                    # Use cleaned ingredient name for matching
                    if ingredient_name == pantry_item:
                        # Keep the original ingredient with quantity for available items
                        available_ingredients.append(ingredient)
                        found = True
                        break
                    # Then check if ingredient is in pantry item name or vice versa
                    elif (ingredient_name in pantry_item or 
                          pantry_item in ingredient_name or
                          self._is_similar_ingredient(ingredient_name, pantry_item)):
                        # Keep the original ingredient with quantity for available items
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
            contains_allergens = []
            
            # More comprehensive allergen checking
            for allergen in allergens:
                allergen_lower = allergen.lower()
                for ingredient in recipe_ingredients_lower:
                    # Check for exact match or if allergen is contained in ingredient
                    if allergen_lower in ingredient or self._is_allergen_in_ingredient(allergen_lower, ingredient):
                        contains_allergens.append(allergen)
                        break
            
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
    
    def _clean_ingredient_name(self, ingredient: str) -> str:
        """Clean ingredient name by removing brand names and simplifying."""
        # Remove size/weight info after dash
        clean_name = ingredient.split('–')[0].strip() if '–' in ingredient else ingredient
        
        # Common brand names to remove
        brand_patterns = [
            'Muir Glen', 'Ancient Harvest', 'Trader Joe\'s', 'Kirkland', 'Great Value',
            'Nature\'s Own', 'Kraft', 'Heinz', 'Campbell\'s', 'Del Monte', 'Hunt\'s',
            'Barilla', 'Ronzoni', 'Progresso', 'Swanson', 'Ocean Spray', 'Minute Maid',
            'Tropicana', 'Simply', 'Organic', 'Natural', 'Premium', 'Select', 'Choice'
        ]
        
        # Remove brand names
        for brand in brand_patterns:
            clean_name = clean_name.replace(brand, '').strip()
        
        # Remove extra spaces
        clean_name = ' '.join(clean_name.split())
        
        # Capitalize properly
        return clean_name.title()
    
    def _is_allergen_in_ingredient(self, allergen: str, ingredient: str) -> bool:
        """Check if an allergen is present in an ingredient."""
        # Common allergen mappings
        allergen_mappings = {
            'nuts': ['almond', 'cashew', 'walnut', 'pecan', 'hazelnut', 'pistachio', 'macadamia', 'brazil nut'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'whey', 'casein', 'lactose'],
            'eggs': ['egg', 'eggs', 'egg white', 'egg yolk', 'mayonnaise'],
            'gluten': ['wheat', 'barley', 'rye', 'bread', 'pasta', 'flour', 'crackers', 'cereal'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'prawns', 'crawfish', 'crayfish'],
            'soy': ['soy', 'soybean', 'tofu', 'tempeh', 'edamame', 'miso'],
            'peanuts': ['peanut', 'peanuts', 'peanut butter'],
            'tree nuts': ['almond', 'cashew', 'walnut', 'pecan', 'hazelnut', 'pistachio'],
        }
        
        # Check if allergen is a category
        if allergen in allergen_mappings:
            return any(specific in ingredient for specific in allergen_mappings[allergen])
        
        # Direct check for specific allergens
        return allergen in ingredient
    
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
        
        # Check if user is asking about expiring items
        is_expiring_query = any(phrase in message.lower() for phrase in [
            'expiring', 'expire', 'going bad', 'use soon', 'about to expire'
        ])
        
        if is_expiring_query:
            # Get items expiring soon (within 7 days)
            from datetime import datetime, timedelta
            today = datetime.now().date()
            expiring_soon = []
            
            for item in items:
                if item.get('expiration_date'):
                    exp_date = datetime.strptime(str(item['expiration_date']), '%Y-%m-%d').date()
                    days_until_expiry = (exp_date - today).days
                    if 0 <= days_until_expiry <= 7:
                        expiring_soon.append({
                            'name': item.get('product_name', 'Unknown item'),
                            'days': days_until_expiry,
                            'date': exp_date.strftime('%B %d')
                        })
            
            if expiring_soon:
                # Sort by days until expiry
                expiring_soon.sort(key=lambda x: x['days'])
                
                # Remove duplicates while preserving order
                seen = set()
                unique_expiring = []
                for item in expiring_soon:
                    if item['name'] not in seen:
                        seen.add(item['name'])
                        unique_expiring.append(item)
                
                response = f"🚨 You have {len(unique_expiring)} items expiring soon:\n\n"
                for item in unique_expiring[:10]:  # Show top 10
                    if item['days'] == 0:
                        response += f"• {item['name']} - Expires TODAY!\n"
                    elif item['days'] == 1:
                        response += f"• {item['name']} - Expires tomorrow\n"
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
            
            # Fetch user preferences
            user_preferences = await self._fetch_user_preferences(user_id)
            
            # Get some recipe suggestions based on message
            if not pantry_items:
                return {
                    "response": "I notice your pantry is empty. Would you like me to suggest some essential items to stock up on?",
                    "recipes": [],
                    "pantry_items": [],
                    "user_preferences": user_preferences
                }
            
            # Simple keyword matching for different queries
            message_lower = message.lower()
            
            # Check for expiring items query first
            if any(phrase in message_lower for phrase in ['expiring', 'expire', 'going bad', 'use soon', 'about to expire']):
                # Use the same format_response method which handles expiring queries
                response = self._format_response([], pantry_items, message, user_preferences)
                return {
                    "response": response,
                    "recipes": [],  # We could generate recipes for expiring items here
                    "pantry_items": pantry_items[:10],
                    "user_preferences": user_preferences
                }
            elif any(word in message_lower for word in ['dinner', 'lunch', 'breakfast', 'meal', 'cook', 'make']):
                # Get unique ingredient names from ALL pantry items
                ingredients_set = set()
                for item in pantry_items:  # Use ALL items, not just first 10
                    if item.get('product_name'):
                        # Clean up the ingredient name
                        name = item['product_name'].strip()
                        # Remove size/quantity info if present
                        if '–' in name:
                            name = name.split('–')[0].strip()
                        ingredients_set.add(name)
                
                # Convert to sorted list for consistent ordering
                ingredients = sorted(list(ingredients_set))
                
                # Generate simple response
                response = f"Based on your {len(ingredients)} unique pantry items, here are some recipe suggestions! "
                
                # Create more diverse recipes based on actual ingredients
                simple_recipes = []
                
                # Check what types of ingredients we have
                has_corn = any('corn' in ing.lower() for ing in ingredients)
                has_tomatoes = any('tomato' in ing.lower() for ing in ingredients)
                has_pasta = any('pasta' in ing.lower() or 'noodle' in ing.lower() for ing in ingredients)
                has_rice = any('rice' in ing.lower() for ing in ingredients)
                has_protein = any(any(p in ing.lower() for p in ['chicken', 'beef', 'pork', 'fish', 'tofu', 'beans']) for ing in ingredients)
                
                # Recipe 1: Based on corn and tomatoes if available
                if has_corn and has_tomatoes:
                    recipe_ingredients = [ing for ing in ingredients if 'corn' in ing.lower() or 'tomato' in ing.lower()][:3]
                    recipe_ingredients.extend([ing for ing in ingredients if ing not in recipe_ingredients][:2])
                    simple_recipes.append({
                        "name": "Mexican-Style Corn & Tomato Skillet",
                        "description": "A vibrant dish combining corn and tomatoes with spices",
                        "ingredients": recipe_ingredients[:5],
                        "instructions": [
                            "Heat 2 tablespoons oil in a large skillet over medium-high heat",
                            "Add corn kernels and cook for 3-4 minutes until lightly charred",
                            "Add diced tomatoes and cook for another 2-3 minutes",
                            "Season with cumin, chili powder, salt, and pepper",
                            "Stir in any additional vegetables and cook until tender",
                            "Squeeze fresh lime juice over the mixture",
                            "Garnish with cilantro and serve hot"
                        ],
                        "nutrition": {"calories": 320, "protein": 12},
                        "time": 25,
                        "available_ingredients": recipe_ingredients[:4],
                        "missing_ingredients": ["Cumin", "Chili powder", "Lime"],
                        "missing_count": 3,
                        "available_count": 4,
                        "match_score": 0.57,
                        "expected_joy": 82,
                        "cuisine_type": "Mexican",
                        "dietary_tags": ["vegetarian"],
                        "allergens_present": [],
                        "matched_preferences": []
                    })
                
                # Recipe 2: Stir-fry with available vegetables
                veggie_ingredients = [ing for ing in ingredients if any(v in ing.lower() for v in ['corn', 'tomato', 'pepper', 'onion', 'broccoli', 'carrot'])][:4]
                if len(veggie_ingredients) < 4:
                    veggie_ingredients.extend([ing for ing in ingredients if ing not in veggie_ingredients][:4-len(veggie_ingredients)])
                
                simple_recipes.append({
                    "name": "Garden Vegetable Stir-Fry",
                    "description": "Quick and healthy vegetable stir-fry with available produce",
                    "ingredients": veggie_ingredients[:5],
                    "instructions": [
                        "Prep all vegetables by washing and cutting into uniform pieces",
                        "Heat 2 tablespoons oil in a wok or large skillet over high heat",
                        "Add harder vegetables first (carrots, broccoli) and stir-fry for 2 minutes",
                        "Add softer vegetables (peppers, tomatoes) and cook for another 2 minutes",
                        "Push vegetables to the sides and add minced garlic and ginger to center",
                        "Stir-fry aromatics for 30 seconds until fragrant",
                        "Toss everything together with soy sauce and sesame oil",
                        "Serve immediately over rice or noodles"
                    ],
                    "nutrition": {"calories": 280, "protein": 8},
                    "time": 20,
                    "available_ingredients": veggie_ingredients[:4],
                    "missing_ingredients": ["Soy sauce", "Ginger", "Garlic"],
                    "missing_count": 3,
                    "available_count": 4,
                    "match_score": 0.57,
                    "expected_joy": 78,
                    "cuisine_type": "Asian",
                    "dietary_tags": ["vegetarian", "vegan"],
                    "allergens_present": [],
                    "matched_preferences": []
                })
                
                # Recipe 3: Comfort food option
                comfort_ingredients = ingredients[5:10] if len(ingredients) > 10 else ingredients[:5]
                simple_recipes.append({
                    "name": "Hearty One-Pot Meal",
                    "description": "Comforting dish using your pantry staples",
                    "ingredients": comfort_ingredients,
                    "instructions": [
                        "Heat 2 tablespoons oil in a large Dutch oven or heavy pot",
                        "Brown any protein ingredients over medium-high heat, then set aside",
                        "In the same pot, sauté onions and garlic until softened",
                        "Add remaining vegetables and cook for 5 minutes",
                        "Return protein to pot and add 4 cups of stock or water",
                        "Add bay leaves and bring to a simmer",
                        "Cover and cook for 25-30 minutes until everything is tender",
                        "Season with salt, pepper, and herbs to taste before serving"
                    ],
                    "nutrition": {"calories": 420, "protein": 18},
                    "time": 35,
                    "available_ingredients": comfort_ingredients[:3],
                    "missing_ingredients": ["Stock", "Bay leaves"],
                    "missing_count": 2,
                    "available_count": 3,
                    "match_score": 0.6,
                    "expected_joy": 85,
                    "cuisine_type": "American",
                    "dietary_tags": [],
                    "allergens_present": [],
                    "matched_preferences": []
                })
                
                # Add variety by using different ingredient combinations
                if len(ingredients) > 15:
                    # Recipe 4: Using middle ingredients
                    middle_ingredients = ingredients[10:15]
                    simple_recipes.append({
                        "name": "Creative Fusion Bowl",
                        "description": "Mix and match your pantry items for a unique meal",
                        "ingredients": middle_ingredients,
                        "instructions": [
                            "Cook 1 cup of quinoa or rice in 2 cups water/broth for 15-20 minutes",
                            "While grains cook, dice vegetables into 1/2 inch pieces for even cooking",
                            "Heat 2 tablespoons oil in a large skillet or wok over medium-high heat",
                            "If using protein, season with salt and pepper, cook 5-7 minutes until golden",
                            "Remove protein and set aside, keeping warm under foil",
                            "Add harder vegetables (carrots, broccoli) first, cook 3-4 minutes",
                            "Add softer vegetables (peppers, zucchini), cook another 2-3 minutes",
                            "Mix 2 tbsp soy sauce with 1 tbsp honey and 1 tsp sesame oil for sauce",
                            "Return protein to pan, add sauce, toss everything for 1 minute",
                            "Serve over cooked grains, garnish with sesame seeds or green onions"
                        ],
                        "nutrition": {"calories": 380, "protein": 15},
                        "time": 30,
                        "available_ingredients": middle_ingredients[:4],
                        "missing_ingredients": ["Soy sauce", "Honey", "Sesame oil"],
                        "missing_count": 3,
                        "available_count": 4,
                        "match_score": 0.57,
                        "expected_joy": 75,
                        "cuisine_type": "Fusion",
                        "dietary_tags": [],
                        "allergens_present": [],
                        "matched_preferences": []
                    })
                
                # Rank recipes using the same ranking function
                ranked_recipes = self._rank_recipes(simple_recipes, pantry_items, user_preferences)
                
                # Filter out recipes with allergens
                safe_recipes = [r for r in ranked_recipes if not r.get('allergens_present', [])]
                
                # If all recipes contain allergens, return a message
                if not safe_recipes and ranked_recipes:
                    response = "I found some recipes, but they all contain ingredients you're allergic to. Let me find alternatives..."
                    safe_recipes = []
                
                # Format response with preferences
                formatted_response = self._format_response(safe_recipes[:5], pantry_items, message, user_preferences)
                
                return {
                    "response": formatted_response,
                    "recipes": safe_recipes[:5],
                    "pantry_items": pantry_items[:10],
                    "user_preferences": user_preferences
                }
            else:
                # General response
                return {
                    "response": f"You currently have {len(pantry_items)} items in your pantry. What would you like to know about them?",
                    "recipes": [],
                    "pantry_items": pantry_items[:10],
                    "user_preferences": user_preferences
                }
                
        except Exception as e:
            logger.error(f"Error in fallback chat: {str(e)}")
            return {
                "response": "I'm having trouble accessing your pantry data. Please try again later.",
                "recipes": [],
                "pantry_items": [],
                "user_preferences": {
                    "dietary_preference": [],
                    "allergens": [],
                    "cuisine_preference": []
                }
            }