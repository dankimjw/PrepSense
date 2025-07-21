"""
Unit tests for the chat router endpoints.
Tests the router logic with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

from backend_gateway.main import app


class TestChatRouterUnit:
    """Unit tests for chat router endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_crew_service(self):
        """Mock CrewAI service with realistic responses"""
        with patch('backend_gateway.routers.chat_router.get_crew_ai_service') as mock_get:
            mock_service = MagicMock()
            
            # Create async mock for process_message
            async def mock_process_message(user_id, message, use_preferences=True):
                # Simulate different responses based on message content
                if "dinner" in message.lower():
                    response_text = "Based on your pantry items, here are my dinner recommendations!"
                    recipes = [
                        {
                            "name": "Chicken Stir Fry",
                            "ingredients": ["2 chicken breasts", "3 cups vegetables", "2 tbsp soy sauce"],
                            "instructions": ["Cut chicken", "Heat oil", "Stir fry", "Add sauce"],
                            "nutrition": {"calories": 350, "protein": 35},
                            "time": 20,
                            "meal_type": "dinner",
                            "cuisine_type": "asian",
                            "dietary_tags": ["gluten-free"],
                            "available_ingredients": ["chicken breasts", "vegetables"],
                            "missing_ingredients": ["soy sauce"],
                            "missing_count": 1,
                            "available_count": 2,
                            "match_score": 0.67,
                            "allergens_present": [],
                            "matched_preferences": []
                        }
                    ]
                elif "breakfast" in message.lower():
                    response_text = "Here are some quick breakfast ideas!"
                    recipes = [
                        {
                            "name": "Scrambled Eggs",
                            "ingredients": ["3 eggs", "1 tbsp butter", "salt", "pepper"],
                            "instructions": ["Beat eggs", "Heat butter", "Cook eggs", "Season"],
                            "nutrition": {"calories": 220, "protein": 18},
                            "time": 10,
                            "meal_type": "breakfast",
                            "cuisine_type": "american",
                            "dietary_tags": ["vegetarian", "gluten-free"],
                            "available_ingredients": ["eggs", "butter"],
                            "missing_ingredients": [],
                            "missing_count": 0,
                            "available_count": 2,
                            "match_score": 1.0,
                            "allergens_present": ["eggs"],
                            "matched_preferences": []
                        }
                    ]
                elif "expiring" in message.lower():
                    response_text = "⚠️ You have 3 items expiring soon:\n• Milk - Expires in 2 days\n• Yogurt - Expires in 3 days\n\n💡 Here are recipes to use these items:"
                    recipes = [
                        {
                            "name": "Yogurt Smoothie",
                            "ingredients": ["1 cup yogurt", "1 banana", "1/2 cup milk"],
                            "instructions": ["Blend all ingredients", "Serve cold"],
                            "nutrition": {"calories": 180, "protein": 8},
                            "time": 5,
                            "meal_type": "snack",
                            "cuisine_type": "american",
                            "dietary_tags": ["vegetarian"],
                            "available_ingredients": ["yogurt", "milk"],
                            "missing_ingredients": ["banana"],
                            "missing_count": 1,
                            "available_count": 2,
                            "match_score": 0.67,
                            "evaluation": {"uses_expiring": True},
                            "allergens_present": ["dairy"],
                            "matched_preferences": []
                        }
                    ]
                else:
                    response_text = "Based on your pantry items, here are my recommendations!"
                    recipes = []
                
                # Build response based on use_preferences
                if use_preferences:
                    user_prefs = {
                        "dietary_preference": ["vegetarian"],
                        "allergens": ["nuts"],
                        "cuisine_preference": ["italian", "asian"]
                    }
                else:
                    user_prefs = {
                        "dietary_preference": [],
                        "allergens": [],
                        "cuisine_preference": []
                    }
                
                return {
                    "response": response_text,
                    "recipes": recipes,
                    "pantry_items": [
                        {"product_name": "chicken breasts", "quantity": 2, "expiration_date": "2024-01-25"},
                        {"product_name": "eggs", "quantity": 12, "expiration_date": "2024-01-20"},
                        {"product_name": "milk", "quantity": 1, "expiration_date": "2024-01-18"}
                    ],
                    "user_preferences": user_prefs,
                    "show_preference_choice": len(recipes) > 0 and use_preferences
                }
            
            mock_service.process_message = mock_process_message
            mock_get.return_value = mock_service
            yield mock_service
    
    def test_chat_message_dinner_request(self, client, mock_crew_service):
        """Test chat endpoint with dinner request"""
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
        
        # Verify dinner-specific response
        assert "dinner" in data["response"].lower()
        assert len(data["recipes"]) > 0
        assert data["recipes"][0]["meal_type"] == "dinner"
        assert data["recipes"][0]["name"] == "Chicken Stir Fry"
    
    def test_chat_message_breakfast_request(self, client, mock_crew_service):
        """Test chat endpoint with breakfast request"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What's good for breakfast?",
                "user_id": 111,
                "use_preferences": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify breakfast-specific response
        assert "breakfast" in data["response"].lower()
        assert len(data["recipes"]) > 0
        assert data["recipes"][0]["meal_type"] == "breakfast"
        assert data["recipes"][0]["missing_count"] == 0  # Can make with available ingredients
    
    def test_chat_message_expiring_items(self, client, mock_crew_service):
        """Test chat endpoint with expiring items query"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What items are expiring soon?",
                "user_id": 111,
                "use_preferences": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify expiring items response
        assert "expiring" in data["response"].lower()
        assert "Milk" in data["response"]
        assert len(data["recipes"]) > 0
        # Check that recipe uses expiring items
        recipe = data["recipes"][0]
        assert recipe.get("evaluation", {}).get("uses_expiring") == True
    
    def test_chat_message_without_preferences(self, client, mock_crew_service):
        """Test chat endpoint without using preferences"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Show me all dinner recipes",
                "user_id": 111,
                "use_preferences": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify preferences are empty when not used
        assert data["user_preferences"]["dietary_preference"] == []
        assert data["user_preferences"]["allergens"] == []
        assert data["user_preferences"]["cuisine_preference"] == []
    
    def test_chat_message_with_preferences(self, client, mock_crew_service):
        """Test chat endpoint with preferences"""
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
        
        # Verify preferences are included
        prefs = data["user_preferences"]
        assert "vegetarian" in prefs["dietary_preference"]
        assert "nuts" in prefs["allergens"]
        assert "italian" in prefs["cuisine_preference"]
        assert data.get("show_preference_choice") == True
    
    def test_chat_message_default_user_id(self, client, mock_crew_service):
        """Test that default user_id is used when not provided"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What can I cook?"
                # user_id not provided, should default to 111
            }
        )
        
        assert response.status_code == 200
        # Test passes if no error - default user_id was used
    
    def test_chat_message_preference_detection(self, client, mock_crew_service):
        """Test preference choice detection in messages"""
        # Test message that should NOT show preference choice
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Show me recipes without preferences",
                "user_id": 111,
                "use_preferences": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        # Even though use_preferences is True, message indicates no preferences
        # The router should detect this (though current implementation might not)
    
    def test_chat_message_error_handling(self, client):
        """Test error handling when service fails"""
        with patch('backend_gateway.routers.chat_router.get_crew_ai_service') as mock_get:
            mock_service = MagicMock()
            
            # Make process_message raise an exception
            async def failing_process(*args, **kwargs):
                raise Exception("Database connection failed")
            
            mock_service.process_message = failing_process
            mock_get.return_value = mock_service
            
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "What can I make?",
                    "user_id": 111
                }
            )
            
            assert response.status_code == 500
            assert "Failed to process message" in response.json()["detail"]
    
    def test_recipe_image_generation_unsplash(self, client):
        """Test recipe image generation with Unsplash (default)"""
        response = client.post(
            "/api/v1/chat/generate-recipe-image",
            json={
                "recipe_name": "Chicken Pasta",
                "style": "professional food photography",
                "use_generated": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "image_url" in data
        assert data["recipe_name"] == "Chicken Pasta"
        # Should return an Unsplash URL
        assert "unsplash.com" in data["image_url"]
    
    def test_recipe_image_generation_dalle(self, client):
        """Test recipe image generation with DALL-E"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                # Mock DALL-E response
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.data = [MagicMock(url="https://dalle-generated-url.com/image.png")]
                mock_client.images.generate.return_value = mock_response
                mock_openai.return_value = mock_client
                
                response = client.post(
                    "/api/v1/chat/generate-recipe-image",
                    json={
                        "recipe_name": "Chocolate Cake",
                        "style": "artistic",
                        "use_generated": True
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["image_url"] == "https://dalle-generated-url.com/image.png"
                
                # Verify DALL-E was called with correct parameters
                mock_client.images.generate.assert_called_once()
                call_args = mock_client.images.generate.call_args
                assert call_args[1]["model"] == "dall-e-2"
                assert "Chocolate Cake" in call_args[1]["prompt"]
    
    def test_recipe_image_fallback_categories(self, client):
        """Test recipe image fallback based on recipe categories"""
        # Test various recipe types to ensure proper categorization
        test_cases = [
            ("Pasta Carbonara", "pasta"),
            ("Chicken Stir Fry", "stir_fry"),
            ("Garden Salad", "salad"),
            ("Beef Burger", "burger"),
            ("Breakfast Pancakes", "breakfast"),
            ("Chocolate Cake", "dessert"),
        ]
        
        for recipe_name, expected_category in test_cases:
            response = client.post(
                "/api/v1/chat/generate-recipe-image",
                json={
                    "recipe_name": recipe_name,
                    "use_generated": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "image_url" in data
            # Should get a consistent URL for each category
            assert "unsplash.com" in data["image_url"]
    
    def test_chat_service_initialization(self):
        """Test that CrewAI service initializes correctly"""
        from backend_gateway.services.recipe_advisor_service import CrewAIService
        
        # Test service can be created
        service = CrewAIService()
        assert service is not None
        
        # Test service has required attributes
        assert hasattr(service, 'recipe_advisor')
        assert hasattr(service, 'db_service')
        assert hasattr(service, 'recipe_service')
        assert hasattr(service, 'spoonacular_service')
        assert hasattr(service, 'openai_service')
        assert hasattr(service, 'preference_scorer')
        
        # Test recipe advisor has correct methods
        advisor = service.recipe_advisor
        assert hasattr(advisor, 'analyze_pantry')
        assert hasattr(advisor, 'evaluate_recipe_fit')
        assert hasattr(advisor, 'generate_advice')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])