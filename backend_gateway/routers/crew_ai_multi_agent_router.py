"""
Router for CrewAI Multi-Agent service
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from backend_gateway.services.crew_ai_multi_agent import MultiAgentCrewAIService
from backend_gateway.routers.users import get_current_active_user
from backend_gateway.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat/multi-agent",
    tags=["Multi-Agent Chat"],
    responses={404: {"description": "Not found"}},
)


class MultiAgentRequest(BaseModel):
    """Request model for multi-agent chat"""
    message: str
    user_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What can I make for dinner tonight?",
                "user_id": 123
            }
        }


class MultiAgentResponse(BaseModel):
    """Response model for multi-agent chat"""
    response: str
    recipes: List[Dict[str, Any]]
    pantry_items: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on your pantry items, I recommend making Chicken Stir Fry...",
                "recipes": [
                    {
                        "id": 1,
                        "name": "Chicken Stir Fry",
                        "ingredients": ["chicken", "vegetables", "rice"],
                        "time": 30,
                        "instructions": ["Cook rice", "Stir fry chicken", "Add vegetables"],
                        "cuisine_type": "asian"
                    }
                ],
                "pantry_items": [
                    {
                        "product_name": "Chicken Breast",
                        "quantity": 2,
                        "unit": "lbs",
                        "expiration_date": "2024-01-25"
                    }
                ],
                "user_preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "allergens": ["nuts"],
                    "cuisine_preferences": ["italian", "asian"]
                }
            }
        }


# Initialize the service lazily to avoid startup issues
_multi_agent_service = None

def get_multi_agent_service():
    """Get or create the multi-agent service instance"""
    global _multi_agent_service
    if _multi_agent_service is None:
        _multi_agent_service = MultiAgentCrewAIService()
    return _multi_agent_service


@router.post("/recommend", response_model=MultiAgentResponse)
async def get_multi_agent_recommendations(
    request: MultiAgentRequest,
    current_user: UserInDB = Depends(get_current_active_user)
) -> MultiAgentResponse:
    """
    Get recipe recommendations using the multi-agent CrewAI system.
    
    This endpoint uses 8 specialized agents working together:
    - Pantry Scanner: Reads pantry items from database
    - Ingredient Filter: Filters expired/unusable items
    - User Preference Specialist: Applies dietary restrictions
    - Recipe Researcher: Searches for matching recipes
    - Nutritional Analyst: Evaluates nutritional content
    - Recipe Scoring Expert: Ranks recipes by relevance
    - Recipe Evaluator: Validates feasibility
    - Response Formatter: Formats the final response
    """
    try:
        # Use provided user_id or current user's ID
        user_id = request.user_id or current_user.id
        
        logger.info(f"Processing multi-agent request for user {user_id}: {request.message}")
        
        # Process the message through the multi-agent system
        service = get_multi_agent_service()
        result = await service.process_message(
            user_id=user_id,
            message=request.message
        )
        
        return MultiAgentResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in multi-agent recommendation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process multi-agent request: {str(e)}"
        )


@router.get("/status")
async def get_multi_agent_status(
    current_user: UserInDB = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get the status of the multi-agent system.
    
    Returns information about:
    - Number of agents configured
    - Agent roles and capabilities
    - System health status
    """
    try:
        agents_info = []
        
        service = get_multi_agent_service()
        
        for agent_name, agent in service.agents.items():
            agents_info.append({
                "name": agent_name,
                "role": agent.role,
                "tools": len(agent.tools),
                "status": "active"
            })
        
        return {
            "status": "healthy",
            "total_agents": len(service.agents),
            "agents": agents_info,
            "capabilities": [
                "Pantry inventory management",
                "Ingredient freshness checking",
                "User preference matching",
                "Recipe search and discovery",
                "Nutritional analysis",
                "Recipe scoring and ranking",
                "Feasibility validation",
                "Response formatting"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting multi-agent status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get multi-agent status: {str(e)}"
        )


@router.post("/test")
async def test_multi_agent_system(
    current_user: UserInDB = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Test the multi-agent system with a sample request.
    
    This endpoint is useful for:
    - Verifying the system is working
    - Testing agent coordination
    - Debugging issues
    """
    try:
        # Run a test query
        test_message = "What can I make with chicken and rice?"
        
        service = get_multi_agent_service()
        
        result = await service.process_message(
            user_id=current_user.id,
            message=test_message
        )
        
        return {
            "status": "success",
            "test_message": test_message,
            "agents_used": len(service.agents),
            "result_summary": {
                "response_length": len(result.get("response", "")),
                "recipes_found": len(result.get("recipes", [])),
                "pantry_items": len(result.get("pantry_items", [])),
                "has_preferences": bool(result.get("user_preferences", {}))
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing multi-agent system: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "agents_configured": len(get_multi_agent_service().agents) if _multi_agent_service else 0
        }