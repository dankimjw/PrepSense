"""Recipe Search Agent for CrewAI

Enhanced recipe search agent that finds recipes with beautiful images and maximizes pantry utilization.
"""

from crewai import Agent
from backend_gateway.crewai.tools.ingredient_matcher_tool import IngredientMatcherTool
from backend_gateway.crewai.tools.recipe_image_fetcher_tool import RecipeImageFetcherTool


def create_recipe_search_agent() -> Agent:
    """Create the Recipe Search Agent with image fetching capabilities"""
    
    return Agent(
        role="Recipe Discovery Expert",
        goal="Find recipes with beautiful images that maximize pantry utilization",
        backstory="Creative chef who finds perfect recipes with stunning visuals to help users make the most of their pantry ingredients",
        tools=[
            IngredientMatcherTool(),
            RecipeImageFetcherTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
RecipeSearchAgent = create_recipe_search_agent