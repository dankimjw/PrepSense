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
        backstory="Precision expert ensuring measurement consistency across all pantry items and recipes",
        tools=[
            UnitConverterTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
UnitCanonAgent = create_unit_canon_agent