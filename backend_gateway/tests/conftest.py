"""Pytest configuration and shared fixtures"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer

from backend_gateway.app import app  # FastAPI app

# Add backend_gateway to Python path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://test@localhost/test_db"
os.environ["OPENAI_API_KEY"] = "test-key-123"
os.environ["SPOONACULAR_API_KEY"] = "test-spoon-key"
os.environ["UNSPLASH_ACCESS_KEY"] = "test-unsplash-key"


@pytest.fixture(scope="session")
def event_loop():
    """Enable pytest-asyncio on Windows + Detox"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Launch ephemeral Postgres in Docker."""
    with PostgresContainer("postgres:16-alpine") as pg:
        os.environ["DATABASE_URL"] = pg.get_connection_url()
        # Run Alembic migrations if they exist
        try:
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Alembic migrations not found or failed - continuing with empty DB")
        yield pg


@pytest.fixture()
async def client(test_db):
    """HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def sample_pantry_data(tmp_path):
    """Sample pantry data for testing"""
    fp = tmp_path / "pantry.json"
    data = [
        {
            "pantry_item_id": 1,
            "product_name": "Chicken Breast",
            "quantity": 2,
            "unit_of_measurement": "lbs",
            "expiration_date": "2024-12-31",
            "category": "protein",
        },
        {
            "pantry_item_id": 2,
            "product_name": "Rice",
            "quantity": 3,
            "unit_of_measurement": "cups",
            "expiration_date": "2025-06-01",
            "category": "grains",
        },
    ]
    json.dump(data, fp.open("w"))
    return fp


@pytest.fixture()
def sample_recipes():
    """Sample recipe data for testing"""
    return [
        {
            "id": 1,
            "name": "Chicken Rice Bowl",
            "ingredients": ["2 lbs chicken breast", "2 cups rice", "soy sauce"],
            "instructions": ["Cook chicken", "Cook rice", "Combine with soy sauce"],
            "nutrition": {"protein": 35, "carbs": 45, "fat": 12, "fiber": 3},
        },
        {
            "id": 2,
            "name": "Fried Rice",
            "ingredients": ["3 cups cooked rice", "2 eggs", "soy sauce", "vegetable oil"],
            "instructions": ["Heat oil", "Scramble eggs", "Add rice and soy sauce"],
            "nutrition": {"protein": 12, "carbs": 58, "fat": 8, "fiber": 2},
        },
    ]


@pytest.fixture()
def mock_crewai_service():
    """Mock CrewAI service for testing"""
    mock_service = Mock()
    mock_service.get_recipe_recommendations.return_value = {
        "message": "Here are some great recipes for you!",
        "recipes": [
            {
                "id": 1,
                "name": "Chicken Rice Bowl",
                "available_count": 2,
                "missing_count": 1,
                "score": 85,
            }
        ],
    }
    return mock_service


@pytest.fixture()
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content="Here's a great recipe recommendation based on your pantry items."
                )
            )
        ]
    )
    return mock_client


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure async backend for tests"""
    return "asyncio"


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/test_db")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("SPOONACULAR_API_KEY", "test-spoon-key")
    yield


# Import CrewAI fixtures
from backend_gateway.tests.fixtures.crew_ai_fixtures import (
    create_mock_crew_components,
    create_mock_database_service,
    create_mock_spoonacular_service,
    get_mock_crew_ai_response,
    get_mock_pantry_items_for_crew,
    get_mock_recipes_for_crew,
    get_mock_user_preferences_for_crew,
)


@pytest.fixture
def mock_crew_ai_database():
    """Mock database service for CrewAI tests"""
    return create_mock_database_service()


@pytest.fixture
def mock_crew_ai_spoonacular():
    """Mock Spoonacular service for CrewAI tests"""
    return create_mock_spoonacular_service()


@pytest.fixture
def mock_crew_ai_components():
    """All mock CrewAI components"""
    return create_mock_crew_components()


@pytest.fixture
def crew_ai_test_data():
    """Test data for CrewAI"""
    return {
        "pantry_items": get_mock_pantry_items_for_crew(),
        "user_preferences": get_mock_user_preferences_for_crew(),
        "recipes": get_mock_recipes_for_crew(),
        "full_response": get_mock_crew_ai_response(),
    }
