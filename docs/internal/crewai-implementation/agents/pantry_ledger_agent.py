"""Pantry Ledger Agent for CrewAI

Agent that manages pantry inventory updates using existing pantry services.
"""

from crewai import Agent


def create_pantry_ledger_agent() -> Agent:
    """Create the Pantry Ledger Agent"""
    
    return Agent(
        role="Inventory Manager",
        goal="Update pantry using existing pantry service",
        backstory="Meticulous accountant tracking ingredient usage and maintaining accurate inventory records",
        tools=[],  # Uses existing pantry_service.py
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


# For backward compatibility
PantryLedgerAgent = create_pantry_ledger_agent