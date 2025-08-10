"""
USDA Unit Validation Router - API endpoints for unit validation using USDA data
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend_gateway.core.database import get_db_pool
from backend_gateway.services.usda_food_service import USDAFoodService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/usda/units", tags=["USDA Unit Validation"])


async def get_usda_service():
    """Dependency to get USDA service instance."""
    db_pool = await get_db_pool()
    return USDAFoodService(db_pool)


@router.get("/validate")
async def validate_unit_for_food(
    food_name: str = Query(..., description="Name of the food item"),
    unit: str = Query(..., description="Unit to validate"),
    category_id: Optional[int] = Query(None, description="Optional food category ID"),
    usda_service: USDAFoodService = Depends(get_usda_service),
) -> dict[str, Any]:
    """
    Validate if a unit is appropriate for a food item using USDA data.

    Args:
        food_name: Name of the food item
        unit: Unit to validate (e.g., 'cup', 'lb', 'each')
        category_id: Optional USDA food category ID

    Returns:
        Validation result with suggestions
    """
    try:
        async with usda_service.db_pool.acquire() as conn:
            # Call the validation function
            result = await conn.fetchrow(
                """
                SELECT * FROM validate_unit_for_food($1, $2, $3)
                """,
                food_name,
                unit,
                category_id,
            )

            if result:
                return {
                    "is_valid": result["is_valid"],
                    "confidence": float(result["confidence"]) if result["confidence"] else 0.0,
                    "suggested_units": result["suggested_units"] or [],
                    "reason": result["reason"],
                    "food_name": food_name,
                    "unit": unit,
                }
            else:
                return {
                    "is_valid": False,
                    "confidence": 0.0,
                    "suggested_units": ["each", "lb", "oz"],
                    "reason": "Unable to validate unit",
                    "food_name": food_name,
                    "unit": unit,
                }

    except Exception as e:
        logger.error(f"Error validating unit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/category/{category_id}/units")
async def get_units_for_category(
    category_id: int,
    preferred_only: bool = Query(False, description="Return only preferred units"),
    usda_service: USDAFoodService = Depends(get_usda_service),
) -> list[dict[str, Any]]:
    """
    Get appropriate units for a food category based on USDA data.

    Args:
        category_id: USDA food category ID
        preferred_only: If true, return only the most commonly used units

    Returns:
        List of units with usage statistics
    """
    try:
        async with usda_service.db_pool.acquire() as conn:
            query = """
                SELECT
                    um.id as unit_id,
                    um.name as unit_name,
                    um.abbreviation,
                    um.unit_type,
                    ucm.usage_percentage,
                    ucm.is_preferred,
                    fc.description as category_name
                FROM usda_category_unit_mappings ucm
                JOIN usda_measure_units um ON ucm.unit_id = um.id
                JOIN usda_food_categories fc ON ucm.category_id = fc.id
                WHERE ucm.category_id = $1
            """

            if preferred_only:
                query += " AND ucm.is_preferred = TRUE"

            query += " ORDER BY ucm.usage_percentage DESC"

            rows = await conn.fetch(query, category_id)

            return [
                {
                    "unit_id": row["unit_id"],
                    "unit_name": row["unit_name"],
                    "abbreviation": row["abbreviation"],
                    "unit_type": row["unit_type"],
                    "usage_percentage": float(row["usage_percentage"]),
                    "is_preferred": row["is_preferred"],
                    "category_name": row["category_name"],
                }
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Error getting units for category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/suggest-units")
async def suggest_units_for_food(
    food_name: str = Query(..., description="Name of the food item"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
    usda_service: USDAFoodService = Depends(get_usda_service),
) -> dict[str, Any]:
    """
    Suggest appropriate units for a food item based on USDA data patterns.

    Args:
        food_name: Name of the food item
        limit: Maximum number of unit suggestions

    Returns:
        Unit suggestions with confidence scores
    """
    try:
        # First, try to find the food in USDA database
        foods = await usda_service.search_foods(food_name, limit=1)

        if not foods:
            return {
                "food_name": food_name,
                "category": "Unknown",
                "suggested_units": [
                    {"name": "each", "confidence": 0.5},
                    {"name": "lb", "confidence": 0.4},
                    {"name": "oz", "confidence": 0.3},
                ],
                "message": "Food not found in USDA database, using default suggestions",
            }

        food = foods[0]
        category_id = food.get("food_category_id")

        if not category_id:
            return {
                "food_name": food_name,
                "category": "Uncategorized",
                "suggested_units": [
                    {"name": "each", "confidence": 0.5},
                    {"name": "lb", "confidence": 0.4},
                    {"name": "oz", "confidence": 0.3},
                ],
                "message": "Food found but not categorized",
            }

        # Get units for this category
        async with usda_service.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    um.name as unit_name,
                    ucm.usage_percentage / 100.0 as confidence,
                    fc.description as category_name
                FROM usda_category_unit_mappings ucm
                JOIN usda_measure_units um ON ucm.unit_id = um.id
                JOIN usda_food_categories fc ON ucm.category_id = fc.id
                WHERE ucm.category_id = $1
                ORDER BY ucm.usage_percentage DESC
                LIMIT $2
                """,
                category_id,
                limit,
            )

            if rows:
                return {
                    "food_name": food_name,
                    "food_description": food.get("description"),
                    "category": rows[0]["category_name"],
                    "suggested_units": [
                        {"name": row["unit_name"], "confidence": float(row["confidence"])}
                        for row in rows
                    ],
                    "message": "Suggestions based on USDA category patterns",
                }
            else:
                return {
                    "food_name": food_name,
                    "category": "Unknown",
                    "suggested_units": [
                        {"name": "each", "confidence": 0.5},
                        {"name": "lb", "confidence": 0.4},
                        {"name": "oz", "confidence": 0.3},
                    ],
                    "message": "No unit patterns found for this category",
                }

    except Exception as e:
        logger.error(f"Error suggesting units: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/unit-types")
async def get_unit_types(usda_service: USDAFoodService = Depends(get_usda_service)) -> list[str]:
    """
    Get all available unit types from USDA data.

    Returns:
        List of unit types (e.g., 'volume', 'weight', 'count')
    """
    try:
        async with usda_service.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT unit_type
                FROM usda_measure_units
                WHERE unit_type IS NOT NULL
                ORDER BY unit_type
                """
            )

            return [row["unit_type"] for row in rows]

    except Exception as e:
        logger.error(f"Error getting unit types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
