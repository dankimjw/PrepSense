import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/shopping-list",
    tags=["Shopping List"],
    responses={404: {"description": "Not found"}},
)

# In-memory storage for shopping list items (replace with database in production)
shopping_lists: Dict[int, List[Dict[str, Any]]] = {}


class ShoppingListItem(BaseModel):
    item_name: str = Field(..., description="Name of the item")
    quantity: Optional[float] = Field(None, description="Quantity needed")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    category: Optional[str] = Field(None, description="Category of the item")
    recipe_name: Optional[str] = Field(None, description="Associated recipe")
    added_date: Optional[datetime] = Field(default_factory=datetime.now)


class AddItemsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    items: List[ShoppingListItem] = Field(..., description="Items to add")


class RemoveItemsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    item_names: List[str] = Field(..., description="Names of items to remove")


@router.get(
    "/user/{user_id}/items", response_model=List[Dict[str, Any]], summary="Get Shopping List"
)
async def get_shopping_list(user_id: int):
    """
    Get all items in the user's shopping list.
    """
    if user_id not in shopping_lists:
        shopping_lists[user_id] = []

    return shopping_lists[user_id]


@router.post("/add-items", response_model=Dict[str, Any], summary="Add Items to Shopping List")
async def add_shopping_list_items(request: AddItemsRequest):
    """
    Add items to the user's shopping list.
    """
    try:
        if request.user_id not in shopping_lists:
            shopping_lists[request.user_id] = []

        # Convert items to dict and add to list
        for item in request.items:
            item_dict = item.dict()
            # Check if item already exists
            existing_item = next(
                (
                    x
                    for x in shopping_lists[request.user_id]
                    if x["item_name"].lower() == item.item_name.lower()
                ),
                None,
            )

            if existing_item:
                # Update quantity if item exists
                if item.quantity and existing_item.get("quantity"):
                    existing_item["quantity"] += item.quantity
                logger.info(f"Updated quantity for {item.item_name}")
            else:
                shopping_lists[request.user_id].append(item_dict)
                logger.info(f"Added {item.item_name} to shopping list")

        return {
            "message": "Items added successfully",
            "items_added": len(request.items),
            "total_items": len(shopping_lists[request.user_id]),
        }

    except Exception as e:
        logger.error(f"Error adding shopping list items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add items: {str(e)}")


@router.post(
    "/remove-items", response_model=Dict[str, Any], summary="Remove Items from Shopping List"
)
async def remove_shopping_list_items(request: RemoveItemsRequest):
    """
    Remove items from the user's shopping list.
    """
    try:
        if request.user_id not in shopping_lists:
            shopping_lists[request.user_id] = []
            return {"message": "No items to remove", "items_removed": 0}

        removed_count = 0
        for item_name in request.item_names:
            # Find and remove item
            shopping_lists[request.user_id] = [
                item
                for item in shopping_lists[request.user_id]
                if item["item_name"].lower() != item_name.lower()
            ]
            removed_count += 1

        return {
            "message": "Items removed successfully",
            "items_removed": removed_count,
            "remaining_items": len(shopping_lists[request.user_id]),
        }

    except Exception as e:
        logger.error(f"Error removing shopping list items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove items: {str(e)}")


@router.delete(
    "/user/{user_id}/clear", response_model=Dict[str, Any], summary="Clear Shopping List"
)
async def clear_shopping_list(user_id: int):
    """
    Clear all items from the user's shopping list.
    """
    try:
        if user_id in shopping_lists:
            item_count = len(shopping_lists[user_id])
            shopping_lists[user_id] = []
            return {"message": "Shopping list cleared", "items_removed": item_count}
        else:
            return {"message": "Shopping list was already empty", "items_removed": 0}

    except Exception as e:
        logger.error(f"Error clearing shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear shopping list: {str(e)}")
