"""
Real integration tests for recipe data flow without mocks.
Tests actual database operations, API calls, and data parsing.
"""

import pytest
import asyncio
from datetime import datetime
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend_gateway.services.database_service import DatabaseService
from backend_gateway.services.recipe_service import RecipeService
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.spoonacular_service import SpoonacularService


class TestRealRecipeIntegration:
    """Test actual recipe data flow from database to API responses"""
    
    @pytest.fixture
    async def real_db_service(self):
        """Create real database service with test database"""
        # Use test database URL from environment
        db_url = os.environ.get("DATABASE_URL", "postgresql://test@localhost/test_db")
        service = DatabaseService(db_url)
        
        # Initialize database schema if needed
        await service.initialize_database()
        
        yield service
        
        # Cleanup after tests
        await service.cleanup_test_data()
    
    @pytest.fixture
    def real_recipe_service(self):
        """Create real recipe service with actual API key"""
        return RecipeService()
    
    @pytest.fixture
    def real_pantry_service(self, real_db_service):
        """Create real pantry service"""
        return PantryService(real_db_service)
    
    @pytest.fixture
    def real_spoonacular_service(self):
        """Create real Spoonacular service"""
        return SpoonacularService()
    
    @pytest.mark.asyncio
    async def test_complete_recipe_flow_with_real_data(self, real_db_service, real_pantry_service, real_spoonacular_service):
        """Test complete flow: add pantry items → get recipes → check ingredient matching"""
        
        # Step 1: Add real pantry items to database
        test_user_id = 999  # Test user ID
        
        pantry_items = [
            {
                'product_name': 'Chicken Breast',
                'quantity': 2.0,
                'unit_of_measurement': 'lb',
                'category': 'meat',
                'expiration_date': '2024-12-31'
            },
            {
                'product_name': 'White Rice',
                'quantity': 500,
                'unit_of_measurement': 'g',
                'category': 'grain',
                'expiration_date': '2025-06-01'
            },
            {
                'product_name': 'Broccoli',
                'quantity': 2,
                'unit_of_measurement': 'heads',
                'category': 'vegetable',
                'expiration_date': '2024-11-15'
            }
        ]
        
        # Add items to database
        for item in pantry_items:
            await real_pantry_service.add_pantry_item(
                user_id=test_user_id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit_of_measurement=item['unit_of_measurement'],
                category=item['category'],
                expiration_date=item['expiration_date']
            )
        
        # Step 2: Get pantry items from database
        db_pantry_items = await real_pantry_service.get_user_pantry_items(test_user_id)
        assert len(db_pantry_items) >= 3
        
        # Step 3: Get recipes from Spoonacular based on pantry
        ingredient_list = [item['product_name'] for item in db_pantry_items]
        recipes = await real_spoonacular_service.find_recipes_by_ingredients(
            ingredients=ingredient_list,
            number=5
        )
        
        assert len(recipes) > 0
        
        # Step 4: For each recipe, verify ingredient matching
        for recipe in recipes:
            recipe_id = recipe['id']
            
            # Get full recipe details
            recipe_details = await real_spoonacular_service.get_recipe_information(recipe_id)
            
            # Verify recipe has required fields
            assert 'title' in recipe_details
            assert 'extendedIngredients' in recipe_details
            assert 'analyzedInstructions' in recipe_details
            
            # Check ingredient matching
            used_count = 0
            missed_count = 0
            
            for ingredient in recipe_details['extendedIngredients']:
                matched = False
                for pantry_item in db_pantry_items:
                    if self._ingredient_matches(ingredient['name'], pantry_item['product_name']):
                        used_count += 1
                        matched = True
                        break
                
                if not matched:
                    missed_count += 1
            
            # Verify counts match what API reported
            assert used_count == recipe.get('usedIngredientCount', 0)
            assert missed_count == recipe.get('missedIngredientCount', 0)
        
        # Cleanup
        await real_pantry_service.delete_all_user_items(test_user_id)
    
    @pytest.mark.asyncio
    async def test_recipe_instructions_completeness(self, real_spoonacular_service):
        """Test that recipe instructions are complete and ordered"""
        
        # Get a known recipe with multiple steps
        recipe_id = 716429  # Pasta with Garlic, Scallions, Cauliflower & Breadcrumbs
        recipe = await real_spoonacular_service.get_recipe_information(recipe_id)
        
        assert 'analyzedInstructions' in recipe
        assert len(recipe['analyzedInstructions']) > 0
        
        # Extract all steps
        all_steps = []
        for instruction_group in recipe['analyzedInstructions']:
            if 'steps' in instruction_group:
                all_steps.extend(instruction_group['steps'])
        
        # Verify steps are ordered
        assert len(all_steps) > 0
        step_numbers = [step['number'] for step in all_steps]
        assert step_numbers == sorted(step_numbers)
        
        # Verify no missing step numbers
        expected_steps = list(range(1, len(all_steps) + 1))
        assert step_numbers == expected_steps
        
        # Verify each step has content
        for step in all_steps:
            assert 'step' in step
            assert len(step['step']) > 0
    
    @pytest.mark.asyncio
    async def test_nutrition_data_validation(self, real_spoonacular_service):
        """Test that nutrition data is complete and valid"""
        
        recipe_id = 716429
        recipe = await real_spoonacular_service.get_recipe_information(recipe_id)
        
        assert 'nutrition' in recipe
        nutrition = recipe['nutrition']
        
        assert 'nutrients' in nutrition
        nutrients = nutrition['nutrients']
        
        # Check for essential nutrients
        essential_nutrients = ['Calories', 'Protein', 'Fat', 'Carbohydrates']
        found_nutrients = {n['name']: n for n in nutrients}
        
        for essential in essential_nutrients:
            assert essential in found_nutrients
            nutrient = found_nutrients[essential]
            
            # Verify nutrient has valid data
            assert 'amount' in nutrient
            assert nutrient['amount'] >= 0
            assert 'unit' in nutrient
            assert len(nutrient['unit']) > 0
    
    @pytest.mark.asyncio
    async def test_recipe_completion_updates_pantry(self, real_db_service, real_pantry_service, real_recipe_service):
        """Test that completing a recipe updates pantry quantities"""
        
        test_user_id = 998
        
        # Add pantry items
        initial_items = [
            {
                'product_name': 'Pasta',
                'quantity': 500,
                'unit_of_measurement': 'g',
                'category': 'grain'
            },
            {
                'product_name': 'Tomato Sauce',
                'quantity': 400,
                'unit_of_measurement': 'ml',
                'category': 'sauce'
            }
        ]
        
        for item in initial_items:
            await real_pantry_service.add_pantry_item(
                user_id=test_user_id,
                **item
            )
        
        # Get initial quantities
        before_items = await real_pantry_service.get_user_pantry_items(test_user_id)
        before_quantities = {item['product_name']: item['quantity'] for item in before_items}
        
        # Complete a recipe that uses these ingredients
        recipe_ingredients = [
            {'name': 'pasta', 'amount': 200, 'unit': 'g'},
            {'name': 'tomato sauce', 'amount': 150, 'unit': 'ml'}
        ]
        
        # Update pantry after recipe completion
        for ingredient in recipe_ingredients:
            for pantry_item in before_items:
                if self._ingredient_matches(ingredient['name'], pantry_item['product_name']):
                    new_quantity = pantry_item['quantity'] - ingredient['amount']
                    if new_quantity > 0:
                        await real_pantry_service.update_pantry_item(
                            pantry_item['pantry_item_id'],
                            quantity=new_quantity
                        )
                    else:
                        await real_pantry_service.delete_pantry_item(
                            pantry_item['pantry_item_id']
                        )
        
        # Verify quantities were updated
        after_items = await real_pantry_service.get_user_pantry_items(test_user_id)
        after_quantities = {item['product_name']: item['quantity'] for item in after_items}
        
        assert after_quantities.get('Pasta', 0) == 300  # 500 - 200
        assert after_quantities.get('Tomato Sauce', 0) == 250  # 400 - 150
        
        # Cleanup
        await real_pantry_service.delete_all_user_items(test_user_id)
    
    def _ingredient_matches(self, recipe_ingredient: str, pantry_item: str) -> bool:
        """Check if recipe ingredient matches pantry item"""
        recipe_lower = recipe_ingredient.lower()
        pantry_lower = pantry_item.lower()
        
        # Direct match
        if recipe_lower in pantry_lower or pantry_lower in recipe_lower:
            return True
        
        # Check individual words
        recipe_words = set(recipe_lower.split())
        pantry_words = set(pantry_lower.split())
        
        # If any significant word matches
        common_words = recipe_words.intersection(pantry_words)
        # Filter out common words like 'and', 'or', etc.
        significant_words = [w for w in common_words if len(w) > 2]
        
        return len(significant_words) > 0
    
    @pytest.mark.asyncio
    async def test_recipe_search_with_filters(self, real_spoonacular_service):
        """Test recipe search with dietary filters"""
        
        # Search for vegetarian recipes
        recipes = await real_spoonacular_service.search_recipes(
            query="pasta",
            diet="vegetarian",
            number=5
        )
        
        assert len(recipes) > 0
        
        # Verify each recipe to ensure it's actually vegetarian
        for recipe in recipes[:2]:  # Check first 2 to avoid rate limits
            details = await real_spoonacular_service.get_recipe_information(recipe['id'])
            
            # Check that recipe is marked as vegetarian
            assert details.get('vegetarian', False) == True
            
            # Verify no meat ingredients
            if 'extendedIngredients' in details:
                ingredient_names = [ing['name'].lower() for ing in details['extendedIngredients']]
                meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'meat', 'bacon']
                
                for meat in meat_keywords:
                    for ingredient in ingredient_names:
                        assert meat not in ingredient
