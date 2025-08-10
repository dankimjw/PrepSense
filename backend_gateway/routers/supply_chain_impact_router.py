"""
Supply Chain Impact Router - API endpoints for showing full supply chain waste impact
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from backend_gateway.config.database import get_database_service
from backend_gateway.services.environmental_impact_service import get_environmental_impact_service
from backend_gateway.services.food_waste_service import get_food_waste_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supply-chain-impact", tags=["supply chain impact"])

# Load supply chain analysis data
SUPPLY_CHAIN_DATA = {}
try:
    supply_chain_file = Path("data/food_loss_waste/supply_chain_analysis.json")
    if supply_chain_file.exists():
        with open(supply_chain_file) as f:
            SUPPLY_CHAIN_DATA = json.load(f)
except Exception as e:
    logger.warning(f"Could not load supply chain data: {e}")


@router.get("/today-impact/{user_id}")
async def get_today_impact(user_id: str):
    """
    Calculate today's supply chain impact based on expiring items

    Shows the amplified environmental impact when accounting for upstream losses
    """
    try:
        # Get user's pantry items expiring in next 3 days
        db_service = get_database_service()

        query = """
            SELECT
                pi.product_name,
                pi.quantity,
                pi.unit_of_measurement,
                pi.expiration_date,
                p.ghg_kg_co2e_per_kg,
                p.impact_category
            FROM pantry_items pi
            LEFT JOIN products p ON LOWER(pi.product_name) = LOWER(p.product_name)
            WHERE pi.pantry_id IN (
                SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s
            )
            AND pi.status = 'available'
            AND pi.expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days'
        """

        expiring_items = db_service.execute_query(query, {"user_id": user_id})

        if not expiring_items:
            return {
                "user_id": user_id,
                "items_at_risk": 0,
                "total_co2e": 0,
                "supply_chain_multiplier": 0,
                "economic_value": 0,
                "message": "No items expiring in the next 3 days",
            }

        # Calculate supply chain impact
        get_food_waste_service()
        get_environmental_impact_service()

        total_co2e = 0
        total_value = 0
        total_multiplier_weighted = 0
        weight_sum = 0

        for item in expiring_items:
            # Estimate quantity in kg
            quantity_kg = float(item["quantity"]) if item["quantity"] else 1.0
            if item["unit_of_measurement"] in ["g", "grams"]:
                quantity_kg = quantity_kg / 1000
            elif item["unit_of_measurement"] in ["lb", "lbs"]:
                quantity_kg = quantity_kg * 0.453592

            # Get supply chain multiplier
            food_name = item["product_name"].lower()
            multiplier = get_supply_chain_multiplier(food_name)

            # Get environmental impact
            ghg_per_kg = item["ghg_kg_co2e_per_kg"] or estimate_ghg_impact(food_name)

            # Calculate amplified impact
            amplified_co2e = quantity_kg * ghg_per_kg * multiplier
            total_co2e += amplified_co2e

            # Estimate economic value
            price_per_kg = estimate_price(food_name)
            total_value += quantity_kg * price_per_kg

            # Weight multiplier by quantity
            total_multiplier_weighted += multiplier * quantity_kg
            weight_sum += quantity_kg

        avg_multiplier = total_multiplier_weighted / weight_sum if weight_sum > 0 else 1.8

        return {
            "user_id": user_id,
            "date": datetime.now().date().isoformat(),
            "items_at_risk": len(expiring_items),
            "total_co2e": round(total_co2e, 1),
            "supply_chain_multiplier": round(avg_multiplier, 2),
            "economic_value": round(total_value, 2),
            "driving_equivalent_miles": round(total_co2e * 2.5, 0),
            "trees_to_offset": round(total_co2e / 21.77, 1),
            "items": [
                {
                    "name": item["product_name"],
                    "days_left": (item["expiration_date"] - datetime.now().date()).days,
                    "quantity": item["quantity"],
                    "unit": item["unit_of_measurement"],
                    "multiplier": get_supply_chain_multiplier(item["product_name"].lower()),
                }
                for item in expiring_items
            ],
        }

    except Exception as e:
        logger.error(f"Error calculating today's impact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/supply-chain-guide")
async def get_supply_chain_guide():
    """
    Get educational information about supply chain waste multipliers

    Returns data about which foods have highest upstream impact
    """
    try:
        # Define supply chain multipliers by food category
        multiplier_guide = [
            {
                "food": "Lettuce",
                "multiplier": 5.7,
                "supply_chain_loss_pct": 82.5,
                "consumer_loss_pct": 14.4,
                "co2e_per_kg": 1.5,
                "amplified_co2e": 8.6,
                "description": "Extremely high post-harvest losses due to short shelf life",
                "key_insight": "Only 17.5% of lettuce produced reaches consumers",
            },
            {
                "food": "Tomatoes",
                "multiplier": 2.52,
                "supply_chain_loss_pct": 60.3,
                "consumer_loss_pct": 9.6,
                "co2e_per_kg": 2.09,
                "amplified_co2e": 5.3,
                "description": "High losses during transport and storage",
                "key_insight": "For every 1kg wasted, 2.52kg was originally grown",
            },
            {
                "food": "Bananas",
                "multiplier": 2.86,
                "supply_chain_loss_pct": 65.0,
                "consumer_loss_pct": 26.0,
                "co2e_per_kg": 0.86,
                "amplified_co2e": 2.5,
                "description": "Significant losses due to ripening during transport",
                "key_insight": "Long supply chains from tropical regions increase waste",
            },
            {
                "food": "Rice",
                "multiplier": 1.60,
                "supply_chain_loss_pct": 37.7,
                "consumer_loss_pct": 17.8,
                "co2e_per_kg": 4.45,
                "amplified_co2e": 7.1,
                "description": "Better storage characteristics reduce supply chain losses",
                "key_insight": "Grains generally have lower multipliers than fresh produce",
            },
            {
                "food": "Beef",
                "multiplier": 1.8,  # Estimated
                "supply_chain_loss_pct": 44.4,
                "consumer_loss_pct": 11.0,
                "co2e_per_kg": 99.48,
                "amplified_co2e": 179.1,
                "description": "Lower percentage losses but massive CO2 impact",
                "key_insight": "Even small waste has enormous environmental cost",
            },
        ]

        # Calculate summary statistics
        avg_multiplier = sum(item["multiplier"] for item in multiplier_guide) / len(
            multiplier_guide
        )
        highest_impact = max(multiplier_guide, key=lambda x: x["amplified_co2e"])
        highest_multiplier = max(multiplier_guide, key=lambda x: x["multiplier"])

        return {
            "multiplier_guide": multiplier_guide,
            "summary": {
                "average_multiplier": round(avg_multiplier, 2),
                "highest_impact_food": highest_impact["food"],
                "highest_multiplier_food": highest_multiplier["food"],
                "key_message": "Fresh produce has the highest supply chain losses, but animal products have the highest total environmental impact when wasted",
            },
            "insights": [
                "Supply chain losses are highest for perishable items like leafy greens",
                "Even foods with lower multipliers can have massive CO2 impact",
                "Preventing household waste saves the entire upstream production impact",
                "Fresh produce deserves highest priority in waste prevention",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting supply chain guide: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/weekly-trends/{user_id}")
async def get_weekly_trends(
    user_id: str, weeks: int = Query(4, description="Number of weeks to analyze")
):
    """
    Get weekly trends showing prevented vs wasted impact over time
    """
    try:
        db_service = get_database_service()

        # Get waste tracking data
        query = """
            SELECT
                DATE_TRUNC('week', recorded_at) as week,
                COUNT(*) as items_wasted,
                SUM(quantity_wasted) as total_kg_wasted,
                SUM(ghg_impact) as total_co2e
            FROM user_food_waste
            WHERE user_id = %(user_id)s
            AND recorded_at >= CURRENT_DATE - INTERVAL '%(weeks)s weeks'
            GROUP BY DATE_TRUNC('week', recorded_at)
            ORDER BY week DESC
        """

        waste_data = db_service.execute_query(query, {"user_id": user_id, "weeks": weeks})

        # Calculate prevented waste (items that expired but weren't recorded as waste)
        prevented_query = """
            SELECT
                DATE_TRUNC('week', expiration_date) as week,
                COUNT(*) as items_expired,
                AVG(quantity) as avg_quantity
            FROM pantry_items pi
            WHERE pi.pantry_id IN (
                SELECT pantry_id FROM pantries WHERE user_id = %(user_id)s
            )
            AND expiration_date >= CURRENT_DATE - INTERVAL '%(weeks)s weeks'
            AND expiration_date < CURRENT_DATE
            GROUP BY DATE_TRUNC('week', expiration_date)
            ORDER BY week DESC
        """

        expired_data = db_service.execute_query(
            prevented_query, {"user_id": user_id, "weeks": weeks}
        )

        # Combine data and estimate prevented waste
        weekly_trends = []
        for week_data in expired_data:
            week = week_data["week"]

            # Find corresponding waste data
            waste_week = next((w for w in waste_data if w["week"] == week), None)

            items_expired = week_data["items_expired"]
            items_wasted = waste_week["items_wasted"] if waste_week else 0
            items_prevented = max(0, items_expired - items_wasted)

            # Estimate CO2 impact of prevented waste
            avg_co2_per_item = 3.5  # Estimated average
            prevented_co2e = items_prevented * avg_co2_per_item * 2.2  # Apply multiplier

            weekly_trends.append(
                {
                    "week": week.isoformat(),
                    "items_expired": items_expired,
                    "items_wasted": items_wasted,
                    "items_prevented": items_prevented,
                    "waste_rate": round(
                        (items_wasted / items_expired * 100) if items_expired > 0 else 0, 1
                    ),
                    "prevented_co2e": round(prevented_co2e, 1),
                    "wasted_co2e": round(waste_week["total_co2e"] if waste_week else 0, 1),
                }
            )

        # Calculate totals
        total_prevented = sum(w["items_prevented"] for w in weekly_trends)
        total_wasted = sum(w["items_wasted"] for w in weekly_trends)
        total_prevented_co2e = sum(w["prevented_co2e"] for w in weekly_trends)

        return {
            "user_id": user_id,
            "period_weeks": weeks,
            "weekly_data": weekly_trends,
            "summary": {
                "total_items_prevented": total_prevented,
                "total_items_wasted": total_wasted,
                "prevention_rate": round(
                    (
                        (total_prevented / (total_prevented + total_wasted) * 100)
                        if (total_prevented + total_wasted) > 0
                        else 0
                    ),
                    1,
                ),
                "total_co2e_saved": round(total_prevented_co2e, 1),
                "driving_miles_saved": round(total_prevented_co2e * 2.5, 0),
                "trend": (
                    "improving"
                    if len(weekly_trends) > 1
                    and weekly_trends[0]["waste_rate"] < weekly_trends[-1]["waste_rate"]
                    else "stable"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting weekly trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


def get_supply_chain_multiplier(food_name: str) -> float:
    """Get supply chain multiplier for a food item"""
    food_lower = food_name.lower()

    # High multiplier foods (fresh produce with high supply chain losses)
    if any(term in food_lower for term in ["lettuce", "spinach", "arugula", "kale"]):
        return 5.7  # Lettuce-like leafy greens
    elif any(term in food_lower for term in ["tomato", "cucumber", "pepper", "zucchini"]):
        return 2.52  # Fresh vegetables
    elif any(term in food_lower for term in ["banana", "avocado", "mango", "papaya"]):
        return 2.86  # Tropical fruits
    elif any(term in food_lower for term in ["strawberr", "raspberr", "blueberr", "grape"]):
        return 2.8  # Berries and soft fruits
    elif any(term in food_lower for term in ["apple", "orange", "lemon", "lime"]):
        return 2.0  # Tree fruits
    elif any(term in food_lower for term in ["carrot", "potato", "onion", "cabbage"]):
        return 2.2  # Root vegetables and hardy produce
    elif any(term in food_lower for term in ["beef", "pork", "lamb", "chicken"]):
        return 1.8  # Meat products
    elif any(term in food_lower for term in ["milk", "cheese", "yogurt", "butter"]):
        return 1.6  # Dairy products
    elif any(term in food_lower for term in ["rice", "pasta", "bread", "cereal"]):
        return 1.5  # Grains and processed foods
    else:
        return 1.8  # Default multiplier


def estimate_ghg_impact(food_name: str) -> float:
    """Estimate GHG impact for foods without data"""
    food_lower = food_name.lower()

    if any(term in food_lower for term in ["beef", "steak", "ground beef"]):
        return 99.48
    elif any(term in food_lower for term in ["lamb", "mutton"]):
        return 39.2
    elif any(term in food_lower for term in ["pork", "bacon", "ham"]):
        return 12.1
    elif any(term in food_lower for term in ["chicken", "turkey", "poultry"]):
        return 9.87
    elif any(term in food_lower for term in ["fish", "salmon", "tuna"]):
        return 6.0
    elif any(term in food_lower for term in ["cheese"]):
        return 23.88
    elif any(term in food_lower for term in ["milk"]):
        return 3.15
    elif any(term in food_lower for term in ["rice"]):
        return 4.45
    elif any(term in food_lower for term in ["tomato"]):
        return 2.09
    elif any(term in food_lower for term in ["potato"]):
        return 0.46
    else:
        return 2.0  # Default for vegetables/fruits


def estimate_price(food_name: str) -> float:
    """Estimate price per kg for economic impact calculation"""
    food_lower = food_name.lower()

    if any(term in food_lower for term in ["beef", "steak"]):
        return 20.0
    elif any(term in food_lower for term in ["chicken", "turkey"]):
        return 8.0
    elif any(term in food_lower for term in ["fish", "salmon"]):
        return 15.0
    elif any(term in food_lower for term in ["cheese"]):
        return 12.0
    elif any(term in food_lower for term in ["berry", "grape"]):
        return 8.0
    elif any(term in food_lower for term in ["tomato", "pepper"]):
        return 4.0
    elif any(term in food_lower for term in ["lettuce", "spinach"]):
        return 6.0
    else:
        return 5.0  # Default price per kg
