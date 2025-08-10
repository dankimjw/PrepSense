"""Nutri Check Agent for CrewAI

Agent that calculates nutritional information using existing nutrition services.
"""

from crewai import Agent
from backend_gateway.crewai.tools.nutrition_calculator_tool import NutritionCalculatorTool


def create_nutri_check_agent() -> Agent:
    """Create the Nutri Check Agent"""
    
    return Agent(
        role="Nutrition Analyst", 
        goal="Calculate nutrition using existing nutrition service",
        backstory="Registered dietitian ensuring nutritional goals and providing accurate nutritional analysis",
        tools=[
            NutritionCalculatorTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
NutriCheckAgent = create_nutri_check_agent