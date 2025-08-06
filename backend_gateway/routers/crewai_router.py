"""Router for CrewAI intelligent recipe recommendation system"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Add src directory to path to import CrewAI agents
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "src"))

try:
    from src.crews.pantry_normalization import PantryNormalizationCrew
    from src.crews.prepsense_main import PrepSenseMainCrew

    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI modules not available: {e}")
    CREWAI_AVAILABLE = False

logger = logging.getLogger(__name__)


# Request/Response models
class PantryNormalizationRequest(BaseModel):
    """Request for pantry normalization workflow"""

    image_b64: Optional[str] = Field(
        None, description="Base64 encoded image for BiteCam processing"
    )
    raw_items: Optional[List[Dict[str, Any]]] = Field(
        None, description="Pre-extracted raw items [{'raw_line': '2 lb chicken'}]"
    )
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    freshness_days: int = Field(7, ge=1, le=30, description="Days threshold for freshness filter")


class PrepSenseWorkflowRequest(BaseModel):
    """Request for complete PrepSense workflow"""

    # Pantry inputs
    image_b64: Optional[str] = Field(
        None, description="Base64 encoded image for BiteCam processing"
    )
    raw_items: Optional[List[Dict[str, Any]]] = Field(None, description="Pre-extracted raw items")
    user_id: str = Field(..., description="User ID (required)")
    freshness_days: int = Field(7, ge=1, le=30, description="Days threshold for freshness filter")

    # Recipe search inputs
    max_recipes: int = Field(20, ge=1, le=100, description="Maximum recipes to search")
    max_final_recipes: int = Field(5, ge=1, le=20, description="Maximum final recommendations")

    # Health goals
    user_health_goals: Optional[Dict[str, Any]] = Field(
        None, description="User health goals for nutrition analysis"
    )

    # Recipe selection
    selected_recipe_id: Optional[int] = Field(None, description="Recipe to deduct ingredients for")
    commit_deduction: bool = Field(
        False, description="Whether to actually deduct ingredients from pantry"
    )


class QuickRecommendationRequest(BaseModel):
    """Request for quick recipe recommendations"""

    user_id: str = Field(..., description="User ID")
    max_recipes: int = Field(3, ge=1, le=10, description="Maximum number of recipes to return")


class CrewHealthResponse(BaseModel):
    """Response for crew health check"""

    status: str
    crew_name: str
    agents: Dict[str, str]
    enabled_features: List[str]
    timestamp: str


class WorkflowResponse(BaseModel):
    """Response for workflow execution"""

    status: str
    message: str
    timestamp: str
    user_id: Optional[str]
    recommendations: Optional[List[Dict[str, Any]]] = None
    workflow_summary: Optional[Dict[str, Any]] = None
    steps: Optional[Dict[str, Any]] = None


# Router setup
router = APIRouter(
    prefix="/crewai",
    tags=["CrewAI Intelligence"],
    responses={404: {"description": "Not found"}},
)

# Global crew instances (lazy initialization)
main_crew = None
pantry_crew = None


def get_main_crew() -> PrepSenseMainCrew:
    """Get or create main crew instance"""
    global main_crew
    if not CREWAI_AVAILABLE:
        raise HTTPException(status_code=503, detail="CrewAI system not available")

    if main_crew is None:
        try:
            main_crew = PrepSenseMainCrew()
            logger.info("PrepSense main crew initialized")
        except Exception as e:
            logger.error(f"Failed to initialize main crew: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize CrewAI system: {str(e)}"
            )

    return main_crew


def get_pantry_crew() -> PantryNormalizationCrew:
    """Get or create pantry normalization crew instance"""
    global pantry_crew
    if not CREWAI_AVAILABLE:
        raise HTTPException(status_code=503, detail="CrewAI system not available")

    if pantry_crew is None:
        try:
            pantry_crew = PantryNormalizationCrew()
            logger.info("Pantry normalization crew initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pantry crew: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize pantry normalization: {str(e)}"
            )

    return pantry_crew


@router.get("/health", response_model=CrewHealthResponse)
async def crew_health_check():
    """Check the health of CrewAI system"""
    if not CREWAI_AVAILABLE:
        return CrewHealthResponse(
            status="unavailable",
            crew_name="none",
            agents={},
            enabled_features=[],
            timestamp=_get_timestamp(),
        )

    try:
        crew = get_main_crew()
        health_data = await crew.health_check()

        return CrewHealthResponse(
            status=health_data["status"],
            crew_name=health_data["crew"],
            agents=health_data["agents"],
            enabled_features=health_data["enabled_features"],
            timestamp=_get_timestamp(),
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return CrewHealthResponse(
            status="error",
            crew_name="unknown",
            agents={"error": str(e)},
            enabled_features=[],
            timestamp=_get_timestamp(),
        )


@router.get("/workflow/description")
async def get_workflow_description():
    """Get description of the complete CrewAI workflow"""
    try:
        crew = get_main_crew()
        return crew.get_workflow_description()
    except Exception as e:
        logger.error(f"Failed to get workflow description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pantry/normalize", response_model=WorkflowResponse)
async def normalize_pantry(request: PantryNormalizationRequest):
    """
    Run pantry normalization workflow only.
    Processes raw food items into normalized, categorized inventory.
    """
    try:
        crew = get_pantry_crew()

        input_data = {
            "image_b64": request.image_b64,
            "raw_items": request.raw_items,
            "user_id": request.user_id,
            "freshness_days": request.freshness_days,
        }

        logger.info(f"Starting pantry normalization for user {request.user_id}")
        result = await crew.run(input_data)

        return WorkflowResponse(
            status="success",
            message=f"Pantry normalization completed. Processed {len(result)} items.",
            timestamp=_get_timestamp(),
            user_id=request.user_id,
            recommendations=result,
            workflow_summary={
                "normalized_items": len(result),
                "workflow": "pantry_normalization_only",
            },
        )

    except Exception as e:
        logger.error(f"Pantry normalization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pantry normalization failed: {str(e)}")


@router.post("/workflow/complete", response_model=WorkflowResponse)
async def run_complete_workflow(request: PrepSenseWorkflowRequest):
    """
    Run the complete PrepSense workflow.
    End-to-end intelligent recipe recommendation with pantry management.
    """
    try:
        crew = get_main_crew()

        input_data = request.dict()

        logger.info(f"Starting complete PrepSense workflow for user {request.user_id}")
        result = await crew.run(input_data)

        return WorkflowResponse(**result)

    except Exception as e:
        logger.error(f"Complete workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")


@router.post("/recipes/quick", response_model=WorkflowResponse)
async def quick_recipe_recommendations(request: QuickRecommendationRequest):
    """
    Get quick recipe recommendations based on current pantry.
    Bypasses image processing and uses existing pantry inventory.
    """
    try:
        crew = get_main_crew()

        logger.info(f"Starting quick recommendations for user {request.user_id}")
        result = await crew.quick_recipe_recommendation(request.user_id, request.max_recipes)

        return WorkflowResponse(**result)

    except Exception as e:
        logger.error(f"Quick recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quick recommendations failed: {str(e)}")


@router.post("/recipes/select")
async def select_recipe(
    user_id: str = Query(..., description="User ID"),
    recipe_id: int = Query(..., description="Recipe ID to select"),
    commit_deduction: bool = Query(False, description="Whether to deduct ingredients from pantry"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Select a recipe and optionally deduct ingredients from pantry.
    """
    try:
        crew = get_main_crew()

        # Run workflow with specific recipe selection
        input_data = {
            "user_id": user_id,
            "selected_recipe_id": recipe_id,
            "commit_deduction": commit_deduction,
            "max_recipes": 1,  # Only process the selected recipe
        }

        if commit_deduction:
            logger.info(f"Deducting ingredients for recipe {recipe_id} for user {user_id}")
        else:
            logger.info(
                f"Checking ingredient availability for recipe {recipe_id} for user {user_id}"
            )

        # For now, we need to get the recipe details first, then run pantry ledger
        # This is a simplified implementation
        pantry_ledger = crew.pantry_ledger

        # Mock recipe for ingredient matching (in real implementation, would fetch from database/API)
        mock_recipe = [{"recipe_id": recipe_id, "ingredients": []}]  # Would need actual recipe data

        result = await pantry_ledger.run(mock_recipe, user_id, recipe_id, commit_deduction)

        action = "deducted" if commit_deduction else "checked"
        return {
            "status": "success",
            "message": f"Successfully {action} ingredients for recipe {recipe_id}",
            "recipe_id": recipe_id,
            "user_id": user_id,
            "pantry_match": result[0].get("pantry_match", {}) if result else {},
            "deduction_performed": commit_deduction,
        }

    except Exception as e:
        logger.error(f"Recipe selection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recipe selection failed: {str(e)}")


@router.get("/pantry/summary/{user_id}")
async def get_pantry_summary(user_id: str):
    """Get summary of user's pantry inventory"""
    try:
        crew = get_main_crew()
        pantry_ledger = crew.pantry_ledger

        summary = await pantry_ledger.get_pantry_summary(user_id)

        return {
            "status": "success",
            "user_id": user_id,
            "pantry_summary": summary,
            "timestamp": _get_timestamp(),
        }

    except Exception as e:
        logger.error(f"Pantry summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pantry summary failed: {str(e)}")


@router.get("/status")
async def crewai_status():
    """Get overall status of CrewAI system"""
    return {
        "crewai_available": CREWAI_AVAILABLE,
        "main_crew_initialized": main_crew is not None,
        "pantry_crew_initialized": pantry_crew is not None,
        "environment_flags": {
            "ENABLE_BITE_CAM": os.getenv("ENABLE_BITE_CAM", "true"),
            "ENABLE_FRESH_FILTER_AGENT": os.getenv("ENABLE_FRESH_FILTER_AGENT", "true"),
            "ENABLE_JUDGE_THYME": os.getenv("ENABLE_JUDGE_THYME", "true"),
        },
        "timestamp": _get_timestamp(),
    }


def _get_timestamp() -> str:
    """Get current timestamp"""
    from datetime import datetime

    return datetime.now().isoformat()


# Error handlers for development
@router.get("/test/import")
async def test_imports():
    """Test endpoint to verify imports work correctly"""
    try:
        from src.agents.bite_cam import BiteCam
        from src.agents.food_categorizer import FoodCategorizer
        from src.agents.fresh_filter import FreshFilter
        from src.agents.judge_thyme import JudgeThyme
        from src.agents.nutri_check import NutriCheck
        from src.agents.pantry_ledger import PantryLedger
        from src.agents.recipe_search import RecipeSearch
        from src.agents.unit_canon import UnitCanon
        from src.agents.user_preferences import UserPreferences
        from src.crews.pantry_normalization import PantryNormalizationCrew
        from src.crews.prepsense_main import PrepSenseMainCrew

        return {
            "status": "success",
            "message": "All CrewAI imports successful",
            "agents": [
                "BiteCam",
                "FoodCategorizer",
                "UnitCanon",
                "FreshFilter",
                "RecipeSearch",
                "NutriCheck",
                "UserPreferences",
                "JudgeThyme",
                "PantryLedger",
            ],
            "crews": ["PantryNormalizationCrew", "PrepSenseMainCrew"],
        }
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Import failed: {str(e)}",
            "suggestion": "Ensure src/ directory and all agent files are properly created",
        }
