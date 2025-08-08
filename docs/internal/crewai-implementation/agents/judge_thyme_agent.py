"""Judge Thyme Agent for CrewAI

Agent that evaluates recipe practicality and cooking feasibility.
"""

from crewai import Agent


def create_judge_thyme_agent() -> Agent:
    """Create the Judge Thyme Agent"""
    
    return Agent(
        role="Cooking Feasibility Judge",
        goal="Evaluate recipe practicality based on user constraints",
        backstory="Practical cooking expert ensuring recipes are makeable given time, skill level, and equipment constraints",
        tools=[],  # Uses recipe complexity analysis
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
JudgeThymeAgent = create_judge_thyme_agent