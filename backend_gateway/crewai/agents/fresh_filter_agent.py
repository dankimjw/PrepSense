"""Fresh Filter Agent for CrewAI

Agent that analyzes freshness and expiry data to prioritize pantry item usage.
"""

from crewai import Agent


def create_fresh_filter_agent() -> Agent:
    """Create the Fresh Filter Agent"""
    
    return Agent(
        role="Freshness Analyst",
        goal="Score items for freshness using expiry data",
        backstory="Food safety expert preventing waste by analyzing expiration dates and freshness indicators",
        tools=[],  # Uses existing pantry data directly
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility  
FreshFilterAgent = create_fresh_filter_agent