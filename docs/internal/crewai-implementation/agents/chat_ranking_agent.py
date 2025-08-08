"""Chat Ranking Agent for CrewAI

Agent that analyzes user chat messages and ranks recipes based on contextual intent.
"""

from crewai import Agent


def create_chat_ranking_agent() -> Agent:
    """Create the Chat Ranking Agent for contextual recipe ranking"""
    
    return Agent(
        role="Contextual Recipe Ranking Specialist",
        goal="Analyze user chat messages and rank recipes based on their actual intent and needs",
        backstory="""Expert at understanding what users really want when they ask for recipes. 
        You analyze chat messages to determine if they want quick meals, healthy options, 
        specific cuisines, ways to use expiring ingredients, comfort food, or other specific needs.
        You then rank recipes to match their actual request, not just ingredient availability.""",
        tools=[],  # Uses LLM reasoning capabilities
        verbose=True,
        allow_delegation=False,
        max_iter=2
    )


# For backward compatibility  
ChatRankingAgent = create_chat_ranking_agent