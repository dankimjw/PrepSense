"""
Chat router v2 - Uses the new CrewAI implementation with multi-source recipes
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from backend_gateway.services.crew_ai_service_legacy import CrewAIServiceLegacy
from backend_gateway.routers.users import get_current_active_user
from backend_gateway.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat/v2",
    tags=["Chat V2"],
    responses={404: {"description": "Not found"}},
)


class ChatMessageV2(BaseModel):
    message: str
    user_id: Optional[int] = None
    use_preferences: bool = True
    include_saved_recipes: bool = True
    num_spoonacular: int = 2
    num_ai_generated: int = 2


class RecipeV2(BaseModel):
    name: str
    ingredients: List[str]
    instructions: List[str]
    nutrition: Dict[str, Any]
    time: int
    source: str  # 'saved', 'spoonacular', 'ai_generated'
    match_score: float
    missing_ingredients: List[str]
    cuisine_type: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    user_rating: Optional[str] = None  # For saved recipes
    is_favorite: Optional[bool] = None  # For saved recipes


class ChatResponseV2(BaseModel):
    response: str
    recipes: List[RecipeV2]
    pantry_summary: Dict[str, Any]
    preferences_used: bool
    debug_info: Optional[Dict[str, Any]] = None


# Service will be initialized on first use
crew_service = None

def get_crew_service():
    """Get or create the crew service instance"""
    global crew_service
    if crew_service is None:
        crew_service = CrewAIServiceLegacy()
    return crew_service


@router.post("/message", response_model=ChatResponseV2)
async def chat_with_crew(
    chat_message: ChatMessageV2,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Process a chat message using the CrewAI multi-agent system
    
    Features:
    - Checks user's saved recipes first
    - Gets recipes from Spoonacular API
    - Generates creative recipes with OpenAI
    - Learns from user preferences and history
    - Handles dietary restrictions and allergens
    """
    try:
        # Use authenticated user's ID
        user_id = current_user.user_id
        
        logger.info(f"Processing chat message for user {user_id}: {chat_message.message}")
        
        # Process with CrewAI
        service = get_crew_service()
        result = await service.process_message(
            user_id=user_id,
            message=chat_message.message,
            use_preferences=chat_message.use_preferences
        )
        
        # Format response
        return ChatResponseV2(
            response=result.get("response", ""),
            recipes=result.get("recipes", []),
            pantry_summary={
                "total_items": len(result.get("pantry_items", [])),
                "expiring_soon": sum(1 for item in result.get("pantry_items", []) 
                                   if item.get("freshness_status") == "expiring_soon")
            },
            preferences_used=chat_message.use_preferences,
            debug_info=result.get("crew_raw_output") if logger.level <= logging.DEBUG else None
        )
        
    except Exception as e:
        logger.error(f"Error in chat v2: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_crew_service():
    """Test if CrewAI service is properly initialized"""
    try:
        from crewai import Agent
        crew_available = True
    except ImportError:
        crew_available = False
    
    service = get_crew_service()
    return {
        "service_initialized": service is not None,
        "crewai_available": crew_available,
        "tools_available": {
            "pantry_tool": hasattr(service, 'pantry_tool'),
            "preferences_tool": hasattr(service, 'preferences_tool'),
            "saved_recipe_tool": hasattr(service, 'saved_recipe_tool'),
            "openai_tool": hasattr(service, 'openai_tool'),
            "ranker_tool": hasattr(service, 'ranker_tool')
        },
        "agents_initialized": crew_available and service._agents_initialized if service else False
    }


@router.post("/simple", response_model=ChatResponseV2)
async def chat_simple_fallback(
    chat_message: ChatMessageV2,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Simple fallback endpoint when CrewAI is not available
    Still provides saved recipe matching and basic responses
    """
    try:
        user_id = current_user.user_id
        
        # Use simple fallback method
        service = get_crew_service()
        result = await service.process_message_simple(
            user_id=user_id,
            message=chat_message.message,
            use_preferences=chat_message.use_preferences
        )
        
        return ChatResponseV2(
            response=result.get("response", ""),
            recipes=result.get("recipes", []),
            pantry_summary={
                "total_items": len(result.get("pantry_items", [])),
                "expiring_soon": 0  # Would need to calculate
            },
            preferences_used=chat_message.use_preferences
        )
        
    except Exception as e:
        logger.error(f"Error in simple chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))