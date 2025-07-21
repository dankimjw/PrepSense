"""
Comprehensive tests for the Recipe Advisor (CrewAI) Service.
Tests the service logic including pantry analysis, recipe fetching, and ranking.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import json

from backend_gateway.services.recipe_advisor_service import RecipeAdvisor, CrewAIService


class TestRecipeAdvisor:
    """Test the RecipeAdvisor component"""
    
    def test_analyze_pantry_with_expiring_items(self):
        """Test pantry analysis identifies expiring items correctly"""
        advisor = RecipeAdvisor()
        
        # Create test pantry with various expiration dates
        today = datetime.now().date()
        pantry_items = [
            {
                "product_name": "Milk",
                "category": "dairy",
                "expiration_date": (today + timedelta(days=2)).strftime("%Y-%m-%d")
            },
            {
                "product_name": "Yogurt",
                "category": "dairy",
                "expiration_date": (today + timedelta(days=5)).strftime("%Y-%m-%d")
            },
            {
                "product_name": "Bread",
                "category": "bakery",
                "expiration_date": (today - timedelta(days=1)).strftime("%Y-%m-%d")  # Expired
            },
            {
                "product_name": "Chicken Breast",
                "category": "meat",
                "expiration_date": (today + timedelta(days=3)).strftime("%Y-%m-%d")
            },
            {
                "product_name": "Rice",
                "category": "pantry",
                "expiration_date": (today + timedelta(days=180)).strftime("%Y-%m-%d")
            }
        ]
        
        analysis = advisor.analyze_pantry(pantry_items)
        
        # Verify analysis results
        assert analysis["total_items"] == 5
        assert len(analysis["expiring_soon"]) == 3  # Milk, Yogurt, Chicken (within 7 days)
        assert len(analysis["expired"]) == 1  # Bread
        
        # Check specific expiring items
        expiring_names = [item["name"] for item in analysis["expiring_soon"]]
        assert "Milk" in expiring_names
        assert "Chicken Breast" in expiring_names
        
        # Check categories
        assert "dairy" in analysis["categories"]
        assert len(analysis["categories"]["dairy"]) == 2
        
        # Check protein sources
        assert "chicken breast" in analysis["protein_sources"]
        
        # Check staples
        assert "rice" in analysis["staples"]
    
    def test_analyze_pantry_no_expiration_dates(self):
        """Test pantry analysis with items lacking expiration dates"""
        advisor = RecipeAdvisor()
        
        pantry_items = [
            {"product_name": "Salt", "category": "pantry"},
            {"product_name": "Olive Oil", "category": "pantry"},
            {"product_name": "Pasta", "category": "pantry", "expiration_date": None}
        ]
        
        analysis = advisor.analyze_pantry(pantry_items)
        
        assert analysis["total_items"] == 3
        assert len(analysis["expiring_soon"]) == 0
        assert len(analysis["expired"]) == 0
    
    def test_evaluate_recipe_fit(self):
        """Test recipe evaluation based on pantry and preferences"""
        advisor = RecipeAdvisor()
        
        # Mock pantry analysis
        pantry_analysis = {
            "expiring_soon": [
                {"name": "chicken breast", "days": 3}
            ],
            "protein_sources": ["chicken breast", "eggs"],
            "staples": ["rice", "pasta"]
        }
        
        # Test recipe that uses expiring ingredients
        recipe = {
            "name": "Chicken Stir Fry",
            "ingredients": ["chicken breast", "vegetables", "soy sauce"],
            "instructions": ["Step 1", "Step 2", "Step 3"]
        }
        
        user_prefs = {"dietary_preference": [], "allergens": []}
        
        evaluation = advisor.evaluate_recipe_fit(recipe, user_prefs, pantry_analysis)
        
        assert evaluation["uses_expiring"] == True
        assert evaluation["nutritional_balance"] == "good"  # Has protein + vegetables
        assert evaluation["cooking_complexity"] == "easy"  # Only 3 steps
    
    def test_generate_advice(self):
        """Test contextual advice generation"""
        advisor = RecipeAdvisor()
        
        pantry_analysis = {
            "expiring_soon": [
                {"name": "milk", "days": 2},
                {"name": "yogurt", "days": 3}
            ]
        }
        
        recipes = [
            {"name": "Smoothie", "cuisine_type": "american", "time": 5},
            {"name": "Pasta", "cuisine_type": "italian", "time": 25},
            {"name": "Stir Fry", "cuisine_type": "asian", "time": 15}
        ]
        
        # Test expiring items message
        advice = advisor.generate_advice(recipes, pantry_analysis, "What can I make with expiring items?")
        assert "2 items expiring soon" in advice
        
        # Test variety message
        advice = advisor.generate_advice(recipes, pantry_analysis, "Show me recipes")
        assert "diverse cuisine" in advice
        
        # Test quick recipes message
        advice = advisor.generate_advice(recipes, pantry_analysis, "I need something quick")
        assert "quick recipes" in advice
        assert "20 min or less" in advice


class TestCrewAIService:
    """Test the main CrewAI Service"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all service dependencies"""
        with patch('backend_gateway.services.recipe_advisor_service.get_database_service') as mock_db, \
             patch('backend_gateway.services.recipe_advisor_service.RecipeService') as mock_recipe, \
             patch('backend_gateway.services.recipe_advisor_service.UserRecipesService') as mock_user_recipes, \
             patch('backend_gateway.services.recipe_advisor_service.SpoonacularService') as mock_spoon, \
             patch('backend_gateway.services.recipe_advisor_service.OpenAIRecipeService') as mock_openai, \
             patch('backend_gateway.services.recipe_advisor_service.RecipePreferenceScorer') as mock_scorer, \
             patch('backend_gateway.services.recipe_advisor_service.get_openai_api_key', return_value='test-key'):
            
            # Setup database mock
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            
            # Setup other service mocks
            mock_recipe_instance = MagicMock()
            mock_recipe.return_value = mock_recipe_instance
            
            mock_user_recipes_instance = MagicMock()
            mock_user_recipes.return_value = mock_user_recipes_instance
            
            mock_spoon_instance = MagicMock()
            mock_spoon.return_value = mock_spoon_instance
            
            mock_openai_instance = MagicMock()
            mock_openai.return_value = mock_openai_instance
            
            mock_scorer_instance = MagicMock()
            mock_scorer.return_value = mock_scorer_instance
            
            yield {
                'db': mock_db_instance,
                'recipe': mock_recipe_instance,
                'user_recipes': mock_user_recipes_instance,
                'spoonacular': mock_spoon_instance,
                'openai': mock_openai_instance,
                'scorer': mock_scorer_instance
            }
    
    @pytest.mark.asyncio
    async def test_process_message_dinner_request(self, mock_dependencies):
        """Test processing a dinner request message"""
        service = CrewAIService()
        
        # Mock pantry items
        mock_dependencies['db'].execute_query.return_value = [
            {
                "product_name": "Chicken Breast",
                "category": "meat",
                "quantity": 2,
                "unit_of_measurement": "lb",
                "expiration_date": "2024-01-25",
                "user_id": 111,
                "pantry_item_id": 1
            },
            {
                "product_name": "Rice",
                "category": "grain",
                "quantity": 1,
                "unit_of_measurement": "bag",
                "expiration_date": "2024-06-01",
                "user_id": 111,
                "pantry_item_id": 2
            }
        ]
        
        # Mock user preferences
        mock_dependencies['db'].execute_query.side_effect = [
            # First call for pantry items (above)
            mock_dependencies['db'].execute_query.return_value,
            # Second call for preferences
            [{
                "preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "allergens": ["nuts"],
                    "cuisine_preferences": ["italian", "mexican"]
                }
            }]
        ]
        
        # Mock saved recipes
        mock_dependencies['user_recipes'].match_recipes_with_pantry = AsyncMock(return_value=[])
        
        # Mock Spoonacular recipes
        mock_dependencies['spoonacular'].search_recipes_by_ingredients = AsyncMock(return_value=[
            {
                "id": 123,
                "title": "Chicken and Rice",
                "missedIngredients": [],
                "usedIngredients": [
                    {"name": "chicken", "original": "2 chicken breasts"},
                    {"name": "rice", "original": "1 cup rice"}
                ]
            }
        ])
        
        mock_dependencies['spoonacular'].get_recipe_information = AsyncMock(return_value={
            "id": 123,
            "title": "Chicken and Rice",
            "readyInMinutes": 30,
            "servings": 4,
            "cuisines": ["american"],
            "diets": [],
            "extendedIngredients": [
                {"name": "chicken", "amount": 2, "unit": "breasts"},
                {"name": "rice", "amount": 1, "unit": "cup"}
            ],
            "analyzedInstructions": [{
                "steps": [
                    {"step": "Cook rice according to package"},
                    {"step": "Season and cook chicken"},
                    {"step": "Serve together"}
                ]
            }],
            "nutrition": {
                "nutrients": [
                    {"name": "Calories", "amount": 400},
                    {"name": "Protein", "amount": 35}
                ]
            }
        })
        
        # Mock preference scorer
        mock_dependencies['scorer'].calculate_comprehensive_score.return_value = {
            "score": 85.0,
            "reasoning": ["High protein content", "Uses available ingredients"],
            "recommendation_level": "Highly Recommended",
            "components": {}
        }
        
        # Test the service
        result = await service.process_message(
            user_id=111,
            message="What can I make for dinner?",
            use_preferences=True
        )
        
        # Verify response structure
        assert "response" in result
        assert "recipes" in result
        assert "pantry_items" in result
        assert "user_preferences" in result
        
        # Verify recipes were returned
        assert len(result["recipes"]) > 0
        recipe = result["recipes"][0]
        assert recipe["name"] == "Chicken and Rice"
        assert recipe["time"] == 30
        assert recipe["meal_type"] == "dinner"
        assert recipe["missing_count"] == 0
        assert recipe["available_count"] == 2
        
        # Verify pantry items
        assert len(result["pantry_items"]) == 2
        
        # Verify preferences
        assert "vegetarian" in result["user_preferences"]["dietary_preference"]
    
    @pytest.mark.asyncio
    async def test_process_message_expiring_items(self, mock_dependencies):
        """Test processing a message about expiring items"""
        service = CrewAIService()
        
        # Mock pantry with expiring items
        today = datetime.now().date()
        mock_dependencies['db'].execute_query.return_value = [
            {
                "product_name": "Milk",
                "category": "dairy",
                "quantity": 1,
                "unit_of_measurement": "gallon",
                "expiration_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "user_id": 111,
                "pantry_item_id": 1
            },
            {
                "product_name": "Yogurt",
                "category": "dairy",
                "expiration_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "user_id": 111,
                "pantry_item_id": 2
            }
        ]
        
        # Mock empty preferences
        mock_dependencies['db'].execute_query.side_effect = [
            mock_dependencies['db'].execute_query.return_value,
            []  # No preferences
        ]
        
        # Mock recipes that use expiring items
        mock_dependencies['user_recipes'].match_recipes_with_pantry = AsyncMock(return_value=[])
        mock_dependencies['spoonacular'].search_recipes_by_ingredients = AsyncMock(return_value=[
            {
                "id": 456,
                "title": "Yogurt Smoothie",
                "usedIngredients": [{"name": "yogurt"}, {"name": "milk"}]
            }
        ])
        
        mock_dependencies['spoonacular'].get_recipe_information = AsyncMock(return_value={
            "id": 456,
            "title": "Yogurt Smoothie",
            "readyInMinutes": 5,
            "extendedIngredients": [
                {"name": "yogurt", "amount": 1, "unit": "cup"},
                {"name": "milk", "amount": 0.5, "unit": "cup"}
            ],
            "analyzedInstructions": [{"steps": [{"step": "Blend all ingredients"}]}],
            "nutrition": {"nutrients": [{"name": "Calories", "amount": 150}]}
        })
        
        mock_dependencies['scorer'].calculate_comprehensive_score.return_value = {
            "score": 90.0,
            "reasoning": ["Uses expiring ingredients"],
            "recommendation_level": "Highly Recommended",
            "components": {}
        }
        
        result = await service.process_message(
            user_id=111,
            message="What items are expiring soon?",
            use_preferences=False
        )
        
        # Verify expiring items are mentioned
        assert "expiring" in result["response"].lower()
        assert len(result["recipes"]) > 0
        
        # Verify recipe uses expiring items
        recipe = result["recipes"][0]
        assert "Smoothie" in recipe["name"]
    
    def test_clean_ingredient_name(self):
        """Test ingredient name cleaning logic"""
        service = CrewAIService()
        
        # Test various ingredient formats
        assert service._clean_ingredient_name("Chicken Breast – 2 lbs") == "chicken breast"
        assert service._clean_ingredient_name("Fresh Organic Spinach") == "spinach"
        assert service._clean_ingredient_name("1.5 oz frozen peas") == "peas"
        assert service._clean_ingredient_name("Diced tomatoes (canned)") == "tomatoes"
        assert service._clean_ingredient_name("2 cups whole milk") == "milk"
    
    def test_is_similar_ingredient(self):
        """Test ingredient similarity matching"""
        service = CrewAIService()
        
        # Test exact matches
        assert service._is_similar_ingredient("chicken", "chicken") == True
        
        # Test variations
        assert service._is_similar_ingredient("chicken breast", "chicken") == True
        assert service._is_similar_ingredient("whole milk", "milk") == True
        assert service._is_similar_ingredient("roma tomatoes", "tomatoes") == True
        
        # Test non-matches
        assert service._is_similar_ingredient("chicken", "beef") == False
        assert service._is_similar_ingredient("milk", "almond milk") == False
        assert service._is_similar_ingredient("ham", "hamburger") == False
    
    def test_is_allergen_in_ingredient(self):
        """Test allergen detection in ingredients"""
        service = CrewAIService()
        
        # Test direct allergen matches
        assert service._is_allergen_in_ingredient("dairy", "milk") == True
        assert service._is_allergen_in_ingredient("nuts", "almond butter") == True
        assert service._is_allergen_in_ingredient("eggs", "scrambled eggs") == True
        assert service._is_allergen_in_ingredient("gluten", "wheat flour") == True
        
        # Test indirect matches
        assert service._is_allergen_in_ingredient("dairy", "cheese sauce") == True
        assert service._is_allergen_in_ingredient("shellfish", "shrimp cocktail") == True
        
        # Test non-matches
        assert service._is_allergen_in_ingredient("dairy", "olive oil") == False
        assert service._is_allergen_in_ingredient("nuts", "sunflower seeds") == False
    
    def test_detect_meal_type(self):
        """Test meal type detection from recipe title and message"""
        service = CrewAIService()
        
        # Test based on message
        assert service._detect_meal_type("Any recipe", "What's for breakfast?") == "breakfast"
        assert service._detect_meal_type("Any recipe", "lunch ideas please") == "lunch"
        assert service._detect_meal_type("Any recipe", "dinner tonight") == "dinner"
        assert service._detect_meal_type("Any recipe", "need a snack") == "snack"
        
        # Test based on recipe title
        assert service._detect_meal_type("Pancakes with Syrup", "") == "breakfast"
        assert service._detect_meal_type("Caesar Salad", "") == "lunch"
        assert service._detect_meal_type("Chocolate Cake", "") == "dessert"
        
        # Test default
        assert service._detect_meal_type("Random Recipe", "") == "dinner"
    
    @pytest.mark.asyncio
    async def test_combine_recipe_sources(self):
        """Test combining saved and AI recipes without duplicates"""
        service = CrewAIService()
        
        saved_recipes = [
            {"name": "Chicken Pasta", "source": "saved"},
            {"name": "Beef Stir Fry", "source": "saved"}
        ]
        
        ai_recipes = [
            {"name": "chicken pasta", "source": "spoonacular"},  # Duplicate
            {"name": "Vegetable Soup", "source": "spoonacular"},
            {"name": "Beef Stir-Fry", "source": "spoonacular"}  # Similar name
        ]
        
        combined = service._combine_recipe_sources(saved_recipes, ai_recipes)
        
        # Should have 3 recipes (2 saved + 1 unique AI)
        assert len(combined) == 3
        
        # Verify saved recipes come first
        assert combined[0]["name"] == "Chicken Pasta"
        assert combined[1]["name"] == "Beef Stir Fry"
        assert combined[2]["name"] == "Vegetable Soup"
    
    def test_format_response_expiring_items(self):
        """Test response formatting for expiring items query"""
        service = CrewAIService()
        
        today = datetime.now().date()
        items = [
            {
                "product_name": "Milk",
                "expiration_date": today.strftime("%Y-%m-%d")  # Expires today
            },
            {
                "product_name": "Yogurt",
                "expiration_date": (today + timedelta(days=3)).strftime("%Y-%m-%d")
            }
        ]
        
        recipes = []
        user_prefs = {}
        
        response = service._format_response(
            recipes, items, "What's expiring soon?", user_prefs
        )
        
        assert "expiring soon" in response
        assert "Expires TODAY!" in response
        assert "Yogurt" in response
        assert "3 days" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])