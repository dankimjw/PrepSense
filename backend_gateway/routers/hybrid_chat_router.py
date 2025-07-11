"""
Hybrid Chat Router - Combines fast generation with quality evaluation
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from backend_gateway.services.hybrid_crew_service import HybridCrewService
from backend_gateway.routers.users import get_current_active_user
from backend_gateway.models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat/hybrid",
    tags=["Hybrid Chat"],
    responses={404: {"description": "Not found"}},
)


class HybridChatRequest(BaseModel):
    message: str = Field(..., description="User's message/request")
    user_id: int = Field(default=111, description="User ID")
    use_preferences: bool = Field(default=True, description="Use dietary preferences")
    evaluate_quality: bool = Field(default=True, description="Run quality evaluation")
    evaluate_top_n: int = Field(default=3, description="Number of recipes to evaluate", ge=1, le=10)
    comparison_mode: bool = Field(default=False, description="Compare with/without evaluation")


class QualityEvaluation(BaseModel):
    quality_score: int = Field(..., ge=1, le=5)
    critique: str
    suggestion: str
    nutrition_score: int = Field(..., ge=0, le=100)
    preference_match: bool


class EnhancedRecipe(BaseModel):
    id: str
    title: str
    readyInMinutes: int
    match_score: float
    expected_joy: int
    quality_evaluation: Optional[QualityEvaluation] = None
    ingredients: List[str]
    instructions: List[str]


class HybridChatResponse(BaseModel):
    response: str
    recipes: List[Dict[str, Any]]
    evaluated_recipes: List[Dict[str, Any]]
    performance: Dict[str, float]
    comparison: Optional[Dict[str, Any]] = None


def get_hybrid_service():
    return HybridCrewService()


@router.post("/message", response_model=HybridChatResponse)
async def send_hybrid_message(
    request: HybridChatRequest,
    hybrid_service: HybridCrewService = Depends(get_hybrid_service)
):
    """
    Send a message to the hybrid AI system that:
    1. Generates recipes quickly with OpenAI
    2. Evaluates top recipes with CrewAI agents
    3. Returns both fast results and quality-evaluated results
    """
    try:
        logger.info(f"Hybrid request: evaluate_quality={request.evaluate_quality}, top_n={request.evaluate_top_n}")
        
        # Get enhanced results
        result = await hybrid_service.generate_and_evaluate_recipes(
            user_id=request.user_id,
            message=request.message,
            use_preferences=request.use_preferences,
            evaluate_top_n=request.evaluate_top_n if request.evaluate_quality else 0
        )
        
        # Separate evaluated vs non-evaluated recipes
        all_recipes = result.get('recipes', [])
        evaluated_recipes = [r for r in all_recipes if r.get('quality_evaluated', False)]
        
        response = HybridChatResponse(
            response=result.get('response', ''),
            recipes=all_recipes,
            evaluated_recipes=evaluated_recipes,
            performance=result.get('performance', {})
        )
        
        # If comparison mode, also run without evaluation
        if request.comparison_mode and request.evaluate_quality:
            logger.info("Running comparison mode...")
            
            # Get results without evaluation
            no_eval_result = await hybrid_service.generate_and_evaluate_recipes(
                user_id=request.user_id,
                message=request.message,
                use_preferences=request.use_preferences,
                evaluate_top_n=0  # No evaluation
            )
            
            response.comparison = {
                'with_evaluation': {
                    'total_time': result['performance']['total_time'],
                    'quality_recipes': len(evaluated_recipes),
                    'average_quality': sum(r.get('evaluation_score', 0) for r in evaluated_recipes) / len(evaluated_recipes) if evaluated_recipes else 0
                },
                'without_evaluation': {
                    'total_time': no_eval_result['performance']['total_time'],
                    'recipes_count': len(no_eval_result['recipes'])
                },
                'time_difference': result['performance']['total_time'] - no_eval_result['performance']['total_time'],
                'quality_improvement': 'Recipes evaluated for quality, nutrition, and preferences'
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in hybrid chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process hybrid request: {str(e)}"
        )


@router.get("/comparison-demo")
async def run_comparison_demo(
    message: str = "What can I make for dinner?",
    user_id: int = 111,
    hybrid_service: HybridCrewService = Depends(get_hybrid_service)
):
    """
    Demo endpoint to show the difference between:
    1. Fast generation only (2-3 seconds)
    2. Generation + quality evaluation (5-8 seconds)
    
    This demonstrates the trade-off between speed and quality.
    """
    try:
        # Run both approaches
        fast_only = await hybrid_service.generate_and_evaluate_recipes(
            user_id=user_id,
            message=message,
            use_preferences=True,
            evaluate_top_n=0  # No evaluation
        )
        
        with_quality = await hybrid_service.generate_and_evaluate_recipes(
            user_id=user_id,
            message=message,
            use_preferences=True,
            evaluate_top_n=3  # Evaluate top 3
        )
        
        # Compare results
        comparison = {
            'test_parameters': {
                'message': message,
                'user_id': user_id,
                'recipes_evaluated': 3
            },
            'fast_approach': {
                'time': fast_only['performance']['total_time'],
                'recipes_generated': len(fast_only['recipes']),
                'quality_assurance': 'None',
                'cost_estimate': '$0.02'
            },
            'quality_approach': {
                'time': with_quality['performance']['total_time'],
                'recipes_generated': len(with_quality['recipes']),
                'recipes_evaluated': len([r for r in with_quality['recipes'] if r.get('quality_evaluated')]),
                'quality_assurance': 'Claude AI evaluation + nutrition analysis + preference matching',
                'cost_estimate': '$0.05'
            },
            'recommendations': {
                'use_fast_only': [
                    'User needs quick suggestions',
                    'Cost is primary concern',
                    'User is experienced cook'
                ],
                'use_quality_evaluation': [
                    'First-time users',
                    'Special occasions',
                    'Users with strict dietary needs',
                    'Quality is priority over speed'
                ]
            }
        }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error in comparison demo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run comparison: {str(e)}"
        )