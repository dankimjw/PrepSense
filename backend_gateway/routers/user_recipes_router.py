"""Router for user recipes management"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.services.user_recipes_service import UserRecipesService
from backend_gateway.services.bigquery_service import BigQueryService
from backend_gateway.core.security import get_current_user

logger = logging.getLogger(__name__)


class SaveRecipeRequest(BaseModel):
    """Request model for saving a recipe"""
    recipe_id: Optional[int] = Field(None, description="Spoonacular recipe ID if applicable")
    recipe_title: str = Field(..., description="Recipe title")
    recipe_image: Optional[str] = Field(None, description="Recipe image URL")
    recipe_data: Dict[str, Any] = Field(..., description="Complete recipe data")
    source: str = Field(..., description="Recipe source: 'spoonacular', 'generated', 'custom'")
    rating: str = Field("neutral", description="Initial rating: 'thumbs_up', 'thumbs_down', 'neutral'")


class UpdateRatingRequest(BaseModel):
    """Request model for updating recipe rating"""
    rating: str = Field(..., description="New rating: 'thumbs_up', 'thumbs_down', 'neutral'")


router = APIRouter(
    prefix="/user-recipes",
    tags=["User Recipes"],
    responses={404: {"description": "Not found"}},
)


def get_user_recipes_service(bq_service: BigQueryService = Depends(lambda: BigQueryService())) -> UserRecipesService:
    return UserRecipesService(bq_service=bq_service)


@router.post("", summary="Save a recipe to user's collection")
async def save_recipe(
    request: SaveRecipeRequest,
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Save a recipe to the user's personal collection
    
    This endpoint allows users to save recipes from various sources:
    - Spoonacular recipes (from search or recommendations)
    - AI-generated recipes (from chat)
    - Custom recipes (user-created)
    """
    try:
        # Extract user_id from current user
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        # Check if recipe already exists (if it has a recipe_id)
        if request.recipe_id:
            existing = await service.check_recipe_exists(user_id, request.recipe_id)
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Recipe already saved with rating: {existing['rating']}"
                )
        
        result = await service.save_recipe(
            user_id=user_id,
            recipe_id=request.recipe_id,
            recipe_title=request.recipe_title,
            recipe_image=request.recipe_image,
            recipe_data=request.recipe_data,
            source=request.source,
            rating=request.rating
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


@router.get("", summary="Get user's saved recipes")
async def get_user_recipes(
    rating_filter: Optional[str] = Query(None, description="Filter by rating: 'thumbs_up' or 'thumbs_down'"),
    limit: int = Query(50, ge=1, le=100, description="Number of recipes to return"),
    offset: int = Query(0, ge=0, description="Number of recipes to skip"),
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Get all recipes saved by the user
    
    Optionally filter by rating (thumbs up/down)
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        recipes = await service.get_user_recipes(
            user_id=user_id,
            rating_filter=rating_filter,
            limit=limit,
            offset=offset
        )
        
        return {
            "recipes": recipes,
            "total": len(recipes),
            "filter": rating_filter,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching user recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recipes: {str(e)}")


@router.put("/{recipe_id}/rating", summary="Update recipe rating")
async def update_recipe_rating(
    recipe_id: str,
    request: UpdateRatingRequest,
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Update the rating of a saved recipe
    
    Ratings:
    - thumbs_up: User likes this recipe
    - thumbs_down: User dislikes this recipe
    - neutral: No rating
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        result = await service.update_recipe_rating(
            user_id=user_id,
            recipe_id=recipe_id,
            rating=request.rating
        )
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recipe rating: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update rating: {str(e)}")


@router.delete("/{recipe_id}", summary="Delete a saved recipe")
async def delete_recipe(
    recipe_id: str,
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Remove a recipe from user's collection
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        result = await service.delete_user_recipe(
            user_id=user_id,
            recipe_id=recipe_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")


@router.get("/check/{spoonacular_recipe_id}", summary="Check if recipe is saved")
async def check_recipe_saved(
    spoonacular_recipe_id: int,
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Check if a Spoonacular recipe is already saved by the user
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        existing = await service.check_recipe_exists(user_id, spoonacular_recipe_id)
        
        return {
            "is_saved": existing is not None,
            "recipe_id": existing["id"] if existing else None,
            "rating": existing["rating"] if existing else None,
            "is_favorite": existing["is_favorite"] if existing else None
        }
        
    except Exception as e:
        logger.error(f"Error checking recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check recipe: {str(e)}")


@router.post("/{recipe_id}/cooked", summary="Mark recipe as cooked")
async def mark_recipe_cooked(
    recipe_id: str,
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Increment the times_cooked counter for a recipe
    
    This endpoint is called when a user cooks a saved recipe
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        result = await service.increment_times_cooked(user_id, recipe_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recipe as cooked: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")


@router.get("/stats", summary="Get user recipe statistics")
async def get_recipe_stats(
    current_user: Dict = Depends(get_current_user),
    service: UserRecipesService = Depends(get_user_recipes_service)
) -> Dict[str, Any]:
    """
    Get statistics about user's saved recipes
    
    Returns:
    - Total recipes saved
    - Number of liked/disliked recipes
    - Total times cooked
    - Unique cuisines explored
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        stats = await service.get_user_recipe_stats(user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting recipe stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")