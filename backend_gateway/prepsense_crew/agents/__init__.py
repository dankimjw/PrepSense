"""CrewAI Agents for PrepSense

This module contains specialized CrewAI agents that use existing services as tools.
Following the service composition pattern to integrate with PrepSense backend.
"""

from .bite_cam import create_bite_cam_agent
from .chef_parser import create_chef_parser_agent
from .food_categorizer import create_food_categorizer_agent
from .fresh_filter import create_fresh_filter_agent
from .judge_thyme import create_judge_thyme_agent
from .nutri_check import create_nutri_check_agent
from .pantry_ledger import create_pantry_ledger_agent
from .recipe_search import create_recipe_search_agent
from .unit_canon import create_unit_canon_agent
from .user_preferences import create_user_preferences_agent

__all__ = [
    "create_bite_cam_agent",
    "create_chef_parser_agent",
    "create_food_categorizer_agent",
    "create_fresh_filter_agent",
    "create_judge_thyme_agent",
    "create_nutri_check_agent",
    "create_pantry_ledger_agent",
    "create_recipe_search_agent",
    "create_unit_canon_agent",
    "create_user_preferences_agent",
]