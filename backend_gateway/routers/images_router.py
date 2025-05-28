"""Endpoints for uploading pantry images and detecting items."""

# File: PrepSense/backend_gateway/routers/images_router.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Dict, Any, List # For type hinting

# Correct import for the centralized VisionService
from backend_gateway.services.vision_service import VisionService

# Import additional services
from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.bigquery_service import BigQueryService

# Dependency functions
def get_vision_service():
    return VisionService()
    
def get_bigquery_service():
    return BigQueryService()
    
def get_pantry_service(bq_service: BigQueryService = Depends(get_bigquery_service)):
    return PantryService(bq_service)

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
    items: List[Dict[str, Any]],
    user_id: int = 111, # Default demo user ID
    pantry_service: PantryService = Depends(get_pantry_service)
):
    """
    Save detected food items from vision service to the user's pantry in BigQuery.
    
    Args:
        items: List of detected items with their details
        user_id: The user ID to save items for (defaults to 111 for demo)
        pantry_service: The pantry service instance
        
    Returns:
        A status message and count of saved items
    """
    try:
        # Step 1: Get all pantry IDs for this user
        pantry_query = """
            SELECT pantry_id
            FROM `adsp-34002-on02-prep-sense.Inventory.pantry`
            WHERE user_id = @user_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        pantry_params = {"user_id": user_id}
        pantry_results = pantry_service.bq_service.execute_query(pantry_query, pantry_params)
        
        if not pantry_results:
            # Create a new pantry for this user if none exists
            create_pantry_query = """
                INSERT INTO `adsp-34002-on02-prep-sense.Inventory.pantry` 
                (user_id, pantry_name, created_at)
                VALUES (@user_id, @pantry_name, CURRENT_TIMESTAMP())
            """
            create_params = {
                "user_id": user_id,
                "pantry_name": f"User {user_id} Primary Pantry"
            }
            pantry_service.bq_service.execute_query(create_pantry_query, create_params)
            
            # Get the newly created pantry ID
            pantry_results = pantry_service.bq_service.execute_query(pantry_query, pantry_params)
            
            if not pantry_results:
                raise HTTPException(status_code=500, detail="Failed to create or retrieve user pantry")
                
        # Use the first (most recent) pantry ID
        pantry_id = pantry_results[0]["pantry_id"]
        
        # Step 2: Add each item to the pantry
        saved_items = []
        for item in items:
            try:
                # Transform item to the format expected by add_pantry_item
                item_data = {
                    "name": item.get("item_name") or item.get("name"),
                    "quantity": float(item.get("quantity_amount", 1)),
                    "unit_of_measurement": item.get("quantity_unit", "unit"),
                    "expiration_date": item.get("expiration_date") or item.get("expected_expiration"),
                    "status": "available",
                    "unit_price": 0.0,  # Default since vision can't detect price
                    "total_price": 0.0  # Default 
                }
                
                result = await pantry_service.add_pantry_item(pantry_id, item_data)
                saved_items.append({
                    "item_name": item_data["name"],
                    "status": "saved"
                })
            except Exception as item_error:
                print(f"Error saving item {item.get('item_name')}: {str(item_error)}")
                # Continue with other items instead of failing the whole batch
                saved_items.append({
                    "item_name": item.get("item_name") or item.get("name"),
                    "status": "error",
                    "error": str(item_error)
                })
                
        return {
            "message": "Items saved to pantry",
            "saved_count": len([i for i in saved_items if i["status"] == "saved"]), 
            "error_count": len([i for i in saved_items if i["status"] == "error"]),
            "pantry_id": pantry_id,
            "saved_items": saved_items
        }
        
    except Exception as e:
        print(f"Error saving detected items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save detected items: {str(e)}")
        

@router.delete("/cleanup-detected-items", response_model=Dict[str, Any])
async def cleanup_detected_items(
    user_id: int = 111, # Default demo user ID
    hours_ago: int = 24, # Default to last 24 hours
    pantry_service: PantryService = Depends(get_pantry_service)
):
    """
    Cleanup recently detected food items for demo purposes.
    
    Args:
        user_id: The user ID to clean up items for (defaults to 111 for demo)
        hours_ago: Only delete items added within this many hours
        pantry_service: The pantry service instance
        
    Returns:
        A status message and count of deleted items
    """
    try:
        result = await pantry_service.delete_user_pantry_items(
            user_id=user_id,
            hours_ago=hours_ago
        )
        return result
    except Exception as e:
        print(f"Error cleaning up detected items: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clean up detected items: {str(e)}")