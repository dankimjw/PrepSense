"""
Updated CrewAI Router for PrepSense Recipe Recommendations

Uses the prepsense_crew module with proper error handling and fallbacks.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

try:
    from backend_gateway.services.real_crewai_service import RealCrewAIService
    from backend_gateway.prepsense_crew.models import CrewInput
    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI modules not available: {e}")
    CREWAI_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models
class CrewAIRecipeRequest(BaseModel):
    """Request for CrewAI recipe recommendations"""
    user_id: int = Field(..., description="User ID")
    message: str = Field(..., description="User's recipe request or question")
    use_preferences: bool = Field(True, description="Whether to use user preferences")
    context: Optional[str] = Field(None, description="Additional context for recommendations")

class CrewAIRecipeResponse(BaseModel):
    """Response from CrewAI recipe recommendations"""
    success: bool
    message: str
    recommendations: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[int] = None
    cache_used: Optional[bool] = None
    error: Optional[str] = None

class CrewAIStatusResponse(BaseModel):
    """Status of CrewAI system"""
    available: bool
    service_initialized: bool
    cache_status: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Global service instance
_crewai_service: Optional[RealCrewAIService] = None

def get_crewai_service() -> RealCrewAIService:
    """Get or create CrewAI service instance"""
    global _crewai_service
    if _crewai_service is None:
        if not CREWAI_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="CrewAI service not available - missing dependencies"
            )
        try:
            _crewai_service = RealCrewAIService()
            logger.info("CrewAI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI service: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"CrewAI service initialization failed: {str(e)}"
            )
    return _crewai_service

@router.get("/crewai/status", response_model=CrewAIStatusResponse)
async def get_crewai_status():
    """Get status of CrewAI system"""
    try:
        service = get_crewai_service()
        
        # Get cache stats
        cache_status = None
        try:
            if hasattr(service, 'cache_manager'):
                cache_status = service.cache_manager.get_cache_stats()
        except Exception as e:
            logger.warning(f"Could not get cache status: {e}")
        
        return CrewAIStatusResponse(
            available=True,
            service_initialized=True,
            cache_status=cache_status
        )
    except Exception as e:
        return CrewAIStatusResponse(
            available=CREWAI_AVAILABLE,
            service_initialized=False,
            error=str(e)
        )

@router.post("/crewai/recommendations", response_model=CrewAIRecipeResponse)
async def get_recipe_recommendations(
    request: CrewAIRecipeRequest,
    background_tasks: BackgroundTasks
):
    """
    Get recipe recommendations using CrewAI.
    
    This endpoint provides intelligent recipe recommendations based on:
    - User's pantry items (cached or real-time)
    - User preferences and dietary restrictions
    - Current ingredient availability and expiration
    - Recipe feasibility and nutrition analysis
    """
    start_time = datetime.now()
    
    try:
        service = get_crewai_service()
        
        # Process the request
        result = await service.process_message(
            user_id=request.user_id,
            message=request.message,
            use_preferences=request.use_preferences
        )
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return CrewAIRecipeResponse(
            success=True,
            message="Recipe recommendations generated successfully",
            recommendations=result,
            processing_time_ms=processing_time,
            cache_used=result.get('cache_used', False)
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing CrewAI request: {e}")
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return CrewAIRecipeResponse(
            success=False,
            message="Failed to generate recommendations",
            error=str(e),
            processing_time_ms=processing_time
        )

@router.post("/crewai/cache/invalidate")
async def invalidate_cache(user_id: int):
    """Invalidate cache for a specific user"""
    try:
        service = get_crewai_service()
        
        if hasattr(service, 'cache_manager'):
            # Invalidate all cache types for the user
            results = []
            try:
                recipe_results = service.cache_manager.invalidate_recipe_cache(user_id)
                results.extend(recipe_results)
            except Exception as e:
                logger.warning(f"Could not invalidate recipe cache: {e}")
            
            return {
                "success": True,
                "message": f"Cache invalidated for user {user_id}",
                "details": results
            }
        else:
            return {
                "success": False,
                "message": "Cache manager not available"
            }
            
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crewai/cache/stats")
async def get_cache_statistics():
    """Get detailed cache statistics"""
    try:
        service = get_crewai_service()
        
        if hasattr(service, 'cache_manager'):
            stats = service.cache_manager.get_cache_stats()
            return {
                "success": True,
                "stats": stats
            }
        else:
            return {
                "success": False,
                "message": "Cache manager not available"
            }
            
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))