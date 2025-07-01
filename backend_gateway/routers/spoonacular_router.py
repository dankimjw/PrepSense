"""Router for Spoonacular recipe endpoints"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.bigquery_service import BigQueryService

logger = logging.getLogger(__name__)

# Request/Response models
class RecipeSearchByIngredientsRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of ingredients to search with")
    number: int = Field(10, ge=1, le=100, description="Number of recipes to return")
    ranking: int = Field(1, ge=0, le=1, description="0 = maximize used ingredients, 1 = minimize missing ingredients")
    ignore_pantry: bool = Field(False, description="Whether to ignore typical pantry items")


class RecipeSearchComplexRequest(BaseModel):
    query: Optional[str] = Field(None, description="Natural language search query")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    diet: Optional[str] = Field(None, description="Diet type")
    include_ingredients: Optional[List[str]] = Field(None, description="Ingredients that must be included")
    exclude_ingredients: Optional[List[str]] = Field(None, description="Ingredients to exclude")
    max_ready_time: Optional[int] = Field(None, description="Maximum ready time in minutes")
    sort: Optional[str] = Field(None, description="Sort by (popularity, time, etc.)")
    number: int = Field(10, ge=1, le=100, description="Number of results")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class RecipeFromPantryRequest(BaseModel):
    user_id: int = Field(..., description="User ID to get pantry items from")
    max_missing_ingredients: int = Field(5, description="Maximum number of missing ingredients allowed")
    use_expiring_first: bool = Field(True, description="Prioritize items expiring soon")


router = APIRouter(
    prefix="/recipes",
    tags=["Spoonacular Recipes"],
    responses={404: {"description": "Not found"}},
)


# Dependencies
def get_spoonacular_service() -> SpoonacularService:
    return SpoonacularService()


def get_bigquery_service() -> BigQueryService:
    return BigQueryService()


def get_pantry_service(bq_service: BigQueryService = Depends(get_bigquery_service)) -> PantryService:
    return PantryService(bq_service=bq_service)


@router.post("/search/by-ingredients", summary="Search recipes by ingredients")
async def search_recipes_by_ingredients(
    request: RecipeSearchByIngredientsRequest,
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> List[Dict[str, Any]]:
    """
    Search for recipes based on a list of ingredients
    """
    try:
        recipes = await spoonacular_service.search_recipes_by_ingredients(
            ingredients=request.ingredients,
            number=request.number,
            ranking=request.ranking,
            ignore_pantry=request.ignore_pantry
        )
        return recipes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching recipes by ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search recipes")


@router.post("/search/complex", summary="Complex recipe search")
async def search_recipes_complex(
    request: RecipeSearchComplexRequest,
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> Dict[str, Any]:
    """
    Complex recipe search with multiple filters
    """
    try:
        results = await spoonacular_service.search_recipes_complex(
            query=request.query,
            cuisine=request.cuisine,
            diet=request.diet,
            include_ingredients=request.include_ingredients,
            exclude_ingredients=request.exclude_ingredients,
            max_ready_time=request.max_ready_time,
            sort=request.sort,
            number=request.number,
            offset=request.offset
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in complex recipe search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search recipes")


@router.get("/recipe/{recipe_id}", summary="Get recipe information")
async def get_recipe_information(
    recipe_id: int,
    include_nutrition: bool = Query(True, description="Include nutrition information"),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific recipe
    """
    try:
        recipe = await spoonacular_service.get_recipe_information(
            recipe_id=recipe_id,
            include_nutrition=include_nutrition
        )
        return recipe
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting recipe information: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recipe information")


@router.get("/random", summary="Get random recipes")
async def get_random_recipes(
    number: int = Query(10, ge=1, le=100, description="Number of random recipes"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> Dict[str, Any]:
    """
    Get random recipes, optionally filtered by tags
    """
    try:
        tag_list = tags.split(",") if tags else None
        recipes = await spoonacular_service.get_random_recipes(
            number=number,
            tags=tag_list
        )
        return recipes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting random recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get random recipes")


@router.post("/search/from-pantry", summary="Find recipes using pantry items")
async def search_recipes_from_pantry(
    request: RecipeFromPantryRequest,
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
    pantry_service: PantryService = Depends(get_pantry_service)
) -> Dict[str, Any]:
    """
    Find recipes based on user's pantry items, prioritizing expiring items
    """
    try:
        # Get user's pantry items
        pantry_items = await pantry_service.get_user_pantry_items(request.user_id)
        
        if not pantry_items:
            return {
                "recipes": [],
                "message": "No items found in pantry"
            }
        
        # Extract ingredient names
        ingredients = []
        expiring_soon = []
        
        for item in pantry_items:
            ingredient_name = item.product_name or item.food_category
            if ingredient_name:
                ingredients.append(ingredient_name)
                
                # Check if expiring soon (within 3 days)
                if item.expiration_date:
                    from datetime import datetime, timedelta
                    expiry = datetime.fromisoformat(str(item.expiration_date))
                    if expiry <= datetime.now() + timedelta(days=3):
                        expiring_soon.append(ingredient_name)
        
        # Prioritize expiring items if requested
        if request.use_expiring_first and expiring_soon:
            # Search with expiring items first
            search_ingredients = expiring_soon[:10]  # Limit to 10 ingredients
        else:
            search_ingredients = ingredients[:20]  # Limit to 20 ingredients
        
        # Search for recipes
        recipes = await spoonacular_service.search_recipes_by_ingredients(
            ingredients=search_ingredients,
            number=20,
            ranking=1,  # Minimize missing ingredients
            ignore_pantry=True
        )
        
        # Filter by max missing ingredients
        filtered_recipes = [
            recipe for recipe in recipes
            if recipe.get('missedIngredientCount', 0) <= request.max_missing_ingredients
        ]
        
        return {
            "recipes": filtered_recipes,
            "total_pantry_items": len(ingredients),
            "expiring_items": expiring_soon,
            "searched_with": search_ingredients
        }
        
    except Exception as e:
        logger.error(f"Error searching recipes from pantry: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search recipes from pantry")