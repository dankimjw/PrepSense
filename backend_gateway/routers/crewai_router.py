"""CrewAI Router for FastAPI

FastAPI router for CrewAI workflow endpoints.
Phase 2: Production-ready endpoints with proper async support and error handling.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from backend_gateway.crewai.crew_manager import (
    process_recipe_request,
    process_pantry_normalization,
    background_pantry_normalization,
    get_crewai_health,
    get_crewai_statistics,
    crew_manager
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/crewai", tags=["crewai", "ai", "workflows"])


# Request/Response Models

class RecipeRequestModel(BaseModel):
    """Recipe recommendation request model"""
    user_message: str = Field(..., description="User's recipe request message")
    include_images: bool = Field(True, description="Whether to include recipe images")
    max_recipes: int = Field(5, ge=1, le=10, description="Maximum number of recipes to return")


class PantryNormalizationRequestModel(BaseModel):
    """Pantry normalization request model"""
    raw_pantry_items: List[Any] = Field(..., description="Raw pantry items to normalize")
    processing_mode: str = Field("full", description="Processing mode: full, fast, or verification")


class WorkflowStatusModel(BaseModel):
    """Workflow status response model"""
    workflow_id: str
    status: str
    processing_time_ms: int
    created_at: datetime
    completed_at: Optional[datetime] = None


# Recipe Recommendation Endpoints

@router.post("/recipe-recommendations")
async def create_recipe_recommendations(
    request: RecipeRequestModel,
    user_id: str = "anonymous"
) -> Dict[str, Any]:
    """
    Generate recipe recommendations using CrewAI agents.
    
    This endpoint orchestrates multiple AI agents to:
    1. Search for recipes that maximize pantry utilization
    2. Calculate nutritional information
    3. Score based on user preferences  
    4. Assess cooking feasibility
    
    Returns enhanced recipe data with images, nutrition, and feasibility scores.
    """
    try:
        logger.info(f"Recipe recommendation request from user {user_id}: {request.user_message[:50]}...")
        
        result = await process_recipe_request(
            user_id=user_id,
            user_message=request.user_message,
            include_images=request.include_images,
            max_recipes=request.max_recipes
        )
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=500,
                detail=f"Recipe recommendation failed: {result.get('error_details', 'Unknown error')}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recipe recommendation endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/recipe-recommendations/quick")
async def quick_recipe_recommendations(
    query: str,
    user_id: str = "anonymous",
    max_recipes: int = 3
) -> Dict[str, Any]:
    """
    Quick recipe recommendations with minimal processing.
    Optimized for faster response times.
    """
    try:
        result = await process_recipe_request(
            user_id=user_id,
            user_message=query,
            include_images=False,  # Skip images for speed
            max_recipes=max_recipes
        )
        
        return {
            "recipes": result.get('recipes', []),
            "processing_time_ms": result.get('processing_time_ms', 0),
            "agents_used": result.get('agents_used', [])
        }
        
    except Exception as e:
        logger.error(f"Quick recipe recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pantry Normalization Endpoints

@router.post("/pantry/normalize")
async def normalize_pantry_items(
    request: PantryNormalizationRequestModel,
    user_id: str = "anonymous"
) -> Dict[str, Any]:
    """
    Normalize and categorize pantry items using CrewAI agents.
    
    This endpoint orchestrates multiple AI agents to:
    1. Categorize food items and map to USDA database
    2. Standardize units and quantities
    3. Analyze freshness and prioritize usage
    
    Returns structured, normalized pantry data.
    """
    try:
        logger.info(f"Pantry normalization request from user {user_id}: {len(request.raw_pantry_items)} items")
        
        result = await process_pantry_normalization(
            user_id=user_id,
            raw_pantry_items=request.raw_pantry_items,
            processing_mode=request.processing_mode
        )
        
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=500,
                detail=f"Pantry normalization failed: {result.get('error_details', 'Unknown error')}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pantry normalization endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/pantry/normalize/background")
async def normalize_pantry_background(
    request: PantryNormalizationRequestModel,
    background_tasks: BackgroundTasks,
    user_id: str = "anonymous"
) -> Dict[str, Any]:
    """
    Start pantry normalization as a background task.
    Returns workflow ID for status tracking.
    """
    try:
        # Add background task
        background_tasks.add_task(
            background_pantry_normalization,
            user_id=user_id,
            raw_pantry_items=request.raw_pantry_items,
            processing_mode=request.processing_mode
        )
        
        # Generate workflow ID for tracking
        workflow_id = crew_manager.generate_workflow_id()
        
        return {
            "status": "accepted",
            "workflow_id": workflow_id,
            "message": f"Pantry normalization started for {len(request.raw_pantry_items)} items",
            "estimated_completion_time": "30-60 seconds"
        }
        
    except Exception as e:
        logger.error(f"Background pantry normalization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Workflow Management Endpoints

@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get the status of a specific workflow"""
    try:
        workflow_result = await crew_manager.get_workflow_status(workflow_id)
        
        if not workflow_result:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return {
            "workflow_id": workflow_result.workflow_id,
            "workflow_type": workflow_result.workflow_type.value,
            "status": workflow_result.status.value,
            "processing_time_ms": workflow_result.processing_time_ms,
            "created_at": workflow_result.created_at,
            "completed_at": workflow_result.completed_at,
            "error_message": workflow_result.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workflow status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/active")
async def get_active_workflows() -> Dict[str, Any]:
    """Get all currently active workflows"""
    try:
        active_workflows = crew_manager.get_active_workflows()
        
        return {
            "active_workflows": len(active_workflows),
            "workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "workflow_type": w.workflow_type.value,
                    "status": w.status.value,
                    "created_at": w.created_at
                }
                for w in active_workflows
            ]
        }
        
    except Exception as e:
        logger.error(f"Get active workflows failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and Monitoring Endpoints

@router.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """Get CrewAI system health status"""
    try:
        health = await get_crewai_health()
        
        # Return appropriate HTTP status based on health
        status_code = 200 if health['status'] == 'healthy' else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/statistics")
async def get_system_statistics() -> Dict[str, Any]:
    """Get CrewAI workflow statistics"""
    try:
        stats = get_crewai_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Get statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/info")
async def get_agent_information() -> Dict[str, Any]:
    """Get information about available CrewAI agents"""
    return {
        "available_agents": {
            "recipe_recommendation_crew": {
                "agents": [
                    {
                        "name": "Recipe Search Agent",
                        "role": "Recipe Discovery Expert",
                        "tools": ["IngredientMatcherTool", "RecipeImageFetcherTool"],
                        "description": "Finds recipes with beautiful images that maximize pantry utilization"
                    },
                    {
                        "name": "Nutri Check Agent", 
                        "role": "Nutrition Analysis Expert",
                        "tools": ["NutritionCalculatorTool"],
                        "description": "Calculates detailed nutritional information for recipes"
                    },
                    {
                        "name": "User Preferences Agent",
                        "role": "Preference Analysis Expert", 
                        "tools": ["PreferenceScorerTool"],
                        "description": "Scores recipes based on user dietary preferences and restrictions"
                    },
                    {
                        "name": "Judge Thyme Agent",
                        "role": "Cooking Feasibility Expert",
                        "tools": [],
                        "description": "Evaluates cooking difficulty, time requirements, and feasibility"
                    }
                ]
            },
            "pantry_normalization_crew": {
                "agents": [
                    {
                        "name": "Food Categorizer Agent",
                        "role": "Food Classification Expert",
                        "tools": [],
                        "description": "Categorizes food items and maps to USDA nutrition database"
                    },
                    {
                        "name": "Unit Canon Agent",
                        "role": "Measurement Standardization Expert", 
                        "tools": ["UnitConverterTool"],
                        "description": "Standardizes measurements and quantities for consistency"
                    },
                    {
                        "name": "Fresh Filter Agent",
                        "role": "Freshness Analysis Expert",
                        "tools": [],
                        "description": "Analyzes freshness and prioritizes items for optimal usage"
                    }
                ]
            }
        },
        "workflow_capabilities": [
            "Multi-source recipe image fetching",
            "Pantry utilization optimization", 
            "Nutritional analysis and scoring",
            "User preference matching",
            "Cooking feasibility assessment",
            "Food categorization and USDA mapping",
            "Unit standardization and conversion",
            "Freshness analysis and usage prioritization"
        ]
    }


# Development and Testing Endpoints

@router.post("/test/recipe-workflow")
async def test_recipe_workflow() -> Dict[str, Any]:
    """Test endpoint for recipe recommendation workflow"""
    if not logger.isEnabledFor(logging.DEBUG):
        raise HTTPException(
            status_code=403,
            detail="Test endpoints only available in debug mode"
        )
    
    test_result = await process_recipe_request(
        user_id="test_user",
        user_message="Test recipe request for pasta with vegetables",
        include_images=False,
        max_recipes=2
    )
    
    return {
        "test_status": "completed",
        "workflow_result": test_result
    }


@router.post("/test/pantry-workflow")
async def test_pantry_workflow() -> Dict[str, Any]:
    """Test endpoint for pantry normalization workflow"""
    if not logger.isEnabledFor(logging.DEBUG):
        raise HTTPException(
            status_code=403,
            detail="Test endpoints only available in debug mode"
        )
    
    test_items = ["chicken", "tomatoes", "rice", "milk", "carrots"]
    
    test_result = await process_pantry_normalization(
        user_id="test_user",
        raw_pantry_items=test_items
    )
    
    return {
        "test_status": "completed",
        "workflow_result": test_result
    }