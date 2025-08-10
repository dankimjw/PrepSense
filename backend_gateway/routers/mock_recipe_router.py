"""Mock recipe router for testing recipe completion and pantry subtraction"""

import logging

from fastapi import APIRouter, HTTPException

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
                "name": "eggs",
                "original": "2 large eggs",
                "amount": 2,
                "unit": "",
                "originalName": "large eggs",
            },
            {
                "id": 4,
                "name": "chocolate chips",
                "original": "2 cups chocolate chips",
                "amount": 2,
                "unit": "cups",
                "originalName": "chocolate chips",
            },
        ],
        "analyzedInstructions": [
            {
                "name": "",
                "steps": [
                    {"number": 1, "step": "Preheat oven to 375°F."},
                    {"number": 2, "step": "Mix flour and butter in large bowl."},
                    {"number": 3, "step": "Beat in eggs until well combined."},
                    {"number": 4, "step": "Stir in chocolate chips."},
                    {"number": 5, "step": "Drop spoonfuls on baking sheet and bake 9-11 minutes."},
                ],
            }
        ],
    },
    {
        "id": 654959,
        "title": "Spinach Coriander Chive Bread",
        "image": "https://img.spoonacular.com/recipes/654959-556x370.jpg",
        "readyInMinutes": 25,
        "servings": 6,
        "extendedIngredients": [
            {
                "id": 1,
                "name": "spinach",
                "original": "2 cups fresh spinach, chopped",
                "amount": 2,
                "unit": "cups",
                "originalName": "fresh spinach, chopped",
            },
            {
                "id": 2,
                "name": "coriander",
                "original": "1/4 cup fresh coriander, chopped",
                "amount": 0.25,
                "unit": "cup",
                "originalName": "fresh coriander, chopped",
            },
            {
                "id": 3,
                "name": "chives",
                "original": "2 tablespoons fresh chives, chopped",
                "amount": 2,
                "unit": "tablespoons",
                "originalName": "fresh chives, chopped",
            },
            {
                "id": 4,
                "name": "bread flour",
                "original": "3 cups bread flour",
                "amount": 3,
                "unit": "cups",
                "originalName": "bread flour",
            },
            {
                "id": 5,
                "name": "eggs",
                "original": "2 eggs",
                "amount": 2,
                "unit": "",
                "originalName": "eggs",
            },
        ],
        "analyzedInstructions": [
            {
                "name": "",
                "steps": [
                    {"number": 1, "step": "Preheat oven to 350°F."},
                    {"number": 2, "step": "Mix spinach, coriander, and chives in a bowl."},
                    {"number": 3, "step": "Combine bread flour with herb mixture."},
                    {"number": 4, "step": "Beat eggs and fold into mixture."},
                    {"number": 5, "step": "Form into loaf and bake 25 minutes until golden."},
                ],
            }
        ],
    },
]


def is_chat_recipes_mock_enabled() -> bool:
    """Check if mock recipes are enabled for chat"""
    try:
        from backend_gateway.RemoteControl_7 import is_chat_recipes_mock_enabled as rc_enabled

        return rc_enabled()
    except ImportError:
        return False


def set_mock(key: str, value: bool, source: str = "mock_router"):
    """Set mock state through RemoteControl"""
    try:
        from backend_gateway.RemoteControl_7 import set_mock as rc_set_mock

        return rc_set_mock(key, value, source)
    except ImportError:
        logger.warning("RemoteControl not available, mock state not persisted")
        return False


@router.post("/enable", summary="Enable mock recipes for testing")
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
    """Helper function to get mock recipes in chat format with proper IDs"""
    if not is_chat_recipes_mock_enabled():
        return None

    return [
        {
            "id": recipe["id"],  # ✅ ADD MISSING ID FROM MOCK DATA
            "name": recipe["title"],
            "ingredients": [ing["original"] for ing in recipe["extendedIngredients"]],
            "instructions": [
                step["step"] for inst in recipe["analyzedInstructions"] for step in inst["steps"]
            ],
            "time": recipe["readyInMinutes"],
            "servings": recipe.get("servings", 4),
            "image_url": recipe.get("image", ""),
            "source": "mock",  # ✅ ADD SOURCE IDENTIFIER
            "nutrition": {"calories": 420, "protein": 18},
            "available_ingredients": ["pasta", "eggs", "olive oil", "salt", "pepper"],
            "missing_ingredients": [],
            "missing_count": 0,
            "available_count": 5,
            "match_score": 0.95,
            "can_make": True,  # ✅ ADD MISSING FIELDS
            "recipe_id": recipe["id"],  # ✅ BACKUP ID FIELD
        }
        for recipe in MOCK_RECIPES_FOR_TESTING
    ]


# Export for use in other modules
__all__ = ["router", "get_mock_recipes_for_chat", "use_mock_recipes", "MOCK_RECIPES_FOR_TESTING"]
