import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Any, Dict, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Security imports
from backend_gateway.core.security import oauth2_scheme_optional, get_current_user

# User and Auth related imports
from backend_gateway.models.user import UserInDB
from backend_gateway.routers.users import get_current_active_user

# Service imports
from backend_gateway.services.bigquery_service import BigQueryService
from backend_gateway.services.pantry_service import PantryService

# Model for creating a pantry item
from pydantic import BaseModel, Field
from datetime import date, datetime

# Set up logging
logger = logging.getLogger(__name__)

class PantryItemCreate(BaseModel):
    product_name: str = Field(..., example="Whole Milk", description="Name of the product.")
    quantity: float = Field(..., gt=0, example=1.0, description="Quantity of the item.")
    unit_of_measurement: str = Field(..., example="gallon", description="Unit of measurement (e.g., kg, lbs, gallon, liter).")
    expiration_date: Optional[date] = Field(None, description="Expiration date of the item.")
    purchase_date: Optional[date] = Field(None, description="Date the item was purchased.")
    unit_price: Optional[float] = Field(None, ge=0, example=3.50, description="Price per unit of the item.")
    category: Optional[str] = Field(None, example="Dairy", description="Category of the product.")
    # product_id: Optional[str] = Field(None, description="Optional ID linking to a master products table.")
    # pantry_id: Optional[str] = Field(None, description="Optional ID if user has multiple pantries; service might handle default.")

    class Config:
        from_attributes = True


class PantryItemConsumption(BaseModel):
    quantity_amount: float = Field(..., ge=0, description="New quantity amount after consumption")
    used_quantity: Optional[float] = Field(None, description="Total amount that has been used")
    
    class Config:
        from_attributes = True


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
    used_quantity: Optional[int]
    status: Optional[str]
    product_id: Optional[int]
    product_name: Optional[str]
    brand_name: Optional[str]
    food_category: Optional[str]
    upc_code: Optional[str]
    product_created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


router = APIRouter(
    prefix="/pantry",
    tags=["Pantry"],
    responses={404: {"description": "Not found"}},
)

# Dependency for BigQueryService
def get_bigquery_service() -> BigQueryService:
    return BigQueryService()

# Dependency for PantryService
def get_pantry_service(bq_service: BigQueryService = Depends(get_bigquery_service)) -> PantryService:
    return PantryService(bq_service=bq_service)

@router.get("/user/{user_id}/items", response_model=List[UserPantryItem], summary="Get User's Pantry Items")
async def get_user_pantry_items(
    user_id: int,
    pantry_service: PantryService = Depends(get_pantry_service)
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
        items = await pantry_service.get_user_pantry_items(user_id)
        return items
    except Exception as e:
        logger.error(f"Error retrieving pantry items for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve pantry items: {str(e)}"
        )

@router.post("/user/{user_id}/items", response_model=Dict[str, Any], status_code=201, summary="Add Item to Specific User's Pantry")
async def add_pantry_item_for_specific_user(
    user_id: int,
    item_data: PantryItemCreate,
    pantry_service: PantryService = Depends(get_pantry_service)
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
        new_item = await pantry_service.add_pantry_item(item_data=item_data, user_id=user_id)
        return new_item 
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error adding pantry item for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add pantry item: {str(e)}")

@router.post("/items", response_model=Dict[str, Any], status_code=201, summary="Add Item to User's Pantry")
async def add_pantry_item_for_user(
    item_data: PantryItemCreate,
    pantry_service: PantryService = Depends(get_pantry_service)
):
    """
    Adds a new item to the pantry for a hardcoded user (ID 111).
    The `PantryService.add_pantry_item` method is currently a placeholder
    and will need full implementation for actual database insertion.
    """
    numeric_user_id = 111  # TEMPORARY: Hardcode for user 111
        
    try:
        new_item = await pantry_service.add_pantry_item(item_data=item_data, user_id=numeric_user_id)
        return new_item 
    except ValueError as ve: # Example: if service validates and raises ValueError
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log the exception for server-side diagnostics
        logger.error(f"Error adding pantry item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add pantry item: {str(e)}")

@router.get("/user/{user_id}/full", response_model=List[Dict[str, Any]])
async def get_user_pantry_full(user_id: int = 111, bq: BigQueryService = Depends(get_bigquery_service)):
    """
    Get the user's full pantry view ordered by expiration date.
    Uses the user_pantry_full table which likely contains joined data.
    """
    try:
        # The query to get the full user pantry view
        query = """
            SELECT *
            FROM
              `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
            WHERE
              user_id = @user_id
            ORDER BY
              expiration_date ASC
        """
        
        params = {"user_id": user_id}
        
        # Execute the query and return results
        return bq.execute_query(query, params)
    
    except Exception as e:
        logger.error(f"Error retrieving user pantry full view: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving pantry items: {str(e)}")


@router.put("/items/{item_id}", response_model=Dict[str, Any], summary="Update Pantry Item")
async def update_pantry_item(
    item_id: str,
    item_data: PantryItemCreate,
    pantry_service: PantryService = Depends(get_pantry_service)
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
            pantry_item_id=int(item_id),
            item_data=item_data
        )
        if not updated_item:
            raise HTTPException(status_code=404, detail=f"Pantry item {item_id} not found")
        return updated_item
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise  # Re-raise HTTPException as is
    except Exception as e:
        logger.error(f"Error updating pantry item {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update pantry item: {str(e)}")

@router.patch("/items/{item_id}/consume", response_model=Dict[str, Any], summary="Update Item Consumption")
async def consume_pantry_item(
    item_id: str,
    consumption_data: PantryItemConsumption,
    pantry_service: PantryService = Depends(get_pantry_service),
    bq_service: BigQueryService = Depends(get_bigquery_service)
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
        query = """
        UPDATE `pantry_items`
        SET 
            quantity = @quantity_amount,
            used_quantity = @used_quantity
        WHERE pantry_item_id = @item_id
        """
        
        params = {
            "quantity_amount": consumption_data.quantity_amount,
            "used_quantity": consumption_data.used_quantity or 0,
            "item_id": int(item_id)
        }
        
        # Execute the update
        rows_updated = bq_service.update_rows(
            "pantry_items",
            {
                "quantity": consumption_data.quantity_amount,
                "used_quantity": consumption_data.used_quantity or 0
            },
            {"pantry_item_id": int(item_id)}
        )
        
        if rows_updated == 0:
            raise HTTPException(status_code=404, detail=f"Pantry item {item_id} not found")
        
        return {
            "message": "Item consumption updated successfully",
            "item_id": item_id,
            "new_quantity": consumption_data.quantity_amount,
            "total_used": consumption_data.used_quantity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item consumption {item_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update item consumption: {str(e)}")

@router.delete("/items/{item_id}", response_model=Dict[str, Any], summary="Delete Single Pantry Item")
async def delete_pantry_item(
    item_id: str,
    pantry_service: PantryService = Depends(get_pantry_service)
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
        raise HTTPException(status_code=500, detail=f"Failed to delete pantry item: {str(e)}")

@router.delete("/user/{user_id}/items", response_model=Dict[str, Any])
async def delete_user_pantry_items(
    user_id: int = 111, 
    hours_ago: Optional[int] = None,
    delete_all: bool = False,
    pantry_service: PantryService = Depends(get_pantry_service)
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
            user_id=user_id,
            hours_ago=hours_ago,
            delete_all=delete_all
        )
        return result
    except Exception as e:
        logger.error(f"Error deleting user pantry items: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting pantry items: {str(e)}")