"""
End-to-end tests for the chat system.
Tests the complete flow with real database and minimal mocking.
Only external APIs (OpenAI, Spoonacular) are mocked.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime, timedelta
import time

from backend_gateway.main import app
from backend_gateway.config.database import get_database_service


class TestChatE2E:
    """End-to-end tests for chat functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_user_id(self):
        """Use a consistent test user ID"""
        return 99999  # High number to avoid conflicts
    
    @pytest.fixture
    def setup_test_data(self, test_user_id):
        """Setup test data in database"""
        db_service = get_database_service()
        
        # Clean up any existing test data
        cleanup_queries = [
            "DELETE FROM user_pantry WHERE user_id = %(user_id)s",
            "DELETE FROM user_preferences WHERE user_id = %(user_id)s",
            "DELETE FROM user_recipes WHERE user_id = %(user_id)s"
        ]
        
        for query in cleanup_queries:
            try:
                db_service.execute_query(query, {"user_id": test_user_id})
            except:
                pass  # Ignore errors if tables don't exist
        
        # Insert test pantry items
        today = datetime.now().date()
        pantry_items = [
            {
                "user_id": test_user_id,
                "product_name": "Chicken Breast",
                "category": "meat",
                "quantity": 2.0,
                "unit": "lb",
                "expiration_date": (today + timedelta(days=3)).strftime("%Y-%m-%d")
            },
            {
                "user_id": test_user_id,
                "product_name": "Rice",
                "category": "grain",
                "quantity": 1.0,
                "unit": "bag",
                "expiration_date": (today + timedelta(days=180)).strftime("%Y-%m-%d")
            },
            {
                "user_id": test_user_id,
                "product_name": "Milk",
                "category": "dairy",
                "quantity": 0.5,
                "unit": "gallon",
                "expiration_date": (today + timedelta(days=2)).strftime("%Y-%m-%d")
            },
            {
                "user_id": test_user_id,
                "product_name": "Broccoli",
                "category": "vegetable",
                "quantity": 1.0,
                "unit": "bunch",
                "expiration_date": (today + timedelta(days=5)).strftime("%Y-%m-%d")
            }
        ]
        
        # Insert pantry items
        for item in pantry_items:
            insert_query = """
                INSERT INTO user_pantry (user_id, product_name, category, quantity, unit, expiration_date)
                VALUES (%(user_id)s, %(product_name)s, %(category)s, %(quantity)s, %(unit)s, %(expiration_date)s)
            """
            db_service.execute_query(insert_query, item)
        
        # Insert test user preferences
        prefs_query = """
            INSERT INTO user_preferences (user_id, preferences)
            VALUES (%(user_id)s, %(preferences)s)
            ON CONFLICT (user_id) DO UPDATE SET preferences = %(preferences)s
        """
        preferences = {
            "dietary_restrictions": ["pescatarian"],
            "allergens": ["peanuts", "shellfish"],
            "cuisine_preferences": ["italian", "asian", "mexican"]
        }
        db_service.execute_query(prefs_query, {
            "user_id": test_user_id,
            "preferences": json.dumps(preferences)
        })
        
        yield
        
        # Cleanup after test
        for query in cleanup_queries:
            try:
                db_service.execute_query(query, {"user_id": test_user_id})
            except:
                pass
    
    @pytest.fixture
    def mock_external_apis(self):
        """Mock only external APIs (Spoonacular, OpenAI)"""
        with patch('backend_gateway.services.spoonacular_service.requests.get') as mock_spoon_get, \
             patch('openai.OpenAI') as mock_openai:
            
            # Mock Spoonacular search response
            def spoonacular_response(url, *args, **kwargs):
                response = MagicMock()
                response.status_code = 200
                
                if "findByIngredients" in url:
                    response.json.return_value = [
                        {
                            "id": 123,
                            "title": "Chicken and Broccoli Stir Fry",
                            "image": "https://spoonacular.com/image1.jpg",
                            "usedIngredients": [
                                {"name": "chicken breast", "amount": 1, "unit": "lb"},
                                {"name": "broccoli", "amount": 2, "unit": "cups"}
                            ],
                            "missedIngredients": [
                                {"name": "soy sauce", "amount": 2, "unit": "tbsp"}
                            ]
                        },
                        {
                            "id": 456,
                            "title": "Chicken Rice Bowl",
                            "image": "https://spoonacular.com/image2.jpg",
                            "usedIngredients": [
                                {"name": "chicken", "amount": 1, "unit": "lb"},
                                {"name": "rice", "amount": 1, "unit": "cup"}
                            ],
                            "missedIngredients": []
                        }
                    ]
                elif f"/recipes/123/information" in url:
                    response.json.return_value = {
                        "id": 123,
                        "title": "Chicken and Broccoli Stir Fry",
                        "readyInMinutes": 25,
                        "servings": 4,
                        "cuisines": ["asian"],
                        "diets": [],
                        "extendedIngredients": [
                            {"name": "chicken breast", "amount": 1, "unit": "lb"},
                            {"name": "broccoli", "amount": 2, "unit": "cups"},
                            {"name": "soy sauce", "amount": 2, "unit": "tbsp"}
                        ],
                        "analyzedInstructions": [{
                            "steps": [
                                {"number": 1, "step": "Cut chicken into bite-sized pieces"},
                                {"number": 2, "step": "Steam broccoli until tender"},
                                {"number": 3, "step": "Heat oil in wok"},
                                {"number": 4, "step": "Stir fry chicken until cooked"},
                                {"number": 5, "step": "Add broccoli and soy sauce"},
                                {"number": 6, "step": "Serve over rice"}
                            ]
                        }],
                        "nutrition": {
                            "nutrients": [
                                {"name": "Calories", "amount": 320},
                                {"name": "Protein", "amount": 35}
                            ]
                        }
                    }
                elif f"/recipes/456/information" in url:
                    response.json.return_value = {
                        "id": 456,
                        "title": "Chicken Rice Bowl",
                        "readyInMinutes": 30,
                        "servings": 2,
                        "cuisines": ["american"],
                        "diets": [],
                        "extendedIngredients": [
                            {"name": "chicken", "amount": 1, "unit": "lb"},
                            {"name": "rice", "amount": 1, "unit": "cup"}
                        ],
                        "analyzedInstructions": [{
                            "steps": [
                                {"number": 1, "step": "Cook rice according to package"},
                                {"number": 2, "step": "Season and grill chicken"},
                                {"number": 3, "step": "Slice chicken and serve over rice"}
                            ]
                        }],
                        "nutrition": {
                            "nutrients": [
                                {"name": "Calories", "amount": 400},
                                {"name": "Protein", "amount": 40}
                            ]
                        }
                    }
                
                return response
            
            mock_spoon_get.side_effect = spoonacular_response
            
            # Mock OpenAI (for any potential AI calls)
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            yield {
                'spoonacular': mock_spoon_get,
                'openai': mock_openai
            }
    
    @pytest.mark.asyncio
    async def test_complete_chat_flow_with_preferences(self, client, test_user_id, setup_test_data, mock_external_apis):
        """Test complete chat flow with user preferences"""
        start_time = time.time()
        
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What can I make for dinner tonight?",
                "user_id": test_user_id,
                "use_preferences": True
            }
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data
        assert "recipes" in data
        assert "pantry_items" in data
        assert "user_preferences" in data
        
        # Verify we got recipes
        assert len(data["recipes"]) > 0
        
        # Verify first recipe
        recipe = data["recipes"][0]
        assert "name" in recipe
        assert recipe["meal_type"] == "dinner"
        assert "available_ingredients" in recipe
        assert "missing_ingredients" in recipe
        
        # Verify pantry items returned
        assert len(data["pantry_items"]) == 4
        pantry_names = [item["product_name"] for item in data["pantry_items"]]
        assert "Chicken Breast" in pantry_names
        assert "Rice" in pantry_names
        
        # Verify preferences were used
        prefs = data["user_preferences"]
        assert "pescatarian" in prefs["dietary_preference"]
        assert "peanuts" in prefs["allergens"]
        assert "italian" in prefs["cuisine_preference"]
        
        # Performance check (should be reasonably fast even with real DB)
        assert response_time < 5.0  # Should complete within 5 seconds
        
        print(f"Response time: {response_time:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_complete_chat_flow_expiring_items(self, client, test_user_id, setup_test_data, mock_external_apis):
        """Test chat flow for expiring items query"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What items are expiring soon? I need to use them up",
                "user_id": test_user_id,
                "use_preferences": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify expiring items are mentioned
        assert "expiring" in data["response"].lower()
        
        # Should mention Milk (2 days) and Chicken (3 days)
        assert "Milk" in data["response"] or "milk" in data["response"].lower()
        
        # Verify recipes prioritize expiring ingredients
        if data["recipes"]:
            # Check if any recipe uses milk or chicken
            recipe_ingredients = []
            for recipe in data["recipes"]:
                recipe_ingredients.extend(recipe.get("available_ingredients", []))
            
            ingredients_text = " ".join(recipe_ingredients).lower()
            assert "chicken" in ingredients_text or "milk" in ingredients_text
    
    @pytest.mark.asyncio
    async def test_complete_chat_flow_no_preferences(self, client, test_user_id, setup_test_data, mock_external_apis):
        """Test chat flow without using preferences"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Show me all breakfast recipes",
                "user_id": test_user_id,
                "use_preferences": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify preferences are empty
        prefs = data["user_preferences"]
        assert prefs["dietary_preference"] == []
        assert prefs["allergens"] == []
        assert prefs["cuisine_preference"] == []
        
        # Response should not show preference choice
        assert data.get("show_preference_choice", False) == False
    
    @pytest.mark.asyncio
    async def test_recipe_ranking_and_scoring(self, client, test_user_id, setup_test_data, mock_external_apis):
        """Test that recipes are properly ranked and scored"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What can I cook with what I have?",
                "user_id": test_user_id,
                "use_preferences": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        recipes = data["recipes"]
        assert len(recipes) >= 2
        
        # Verify each recipe has scoring information
        for recipe in recipes:
            assert "match_score" in recipe
            assert "missing_count" in recipe
            assert "available_count" in recipe
            assert 0 <= recipe["match_score"] <= 1
            
            # If preference scorer is working
            if "preference_score" in recipe:
                assert 0 <= recipe["preference_score"] <= 100
        
        # Verify recipes are sorted (best match first)
        if len(recipes) > 1:
            # Recipe with fewer missing ingredients should come first
            assert recipes[0]["missing_count"] <= recipes[1]["missing_count"]
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_user(self, client, mock_external_apis):
        """Test error handling for user with no pantry items"""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What can I make?",
                "user_id": 0,  # Invalid user ID
                "use_preferences": True
            }
        )
        
        # Should still return 200 but with no recipes
        assert response.status_code == 200
        data = response.json()
        
        # Should have empty pantry
        assert len(data["pantry_items"]) == 0
        
        # May or may not have recipes (depends on implementation)
        # But should not crash
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, client, test_user_id, setup_test_data, mock_external_apis):
        """Test performance of the chat system"""
        # Warm up
        client.post(
            "/api/v1/chat/message",
            json={"message": "test", "user_id": test_user_id}
        )
        
        # Measure multiple requests
        response_times = []
        
        for i in range(3):
            start_time = time.time()
            
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": f"What can I make for dinner? Request {i}",
                    "user_id": test_user_id,
                    "use_preferences": True
                }
            )
            
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # Calculate metrics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        print(f"\nPerformance Metrics:")
        print(f"Average response time: {avg_time:.2f} seconds")
        print(f"Max response time: {max_time:.2f} seconds")
        print(f"All times: {[f'{t:.2f}s' for t in response_times]}")
        
        # Performance assertions
        assert avg_time < 3.0  # Average should be under 3 seconds
        assert max_time < 5.0  # No request should take more than 5 seconds
    
    def test_database_connection(self):
        """Test that database connection works"""
        db_service = get_database_service()
        
        # Simple query to test connection
        result = db_service.execute_query("SELECT 1 as test")
        assert result[0]["test"] == 1
        
        # Test pantry table exists
        result = db_service.execute_query(
            "SELECT COUNT(*) as count FROM user_pantry WHERE user_id = %(user_id)s",
            {"user_id": -1}  # Non-existent user
        )
        assert result[0]["count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print statements