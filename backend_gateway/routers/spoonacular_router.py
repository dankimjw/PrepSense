"""Router for Spoonacular recipe endpoints"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.recipe_image_service import RecipeImageService
from backend_gateway.services.recipe_cache_service import RecipeCacheService
from backend_gateway.utils.instruction_parser import improve_recipe_instructions
from backend_gateway.config.database import get_pantry_service as get_pantry_service_dep, get_database_service

logger = logging.getLogger(__name__)

# Request/Response models
class RecipeSearchByIngredientsRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of ingredients to search with")
    number: int = Field(10, ge=1, le=100, description="Number of recipes to return")
    ranking: int = Field(1, ge=0, le=1, description="0 = maximize used ingredients, 1 = minimize missing ingredients")
    ignore_pantry: bool = Field(False, description="Whether to ignore typical pantry items")
    intolerances: Optional[List[str]] = Field(None, description="List of allergens/intolerances to exclude (e.g., dairy, gluten, peanut)")


class RecipeSearchComplexRequest(BaseModel):
    query: Optional[str] = Field(None, description="Natural language search query")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    diet: Optional[str] = Field(None, description="Diet type")
    include_ingredients: Optional[List[str]] = Field(None, description="Ingredients that must be included")
    exclude_ingredients: Optional[List[str]] = Field(None, description="Ingredients to exclude")
    intolerances: Optional[List[str]] = Field(None, description="List of allergens/intolerances to exclude (e.g., dairy, gluten, peanut)")
    max_ready_time: Optional[int] = Field(None, description="Maximum ready time in minutes")
    sort: Optional[str] = Field(None, description="Sort by (popularity, time, etc.)")
    number: int = Field(10, ge=1, le=100, description="Number of results")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class RecipeFromPantryRequest(BaseModel):
    user_id: int = Field(..., description="User ID to get pantry items from")
    max_missing_ingredients: int = Field(5, description="Maximum number of missing ingredients allowed")
    use_expiring_first: bool = Field(True, description="Prioritize items expiring soon")
    intolerances: Optional[List[str]] = Field(None, description="List of allergens/intolerances to exclude (e.g., dairy, gluten, peanut)")


router = APIRouter(
    prefix="/recipes",
    tags=["Spoonacular Recipes"],
    responses={404: {"description": "Not found"}},
)


# Dependencies
def get_spoonacular_service() -> SpoonacularService:
    return SpoonacularService()

def get_recipe_image_service() -> RecipeImageService:
    return RecipeImageService()


def get_pantry_service() -> PantryService:
    return get_pantry_service_dep()  # Use the same dep as pantry_router

def get_cache_service() -> RecipeCacheService:
    return RecipeCacheService()


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
            ignore_pantry=request.ignore_pantry,
            intolerances=request.intolerances
        )
        
        # Filter out recipes with insufficient instructions
        original_count = len(recipes)
        recipes = spoonacular_service.filter_recipes_by_instructions(recipes, min_steps=2)
        filtered_count = original_count - len(recipes)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} recipes with insufficient instructions")
        
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
            intolerances=request.intolerances,
            max_ready_time=request.max_ready_time,
            sort=request.sort,
            number=request.number,
            offset=request.offset
        )
        
        # Filter out recipes with insufficient instructions
        if 'results' in results:
            original_count = len(results['results'])
            results['results'] = spoonacular_service.filter_recipes_by_instructions(
                results['results'], 
                min_steps=2
            )
            filtered_count = original_count - len(results['results'])
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} recipes with insufficient instructions")
        
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
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
    recipe_image_service: RecipeImageService = Depends(get_recipe_image_service),
    db_service = Depends(get_database_service)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific recipe.
    This endpoint also checks for stored recipe images in GCS and generates new ones using OpenAI if needed.
    """
    try:
        # First, try to get recipe from Spoonacular
        recipe = None
        try:
            recipe = await spoonacular_service.get_recipe_information(
                recipe_id=recipe_id,
                include_nutrition=include_nutrition
            )
        except Exception as spoon_error:
            logger.warning(f"Spoonacular API failed for recipe {recipe_id}: {str(spoon_error)}")
            
            # Fallback: Check if we have this recipe saved locally
            try:
                saved_recipe_query = """
                    SELECT recipe_data
                    FROM user_recipes
                    WHERE (recipe_id = %(recipe_id)s OR recipe_data->>'id' = %(recipe_id_str)s OR recipe_data->>'external_recipe_id' = %(recipe_id_str)s)
                    AND recipe_data IS NOT NULL
                    AND recipe_data != '{}'::jsonb
                    LIMIT 1
                """
                
                result = db_service.execute_query(saved_recipe_query, {
                    "recipe_id": recipe_id,
                    "recipe_id_str": str(recipe_id)
                })
                
                if result and result[0].get('recipe_data'):
                    logger.info(f"Using locally saved recipe data for {recipe_id}")
                    recipe = result[0]['recipe_data']
                else:
                    # If no local data, re-raise the original error
                    raise spoon_error
            except Exception as db_error:
                logger.error(f"Database fallback also failed: {str(db_error)}")
                raise spoon_error
        
        # Check if we have a stored image or generate a new one
        try:
            # Extract recipe details for image generation
            recipe_title = recipe.get('title', '')
            ingredients = []
            
            # Extract ingredient names from the recipe
            if 'extendedIngredients' in recipe:
                ingredients = [ing.get('name', '') for ing in recipe['extendedIngredients'] if ing.get('name')]
            
            # Get cuisine type if available
            cuisine = None
            if 'cuisines' in recipe and recipe['cuisines']:
                cuisine = recipe['cuisines'][0]
            
            # Generate or retrieve image from GCS
            stored_image_url = await recipe_image_service.generate_and_store_recipe_image(
                recipe_id=str(recipe_id),
                recipe_title=recipe_title,
                ingredients=ingredients[:5],  # Use top 5 ingredients
                cuisine=cuisine,
                force_regenerate=False
            )
            
            # Replace Spoonacular image with our stored/generated image
            if stored_image_url:
                recipe['image'] = stored_image_url
                logger.info(f"Using stored/generated image for recipe {recipe_id}: {stored_image_url}")
            else:
                logger.warning(f"Could not generate/retrieve image for recipe {recipe_id}, using Spoonacular image")
                
        except Exception as img_error:
            logger.error(f"Error handling recipe image for ID {recipe_id}: {str(img_error)}")
            # Continue with Spoonacular image if image generation fails
        
        # Improve recipe instructions parsing
        if recipe and 'analyzedInstructions' in recipe:
            try:
                recipe['analyzedInstructions'] = improve_recipe_instructions(recipe['analyzedInstructions'])
                logger.info(f"Improved instructions for recipe {recipe_id}")
            except Exception as inst_error:
                logger.warning(f"Failed to improve instructions for recipe {recipe_id}: {str(inst_error)}")
        
        return recipe
    except ValueError as e:
        logger.error(f"ValueError getting recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting recipe information for ID {recipe_id}: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get recipe information")


@router.get("/random", summary="Get random recipes")
async def get_random_recipes(
    number: int = Query(10, ge=1, le=100, description="Number of random recipes"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
    cache_service: RecipeCacheService = Depends(get_cache_service)
) -> Dict[str, Any]:
    """
    Get random recipes, optionally filtered by tags with caching for performance
    """
    try:
        # Create cache key for random recipes
        tag_str = tags or "no_tags"
        cache_key = f"random_recipes_{number}_{tag_str}"
        
        # Try to get from cache first (cache for 30 minutes)
        cached_recipes = await cache_service.get_recipe_data(cache_key)
        if cached_recipes:
            logger.info(f"Returning cached random recipes for key: {cache_key}")
            return cached_recipes
        
        # Fetch from Spoonacular API
        tag_list = tags.split(",") if tags else None
        recipes = await spoonacular_service.get_random_recipes(
            number=number,
            tags=tag_list
        )
        
        # Cache the results for 30 minutes
        await cache_service.cache_recipe_data(cache_key, recipes, ttl_minutes=30)
        
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
    pantry_service: PantryService = Depends(get_pantry_service),
    db_service = Depends(get_database_service)
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
        
        # Extract and aggregate ingredients with quantities
        from collections import defaultdict
        ingredient_quantities = defaultdict(float)  # ingredient_name -> total_quantity
        ingredient_units = {}  # ingredient_name -> unit
        ingredient_items = defaultdict(list)  # ingredient_name -> list of pantry items
        expiring_soon = []
        
        logger.info(f"Processing {len(pantry_items)} pantry items")
        
        for item in pantry_items:
            ingredient_name = item.get('product_name') or item.get('food_category')
            if ingredient_name:
                # Normalize ingredient name (lowercase, strip)
                normalized_name = ingredient_name.lower().strip()
                
                # Aggregate quantities - convert Decimal to float
                quantity = float(item.get('quantity', 0))
                ingredient_quantities[normalized_name] += quantity
                
                # Store unit (assuming same ingredient has same unit)
                if normalized_name not in ingredient_units:
                    ingredient_units[normalized_name] = item.get('unit_of_measurement', 'unit')
                
                # Store the item reference for later use
                ingredient_items[normalized_name].append(item)
                
                # Check if expiring soon (within 3 days)
                if item.get('expiration_date'):
                    from datetime import datetime, timedelta
                    expiry = datetime.fromisoformat(str(item['expiration_date']))
                    if expiry <= datetime.now() + timedelta(days=3):
                        if normalized_name not in expiring_soon:
                            expiring_soon.append(normalized_name)
        
        # Get unique ingredient names
        ingredients = list(ingredient_quantities.keys())
        logger.info(f"Found {len(ingredients)} unique ingredients from pantry")
        
        if not ingredients:
            return {
                "recipes": [],
                "message": "No valid ingredients found in pantry",
                "total_pantry_items": 0
            }
        
        # Prioritize expiring items if requested
        if request.use_expiring_first and expiring_soon:
            # Search with expiring items first
            search_ingredients = expiring_soon[:5]  # Limit to 5 ingredients to avoid timeouts
        else:
            # For better results, prioritize ingredients by quantity (more quantity = more to use)
            sorted_ingredients = sorted(
                ingredients, 
                key=lambda x: ingredient_quantities.get(x, 0), 
                reverse=True
            )
            search_ingredients = sorted_ingredients[:5]  # Limit to 5 ingredients to avoid timeouts
        
        # Clean ingredient names (remove brand names, keep only food item)
        cleaned_ingredients = []
        for ingredient in search_ingredients:
            # Simple cleaning: take last part after brand names
            parts = ingredient.split()
            if len(parts) > 2:
                # Likely has brand name, take last 1-2 words
                cleaned = ' '.join(parts[-2:]) if len(parts) > 3 else ' '.join(parts[-1:])
            else:
                cleaned = ingredient
            cleaned_ingredients.append(cleaned)
        
        logger.info(f"Searching recipes with {len(cleaned_ingredients)} ingredients: {cleaned_ingredients}")
        
        # Get user allergens from database if not provided
        intolerances = request.intolerances
        if intolerances is None:
            try:
                allergen_query = """
                SELECT allergen FROM user_allergens 
                WHERE user_id = %(user_id)s
                """
                allergen_results = db_service.execute_query(allergen_query, {"user_id": request.user_id})
                intolerances = [row['allergen'] for row in allergen_results]
                if intolerances:
                    logger.info(f"Found user allergens: {intolerances}")
            except Exception as e:
                logger.warning(f"Could not fetch user allergens: {e}")
                intolerances = []
        
        # Search for recipes without allergen filtering to allow matching ingredients
        # We'll filter allergens later only if no pantry ingredients match
        recipes = await spoonacular_service.search_recipes_by_ingredients(
            ingredients=cleaned_ingredients,  # Use cleaned ingredients without brand names
            number=30,  # Get more recipes to filter after allergen consideration
            ranking=1,  # Minimize missing ingredients
            ignore_pantry=True,
            intolerances=[]  # Don't filter allergens at Spoonacular level
        )
        
        # Filter to only show recipes with at least 1 matching ingredient (usedIngredientCount >= 1)
        # This ensures we only show recipes that actually use pantry ingredients
        filtered_recipes = [
            recipe for recipe in recipes
            if recipe.get('usedIngredientCount', 0) >= 1
        ]
        
        # Smart allergen filtering: since all recipes now have >= 1 matching ingredient,
        # include them even if they contain allergens (user can decide)
        if intolerances:
            # All recipes in filtered_recipes already have matching ingredients,
            # so we include them all and let users make allergen decisions
            pass  # Keep all recipes - they all have pantry ingredient matches
        
        # Sort by most used ingredients first, then by fewest missing
        filtered_recipes.sort(key=lambda x: (-x.get('usedIngredientCount', 0), x.get('missedIngredientCount', 999)))
        
        # Limit to reasonable number for display
        filtered_recipes = filtered_recipes[:20]
        
        # Add pantry quantities to response for frontend use
        pantry_ingredients = [
            {
                "name": name,
                "quantity": ingredient_quantities[name],
                "unit": ingredient_units[name],
                "items": ingredient_items[name]  # Include item details for consumption tracking
            }
            for name in ingredients
        ]
        
        return {
            "recipes": filtered_recipes,
            "total_pantry_items": len(ingredients),
            "pantry_ingredients": pantry_ingredients,
            "ingredient_quantities": dict(ingredient_quantities),
            "ingredient_units": dict(ingredient_units),
            "expiring_items": expiring_soon,
            "searched_with": cleaned_ingredients,
            "original_ingredients": search_ingredients
        }
        
    except ValueError as e:
        logger.error(f"ValueError in search recipes from pantry: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching recipes from pantry: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to search recipes from pantry")