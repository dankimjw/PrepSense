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
        # Extract ingredient names
        ingredients = [item['product_name'] for item in pantry_items if item.get('product_name')]
        
        # Use the recipe service to search
        # This is a placeholder - implement actual recipe search logic
        recipes = []
        
        # Simple mock implementation
        if 'breakfast' in message.lower():
            recipes = [
                {
                    'name': 'Scrambled Eggs with Toast',
                    'ingredients': ['eggs', 'bread', 'butter'],
                    'nutrition': {'calories': 350, 'protein': 20},
                    'time': 15
                }
            ]
        elif 'dinner' in message.lower():
            recipes = [
                {
                    'name': 'Pasta with Tomato Sauce',
                    'ingredients': ['pasta', 'tomatoes', 'garlic'],
                    'nutrition': {'calories': 450, 'protein': 15},
                    'time': 30
                }
            ]
        
        return recipes
    
    def _rank_recipes(self, recipes: List[Dict[str, Any]], pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank recipes based on available ingredients and nutritional value."""
        # Simple ranking based on ingredient availability
        pantry_names = {item['product_name'].lower() for item in pantry_items if item.get('product_name')}
        
        for recipe in recipes:
            available_ingredients = sum(1 for ing in recipe.get('ingredients', []) 
                                      if ing.lower() in pantry_names)
            recipe['match_score'] = available_ingredients / len(recipe.get('ingredients', [1]))
        
        # Sort by match score
        return sorted(recipes, key=lambda x: x.get('match_score', 0), reverse=True)
    
    def _format_response(self, recipes: List[Dict[str, Any]], items: List[Dict[str, Any]], message: str) -> str:
        """Format the final response message."""
        if not recipes:
            return "I couldn't find any recipes matching your request with your current pantry items. Would you like some shopping suggestions?"
        
        response = f"Based on your pantry items, here are my recommendations:\n\n"
        
        for i, recipe in enumerate(recipes[:3], 1):
            response += f"{i}. **{recipe['name']}**\n"
            response += f"   - Time: {recipe.get('time', 'N/A')} minutes\n"
            response += f"   - Match: {recipe.get('match_score', 0)*100:.0f}% of ingredients available\n\n"
        
        return response