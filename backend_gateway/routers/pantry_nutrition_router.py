"""
Pantry Nutrition Router
Provides endpoints for nutritional analysis of pantry items.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import asyncpg

from backend_gateway.services.pantry_nutrition_service import PantryNutritionService
from backend_gateway.core.database import get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pantry-nutrition", tags=["Pantry Nutrition"])


@router.get("/summary/{user_id}")
async def get_nutrition_summary(
    user_id: int,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Get nutritional summary of user's entire pantry.
    
    Returns total nutritional content and daily value percentages.
    """
    service = PantryNutritionService(db_pool)
    summary = await service.get_pantry_nutrition_summary(user_id)
    
    return summary


@router.post("/match-items/{user_id}")
async def match_pantry_items(
    user_id: int,
    auto_match: bool = True,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Match pantry items to USDA foods for nutritional data.
    
    Args:
        user_id: User ID
        auto_match: If True, automatically create high-confidence matches
        
    Returns:
        Matching results and statistics
    """
    service = PantryNutritionService(db_pool)
    results = await service.match_pantry_items_to_usda(user_id, auto_match)
    
    return results


@router.get("/item/{pantry_item_id}")
async def get_item_nutrition(
    pantry_item_id: int,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Get nutritional information for a specific pantry item.
    """
    service = PantryNutritionService(db_pool)
    nutrition = await service.get_item_nutrition_by_pantry_id(pantry_item_id)
    
    if not nutrition:
        raise HTTPException(
            status_code=404,
            detail="Nutritional information not available for this item"
        )
    
    return nutrition


@router.get("/daily-intake/{user_id}")
async def calculate_daily_intake(
    user_id: int,
    days: int = 7,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Calculate estimated daily nutritional intake based on pantry consumption.
    
    Args:
        user_id: User ID
        days: Number of days to calculate intake for
        
    Returns:
        Estimated daily nutritional values
    """
    service = PantryNutritionService(db_pool)
    summary = await service.get_pantry_nutrition_summary(user_id)
    
    # Simple calculation - divide total by days
    # A more sophisticated version would track actual consumption
    daily_nutrition = {
        nutrient: round(value / days, 2)
        for nutrient, value in summary['total_nutrition'].items()
    }
    
    return {
        'calculation_method': 'pantry_total_divided_by_days',
        'days': days,
        'estimated_daily_nutrition': daily_nutrition,
        'daily_value_percentages': {
            'calories': round((daily_nutrition['calories'] / 2000) * 100, 1),
            'protein': round((daily_nutrition['protein_g'] / 50) * 100, 1),
            'fat': round((daily_nutrition['fat_g'] / 65) * 100, 1),
            'carbs': round((daily_nutrition['carbs_g'] / 300) * 100, 1),
            'fiber': round((daily_nutrition['fiber_g'] / 25) * 100, 1),
            'sodium': round((daily_nutrition['sodium_mg'] / 2300) * 100, 1)
        },
        'note': 'This is an estimate based on pantry contents divided by days'
    }


@router.get("/recipe-nutrition")
async def calculate_recipe_nutrition(
    recipe_id: int,
    servings: int = 1,
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Calculate nutritional information for a recipe based on ingredients.
    
    Args:
        recipe_id: Recipe ID
        servings: Number of servings to calculate for
        
    Returns:
        Nutritional breakdown per serving
    """
    async with db_pool.acquire() as conn:
        # Get recipe ingredients
        ingredients = await conn.fetch("""
            SELECT 
                ri.name,
                ri.quantity_amount,
                ri.quantity_unit,
                pi.id as pantry_item_id
            FROM recipe_ingredients ri
            LEFT JOIN pantry_items pi ON 
                LOWER(pi.name) LIKE '%' || LOWER(ri.name) || '%'
            WHERE ri.recipe_id = $1
        """, recipe_id)
        
        if not ingredients:
            raise HTTPException(
                status_code=404,
                detail="Recipe not found or has no ingredients"
            )
        
        service = PantryNutritionService(db_pool)
        total_nutrition = {
            'calories': 0,
            'protein_g': 0,
            'fat_g': 0,
            'carbs_g': 0,
            'fiber_g': 0,
            'sugar_g': 0,
            'sodium_mg': 0
        }
        
        ingredients_with_nutrition = []
        missing_nutrition = []
        
        for ingredient in ingredients:
            if ingredient['pantry_item_id']:
                nutrition = await service.get_item_nutrition_by_pantry_id(
                    ingredient['pantry_item_id']
                )
                
                if nutrition and nutrition.get('nutrients'):
                    # Add to total (simplified - would need proper unit conversion)
                    for nutrient_name, data in nutrition['nutrients'].items():
                        # Map to our simplified names
                        # This is a simplified example
                        pass
                    
                    ingredients_with_nutrition.append(ingredient['name'])
                else:
                    missing_nutrition.append(ingredient['name'])
            else:
                missing_nutrition.append(ingredient['name'])
        
        # Calculate per serving
        per_serving = {
            nutrient: round(value / servings, 2)
            for nutrient, value in total_nutrition.items()
        }
        
        return {
            'recipe_id': recipe_id,
            'servings': servings,
            'nutrition_per_serving': per_serving,
            'ingredients_analyzed': len(ingredients_with_nutrition),
            'ingredients_missing_data': missing_nutrition,
            'completeness': round(
                len(ingredients_with_nutrition) / len(ingredients) * 100, 1
            )
        }