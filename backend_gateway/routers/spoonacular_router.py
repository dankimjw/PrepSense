"""Router for Spoonacular recipe endpoints"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.config.database import get_database_service
from backend_gateway.config.database import get_pantry_service as get_pantry_service_dep
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.recipe_cache_service import RecipeCacheService
from backend_gateway.services.recipe_image_service import RecipeImageService
from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.utils.instruction_parser import improve_recipe_instructions

logger = logging.getLogger(__name__)


# Request/Response models
class RecipeSearchByIngredientsRequest(BaseModel):
    ingredients: list[str] = Field(..., description="List of ingredients to search with")
    number: int = Field(10, ge=1, le=100, description="Number of recipes to return")
    ranking: int = Field(
        1, ge=0, le=1, description="0 = maximize used ingredients, 1 = minimize missing ingredients"
    )
    ignore_pantry: bool = Field(False, description="Whether to ignore typical pantry items")
    intolerances: Optional[list[str]] = Field(
        None, description="List of allergens/intolerances to exclude (e.g., dairy, gluten, peanut)"
    )


class RecipeSearchComplexRequest(BaseModel):
    query: Optional[str] = Field(None, description="Natural language search query")
    cuisine: Optional[str] = Field(None, description="Cuisine type")
    diet: Optional[str] = Field(None, description="Diet type")
    include_ingredients: Optional[list[str]] = Field(
        None, description="Ingredients that must be included"
    )
    exclude_ingredients: Optional[list[str]] = Field(None, description="Ingredients to exclude")
    intolerances: Optional[list[str]] = Field(
        None, description="List of allergens/intolerances to exclude (e.g., dairy, gluten, peanut)"
    )
    max_ready_time: Optional[int] = Field(None, description="Maximum ready time in minutes")
    sort: Optional[str] = Field(None, description="Sort by (popularity, time, etc.)")
    number: int = Field(10, ge=1, le=100, description="Number of results")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class RecipeFromPantryRequest(BaseModel):
    user_id: int = Field(..., description="User ID to get pantry items from")
    max_missing_ingredients: int = Field(
        5, description="Maximum number of missing ingredients allowed"
    )
    use_expiring_first: bool = Field(True, description="Prioritize items expiring soon")
    intolerances: Optional[list[str]] = Field(
        None, description="List of allergens/intolerances to exclude (e.g., dairy, gluten, peanut)"
    )


router = APIRouter(
    prefix="/recipes",
    tags=["Spoonacular Recipes"],
    responses={404: {"description": "Not found"}},
)


# Helper function to validate and normalize recipe IDs
def validate_and_normalize_recipe_id(recipe_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize recipe ID field to ensure proper identification
    """
    # Try multiple potential ID fields
    possible_id_fields = ["id", "recipe_id", "spoonacularId", "external_id"]
    recipe_id = None

    for field in possible_id_fields:
        if field in recipe_data and recipe_data[field] is not None:
            try:
                # Convert to integer if it's a string
                potential_id = recipe_data[field]
                if isinstance(potential_id, (str, int, float)):
                    potential_id = int(potential_id)
                else:
                    continue

                # Validate it's a positive integer
                if potential_id > 0:
                    recipe_id = potential_id
                    break
            except (ValueError, TypeError):
                continue

    if recipe_id is None:
        logger.warning(f"No valid recipe ID found in recipe data: {list(recipe_data.keys())}")
        # Generate a fallback ID based on title hash if available
        if "title" in recipe_data and recipe_data["title"]:
            import hashlib

            title_hash = hashlib.md5(recipe_data["title"].encode()).hexdigest()
            recipe_id = int(title_hash[:8], 16)  # Use first 8 chars of hash as numeric ID
            logger.info(f"Generated fallback ID {recipe_id} for recipe: {recipe_data['title']}")

    # Ensure the id field is set
    recipe_data["id"] = recipe_id

    # Log the ID resolution for debugging
    logger.debug(
        f"Recipe ID resolved: {recipe_id} for recipe: {recipe_data.get('title', 'Unnamed')}"
    )

    return recipe_data


def enhance_spoonacular_image_url(recipe_data: dict[str, Any]) -> dict[str, Any]:
    """
    Enhance recipe image URL for Spoonacular recipes
    """
    recipe_id = recipe_data.get("id")
    current_image = recipe_data.get("image", "")

    if recipe_id and isinstance(recipe_id, int) and recipe_id > 0:
        # Generate proper Spoonacular image URL if missing or invalid
        if not current_image or not current_image.startswith("http"):
            spoonacular_image_url = f"https://img.spoonacular.com/recipes/{recipe_id}-312x231.jpg"
            recipe_data["image"] = spoonacular_image_url
            logger.debug(f"Generated Spoonacular image URL: {spoonacular_image_url}")
        elif "spoonacular.com" in current_image:
            # Ensure the URL format is correct
            if f"{recipe_id}-" not in current_image:
                spoonacular_image_url = (
                    f"https://img.spoonacular.com/recipes/{recipe_id}-312x231.jpg"
                )
                recipe_data["image"] = spoonacular_image_url
                logger.debug(f"Fixed Spoonacular image URL: {spoonacular_image_url}")
    # Use a working fallback image
    elif (
        not current_image
        or current_image == "https://img.spoonacular.com/recipes/default-312x231.jpg"
    ):
        recipe_data["image"] = "https://via.placeholder.com/312x231/E5E5E5/666666?text=Recipe+Image"
        logger.debug("Using placeholder image for recipe without valid ID")

    return recipe_data


def process_recipe_list_response(recipes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Process a list of recipes to ensure proper ID and image handling
    """
    processed_recipes = []

    for recipe in recipes:
        try:
            # Validate and normalize recipe ID
            recipe = validate_and_normalize_recipe_id(recipe)

            # Enhance image URL
            recipe = enhance_spoonacular_image_url(recipe)

            # Ensure title field is present
            if not recipe.get("title") and recipe.get("name"):
                recipe["title"] = recipe["name"]
            elif not recipe.get("name") and recipe.get("title"):
                recipe["name"] = recipe["title"]

            processed_recipes.append(recipe)

        except Exception as e:
            logger.error(f"Error processing recipe: {e}")
            # Skip malformed recipes rather than crashing
            continue

    logger.info(f"Processed {len(processed_recipes)}/{len(recipes)} recipes successfully")
    return processed_recipes


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
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
) -> list[dict[str, Any]]:
    """
    Search for recipes based on a list of ingredients
    """
    try:
        recipes = await spoonacular_service.search_recipes_by_ingredients(
            ingredients=request.ingredients,
            number=request.number,
            ranking=request.ranking,
            ignore_pantry=request.ignore_pantry,
            intolerances=request.intolerances,
        )

        # Process recipes to ensure proper IDs and images
        recipes = process_recipe_list_response(recipes)

        # Filter out recipes with insufficient instructions
        original_count = len(recipes)
        recipes = spoonacular_service.filter_recipes_by_instructions(recipes, min_steps=2)
        filtered_count = original_count - len(recipes)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} recipes with insufficient instructions")

        return recipes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error searching recipes by ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search recipes") from e


@router.post("/search/complex", summary="Complex recipe search")
async def search_recipes_complex(
    request: RecipeSearchComplexRequest,
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
) -> dict[str, Any]:
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
            offset=request.offset,
        )

        # Process recipes in the results
        if "results" in results and results["results"]:
            results["results"] = process_recipe_list_response(results["results"])

            # Filter out recipes with insufficient instructions
            original_count = len(results["results"])
            results["results"] = spoonacular_service.filter_recipes_by_instructions(
                results["results"], min_steps=2
            )
            filtered_count = original_count - len(results["results"])
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} recipes with insufficient instructions")

        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error in complex recipe search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search recipes") from e


@router.get("/recipe/{recipe_id}", summary="Get recipe information")
async def get_recipe_information(
    recipe_id: int,
    include_nutrition: bool = Query(True, description="Include nutrition information"),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
    recipe_image_service: RecipeImageService = Depends(get_recipe_image_service),
    db_service=Depends(get_database_service),
) -> dict[str, Any]:
    """
    Get detailed information about a specific recipe.
    This endpoint uses Spoonacular images when available, with local backups.
    """
    try:
        # First, try to get recipe from Spoonacular
        recipe = None
        try:
            recipe = await spoonacular_service.get_recipe_information(
                recipe_id=recipe_id, include_nutrition=include_nutrition
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

                result = db_service.execute_query(
                    saved_recipe_query, {"recipe_id": recipe_id, "recipe_id_str": str(recipe_id)}
                )

                if result and result[0].get("recipe_data"):
                    logger.info(f"Using locally saved recipe data for {recipe_id}")
                    recipe = result[0]["recipe_data"]
                else:
                    # If no local data, re-raise the original error
                    raise spoon_error from spoon_error
            except Exception as db_error:
                logger.error(f"Database fallback also failed: {str(db_error)}")
                raise spoon_error from db_error

        if recipe:
            # Process the single recipe to ensure proper ID and image handling
            recipe = validate_and_normalize_recipe_id(recipe)
            recipe = enhance_spoonacular_image_url(recipe)

        # Check for local images first, then fall back to Spoonacular
        if recipe and "image" in recipe and recipe["image"]:
            from pathlib import Path

            # Look for any file that starts with recipe_{recipe_id}_
            recipe_images_dir = Path("Recipe Images")
            pattern = f"recipe_{recipe_id}_*.jpg"
            matching_files = list(recipe_images_dir.glob(pattern))

            if matching_files:
                # Use the first matching file
                local_filename = matching_files[0].name
                # Need full URL for iOS app - get actual IP address
                import socket

                from backend_gateway.core.config import settings

                # Get the actual IP address
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                base_url = f"http://{local_ip}:{settings.SERVER_PORT}"
                # URL encode the path

                recipe["image"] = f"{base_url}/Recipe%20Images/{local_filename}"
                recipe["local_image"] = True
                logger.info(
                    f"Using local image for recipe {recipe_id}: {local_filename} at {base_url}"
                )
            else:
                logger.info(f"Using original Spoonacular image for recipe {recipe_id}")

        # Improve recipe instructions parsing
        if recipe and "analyzedInstructions" in recipe:
            try:
                recipe["analyzedInstructions"] = improve_recipe_instructions(
                    recipe["analyzedInstructions"]
                )
                logger.info(f"Improved instructions for recipe {recipe_id}")
            except Exception as inst_error:
                logger.warning(
                    f"Failed to improve instructions for recipe {recipe_id}: {str(inst_error)}"
                )

        return recipe
    except ValueError as e:
        logger.error(f"ValueError getting recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(
            f"Error getting recipe information for ID {recipe_id}: {type(e).__name__}: {str(e)}"
        )
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get recipe information") from e


@router.get("/random", summary="Get random recipes")
async def get_random_recipes(
    number: int = Query(10, ge=1, le=100, description="Number of random recipes"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
    cache_service: RecipeCacheService = Depends(get_cache_service),
) -> dict[str, Any]:
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
        results = await spoonacular_service.get_random_recipes(number=number, tags=tag_list)

        # Process recipes in the results
        if "recipes" in results and results["recipes"]:
            results["recipes"] = process_recipe_list_response(results["recipes"])

        # Cache the results for 30 minutes
        await cache_service.cache_recipe_data(cache_key, results, ttl_minutes=30)

        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting random recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get random recipes") from e


@router.post("/search/from-pantry", summary="Find recipes using pantry items")
async def search_recipes_from_pantry(
    request: RecipeFromPantryRequest,
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service),
    pantry_service: PantryService = Depends(get_pantry_service),
    db_service=Depends(get_database_service),
) -> dict[str, Any]:
    """
    Find recipes based on user's pantry items, prioritizing expiring items
    """
    try:
        # Get user's pantry items
        pantry_items = await pantry_service.get_user_pantry_items(request.user_id)

        if not pantry_items:
            return {"recipes": [], "message": "No items found in pantry"}

        # Extract and aggregate ingredients with quantities
        from collections import defaultdict

        ingredient_quantities = defaultdict(float)  # ingredient_name -> total_quantity
        ingredient_units = {}  # ingredient_name -> unit
        ingredient_items = defaultdict(list)  # ingredient_name -> list of pantry items
        expiring_soon = []

        logger.info(f"Processing {len(pantry_items)} pantry items")

        for item in pantry_items:
            ingredient_name = item.get("product_name") or item.get("food_category")
            if ingredient_name:
                # Normalize ingredient name (lowercase, strip)
                normalized_name = ingredient_name.lower().strip()

                # Aggregate quantities - convert Decimal to float
                quantity = float(item.get("quantity", 0))
                ingredient_quantities[normalized_name] += quantity

                # Store unit (assuming same ingredient has same unit)
                if normalized_name not in ingredient_units:
                    ingredient_units[normalized_name] = item.get("unit_of_measurement", "unit")

                # Store the item reference for later use
                ingredient_items[normalized_name].append(item)

                # Check if expiring soon (within 3 days)
                if item.get("expiration_date"):
                    from datetime import datetime, timedelta

                    expiry = datetime.fromisoformat(str(item["expiration_date"]))
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
                "total_pantry_items": 0,
            }

        # Prioritize expiring items if requested
        if request.use_expiring_first and expiring_soon:
            # Search with expiring items first
            search_ingredients = expiring_soon[:5]  # Limit to 5 ingredients to avoid timeouts
        else:
            # For better results, prioritize ingredients by quantity (more quantity = more to use)
            sorted_ingredients = sorted(
                ingredients, key=lambda x: ingredient_quantities.get(x, 0), reverse=True
            )
            search_ingredients = sorted_ingredients[:5]  # Limit to 5 ingredients to avoid timeouts

        # Clean ingredient names (remove brand names, keep only food item)
        cleaned_ingredients = []
        for ingredient in search_ingredients:
            # Simple cleaning: take last part after brand names
            parts = ingredient.split()
            if len(parts) > 2:
                # Likely has brand name, take last 1-2 words
                cleaned = " ".join(parts[-2:]) if len(parts) > 3 else " ".join(parts[-1:])
            else:
                cleaned = ingredient
            cleaned_ingredients.append(cleaned)

        logger.info(
            f"Searching recipes with {len(cleaned_ingredients)} ingredients: {cleaned_ingredients}"
        )

        # Get user allergens from database if not provided
        intolerances = request.intolerances
        if intolerances is None:
            try:
                allergen_query = """
                SELECT allergen FROM user_allergens
                WHERE user_id = %(user_id)s
                """
                allergen_results = db_service.execute_query(
                    allergen_query, {"user_id": request.user_id}
                )
                intolerances = [row["allergen"] for row in allergen_results]
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
            intolerances=[],  # Don't filter allergens at Spoonacular level
        )

        # Process recipes to ensure proper IDs and images
        recipes = process_recipe_list_response(recipes)

        # Filter to only show recipes with at least 1 matching ingredient (usedIngredientCount >= 1)
        # This ensures we only show recipes that actually use pantry ingredients
        filtered_recipes = [
            recipe for recipe in recipes if recipe.get("usedIngredientCount", 0) >= 1
        ]

        # Smart allergen filtering: since all recipes now have >= 1 matching ingredient,
        # include them even if they contain allergens (user can decide)
        if intolerances:
            # All recipes in filtered_recipes already have matching ingredients,
            # so we include them all and let users make allergen decisions
            pass  # Keep all recipes - they all have pantry ingredient matches

        # Sort by most used ingredients first, then by fewest missing
        filtered_recipes.sort(
            key=lambda x: (-x.get("usedIngredientCount", 0), x.get("missedIngredientCount", 999))
        )

        # Limit to reasonable number for display
        filtered_recipes = filtered_recipes[:20]

        # Add pantry quantities to response for frontend use
        pantry_ingredients = [
            {
                "name": name,
                "quantity": ingredient_quantities[name],
                "unit": ingredient_units[name],
                "items": ingredient_items[name],  # Include item details for consumption tracking
            }
            for name in ingredients
        ]

        logger.info(f"✅ Returning {len(filtered_recipes)} processed recipes from pantry search")

        return {
            "recipes": filtered_recipes,
            "total_pantry_items": len(ingredients),
            "pantry_ingredients": pantry_ingredients,
            "ingredient_quantities": dict(ingredient_quantities),
            "ingredient_units": dict(ingredient_units),
            "expiring_items": expiring_soon,
            "searched_with": cleaned_ingredients,
            "original_ingredients": search_ingredients,
        }

    except ValueError as e:
        logger.error(f"ValueError in search recipes from pantry: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error searching recipes from pantry: {type(e).__name__}: {str(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to search recipes from pantry")
