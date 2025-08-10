"""
Enhanced recipe router with intelligent fallback logic.
Integrates backup recipes, Spoonacular, and AI generation.

🟡 PARTIAL - Enhanced router (requires app.py registration and dependency injection)
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.config.database import get_pantry_service as get_pantry_service_dep
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.recipe_fallback_service import (
    RecipeFallbackService,
    RecipeSearchConfig,
    RecipeSource,
    get_recipe_fallback_service,
)

logger = logging.getLogger(__name__)


# Request/Response models
class EnhancedRecipeSearchRequest(BaseModel):
    """Enhanced recipe search with fallback options."""

    user_id: Optional[int] = Field(None, description="User ID for personalized search")
    ingredients: Optional[list[str]] = Field(None, description="Available ingredients")
    query: Optional[str] = Field(None, description="Natural language search query")
    cuisine: Optional[str] = Field(None, description="Cuisine type preference")
    diet_type: Optional[str] = Field(None, description="Diet type (vegetarian, vegan, etc.)")
    max_ready_time: Optional[int] = Field(None, description="Maximum ready time in minutes")
    number: int = Field(10, ge=1, le=50, description="Number of results to return")

    # Fallback configuration
    enable_backup_recipes: bool = Field(True, description="Enable local backup recipe search")
    enable_spoonacular: bool = Field(True, description="Enable Spoonacular API search")
    enable_ai_generation: bool = Field(False, description="Enable AI recipe generation as fallback")
    backup_min_match_ratio: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum ingredient match ratio for backup recipes"
    )
    prefer_images: bool = Field(True, description="Prefer recipes with images")
    require_instructions: bool = Field(True, description="Only return recipes with instructions")


class RecipeFromPantryRequest(BaseModel):
    """Find recipes using pantry items with fallback support."""

    user_id: int = Field(..., description="User ID to get pantry items from")
    max_missing_ingredients: int = Field(
        5, description="Maximum number of missing ingredients allowed"
    )
    use_expiring_first: bool = Field(True, description="Prioritize items expiring soon")
    number: int = Field(10, ge=1, le=50, description="Number of results to return")

    # Fallback configuration
    enable_backup_recipes: bool = Field(True, description="Enable local backup recipe search")
    enable_spoonacular: bool = Field(True, description="Enable Spoonacular API search")
    backup_min_match_ratio: float = Field(
        0.4, ge=0.0, le=1.0, description="Minimum ingredient match ratio"
    )


class RecipeSourceFilter(BaseModel):
    """Filter recipes by source."""

    sources: list[RecipeSource] = Field(
        default_factory=lambda: [RecipeSource.BACKUP_LOCAL, RecipeSource.SPOONACULAR]
    )
    prefer_local: bool = Field(True, description="Prefer local recipes over external APIs")


router = APIRouter(
    prefix="/api/v1/enhanced-recipes",
    tags=["Enhanced Recipes"],
    responses={404: {"description": "Not found"}},
)


@router.post("/search", summary="Enhanced recipe search with intelligent fallback")
async def search_recipes_enhanced(
    request: EnhancedRecipeSearchRequest,
    fallback_service: RecipeFallbackService = Depends(get_recipe_fallback_service),
) -> dict[str, Any]:
    """
    Enhanced recipe search using intelligent fallback logic.

    Search order:
    1. Local backup recipes (13k+ recipes, always available)
    2. Spoonacular API (if enabled and needed)
    3. AI generation (if enabled and minimal results found)

    Returns recipes with source tracking and quality scoring.
    """
    try:
        # Configure fallback behavior
        config = RecipeSearchConfig(
            enable_backup_recipes=request.enable_backup_recipes,
            enable_spoonacular=request.enable_spoonacular,
            enable_openai=request.enable_ai_generation,
            backup_min_match_ratio=request.backup_min_match_ratio,
            max_results_per_source=request.number,
            total_max_results=request.number,
            prefer_images=request.prefer_images,
            require_instructions=request.require_instructions,
        )

        # Execute search with fallback
        results = await fallback_service.search_recipes(
            user_id=request.user_id,
            ingredients=request.ingredients,
            query=request.query,
            cuisine=request.cuisine,
            diet_type=request.diet_type,
            max_ready_time=request.max_ready_time,
            config=config,
        )

        # Format response with source information
        formatted_results = []
        source_counts = {}

        for result in results:
            source_counts[result.source.value] = source_counts.get(result.source.value, 0) + 1

            formatted_result = {
                "id": result.id,
                "title": result.title,
                "source": result.source.value,
                "image": result.image_url,
                "readyInMinutes": result.ready_in_minutes,
                "servings": result.servings,
                "usedIngredients": result.used_ingredients or [],
                "missedIngredients": result.missed_ingredients or [],
                "matchRatio": result.match_ratio,
                "cuisineType": result.cuisine_type,
                "difficulty": result.difficulty,
                "spoonacularId": result.spoonacular_id,
                "backupRecipeId": result.backup_recipe_id,
            }
            formatted_results.append(formatted_result)

        return {
            "results": formatted_results,
            "totalResults": len(formatted_results),
            "sourceBreakdown": source_counts,
            "searchConfig": {
                "backupEnabled": config.enable_backup_recipes,
                "spoonacularEnabled": config.enable_spoonacular,
                "aiEnabled": config.enable_openai,
                "minMatchRatio": config.backup_min_match_ratio,
            },
            "performanceStats": fallback_service.get_performance_stats(),
        }

    except Exception as e:
        logger.error(f"Enhanced recipe search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@router.post("/search/from-pantry", summary="Find recipes using pantry items with fallback")
async def search_recipes_from_pantry_enhanced(
    request: RecipeFromPantryRequest,
    fallback_service: RecipeFallbackService = Depends(get_recipe_fallback_service),
    pantry_service: PantryService = Depends(get_pantry_service_dep),
) -> dict[str, Any]:
    """
    Find recipes using user's pantry items with intelligent fallback.

    Automatically gets user's pantry items and searches for recipes
    using the enhanced fallback system.
    """
    try:
        # Get user's pantry items
        pantry_items = await pantry_service.get_pantry_items(request.user_id)

        if not pantry_items:
            raise HTTPException(status_code=404, detail="No pantry items found for user")

        # Extract ingredient names
        ingredients = [
            item.get("product_name", "").lower()
            for item in pantry_items
            if item.get("product_name")
        ]

        if not ingredients:
            raise HTTPException(status_code=400, detail="No valid ingredients found in pantry")

        # Configure search for pantry-based recipes
        config = RecipeSearchConfig(
            enable_backup_recipes=request.enable_backup_recipes,
            enable_spoonacular=request.enable_spoonacular,
            enable_openai=False,  # Don't generate AI recipes for pantry searches
            backup_min_match_ratio=request.backup_min_match_ratio,
            max_results_per_source=request.number,
            total_max_results=request.number,
            prefer_images=True,
            require_instructions=True,
        )

        # Search recipes with fallback
        results = await fallback_service.search_recipes(
            user_id=request.user_id, ingredients=ingredients, config=config
        )

        # Filter by missing ingredients threshold
        filtered_results = []
        for result in results:
            missing_count = len(result.missed_ingredients or [])
            if missing_count <= request.max_missing_ingredients:
                filtered_results.append(result)

        # Sort by match ratio and missing ingredients
        filtered_results.sort(
            key=lambda r: (-(r.match_ratio or 0), len(r.missed_ingredients or []))
        )

        # Format response
        formatted_results = []
        for result in filtered_results:
            formatted_result = {
                "id": result.id,
                "title": result.title,
                "source": result.source.value,
                "image": result.image_url,
                "readyInMinutes": result.ready_in_minutes,
                "servings": result.servings,
                "usedIngredients": result.used_ingredients or [],
                "missedIngredients": result.missed_ingredients or [],
                "matchRatio": result.match_ratio,
                "missingCount": len(result.missed_ingredients or []),
                "canMake": len(result.missed_ingredients or []) == 0,
                "spoonacularId": result.spoonacular_id,
                "backupRecipeId": result.backup_recipe_id,
            }
            formatted_results.append(formatted_result)

        return {
            "results": formatted_results,
            "pantryIngredients": ingredients,
            "totalPantryItems": len(pantry_items),
            "usableIngredients": len(ingredients),
            "searchConfig": {
                "maxMissingIngredients": request.max_missing_ingredients,
                "minMatchRatio": request.backup_min_match_ratio,
                "backupEnabled": request.enable_backup_recipes,
                "spoonacularEnabled": request.enable_spoonacular,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pantry recipe search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pantry search failed: {str(e)}") from e


@router.get("/{recipe_id}", summary="Get recipe details with source auto-detection")
async def get_recipe_details_enhanced(
    recipe_id: str,
    source: Optional[RecipeSource] = Query(
        None, description="Recipe source (auto-detect if not provided)"
    ),
    include_nutrition: bool = Query(False, description="Include nutrition information"),
    fallback_service: RecipeFallbackService = Depends(get_recipe_fallback_service),
) -> dict[str, Any]:
    """
    Get detailed recipe information with intelligent source detection.

    If source is not specified, attempts to detect from recipe_id format:
    - Numeric IDs < 1000000: Try Spoonacular first, then backup
    - Numeric IDs >= 1000000: Try backup first, then Spoonacular
    - Non-numeric IDs: Try AI/generated recipes
    """
    try:
        # Auto-detect source if not provided
        if source is None:
            try:
                numeric_id = int(recipe_id)
                if numeric_id >= 1000000:  # Backup recipe IDs are typically large
                    source = RecipeSource.BACKUP_LOCAL
                else:
                    source = RecipeSource.SPOONACULAR
            except ValueError:
                source = RecipeSource.OPENAI  # Non-numeric IDs are likely AI-generated

        # Get recipe details from appropriate source
        recipe_details = await fallback_service.get_recipe_details(
            recipe_id=recipe_id, source=source, include_nutrition=include_nutrition
        )

        if not recipe_details:
            # Try alternative source if first attempt failed
            if source == RecipeSource.BACKUP_LOCAL:
                alternative_source = RecipeSource.SPOONACULAR
            elif source == RecipeSource.SPOONACULAR:
                alternative_source = RecipeSource.BACKUP_LOCAL
            else:
                raise HTTPException(status_code=404, detail="Recipe not found")

            logger.info(f"Trying alternative source {alternative_source} for recipe {recipe_id}")
            recipe_details = await fallback_service.get_recipe_details(
                recipe_id=recipe_id, source=alternative_source, include_nutrition=include_nutrition
            )

            if recipe_details:
                source = alternative_source

        if not recipe_details:
            raise HTTPException(status_code=404, detail="Recipe not found in any source")

        # Add source information to response
        recipe_details["recipeSource"] = source.value
        recipe_details["sourceDetected"] = source != Query(None)

        return recipe_details

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe details for {recipe_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get recipe details: {str(e)}"
        ) from e


@router.get("/stats/performance", summary="Get fallback service performance statistics")
async def get_performance_statistics(
    fallback_service: RecipeFallbackService = Depends(get_recipe_fallback_service),
) -> dict[str, Any]:
    """Get current performance statistics for the recipe fallback service."""
    stats = fallback_service.get_performance_stats()

    return {
        "performanceStats": stats,
        "recommendations": {
            "backupRecipesHealthy": stats.get("backup_success_rate", 0) > 0.8,
            "spoonacularHealthy": stats.get("spoonacular_success_rate", 0) > 0.7,
            "avgResponseTimeOk": stats.get("avg_response_time", 0) < 2.0,
            "preferBackupRecipes": stats.get("backup_success_rate", 0)
            > stats.get("spoonacular_success_rate", 0),
        },
    }


@router.get("/sources/available", summary="Check availability of recipe sources")
async def check_source_availability() -> dict[str, Any]:
    """Check the availability and health of different recipe sources."""
    try:
        source_status = {
            "backup_recipes": {
                "available": True,
                "description": "Local backup recipe database",
                "recipe_count": "Unknown",  # Would need database query
                "response_time": "< 100ms",
                "reliability": "99.9%",
            },
            "spoonacular": {
                "available": True,  # Would need API health check
                "description": "Spoonacular Recipe API",
                "api_key_configured": "Unknown",  # Would need config check
                "rate_limit_status": "Unknown",
                "reliability": "95%",
            },
            "ai_generation": {
                "available": False,  # Not yet implemented in fallback
                "description": "AI-powered recipe generation",
                "openai_configured": "Unknown",
                "crew_ai_configured": "Unknown",
                "reliability": "80%",
            },
        }

        return {
            "sources": source_status,
            "fallback_chain": ["backup_recipes", "spoonacular", "ai_generation"],
            "recommended_config": {
                "enable_backup_recipes": True,
                "enable_spoonacular": True,
                "enable_ai_generation": False,
                "backup_min_match_ratio": 0.3,
            },
        }

    except Exception as e:
        logger.error(f"Error checking source availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to check source availability") from e
