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
    use_preferences: bool = True  # Whether to use user preferences

class ChatResponse(BaseModel):
    response: str
    recipes: List[Dict[str, Any]] = []
    pantry_items: List[Dict[str, Any]] = []
    user_preferences: Dict[str, Any] = None
    show_preference_choice: bool = False

class ImageGenerationRequest(BaseModel):
    recipe_name: str
    style: str = "professional food photography"
    use_generated: bool = False  # False = Unsplash (fast), True = DALL-E (generated)

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
        # Check if this is the first message (to show preference choice)
        show_preference_choice = len(chat_message.message) > 0 and not any(
            word in chat_message.message.lower() 
            for word in ['without preferences', 'ignore preferences', 'no preferences']
        )
        
        response = await crew_ai_service.process_message(
            user_id=chat_message.user_id,
            message=chat_message.message,
            use_preferences=chat_message.use_preferences
        )
        
        # Add preference choice flag for first message
        if show_preference_choice and response.get('user_preferences'):
            response['show_preference_choice'] = True
        
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
    Get an image for a recipe using either Unsplash (fast) or DALL-E 2 (generated).
    
    Args:
        request: The image generation request with recipe name, style, and use_generated flag
        
    Returns:
        ImageGenerationResponse with the image URL
    """
    try:
        # If user wants generated images, use DALL-E 2 (cheaper than DALL-E 3)
        if request.use_generated:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            if openai.api_key:
                try:
                    # Create a simple prompt for DALL-E 2
                    prompt = f"{request.recipe_name}, food photography, delicious, appetizing"
                    
                    # Generate with DALL-E 2 (much cheaper and faster than DALL-E 3)
                    client = openai.OpenAI(api_key=openai.api_key)
                    response = client.images.generate(
                        model="dall-e-2",  # Using DALL-E 2 instead of 3
                        prompt=prompt,
                        size="512x512",    # Smaller size for faster generation
                        n=1
                    )
                    
                    image_url = response.data[0].url
                    return ImageGenerationResponse(
                        image_url=image_url,
                        recipe_name=request.recipe_name
                    )
                except Exception as e:
                    logger.warning(f"DALL-E 2 generation failed, falling back to Unsplash: {str(e)}")
                    # Fall through to Unsplash
            else:
                logger.warning("OpenAI API key not configured, using Unsplash instead")
        
        # Default to Unsplash for fast image retrieval
        import requests
        
        # Get Unsplash access key from environment
        unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        
        if not unsplash_access_key:
            # Fallback to varied food images based on recipe name hash
            logger.warning("Unsplash API key not configured, using fallback images")
            
            # Smart image selection based on recipe name
            recipe_lower = request.recipe_name.lower()
            
            # Map recipe types to appropriate images
            if 'bowl' in recipe_lower or 'buddha' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800"  # Healthy bowl
            elif 'stir fry' in recipe_lower or 'stir-fry' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800"  # Stir fry
            elif 'pasta' in recipe_lower or 'spaghetti' in recipe_lower or 'noodle' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800"  # Pasta
            elif 'salad' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800"  # Salad
            elif 'burger' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800"  # Burger
            elif 'sandwich' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=800"  # Sandwich
            elif 'pizza' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800"  # Pizza
            elif 'soup' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=800"  # Soup
            elif 'smoothie' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=800"  # Smoothie
            elif 'chicken' in recipe_lower:
                image_url = "https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=800"  # Chicken dish
            else:
                # Fallback to hash-based selection for unmatched recipes
                fallback_images = [
                    "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",  # General food
                    "https://images.unsplash.com/photo-1529042410759-befb1204b468?w=800",  # Asian food
                    "https://images.unsplash.com/photo-1499028344343-cd173ffc68a9?w=800",  # Meal
                ]
                import hashlib
                recipe_hash = hashlib.md5(request.recipe_name.encode()).hexdigest()
                image_index = int(recipe_hash[:8], 16) % len(fallback_images)
                image_url = fallback_images[image_index]
            
            return ImageGenerationResponse(
                image_url=image_url,
                recipe_name=request.recipe_name
            )
        
        # Search for food images related to the recipe
        search_query = request.recipe_name.replace(" ", "+")
        url = f"https://api.unsplash.com/search/photos?query={search_query}+food&per_page=1&orientation=landscape"
        
        headers = {
            "Authorization": f"Client-ID {unsplash_access_key}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                # Get the first image result
                image_url = data["results"][0]["urls"]["regular"]
                return ImageGenerationResponse(
                    image_url=image_url,
                    recipe_name=request.recipe_name
                )
        
        # Fallback to a generic food image search if specific recipe not found
        fallback_url = f"https://api.unsplash.com/search/photos?query=delicious+food&per_page=1&orientation=landscape"
        fallback_response = requests.get(fallback_url, headers=headers)
        
        if fallback_response.status_code == 200:
            fallback_data = fallback_response.json()
            if fallback_data["results"]:
                image_url = fallback_data["results"][0]["urls"]["regular"]
                return ImageGenerationResponse(
                    image_url=image_url,
                    recipe_name=request.recipe_name
                )
        
        # Final fallback to varied food images
        fallback_images = [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
            "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800",
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
        ]
        import hashlib
        recipe_hash = hashlib.md5(request.recipe_name.encode()).hexdigest()
        image_index = int(recipe_hash[:8], 16) % len(fallback_images)
        
        return ImageGenerationResponse(
            image_url=fallback_images[image_index],
            recipe_name=request.recipe_name
        )
        
    except Exception as e:
        logger.error(f"Error getting recipe image: {str(e)}")
        # Fallback to varied food images
        fallback_images = [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
            "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800",
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
        ]
        import hashlib
        recipe_hash = hashlib.md5(request.recipe_name.encode()).hexdigest()
        image_index = int(recipe_hash[:8], 16) % len(fallback_images)
        
        return ImageGenerationResponse(
            image_url=fallback_images[image_index],
            recipe_name=request.recipe_name
        )