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
        You analyze conversation context, implied preferences, and subtle cues to rank recipes 
        in order of relevance. Your deep understanding of natural language helps identify whether 
        someone wants comfort food, healthy options, quick meals, or impressive dishes based on 
        how they phrase their requests.""",
        tools=[],  # This agent uses analysis skills rather than external tools
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
