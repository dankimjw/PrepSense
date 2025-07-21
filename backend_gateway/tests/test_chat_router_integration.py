"""
Integration tests for the chat router to ensure basic functionality works.
This test catches import errors and basic endpoint failures.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Import the app
from backend_gateway.main import app


class TestChatRouterIntegration:
    """Integration tests for chat router endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_crew_service(self):
        """Mock the CrewAI service to avoid external dependencies"""
        with patch('backend_gateway.routers.chat_router.get_crew_ai_service') as mock_get:
            mock_service = MagicMock()
            
            # Mock the process_message method
            async def mock_process_message(user_id, message, use_preferences=True):
                return {
                    "response": f"Test response for: {message}",
                    "recipes": [
                        {
                            "name": "Test Recipe",
                            "ingredients": ["ingredient 1", "ingredient 2"],
                            "instructions": ["Step 1", "Step 2"],
                            "nutrition": {"calories": 300, "protein": 20},
                            "time": 30,
                            "meal_type": "dinner",
                            "cuisine_type": "italian",
                            "dietary_tags": [],
                            "available_ingredients": ["ingredient 1"],
                            "missing_ingredients": ["ingredient 2"],
                            "missing_count": 1,
                            "available_count": 1,
                            "match_score": 0.5,
                            "allergens_present": [],
                            "matched_preferences": []
                        }
                    ],
                    "pantry_items": [
                        {"product_name": "ingredient 1", "quantity": 1}
                    ],
                    "user_preferences": {
                        "dietary_preference": [],
                        "allergens": [],
                        "cuisine_preference": []
                    }
                }
            
            mock_service.process_message = mock_process_message
            mock_get.return_value = mock_service
            yield mock_service
    
    def test_chat_message_endpoint_exists(self, client):
        """Test that the chat message endpoint exists and doesn't throw import errors"""
        # This test will fail if there are import errors
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What can I make for dinner?",
                "user_id": 111,
                "use_preferences": True
            }
        )
        # We expect either 200 (if mocked) or 500 (if service fails)
        # but NOT 404 (endpoint not found due to import error)
        assert response.status_code != 404
    
    def test_chat_message_with_mock_service(self, client, mock_crew_service):
        """Test chat message endpoint with mocked CrewAI service"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What can I make for dinner?",
                "user_id": 111,
                "use_preferences": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "recipes" in data
        assert "pantry_items" in data
        assert "user_preferences" in data
        
        # Verify we got recipes
        assert len(data["recipes"]) > 0
        assert data["recipes"][0]["name"] == "Test Recipe"
    
    def test_chat_message_without_preferences(self, client, mock_crew_service):
        """Test chat message endpoint without using preferences"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Show me quick recipes",
                "user_id": 111,
                "use_preferences": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_generate_recipe_image_endpoint(self, client):
        """Test that the recipe image generation endpoint exists"""
        response = client.post(
            "/api/v1/chat/generate-recipe-image",
            json={
                "recipe_name": "Spaghetti Carbonara",
                "style": "professional food photography",
                "use_generated": False
            }
        )
        
        # Should return 200 with fallback image
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
        assert "recipe_name" in data
    
    def test_import_error_prevention(self):
        """Test that we can import the router without errors"""
        try:
            from backend_gateway.routers import chat_router
            # Check that router has expected attributes
            assert hasattr(chat_router, 'router')
            assert hasattr(chat_router, 'get_crew_ai_service')
            
            # Verify the service can be imported
            from backend_gateway.services.recipe_advisor_service import CrewAIService
            assert CrewAIService is not None
            
            # Verify the service has the expected method
            service = CrewAIService()
            assert hasattr(service, 'process_message')
            
        except ImportError as e:
            pytest.fail(f"Import error in chat router: {e}")
    
    def test_crew_ai_service_initialization(self):
        """Test that CrewAI service can be initialized without errors"""
        from backend_gateway.services.recipe_advisor_service import CrewAIService
        
        # This will catch any initialization errors
        service = CrewAIService()
        assert service is not None
        assert hasattr(service, 'recipe_advisor')
        assert hasattr(service, 'db_service')
        assert hasattr(service, 'recipe_service')


if __name__ == "__main__":
    # Run just the import test for quick verification
    test = TestChatRouterIntegration()
    test.test_import_error_prevention()
    print("✅ Import test passed - no import errors!")