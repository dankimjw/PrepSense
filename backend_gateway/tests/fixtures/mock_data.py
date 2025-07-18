"""Mock data and fixtures for testing"""
from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_mock_pantry_items(user_id: int = 111) -> List[Dict[str, Any]]:
    """Get mock pantry items for testing"""
    today = datetime.now().date()
    return [
        {
            "pantry_item_id": 1,
            "user_id": user_id,
            "product_name": "Chicken Breast",
            "quantity": 2,
            "unit_of_measurement": "lbs",
            "expiration_date": (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            "category": "protein",
            "purchase_date": (today - timedelta(days=4)).strftime('%Y-%m-%d')
        },
        {
            "pantry_item_id": 2,
            "user_id": user_id,
            "product_name": "Milk",
            "quantity": 0.5,
            "unit_of_measurement": "gallon",
            "expiration_date": (today + timedelta(days=2)).strftime('%Y-%m-%d'),
            "category": "dairy",
            "purchase_date": (today - timedelta(days=5)).strftime('%Y-%m-%d')
        },
        {
            "pantry_item_id": 3,
            "user_id": user_id,
            "product_name": "Rice",
            "quantity": 5,
            "unit_of_measurement": "lbs",
            "expiration_date": (today + timedelta(days=180)).strftime('%Y-%m-%d'),
            "category": "grains",
            "purchase_date": (today - timedelta(days=30)).strftime('%Y-%m-%d')
        },
        {
            "pantry_item_id": 4,
            "user_id": user_id,
            "product_name": "Broccoli",
            "quantity": 2,
            "unit_of_measurement": "bunch",
            "expiration_date": (today + timedelta(days=5)).strftime('%Y-%m-%d'),
            "category": "vegetables",
            "purchase_date": (today - timedelta(days=2)).strftime('%Y-%m-%d')
        },
        {
            "pantry_item_id": 5,
            "user_id": user_id,
            "product_name": "Eggs",
            "quantity": 12,
            "unit_of_measurement": "count",
            "expiration_date": (today + timedelta(days=14)).strftime('%Y-%m-%d'),
            "category": "protein",
            "purchase_date": (today - timedelta(days=3)).strftime('%Y-%m-%d')
        },
        {
            "pantry_item_id": 6,
            "user_id": user_id,
            "product_name": "Bread",
            "quantity": 1,
            "unit_of_measurement": "loaf",
            "expiration_date": (today - timedelta(days=1)).strftime('%Y-%m-%d'),  # Expired
            "category": "grains",
            "purchase_date": (today - timedelta(days=7)).strftime('%Y-%m-%d')
        }
    ]


def get_mock_user_preferences(user_id: int = 111) -> Dict[str, Any]:
    """Get mock user preferences"""
    return {
        "user_id": user_id,
        "preferences": {
            "dietary_restrictions": ["vegetarian"],
            "allergens": ["nuts", "shellfish"],
            "cuisine_preferences": ["italian", "asian", "mexican"],
            "cooking_skill": "intermediate",
            "max_cooking_time": 45
        }
    }


def get_mock_spoonacular_recipes() -> List[Dict[str, Any]]:
    """Get mock Spoonacular API response"""
    return [
        {
            "id": 12345,
            "title": "Chicken and Rice Stir Fry",
            "image": "https://spoonacular.com/recipe-12345.jpg",
            "usedIngredients": [
                {"id": 1, "original": "2 lbs chicken breast", "name": "chicken breast"},
                {"id": 2, "original": "2 cups rice", "name": "rice"}
            ],
            "missedIngredients": [
                {"id": 3, "original": "2 tbsp soy sauce", "name": "soy sauce"},
                {"id": 4, "original": "1 tsp ginger", "name": "ginger"}
            ]
        },
        {
            "id": 67890,
            "title": "Creamy Chicken and Broccoli",
            "image": "https://spoonacular.com/recipe-67890.jpg",
            "usedIngredients": [
                {"id": 1, "original": "1 lb chicken breast", "name": "chicken breast"},
                {"id": 2, "original": "2 cups broccoli", "name": "broccoli"},
                {"id": 3, "original": "1 cup milk", "name": "milk"}
            ],
            "missedIngredients": [
                {"id": 4, "original": "2 cloves garlic", "name": "garlic"}
            ]
        }
    ]


def get_mock_spoonacular_recipe_details(recipe_id: int) -> Dict[str, Any]:
    """Get mock detailed recipe information from Spoonacular"""
    recipes = {
        12345: {
            "id": 12345,
            "title": "Chicken and Rice Stir Fry",
            "readyInMinutes": 25,
            "servings": 4,
            "sourceUrl": "https://example.com/recipe-12345",
            "image": "https://spoonacular.com/recipe-12345.jpg",
            "cuisines": ["asian"],
            "diets": ["gluten free"],
            "extendedIngredients": [
                {
                    "id": 1,
                    "name": "chicken breast",
                    "original": "2 lbs chicken breast, diced",
                    "amount": 2,
                    "unit": "lbs"
                },
                {
                    "id": 2,
                    "name": "rice",
                    "original": "2 cups rice",
                    "amount": 2,
                    "unit": "cups"
                },
                {
                    "id": 3,
                    "name": "soy sauce",
                    "original": "2 tbsp soy sauce",
                    "amount": 2,
                    "unit": "tbsp"
                }
            ],
            "analyzedInstructions": [{
                "name": "",
                "steps": [
                    {"number": 1, "step": "Cook rice according to package directions"},
                    {"number": 2, "step": "Heat oil in a large wok or skillet"},
                    {"number": 3, "step": "Add diced chicken and cook until golden"},
                    {"number": 4, "step": "Add vegetables and stir fry for 3-4 minutes"},
                    {"number": 5, "step": "Add cooked rice and soy sauce, stir to combine"}
                ]
            }],
            "nutrition": {
                "nutrients": [
                    {"name": "Calories", "amount": 420, "unit": "kcal"},
                    {"name": "Protein", "amount": 32, "unit": "g"},
                    {"name": "Fat", "amount": 12, "unit": "g"},
                    {"name": "Carbohydrates", "amount": 45, "unit": "g"}
                ]
            }
        },
        67890: {
            "id": 67890,
            "title": "Creamy Chicken and Broccoli",
            "readyInMinutes": 30,
            "servings": 4,
            "sourceUrl": "https://example.com/recipe-67890",
            "image": "https://spoonacular.com/recipe-67890.jpg",
            "cuisines": ["american"],
            "diets": [],
            "extendedIngredients": [
                {
                    "id": 1,
                    "name": "chicken breast",
                    "original": "1 lb chicken breast, sliced",
                    "amount": 1,
                    "unit": "lb"
                },
                {
                    "id": 2,
                    "name": "broccoli",
                    "original": "2 cups broccoli florets",
                    "amount": 2,
                    "unit": "cups"
                },
                {
                    "id": 3,
                    "name": "milk",
                    "original": "1 cup milk",
                    "amount": 1,
                    "unit": "cup"
                },
                {
                    "id": 4,
                    "name": "garlic",
                    "original": "2 cloves garlic, minced",
                    "amount": 2,
                    "unit": "cloves"
                }
            ],
            "analyzedInstructions": [{
                "name": "",
                "steps": [
                    {"number": 1, "step": "Season chicken with salt and pepper"},
                    {"number": 2, "step": "Heat oil in a large skillet over medium heat"},
                    {"number": 3, "step": "Cook chicken until golden brown, about 6-7 minutes"},
                    {"number": 4, "step": "Add garlic and cook for 30 seconds"},
                    {"number": 5, "step": "Add broccoli and milk, simmer until tender"},
                    {"number": 6, "step": "Season to taste and serve"}
                ]
            }],
            "nutrition": {
                "nutrients": [
                    {"name": "Calories", "amount": 380, "unit": "kcal"},
                    {"name": "Protein", "amount": 28, "unit": "g"},
                    {"name": "Fat", "amount": 15, "unit": "g"},
                    {"name": "Carbohydrates", "amount": 20, "unit": "g"}
                ]
            }
        }
    }
    return recipes.get(recipe_id, {})


def get_mock_saved_recipes(user_id: int = 111) -> List[Dict[str, Any]]:
    """Get mock saved recipes for a user"""
    return [
        {
            "id": 1,
            "user_id": user_id,
            "title": "Grandma's Chicken Rice",
            "is_favorite": True,
            "rating": "thumbs_up",
            "recipe_data": {
                "ingredients": ["2 lbs chicken", "2 cups rice", "4 cups chicken broth"],
                "instructions": [
                    "Season chicken with salt and pepper",
                    "Brown chicken in a pot",
                    "Add rice and broth",
                    "Simmer for 20 minutes until rice is tender"
                ],
                "time": 35,
                "meal_type": "dinner",
                "cuisine_type": "comfort food",
                "dietary_tags": ["gluten-free"],
                "nutrition": {"calories": 450, "protein": 38}
            },
            "matched_ingredients": ["2 lbs chicken", "2 cups rice"],
            "missing_ingredients": ["4 cups chicken broth"],
            "match_score": 0.67
        },
        {
            "id": 2,
            "user_id": user_id,
            "title": "Quick Egg Fried Rice",
            "is_favorite": False,
            "rating": None,
            "recipe_data": {
                "ingredients": ["3 cups cooked rice", "3 eggs", "2 tbsp oil", "soy sauce"],
                "instructions": [
                    "Heat oil in wok",
                    "Scramble eggs and set aside",
                    "Fry rice until heated through",
                    "Add eggs back and season with soy sauce"
                ],
                "time": 15,
                "meal_type": "dinner",
                "cuisine_type": "asian",
                "dietary_tags": ["vegetarian"],
                "nutrition": {"calories": 320, "protein": 12}
            },
            "matched_ingredients": ["3 cups cooked rice", "3 eggs"],
            "missing_ingredients": ["soy sauce"],
            "match_score": 0.75
        }
    ]


class MockDatabaseService:
    """Mock database service for testing"""
    
    def __init__(self):
        self.pantry_items = get_mock_pantry_items()
        self.user_preferences = get_mock_user_preferences()
        self.saved_recipes = get_mock_saved_recipes()
    
    def execute_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock execute_query method"""
        if "user_pantry_full" in query:
            user_id = params.get("user_id", 111)
            return [item for item in self.pantry_items if item["user_id"] == user_id]
        elif "user_preferences" in query:
            user_id = params.get("user_id", 111)
            return [self.user_preferences] if self.user_preferences["user_id"] == user_id else []
        elif "user_cuisine_preferences" in query:
            # Mock cuisine preferences with preference_level
            return [
                {"user_id": 111, "cuisine": "italian", "preference_level": 2},
                {"user_id": 111, "cuisine": "asian", "preference_level": 1},
                {"user_id": 111, "cuisine": "mexican", "preference_level": 1}
            ]
        return []


class MockSpoonacularService:
    """Mock Spoonacular service for testing"""
    
    async def search_recipes_by_ingredients(self, ingredients, number=10, ranking=1, ignore_pantry=True, intolerances=None):
        """Mock recipe search"""
        return get_mock_spoonacular_recipes()[:number]
    
    async def get_recipe_information(self, recipe_id, include_nutrition=True):
        """Mock getting detailed recipe information"""
        return get_mock_spoonacular_recipe_details(recipe_id)


class MockOpenAIService:
    """Mock OpenAI service for testing"""
    
    async def generate_recipes(self, ingredients, preferences, num_recipes=5):
        """Mock recipe generation"""
        # Return empty since this is deprecated
        return []