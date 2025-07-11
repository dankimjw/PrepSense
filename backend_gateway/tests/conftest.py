"""
Shared pytest fixtures and configuration for all tests
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List
import json
from datetime import datetime


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============= MOCK SERVICES =============

@pytest.fixture
def mock_spoonacular_service():
    """Mock SpoonacularService with common responses"""
    mock = Mock()
    
    # Common method mocks
    mock.search_recipes_complex = AsyncMock(return_value={
        'results': [
            {
                'id': 1,
                'title': 'Test Recipe 1',
                'readyInMinutes': 30,
                'servings': 4
            }
        ]
    })
    
    mock.search_ingredients = AsyncMock(return_value=[
        {'id': 1, 'name': 'chicken'},
        {'id': 2, 'name': 'chicken breast'}
    ])
    
    mock.get_ingredient_information = AsyncMock(return_value={
        'id': 1,
        'name': 'chicken',
        'nutrition': {'calories': 165, 'protein': 31},
        'estimatedCost': {'value': 299},
        'glutenFree': True,
        'vegan': False,
        'vegetarian': False
    })
    
    mock.parse_ingredients = AsyncMock(return_value=[{
        'id': 1,
        'name': 'parsed ingredient',
        'amount': 100,
        'unit': 'g',
        'nutrition': {
            'nutrients': [
                {'name': 'Calories', 'amount': 100},
                {'name': 'Protein', 'amount': 20}
            ]
        }
    }])
    
    mock.get_wine_pairing = AsyncMock(return_value={
        'pairedWines': ['pinot noir', 'chardonnay'],
        'pairingText': 'These wines complement the dish well.'
    })
    
    mock.convert_amounts = AsyncMock(return_value={
        'targetAmount': 453.6,
        'targetUnit': 'grams'
    })
    
    return mock


@pytest.fixture
def mock_recipe_evaluator():
    """Mock RecipeEvaluator service"""
    mock = Mock()
    mock.evaluate_recipe = AsyncMock(return_value={
        'score': 4,
        'critique': 'Well-balanced and flavorful recipe',
        'suggestion': 'Consider adding more vegetables'
    })
    return mock


@pytest.fixture
def mock_crew_ai_service():
    """Mock CrewAIService"""
    mock = Mock()
    mock.process_message = AsyncMock(return_value={
        'response': 'Here are some recipe suggestions',
        'recipes': [
            {
                'id': 'ai_1',
                'title': 'AI Generated Recipe',
                'readyInMinutes': 25,
                'match_score': 0.85,
                'expected_joy': 80
            }
        ]
    })
    return mock


@pytest.fixture
def mock_database_service():
    """Mock database service"""
    mock = Mock()
    mock.execute_query = Mock(return_value=[{
        'preferences': {
            'dietary_restrictions': ['vegetarian'],
            'allergens': ['nuts'],
            'cuisine_preferences': ['italian', 'mexican'],
            'measurement_system': 'imperial'
        }
    }])
    return mock


# ============= SAMPLE DATA =============

@pytest.fixture
def sample_recipe():
    """Sample recipe data for testing"""
    return {
        "id": "test_123",
        "title": "Grilled Chicken Salad",
        "readyInMinutes": 25,
        "servings": 4,
        "cuisine_type": "american",
        "extendedIngredients": [
            {
                "id": 1,
                "name": "chicken breast",
                "original": "2 lbs boneless chicken breast",
                "amount": 2,
                "unit": "lbs"
            },
            {
                "id": 2,
                "name": "mixed greens",
                "original": "6 cups mixed salad greens",
                "amount": 6,
                "unit": "cups"
            },
            {
                "id": 3,
                "name": "olive oil",
                "original": "3 tablespoons olive oil",
                "amount": 3,
                "unit": "tablespoons"
            }
        ],
        "instructions": [
            {"step": 1, "text": "Season chicken with salt and pepper"},
            {"step": 2, "text": "Grill chicken for 6-7 minutes per side"},
            {"step": 3, "text": "Let rest 5 minutes, then slice"},
            {"step": 4, "text": "Toss greens with oil and top with chicken"}
        ],
        "nutrition": {
            "calories": 320,
            "protein": 35,
            "carbohydrates": 8,
            "fat": 18,
            "fiber": 3,
            "sugar": 4,
            "sodium": 450
        },
        "dietary_tags": ["gluten-free", "low-carb", "high-protein"]
    }


@pytest.fixture
def sample_user_preferences():
    """Sample user preferences for testing"""
    return {
        'dietary_restrictions': ['vegetarian', 'gluten-free'],
        'allergens': ['nuts', 'shellfish'],
        'cuisine_preferences': ['italian', 'mexican', 'thai'],
        'measurement_system': 'metric',
        'budget_conscious': True,
        'cooking_skill': 'intermediate',
        'time_preference': 'quick',  # under 30 minutes
        'health_conscious': True
    }


@pytest.fixture
def sample_ingredients_list():
    """Sample ingredients list for testing"""
    return [
        {"name": "chicken", "amount": 500, "unit": "g"},
        {"name": "rice", "amount": 2, "unit": "cups"},
        {"name": "broccoli", "amount": 1, "unit": "head"},
        {"name": "soy sauce", "amount": 3, "unit": "tablespoons"}
    ]


# ============= MOCK CREWAI COMPONENTS =============

@pytest.fixture
def mock_agent():
    """Mock CrewAI Agent"""
    agent = Mock()
    agent.role = "Test Agent"
    agent.goal = "Test goal"
    agent.tools = []
    return agent


@pytest.fixture
def mock_task():
    """Mock CrewAI Task"""
    task = Mock()
    task.description = "Test task"
    task.expected_output = "Test output"
    return task


@pytest.fixture
def mock_crew():
    """Mock CrewAI Crew"""
    crew = Mock()
    crew.kickoff = Mock(return_value="Crew execution complete")
    return crew


# ============= ASYNC HELPERS =============

@pytest.fixture
def async_mock():
    """Helper to create async mocks"""
    def _create_async_mock(return_value=None, side_effect=None):
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock
    return _create_async_mock


# ============= API CLIENT FIXTURES =============

@pytest.fixture
def test_client():
    """Create test client for FastAPI app"""
    from fastapi.testclient import TestClient
    from backend_gateway.app import app
    return TestClient(app)


# ============= ENVIRONMENT FIXTURES =============

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    env_vars = {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'SPOONACULAR_API_KEY': 'test-spoonacular-key',
        'DATABASE_URL': 'postgresql://test:test@localhost/test',
        'ENVIRONMENT': 'test'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


# ============= UTILITY FUNCTIONS =============

@pytest.fixture
def json_loads():
    """Safe JSON loads for testing"""
    def _loads(data):
        if isinstance(data, str):
            return json.loads(data)
        return data
    return _loads


@pytest.fixture
def assert_recipe_valid():
    """Helper to validate recipe structure"""
    def _validate(recipe):
        assert 'id' in recipe
        assert 'title' in recipe
        assert 'readyInMinutes' in recipe
        assert 'extendedIngredients' in recipe
        assert isinstance(recipe['extendedIngredients'], list)
        assert 'instructions' in recipe
        assert 'nutrition' in recipe
    return _validate


@pytest.fixture
def create_mock_recipe():
    """Factory for creating mock recipes"""
    def _create(title="Test Recipe", recipe_id=None, **kwargs):
        base_recipe = {
            "id": recipe_id or f"test_{datetime.now().timestamp()}",
            "title": title,
            "readyInMinutes": 30,
            "servings": 4,
            "extendedIngredients": [
                {"name": "ingredient1", "amount": 1, "unit": "cup"}
            ],
            "instructions": [{"step": 1, "text": "Test step"}],
            "nutrition": {"calories": 300, "protein": 20}
        }
        base_recipe.update(kwargs)
        return base_recipe
    return _create


# ============= CLEANUP =============

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Any cleanup code here


# ============= MARKERS =============

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require external API access"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )