"""Enhanced OpenAI Recipe Router
Provides endpoints for generating Spoonacular-compatible recipes using OpenAI.
Returns rich recipe data that displays identically to Spoonacular recipes in the frontend.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from backend_gateway.services.enhanced_openai_recipe_service import EnhancedOpenAIRecipeService
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/enhanced-openai-recipes",
    tags=["Enhanced OpenAI Recipes"],
    responses={404: {"description": "Not found"}},
)

# Service initialization
enhanced_recipe_service = EnhancedOpenAIRecipeService()


# Request/Response Models
class RecipeGenerationRequest(BaseModel):
    """Request model for recipe generation"""
    recipe_name: str = Field(..., description="Name of the recipe to generate")
    available_ingredients: List[str] = Field(..., description="List of available ingredients")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions (vegetarian, vegan, etc.)")
    allergens: Optional[List[str]] = Field(None, description="Allergens to avoid")
    cuisine_type: Optional[str] = Field(None, description="Preferred cuisine type")
    cooking_time: Optional[int] = Field(None, description="Maximum cooking time in minutes")
    servings: Optional[int] = Field(4, description="Number of servings")


class BatchRecipeRequest(BaseModel):
    """Request model for batch recipe generation"""
    recipe_requests: List[RecipeGenerationRequest] = Field(..., description="List of recipe generation requests")
    max_concurrent: Optional[int] = Field(3, description="Maximum concurrent requests")


class RecipeResponse(BaseModel):
    """Response model for generated recipes"""
    success: bool
    recipe: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None


class BatchRecipeResponse(BaseModel):
    """Response model for batch recipe generation"""
    success: bool
    recipes: List[Dict[str, Any]]
    generated_count: int
    failed_count: int
    errors: List[str]


# Single Recipe Generation Endpoints

@router.post("/generate", response_model=RecipeResponse, summary="Generate a single enhanced recipe")
async def generate_enhanced_recipe(
    request: RecipeGenerationRequest
) -> RecipeResponse:
    """
    Generate a single Spoonacular-compatible recipe using OpenAI.
    
    Returns a rich recipe object with:
    - Complete nutrition data (nutrients array, caloricBreakdown)
    - Structured ingredients (extendedIngredients with measures)
    - Detailed instructions (analyzedInstructions with steps)
    - Metadata (cuisines, dishTypes, diets, occasions)
    - Compatibility fields for both chat and Spoonacular formats
    
    The generated recipe will display identically to Spoonacular recipes in the frontend.
    """
    try:
        recipe = enhanced_recipe_service.generate_enhanced_recipe(
            recipe_name=request.recipe_name,
            available_ingredients=request.available_ingredients,
            dietary_restrictions=request.dietary_restrictions,
            allergens=request.allergens,
            cuisine_type=request.cuisine_type,
            cooking_time=request.cooking_time,
            servings=request.servings
        )
        
        # Validate the recipe structure
        validation_result = enhanced_recipe_service.validate_recipe_structure(recipe)
        
        return RecipeResponse(
            success=True,
            recipe=recipe,
            validation_result=validation_result
        )
        
    except Exception as e:
        logger.error(f"Error generating enhanced recipe: {str(e)}")
        return RecipeResponse(
            success=False,
            error=str(e)
        )


@router.get("/generate-from-query", response_model=RecipeResponse, summary="Generate recipe from query parameters")
async def generate_recipe_from_query(
    recipe_name: str = Query(..., description="Name of the recipe"),
    ingredients: str = Query(..., description="Comma-separated list of ingredients"),
    dietary_restrictions: Optional[str] = Query(None, description="Comma-separated dietary restrictions"),
    allergens: Optional[str] = Query(None, description="Comma-separated allergens to avoid"),
    cuisine_type: Optional[str] = Query(None, description="Cuisine type"),
    cooking_time: Optional[int] = Query(None, description="Maximum cooking time in minutes"),
    servings: Optional[int] = Query(4, description="Number of servings")
) -> RecipeResponse:
    """
    Generate a recipe from query parameters (useful for direct API calls).
    
    Example:
    /generate-from-query?recipe_name=Pasta Marinara&ingredients=pasta,tomatoes,garlic&cuisine_type=Italian
    """
    try:
        # Parse comma-separated strings into lists
        ingredient_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
        dietary_list = [diet.strip() for diet in dietary_restrictions.split(',') if diet.strip()] if dietary_restrictions else None
        allergen_list = [allergen.strip() for allergen in allergens.split(',') if allergen.strip()] if allergens else None
        
        recipe = enhanced_recipe_service.generate_enhanced_recipe(
            recipe_name=recipe_name,
            available_ingredients=ingredient_list,
            dietary_restrictions=dietary_list,
            allergens=allergen_list,
            cuisine_type=cuisine_type,
            cooking_time=cooking_time,
            servings=servings
        )
        
        validation_result = enhanced_recipe_service.validate_recipe_structure(recipe)
        
        return RecipeResponse(
            success=True,
            recipe=recipe,
            validation_result=validation_result
        )
        
    except Exception as e:
        logger.error(f"Error generating recipe from query: {str(e)}")
        return RecipeResponse(
            success=False,
            error=str(e)
        )


# Batch Recipe Generation

@router.post("/generate-batch", response_model=BatchRecipeResponse, summary="Generate multiple enhanced recipes")
async def generate_batch_recipes(
    request: BatchRecipeRequest
) -> BatchRecipeResponse:
    """
    Generate multiple recipes in batch with rate limiting.
    Useful for generating multiple recipe variations or meal plans.
    """
    try:
        # Convert request to service format
        recipe_requests = [
            {
                "recipe_name": req.recipe_name,
                "available_ingredients": req.available_ingredients,
                "dietary_restrictions": req.dietary_restrictions,
                "allergens": req.allergens,
                "cuisine_type": req.cuisine_type,
                "cooking_time": req.cooking_time,
                "servings": req.servings
            }
            for req in request.recipe_requests
        ]
        
        recipes = enhanced_recipe_service.batch_generate_recipes(
            recipe_requests=recipe_requests,
            max_concurrent=request.max_concurrent
        )
        
        # Count successes and failures
        successful_recipes = [r for r in recipes if r.get("id")]
        failed_count = len(recipes) - len(successful_recipes)
        
        errors = []
        for i, recipe in enumerate(recipes):
            if not recipe.get("id"):
                errors.append(f"Recipe {i+1}: Failed to generate")
        
        return BatchRecipeResponse(
            success=True,
            recipes=successful_recipes,
            generated_count=len(successful_recipes),
            failed_count=failed_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in batch recipe generation: {str(e)}")
        return BatchRecipeResponse(
            success=False,
            recipes=[],
            generated_count=0,
            failed_count=len(request.recipe_requests),
            errors=[str(e)]
        )


# Recipe Validation and Utilities

@router.post("/validate-recipe", summary="Validate recipe structure")
async def validate_recipe_structure(
    recipe: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate that a recipe matches the expected Spoonacular structure.
    Useful for debugging and quality assurance.
    """
    try:
        validation_result = enhanced_recipe_service.validate_recipe_structure(recipe)
        return {
            "success": True,
            "validation": validation_result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/template", summary="Get recipe template structure")
async def get_recipe_template() -> Dict[str, Any]:
    """
    Get the expected recipe template structure for reference.
    Useful for understanding the required fields and format.
    """
    return {
        "success": True,
        "template": {
            "id": 3001,
            "title": "Recipe Name",
            "name": "Recipe Name",  # Chat compatibility
            "image": "https://example.com/image.jpg",
            "summary": "Brief description of the dish",
            "readyInMinutes": 30,
            "time": 30,  # Chat compatibility
            "servings": 4,
            "sourceUrl": "https://example.com/recipe",
            "cuisines": ["American"],
            "dishTypes": ["main course", "dinner"],
            "diets": ["vegetarian"],
            "occasions": ["casual", "weeknight"],
            "extendedIngredients": [{
                "id": 1,
                "name": "ingredient_name",
                "original": "2 cups ingredient_name, diced",
                "amount": 2.0,
                "unit": "cups",
                "aisle": "Produce",
                "meta": ["diced"],
                "measures": {
                    "us": {"amount": 2.0, "unitShort": "cups", "unitLong": "cups"},
                    "metric": {"amount": 473.0, "unitShort": "ml", "unitLong": "milliliters"}
                }
            }],
            "analyzedInstructions": [{
                "steps": [{
                    "number": 1,
                    "step": "Detailed cooking instruction",
                    "ingredients": [{"id": 1, "name": "ingredient_used"}],
                    "equipment": [{"id": 1, "name": "equipment_needed"}],
                    "length": {"number": 5, "unit": "minutes"}
                }]
            }],
            "nutrition": {
                "nutrients": [
                    {"name": "Calories", "amount": 420, "unit": "kcal"},
                    {"name": "Protein", "amount": 32, "unit": "g"},
                    {"name": "Fat", "amount": 12, "unit": "g"},
                    {"name": "Carbohydrates", "amount": 45, "unit": "g"}
                ],
                "caloricBreakdown": {
                    "percentProtein": 30,
                    "percentFat": 26,
                    "percentCarbs": 44
                },
                "calories": 420,
                "protein": 32,
                "carbs": 45,
                "fat": 12
            },
            # Chat format compatibility
            "ingredients": ["2 cups ingredient_name, diced"],
            "instructions": ["Detailed cooking instruction"],
            # Matching data
            "available_ingredients": ["ingredient_name"],
            "missing_ingredients": [],
            "available_count": 1,
            "missing_count": 0,
            "match_score": 1.0,
            # Safety data
            "safety_status": "SAFE",
            "safety_violations": [],
            "safety_warnings": [],
            "allergen_risks": [],
            "source": "openai_enhanced"
        },
        "description": "This template shows the complete structure of an enhanced recipe that is compatible with both Spoonacular and chat formats."
    }


# Health and Status Endpoints

@router.get("/health", summary="Check service health")
async def health_check() -> Dict[str, Any]:
    """Check if the enhanced OpenAI recipe service is healthy and configured"""
    try:
        # Test basic service functionality
        test_recipe = enhanced_recipe_service.generate_enhanced_recipe(
            recipe_name="Test Recipe",
            available_ingredients=["test_ingredient"],
            dietary_restrictions=[],
            allergens=[],
            cuisine_type=None,
            cooking_time=None,
            servings=2
        )
        
        has_openai_key = enhanced_recipe_service.client is not None
        
        return {
            "success": True,
            "service_status": "healthy",
            "openai_configured": has_openai_key,
            "test_generation": test_recipe.get("id") is not None,
            "features": {
                "recipe_generation": True,
                "batch_processing": True,
                "structure_validation": True,
                "spoonacular_compatibility": True
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "service_status": "unhealthy",
            "error": str(e)
        }


@router.get("/stats", summary="Get service statistics")
async def get_service_stats() -> Dict[str, Any]:
    """Get statistics about the enhanced recipe service"""
    return {
        "success": True,
        "stats": {
            "current_recipe_id": enhanced_recipe_service.recipe_id_counter,
            "service_version": "1.0.0",
            "features": {
                "spoonacular_compatibility": "✅ Full compatibility",
                "nutrition_data": "✅ Complete nutrients array",
                "structured_ingredients": "✅ Extended ingredients with measures",
                "detailed_instructions": "✅ Analyzed instructions with steps",
                "safety_validation": "✅ Built-in safety checks",
                "batch_processing": "✅ Rate-limited batch generation"
            },
            "supported_formats": [
                "Spoonacular API format",
                "Chat recipe format",
                "Hybrid compatibility format"
            ]
        }
    }


# Export the router
__all__ = ["router"]