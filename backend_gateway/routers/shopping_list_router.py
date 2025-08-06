import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend_gateway.config.database import get_database_service
from backend_gateway.utils.fraction_converter import format_quantity_with_fraction

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/shopping-list",
    tags=["Shopping List"],
    responses={404: {"description": "Not found"}},
)


class ShoppingListItem(BaseModel):
    item_name: str = Field(..., description="Name of the item")
    quantity: Optional[float] = Field(None, description="Quantity needed")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    category: Optional[str] = Field(None, description="Category of the item")
    recipe_name: Optional[str] = Field(None, description="Associated recipe")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_checked: Optional[bool] = Field(False, description="Whether item is checked off")
    priority: Optional[int] = Field(0, description="Priority level (0=normal, 1=high, 2=urgent)")


class AddItemsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    items: List[ShoppingListItem] = Field(..., description="Items to add")


class RemoveItemsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    item_names: List[str] = Field(..., description="Names of items to remove")


class UpdateItemRequest(BaseModel):
    is_checked: Optional[bool] = Field(None, description="Update checked status")
    quantity: Optional[float] = Field(None, description="Update quantity")
    unit: Optional[str] = Field(None, description="Update unit")
    notes: Optional[str] = Field(None, description="Update notes")
    priority: Optional[int] = Field(None, description="Update priority")


@router.get(
    "/user/{user_id}/items", response_model=List[Dict[str, Any]], summary="Get Shopping List"
)
async def get_shopping_list(user_id: int, db_service=Depends(get_database_service)):
    """
    Get all items in the user's shopping list from database.
    """
    try:
        query = """
        SELECT 
            shopping_list_item_id,
            item_name,
            quantity,
            unit,
            category,
            recipe_name,
            notes,
            is_checked,
            priority,
            added_date,
            updated_at
        FROM shopping_list_items
        WHERE user_id = @user_id
        ORDER BY 
            is_checked ASC,  -- Unchecked items first
            priority DESC,   -- Higher priority first
            added_date DESC  -- Newest first
        """

        items = db_service.execute_query(query, {"user_id": user_id})

        # Convert datetime objects to ISO format strings and format quantities as fractions
        for item in items:
            if item.get("added_date"):
                item["added_date"] = item["added_date"].isoformat()
            if item.get("updated_at"):
                item["updated_at"] = item["updated_at"].isoformat()

            # Format quantity as fraction for better readability
            if item.get("quantity") is not None:
                try:
                    # Keep original quantity for calculations
                    item["quantity_decimal"] = item["quantity"]
                    # Add user-friendly fraction display
                    item["quantity"] = format_quantity_with_fraction(item["quantity"], "")
                except (ValueError, TypeError):
                    # If conversion fails, keep original
                    pass

        return items

    except Exception as e:
        logger.error(f"Error getting shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get shopping list: {str(e)}")


@router.post("/add-items", response_model=Dict[str, Any], summary="Add Items to Shopping List")
async def add_shopping_list_items(
    request: AddItemsRequest, db_service=Depends(get_database_service)
):
    """
    Add items to the user's shopping list in database.
    """
    try:
        added_count = 0
        updated_count = 0

        for item in request.items:
            # Check if item already exists
            check_query = """
            SELECT shopping_list_item_id, quantity
            FROM shopping_list_items
            WHERE user_id = @user_id 
            AND LOWER(item_name) = LOWER(@item_name)
            AND is_checked = false
            """

            existing = db_service.execute_query(
                check_query, {"user_id": request.user_id, "item_name": item.item_name}
            )

            if existing:
                # Update quantity if item exists and quantities can be combined
                if item.quantity and existing[0].get("quantity"):
                    update_query = """
                    UPDATE shopping_list_items
                    SET quantity = quantity + @additional_quantity,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE shopping_list_item_id = @item_id
                    """

                    db_service.execute_query(
                        update_query,
                        {
                            "additional_quantity": item.quantity,
                            "item_id": existing[0]["shopping_list_item_id"],
                        },
                    )
                    updated_count += 1
                    logger.info(f"Updated quantity for {item.item_name}")
            else:
                # Insert new item
                insert_query = """
                INSERT INTO shopping_list_items (
                    user_id, item_name, quantity, unit, category, 
                    recipe_name, notes, is_checked, priority
                ) VALUES (
                    @user_id, @item_name, @quantity, @unit, @category,
                    @recipe_name, @notes, @is_checked, @priority
                )
                """

                db_service.execute_query(
                    insert_query,
                    {
                        "user_id": request.user_id,
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "unit": item.unit,
                        "category": item.category,
                        "recipe_name": item.recipe_name,
                        "notes": item.notes,
                        "is_checked": item.is_checked or False,
                        "priority": item.priority or 0,
                    },
                )
                added_count += 1
                logger.info(f"Added {item.item_name} to shopping list")

        # Get total count
        count_query = """
        SELECT COUNT(*) as total
        FROM shopping_list_items
        WHERE user_id = @user_id
        """

        total_result = db_service.execute_query(count_query, {"user_id": request.user_id})
        total_items = total_result[0]["total"] if total_result else 0

        return {
            "message": "Items processed successfully",
            "items_added": added_count,
            "items_updated": updated_count,
            "total_items": total_items,
        }

    except Exception as e:
        logger.error(f"Error adding shopping list items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add items: {str(e)}")


@router.post(
    "/remove-items", response_model=Dict[str, Any], summary="Remove Items from Shopping List"
)
async def remove_shopping_list_items(
    request: RemoveItemsRequest, db_service=Depends(get_database_service)
):
    """
    Remove items from the user's shopping list.
    """
    try:
        removed_count = 0

        for item_name in request.item_names:
            delete_query = """
            DELETE FROM shopping_list_items
            WHERE user_id = @user_id 
            AND LOWER(item_name) = LOWER(@item_name)
            """

            result = db_service.execute_query(
                delete_query, {"user_id": request.user_id, "item_name": item_name}
            )

            # Check affected rows
            if result and result[0].get("affected_rows", 0) > 0:
                removed_count += 1

        # Get remaining count
        count_query = """
        SELECT COUNT(*) as total
        FROM shopping_list_items
        WHERE user_id = @user_id
        """

        total_result = db_service.execute_query(count_query, {"user_id": request.user_id})
        remaining_items = total_result[0]["total"] if total_result else 0

        return {
            "message": "Items removed successfully",
            "items_removed": removed_count,
            "remaining_items": remaining_items,
        }

    except Exception as e:
        logger.error(f"Error removing shopping list items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove items: {str(e)}")


@router.patch(
    "/items/{item_id}", response_model=Dict[str, Any], summary="Update Shopping List Item"
)
async def update_shopping_list_item(
    item_id: int, update_data: UpdateItemRequest, db_service=Depends(get_database_service)
):
    """
    Update a specific shopping list item (e.g., mark as checked).
    """
    try:
        # Build dynamic update query
        update_fields = []
        params = {"item_id": item_id}

        if update_data.is_checked is not None:
            update_fields.append("is_checked = @is_checked")
            params["is_checked"] = update_data.is_checked

        if update_data.quantity is not None:
            update_fields.append("quantity = @quantity")
            params["quantity"] = update_data.quantity

        if update_data.unit is not None:
            update_fields.append("unit = @unit")
            params["unit"] = update_data.unit

        if update_data.notes is not None:
            update_fields.append("notes = @notes")
            params["notes"] = update_data.notes

        if update_data.priority is not None:
            update_fields.append("priority = @priority")
            params["priority"] = update_data.priority

        if not update_fields:
            return {"message": "No fields to update"}

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        update_query = f"""
        UPDATE shopping_list_items
        SET {", ".join(update_fields)}
        WHERE shopping_list_item_id = @item_id
        """

        result = db_service.execute_query(update_query, params)

        if result and result[0].get("affected_rows", 0) > 0:
            return {"message": "Item updated successfully", "item_id": item_id}
        else:
            raise HTTPException(status_code=404, detail="Item not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shopping list item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update item: {str(e)}")


@router.delete(
    "/user/{user_id}/clear", response_model=Dict[str, Any], summary="Clear Shopping List"
)
async def clear_shopping_list(user_id: int, db_service=Depends(get_database_service)):
    """
    Clear all items from the user's shopping list.
    """
    try:
        # Get count before deletion
        count_query = """
        SELECT COUNT(*) as total
        FROM shopping_list_items
        WHERE user_id = @user_id
        """

        count_result = db_service.execute_query(count_query, {"user_id": user_id})
        item_count = count_result[0]["total"] if count_result else 0

        # Delete all items
        delete_query = """
        DELETE FROM shopping_list_items
        WHERE user_id = @user_id
        """

        db_service.execute_query(delete_query, {"user_id": user_id})

        return {"message": "Shopping list cleared", "items_removed": item_count}

    except Exception as e:
        logger.error(f"Error clearing shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear shopping list: {str(e)}")


@router.get(
    "/user/{user_id}/summary", response_model=Dict[str, Any], summary="Get Shopping List Summary"
)
async def get_shopping_list_summary(user_id: int, db_service=Depends(get_database_service)):
    """
    Get summary statistics for user's shopping list.
    """
    try:
        query = """
        SELECT 
            total_items,
            unchecked_items,
            checked_items,
            last_added
        FROM user_shopping_list_summary
        WHERE user_id = @user_id
        """

        result = db_service.execute_query(query, {"user_id": user_id})

        if result:
            summary = result[0]
            if summary.get("last_added"):
                summary["last_added"] = summary["last_added"].isoformat()
            return summary
        else:
            return {"total_items": 0, "unchecked_items": 0, "checked_items": 0, "last_added": None}

    except Exception as e:
        logger.error(f"Error getting shopping list summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
