from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

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