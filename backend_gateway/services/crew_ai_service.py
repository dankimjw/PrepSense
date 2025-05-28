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
    
    async def process_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """
        Process a chat message and return recipe recommendations.
        
        Args:
            user_id: The user's ID
            message: The user's message
            
        Returns:
            Dict containing response, recipes, and pantry items
        """
        if not CREWAI_AVAILABLE:
            # Provide a fallback response if CrewAI is not installed
            return {
                "response": "The AI chat service is currently unavailable. Please install the required dependencies.",
                "recipes": [],
                "pantry_items": []
            }
            
        try:
            # Step 1: Fetch pantry items
            pantry_items = await self._fetch_pantry_items(user_id)
            
            # Step 2: Filter non-expired items
            valid_items = self._filter_valid_items(pantry_items)
            
            # Step 3: Search for recipes based on message context
            recipes = await self._search_recipes(valid_items, message)
            
            # Step 4: Evaluate and rank recipes
            ranked_recipes = self._rank_recipes(recipes, valid_items)
            
            # Step 5: Format response
            response = self._format_response(ranked_recipes, valid_items, message)
            
            return {
                "response": response,
                "recipes": ranked_recipes[:3],  # Top 3 recipes
                "pantry_items": valid_items
            }
            
        except Exception as e:
            logger.error(f"Error in CrewAI service: {str(e)}")
            raise
    
    async def _fetch_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch pantry items from BigQuery."""
        query = """
            SELECT *
            FROM `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
            WHERE user_id = @user_id
            ORDER BY expiration_date ASC
        """
        params = {"user_id": user_id}
        return self.bq_service.execute_query(query, params)
    
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
    
    async def _search_recipes(self, pantry_items: List[Dict[str, Any]], message: str) -> List[Dict[str, Any]]:
        """Search for recipes based on pantry items and user message."""
        # Extract ingredient names from pantry
        available_ingredients = [item['product_name'].lower() for item in pantry_items if item.get('product_name')]
        
        # Create a comprehensive recipe database with varying ingredient requirements
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
            }
        ]
        
        # Filter recipes based on message context
        filtered_recipes = []
        message_lower = message.lower()
        
        if 'breakfast' in message_lower:
            filtered_recipes = [r for r in all_recipes if r.get('meal_type') == 'breakfast']
        elif 'lunch' in message_lower:
            filtered_recipes = [r for r in all_recipes if r.get('meal_type') == 'lunch']
        elif 'dinner' in message_lower:
            filtered_recipes = [r for r in all_recipes if r.get('meal_type') == 'dinner']
        else:
            # Return all recipes if no specific meal mentioned
            filtered_recipes = all_recipes
        
        return filtered_recipes
    
    def _rank_recipes(self, recipes: List[Dict[str, Any]], pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank recipes based on available ingredients and calculate missing items."""
        pantry_names = {item['product_name'].lower() for item in pantry_items if item.get('product_name')}
        
        for recipe in recipes:
            recipe_ingredients = recipe.get('ingredients', [])
            available_ingredients = []
            missing_ingredients = []
            
            for ingredient in recipe_ingredients:
                if ingredient.lower() in pantry_names:
                    available_ingredients.append(ingredient)
                else:
                    missing_ingredients.append(ingredient)
            
            recipe['available_ingredients'] = available_ingredients
            recipe['missing_ingredients'] = missing_ingredients
            recipe['missing_count'] = len(missing_ingredients)
            recipe['available_count'] = len(available_ingredients)
            recipe['match_score'] = len(available_ingredients) / len(recipe_ingredients) if recipe_ingredients else 0
        
        # Sort by fewest missing ingredients first, then by match score
        return sorted(recipes, key=lambda x: (x.get('missing_count', 999), -x.get('match_score', 0)))
    
    def _format_response(self, recipes: List[Dict[str, Any]], items: List[Dict[str, Any]], message: str) -> str:
        """Format the final response message."""
        if not recipes:
            return "I couldn't find any recipes matching your request with your current pantry items. Would you like some shopping suggestions?"
        
        # Check if user wants recipes with only available ingredients
        wants_available_only = any(phrase in message.lower() for phrase in [
            'only ingredients i have', 'what i have', 'without shopping', 
            'available ingredients', 'no missing', 'dont need to buy'
        ])
        
        if wants_available_only:
            # Filter for recipes with no missing ingredients
            perfect_match_recipes = [r for r in recipes if r.get('missing_count', 0) == 0]
            if perfect_match_recipes:
                response = "Here are recipes you can make with only your current pantry items:\n\n"
                target_recipes = perfect_match_recipes[:3]
            else:
                response = "No recipes can be made with only your current ingredients. Here are the recipes requiring the fewest additional items:\n\n"
                target_recipes = recipes[:3]
        else:
            response = "Based on your pantry items, here are my recommendations:\n\n"
            target_recipes = recipes[:3]
        
        for i, recipe in enumerate(target_recipes, 1):
            response += f"{i}. **{recipe['name']}**\n"
            response += f"   - Time: {recipe.get('time', 'N/A')} minutes\n"
            response += f"   - Available ingredients: {', '.join(recipe.get('available_ingredients', []))}\n"
            
            if recipe.get('missing_ingredients'):
                response += f"   - Missing ingredients: {', '.join(recipe.get('missing_ingredients', []))}\n"
                response += f"   - You need {recipe.get('missing_count', 0)} additional item(s)\n"
            else:
                response += f"   - ✅ You have all ingredients!\n"
            
            response += f"   - Match: {recipe.get('match_score', 0)*100:.0f}% complete\n\n"
        
        # Add helpful tip if there are missing ingredients
        if any(r.get('missing_count', 0) > 0 for r in target_recipes):
            response += "💡 Tip: Ask me for 'recipes with only ingredients I have' if you prefer not to shop for additional items!"
        
        return response