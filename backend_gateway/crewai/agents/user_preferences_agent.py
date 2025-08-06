"""User Preferences Agent for CrewAI

Agent that scores recipes based on user preferences using existing preference systems.
"""

from crewai import Agent
from backend_gateway.crewai.tools.preference_scorer_tool import PreferenceScorerTool


def create_user_preferences_agent() -> Agent:
    """Create the User Preferences Agent"""
    
    return Agent(
        role="Preference Specialist",
        goal="Score recipes using existing preference system",
        backstory="Personal taste expert adapting to individual preferences and dietary requirements",
        tools=[
            PreferenceScorerTool()
        ],
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
UserPreferencesAgent = create_user_preferences_agent