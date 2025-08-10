"""
Shared fixtures and mocks for CrewAI testing
"""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock


def get_mock_pantry_items_for_crew() -> list[dict[str, Any]]:
    """Get mock pantry items for CrewAI testing"""
    today = datetime.now().date()
    return [
        {
            "user_id": 123,
            "product_name": "Chicken Breast",
            "quantity": 2.0,
            "unit": "lbs",
            "expiration_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "category": "proteins",
            "location": "fridge",
        },
        {
            "user_id": 123,
            "product_name": "Basmati Rice",
            "quantity": 1.0,
            "unit": "kg",
            "expiration_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "category": "grains",
            "location": "pantry",
        },
        {
            "user_id": 123,
            "product_name": "Broccoli",
            "quantity": 1.5,
            "unit": "lbs",
            "expiration_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "category": "vegetables",
            "location": "fridge",
        },
        {
            "user_id": 123,
            "product_name": "Milk",
            "quantity": 0.5,
            "unit": "gal",
            "expiration_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "category": "dairy",
            "location": "fridge",
        },
        {
            "user_id": 123,
            "product_name": "Expired Bread",
            "quantity": 1,
            "unit": "loaf",
            "expiration_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "category": "grains",
            "location": "pantry",
        },
    ]


def get_mock_user_preferences_for_crew() -> dict[str, Any]:
    """Get mock user preferences for CrewAI testing"""
    return {
        "dietary_restrictions": ["vegetarian"],
        "allergens": ["nuts", "shellfish"],
        "cuisine_preferences": ["italian", "asian", "mediterranean"],
        "cooking_skill": "intermediate",
        "max_cooking_time": 45,
        "spice_tolerance": "medium",
        "health_goals": ["high-protein", "low-carb"],
    }


def get_mock_recipes_for_crew() -> list[dict[str, Any]]:
    """Get mock recipes for CrewAI testing"""
    return [
        {
            "id": 1,
            "name": "Healthy Chicken Stir Fry",
            "ingredients": ["chicken breast", "broccoli", "rice", "soy sauce", "garlic"],
            "instructions": [
                "Cook rice according to package directions",
                "Cut chicken into bite-sized pieces",
                "Stir fry chicken until cooked through",
                "Add broccoli and cook until tender",
                "Serve over rice",
            ],
            "time": 30,
            "cuisine_type": "asian",
            "nutrition": {
                "calories": 420,
                "protein": 35,
                "carbs": 45,
                "fat": 12,
                "fiber": 5,
                "nutritional_balance": "excellent",
            },
            "dietary_tags": ["high-protein", "balanced"],
            "difficulty": "easy",
        },
        {
            "id": 2,
            "name": "Mediterranean Chicken Bowl",
            "ingredients": ["chicken breast", "rice", "tomatoes", "cucumber", "feta cheese"],
            "instructions": [
                "Grill chicken with Mediterranean spices",
                "Cook rice with herbs",
                "Chop vegetables",
                "Assemble bowl with all ingredients",
                "Drizzle with olive oil and lemon",
            ],
            "time": 35,
            "cuisine_type": "mediterranean",
            "nutrition": {
                "calories": 480,
                "protein": 38,
                "carbs": 42,
                "fat": 18,
                "fiber": 6,
                "nutritional_balance": "good",
            },
            "dietary_tags": ["high-protein", "heart-healthy"],
            "difficulty": "medium",
        },
        {
            "id": 3,
            "name": "Quick Pasta Primavera",
            "ingredients": ["pasta", "broccoli", "carrots", "olive oil", "parmesan"],
            "instructions": [
                "Cook pasta al dente",
                "Steam vegetables until tender",
                "Toss pasta with vegetables and olive oil",
                "Top with parmesan cheese",
            ],
            "time": 20,
            "cuisine_type": "italian",
            "nutrition": {
                "calories": 380,
                "protein": 15,
                "carbs": 58,
                "fat": 14,
                "fiber": 7,
                "nutritional_balance": "good",
            },
            "dietary_tags": ["vegetarian"],
            "difficulty": "easy",
        },
    ]


def get_mock_crew_ai_response() -> dict[str, Any]:
    """Get a complete mock CrewAI response"""
    return {
        "response": """Based on your pantry items and preferences, I've found some great recipes for you!

You have several items expiring soon:
- Milk expires in 2 days
- Chicken Breast expires in 3 days

I recommend the Healthy Chicken Stir Fry which uses your expiring chicken and fresh broccoli.
It's a high-protein, balanced meal that fits your intermediate cooking skill level and can be ready in just 30 minutes.

All recipes have been checked against your nut and shellfish allergies.""",
        "recipes": get_mock_recipes_for_crew(),
        "pantry_items": [
            item
            for item in get_mock_pantry_items_for_crew()
            if item["product_name"] != "Expired Bread"
        ],
        "user_preferences": get_mock_user_preferences_for_crew(),
    }


class MockCrewAIAgent:
    """Mock CrewAI Agent for testing"""

    def __init__(self, role: str, goal: str, tools: list = None):
        self.role = role
        self.goal = goal
        self.tools = tools or []
        self.backstory = f"Mock agent for {role}"
        self.verbose = True


class MockCrewAITask:
    """Mock CrewAI Task for testing"""

    def __init__(self, description: str, agent: MockCrewAIAgent, expected_output: str):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output


class MockCrewAICrew:
    """Mock CrewAI Crew for testing"""

    def __init__(self, agents: list, tasks: list, process: Any = None, verbose: bool = True):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self._kickoff_result = get_mock_crew_ai_response()["response"]

    def kickoff(self):
        """Mock crew execution"""
        return self._kickoff_result


def create_mock_database_service():
    """Create a mock database service for CrewAI testing"""
    mock_db = Mock()

    def mock_query(query: str, params: dict[str, Any]):
        if "user_pantry_full" in query:
            return get_mock_pantry_items_for_crew()
        elif "user_preferences" in query:
            return [
                {
                    "user_id": params["user_id"],
                    "preferences": {
                        "dietary_restrictions": get_mock_user_preferences_for_crew()[
                            "dietary_restrictions"
                        ],
                        "allergens": get_mock_user_preferences_for_crew()["allergens"],
                        "cuisine_preferences": get_mock_user_preferences_for_crew()[
                            "cuisine_preferences"
                        ],
                        "cooking_skill": get_mock_user_preferences_for_crew()["cooking_skill"],
                        "max_cooking_time": get_mock_user_preferences_for_crew()[
                            "max_cooking_time"
                        ],
                    },
                }
            ]
        return []

    mock_db.execute_query = Mock(side_effect=mock_query)
    return mock_db


def create_mock_spoonacular_service():
    """Create a mock Spoonacular service for CrewAI testing"""
    mock_service = AsyncMock()

    # Mock search recipes
    mock_service.search_recipes_by_ingredients.return_value = [
        {
            "id": 101,
            "title": "Spoonacular Chicken Rice",
            "usedIngredients": [
                {"name": "chicken", "amount": 1, "unit": "lb"},
                {"name": "rice", "amount": 1, "unit": "cup"},
            ],
            "missedIngredients": [],
            "nutrition": {"calories": 400},
        }
    ]

    # Mock get recipe details
    mock_service.get_recipe_information.return_value = {
        "id": 101,
        "title": "Spoonacular Chicken Rice",
        "readyInMinutes": 35,
        "instructions": "Cook the chicken and rice...",
        "extendedIngredients": [{"original": "1 lb chicken"}, {"original": "1 cup rice"}],
    }

    return mock_service


def create_mock_crew_components():
    """Create all mock CrewAI components for testing"""
    return {
        "Agent": MockCrewAIAgent,
        "Task": MockCrewAITask,
        "Crew": MockCrewAICrew,
        "Process": Mock(sequential="sequential", hierarchical="hierarchical"),
        "database": create_mock_database_service(),
        "spoonacular": create_mock_spoonacular_service(),
    }
