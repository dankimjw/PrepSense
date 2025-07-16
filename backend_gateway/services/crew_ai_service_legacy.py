"""
CrewAI Service Legacy - Compatible with CrewAI 0.1.32
Uses simple LangChain tools instead of custom CrewAI tools
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime

# CrewAI imports
try:
    from crewai import Agent, Task, Crew
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = None

# Service imports
from backend_gateway.config.database import get_database_service
from backend_gateway.services.user_recipes_service import UserRecipesService
from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.services.preference_analyzer_service import PreferenceAnalyzerService

# Legacy tool imports
from backend_gateway.services.crewai_tools_legacy import (
    create_pantry_tool,
    create_preferences_tool,
    create_saved_recipes_tool,
    create_openai_recipe_tool,
    create_recipe_ranker_tool
)

logger = logging.getLogger(__name__)


class CrewAIServiceLegacy:
    """Legacy CrewAI service compatible with version 0.1.32"""
    
    def __init__(self):
        """Initialize the CrewAI service with all necessary components"""
        # Initialize services
        self.db_service = get_database_service()
        self.user_recipes_service = UserRecipesService(self.db_service)
        self.spoonacular_service = SpoonacularService()
        self.preference_analyzer_service = PreferenceAnalyzerService(self.db_service)
        
        # Initialize tools
        self.pantry_tool = create_pantry_tool(self.db_service)
        self.preferences_tool = create_preferences_tool(self.db_service)
        self.saved_recipes_tool = create_saved_recipes_tool(self.user_recipes_service)
        self.openai_tool = create_openai_recipe_tool()
        self.ranker_tool = create_recipe_ranker_tool()
        
        # Initialize agents later when needed
        self._agents_initialized = False
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not installed. Install with: pip install crewai==0.1.32")
    
    def _initialize_agents(self):
        """Initialize the agents for recipe recommendation"""
        if self._agents_initialized:
            return
            
        # Make sure OpenAI API key is available
        import os
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment")
            return
        
        # 1. Pantry Analyst Agent
        self.pantry_analyst = Agent(
            role='Pantry Analyst',
            goal='Analyze pantry inventory and user preferences',
            backstory="""You are an expert at understanding what's in someone's pantry 
            and their food preferences. You identify expiring items and categorize ingredients.""",
            tools=[self.pantry_tool, self.preferences_tool],
            verbose=True
        )
        
        # 2. Recipe Finder Agent
        self.recipe_finder = Agent(
            role='Recipe Finder',
            goal='Find the best recipes from saved recipes and generate new ones',
            backstory="""You are a culinary expert who finds perfect recipes.
            You check saved recipes and create new options based on available ingredients.""",
            tools=[self.saved_recipes_tool, self.openai_tool],
            verbose=True
        )
        
        # 3. Recipe Advisor Agent
        self.recipe_advisor = Agent(
            role='Recipe Advisor',
            goal='Provide helpful recipe recommendations',
            backstory="""You are a friendly kitchen assistant who helps people decide what 
            to cook. You explain why certain recipes are recommended.""",
            tools=[],
            verbose=True
        )
        
        self._agents_initialized = True
    
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
            return await self.process_message_simple(user_id, message, use_preferences)
        
        # Initialize agents if not already done
        if not self._agents_initialized:
            self._initialize_agents()
            if not self._agents_initialized:
                logger.error("Failed to initialize CrewAI agents")
                return await self.process_message_simple(user_id, message, use_preferences)
        
        try:
            # Create tasks for the agents
            tasks = self._create_tasks(user_id, message, use_preferences)
            
            # Create and run the crew
            recipe_crew = Crew(
                agents=[
                    self.pantry_analyst,
                    self.recipe_finder,
                    self.recipe_advisor
                ],
                tasks=tasks,
                verbose=True
            )
            
            # Execute the crew
            result = recipe_crew.kickoff()
            
            # Get recipes separately since crew result is just text
            recipes = await self._get_all_recipes(user_id)
            
            return {
                "response": str(result),
                "recipes": recipes[:5],  # Top 5 recipes
                "pantry_items": self._get_pantry_items(user_id),
                "crew_output": str(result)
            }
            
        except Exception as e:
            logger.error(f"Error in CrewAI service: {str(e)}")
            # Fallback to simple method
            return await self.process_message_simple(user_id, message, use_preferences)
    
    def _create_tasks(self, user_id: int, message: str, use_preferences: bool) -> List[Task]:
        """Create tasks for the CrewAI agents"""
        
        # Task 1: Analyze pantry
        pantry_task = Task(
            description=f"""
            Analyze the pantry for user {user_id}:
            1. Use fetch_pantry_items tool with user_id: {user_id}
            2. Identify items expiring within 7 days
            3. {'Use fetch_preferences tool to get dietary restrictions' if use_preferences else 'Skip preferences'}
            
            Provide a summary of findings.
            """,
            agent=self.pantry_analyst
        )
        
        # Task 2: Find recipes
        recipe_task = Task(
            description=f"""
            Based on the pantry analysis and user message: "{message}"
            
            1. Use fetch_saved_recipes tool with input: {user_id}|pantry_items
            2. Generate 2 new recipes using generate_recipe tool with expiring ingredients
            3. Focus on practical, common dishes
            
            The user asked: {message}
            """,
            agent=self.recipe_finder
        )
        
        # Task 3: Create response
        response_task = Task(
            description=f"""
            Create a helpful response for the user who asked: "{message}"
            
            Based on the pantry analysis and recipes found:
            1. Recommend the best recipes and explain why
            2. Mention if recipes use expiring ingredients
            3. Be friendly and conversational
            
            Format as clear, helpful advice.
            """,
            agent=self.recipe_advisor
        )
        
        return [pantry_task, recipe_task, response_task]
    
    def _get_pantry_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Get pantry items for a user"""
        query = """
        SELECT * FROM pantry_items 
        WHERE pantry_id IN (SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s)
        AND status = 'available'
        """
        return self.db_service.execute_query(query, {"user_id": user_id})
    
    async def _get_all_recipes(self, user_id: int) -> List[Dict[str, Any]]:
        """Get recipes from saved collection"""
        pantry_items = self._get_pantry_items(user_id)
        
        # Get saved recipes
        saved_recipes = await self.user_recipes_service.match_recipes_with_pantry(
            user_id=user_id,
            pantry_items=pantry_items[:20],
            limit=5
        )
        
        return saved_recipes
    
    # Fallback method for when CrewAI is not available
    async def process_message_simple(self, user_id: int, message: str, use_preferences: bool = True) -> Dict[str, Any]:
        """Simple fallback when CrewAI is not available"""
        
        # Get pantry items
        pantry_items = self._get_pantry_items(user_id)
        
        # Get saved recipes
        saved_recipes = await self.user_recipes_service.match_recipes_with_pantry(
            user_id=user_id,
            pantry_items=pantry_items[:20],
            limit=5
        )
        
        # Create a simple response
        expiring = sum(1 for item in pantry_items if item.get('expiration_date') and 
                      (datetime.now().date() - item['expiration_date']).days <= 7)
        
        response = f"I found {len(saved_recipes)} recipes from your saved collection"
        if expiring > 0:
            response += f" and you have {expiring} items expiring soon"
        response += "! Here are my recommendations based on your pantry items."
        
        return {
            "response": response,
            "recipes": saved_recipes[:5],
            "pantry_items": pantry_items[:10]
        }