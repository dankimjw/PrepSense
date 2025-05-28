from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import openai
import os

from backend_gateway.services.crew_ai_service import CrewAIService
from backend_gateway.routers.users import get_current_active_user
from backend_gateway.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

class ChatMessage(BaseModel):
    message: str
    user_id: int = 111  # Default user for now

class ChatResponse(BaseModel):
    response: str
    recipes: List[Dict[str, Any]] = []
    pantry_items: List[Dict[str, Any]] = []

class ImageGenerationRequest(BaseModel):
    recipe_name: str
    style: str = "professional food photography"

class ImageGenerationResponse(BaseModel):
    image_url: str
    recipe_name: str

def get_crew_ai_service():
    return CrewAIService()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    crew_ai_service: CrewAIService = Depends(get_crew_ai_service)
):
    """
    Send a message to the AI assistant and get recipe recommendations
    based on the user's pantry items.
    """
    try:
        response = await crew_ai_service.process_message(
            user_id=chat_message.user_id,
            message=chat_message.message
        )
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

@router.post("/generate-recipe-image", response_model=ImageGenerationResponse)
async def generate_recipe_image(
    request: ImageGenerationRequest
):
    """
    Generate an image for a recipe using OpenAI's DALL-E.
    
    Args:
        request: The image generation request with recipe name and style
        
    Returns:
        ImageGenerationResponse with the generated image URL
    """
    try:
        # Initialize OpenAI client if not already done
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured"
            )
        
        # Create a detailed prompt for food photography
        prompt = f"Professional food photography of {request.recipe_name}, {request.style}, beautifully plated, appetizing, high resolution, studio lighting, top view, clean background"
        
        # Generate image using DALL-E
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Extract image URL from response
        image_url = response.data[0].url
        
        return ImageGenerationResponse(
            image_url=image_url,
            recipe_name=request.recipe_name
        )
        
    except Exception as e:
        logger.error(f"Error generating recipe image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recipe image: {str(e)}"
        )