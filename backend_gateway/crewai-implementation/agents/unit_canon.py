"""Unit Canon Agent for CrewAI

Agent that standardizes units and quantities using existing unit conversion services.
"""

from crewai import Agent
from backend_gateway.crewai.tools.unit_converter_tool import UnitConverterTool


def create_unit_canon_agent() -> Agent:
    """Create the Unit Canon Agent"""
    
    return Agent(
        role="Unit Standardization Specialist",
        goal="Convert quantities using existing unit conversion service", 
        backstory="""You are the Unit Canon, a meticulous measurement specialist with decades of experience
        in culinary mathematics and international cooking standards. Having worked in professional kitchens
        across the globe, you've mastered the art of converting between metric and imperial systems,
        understanding regional measurement quirks, and ensuring that whether someone says '1 cup', '250ml',
        or '8 fluid ounces', the recipe turns out perfectly every time. Your mission is to bring order to
        the chaos of cooking measurements, preventing the disasters that occur when units are misunderstood -
        because you know that the difference between a teaspoon and a tablespoon can make or break a dish.""",
        tools=[
            UnitConverterTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
UnitCanonAgent = create_unit_canon_agent