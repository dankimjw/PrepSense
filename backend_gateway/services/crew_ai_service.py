"""
CrewAI Service for AI-powered recipe generation based on pantry items.
Integrates multiple AI agents to provide personalized dinner suggestions.
"""

import os
import warnings
from typing import List, Dict, Optional, Any
from datetime import datetime, date
import json
from functools import lru_cache

warnings.filterwarnings('ignore')

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend_gateway.core.config import get_settings
from backend_gateway.models.pantry import PantryItem
from backend_gateway.models.user import UserPreference
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.ai_recipe_cache_service import AIRecipeCacheService


settings = get_settings()


class PantryToolInput(BaseModel):
    """Input schema for pantry-related tools"""
    user_id: int = Field(..., description="The user ID for whom to fetch pantry items")


class PostgresPantryTool(BaseTool):
    """Tool for fetching pantry items from PostgreSQL database"""
    name: str = "PostgresPantryTool"
    description: str = "Fetches available pantry items for a user from PostgreSQL"
    args_schema: type[BaseModel] = PantryToolInput
    
    def __init__(self, db_service: PostgresService):
        super().__init__()
        self.db_service = db_service

    def _run(self, user_id: int) -> List[Dict]:
        """Fetch pantry items for user"""
        try:
            with self.db_service.get_session() as session:
                query = text("""
                    SELECT 
                        pi.id as pantry_item_id,
                        pi.name as product_name,
                        pi.quantity,
                        pi.quantity_consumed as used_quantity,
                        pi.unit,
                        pi.expiration_date,
                        pi.created_at,
                        pi.category
                    FROM pantry_items pi
                    WHERE pi.user_id = :user_id
                        AND pi.quantity > COALESCE(pi.quantity_consumed, 0)
                        AND pi.is_deleted = false
                    ORDER BY pi.expiration_date ASC
                """)
                
                result = session.execute(query, {"user_id": user_id})
                items = []
                for row in result:
                    item = {
                        "pantry_item_id": row.pantry_item_id,
                        "product_name": row.product_name,
                        "quantity": float(row.quantity) if row.quantity else 0,
                        "used_quantity": float(row.used_quantity) if row.used_quantity else 0,
                        "available_quantity": float(row.quantity or 0) - float(row.used_quantity or 0),
                        "unit": row.unit,
                        "expiration_date": row.expiration_date.isoformat() if row.expiration_date else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "category": row.category
                    }
                    items.append(item)
                return items
        except Exception as e:
            return [{"error": str(e)}]


class IngredientFilterTool(BaseTool):
    """Tool for filtering non-expired pantry items"""
    name: str = "IngredientFilterTool"
    description: str = "Filters pantry items to only include non-expired, available items"
    args_schema: type[BaseModel] = PantryToolInput
    
    def __init__(self, db_service: PostgresService):
        super().__init__()
        self.db_service = db_service

    def _run(self, user_id: int) -> List[Dict]:
        """Filter pantry items for non-expired, available items"""
        try:
            with self.db_service.get_session() as session:
                query = text("""
                    SELECT 
                        pi.id as pantry_item_id,
                        pi.name as product_name,
                        pi.quantity,
                        pi.quantity_consumed as used_quantity,
                        pi.unit,
                        pi.expiration_date,
                        pi.created_at,
                        pi.category
                    FROM pantry_items pi
                    WHERE pi.user_id = :user_id
                        AND pi.quantity > COALESCE(pi.quantity_consumed, 0)
                        AND (pi.expiration_date IS NULL OR pi.expiration_date >= CURRENT_DATE)
                        AND pi.is_deleted = false
                    ORDER BY pi.expiration_date ASC
                """)
                
                result = session.execute(query, {"user_id": user_id})
                items = []
                for row in result:
                    item = {
                        "pantry_item_id": row.pantry_item_id,
                        "product_name": row.product_name,
                        "quantity": float(row.quantity) if row.quantity else 0,
                        "used_quantity": float(row.used_quantity) if row.used_quantity else 0,
                        "available_quantity": float(row.quantity or 0) - float(row.used_quantity or 0),
                        "unit": row.unit,
                        "expiration_date": row.expiration_date.isoformat() if row.expiration_date else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "category": row.category
                    }
                    items.append(item)
                return items
        except Exception as e:
            return [{"error": str(e)}]


class UserRestrictionToolInput(BaseModel):
    """Input schema for user restriction tool"""
    user_id: int


class UserRestrictionTool(BaseTool):
    """Tool for fetching user dietary preferences and allergens"""
    name: str = "UserPreferenceTool"
    description: str = "Fetches dietary restrictions and allergens for a user"
    args_schema: type[BaseModel] = UserRestrictionToolInput
    
    def __init__(self, db_service: PostgresService):
        super().__init__()
        self.db_service = db_service

    def _run(self, user_id: int) -> Dict:
        """Fetch user dietary preferences"""
        try:
            with self.db_service.get_session() as session:
                query = text("""
                    SELECT 
                        dietary_preferences,
                        allergies,
                        household_size,
                        cooking_skill_level
                    FROM user_preferences
                    WHERE user_id = :user_id
                """)
                
                result = session.execute(query, {"user_id": user_id}).fetchone()
                
                if result:
                    return {
                        "dietary_preferences": result.dietary_preferences or [],
                        "allergens": result.allergies or [],
                        "household_size": result.household_size,
                        "cooking_skill_level": result.cooking_skill_level
                    }
                else:
                    return {"message": "No dietary data found for this user."}
        except Exception as e:
            return {"error": str(e)}


class CrewAIService:
    """Service for AI-powered recipe generation using CrewAI"""
    
    def __init__(self):
        self.db_service = PostgresService()
        self.cache_service = AIRecipeCacheService()
        self._initialize_tools()
        self._initialize_agents()
        
    def _initialize_tools(self):
        """Initialize all tools used by agents"""
        # Database tools
        self.pantry_tool = PostgresPantryTool(self.db_service)
        self.ingredient_filter_tool = IngredientFilterTool(self.db_service)
        self.user_restriction_tool = UserRestrictionTool(self.db_service)
        
        # External tools (only initialize if API keys are available)
        self.search_tool = None
        self.scrape_tool = None
        
        if settings.SERPER_API_KEY:
            self.search_tool = SerperDevTool(api_key=settings.SERPER_API_KEY)
            self.scrape_tool = ScrapeWebsiteTool()
    
    def _initialize_agents(self):
        """Initialize all AI agents"""
        # Pantry Scan Agent
        self.pantry_scan_agent = Agent(
            role="Pantry Scan Agent",
            goal="Retrieve list of available ingredients for user ID {user_id} from PostgreSQL database",
            tools=[self.pantry_tool],
            verbose=True,
            backstory="You have access to the PrepSense database and can extract pantry contents efficiently."
        )
        
        # Ingredient Filter Agent
        self.ingredient_filter_agent = Agent(
            role="Ingredient Filter Agent",
            goal="Filter out expired or unusable items from the pantry list",
            tools=[self.ingredient_filter_tool],
            verbose=True,
            backstory="You ensure only fresh and usable ingredients are considered for recipes."
        )
        
        # Recipe Search Agent
        recipe_tools = [self.ingredient_filter_tool]
        if self.search_tool and self.scrape_tool:
            recipe_tools.extend([self.search_tool, self.scrape_tool])
            
        self.recipe_search_agent = Agent(
            role="Recipe Search Agent",
            goal="Find recipes that can be made using the filtered ingredients",
            tools=recipe_tools,
            verbose=True,
            backstory="You search for recipes that maximize the use of available ingredients."
        )
        
        # Nutritional Agent
        nutrition_tools = [self.search_tool] if self.search_tool else []
        self.nutritional_agent = Agent(
            role="Nutritional Agent",
            goal="Evaluate the nutritional balance of each proposed recipe",
            tools=nutrition_tools,
            verbose=True,
            backstory="You ensure dinner suggestions are healthy and balanced."
        )
        
        # User Preferences Agent
        self.user_preferences_agent = Agent(
            role="User Preferences Agent",
            goal="Filter recipes based on dietary restrictions and allergens",
            tools=[self.user_restriction_tool],
            verbose=True,
            backstory="You ensure recipes comply with user's health requirements."
        )
        
        # Recipe Scoring Agent
        self.recipe_scoring_agent = Agent(
            role="Recipe Scoring Agent",
            goal="Score recipes based on ingredient match, nutrition, and preferences",
            tools=[],
            verbose=True,
            backstory="You rank recipes to help users make the best choice."
        )
        
        # Response Formatting Agent
        self.response_formatting_agent = Agent(
            role="Response Formatting Agent",
            goal="Format recipe suggestions for user-friendly viewing",
            tools=[],
            verbose=True,
            backstory="You present recipes in a clear, appealing format."
        )
    
    def _create_task(self, agent: Agent, description: str, expected_output: str, 
                     input_variables: Optional[List[str]] = None) -> Task:
        """Create a task for an agent"""
        return Task(
            description=description,
            expected_output=expected_output,
            human_input=False,
            agent=agent,
            input_variables=input_variables or []
        )
    
    def generate_recipes(self, user_id: int, max_recipes: int = 3) -> Dict[str, Any]:
        """Generate recipe suggestions for a user based on their pantry"""
        try:
            # First get pantry items and preferences for cache key
            pantry_items = self.ingredient_filter_tool._run(user_id)
            preferences = self.user_restriction_tool._run(user_id)
            
            # Check cache first
            cached_result = self.cache_service.get_cached_recipes(
                user_id, pantry_items, preferences, max_recipes
            )
            
            if cached_result:
                return cached_result
            # Create tasks for the crew
            tasks = [
                self._create_task(
                    self.pantry_scan_agent,
                    "Query database for available ingredients for user_id {user_id}",
                    "List of pantry ingredients with quantities and expiration dates",
                    input_variables=["user_id"]
                ),
                self._create_task(
                    self.ingredient_filter_agent,
                    "Filter out expired items and ensure adequate quantities",
                    "List of usable ingredients with available quantities",
                    input_variables=["user_id"]
                ),
                self._create_task(
                    self.recipe_search_agent,
                    f"Find {max_recipes + 2} dinner recipes using available ingredients",
                    f"List of at least {max_recipes + 2} suitable recipes"
                ),
                self._create_task(
                    self.nutritional_agent,
                    "Evaluate nutritional value of each recipe",
                    "Nutritional analysis for each recipe"
                ),
                self._create_task(
                    self.user_preferences_agent,
                    "Filter recipes based on dietary restrictions for user_id {user_id}",
                    "List of recipes safe for user consumption",
                    input_variables=["user_id"]
                ),
                self._create_task(
                    self.recipe_scoring_agent,
                    "Score and rank recipes based on all criteria",
                    f"Top {max_recipes} ranked recipes"
                ),
                self._create_task(
                    self.response_formatting_agent,
                    f"Format top {max_recipes} recipes with details",
                    "Formatted recipe suggestions in JSON"
                )
            ]
            
            # Create and run the crew
            pantry_dinner_crew = Crew(
                agents=[
                    self.pantry_scan_agent,
                    self.ingredient_filter_agent,
                    self.recipe_search_agent,
                    self.nutritional_agent,
                    self.user_preferences_agent,
                    self.recipe_scoring_agent,
                    self.response_formatting_agent
                ],
                tasks=tasks,
                verbose=True
            )
            
            # Execute the crew
            inputs = {"user_id": user_id}
            result = pantry_dinner_crew.kickoff(inputs=inputs)
            
            # Parse and structure the result
            parsed_recipes = self._parse_crew_result(result)
            
            # Cache the results
            if parsed_recipes:
                self.cache_service.cache_recipes(
                    user_id=user_id,
                    pantry_items=pantry_items,
                    preferences=preferences,
                    recipes=parsed_recipes,
                    max_recipes=max_recipes,
                    metadata={
                        "generated_at": datetime.now().isoformat(),
                        "crew_version": "1.0"
                    }
                )
            
            return {
                "success": True,
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "recipes": parsed_recipes,
                "cached": False,
                "raw_result": str(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def _parse_crew_result(self, result: Any) -> List[Dict]:
        """Parse the crew result into structured recipe data"""
        # This is a placeholder - actual parsing depends on crew output format
        # In production, this would parse the formatted output from the crew
        try:
            # Attempt to extract structured data from result
            if isinstance(result, str):
                # Try to find JSON in the result
                import re
                json_match = re.search(r'\[.*\]', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            return []
        except:
            return []
    
    def get_pantry_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of user's pantry for recipe generation"""
        try:
            # Get all items
            all_items = self.pantry_tool._run(user_id)
            # Get non-expired items
            fresh_items = self.ingredient_filter_tool._run(user_id)
            # Get user preferences
            preferences = self.user_restriction_tool._run(user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "total_items": len(all_items),
                "fresh_items": len(fresh_items),
                "preferences": preferences,
                "items_by_category": self._group_by_category(fresh_items)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def _group_by_category(self, items: List[Dict]) -> Dict[str, List[str]]:
        """Group items by category"""
        grouped = {}
        for item in items:
            category = item.get("category", "Other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(item.get("product_name", "Unknown"))
        return grouped