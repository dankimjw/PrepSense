"""
API endpoints for food categorization and unit validation
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_gateway.core.security import get_current_user
from backend_gateway.services.food_database_service import FoodDatabaseService
from backend_gateway.services.postgres_service import PostgresService
from backend_gateway.services.unit_validation_service import UnitValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/food", tags=["food_categorization"])


# Request/Response models
class FoodCategorizationRequest(BaseModel):
    item_name: str = Field(..., description="Name of the food item to categorize")
    brand: Optional[str] = Field(None, description="Optional brand name")


class UnitValidationRequest(BaseModel):
    item_name: str = Field(..., description="Name of the food item")
    unit: str = Field(..., description="Unit to validate")
    quantity: Optional[float] = Field(None, description="Optional quantity for context")


class UnitConversionRequest(BaseModel):
    item_name: str = Field(..., description="Name of the food item")
    amount: float = Field(..., description="Amount to convert")
    from_unit: str = Field(..., description="Source unit")
    to_unit: str = Field(..., description="Target unit")


class UserCorrectionRequest(BaseModel):
    item_name: str = Field(..., description="Name of the food item")
    corrected_category: Optional[str] = Field(None, description="Corrected category")
    corrected_unit: Optional[str] = Field(None, description="Corrected unit")


class BatchCategorizationRequest(BaseModel):
    items: list[FoodCategorizationRequest] = Field(..., description="List of items to categorize")


class FoodSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    include_nutrition: bool = Field(False, description="Include nutrition information")
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")


# Dependency to get services
async def get_food_service():
    """Get food database service instance"""
    db_service = PostgresService()
    return FoodDatabaseService(db_service)


async def get_unit_service():
    """Get unit validation service instance"""
    db_service = PostgresService()
    return UnitValidationService(db_service)


@router.post("/categorize")
async def categorize_food_item(
    request: FoodCategorizationRequest,
    food_service: FoodDatabaseService = Depends(get_food_service),
) -> dict[str, Any]:
    """
    Categorize a food item and get allowed units.

    This endpoint uses multiple food databases with fallback to provide:
    - Food category (produce, dairy, snacks, etc.)
    - Allowed units for the item
    - Confidence score
    - Data source used
    """
    try:
        result = await food_service.categorize_food_item(request.item_name, request.brand)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error categorizing food item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/categorize/batch")
async def categorize_food_items_batch(
    request: BatchCategorizationRequest,
    food_service: FoodDatabaseService = Depends(get_food_service),
) -> dict[str, Any]:
    """
    Categorize multiple food items in a single request.

    Useful for bulk operations like processing detected items.
    """
    try:
        results = []
        errors = []

        for item in request.items:
            try:
                result = await food_service.categorize_food_item(item.item_name, item.brand)
                results.append({"item_name": item.item_name, "brand": item.brand, "result": result})
            except Exception as e:
                errors.append({"item_name": item.item_name, "error": str(e)})

        return {
            "success": True,
            "categorized": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors if errors else None,
        }
    except Exception as e:
        logger.error(f"Error in batch categorization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/validate-unit")
async def validate_unit(
    request: UnitValidationRequest, unit_service: UnitValidationService = Depends(get_unit_service)
) -> dict[str, Any]:
    """
    Validate if a unit is appropriate for a food item.

    Returns:
    - Whether the unit is valid
    - Suggestions for better units
    - Warning messages for edge cases
    - Conversion suggestions
    """
    try:
        result = await unit_service.validate_unit(request.item_name, request.unit, request.quantity)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error validating unit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/suggest-unit")
async def suggest_unit(
    item_name: str = Query(..., description="Name of the food item"),
    context: Optional[str] = Query(None, description="Usage context: shopping, recipe, or storage"),
    unit_service: UnitValidationService = Depends(get_unit_service),
) -> dict[str, Any]:
    """
    Get the best unit suggestion for a food item.

    Context can be:
    - shopping: Units commonly used in stores
    - recipe: Precise measurements for cooking
    - storage: Container-based units
    """
    try:
        result = await unit_service.suggest_best_unit(item_name, context)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error suggesting unit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/convert-unit")
async def convert_unit(
    request: UnitConversionRequest, unit_service: UnitValidationService = Depends(get_unit_service)
) -> dict[str, Any]:
    """
    Convert between units for a specific food item.

    Uses food-specific conversion factors when available,
    falls back to standard conversions.
    """
    try:
        result = await unit_service.convert_unit(
            request.item_name, request.amount, request.from_unit, request.to_unit
        )

        if result and not result.get("error"):
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result.get("error", "Conversion not possible")}
    except Exception as e:
        logger.error(f"Error converting unit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/user-correction")
async def record_user_correction(
    request: UserCorrectionRequest,
    current_user: dict = Depends(get_current_user),
    food_service: FoodDatabaseService = Depends(get_food_service),
) -> dict[str, Any]:
    """
    Record a user correction for food categorization or unit.

    This helps improve the system over time by learning from user feedback.
    """
    try:
        await food_service.record_user_correction(
            current_user["user_id"],
            request.item_name,
            request.corrected_category,
            request.corrected_unit,
        )

        return {"success": True, "message": "Correction recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording correction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/search")
async def search_food_items(
    query: str = Query(..., description="Search query"),
    data_source: Optional[str] = Query(None, description="Specific data source to use"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    food_service: FoodDatabaseService = Depends(get_food_service),
) -> dict[str, Any]:
    """
    Search for food items across multiple databases.

    Data sources: usda, spoonacular, openfoodfacts, or None for all
    """
    try:
        # This would be implemented to search across databases
        # For now, return a placeholder
        return {
            "success": True,
            "query": query,
            "results": [],
            "message": "Search endpoint implementation pending",
        }
    except Exception as e:
        logger.error(f"Error searching food items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats/api-usage")
async def get_api_usage_stats(
    current_user: dict = Depends(get_current_user),
    food_service: FoodDatabaseService = Depends(get_food_service),
) -> dict[str, Any]:
    """
    Get API usage statistics (admin only).

    Shows current usage levels for each integrated food database.
    """
    try:
        # Check if user is admin
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Query the api_usage_stats view
        db_service = food_service.db_service
        query = "SELECT * FROM api_usage_stats"
        results = db_service.execute_query(query)

        return {"success": True, "stats": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stats/corrections")
async def get_correction_stats(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: dict = Depends(get_current_user),
    food_service: FoodDatabaseService = Depends(get_food_service),
) -> dict[str, Any]:
    """
    Get most corrected food items (admin only).

    Helps identify items that need better categorization.
    """
    try:
        # Check if user is admin
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        # Query the most_corrected_foods view
        db_service = food_service.db_service
        query = f"SELECT * FROM most_corrected_foods LIMIT {limit}"
        results = db_service.execute_query(query)

        return {"success": True, "corrections": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting correction stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/common-units/{category}")
async def get_common_units_for_category(
    category: str, unit_service: UnitValidationService = Depends(get_unit_service)
) -> dict[str, Any]:
    """
    Get common units used for a food category.

    Categories: produce_countable, produce_bulk, dairy, meat_seafood,
               dry_goods, bread_bakery, beverages, snacks, condiments
    """
    try:
        # Get unit suggestions for the category
        suggestions = unit_service._get_unit_suggestions_by_category(category, "")

        return {
            "success": True,
            "category": category,
            "primary_unit": suggestions.get("primary"),
            "alternatives": suggestions.get("alternatives", []),
            "reasoning": suggestions.get("reasoning", ""),
        }
    except Exception as e:
        logger.error(f"Error getting units for category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
