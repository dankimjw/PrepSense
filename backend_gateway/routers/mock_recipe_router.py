"""Mock recipe router for testing recipe completion and pantry subtraction"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mock",
    tags=["Mock Data"],
    responses={404: {"description": "Not found"}},
)

# Mock recipes that match demo pantry items
MOCK_RECIPES_FOR_TESTING = [
    {
        "id": 645714,
        "title": "Classic Spaghetti Carbonara",
        "image": "https://img.spoonacular.com/recipes/645714-556x370.jpg",
        "readyInMinutes": 30,
        "servings": 4,
        "extendedIngredients": [
            {
                "id": 1,
                "name": "pasta",
                "original": "400g pasta (spaghetti)",
                "amount": 400,
                "unit": "g",
                "originalName": "pasta (spaghetti)",
            },
            {
                "id": 2,
                "name": "eggs",
                "original": "4 large eggs",
                "amount": 4,
                "unit": "",
                "originalName": "large eggs",
            },
            {
                "id": 3,
                "name": "olive oil",
                "original": "2 tablespoons olive oil",
                "amount": 2,
                "unit": "tablespoons",
                "originalName": "olive oil",
            },
            {
                "id": 4,
                "name": "salt",
                "original": "1 teaspoon salt",
                "amount": 1,
                "unit": "teaspoon",
                "originalName": "salt",
            },
            {
                "id": 5,
                "name": "black pepper",
                "original": "1/2 teaspoon black pepper",
                "amount": 0.5,
                "unit": "teaspoon",
                "originalName": "black pepper",
            },
        ],
        "analyzedInstructions": [
            {
                "name": "",
                "steps": [
                    {
                        "number": 1,
                        "step": "Bring a large pot of salted water to boil and cook pasta according to package directions.",
                    },
                    {
                        "number": 2,
                        "step": "While pasta cooks, whisk eggs with salt and pepper in a bowl.",
                    },
                    {"number": 3, "step": "Drain pasta, reserving 1 cup pasta water."},
                    {
                        "number": 4,
                        "step": "Toss hot pasta with egg mixture and olive oil to create creamy sauce.",
                    },
                ],
            }
        ],
    },
    {
        "id": 635675,
        "title": "Chocolate Chip Cookies",
        "image": "https://img.spoonacular.com/recipes/635675-556x370.jpg",
        "readyInMinutes": 45,
        "servings": 24,
        "extendedIngredients": [
            {
                "id": 1,
                "name": "all-purpose flour",
                "original": "2 1/4 cups all-purpose flour",
                "amount": 2.25,
                "unit": "cups",
                "originalName": "all-purpose flour",
            },
            {
                "id": 2,
                "name": "butter",
                "original": "1 cup butter, softened",
                "amount": 1,
                "unit": "cup",
                "originalName": "butter, softened",
            },
            {
                "id": 3,
                "name": "granulated sugar",
                "original": "3/4 cup granulated sugar",
                "amount": 0.75,
                "unit": "cup",
                "originalName": "granulated sugar",
            },
            {
                "id": 4,
                "name": "eggs",
                "original": "2 large eggs",
                "amount": 2,
                "unit": "",
                "originalName": "large eggs",
            },
            {
                "id": 5,
                "name": "vanilla extract",
                "original": "1 teaspoon vanilla extract",
                "amount": 1,
                "unit": "teaspoon",
                "originalName": "vanilla extract",
            },
            {
                "id": 6,
                "name": "salt",
                "original": "1 teaspoon salt",
                "amount": 1,
                "unit": "teaspoon",
                "originalName": "salt",
            },
        ],
        "analyzedInstructions": [
            {
                "name": "",
                "steps": [
                    {"number": 1, "step": "Preheat oven to 375°F (190°C)."},
                    {"number": 2, "step": "Cream butter and sugars until fluffy."},
                    {"number": 3, "step": "Beat in eggs and vanilla."},
                    {"number": 4, "step": "Mix in flour and salt."},
                    {"number": 5, "step": "Drop dough on baking sheets and bake 9-11 minutes."},
                ],
            }
        ],
    },
    {
        "id": 632665,
        "title": "Lemon Herb Roasted Chicken",
        "image": "https://img.spoonacular.com/recipes/632665-556x370.jpg",
        "readyInMinutes": 60,
        "servings": 4,
        "extendedIngredients": [
            {
                "id": 1,
                "name": "chicken breast",
                "original": "1.5 pounds chicken breast",
                "amount": 1.5,
                "unit": "pounds",
                "originalName": "chicken breast",
            },
            {
                "id": 2,
                "name": "olive oil",
                "original": "1/4 cup olive oil",
                "amount": 0.25,
                "unit": "cup",
                "originalName": "olive oil",
            },
            {
                "id": 3,
                "name": "salt",
                "original": "2 teaspoons salt",
                "amount": 2,
                "unit": "teaspoons",
                "originalName": "salt",
            },
            {
                "id": 4,
                "name": "black pepper",
                "original": "1 teaspoon black pepper",
                "amount": 1,
                "unit": "teaspoon",
                "originalName": "black pepper",
            },
        ],
        "analyzedInstructions": [
            {
                "name": "",
                "steps": [
                    {"number": 1, "step": "Preheat oven to 425°F (220°C)."},
                    {"number": 2, "step": "Season chicken with salt and pepper."},
                    {"number": 3, "step": "Drizzle with olive oil."},
                    {"number": 4, "step": "Roast for 45-50 minutes until golden."},
                ],
            }
        ],
    },
]

# Import RemoteControl
from backend_gateway.RemoteControl_7 import is_chat_recipes_mock_enabled, set_mock

# Enable/disable mock mode - DEPRECATED, use RemoteControl instead
use_mock_recipes = False


@router.post("/enable-mock-recipes", summary="Enable mock recipes for testing")
async def enable_mock_recipes(enable: bool = True):
    """Enable or disable mock recipe mode"""
    # Update RemoteControl instead of local variable
    set_mock("chat_recipes", enable, "mock_recipe_router")
    return {
        "success": True,
        "mock_recipes_enabled": enable,
        "message": f"Mock recipes {'enabled' if enable else 'disabled'}",
    }


@router.get("/test-recipes", summary="Get mock recipes for testing")
async def get_mock_recipes():
    """Get the mock recipes that will be used for testing"""
    return {
        "recipes": MOCK_RECIPES_FOR_TESTING,
        "enabled": is_chat_recipes_mock_enabled(),
        "message": "These are the recipes that will be recommended when mock mode is enabled",
    }


@router.get("/mock-recipe/{recipe_id}", summary="Get a specific mock recipe")
async def get_mock_recipe(recipe_id: int):
    """Get details for a specific mock recipe"""
    for recipe in MOCK_RECIPES_FOR_TESTING:
        if recipe["id"] == recipe_id:
            return recipe

    raise HTTPException(status_code=404, detail="Mock recipe not found")


def get_mock_recipes_for_chat():
    """Helper function to get mock recipes in chat format"""
    if not is_chat_recipes_mock_enabled():
        return None

    return [
        {
            "name": recipe["title"],
            "ingredients": [ing["original"] for ing in recipe["extendedIngredients"]],
            "instructions": [
                step["step"] for inst in recipe["analyzedInstructions"] for step in inst["steps"]
            ],
            "time": recipe["readyInMinutes"],
            "nutrition": {"calories": 420, "protein": 18},
            "available_ingredients": ["pasta", "eggs", "olive oil", "salt", "pepper"],
            "missing_ingredients": [],
            "missing_count": 0,
            "available_count": 5,
            "match_score": 0.95,
        }
        for recipe in MOCK_RECIPES_FOR_TESTING
    ]


# Export for use in other modules
__all__ = ["router", "get_mock_recipes_for_chat", "use_mock_recipes", "MOCK_RECIPES_FOR_TESTING"]
