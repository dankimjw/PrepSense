"""
CrewAI Service for AI-powered recipe generation based on pantry items.
Integrates multiple AI agents to provide personalized dinner suggestions.
"""

import json
import logging
import os
import warnings
from datetime import date, datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend_gateway.core.config import get_settings
from backend_gateway.models.pantry import PantryItem
from backend_gateway.models.user import UserPreference
from backend_gateway.services.ai_recipe_cache_service import AIRecipeCacheService
from backend_gateway.services.environmental_impact_service import EnvironmentalImpactService
from backend_gateway.services.food_waste_service import FoodWasteService
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.smart_unit_validator import SmartUnitValidator

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
                query = text(
                    """
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
                """
                )

                result = session.execute(query, {"user_id": user_id})
                items = []
                for row in result:
                    item = {
                        "pantry_item_id": row.pantry_item_id,
                        "product_name": row.product_name,
                        "quantity": float(row.quantity) if row.quantity else 0,
                        "used_quantity": float(row.used_quantity) if row.used_quantity else 0,
                        "available_quantity": float(row.quantity or 0)
                        - float(row.used_quantity or 0),
                        "unit": row.unit,
                        "expiration_date": (
                            row.expiration_date.isoformat() if row.expiration_date else None
                        ),
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "category": row.category,
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
                query = text(
                    """
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
                """
                )

                result = session.execute(query, {"user_id": user_id})
                items = []
                for row in result:
                    item = {
                        "pantry_item_id": row.pantry_item_id,
                        "product_name": row.product_name,
                        "quantity": float(row.quantity) if row.quantity else 0,
                        "used_quantity": float(row.used_quantity) if row.used_quantity else 0,
                        "available_quantity": float(row.quantity or 0)
                        - float(row.used_quantity or 0),
                        "unit": row.unit,
                        "expiration_date": (
                            row.expiration_date.isoformat() if row.expiration_date else None
                        ),
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "category": row.category,
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
                query = text(
                    """
                    SELECT 
                        dietary_preferences,
                        allergies,
                        household_size,
                        cooking_skill_level
                    FROM user_preferences
                    WHERE user_id = :user_id
                """
                )

                result = session.execute(query, {"user_id": user_id}).fetchone()

                if result:
                    return {
                        "dietary_preferences": result.dietary_preferences or [],
                        "allergens": result.allergies or [],
                        "household_size": result.household_size,
                        "cooking_skill_level": result.cooking_skill_level,
                    }
                else:
                    return {"message": "No dietary data found for this user."}
        except Exception as e:
            return {"error": str(e)}


class SustainabilityToolInput(BaseModel):
    """Input schema for sustainability evaluation tool"""

    ingredients: List[Dict[str, Any]] = Field(..., description="List of ingredients to evaluate")


class FoodCategorizationToolInput(BaseModel):
    """Input schema for food categorization tool"""

    food_name: str = Field(..., description="Name of the food item to categorize")
    current_category: Optional[str] = Field(None, description="Current category if known")


class FoodCategorizationTool(BaseTool):
    """Tool for accurately categorizing food items"""

    name: str = "FoodCategorizationTool"
    description: str = "Categorizes food items into appropriate categories based on their nature"
    args_schema: type[BaseModel] = FoodCategorizationToolInput

    def __init__(self, db_service: PostgresService):
        super().__init__()
        self.db_service = db_service

        # Category rules based on keywords and patterns
        self.category_rules = {
            "Beverages": [
                "broth",
                "stock",
                "juice",
                "milk",
                "water",
                "tea",
                "coffee",
                "soda",
                "drink",
            ],
            "Soups & Broths": ["soup", "broth", "stock", "bouillon", "consomme"],
            "Produce": [
                "apple",
                "banana",
                "strawberry",
                "tomato",
                "lettuce",
                "carrot",
                "fruit",
                "vegetable",
            ],
            "Dairy and Egg Products": ["cheese", "yogurt", "butter", "cream", "egg", "milk"],
            "Meat": ["chicken breast", "beef", "pork", "lamb", "turkey", "steak", "ground beef"],
            "Pantry": ["flour", "sugar", "salt", "pepper", "oil", "vinegar", "pasta", "rice"],
            "Frozen": ["frozen", "ice cream"],
            "Bakery": ["bread", "bagel", "muffin", "cake", "cookie"],
            "Condiments": ["ketchup", "mustard", "mayo", "sauce", "dressing"],
            "Spices and Herbs": ["oregano", "basil", "thyme", "cinnamon", "paprika", "spice"],
        }

    def _run(self, food_name: str, current_category: Optional[str] = None) -> Dict:
        """Categorize a food item"""
        try:
            food_lower = food_name.lower()

            # Check for specific patterns first
            if any(word in food_lower for word in ["broth", "stock"]):
                category = "Soups & Broths"
                confidence = 0.95
                reason = "Contains 'broth' or 'stock' - these are liquid soup bases, not meat"
            else:
                # Find best matching category
                best_category = current_category or "Other"
                best_score = 0

                for category, keywords in self.category_rules.items():
                    score = sum(1 for keyword in keywords if keyword in food_lower)
                    if score > best_score:
                        best_score = score
                        best_category = category

                confidence = min(best_score * 0.3, 0.9) if best_score > 0 else 0.3
                reason = f"Matched {best_score} keywords for {best_category}"

            return {
                "food_name": food_name,
                "suggested_category": best_category,
                "current_category": current_category,
                "confidence": confidence,
                "reason": reason,
                "needs_correction": current_category and current_category != best_category,
            }

        except Exception as e:
            return {"error": str(e)}


class UnitCorrectionToolInput(BaseModel):
    """Input schema for unit correction tool"""

    food_name: str = Field(..., description="Name of the food item")
    category: str = Field(..., description="Food category")
    current_unit: str = Field(..., description="Current unit of measurement")


class RecipeSearchToolInput(BaseModel):
    """Input schema for recipe search tool"""

    ingredients: List[str] = Field(..., description="List of available ingredients")
    max_recipes: int = Field(5, description="Maximum number of recipes to return")


class SpoonacularRecipeTool(BaseTool):
    """Tool for searching recipes using Spoonacular API or database"""

    name: str = "SpoonacularRecipeTool"
    description: str = (
        "Searches for recipes using available ingredients via Spoonacular API or local database"
    )
    args_schema: type[BaseModel] = RecipeSearchToolInput

    def __init__(self, db_service: PostgresService):
        super().__init__()
        self.db_service = db_service
        # Import here to avoid circular imports
        from backend_gateway.services.recipe_service import RecipeService
        from backend_gateway.services.spoonacular_service import SpoonacularService

        self.spoonacular = SpoonacularService()
        self.recipe_service = RecipeService()

    def _run(self, ingredients: List[str], max_recipes: int = 5) -> List[Dict]:
        """Search for recipes using ingredients"""
        try:
            # First try Spoonacular API
            if self.spoonacular.api_key:
                # Use Spoonacular's findByIngredients endpoint
                recipes = self.spoonacular.find_recipes_by_ingredients(
                    ingredients=ingredients,
                    number=max_recipes,
                    ranking=2,  # Maximize used ingredients
                )

                if recipes:
                    return [self._format_spoonacular_recipe(r) for r in recipes]

            # Fallback to database search
            with self.db_service.get_session() as session:
                # Search recipes in database that use these ingredients
                query = text(
                    """
                    SELECT DISTINCT r.*, 
                           COUNT(DISTINCT ri.ingredient_name) as matched_ingredients
                    FROM recipes r
                    JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                    WHERE LOWER(ri.ingredient_name) = ANY(:ingredients)
                    GROUP BY r.id
                    ORDER BY matched_ingredients DESC
                    LIMIT :limit
                """
                )

                result = session.execute(
                    query,
                    {"ingredients": [ing.lower() for ing in ingredients], "limit": max_recipes},
                )

                recipes = []
                for row in result:
                    recipes.append(
                        {
                            "id": row.id,
                            "title": row.title,
                            "readyInMinutes": row.ready_in_minutes,
                            "servings": row.servings,
                            "matched_ingredients": row.matched_ingredients,
                            "source": "database",
                        }
                    )

                return recipes

        except Exception as e:
            logger.error(f"Recipe search error: {str(e)}")
            return []

    def _format_spoonacular_recipe(self, recipe: Dict) -> Dict:
        """Format Spoonacular recipe for consistency"""
        return {
            "id": recipe.get("id"),
            "title": recipe.get("title"),
            "readyInMinutes": recipe.get("readyInMinutes", 30),
            "servings": recipe.get("servings", 4),
            "usedIngredientCount": recipe.get("usedIngredientCount", 0),
            "missedIngredientCount": recipe.get("missedIngredientCount", 0),
            "source": "spoonacular",
        }


class UnitCorrectionTool(BaseTool):
    """Tool for suggesting appropriate units based on food category"""

    name: str = "UnitCorrectionTool"
    description: str = "Suggests appropriate units of measurement based on food category"
    args_schema: type[BaseModel] = UnitCorrectionToolInput

    def __init__(self):
        super().__init__()
        self.validator = SmartUnitValidator(None)  # Uses rules without DB

    def _run(self, food_name: str, category: str, current_unit: str) -> Dict:
        """Suggest appropriate unit for food item"""
        try:
            # Get category rules
            category_rules = self.validator.category_unit_rules.get(category, {})
            default_rules = category_rules.get(
                "default", category_rules.get(list(category_rules.keys())[0], {})
            )

            allowed_units = default_rules.get("allowed", [])
            forbidden_units = default_rules.get("forbidden", [])
            preferred_units = default_rules.get("preferred", [])

            # Check if current unit is appropriate
            is_valid = current_unit in allowed_units and current_unit not in forbidden_units

            # Suggest best unit
            if preferred_units:
                suggested_unit = preferred_units[0]
            elif allowed_units:
                suggested_unit = allowed_units[0]
            else:
                suggested_unit = current_unit

            return {
                "food_name": food_name,
                "category": category,
                "current_unit": current_unit,
                "suggested_unit": suggested_unit,
                "is_valid": is_valid,
                "allowed_units": allowed_units,
                "forbidden_units": forbidden_units,
                "reason": default_rules.get("examples", "Standard units for this category"),
            }

        except Exception as e:
            return {"error": str(e)}


class SustainabilityTool(BaseTool):
    """Tool for evaluating environmental impact and food waste"""

    name: str = "SustainabilityTool"
    description: str = "Evaluates environmental impact and food waste potential of ingredients"
    args_schema: type[BaseModel] = SustainabilityToolInput

    def __init__(self):
        super().__init__()
        self.env_service = EnvironmentalImpactService()
        self.waste_service = FoodWasteService()

    def _run(self, ingredients: List[Dict[str, Any]]) -> Dict:
        """Evaluate sustainability metrics for ingredients"""
        try:
            sustainability_data = {
                "total_ghg_emissions": 0.0,
                "total_water_usage": 0.0,
                "total_land_usage": 0.0,
                "waste_reduction_score": 0.0,
                "ingredient_impacts": [],
                "recommendations": [],
            }

            for ingredient in ingredients:
                name = ingredient.get("product_name", "")
                quantity = float(ingredient.get("available_quantity", 0))
                expiration = ingredient.get("expiration_date")

                # Get environmental impact
                impact = self.env_service.get_impact_for_food(name)
                if impact:
                    # Calculate impact based on quantity (convert to kg)
                    kg_quantity = self._convert_to_kg(quantity, ingredient.get("unit", ""))

                    ingredient_impact = {
                        "name": name,
                        "ghg_emissions": impact.get("ghg", 0) * kg_quantity,
                        "water_usage": impact.get("water", 0) * kg_quantity,
                        "land_usage": impact.get("land", 0) * kg_quantity,
                    }

                    sustainability_data["total_ghg_emissions"] += ingredient_impact["ghg_emissions"]
                    sustainability_data["total_water_usage"] += ingredient_impact["water_usage"]
                    sustainability_data["total_land_usage"] += ingredient_impact["land_usage"]
                    sustainability_data["ingredient_impacts"].append(ingredient_impact)

                # Check expiration for waste reduction
                if expiration:
                    from datetime import datetime

                    exp_date = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
                    days_until_expiry = (exp_date - datetime.now()).days

                    if days_until_expiry <= 3:
                        sustainability_data["waste_reduction_score"] += 10
                        sustainability_data["recommendations"].append(
                            f"Using {name} helps prevent food waste (expires in {days_until_expiry} days)"
                        )

            # Add general recommendations
            if sustainability_data["total_ghg_emissions"] < 5:
                sustainability_data["recommendations"].append("Low carbon footprint recipe!")
            elif sustainability_data["total_ghg_emissions"] > 15:
                sustainability_data["recommendations"].append(
                    "Consider plant-based alternatives to reduce emissions"
                )

            return sustainability_data

        except Exception as e:
            return {"error": str(e)}

    def _convert_to_kg(self, quantity: float, unit: str) -> float:
        """Convert various units to kg for impact calculation"""
        conversions = {
            "lb": 0.453592,
            "oz": 0.0283495,
            "g": 0.001,
            "kg": 1.0,
            "l": 1.0,  # Approximate for liquids
            "ml": 0.001,
            "gallon": 3.78541,
            "quart": 0.946353,
            "pint": 0.473176,
        }
        return quantity * conversions.get(unit.lower(), 1.0)


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
        self.sustainability_tool = SustainabilityTool()
        self.categorization_tool = FoodCategorizationTool(self.db_service)
        self.unit_correction_tool = UnitCorrectionTool()
        self.spoonacular_tool = SpoonacularRecipeTool(self.db_service)

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
            backstory="You have access to the PrepSense database and can extract pantry contents efficiently.",
        )

        # Food Categorization Agent
        self.food_categorization_agent = Agent(
            role="Food Category Expert",
            goal="Accurately categorize food items into appropriate categories",
            tools=[self.categorization_tool],
            verbose=True,
            backstory="""You are an expert in food classification with deep knowledge of grocery store layouts and food types.
            
            Critical categorization rules:
            - 'Chicken Broth', 'Beef Stock' → Soups & Broths (NOT Meat)
            - 'Strawberries', 'Apples' → Produce (NOT Beverages)
            - 'Cheese', 'Yogurt' → Dairy (even if measured in slices)
            - 'Tomato Sauce' → Condiments (NOT Produce)
            - Consider the primary use and form of the item
            
            You understand subtle differences like Pacific Organic Low Sodium Chicken Broth being a liquid soup base, not meat.""",
        )

        # Unit Correction Agent
        self.unit_correction_agent = Agent(
            role="Unit Measurement Expert",
            goal="Suggest appropriate units based on food category",
            tools=[self.unit_correction_tool],
            verbose=True,
            backstory="""You ensure foods are measured in sensible, retail-standard units.
            
            Unit correction rules:
            - Produce: lb, oz, each, bunch (NEVER ml for strawberries)
            - Liquids/Broths: fl oz, quart, gallon (NEVER each)
            - Dairy liquids: gallon, quart (milk), solids: oz, lb (cheese)
            - Eggs: dozen, each (NEVER by weight)
            - Spices: tsp, tbsp, oz (NEVER gallons)
            
            You fix common OCR/input errors and ensure units match how items are sold in stores.""",
        )

        # Ingredient Filter Agent
        self.ingredient_filter_agent = Agent(
            role="Ingredient Filter Agent",
            goal="Filter out expired or unusable items from the pantry list",
            tools=[self.ingredient_filter_tool],
            verbose=True,
            backstory="You ensure only fresh and usable ingredients are considered for recipes.",
        )

        # Recipe Search Agent
        self.recipe_search_agent = Agent(
            role="Recipe Search Agent",
            goal="Find recipes using Spoonacular API or database that match available ingredients",
            tools=[self.spoonacular_tool],
            verbose=True,
            backstory="""You search for recipes using the Spoonacular API or local database.
            
            SEARCH STRATEGY:
            1. Use SpoonacularRecipeTool to find recipes by ingredients
            2. Prioritize recipes that use expiring ingredients
            3. Look for recipes that maximize ingredient usage
            4. The tool automatically tries Spoonacular first, then database
            
            IMPORTANT UNIT GUIDELINES (for recipe output):
            - Produce (fruits/vegetables): Use lb, oz, each, container (NEVER ml or liters)
            - Dairy liquids: Use gallon, quart, pint, fl oz (milk, cream)
            - Dairy solids: Use oz, lb, slice (cheese, butter)
            - Eggs: Use dozen or each (NEVER by weight)
            - Beverages: Use ml, l, bottle, can (NEVER lb or each)
            - Meat/Poultry: Use lb, oz, piece (NEVER ml or each)
            - Spices: Use tsp, tbsp, oz, jar (NEVER lb or gallon)
            
            Focus on finding practical, cookable recipes from reliable sources.""",
        )

        # Nutritional Agent
        nutrition_tools = [self.search_tool] if self.search_tool else []
        self.nutritional_agent = Agent(
            role="Nutritional Agent",
            goal="Evaluate the nutritional balance of each proposed recipe using proper food units",
            tools=nutrition_tools,
            verbose=True,
            backstory="""You ensure dinner suggestions are healthy and balanced.
            
            When analyzing nutrition, use proper units:
            - Produce servings: 1 cup = ~4 oz for most vegetables, 1 medium fruit = ~6 oz
            - Protein portions: 3-4 oz cooked meat = 1 serving
            - Dairy: 1 cup milk = 8 fl oz, 1 oz cheese = 1 serving
            - Convert unusual units to standard nutritional portions
            
            Example: "500 ml strawberries" should be analyzed as "~1 lb or 3 cups" for nutrition calculations.""",
        )

        # User Preferences Agent
        self.user_preferences_agent = Agent(
            role="User Preferences Agent",
            goal="Filter recipes based on dietary restrictions and allergens",
            tools=[self.user_restriction_tool],
            verbose=True,
            backstory="You ensure recipes comply with user's health requirements.",
        )

        # Recipe Scoring Agent
        self.recipe_scoring_agent = Agent(
            role="Recipe Scoring Agent",
            goal="Score recipes based on ingredient match, nutrition, and preferences",
            tools=[],
            verbose=True,
            backstory="You rank recipes to help users make the best choice.",
        )

        # Sustainability Agent
        self.sustainability_agent = Agent(
            role="Sustainability Agent",
            goal="Evaluate environmental impact and food waste reduction potential of recipes",
            tools=[self.sustainability_tool],
            verbose=True,
            backstory="""You are an environmental and food waste expert who evaluates recipes for sustainability.
            
            Your responsibilities:
            1. Calculate carbon footprint (GHG emissions) for each recipe
            2. Assess water and land usage impact
            3. Prioritize recipes using expiring ingredients to reduce waste
            4. Provide eco-friendly recommendations
            
            Scoring guidelines:
            - Low emissions (<5 kg CO2e): Excellent eco-score
            - Medium emissions (5-15 kg CO2e): Moderate eco-score
            - High emissions (>15 kg CO2e): Poor eco-score
            - Add bonus points for using expiring ingredients
            - Favor plant-based over animal products
            - Consider seasonal and local ingredients
            
            Always provide actionable sustainability tips with each recipe evaluation.""",
        )

        # Response Formatting Agent
        self.response_formatting_agent = Agent(
            role="Response Formatting Agent",
            goal="Format recipe suggestions with proper units for user-friendly viewing",
            tools=[],
            verbose=True,
            backstory="""You present recipes in a clear, appealing format with correct units.
            
            FORMATTING RULES:
            - Always display produce in lb/oz/each (e.g., "2 lb strawberries" not "1000 ml")
            - Show dairy liquids in standard US units (gallon, quart, pint)
            - Display eggs as dozen/each, meat in lb/oz
            - Keep units consistent with how items are sold in stores
            - Round quantities to practical amounts (0.5 lb not 0.4823 lb)
            
            SUSTAINABILITY FORMATTING:
            - Include eco_score (A-E rating based on emissions)
            - Show carbon_footprint in kg CO2e
            - Highlight waste_reduction_bonus if using expiring items
            - Add sustainability_tips array with actionable advice
            
            Output recipes in JSON format with proper units and sustainability metrics.""",
        )

    def _create_task(
        self,
        agent: Agent,
        description: str,
        expected_output: str,
        input_variables: Optional[List[str]] = None,
    ) -> Task:
        """Create a task for an agent"""
        return Task(
            description=description,
            expected_output=expected_output,
            human_input=False,
            agent=agent,
            input_variables=input_variables or [],
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
                    input_variables=["user_id"],
                ),
                self._create_task(
                    self.food_categorization_agent,
                    "Review and correct food categories for all pantry items",
                    "List of items with corrected categories (e.g., chicken broth → Soups & Broths)",
                ),
                self._create_task(
                    self.unit_correction_agent,
                    "Validate and correct units based on food categories",
                    "List of items with appropriate units (e.g., strawberries in lb not ml)",
                ),
                self._create_task(
                    self.ingredient_filter_agent,
                    "Filter out expired items and ensure adequate quantities",
                    "List of usable ingredients with corrected categories and units",
                    input_variables=["user_id"],
                ),
                self._create_task(
                    self.recipe_search_agent,
                    f"Find {max_recipes + 2} dinner recipes using available ingredients",
                    f"List of at least {max_recipes + 2} suitable recipes",
                ),
                self._create_task(
                    self.nutritional_agent,
                    "Evaluate nutritional value of each recipe",
                    "Nutritional analysis for each recipe",
                ),
                self._create_task(
                    self.user_preferences_agent,
                    "Filter recipes based on dietary restrictions for user_id {user_id}",
                    "List of recipes safe for user consumption",
                    input_variables=["user_id"],
                ),
                self._create_task(
                    self.recipe_scoring_agent,
                    "Score and rank recipes based on all criteria",
                    f"Top {max_recipes} ranked recipes",
                ),
                self._create_task(
                    self.sustainability_agent,
                    "Evaluate environmental impact and waste reduction for top recipes",
                    "Sustainability scores and recommendations for each recipe",
                ),
                self._create_task(
                    self.response_formatting_agent,
                    f"Format top {max_recipes} recipes with details including sustainability",
                    "Formatted recipe suggestions in JSON with eco-scores",
                ),
            ]

            # Create and run the crew
            pantry_dinner_crew = Crew(
                agents=[
                    self.pantry_scan_agent,
                    self.food_categorization_agent,
                    self.unit_correction_agent,
                    self.ingredient_filter_agent,
                    self.recipe_search_agent,
                    self.nutritional_agent,
                    self.user_preferences_agent,
                    self.recipe_scoring_agent,
                    self.sustainability_agent,
                    self.response_formatting_agent,
                ],
                tasks=tasks,
                verbose=True,
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
                    metadata={"generated_at": datetime.now().isoformat(), "crew_version": "1.0"},
                )

            return {
                "success": True,
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "recipes": parsed_recipes,
                "cached": False,
                "raw_result": str(result),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "user_id": user_id}

    def _parse_crew_result(self, result: Any) -> List[Dict]:
        """Parse the crew result into structured recipe data"""
        # This is a placeholder - actual parsing depends on crew output format
        # In production, this would parse the formatted output from the crew
        try:
            # Attempt to extract structured data from result
            if isinstance(result, str):
                # Try to find JSON in the result
                import re

                json_match = re.search(r"\[.*\]", result, re.DOTALL)
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
                "items_by_category": self._group_by_category(fresh_items),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "user_id": user_id}

    def _group_by_category(self, items: List[Dict]) -> Dict[str, List[str]]:
        """Group items by category"""
        grouped = {}
        for item in items:
            category = item.get("category", "Other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(item.get("product_name", "Unknown"))
        return grouped
