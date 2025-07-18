"""API endpoints for nutrition tracking and dietary intake logging."""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from ..models.nutrition import (
    LogMealRequest, LogMealResponse, GetNutrientGapsRequest, GetNutrientGapsResponse,
    NutrientAwareRecipeRequest, NutrientProfile, MealType, NutrientGapAnalysis
)
from ..services.nutrient_aware_crew_service import NutrientAwareCrewService
from ..services.nutrient_auditor_service import NutrientAuditorService
# For now, use a simple function to get user ID
def get_current_user_id() -> int:
    """Get current user ID - simplified for now."""
    return 111  # Default user ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nutrition", tags=["nutrition"])

# Initialize services
nutrient_crew_service = NutrientAwareCrewService()
nutrient_auditor_service = NutrientAuditorService()

@router.post("/log-meal", response_model=LogMealResponse)
async def log_meal(
    request: LogMealRequest,
    user_id: int = Depends(get_current_user_id)
):
    """Log a meal for dietary tracking."""
    try:
        logger.info(f"Logging meal for user {user_id}: {request.meal_type} - {request.food_name}")
        
        # Convert request to meal data
        meal_data = {
            "meal_type": request.meal_type,
            "food_name": request.food_name,
            "quantity": request.quantity,
            "serving_unit": request.serving_unit,
            "brand": request.brand,
            "notes": request.notes
        }
        
        # Log the meal using the nutrient-aware service
        result = await nutrient_crew_service.log_meal_and_update_gaps(user_id, meal_data)
        
        if result["success"]:
            # For now, return a placeholder response
            # In a real implementation, this would return actual nutrient data
            return LogMealResponse(
                meal_id=result["meal_id"],
                nutrients_added=NutrientProfile(
                    calories=250.0,
                    protein=15.0,
                    carbohydrates=30.0,
                    fiber=5.0
                ),
                daily_total=NutrientProfile(
                    calories=1200.0,
                    protein=45.0,
                    carbohydrates=150.0,
                    fiber=18.0
                ),
                message="Meal logged successfully"
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Error logging meal: {e}")
        raise HTTPException(status_code=500, detail="Failed to log meal")

@router.get("/gaps", response_model=GetNutrientGapsResponse)
async def get_nutrient_gaps(
    analysis_date: Optional[date] = Query(None, description="Date for analysis (defaults to today)"),
    period_days: int = Query(1, description="Number of days to analyze (1 = single day, 7 = weekly)"),
    user_id: int = Depends(get_current_user_id)
):
    """Get nutrient gap analysis for a user."""
    try:
        logger.info(f"Getting nutrient gaps for user {user_id}")
        
        if analysis_date is None:
            analysis_date = date.today()
        
        # Get the gap analysis
        gap_analysis = nutrient_auditor_service.get_gap_analysis(str(user_id), analysis_date)
        
        if not gap_analysis:
            # Create a sample analysis if none exists
            gap_analysis = await nutrient_crew_service._create_sample_nutrient_analysis(user_id)
        
        # Get recommendations
        recommendations = nutrient_auditor_service.get_nutrient_recommendations(gap_analysis)
        
        # Generate priority message
        priority_message = nutrient_crew_service.nutrient_auditor.generate_priority_message(gap_analysis)
        
        return GetNutrientGapsResponse(
            analysis=gap_analysis,
            recommendations=recommendations,
            priority_message=priority_message
        )
        
    except Exception as e:
        logger.error(f"Error getting nutrient gaps: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nutrient gaps")

@router.post("/recipe-recommendations")
async def get_nutrient_aware_recipes(
    request: NutrientAwareRecipeRequest,
    user_id: int = Depends(get_current_user_id)
):
    """Get recipe recommendations with nutrient gap awareness."""
    try:
        logger.info(f"Getting nutrient-aware recipes for user {user_id}")
        
        # Default message based on focus nutrients or meal type
        message = "What can I cook?"
        
        if request.focus_nutrients:
            nutrient_names = [n.replace('_', ' ').title() for n in request.focus_nutrients]
            message = f"I need recipes high in {', '.join(nutrient_names)}"
        elif request.meal_type:
            message = f"What can I make for {request.meal_type}?"
        
        # Get nutrient-aware recommendations
        result = await nutrient_crew_service.process_message_with_nutrition(
            user_id=user_id,
            message=message,
            use_preferences=True,
            include_nutrient_gaps=request.include_nutrient_gaps
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting nutrient-aware recipes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recipe recommendations")

@router.get("/daily-intake/{target_date}")
async def get_daily_intake(
    target_date: date,
    user_id: int = Depends(get_current_user_id)
):
    """Get daily dietary intake for a specific date."""
    try:
        logger.info(f"Getting daily intake for user {user_id} on {target_date}")
        
        # In a real implementation, this would fetch from dietary intake database
        # For now, return a placeholder response
        return JSONResponse(content={
            "user_id": user_id,
            "date": target_date.isoformat(),
            "meals": [],
            "total_nutrients": {
                "calories": 0,
                "protein": 0,
                "carbohydrates": 0,
                "fiber": 0,
                "total_fat": 0,
                "sodium": 0
            },
            "water_intake": 0.0
        })
        
    except Exception as e:
        logger.error(f"Error getting daily intake: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily intake")

@router.post("/analyze-food")
async def analyze_food(
    food_name: str,
    quantity: float = 1.0,
    serving_unit: str = "serving",
    user_id: int = Depends(get_current_user_id)
):
    """Analyze nutritional content of a food item."""
    try:
        logger.info(f"Analyzing food: {food_name} ({quantity} {serving_unit})")
        
        # In a real implementation, this would use USDA database or food recognition API
        # For now, return estimated nutrition
        estimated_nutrition = {
            "food_name": food_name,
            "quantity": quantity,
            "serving_unit": serving_unit,
            "nutrients": {
                "calories": 150.0,
                "protein": 8.0,
                "carbohydrates": 25.0,
                "fiber": 3.0,
                "total_fat": 2.0,
                "sodium": 300.0,
                "sugar": 5.0
            },
            "confidence": 0.7,
            "data_source": "estimated"
        }
        
        return JSONResponse(content=estimated_nutrition)
        
    except Exception as e:
        logger.error(f"Error analyzing food: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze food")

@router.get("/nutrition-goals")
async def get_nutrition_goals(
    user_id: int = Depends(get_current_user_id)
):
    """Get personalized nutrition goals for a user."""
    try:
        logger.info(f"Getting nutrition goals for user {user_id}")
        
        # In a real implementation, this would be personalized based on user profile
        # For now, return standard RDA values
        from ..config.nutrient_config import RDA_VALUES, NUTRIENT_DISPLAY_NAMES, NUTRIENT_UNITS
        
        goals = {}
        for nutrient, rda_value in RDA_VALUES.items():
            goals[nutrient] = {
                "target": rda_value,
                "display_name": NUTRIENT_DISPLAY_NAMES.get(nutrient, nutrient),
                "unit": NUTRIENT_UNITS.get(nutrient, "g"),
                "is_upper_limit": nutrient in ["sodium", "saturated_fat", "cholesterol", "sugar"]
            }
        
        return JSONResponse(content={
            "user_id": user_id,
            "goals": goals,
            "personalized": False,
            "notes": "Standard RDA values - personalization coming soon"
        })
        
    except Exception as e:
        logger.error(f"Error getting nutrition goals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nutrition goals")

@router.post("/sync-health-data")
async def sync_health_data(
    data_source: str,
    health_data: Dict,
    user_id: int = Depends(get_current_user_id)
):
    """Sync health data from external sources (Apple Health, Google Fit, etc.)."""
    try:
        logger.info(f"Syncing health data from {data_source} for user {user_id}")
        
        # In a real implementation, this would:
        # 1. Validate the data source and format
        # 2. Parse health data (meals, nutrients, water intake)
        # 3. Store in dietary intake database
        # 4. Trigger nutrient gap analysis update
        
        return JSONResponse(content={
            "success": True,
            "message": f"Health data synced from {data_source}",
            "records_processed": len(health_data.get("records", [])),
            "sync_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error syncing health data: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync health data")

@router.get("/nutrition-insights")
async def get_nutrition_insights(
    period_days: int = Query(7, description="Number of days to analyze"),
    user_id: int = Depends(get_current_user_id)
):
    """Get nutrition insights and trends for a user."""
    try:
        logger.info(f"Getting nutrition insights for user {user_id} over {period_days} days")
        
        # In a real implementation, this would analyze trends in dietary intake
        # For now, return placeholder insights
        return JSONResponse(content={
            "user_id": user_id,
            "period_days": period_days,
            "insights": [
                {
                    "type": "deficiency_trend",
                    "message": "Your fiber intake has been consistently low this week",
                    "recommendation": "Add more fruits, vegetables, and whole grains to your meals"
                },
                {
                    "type": "positive_trend", 
                    "message": "Great job maintaining adequate protein intake!",
                    "recommendation": "Keep including protein sources in every meal"
                },
                {
                    "type": "excess_warning",
                    "message": "Sodium intake is above recommended levels",
                    "recommendation": "Try reducing processed foods and restaurant meals"
                }
            ],
            "overall_score": 72.5,
            "improvement_potential": "High - focus on fiber and sodium balance"
        })
        
    except Exception as e:
        logger.error(f"Error getting nutrition insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nutrition insights")