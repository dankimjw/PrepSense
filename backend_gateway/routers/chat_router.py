from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import openai
import os

from backend_gateway.services.recipe_advisor_service import CrewAIService
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
    include_nutrition: bool = False  # Whether to include nutrient gap awareness

class ChatResponse(BaseModel):
    response: str
    recipes: List[Dict[str, Any]] = []
    pantry_items: List[Dict[str, Any]] = []
    user_preferences: Dict[str, Any] = None
    show_preference_choice: bool = False
    nutrient_analysis: Dict[str, Any] = None

class ImageGenerationRequest(BaseModel):
    recipe_name: str
    style: str = "professional food photography"
    use_generated: bool = False  # False = Unsplash (fast), True = DALL-E (generated)

class ImageGenerationResponse(BaseModel):
    image_url: str
    recipe_name: str

def get_crew_ai_service():
    return CrewAIService()

# def get_nutrient_aware_crew_service():
    # return NutrientAwareCrewService()

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

# @router.post("/message-with-nutrition", response_model=ChatResponse)
# async def send_message_with_nutrition(
#     chat_message: ChatMessage,
#     nutrient_crew_service: NutrientAwareCrewService = Depends(get_nutrient_aware_crew_service)
# ):
    """
    Send a message to the AI assistant and get nutrient-aware recipe recommendations
    based on the user's pantry items and nutritional gaps.
    """
    try:
        logger.info(f"Processing nutrient-aware message: {chat_message.message}")
        
        # Check if this is the first message (to show preference choice)
        show_preference_choice = len(chat_message.message) > 0 and not any(
            word in chat_message.message.lower() 
            for word in ['without preferences', 'ignore preferences', 'no preferences']
        )
        
        response = await nutrient_crew_service.process_message_with_nutrition(
            user_id=chat_message.user_id,
            message=chat_message.message,
            use_preferences=chat_message.use_preferences,
            include_nutrient_gaps=chat_message.include_nutrition
        )
        
        # Add preference choice flag for first message
        if show_preference_choice and response.get('user_preferences'):
            response['show_preference_choice'] = True
        
        return response
    except Exception as e:
        logger.error(f"Error processing nutrient-aware chat message: {str(e)}")
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
                    # Create a simple prompt for gpt-image-1
                    prompt = f"{request.recipe_name}, food photography, delicious, appetizing"
                    
                    # Generate with DALL-E 2 (faster than DALL-E 3)
                    client = openai.OpenAI(api_key=openai.api_key)
                    response = client.images.generate(
                        model="dall-e-2",  # Using DALL-E 2 for faster generation
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
            
            # Smart image selection based on recipe name with more variety
            recipe_lower = request.recipe_name.lower()
            
            # Map recipe types to multiple appropriate images for variety
            food_images = {
                'bowl': [
                    "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800",
                    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800",
                    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
                ],
                'stir_fry': [
                    "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800",
                    "https://images.unsplash.com/photo-1603073163308-9654c3fb70b5?w=800",
                    "https://images.unsplash.com/photo-1609501676725-7186f017a4b7?w=800",
                ],
                'pasta': [
                    "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
                    "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=800",
                    "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=800",
                ],
                'salad': [
                    "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
                    "https://images.unsplash.com/photo-1607532941433-304659e8198a?w=800",
                    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800",
                ],
                'burger': [
                    "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",
                    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
                    "https://images.unsplash.com/photo-1550547660-d9450f859349?w=800",
                ],
                'sandwich': [
                    "https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=800",
                    "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=800",
                    "https://images.unsplash.com/photo-1521390188846-e2a3a97453a0?w=800",
                ],
                'pizza': [
                    "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800",
                    "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",
                    "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=800",
                ],
                'soup': [
                    "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=800",
                    "https://images.unsplash.com/photo-1576577445504-6af96477db52?w=800",
                    "https://images.unsplash.com/photo-1603105037880-2e9c86666081?w=800",
                ],
                'smoothie': [
                    "https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=800",
                    "https://images.unsplash.com/photo-1638176066666-ffb2f013c7dd?w=800",
                    "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=800",
                ],
                'chicken': [
                    "https://images.unsplash.com/photo-1532550907401-a500c9a57435?w=800",
                    "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=800",
                    "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=800",
                ],
                'fish': [
                    "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=800",
                    "https://images.unsplash.com/photo-1535399831218-d5bd36d1a6b3?w=800",
                    "https://images.unsplash.com/photo-1580476262798-bddd9f4b7369?w=800",
                ],
                'rice': [
                    "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=800",
                    "https://images.unsplash.com/photo-1516684732162-798a0062be99?w=800",
                    "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=800",
                ],
                'breakfast': [
                    "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?w=800",
                    "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=800",
                    "https://images.unsplash.com/photo-1555685812-4b943f1cb0eb?w=800",
                ],
                'dessert': [
                    "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=800",
                    "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=800",
                    "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=800",
                ]
            }
            
            # Check which category the recipe falls into
            selected_images = None
            for category, keywords in [
                ('bowl', ['bowl', 'buddha']),
                ('stir_fry', ['stir fry', 'stir-fry', 'wok']),
                ('pasta', ['pasta', 'spaghetti', 'noodle', 'linguine', 'penne', 'fettuccine']),
                ('salad', ['salad']),
                ('burger', ['burger']),
                ('sandwich', ['sandwich', 'wrap', 'sub']),
                ('pizza', ['pizza']),
                ('soup', ['soup', 'stew', 'chowder']),
                ('smoothie', ['smoothie', 'shake', 'juice']),
                ('chicken', ['chicken']),
                ('fish', ['fish', 'salmon', 'tuna', 'tilapia', 'cod', 'seafood']),
                ('rice', ['rice', 'risotto', 'pilaf']),
                ('breakfast', ['breakfast', 'pancake', 'waffle', 'egg', 'omelet', 'bacon']),
                ('dessert', ['dessert', 'cake', 'cookie', 'pie', 'ice cream', 'pudding'])
            ]:
                if any(keyword in recipe_lower for keyword in keywords):
                    selected_images = food_images.get(category, [])
                    break
            
            if not selected_images:
                # More varied fallback images for unmatched recipes
                selected_images = [
                    "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
                    "https://images.unsplash.com/photo-1529042410759-befb1204b468?w=800",
                    "https://images.unsplash.com/photo-1499028344343-cd173ffc68a9?w=800",
                    "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=800",
                    "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=800",
                    "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=800",
                    "https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=800",
                    "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=800",
                ]
            
            # Use hash to select a consistent but varied image for each unique recipe name
            import hashlib
            recipe_hash = hashlib.md5(request.recipe_name.encode()).hexdigest()
            image_index = int(recipe_hash[:8], 16) % len(selected_images)
            image_url = selected_images[image_index]
            
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
        
        # Fallback to a more specific food search based on keywords in recipe name
        recipe_lower = request.recipe_name.lower()
        
        # Extract key ingredients or food types for better search
        food_keywords = []
        for keyword in ['chicken', 'beef', 'pork', 'fish', 'vegetable', 'pasta', 'rice', 'salad', 'soup', 'sandwich']:
            if keyword in recipe_lower:
                food_keywords.append(keyword)
        
        # If no keywords found, use a general search term based on recipe name hash
        if not food_keywords:
            # Use different general terms based on hash for variety
            general_terms = ['homemade food', 'comfort food', 'healthy meal', 'delicious dish', 'gourmet food', 'tasty meal']
            recipe_hash = hashlib.md5(request.recipe_name.encode()).hexdigest()
            term_index = int(recipe_hash[:8], 16) % len(general_terms)
            search_term = general_terms[term_index]
        else:
            search_term = '+'.join(food_keywords[:2]) + '+food'  # Use up to 2 keywords
        
        fallback_url = f"https://api.unsplash.com/search/photos?query={search_term}&per_page=3&orientation=landscape"
        fallback_response = requests.get(fallback_url, headers=headers)
        
        if fallback_response.status_code == 200:
            fallback_data = fallback_response.json()
            if fallback_data["results"]:
                # Use hash to pick one of the results for variety
                recipe_hash = hashlib.md5(request.recipe_name.encode()).hexdigest()
                result_index = int(recipe_hash[:8], 16) % min(len(fallback_data["results"]), 3)
                image_url = fallback_data["results"][result_index]["urls"]["regular"]
                return ImageGenerationResponse(
                    image_url=image_url,
                    recipe_name=request.recipe_name
                )
        
        # Final fallback to varied food images - expanded list for better variety
        fallback_images = [
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",  # General food platter
            "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=800",  # Food spread
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800",  # Grilled food
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",  # Healthy bowl
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",  # Pasta dish
            "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=800",  # Colorful meal
            "https://images.unsplash.com/photo-1529042410759-befb1204b468?w=800",  # Asian cuisine
            "https://images.unsplash.com/photo-1499028344343-cd173ffc68a9?w=800",  # Burger meal
            "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=800",  # Restaurant plate
            "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=800",  # Colorful food
            "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=800",  # Toast breakfast
            "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?w=800",  # Breakfast eggs
            "https://images.unsplash.com/photo-1496412705862-e0088f16f791?w=800",  # Food variety
            "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800",  # Healthy food
            "https://images.unsplash.com/photo-1506354666786-959d6d497f1a?w=800",  # Food styling
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