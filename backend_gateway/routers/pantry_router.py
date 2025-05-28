from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Any, Dict, Optional
import logging

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
from datetime import date

# Set up logging
logger = logging.getLogger(__name__)

class PantryItemCreate(BaseModel):
    product_name: str = Field(..., example="Whole Milk", description="Name of the product.")
    quantity: float = Field(..., gt=0, example=1.0, description="Quantity of the item.")
    unit_of_measurement: str = Field(..., example="gallon", description="Unit of measurement (e.g., kg, lbs, gallon, liter).")
    expiration_date: Optional[date] = Field(None, description="Expiration date of the item.")
    purchase_date: Optional[date] = Field(None, description="Date the item was purchased.")
    unit_price: Optional[float] = Field(None, ge=0, example=3.50, description="Price per unit of the item.")
    # product_id: Optional[str] = Field(None, description="Optional ID linking to a master products table.")
    # pantry_id: Optional[str] = Field(None, description="Optional ID if user has multiple pantries; service might handle default.")

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

@router.get("/items", response_model=List[Dict[str, Any]], summary="List User's Pantry Items")
async def list_user_pantry_items(
    pantry_service: PantryService = Depends(get_pantry_service)
):
    """List all pantry items for a hardcoded user (ID 111)."""
    numeric_user_id = 111  # TEMPORARY: Hardcode for user 111
    
    try:
        items = await pantry_service.get_pantry_items(numeric_user_id)
        return items
    except Exception as e:
        # Consider logging the exception e for server-side diagnostics
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pantry items: {str(e)}")

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

@router.get("/user-pantry-full", response_model=List[Dict[str, Any]], summary="Get User's Full Pantry View")
async def get_user_pantry_full(
    user_id: int = 111,
    bq: BigQueryService = Depends(get_bigquery_service)
):
    """
    Get the user's full pantry view ordered by expiration date.
    Uses the user_pantry_full table which likely contains joined data.
    """
    try:
        query = """
            SELECT *
            FROM `adsp-34002-on02-prep-sense.Inventory.user_pantry_full`
            WHERE user_id = @user_id
            ORDER BY expiration_date
        """
        
        params = {"user_id": user_id}
        results = bq.execute_query(query, params)
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching user pantry full for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve user pantry data: {str(e)}"
        )