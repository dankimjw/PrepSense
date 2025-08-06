"""Routes for recipe generation based on pantry contents."""

from fastapi import APIRouter

from backend_gateway.models import PantryDB

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/", summary="Generate a recipe from the user’s pantry")
async def create_recipe(pantry: PantryDB):
    """
    Return a simple recipe (and, optionally, an image) based on the
    pantry items supplied by the client.
    """
    # Lazy import to avoid circular dependency
    from ..services.recipe_service import RecipeService

    recipe_service = RecipeService()
    recipe_text = recipe_service.generate_recipe_from_pantry(pantry)
    return {"recipe": recipe_text}
