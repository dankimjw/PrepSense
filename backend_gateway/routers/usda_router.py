"""
USDA Food Database Router - API endpoints for USDA food data
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend_gateway.core.database import get_db_pool
from backend_gateway.services.usda_food_service import USDAFoodService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usda", tags=["USDA Food Database"])


async def get_usda_service():
    """Dependency to get USDA service instance."""
    db_pool = await get_db_pool()
    return USDAFoodService(db_pool)


@router.get("/search")
async def search_foods(
    query: str = Query(..., description="Search query for food items"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    usda_service: USDAFoodService = Depends(get_usda_service),
) -> List[dict]:
    """
    Search USDA food database

    Args:
        query: Search term for food items
        limit: Maximum number of results to return

    Returns:
        List of matching food items with nutritional data
    """
    try:
        results = await usda_service.search_foods(query, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Error searching USDA database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/food/{fdc_id}")
async def get_food_details(
    fdc_id: str, usda_service: USDAFoodService = Depends(get_usda_service)
) -> dict:
    """
    Get detailed nutritional information for a specific food

    Args:
        fdc_id: USDA FDC ID for the food item

    Returns:
        Detailed nutritional information
    """
    try:
        details = await usda_service.get_food_details(fdc_id)
        if not details:
            raise HTTPException(status_code=404, detail="Food not found")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting food details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nutrients/{food_name}")
async def get_nutrients_by_name(
    food_name: str,
    serving_size: Optional[float] = Query(100, description="Serving size in grams"),
    usda_service: USDAFoodService = Depends(get_usda_service),
) -> dict:
    """
    Get nutritional information by food name

    Args:
        food_name: Name of the food item
        serving_size: Serving size in grams (default: 100g)

    Returns:
        Nutritional information for the specified serving
    """
    try:
        nutrients = await usda_service.get_nutrients_by_name(food_name, serving_size)
        if not nutrients:
            raise HTTPException(status_code=404, detail="Food not found")
        return nutrients
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting nutrients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
