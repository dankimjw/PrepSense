"""
Units API Router
Provides endpoints for unit management and food category rules
"""

from typing import Dict, List, Optional

import asyncpg
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..constants.food_category_unit_rules import (
    FOOD_CATEGORY_UNIT_RULES,
    UnitCategory,
    get_allowed_unit_categories,
    get_default_unit_category,
    get_preferred_unit,
    validate_unit_for_food_category,
)

router = APIRouter(prefix="/units", tags=["units"])


class Unit(BaseModel):
    id: str
    label: str
    category: str
    to_base_factor: float
    is_metric: bool = True
    display_order: int = 999


class UnitConversion(BaseModel):
    from_unit: str
    to_unit: str
    factor: float
    convertible: bool


class FoodCategoryRules(BaseModel):
    category: str
    allowed_unit_categories: List[str]
    default_unit_category: str
    default_unit: str
    available_units: Dict[str, List[Unit]]


@router.get("/", response_model=List[Unit])
async def get_units(
    category: Optional[str] = Query(
        None, description="Filter by unit category (mass, volume, count)"
    ),
    metric_only: bool = Query(False, description="Return only metric units"),
):
    """Get all available units, optionally filtered by category"""
    try:
        # This would normally query the database
        # For now, return a hardcoded list based on the SQL schema
        units = [
            # Mass units
            Unit(
                id="g",
                label="gram",
                category="mass",
                to_base_factor=1.0,
                is_metric=True,
                display_order=1,
            ),
            Unit(
                id="kg",
                label="kilogram",
                category="mass",
                to_base_factor=1000.0,
                is_metric=True,
                display_order=2,
            ),
            Unit(
                id="mg",
                label="milligram",
                category="mass",
                to_base_factor=0.001,
                is_metric=True,
                display_order=3,
            ),
            Unit(
                id="oz",
                label="ounce",
                category="mass",
                to_base_factor=28.3495,
                is_metric=False,
                display_order=10,
            ),
            Unit(
                id="lb",
                label="pound",
                category="mass",
                to_base_factor=453.592,
                is_metric=False,
                display_order=11,
            ),
            # Volume units
            Unit(
                id="ml",
                label="millilitre",
                category="volume",
                to_base_factor=1.0,
                is_metric=True,
                display_order=1,
            ),
            Unit(
                id="l",
                label="litre",
                category="volume",
                to_base_factor=1000.0,
                is_metric=True,
                display_order=2,
            ),
            Unit(
                id="tsp",
                label="teaspoon",
                category="volume",
                to_base_factor=4.92892,
                is_metric=False,
                display_order=10,
            ),
            Unit(
                id="tbsp",
                label="tablespoon",
                category="volume",
                to_base_factor=14.7868,
                is_metric=False,
                display_order=11,
            ),
            Unit(
                id="cup",
                label="cup",
                category="volume",
                to_base_factor=236.588,
                is_metric=False,
                display_order=12,
            ),
            Unit(
                id="floz",
                label="fluid ounce",
                category="volume",
                to_base_factor=29.5735,
                is_metric=False,
                display_order=13,
            ),
            # Count units
            Unit(
                id="ea",
                label="each",
                category="count",
                to_base_factor=1.0,
                is_metric=True,
                display_order=1,
            ),
            Unit(
                id="dozen",
                label="dozen",
                category="count",
                to_base_factor=12.0,
                is_metric=True,
                display_order=2,
            ),
            Unit(
                id="head",
                label="head",
                category="count",
                to_base_factor=1.0,
                is_metric=True,
                display_order=3,
            ),
            Unit(
                id="bunch",
                label="bunch",
                category="count",
                to_base_factor=1.0,
                is_metric=True,
                display_order=4,
            ),
            Unit(
                id="loaf",
                label="loaf",
                category="count",
                to_base_factor=20.0,
                is_metric=True,
                display_order=5,
            ),
            Unit(
                id="slice",
                label="slice",
                category="count",
                to_base_factor=1.0,
                is_metric=True,
                display_order=6,
            ),
            Unit(
                id="can",
                label="can",
                category="count",
                to_base_factor=1.0,
                is_metric=True,
                display_order=7,
            ),
            Unit(
                id="bottle",
                label="bottle",
                category="count",
                to_base_factor=1.0,
                is_metric=True,
                display_order=8,
            ),
        ]

        # Apply filters
        if category:
            units = [u for u in units if u.category == category]

        if metric_only:
            units = [u for u in units if u.is_metric]

        # Sort by display order
        units.sort(key=lambda x: x.display_order)

        return units

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/food-category-rules/{category}", response_model=FoodCategoryRules)
async def get_food_category_rules(category: str):
    """Get unit rules for a specific food category"""
    # Normalize category name
    category_key = category.lower().replace(" ", "_")

    if category_key not in FOOD_CATEGORY_UNIT_RULES:
        raise HTTPException(status_code=404, detail=f"Food category '{category}' not found")

    rules = FOOD_CATEGORY_UNIT_RULES[category_key]
    allowed_categories = rules["allowed_categories"]
    default_category = rules["default_category"]

    # Get units for each allowed category
    available_units = {}
    for unit_cat in allowed_categories:
        # This would normally query the database
        # For now, return a subset based on the category
        if unit_cat == UnitCategory.MASS:
            available_units["mass"] = [
                Unit(id="g", label="grams", category="mass", to_base_factor=1.0, display_order=1),
                Unit(
                    id="kg",
                    label="kilograms",
                    category="mass",
                    to_base_factor=1000.0,
                    display_order=2,
                ),
                Unit(
                    id="oz",
                    label="ounces",
                    category="mass",
                    to_base_factor=28.3495,
                    is_metric=False,
                    display_order=10,
                ),
                Unit(
                    id="lb",
                    label="pounds",
                    category="mass",
                    to_base_factor=453.592,
                    is_metric=False,
                    display_order=11,
                ),
            ]
        elif unit_cat == UnitCategory.VOLUME:
            available_units["volume"] = [
                Unit(
                    id="ml",
                    label="millilitres",
                    category="volume",
                    to_base_factor=1.0,
                    display_order=1,
                ),
                Unit(
                    id="l",
                    label="litres",
                    category="volume",
                    to_base_factor=1000.0,
                    display_order=2,
                ),
                Unit(
                    id="cup",
                    label="cups",
                    category="volume",
                    to_base_factor=236.588,
                    is_metric=False,
                    display_order=10,
                ),
                Unit(
                    id="tsp",
                    label="teaspoons",
                    category="volume",
                    to_base_factor=4.92892,
                    is_metric=False,
                    display_order=11,
                ),
                Unit(
                    id="tbsp",
                    label="tablespoons",
                    category="volume",
                    to_base_factor=14.7868,
                    is_metric=False,
                    display_order=12,
                ),
            ]
        elif unit_cat == UnitCategory.COUNT:
            available_units["count"] = [
                Unit(id="ea", label="each", category="count", to_base_factor=1.0, display_order=1),
                Unit(
                    id="dozen",
                    label="dozen",
                    category="count",
                    to_base_factor=12.0,
                    display_order=2,
                ),
            ]

            # Add category-specific count units
            if category_key == "produce":
                available_units["count"].extend(
                    [
                        Unit(
                            id="head",
                            label="head",
                            category="count",
                            to_base_factor=1.0,
                            display_order=3,
                        ),
                        Unit(
                            id="bunch",
                            label="bunch",
                            category="count",
                            to_base_factor=1.0,
                            display_order=4,
                        ),
                    ]
                )
            elif category_key == "bakery":
                available_units["count"].extend(
                    [
                        Unit(
                            id="loaf",
                            label="loaf",
                            category="count",
                            to_base_factor=20.0,
                            display_order=3,
                        ),
                        Unit(
                            id="slice",
                            label="slice",
                            category="count",
                            to_base_factor=1.0,
                            display_order=4,
                        ),
                    ]
                )

    # Get default unit
    default_units = {UnitCategory.MASS: "g", UnitCategory.VOLUME: "ml", UnitCategory.COUNT: "ea"}
    default_unit = default_units.get(default_category, "ea")

    return FoodCategoryRules(
        category=category,
        allowed_unit_categories=[cat.value for cat in allowed_categories],
        default_unit_category=default_category.value,
        default_unit=default_unit,
        available_units=available_units,
    )


@router.post("/validate-conversion", response_model=UnitConversion)
async def validate_unit_conversion(
    from_unit: str = Query(..., description="Source unit ID"),
    to_unit: str = Query(..., description="Target unit ID"),
    quantity: Optional[float] = Query(1.0, description="Quantity to convert"),
):
    """Check if units can be converted and calculate conversion factor"""
    # This would normally query the database to check unit categories
    # For now, use a simplified check

    # Define unit categories (would come from DB)
    unit_categories = {
        # Mass
        "g": "mass",
        "kg": "mass",
        "mg": "mass",
        "oz": "mass",
        "lb": "mass",
        # Volume
        "ml": "volume",
        "l": "volume",
        "tsp": "volume",
        "tbsp": "volume",
        "cup": "volume",
        "floz": "volume",
        "pt": "volume",
        "qt": "volume",
        "gal": "volume",
        # Count
        "ea": "count",
        "dozen": "count",
        "pair": "count",
        "head": "count",
        "bunch": "count",
        "loaf": "count",
        "slice": "count",
        "can": "count",
        "bottle": "count",
        "box": "count",
        "bag": "count",
    }

    # Define base factors (would come from DB)
    base_factors = {
        # Mass (to grams)
        "g": 1.0,
        "kg": 1000.0,
        "mg": 0.001,
        "oz": 28.3495,
        "lb": 453.592,
        # Volume (to ml)
        "ml": 1.0,
        "l": 1000.0,
        "tsp": 4.92892,
        "tbsp": 14.7868,
        "cup": 236.588,
        "floz": 29.5735,
        "pt": 473.176,
        "qt": 946.353,
        "gal": 3785.41,
        # Count (to each)
        "ea": 1.0,
        "dozen": 12.0,
        "pair": 2.0,
        "head": 1.0,
        "bunch": 1.0,
        "loaf": 20.0,
        "slice": 1.0,
        "can": 1.0,
        "bottle": 1.0,
        "box": 1.0,
        "bag": 1.0,
    }

    from_category = unit_categories.get(from_unit)
    to_category = unit_categories.get(to_unit)

    if not from_category or not to_category:
        raise HTTPException(status_code=400, detail="Invalid unit ID")

    convertible = from_category == to_category

    if convertible:
        # Calculate conversion factor
        from_base = base_factors.get(from_unit, 1.0)
        to_base = base_factors.get(to_unit, 1.0)
        factor = from_base / to_base
    else:
        factor = 0.0

    return UnitConversion(
        from_unit=from_unit, to_unit=to_unit, factor=factor, convertible=convertible
    )


@router.get("/suggest-unit")
async def suggest_unit_for_item(
    item_name: str = Query(..., description="Name of the item"),
    food_category: str = Query(..., description="Food category of the item"),
):
    """Suggest the best unit for a specific item based on its name and category"""
    preferred_unit, unit_category = get_preferred_unit(food_category, item_name)

    return {
        "item_name": item_name,
        "food_category": food_category,
        "suggested_unit": preferred_unit,
        "unit_category": unit_category.value,
        "reason": f"Based on common usage for {item_name} in {food_category} category",
    }
