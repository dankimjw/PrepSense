"""Endpoints for uploading pantry images and detecting items."""

# File: PrepSense/backend_gateway/routers/images_router.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Dict, Any, List, Optional # For type hinting
from pydantic import BaseModel
from datetime import datetime

# Correct import for the centralized VisionService
from backend_gateway.services.vision_service import VisionService

# Import additional services
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.pantry_item_manager import PantryItemManager
from backend_gateway.config.database import get_database_service, get_pantry_service

# Dependency functions
def get_vision_service():
    return VisionService()
    
def get_pantry_service_dep():
    return get_pantry_service()

def get_pantry_item_manager():
    db_service = get_database_service()
    return PantryItemManager(db_service)

# Pydantic models for request validation
class DetectedItem(BaseModel):
    item_name: str
    quantity_amount: float
    quantity_unit: str
    expected_expiration: str
    category: Optional[str] = "Uncategorized"
    brand: Optional[str] = "Generic"

class SaveItemsRequest(BaseModel):
    items: List[DetectedItem]
    user_id: int = 111

class CleanupRequest(BaseModel):
    user_id: int = 111
    hours_ago: Optional[float] = None

router = APIRouter()

@router.post("/upload", response_model=Dict[str, List[Dict[str, Any]]]) # Define a response model
async def upload_image(
    file: UploadFile = File(...),
    vision_service: VisionService = Depends(get_vision_service)
):
    try:
        base64_image, content_type = await vision_service.process_image(file)
        
        if not content_type:
            # This case should ideally not happen with UploadFile, but good to check
            raise HTTPException(status_code=400, detail="Could not determine image content type.")

        openai_raw_response = vision_service.classify_food_items(base64_image, content_type)
        
        try:
            parsed_items = vision_service.parse_openai_response(openai_raw_response)
            return {"pantry_items": parsed_items}
        except ValueError as e:
            # Log the raw response if parsing fails, helps in debugging prompts or OpenAI output
            print(f"Error parsing OpenAI response: {e}. Raw response: {openai_raw_response}")
            raise HTTPException(status_code=500, detail=f"Failed to parse OpenAI response: {str(e)}")

    except RuntimeError as e: # Errors from VisionService (e.g., OpenAI API communication)
        raise HTTPException(status_code=502, detail=f"Service error: {str(e)}") # 502 Bad Gateway
    except HTTPException: # Re-raise HTTPExceptions explicitly
        raise
    except Exception as e:
        # Log the full traceback for unexpected errors in a production environment
        # traceback.print_exc()
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected internal server error occurred.")
        

@router.post("/save-detected-items", response_model=Dict[str, Any])
async def save_detected_items(
    request: SaveItemsRequest,
    pantry_manager: PantryItemManager = Depends(get_pantry_item_manager)
):
    """
    Save detected food items from vision service to the user's pantry in BigQuery.
    
    This endpoint properly handles the relationship between pantry_items and products tables,
    ensuring each item gets unique IDs that are properly incremented.
    
    Args:
        request: SaveItemsRequest containing items and user_id
        pantry_manager: The pantry item manager service
        
    Returns:
        A status message and details of saved items
    """
    try:
        # Convert Pydantic models to dicts for the service
        items_data = [item.dict() for item in request.items]
        
        # Use the new manager to save items across all tables
        result = pantry_manager.add_items_batch(request.user_id, items_data)
        
        return result
        
    except Exception as e:
        print(f"Error saving detected items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save detected items: {str(e)}")
        

@router.delete("/cleanup-detected-items", response_model=Dict[str, Any])
async def cleanup_detected_items(
    request: CleanupRequest,
    pantry_manager: PantryItemManager = Depends(get_pantry_item_manager)
):
    """
    Cleanup items that were recently added via vision detection.
    
    Args:
        request: CleanupRequest containing user_id and optional hours_ago
        pantry_manager: The pantry item manager service
        
    Returns:
        A status message and count of deleted items
    """
    try:
        print(f"Cleanup request received: user_id={request.user_id}, hours_ago={request.hours_ago}")
        result = pantry_manager.delete_recent_items(
            user_id=request.user_id,
            hours=request.hours_ago
        )
        print(f"Cleanup result: {result}")
        return result
    except Exception as e:
        print(f"Error cleaning up detected items: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to clean up detected items: {str(e)}")

@router.get("/debug-items/{user_id}", response_model=Dict[str, Any])
async def debug_user_items(
    user_id: int,
    db_service = Depends(get_database_service)
):
    """Debug endpoint to check items and their timestamps."""
    try:
        query = """
            SELECT 
                pi.pantry_item_id,
                pi.pantry_id,
                pi.created_at,
                pi.quantity,
                pi.unit_of_measurement,
                p.product_name,
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - pi.created_at))/60 as minutes_ago
            FROM pantry_items pi
            LEFT JOIN products p
            ON pi.pantry_item_id = p.pantry_item_id
            WHERE pi.pantry_id IN (
                SELECT pantry_id 
                FROM pantry
                WHERE user_id = %(user_id)s
            )
            ORDER BY pi.created_at DESC
            LIMIT 20
        """
        
        results = db_service.execute_query(query, {"user_id": user_id})
        
        return {
            "user_id": user_id,
            "item_count": len(results),
            "items": results,
            "current_datetime": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in debug endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/item/{pantry_item_id}", response_model=Dict[str, Any])
async def delete_single_item(
    pantry_item_id: int,
    user_id: int = 111,
    pantry_manager: PantryItemManager = Depends(get_pantry_item_manager)
):
    """
    Delete a single pantry item by its ID.
    
    Args:
        pantry_item_id: The ID of the pantry item to delete
        user_id: The user ID for verification (defaults to 111)
        pantry_manager: The pantry item manager service
        
    Returns:
        A status message with deletion result
    """
    try:
        result = pantry_manager.delete_item(user_id, pantry_item_id)
        if not result["deleted"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting item: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")