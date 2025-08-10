import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

# Import RemoteControl
from backend_gateway.RemoteControl_7 import is_recipe_completion_mock_enabled, set_mock

# Set up logging
logger = logging.getLogger(__name__)

# Mock data flag for recipe completion - DEPRECATED, use RemoteControl instead
use_mock_recipe_completion = False

# Mock response for recipe completion
MOCK_RECIPE_COMPLETION_RESPONSE = {
    "message": "Recipe completed successfully",
    "recipe_name": "Test Recipe",
    "updated_items": [
        {
            "item_name": "Trader Joe's Italian Linguine Pasta",
            "pantry_item_id": 1,
            "previous_quantity": 16.0,
            "new_quantity": 14.0,
            "used_quantity": 2.0,
            "unit": "oz",
            "match_score": 100,
        },
        {
            "item_name": "Trader Joe's Organic Joe's O's Pasta",
            "pantry_item_id": 2,
            "previous_quantity": 15.0,
            "new_quantity": 13.5,
            "used_quantity": 1.5,
            "unit": "oz",
            "match_score": 95,
        },
    ],
    "missing_items": [],
    "insufficient_items": [],
    "errors": [],
    "summary": "Updated 2 items",
}

from datetime import date, datetime

# Model for creating a pantry item
from pydantic import BaseModel, ConfigDict, Field

from backend_gateway.config.database import get_database_service, get_pantry_service

# Security imports
# User and Auth related imports
# Service imports
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.recipe_completion_service import RecipeCompletionService

# Set up logging
logger = logging.getLogger(__name__)

# Mock data flag for recipe completion
use_mock_recipe_completion = False

# Mock response for recipe completion
MOCK_RECIPE_COMPLETION_RESPONSE = {
    "message": "Recipe completed successfully",
    "recipe_name": "Test Recipe",
    "updated_items": [
        {
            "item_name": "Trader Joe's Italian Linguine Pasta",
            "pantry_item_id": 1,
            "previous_quantity": 16.0,
            "new_quantity": 14.0,
            "used_quantity": 2.0,
            "unit": "oz",
            "match_score": 100,
        },
        {
            "item_name": "Trader Joe's Organic Joe's O's Pasta",
            "pantry_item_id": 2,
            "previous_quantity": 15.0,
            "new_quantity": 13.5,
            "used_quantity": 1.5,
            "unit": "oz",
            "match_score": 95,
        },
    ],
    "missing_items": [],
    "insufficient_items": [],
    "errors": [],
    "summary": "Updated 2 items",
}


class PantryItemCreate(BaseModel):
    product_name: str = Field(..., example="Whole Milk", description="Name of the product.")
    quantity: float = Field(
        ..., ge=0, example=1.0, description="Quantity of the item. 0 means the item is depleted."
    )
    unit_of_measurement: str = Field(
        ..., example="gallon", description="Unit of measurement (e.g., kg, lbs, gallon, liter)."
    )
    expiration_date: Optional[date] = Field(None, description="Expiration date of the item.")
    purchase_date: Optional[date] = Field(None, description="Date the item was purchased.")
    unit_price: Optional[float] = Field(
        None, ge=0, example=3.50, description="Price per unit of the item."
    )
    category: Optional[str] = Field(None, example="Dairy", description="Category of the product.")
    # product_id: Optional[str] = Field(None, description="Optional ID linking to a master products table.")
    # pantry_id: Optional[str] = Field(None, description="Optional ID if user has multiple pantries; service might handle default.")

    model_config = ConfigDict(from_attributes=True)


class PantryItemConsumption(BaseModel):
    quantity_amount: float = Field(..., ge=0, description="New quantity amount after consumption")
    used_quantity: Optional[float] = Field(None, description="Total amount that has been used")

    model_config = ConfigDict(from_attributes=True)


class RecipeIngredient(BaseModel):
    ingredient_name: str = Field(..., description="Name of the ingredient")
    quantity: Optional[float] = Field(
        None, description="Quantity to subtract (if not provided, subtract all)"
    )
    unit: Optional[str] = Field(None, description="Unit of measurement")


class RecipeCompletionRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user")
    recipe_name: str = Field(..., description="Name of the completed recipe")
    ingredients: list[RecipeIngredient] = Field(..., description="List of ingredients to subtract")


class UserPantryItem(BaseModel):
    user_id: int
    user_name: str
    pantry_id: int
    pantry_item_id: int
    quantity: float
    unit_of_measurement: str
    expiration_date: Optional[date]
    unit_price: Optional[float]
    total_price: Optional[float]
    pantry_item_created_at: Optional[datetime]
    used_quantity: Optional[float]
    status: Optional[str]
    product_id: Optional[int]
    product_name: Optional[str]
    brand_name: Optional[str]
    food_category: Optional[str]
    upc_code: Optional[str]
    product_created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(
    prefix="/pantry",
    tags=["Pantry"],
    responses={404: {"description": "Not found"}},
)


# Dependency for PantryService - now uses database config
def get_pantry_service_dep() -> PantryService:
    return get_pantry_service()


@router.get(
    "/user/{user_id}/items", response_model=list[UserPantryItem], summary="Get User's Pantry Items"
)
async def get_user_pantry_items(
    user_id: int, pantry_service: PantryService = Depends(get_pantry_service_dep)
):
    """
    Get all pantry items for a specific user from the user_pantry_full view.

    Args:
        user_id: The ID of the user whose pantry items to retrieve
        pantry_service: The pantry service instance

    Returns:
        List of UserPantryItem objects containing all pantry details

    Raises:
        HTTPException: If there's an error retrieving items
    """
    try:
        logger.info(f"Fetching pantry items for user {user_id}")
        items = await pantry_service.get_user_pantry_items(user_id)
        logger.info(f"Found {len(items)} pantry items for user {user_id}")
        return items
    except Exception as e:
        logger.error(f"Error retrieving pantry items for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve pantry items: {str(e)}"
        ) from e


@router.post(
    "/user/{user_id}/items",
    response_model=dict[str, Any],
    status_code=201,
    summary="Add Item to Specific User's Pantry",
)
async def add_pantry_item_for_specific_user(
    user_id: int,
    item_data: PantryItemCreate,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
):
    """
    Adds a new item to the pantry for a specific user.

    Args:
        user_id: The ID of the user to add the item for
        item_data: The pantry item data
        pantry_service: The pantry service instance

    Returns:
        The newly created pantry item
    """
    try:
        # Basic unit validation - check for common invalid combinations
        unit_lower = item_data.unit_of_measurement.lower().strip()
        item_lower = item_data.product_name.lower()

        # Simple validation rules
        liquid_units = [
            "ml",
            "l",
            "liter",
            "milliliter",
            "gallon",
            "quart",
            "pint",
            "fluid ounce",
            "fl oz",
        ]
        solid_items = ["bread", "cookie", "chip", "cracker", "cake", "sandwich", "bar"]

        # Check if solid item is being measured with liquid unit
        if any(solid in item_lower for solid in solid_items) and unit_lower in liquid_units:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": f"Solid items like {item_data.product_name} cannot be measured in liquid units",
                    "suggestions": ["each", "piece", "loaf", "slice", "g", "oz", "lb"],
                    "allowed_units": [
                        "each",
                        "piece",
                        "loaf",
                        "slice",
                        "g",
                        "oz",
                        "lb",
                        "package",
                        "bag",
                    ],
                },
            )

        new_item = await pantry_service.add_pantry_item(item_data=item_data, user_id=user_id)
        return new_item
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        logger.error(f"Error adding pantry item for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add pantry item: {str(e)}") from e


@router.post(
    "/items", response_model=dict[str, Any], status_code=201, summary="Add Item to User's Pantry"
)
async def add_pantry_item_for_user(
    item_data: PantryItemCreate, pantry_service: PantryService = Depends(get_pantry_service_dep)
):
    """
    Adds a new item to the pantry for a hardcoded user (ID 111).
    The `PantryService.add_pantry_item` method is currently a placeholder
    and will need full implementation for actual database insertion.
    """
    numeric_user_id = 111  # TEMPORARY: Hardcode for user 111

    try:
        # Basic unit validation - check for common invalid combinations
        unit_lower = item_data.unit_of_measurement.lower().strip()
        item_lower = item_data.product_name.lower()

        # Simple validation rules
        liquid_units = [
            "ml",
            "l",
            "liter",
            "milliliter",
            "gallon",
            "quart",
            "pint",
            "fluid ounce",
            "fl oz",
        ]
        solid_items = ["bread", "cookie", "chip", "cracker", "cake", "sandwich", "bar"]

        # Check if solid item is being measured with liquid unit
        if any(solid in item_lower for solid in solid_items) and unit_lower in liquid_units:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": f"Solid items like {item_data.product_name} cannot be measured in liquid units",
                    "suggestions": ["each", "piece", "loaf", "slice", "g", "oz", "lb"],
                    "allowed_units": [
                        "each",
                        "piece",
                        "loaf",
                        "slice",
                        "g",
                        "oz",
                        "lb",
                        "package",
                        "bag",
                    ],
                },
            )

        new_item = await pantry_service.add_pantry_item(
            item_data=item_data, user_id=numeric_user_id
        )
        return new_item
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as ve:  # Example: if service validates and raises ValueError
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as e:
        # Log the exception for server-side diagnostics
        logger.error(f"Error adding pantry item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add pantry item: {str(e)}") from e


@router.get("/user/{user_id}/full", response_model=list[dict[str, Any]])
async def get_user_pantry_full(user_id: int = 111, db_service=Depends(get_database_service)):
    """
    Get the user's full pantry view ordered by expiration date.
    Uses the user_pantry_full table which likely contains joined data.
    """
    try:
        # The query to get the full user pantry view
        query = """
            SELECT
                pi.*,
                p.user_id
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            WHERE p.user_id = %(user_id)s
            ORDER BY pi.expiration_date ASC
        """

        params = {"user_id": user_id}

        # Execute the query and return results
        return db_service.execute_query(query, params)

    except Exception as e:
        logger.error(f"Error retrieving user pantry full view: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving pantry items: {str(e)}"
        ) from e


@router.put("/items/{item_id}", response_model=dict[str, Any], summary="Update Pantry Item")
async def update_pantry_item(
    item_id: str,
    item_data: PantryItemCreate,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
):
    """
    Update an existing pantry item.

    Args:
        item_id: The ID of the pantry item to update
        item_data: The updated pantry item data
        pantry_service: The pantry service instance

    Returns:
        The updated pantry item

    Raises:
        HTTPException: If the item is not found or update fails
    """
    try:
        updated_item = await pantry_service.update_pantry_item(
            pantry_item_id=int(item_id), item_data=item_data
        )
        if not updated_item:
            raise HTTPException(status_code=404, detail=f"Pantry item {item_id} not found")
        return updated_item
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except HTTPException:
        raise  # Re-raise HTTPException as is
    except Exception as e:
        logger.error(f"Error updating pantry item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update pantry item: {str(e)}"
        ) from e


@router.patch(
    "/items/{item_id}/consume", response_model=dict[str, Any], summary="Update Item Consumption"
)
async def consume_pantry_item(
    item_id: str,
    consumption_data: PantryItemConsumption,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
    db_service=Depends(get_database_service),
):
    """
    Update the consumption of a pantry item.

    Args:
        item_id: The ID of the pantry item to update
        consumption_data: The consumption data (new quantity and used quantity)
        pantry_service: The pantry service instance

    Returns:
        Success message with updated quantities

    Raises:
        HTTPException: If the item is not found or update fails
    """
    try:
        # Update the pantry_items table with new quantity
        params = {
            "quantity_amount": consumption_data.quantity_amount,
            "used_quantity": consumption_data.used_quantity or 0,
            "item_id": int(item_id),
        }

        # Execute the update using SQL query
        update_query = """
        UPDATE pantry_items
        SET
            quantity = %(quantity_amount)s,
            used_quantity = %(used_quantity)s,
            updated_at = CURRENT_TIMESTAMP
        WHERE pantry_item_id = %(item_id)s
        """

        result = db_service.execute_query(update_query, params)

        # Check if any rows were updated
        if not result or result[0].get("affected_rows", 0) == 0:
            raise HTTPException(status_code=404, detail=f"Pantry item {item_id} not found")

        return {
            "message": "Item consumption updated successfully",
            "item_id": item_id,
            "new_quantity": consumption_data.quantity_amount,
            "total_used": consumption_data.used_quantity,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item consumption {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update item consumption: {str(e)}"
        ) from e


@router.delete(
    "/items/{item_id}", response_model=dict[str, Any], summary="Delete Single Pantry Item"
)
async def delete_pantry_item(
    item_id: str, pantry_service: PantryService = Depends(get_pantry_service_dep)
):
    """
    Delete a single pantry item by ID.

    Args:
        item_id: The ID of the pantry item to delete
        pantry_service: The pantry service instance

    Returns:
        A status message confirming deletion

    Raises:
        HTTPException: If the item is not found or deletion fails
    """
    try:
        result = await pantry_service.delete_single_pantry_item(pantry_item_id=int(item_id))
        if not result:
            raise HTTPException(status_code=404, detail=f"Pantry item {item_id} not found")
        return {"message": f"Pantry item {item_id} deleted successfully", "id": item_id}
    except HTTPException:
        raise  # Re-raise HTTPException as is
    except Exception as e:
        logger.error(f"Error deleting pantry item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete pantry item: {str(e)}"
        ) from e


@router.delete("/user/{user_id}/items", response_model=dict[str, Any])
async def delete_user_pantry_items(
    user_id: int = 111,
    hours_ago: Optional[int] = None,
    delete_all: bool = False,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
):
    """
    Delete pantry items for a specific user.

    For demo purposes, this endpoint allows removing recently added items to prevent
    accumulation of duplicate items when testing vision detection and item adding features.

    Args:
        user_id: The ID of the user whose pantry items to delete (defaults to 111 for demo)
        hours_ago: If provided, only delete items added within the last X hours
        delete_all: If True, delete all items for this user (overrides hours_ago)
        pantry_service: The pantry service instance

    Returns:
        A status message and count of deleted items
    """
    try:
        result = await pantry_service.delete_user_pantry_items(
            user_id=user_id, hours_ago=hours_ago, delete_all=delete_all
        )
        return result
    except Exception as e:
        logger.error(f"Error deleting user pantry items: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting pantry items: {str(e)}") from e


@router.post(
    "/recipe/complete",
    response_model=dict[str, Any],
    summary="Complete Recipe and Subtract Ingredients",
)
async def complete_recipe(
    request: RecipeCompletionRequest,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
    db_service=Depends(get_database_service),
):
    """
    Complete a recipe and subtract the used ingredients from the user's pantry.

    Args:
        request: The recipe completion request with user ID, recipe name, and ingredients
        pantry_service: The pantry service instance
        db_service: The BigQuery service instance

    Returns:
        Success message with details about updated items

    Raises:
        HTTPException: If there's an error updating the pantry
    """
    try:
        # Validate ingredients are provided and not empty
        if not request.ingredients or len(request.ingredients) == 0:
            raise HTTPException(status_code=422, detail="No ingredients provided in the request")

        # Validate each ingredient
        for idx, ingredient in enumerate(request.ingredients):
            if not ingredient.ingredient_name:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid ingredient at index {idx}: missing ingredient_name",
                )

        # If mock data flag is set, return mock response
        if is_recipe_completion_mock_enabled():
            logger.info("Using mock data for recipe completion")
            mock_response = MOCK_RECIPE_COMPLETION_RESPONSE.copy()
            mock_response["recipe_name"] = request.recipe_name
            return mock_response

        # Get the user's current pantry items
        user_items = await pantry_service.get_user_pantry_items(request.user_id)

        if not user_items:
            logger.warning(f"No pantry items found for user {request.user_id}")
            return {
                "message": "No pantry items to update",
                "recipe_name": request.recipe_name,
                "updated_items": [],
                "missing_items": [ing.ingredient_name for ing in request.ingredients],
                "insufficient_items": [],
                "summary": "No pantry items found",
            }

        updated_items = []
        missing_items = []
        insufficient_items = []
        errors = []

        for ingredient in request.ingredients:
            try:
                # Convert ingredient to dict format for the service
                ingredient_dict = {
                    "ingredient_name": ingredient.ingredient_name,
                    "quantity": ingredient.quantity,
                    "unit": ingredient.unit,
                }

                # Find matching items using the new service
                matching_items = RecipeCompletionService.match_ingredient_to_pantry(
                    ingredient.ingredient_name, user_items
                )

                # Process consumption with unit conversion support
                consumption_result = RecipeCompletionService.process_ingredient_consumption(
                    ingredient_dict, matching_items, db_service
                )

                # Handle results
                if consumption_result["missing"]:
                    missing_items.append(
                        {
                            "ingredient": ingredient.ingredient_name,
                            "reason": "Not found in pantry",
                            "requested_quantity": ingredient.quantity,
                            "requested_unit": ingredient.unit,
                        }
                    )
                elif consumption_result["insufficient"]:
                    total_consumed = sum(
                        item["quantity_used"] for item in consumption_result["consumed_items"]
                    )
                    insufficient_items.append(
                        {
                            "ingredient": ingredient.ingredient_name,
                            "needed": ingredient.quantity,
                            "needed_unit": ingredient.unit,
                            "consumed": total_consumed,
                            "remaining_needed": consumption_result.get("remaining_needed"),
                            "warnings": consumption_result.get("warnings", []),
                        }
                    )

                # Add consumed items to updated list
                for consumed in consumption_result["consumed_items"]:
                    update_info = {
                        "item_name": consumed["item_name"],
                        "pantry_item_id": consumed["pantry_item_id"],
                        "previous_quantity": consumed["previous_quantity"],
                        "new_quantity": consumed["new_quantity"],
                        "used_quantity": consumed["quantity_used"],
                        "unit": consumed["unit"],
                        "match_score": consumed.get("match_score", 0),
                    }

                    if "conversion_details" in consumed:
                        update_info["conversion_details"] = consumed["conversion_details"]

                    updated_items.append(update_info)

                # Collect any warnings
                if consumption_result.get("warnings"):
                    for warning in consumption_result["warnings"]:
                        errors.append(f"{ingredient.ingredient_name}: {warning}")

            except Exception as e:
                logger.error(f"Error processing ingredient {ingredient.ingredient_name}: {str(e)}")
                errors.append(f"Error with {ingredient.ingredient_name}: {str(e)}")

        # Log the recipe completion
        logger.info(f"Recipe '{request.recipe_name}' completed for user {request.user_id}")
        logger.info(
            f"Updated {len(updated_items)} items, {len(missing_items)} missing, {len(insufficient_items)} insufficient"
        )

        # Create summary message
        summary_parts = []
        if updated_items:
            summary_parts.append(f"Updated {len(updated_items)} items")
        if insufficient_items:
            summary_parts.append(f"{len(insufficient_items)} items had insufficient quantity")
        if missing_items:
            summary_parts.append(f"{len(missing_items)} items not found")

        return {
            "message": (
                "Recipe completed successfully"
                if updated_items
                else "Recipe completed with warnings"
            ),
            "recipe_name": request.recipe_name,
            "updated_items": updated_items,
            "missing_items": missing_items,
            "insufficient_items": insufficient_items,
            "errors": errors,
            "summary": ". ".join(summary_parts) if summary_parts else "No items were updated",
        }

    except Exception as e:
        logger.error(f"Error completing recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete recipe: {str(e)}") from e


@router.post(
    "/revert-changes", response_model=dict[str, Any], summary="Revert Recent Pantry Changes"
)
async def revert_pantry_changes(
    user_id: int = 111,
    hours_ago: Optional[float] = None,
    minutes_ago: Optional[float] = None,
    include_recipe_changes: bool = True,
    include_additions: bool = True,
    db_service=Depends(get_database_service),
):
    """
    Revert recent pantry changes including recipe subtractions.

    This enhanced version can:
    - Revert items added within X hours/minutes
    - Revert quantity changes from recipe completions
    - Selectively revert only certain types of changes

    Args:
        user_id: The user whose changes to revert
        hours_ago: Revert changes from the last X hours
        minutes_ago: Revert changes from the last X minutes (overrides hours_ago)
        include_recipe_changes: If True, revert recipe-related quantity changes
        include_additions: If True, revert newly added items

    Returns:
        Summary of reverted changes
    """
    try:
        # Calculate the cutoff time
        if minutes_ago:
            cutoff_query = f"CURRENT_TIMESTAMP - INTERVAL '{int(minutes_ago)} minutes'"
        elif hours_ago:
            cutoff_query = f"CURRENT_TIMESTAMP - INTERVAL '{int(hours_ago)} hours'"
        else:
            # Default to last hour
            cutoff_query = "CURRENT_TIMESTAMP - INTERVAL '1 hour'"

        deleted_items = []
        restored_quantities = []

        # 1. Handle newly added items if requested
        if include_additions:
            # Get pantry IDs for the user
            pantry_query = """
            SELECT pantry_id
            FROM pantries
            WHERE user_id = %(user_id)s
            """
            pantry_results = db_service.execute_query(pantry_query, {"user_id": user_id})

            if pantry_results:
                pantry_ids = [row["pantry_id"] for row in pantry_results]

                # Find items to delete
                items_query = f"""
                SELECT pantry_item_id, product_name, quantity, created_at
                FROM pantry_items
                WHERE pantry_id = ANY(%(pantry_ids)s)
                AND created_at >= {cutoff_query}
                """

                items_to_delete = db_service.execute_query(items_query, {"pantry_ids": pantry_ids})

                # Delete the items
                if items_to_delete:
                    item_ids = [item["pantry_item_id"] for item in items_to_delete]

                    delete_query = """
                    DELETE FROM pantry_items
                    WHERE pantry_item_id = ANY(%(item_ids)s)
                    """

                    db_service.execute_query(delete_query, {"item_ids": item_ids})

                    # Also delete from products table - Skip this for PostgreSQL
                    # In PostgreSQL, products are part of pantry_items table
                    # delete_products_query = """
                    # DELETE FROM products
                    # WHERE pantry_item_id = ANY(%(item_ids)s)
                    # """

                    # db_service.execute_query(delete_products_query, {"item_ids": item_ids})

                    deleted_items = [
                        {
                            "item_id": item["pantry_item_id"],
                            "name": item["product_name"],
                            "quantity": item["quantity"],
                            "added_at": str(item["created_at"]),
                        }
                        for item in items_to_delete
                    ]

        # 2. Handle recipe-related quantity changes if requested
        if include_recipe_changes:
            # Find items that were modified (not created) within the time window
            modified_query = f"""
            SELECT
                pi.pantry_item_id,
                pi.product_name,
                pi.quantity as current_quantity,
                pi.used_quantity,
                pi.created_at,
                pi.updated_at
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            WHERE p.user_id = %(user_id)s
            AND pi.updated_at >= {cutoff_query}
            AND pi.updated_at > pi.created_at  -- Only items that were modified after creation
            AND pi.used_quantity > 0  -- Items that have been used
            """

            modified_items = db_service.execute_query(modified_query, {"user_id": user_id})

            # Restore quantities by adding back the used amount
            for item in modified_items:
                restored_quantity = item["current_quantity"] + (item["used_quantity"] or 0)

                restore_query = """
                UPDATE pantry_items
                SET
                    quantity = %(restored_quantity)s,
                    used_quantity = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE pantry_item_id = %(item_id)s
                """

                db_service.execute_query(
                    restore_query,
                    {"restored_quantity": restored_quantity, "item_id": item["pantry_item_id"]},
                )

                restored_quantities.append(
                    {
                        "item_id": item["pantry_item_id"],
                        "name": item["product_name"],
                        "previous_quantity": item["current_quantity"],
                        "restored_quantity": restored_quantity,
                        "amount_restored": item["used_quantity"],
                    }
                )

        # Create summary
        time_desc = (
            f"{minutes_ago} minutes"
            if minutes_ago
            else f"{hours_ago} hours" if hours_ago else "1 hour"
        )

        return {
            "message": f"Successfully reverted pantry changes from the last {time_desc}",
            "deleted_items": deleted_items,
            "restored_quantities": restored_quantities,
            "summary": {
                "items_deleted": len(deleted_items),
                "quantities_restored": len(restored_quantities),
                "total_changes_reverted": len(deleted_items) + len(restored_quantities),
            },
        }

    except Exception as e:
        logger.error(f"Error reverting pantry changes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to revert changes: {str(e)}") from e


class MockRecipeCompletionConfig(BaseModel):
    use_mock_data: bool


@router.post("/configure-mock-recipe-completion", summary="Toggle mock data for recipe completion")
async def configure_mock_recipe_completion(config: MockRecipeCompletionConfig):
    """Toggle the use of mock data for recipe completion"""
    # Update RemoteControl instead of local variable
    set_mock("recipe_completion", config.use_mock_data, "pantry_router")
    logger.info(f"Mock recipe completion data {'enabled' if config.use_mock_data else 'disabled'}")
    return {
        "success": True,
        "use_mock_data": use_mock_recipe_completion,
        "message": f"Mock recipe completion data {'enabled' if use_mock_recipe_completion else 'disabled'}",
    }


@router.delete("/cleanup-trader-joes-items", summary="Remove all Trader Joe's items from pantry")
async def cleanup_trader_joes_items(user_id: int = 111, db_service=Depends(get_database_service)):
    """
    Remove all Trader Joe's items from the user's pantry.
    This helps clean up test data that may have been accidentally saved.
    """
    try:
        # First, get all Trader Joe's items for the user
        query = """
        SELECT pi.pantry_item_id, pi.product_name, pi.quantity
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = %(user_id)s
        AND LOWER(pi.product_name) LIKE %(pattern)s
        """

        trader_joes_items = db_service.execute_query(
            query, {"user_id": user_id, "pattern": "%trader joe%"}
        )

        if not trader_joes_items:
            return {
                "success": True,
                "deleted_count": 0,
                "message": "No Trader Joe's items found in pantry",
            }

        # Delete the items
        item_ids = [item["pantry_item_id"] for item in trader_joes_items]

        delete_query = """
        DELETE FROM pantry_items
        WHERE pantry_item_id IN %(item_ids)s
        """

        db_service.execute_query(delete_query, {"item_ids": tuple(item_ids)})

        # Return details of what was deleted
        deleted_items = [
            {
                "id": item["pantry_item_id"],
                "name": item["product_name"],
                "quantity": item["quantity"],
            }
            for item in trader_joes_items
        ]

        logger.info(f"Deleted {len(deleted_items)} Trader Joe's items for user {user_id}")

        return {
            "success": True,
            "deleted_count": len(deleted_items),
            "deleted_items": deleted_items,
            "message": f"Successfully deleted {len(deleted_items)} Trader Joe's items",
        }

    except Exception as e:
        logger.error(f"Error cleaning up Trader Joe's items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup items: {str(e)}") from e
