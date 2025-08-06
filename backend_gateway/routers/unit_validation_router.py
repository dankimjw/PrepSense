"""
Unit Validation Router
Provides endpoints for validating and fixing inappropriate units.
"""

import logging
from typing import Any, Dict, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend_gateway.core.database import get_db_pool
from backend_gateway.services.smart_unit_validator import SmartUnitValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/units", tags=["Unit Validation"])


class UnitValidationRequest(BaseModel):
    """Request to validate a unit for an item."""

    item_name: str
    unit: str
    quantity: Optional[float] = None


class UnitValidationResponse(BaseModel):
    """Response with unit validation result."""

    is_valid: bool
    current_unit: str
    suggested_unit: str
    suggested_units: list[str]
    category: str
    reason: str
    severity: str  # 'error', 'warning', 'info'


@router.post("/validate", response_model=UnitValidationResponse)
async def validate_unit(
    request: UnitValidationRequest, db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Validate if a unit is appropriate for a food item.

    Example: strawberries with unit 'mL' → error, suggest 'lb' or 'container'
    """
    validator = SmartUnitValidator(db_pool)

    result = await validator.validate_and_suggest_unit(
        request.item_name, request.unit, request.quantity
    )

    return UnitValidationResponse(**result)


@router.get("/check-pantry/{user_id}")
async def check_pantry_units(
    user_id: int, db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Check all pantry items for unit validation issues.

    Returns summary of problems and suggested fixes.
    """
    validator = SmartUnitValidator(db_pool)

    results = await validator.bulk_validate_pantry(user_id)

    return results


@router.post("/fix-pantry/{user_id}")
async def fix_pantry_units(
    user_id: int, auto_fix: bool = False, db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Fix unit validation issues in pantry.

    Args:
        user_id: User ID
        auto_fix: If True, automatically update units. If False, just return suggestions.

    Returns:
        Summary of fixes applied or suggested
    """
    validator = SmartUnitValidator(db_pool)

    results = await validator.fix_pantry_units(user_id, auto_fix)

    return results


@router.get("/suggestions/{item_name}")
async def get_unit_suggestions(
    item_name: str, db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Get suggested units for a food item.

    Useful for dropdowns when adding items manually.
    """
    validator = SmartUnitValidator(db_pool)

    # Get validation with default unit to see suggestions
    result = await validator.validate_and_suggest_unit(item_name, "each")

    return {
        "item_name": item_name,
        "category": result["category"],
        "recommended_units": result["suggested_units"],
        "default_unit": result["suggested_unit"],
    }


@router.get("/categories")
async def get_unit_categories() -> Dict[str, Any]:
    """
    Get all unit categories and their rules.

    Useful for understanding unit validation logic.
    """
    return {
        "produce_fruits": {
            "description": "Fresh fruits like strawberries, apples",
            "allowed_units": [
                "lb",
                "oz",
                "kg",
                "g",
                "each",
                "pint",
                "quart",
                "basket",
                "bag",
                "container",
            ],
            "forbidden_units": ["ml", "l", "fl oz", "cup", "gallon"],
            "examples": "strawberries by lb or pint container, not mL",
        },
        "produce_vegetables": {
            "description": "Fresh vegetables like carrots, lettuce",
            "allowed_units": ["lb", "oz", "kg", "g", "each", "bunch", "head", "bag", "package"],
            "forbidden_units": ["ml", "l", "fl oz", "cup", "gallon"],
            "examples": "carrots by lb, lettuce by head, celery by bunch",
        },
        "dairy_liquid": {
            "description": "Liquid dairy like milk, yogurt",
            "allowed_units": [
                "ml",
                "l",
                "fl oz",
                "cup",
                "pint",
                "quart",
                "gallon",
                "bottle",
                "carton",
            ],
            "forbidden_units": ["each", "slice"],
            "examples": "milk sold by gallon or quart, not each",
        },
        "dairy_solid": {
            "description": "Solid dairy like cheese, butter",
            "allowed_units": ["oz", "lb", "g", "kg", "slice", "stick", "block", "package"],
            "forbidden_units": ["ml", "l", "fl oz", "cup"],
            "examples": "cheese by oz or slice, butter by stick",
        },
        "eggs": {
            "description": "Eggs",
            "allowed_units": ["each", "dozen", "carton"],
            "forbidden_units": ["ml", "l", "oz", "lb"],
            "examples": "eggs sold by dozen, not by weight",
        },
        "beverages": {
            "description": "Drinks and liquids",
            "allowed_units": [
                "ml",
                "l",
                "fl oz",
                "cup",
                "pint",
                "quart",
                "gallon",
                "bottle",
                "can",
                "container",
            ],
            "forbidden_units": ["each", "slice", "oz", "lb"],
            "examples": "juice by bottle or gallon, soda by can",
        },
        "meat": {
            "description": "Meat and poultry",
            "allowed_units": ["lb", "oz", "kg", "g", "piece", "slice", "package"],
            "forbidden_units": ["ml", "l", "fl oz", "cup", "each"],
            "examples": "ground beef by lb, chicken breast by piece",
        },
        "spices": {
            "description": "Spices and seasonings",
            "allowed_units": ["tsp", "tbsp", "g", "oz", "container", "jar"],
            "forbidden_units": ["lb", "kg", "l", "gallon", "each"],
            "examples": "spices sold in small containers, not by pound",
        },
    }


@router.post("/batch-validate")
async def batch_validate_units(
    items: list[UnitValidationRequest], db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Validate multiple items at once.

    Useful for validating OCR results before adding to pantry.
    """
    validator = SmartUnitValidator(db_pool)

    results = []
    error_count = 0
    warning_count = 0

    for item in items:
        validation = await validator.validate_and_suggest_unit(
            item.item_name, item.unit, item.quantity
        )

        results.append({"item_name": item.item_name, "validation": validation})

        if validation["severity"] == "error":
            error_count += 1
        elif validation["severity"] == "warning":
            warning_count += 1

    return {
        "total_items": len(items),
        "errors": error_count,
        "warnings": warning_count,
        "results": results,
    }
