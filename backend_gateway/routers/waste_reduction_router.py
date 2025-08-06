"""
Waste Reduction Router - API endpoints for food waste prevention
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend_gateway.agents.waste_reduction_agent import create_waste_reduction_agent
from backend_gateway.config.database import get_database_service
from backend_gateway.services.food_waste_service import get_food_waste_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/waste-reduction", tags=["waste reduction"])


@router.get("/pantry-risk-analysis/{user_id}")
async def analyze_pantry_waste_risk(user_id: str):
    """
    Analyze waste risk for all items in user's pantry

    Returns items prioritized by waste risk with recommendations
    """
    try:
        # Get user's pantry items
        postgres_service = get_database_service()

        query = """
            SELECT 
                pi.pantry_item_id,
                pi.product_name,
                pi.quantity,
                pi.unit_of_measurement,
                pi.expiration_date,
                pi.category,
                pi.created_at,
                p.ghg_kg_co2e_per_kg,
                p.planet_score
            FROM pantry_items pi
            LEFT JOIN products p ON LOWER(pi.product_name) = LOWER(p.product_name)
            WHERE pi.pantry_id IN (
                SELECT pantry_id FROM pantries WHERE user_id = %s
            )
            AND pi.status = 'available'
            AND pi.quantity > 0
        """

        items = postgres_service.execute_query(query, {"user_id": user_id})

        if not items:
            return {"user_id": user_id, "total_items": 0, "high_risk_count": 0, "items": []}

        # Convert to format expected by waste service
        pantry_data = []
        for item in items:
            pantry_data.append(
                {
                    "pantry_item_id": item["pantry_item_id"],
                    "product_name": item["product_name"],
                    "quantity": float(item["quantity"]) if item["quantity"] else 1.0,
                    "unit": item["unit_of_measurement"],
                    "expiry_date": item["expiration_date"],
                    "category": item["category"],
                }
            )

        # Analyze waste risk
        waste_service = get_food_waste_service()
        prioritized_items = waste_service.prioritize_pantry_by_waste_risk(pantry_data)

        # Calculate summary statistics
        high_risk_count = sum(
            1 for item in prioritized_items if item["risk_category"] in ["very_high", "high"]
        )

        total_potential_waste = sum(
            item.get("quantity_at_risk", 0) * item.get("base_loss_rate", 0)
            for item in prioritized_items
        )

        return {
            "user_id": user_id,
            "total_items": len(prioritized_items),
            "high_risk_count": high_risk_count,
            "potential_waste_kg": round(total_potential_waste, 2),
            "analysis_date": datetime.now().isoformat(),
            "items": prioritized_items[:20],  # Top 20 items
            "summary": {
                "immediate_action": [
                    item["product_name"]
                    for item in prioritized_items[:3]
                    if item["risk_category"] == "very_high"
                ],
                "use_soon": [
                    item["product_name"]
                    for item in prioritized_items[:5]
                    if item["risk_category"] == "high"
                ],
            },
        }

    except Exception as e:
        logger.error(f"Error analyzing pantry waste risk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/food-waste-rate/{food_name}")
async def get_food_waste_rate(food_name: str):
    """
    Get typical waste rate for a specific food

    Based on FAO Food Loss and Waste data
    """
    try:
        waste_service = get_food_waste_service()
        loss_rate = waste_service.get_loss_rate(food_name)

        # Get category for context
        category = "Other"
        if any(item in food_name.lower() for item in ["apple", "banana", "tomato", "lettuce"]):
            category = "Fruits & Vegetables"
        elif any(item in food_name.lower() for item in ["beef", "chicken", "pork"]):
            category = "Meat"
        elif any(item in food_name.lower() for item in ["milk", "cheese", "yogurt"]):
            category = "Dairy"

        return {
            "food_name": food_name,
            "waste_rate_percentage": round(loss_rate * 100, 1),
            "category": category,
            "comparison": "high" if loss_rate > 0.20 else "average" if loss_rate > 0.10 else "low",
            "tips": f"Foods like {food_name} typically have {round(loss_rate * 100)}% waste at consumer level",
        }

    except Exception as e:
        logger.error(f"Error getting waste rate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/waste-smart-recipes")
async def get_waste_smart_recipes(
    user_id: str, recipe_ids: List[str] = Query(..., description="List of available recipe IDs")
):
    """
    Prioritize recipes based on waste reduction potential

    Ranks recipes by how well they use high-waste-risk pantry items
    """
    try:
        # Get high-risk pantry items
        risk_analysis = await analyze_pantry_waste_risk(user_id)
        high_risk_items = (
            risk_analysis["summary"]["immediate_action"] + risk_analysis["summary"]["use_soon"]
        )

        if not high_risk_items:
            return {"message": "No high-risk items found in pantry", "prioritized_recipes": []}

        # Get recipe details (simplified - would fetch from recipe service)
        # For now, return recipe IDs with mock scores
        waste_service = get_food_waste_service()

        prioritized = []
        for recipe_id in recipe_ids[:10]:  # Limit to 10 recipes
            # Mock scoring - in production would analyze actual ingredients
            score = 50  # Base score

            # Higher score if recipe name contains high-risk items
            recipe_name_lower = recipe_id.lower()
            for item in high_risk_items:
                if item.lower() in recipe_name_lower:
                    score += 30

            prioritized.append(
                {
                    "recipe_id": recipe_id,
                    "waste_reduction_score": score,
                    "uses_high_risk_items": [
                        item for item in high_risk_items if item.lower() in recipe_name_lower
                    ],
                }
            )

        # Sort by score
        prioritized.sort(key=lambda x: x["waste_reduction_score"], reverse=True)

        return {"high_risk_items": high_risk_items, "prioritized_recipes": prioritized[:5]}

    except Exception as e:
        logger.error(f"Error prioritizing recipes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/waste-impact-calculator")
async def calculate_waste_impact(
    food_name: str,
    quantity_kg: float = Query(..., description="Quantity in kilograms"),
    price_per_kg: Optional[float] = Query(None, description="Price per kilogram"),
):
    """
    Calculate economic and environmental impact of potential food waste
    """
    try:
        waste_service = get_food_waste_service()
        impact = waste_service.calculate_waste_impact(food_name, quantity_kg, price_per_kg)

        # Add environmental impact if available
        from backend_gateway.services.environmental_impact_service import (
            get_environmental_impact_service,
        )

        env_service = get_environmental_impact_service()
        env_data = env_service.get_food_impact(food_name)

        if env_data:
            ghg = env_data["environmental"].get("ghg_kg_co2e_per_kg", 0)
            potential_ghg = impact["potential_waste_kg"] * ghg
            impact["environmental_impact"] = {
                "ghg_kg_co2e": round(potential_ghg, 2),
                "driving_miles_equivalent": round(potential_ghg * 2.5, 1),
            }

        return impact

    except Exception as e:
        logger.error(f"Error calculating waste impact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly-waste-prevention-plan/{user_id}")
async def create_waste_prevention_plan(user_id: str):
    """
    Create a personalized weekly waste prevention plan

    Uses CrewAI Waste Reduction Agent for intelligent recommendations
    """
    try:
        # Get user's pantry data
        postgres_service = get_database_service()

        query = """
            SELECT 
                pi.product_name,
                pi.quantity,
                pi.unit_of_measurement,
                pi.expiration_date,
                pi.category
            FROM pantry_items pi
            WHERE pi.pantry_id IN (
                SELECT pantry_id FROM pantries WHERE user_id = %s
            )
            AND pi.status = 'available'
            AND pi.quantity > 0
        """

        items = postgres_service.execute_query(query, {"user_id": user_id})

        # Create agent and generate plan
        agent = create_waste_reduction_agent()
        pantry_data = {"user_id": user_id, "items": items}

        plan = agent.create_weekly_waste_prevention_plan(pantry_data)

        return plan

    except Exception as e:
        logger.error(f"Error creating waste prevention plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/waste-tracking-summary/{user_id}")
async def get_waste_tracking_summary(
    user_id: str, days: int = Query(30, description="Number of days to look back")
):
    """
    Get summary of user's food waste tracking

    Shows trends and comparisons to averages
    """
    try:
        postgres_service = get_database_service()

        # Get waste tracking data
        query = """
            SELECT 
                DATE(recorded_at) as waste_date,
                SUM(quantity_wasted) as total_waste_kg,
                SUM(estimated_value) as total_value_lost,
                SUM(ghg_impact) as total_ghg_impact,
                COUNT(*) as items_wasted
            FROM user_food_waste
            WHERE user_id = %s
            AND recorded_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(recorded_at)
            ORDER BY waste_date DESC
        """

        daily_waste = postgres_service.execute_query(query, {"user_id": user_id, "days": days})

        # Calculate totals and averages
        total_waste = sum(day["total_waste_kg"] or 0 for day in daily_waste)
        total_value = sum(day["total_value_lost"] or 0 for day in daily_waste)
        total_ghg = sum(day["total_ghg_impact"] or 0 for day in daily_waste)

        avg_daily_waste = total_waste / days if days > 0 else 0

        # Compare to national average (placeholder values)
        national_avg_daily = 0.5  # kg per person per day
        comparison = "below" if avg_daily_waste < national_avg_daily else "above"

        return {
            "user_id": user_id,
            "period_days": days,
            "summary": {
                "total_waste_kg": round(total_waste, 2),
                "total_value_lost": round(total_value, 2),
                "total_ghg_impact": round(total_ghg, 2),
                "avg_daily_waste_kg": round(avg_daily_waste, 3),
                "comparison_to_average": comparison,
                "national_avg_daily_kg": national_avg_daily,
            },
            "daily_breakdown": daily_waste[:7],  # Last 7 days
            "insights": {
                "trend": (
                    "decreasing"
                    if len(daily_waste) > 1
                    and daily_waste[0]["total_waste_kg"] < daily_waste[-1]["total_waste_kg"]
                    else "stable"
                ),
                "equivalent_meals_lost": int(total_waste / 0.5),  # Assume 0.5kg per meal
                "trees_needed_to_offset": round(total_ghg / 21.77, 1),  # kg CO2 per tree per year
            },
        }

    except Exception as e:
        logger.error(f"Error getting waste tracking summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-waste")
async def record_food_waste(
    user_id: str,
    product_name: str,
    quantity: float,
    unit: str = "kg",
    reason: str = Query("expired", description="Reason for waste: expired, spoiled, excess, other"),
    estimated_value: Optional[float] = None,
):
    """
    Record food waste for tracking and analytics
    """
    try:
        postgres_service = get_database_service()

        # Convert to kg if needed
        quantity_kg = quantity
        if unit.lower() in ["g", "grams"]:
            quantity_kg = quantity / 1000
        elif unit.lower() in ["lb", "lbs", "pounds"]:
            quantity_kg = quantity * 0.453592

        # Get environmental impact
        from backend_gateway.services.environmental_impact_service import (
            get_environmental_impact_service,
        )

        env_service = get_environmental_impact_service()
        env_data = env_service.get_food_impact(product_name)

        ghg_impact = 0
        if env_data:
            ghg = env_data["environmental"].get("ghg_kg_co2e_per_kg", 0)
            ghg_impact = quantity_kg * ghg

        # Record waste
        query = """
            INSERT INTO user_food_waste (
                user_id, product_name, quantity_wasted, unit,
                reason, estimated_value, ghg_impact, recorded_at
            ) VALUES (
                %(user_id)s, %(product_name)s, %(quantity)s, %(unit)s,
                %(reason)s, %(value)s, %(ghg)s, CURRENT_TIMESTAMP
            ) RETURNING id
        """

        result = postgres_service.execute_query(
            query,
            {
                "user_id": user_id,
                "product_name": product_name,
                "quantity": quantity_kg,
                "unit": "kg",
                "reason": reason,
                "value": estimated_value,
                "ghg": ghg_impact,
            },
        )

        return {
            "id": result[0]["id"],
            "message": "Waste recorded successfully",
            "impact": {
                "quantity_kg": quantity_kg,
                "ghg_impact": round(ghg_impact, 2),
                "estimated_value": estimated_value,
            },
        }

    except Exception as e:
        logger.error(f"Error recording waste: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
