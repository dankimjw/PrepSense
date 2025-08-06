"""Router for user recipes management using PostgreSQL"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.config.database import get_database_service
from backend_gateway.core.security import get_current_user
from backend_gateway.services.user_recipes_service import UserRecipesService

logger = logging.getLogger(__name__)


class SaveRecipeRequest(BaseModel):
    """Request model for saving a recipe"""

    recipe_id: Optional[int] = Field(None, description="Spoonacular recipe ID if applicable")
    recipe_title: str = Field(..., description="Recipe title")
    recipe_image: Optional[str] = Field(None, description="Recipe image URL")
    recipe_data: Dict[str, Any] = Field(..., description="Complete recipe data")
    source: str = Field(..., description="Recipe source: 'spoonacular', 'generated', 'custom'")
    rating: str = Field(
        "neutral", description="Initial rating: 'thumbs_up', 'thumbs_down', 'neutral'"
    )
    is_favorite: bool = Field(False, description="Whether this recipe is marked as favorite")


class UpdateRatingRequest(BaseModel):
    """Request model for updating recipe rating"""

    rating: str = Field(..., description="New rating: 'thumbs_up', 'thumbs_down', 'neutral'")


class UpdateFavoriteRequest(BaseModel):
    """Request model for updating favorite status"""

    is_favorite: bool = Field(..., description="Whether this recipe is marked as favorite")


router = APIRouter(
    prefix="/user-recipes",
    tags=["User Recipes"],
    responses={404: {"description": "Not found"}},
)


def get_user_recipes_service(db_service=Depends(get_database_service)) -> UserRecipesService:
    """Dependency to get UserRecipesService instance"""
    return UserRecipesService(db_service)


@router.post("", response_model=Dict[str, Any], summary="Save a recipe to user's collection")
async def save_user_recipe(
    request: SaveRecipeRequest,
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Save a recipe to the user's collection"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        result = await service.save_recipe(
            user_id=user_id,
            recipe_id=request.recipe_id,
            recipe_title=request.recipe_title,
            recipe_image=request.recipe_image,
            recipe_data=request.recipe_data,
            source=request.source,
            rating=request.rating,
            is_favorite=request.is_favorite,
        )

        return result

    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


@router.get("", response_model=List[Dict[str, Any]], summary="Get user's saved recipes")
async def get_user_recipes(
    source: Optional[str] = Query(None, description="Filter by source"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    status: Optional[str] = Query(None, description="Filter by status: 'saved' or 'cooked'"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of recipes to return"),
    offset: int = Query(0, ge=0, description="Number of recipes to skip"),
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Get user's saved recipes with optional filters"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        recipes = await service.get_user_recipes(
            user_id=user_id,
            source=source,
            is_favorite=is_favorite,
            rating=rating,
            status=status,
            limit=limit,
            offset=offset,
        )

        return recipes

    except Exception as e:
        logger.error(f"Error getting user recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipes: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any], summary="Get user's recipe statistics")
async def get_recipe_stats(
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Get statistics about user's saved recipes"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        stats = await service.get_recipe_stats(user_id)

        return stats

    except Exception as e:
        logger.error(f"Error getting recipe stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.put("/{recipe_id}/rating", response_model=Dict[str, Any], summary="Update recipe rating")
async def update_recipe_rating(
    recipe_id: int,
    request: UpdateRatingRequest,
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Update the rating for a saved recipe"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        result = await service.update_recipe_rating(
            user_id=user_id, recipe_id=recipe_id, rating=request.rating
        )

        return result

    except Exception as e:
        logger.error(f"Error updating recipe rating: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update rating: {str(e)}")


@router.put(
    "/{recipe_id}/favorite", response_model=Dict[str, Any], summary="Toggle recipe favorite status"
)
async def toggle_recipe_favorite(
    recipe_id: int,
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Toggle the favorite status for a saved recipe"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        result = await service.toggle_favorite(user_id=user_id, recipe_id=recipe_id)

        return result

    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle favorite: {str(e)}")


@router.put(
    "/{recipe_id}/mark-cooked", response_model=Dict[str, Any], summary="Mark recipe as cooked"
)
async def mark_recipe_as_cooked(
    recipe_id: str,
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Mark a saved recipe as cooked (auto-promotion from saved to cooked status)"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        result = await service.mark_recipe_as_cooked(user_id=user_id, recipe_id=recipe_id)

        return result

    except Exception as e:
        logger.error(f"Error marking recipe as cooked: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark recipe as cooked: {str(e)}")


@router.delete("/{recipe_id}", response_model=Dict[str, Any], summary="Delete a saved recipe")
async def delete_user_recipe(
    recipe_id: int,
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Delete a recipe from user's collection"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        result = await service.delete_recipe(user_id=user_id, recipe_id=recipe_id)

        return result

    except Exception as e:
        logger.error(f"Error deleting recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")


@router.get("/{recipe_id}", response_model=Dict[str, Any], summary="Get a specific saved recipe")
async def get_user_recipe(
    recipe_id: int,
    service: UserRecipesService = Depends(get_user_recipes_service),
    # current_user = Depends(get_current_user)  # Uncomment when auth is enabled
):
    """Get a specific recipe from user's collection"""
    try:
        # For now, hardcode user_id to 111
        user_id = 111  # Replace with: current_user.user_id

        recipes = await service.get_user_recipes(user_id=user_id, limit=1, offset=0)

        # Find the specific recipe
        recipe = next((r for r in recipes if r["id"] == recipe_id), None)

        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")

        return recipe

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe: {str(e)}")
