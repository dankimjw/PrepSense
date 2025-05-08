# File: PrepSense/backend_gateway/routers/images_router.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Dict, Any, List # For type hinting

# Correct import for the centralized VisionService
from backend_gateway.services.vision_service import VisionService

# Dependency function to provide VisionService instance
def get_vision_service():
    return VisionService()

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

        openai_raw_response = await vision_service.classify_food_items(base64_image, content_type)
        
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