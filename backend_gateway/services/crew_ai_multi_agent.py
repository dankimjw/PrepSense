"""
Multi-Agent CrewAI Implementation for Recipe Recommendations
Based on the original architecture design
"""
import os
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from crewai import Agent, Task, Crew, Process
from pydantic import BaseModel, Field
# Note: BaseTool import has been moved in newer CrewAI versions
try:
    from crewai.tools import BaseTool
except ImportError:
    # For newer versions, create a simple tool base class
    class BaseTool:
        def __init__(self):
            pass
        
        def _run(self, *args, **kwargs):
            raise NotImplementedError("Tool must implement _run method")

logger = logging.getLogger(__name__)


# Tool definitions for agents
class PantryScanTool(BaseTool):
    """Tool to read pantry items from database"""
    def __init__(self):
        super().__init__()
        self.name = "pantry_scanner"
        self.description = "Reads pantry items from PostgreSQL database for a given user"
    
    def _run(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch pantry items from database"""
        from backend_gateway.config.database import get_database_service
        
        db = get_database_service()
        query = """
            SELECT *
            FROM user_pantry_full
            WHERE user_id = %(user_id)s
            ORDER BY expiration_date ASC
        """
        return db.execute_query(query, {"user_id": user_id})


class IngredientFilterTool(BaseTool):
    """Tool to filter expired/unusable items"""
    def __init__(self):
        super().__init__()
        self.name = "ingredient_filter"
        self.description = "Removes expired and unusable items from pantry list"
    
    def _run(self, pantry_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out expired items"""
        today = datetime.now().date()
        valid_items = []
        
        for item in pantry_items:
            if item.get('expiration_date'):
                exp_date = datetime.strptime(str(item['expiration_date']), '%Y-%m-%d').date()
                if exp_date >= today:
                    valid_items.append(item)
            else:
                valid_items.append(item)
        
        return valid_items


class UserPreferenceTool(BaseTool):
    """Tool to fetch user preferences"""
    def __init__(self):
        super().__init__()
        self.name = "preference_fetcher"
        self.description = "Fetches user's dietary restrictions and preferences"
    
    def _run(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences from database"""
        from backend_gateway.config.database import get_database_service
        
        db = get_database_service()
        query = """
            SELECT *
            FROM user_preferences
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        results = db.execute_query(query, {"user_id": user_id})
        
        if results and results[0].get('preferences'):
            prefs_data = results[0]['preferences']
            return {
                'dietary_restrictions': prefs_data.get('dietary_restrictions', []),
                'allergens': prefs_data.get('allergens', []),
                'cuisine_preferences': prefs_data.get('cuisine_preferences', []),
                'cooking_skill': prefs_data.get('cooking_skill', 'intermediate'),
                'max_cooking_time': prefs_data.get('max_cooking_time', 45)
            }
        return {}


class RecipeSearchTool(BaseTool):
    """Tool to search for recipes"""
    def __init__(self):
        super().__init__()
        self.name = "recipe_searcher"
        self.description = "Searches for recipes based on ingredients and preferences"
    
    def _run(self, ingredients: List[str], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for recipes using Spoonacular API"""
        from backend_gateway.services.spoonacular_service import SpoonacularService
        
        service = SpoonacularService()
        # This would be async in real implementation
        recipes = []
        
        # Search Spoonacular
        allergens = preferences.get('allergens', [])
        # In real implementation, this would be awaited
        # recipes = await service.search_recipes_by_ingredients(
        #     ingredients=ingredients[:10],
        #     number=10,
        #     intolerances=allergens
        # )
        
        # For now, return mock data
        return [
            {
                'id': 1,
                'name': 'Chicken Rice Bowl',
                'ingredients': ['chicken', 'rice', 'vegetables'],
                'time': 30,
                'instructions': ['Cook rice', 'Grill chicken', 'Combine'],
                'cuisine_type': 'asian'
            }
        ]


class NutritionalAnalysisTool(BaseTool):
    """Tool to analyze nutritional content"""
    def __init__(self):
        super().__init__()
        self.name = "nutrition_analyzer"
        self.description = "Evaluates nutritional balance of recipes"
    
    def _run(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add nutritional analysis to recipes"""
        for recipe in recipes:
            # In real implementation, would call nutrition API
            recipe['nutrition'] = {
                'calories': 450,
                'protein': 35,
                'carbs': 45,
                'fat': 15,
                'fiber': 5,
                'nutritional_balance': 'good'
            }
        return recipes


class RecipeScoringTool(BaseTool):
    """Tool to score and rank recipes"""
    def __init__(self):
        super().__init__()
        self.name = "recipe_scorer"
        self.description = "Ranks recipes by relevance, health, and user preferences"
    
    def _run(self, recipes: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Score and rank recipes"""
        for recipe in recipes:
            score = 0
            
            # Score based on nutritional balance
            if recipe.get('nutrition', {}).get('nutritional_balance') == 'good':
                score += 30
            
            # Score based on cooking time
            if recipe.get('time', 60) <= preferences.get('max_cooking_time', 45):
                score += 20
            
            # Score based on cuisine preference match
            if recipe.get('cuisine_type') in preferences.get('cuisine_preferences', []):
                score += 25
            
            recipe['score'] = score
        
        # Sort by score
        return sorted(recipes, key=lambda x: x.get('score', 0), reverse=True)


# Agent Definitions
def create_agents():
    """Create all the specialized agents"""
    
    pantry_scan_agent = Agent(
        role='Pantry Scanner',
        goal='Read and retrieve all pantry items for the user from the database',
        backstory='I am responsible for accessing the database and retrieving the current pantry inventory.',
        tools=[PantryScanTool()],
        verbose=True
    )
    
    ingredient_filter_agent = Agent(
        role='Ingredient Filter',
        goal='Filter out expired and unusable ingredients from the pantry',
        backstory='I ensure only fresh, usable ingredients are considered for recipes.',
        tools=[IngredientFilterTool()],
        verbose=True
    )
    
    preference_agent = Agent(
        role='User Preference Specialist',
        goal='Retrieve and apply user dietary restrictions and preferences',
        backstory='I understand user preferences including dietary restrictions, allergens, and cuisine preferences.',
        tools=[UserPreferenceTool()],
        verbose=True
    )
    
    recipe_search_agent = Agent(
        role='Recipe Researcher',
        goal='Find recipes that match available ingredients and user preferences',
        backstory='I search through recipe databases to find the best matches for available ingredients.',
        tools=[RecipeSearchTool()],
        verbose=True
    )
    
    nutritional_agent = Agent(
        role='Nutritional Analyst',
        goal='Evaluate the nutritional balance of recipes',
        backstory='I analyze recipes for their nutritional content and health benefits.',
        tools=[NutritionalAnalysisTool()],
        verbose=True
    )
    
    scoring_agent = Agent(
        role='Recipe Scoring Expert',
        goal='Rank recipes by relevance, health, and user preferences',
        backstory='I score and rank recipes based on multiple factors to find the best options.',
        tools=[RecipeScoringTool()],
        verbose=True
    )
    
    evaluator_agent = Agent(
        role='Recipe Evaluator',
        goal='Validate recipes for feasibility and accuracy',
        backstory='I ensure recommended recipes are practical and accurate.',
        tools=[],  # Uses reasoning, no specific tools
        verbose=True
    )
    
    formatter_agent = Agent(
        role='Response Formatter',
        goal='Format recipe recommendations in a user-friendly way',
        backstory='I present recipe recommendations in a clear, engaging format.',
        tools=[],  # Uses reasoning, no specific tools
        verbose=True
    )
    
    return {
        'pantry_scan': pantry_scan_agent,
        'ingredient_filter': ingredient_filter_agent,
        'preference': preference_agent,
        'recipe_search': recipe_search_agent,
        'nutritional': nutritional_agent,
        'scoring': scoring_agent,
        'evaluator': evaluator_agent,
        'formatter': formatter_agent
    }


def create_tasks(agents: Dict[str, Agent], user_id: int, message: str):
    """Create tasks for each agent"""
    
    pantry_scan_task = Task(
        description=f"Retrieve all pantry items for user {user_id} from the database",
        agent=agents['pantry_scan'],
        expected_output="List of all pantry items with expiration dates and quantities"
    )
    
    filter_task = Task(
        description="Filter the pantry items to remove expired or unusable ingredients",
        agent=agents['ingredient_filter'],
        expected_output="Filtered list of valid, usable ingredients"
    )
    
    preference_task = Task(
        description=f"Fetch dietary preferences and restrictions for user {user_id}",
        agent=agents['preference'],
        expected_output="User preferences including dietary restrictions, allergens, and cuisine preferences"
    )
    
    search_task = Task(
        description=f"Search for recipes based on available ingredients and user preferences. User query: {message}",
        agent=agents['recipe_search'],
        expected_output="List of potential recipes matching ingredients and preferences"
    )
    
    nutrition_task = Task(
        description="Analyze the nutritional content of each recipe",
        agent=agents['nutritional'],
        expected_output="Recipes with detailed nutritional information"
    )
    
    scoring_task = Task(
        description="Score and rank recipes based on health, relevance, and user preferences",
        agent=agents['scoring'],
        expected_output="Ranked list of recipes with scores"
    )
    
    evaluation_task = Task(
        description="Evaluate top recipes for feasibility and accuracy",
        agent=agents['evaluator'],
        expected_output="Validated list of recommended recipes"
    )
    
    formatting_task = Task(
        description="Format the final recipe recommendations in a user-friendly response",
        agent=agents['formatter'],
        expected_output="Formatted response with recipe recommendations"
    )
    
    return [
        pantry_scan_task,
        filter_task,
        preference_task,
        search_task,
        nutrition_task,
        scoring_task,
        evaluation_task,
        formatting_task
    ]


class MultiAgentCrewAIService:
    """Service that orchestrates the multi-agent crew"""
    
    def __init__(self):
        self.agents = create_agents()
    
    async def process_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """Process a user message using the multi-agent crew"""
        
        # Create tasks for this request
        tasks = create_tasks(self.agents, user_id, message)
        
        # Create the crew
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,  # Tasks run in sequence
            verbose=True
        )
        
        # Execute the crew
        result = crew.kickoff()
        
        # Parse and return the result
        return {
            "response": str(result),
            "recipes": [],  # Would be parsed from crew output
            "pantry_items": [],
            "user_preferences": {}
        }


# Example usage
if __name__ == "__main__":
    service = MultiAgentCrewAIService()
    # Would be called as: await service.process_message(111, "What can I make for dinner?")