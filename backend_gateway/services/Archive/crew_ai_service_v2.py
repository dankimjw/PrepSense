"""
CrewAI Service v2 - Multi-source recipe recommendation with preference learning
Uses PostgreSQL, integrates saved recipes, Spoonacular, and OpenAI
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime

# CrewAI imports
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = Process = None

# Service imports
from backend_gateway.config.database import get_database_service
from backend_gateway.services.user_recipes_service import UserRecipesService
from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.services.preference_analyzer_service import PreferenceAnalyzerService

# Tool imports
from backend_gateway.services.crewai_tools import (
    PostgresPantryTool,
    UserPreferencesTool,
    SavedRecipeMatchTool,
    SpoonacularRecipeTool,
    OpenAIRecipeTool,
    PreferenceAnalyzerTool,
    RecipeRankerTool
)

logger = logging.getLogger(__name__)


class CrewAIServiceV2:
    """Enhanced CrewAI service with multi-source recipes and preference learning"""
    
    def __init__(self):
        """Initialize the CrewAI service with all necessary components"""
        # Initialize services
        self.db_service = get_database_service()
        self.user_recipes_service = UserRecipesService(self.db_service)
        self.spoonacular_service = SpoonacularService()
        self.preference_analyzer_service = PreferenceAnalyzerService(self.db_service)
        
        # Initialize tools
        self.pantry_tool = PostgresPantryTool(self.db_service)
        self.preferences_tool = UserPreferencesTool(self.db_service)
        self.saved_recipe_tool = SavedRecipeMatchTool(self.user_recipes_service)
        self.spoonacular_tool = SpoonacularRecipeTool(self.spoonacular_service)
        self.openai_tool = OpenAIRecipeTool()
        self.preference_analyzer_tool = PreferenceAnalyzerTool(self.preference_analyzer_service)
        self.ranker_tool = RecipeRankerTool()
        
        # Initialize agents if CrewAI is available
        if CREWAI_AVAILABLE:
            self._initialize_agents()
        else:
            logger.warning("CrewAI not installed. Install with: pip install crewai crewai-tools")
    
    def _initialize_agents(self):
        """Initialize the 4 core agents for recipe recommendation"""
        
        # 1. Pantry Analyst Agent
        self.pantry_analyst = Agent(
            role='Pantry & Preference Analyst',
            goal='Analyze user\'s pantry inventory and understand their preferences',
            backstory="""You are an expert at understanding what's in someone's pantry 
            and learning their food preferences from their history. You identify expiring 
            items, categorize ingredients, and understand dietary needs.""",
            tools=[
                self.pantry_tool,
                self.preferences_tool,
                self.preference_analyzer_tool
            ],
            verbose=True,
            allow_delegation=False
        )
        
        # 2. Recipe Finder Agent
        self.recipe_finder = Agent(
            role='Multi-Source Recipe Finder',
            goal='Find the best recipes from saved recipes, Spoonacular, and AI generation',
            backstory="""You are a culinary expert who knows how to find the perfect recipes.
            You check the user's saved recipes first, then search Spoonacular for tested recipes,
            and use AI to create innovative options. You always respect dietary restrictions.""",
            tools=[
                self.saved_recipe_tool,
                self.spoonacular_tool,
                self.openai_tool
            ],
            verbose=True,
            allow_delegation=False
        )
        
        # 3. Recipe Evaluator Agent  
        self.recipe_evaluator = Agent(
            role='Recipe Quality Evaluator',
            goal='Evaluate recipes for nutrition, complexity, and user fit',
            backstory="""You are both a nutritionist and a practical cook. You evaluate 
            recipes for nutritional balance, cooking complexity, and how well they match 
            the user's preferences and constraints.""",
            tools=[self.ranker_tool],
            verbose=True,
            allow_delegation=False
        )
        
        # 4. Conversation Agent
        self.conversation_agent = Agent(
            role='Helpful Recipe Advisor',
            goal='Present recipes in a friendly, helpful way with clear recommendations',
            backstory="""You are a friendly kitchen assistant who helps people decide what 
            to cook. You explain why certain recipes are recommended and provide helpful 
            context about ingredients and cooking.""",
            tools=[],
            verbose=True,
            allow_delegation=False
        )
    
    async def process_message(self, user_id: int, message: str, use_preferences: bool = True) -> Dict[str, Any]:
        """
        Process a chat message using CrewAI agents
        
        Args:
            user_id: The user's ID
            message: The user's message
            use_preferences: Whether to use user preferences
            
        Returns:
            Dict containing response, recipes, and context
        """
        if not CREWAI_AVAILABLE:
            return {
                "response": "CrewAI is not installed. Please install it to use the AI chat feature.",
                "recipes": [],
                "pantry_items": []
            }
        
        try:
            # Create tasks for the agents
            tasks = self._create_tasks(user_id, message, use_preferences)
            
            # Create and run the crew
            recipe_crew = Crew(
                agents=[
                    self.pantry_analyst,
                    self.recipe_finder,
                    self.recipe_evaluator,
                    self.conversation_agent
                ],
                tasks=tasks,
                process=Process.sequential,  # Tasks run in order
                verbose=True
            )
            
            # Execute the crew
            inputs = {
                "user_id": user_id,
                "user_message": message,
                "use_preferences": use_preferences
            }
            
            result = recipe_crew.kickoff(inputs=inputs)
            
            # Parse the result and format response
            return self._format_crew_response(result, user_id)
            
        except Exception as e:
            logger.error(f"Error in CrewAI service: {str(e)}")
            return {
                "response": "I encountered an error while finding recipes. Please try again.",
                "recipes": [],
                "pantry_items": [],
                "error": str(e)
            }
    
    def _create_tasks(self, user_id: int, message: str, use_preferences: bool) -> List[Task]:
        """Create tasks for the CrewAI agents"""
        
        # Task 1: Analyze pantry and preferences
        pantry_task = Task(
            description=f"""
            Analyze the pantry for user {user_id}:
            1. Fetch all pantry items using PostgresPantryTool
            2. Identify items expiring within 7 days
            3. {"Fetch user preferences and allergens" if use_preferences else "Skip preferences"}
            4. {"Analyze user's recipe history for patterns" if use_preferences else "Skip history analysis"}
            
            Return a summary of:
            - Total items and expiring items
            - {"Dietary restrictions and allergens" if use_preferences else "No preferences used"}
            - {"Favorite ingredients from history" if use_preferences else "No history analysis"}
            """,
            expected_output="Detailed pantry analysis with expiring items and user preferences",
            agent=self.pantry_analyst
        )
        
        # Task 2: Find recipes from multiple sources
        recipe_task = Task(
            description=f"""
            Based on the pantry analysis and user message: "{message}"
            
            1. First check saved recipes using SavedRecipeMatchTool
            2. Get 2 recipes from Spoonacular (respect dietary restrictions)
            3. Generate 2 creative recipes with OpenAI (prioritize expiring items)
            4. Ensure all recipes respect allergens and preferences
            
            User is asking about: {message}
            """,
            expected_output="A collection of recipes from saved, Spoonacular, and AI sources",
            agent=self.recipe_finder,
            context=[pantry_task]  # Depends on pantry analysis
        )
        
        # Task 3: Evaluate and rank recipes
        evaluation_task = Task(
            description="""
            Evaluate and rank all found recipes:
            1. Use RecipeRankerTool to score recipes
            2. Consider pantry match, user preferences, and history
            3. Prioritize recipes that use expiring ingredients
            4. Ensure variety in cuisine types
            
            Return top 5 recipes with scores and reasoning
            """,
            expected_output="Ranked list of top 5 recipes with evaluation scores",
            agent=self.recipe_evaluator,
            context=[pantry_task, recipe_task]  # Depends on both previous tasks
        )
        
        # Task 4: Format conversational response
        response_task = Task(
            description=f"""
            Create a helpful response for the user who asked: "{message}"
            
            1. Explain which recipes are recommended and why
            2. Mention if recipes use expiring ingredients
            3. Note which are from their saved collection
            4. Highlight any that match their preferences particularly well
            5. Be friendly and conversational
            
            Format as clear, helpful advice.
            """,
            expected_output="A friendly, informative response with recipe recommendations",
            agent=self.conversation_agent,
            context=[pantry_task, recipe_task, evaluation_task]  # Depends on all previous
        )
        
        return [pantry_task, recipe_task, evaluation_task, response_task]
    
    def _format_crew_response(self, crew_result: Any, user_id: int) -> Dict[str, Any]:
        """Format the crew result into the expected API response"""
        
        # Extract recipes from the crew result
        # This would need to parse the crew output
        recipes = []
        pantry_items = []
        
        # For now, return a structured response
        # In production, you'd parse the crew_result to extract the actual data
        
        return {
            "response": str(crew_result),  # The conversational response
            "recipes": recipes,  # Extracted recipe list
            "pantry_items": pantry_items,  # Pantry items used
            "user_preferences": {},  # User preferences if used
            "crew_raw_output": str(crew_result)  # Raw output for debugging
        }
    
    # Fallback method for when CrewAI is not available
    async def process_message_simple(self, user_id: int, message: str, use_preferences: bool = True) -> Dict[str, Any]:
        """Simple fallback when CrewAI is not available"""
        
        # Get pantry items
        pantry_query = """
        SELECT * FROM pantry_items 
        WHERE pantry_id = (SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s LIMIT 1)
        AND status = 'active'
        """
        pantry_items = self.db_service.execute_query(pantry_query, {"user_id": user_id})
        
        # Get saved recipes
        saved_recipes = await self.user_recipes_service.match_recipes_with_pantry(
            user_id=user_id,
            pantry_items=pantry_items,
            limit=5
        )
        
        # Simple response
        if saved_recipes:
            response = f"I found {len(saved_recipes)} recipes from your saved collection that match your pantry!"
        else:
            response = "Let me help you find some recipes based on your pantry items."
        
        return {
            "response": response,
            "recipes": saved_recipes[:5],
            "pantry_items": pantry_items[:10]
        }