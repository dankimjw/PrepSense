"""Food Categorizer Agent for CrewAI

Agent that categorizes raw food items using existing USDA database and food services.
"""

from crewai import Agent
from backend_gateway.crewai.tools.ingredient_matcher_tool import IngredientMatcherTool


def create_food_categorizer_agent() -> Agent:
    """Create the Food Categorizer Agent"""
    
    return Agent(
        role="Food Category Expert",
        goal="Categorize raw food items using existing USDA database",
        backstory="Expert at identifying foods and mapping to nutrition databases for accurate pantry management",
        tools=[
            IngredientMatcherTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
FoodCategorizerAgent = create_food_categorizer_agent