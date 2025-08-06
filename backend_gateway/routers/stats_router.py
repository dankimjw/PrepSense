"""Router for comprehensive user statistics including pantry, recipes, and sustainability metrics"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from backend_gateway.config.database import get_database_service
from backend_gateway.core.security import get_current_user
from backend_gateway.services.user_recipes_service import UserRecipesService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/stats",
    tags=["Statistics"],
    responses={404: {"description": "Not found"}},
)


def get_user_recipes_service(db_service=Depends(get_database_service)) -> UserRecipesService:
    """Dependency to get UserRecipesService instance"""
    return UserRecipesService(db_service)


@router.get(
    "/comprehensive", response_model=Dict[str, Any], summary="Get comprehensive user statistics"
)
async def get_comprehensive_stats(
    user_id: int = Query(111, description="User ID"),
    timeframe: str = Query("month", description="Timeframe: week, month, year"),
    db_service=Depends(get_database_service),
    user_recipes_service: UserRecipesService = Depends(get_user_recipes_service),
):
    """Get comprehensive statistics including pantry, recipes, and sustainability metrics"""
    try:
        # Calculate date range
        now = datetime.now()
        if timeframe == "week":
            start_date = now - timedelta(days=7)
        elif timeframe == "month":
            start_date = now - timedelta(days=30)
        elif timeframe == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)  # Default to month

        # 1. Pantry Statistics
        pantry_stats_query = """
        WITH pantry_summary AS (
            SELECT
                COUNT(*) as total_items,
                COUNT(CASE WHEN expiration_date < CURRENT_DATE THEN 1 END) as expired_items,
                COUNT(CASE WHEN expiration_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days' THEN 1 END) as expiring_soon,
                COUNT(CASE WHEN pi.created_at >= %(start_date)s THEN 1 END) as recently_added,
                AVG(pi.quantity) as avg_quantity
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            WHERE p.user_id = %(user_id)s
        ),
        category_breakdown AS (
            SELECT 
                pi.category,
                COUNT(*) as count
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            WHERE p.user_id = %(user_id)s
            GROUP BY pi.category
            ORDER BY count DESC
            LIMIT 5
        ),
        frequent_items AS (
            SELECT 
                pi.product_name,
                COUNT(*) as purchase_count
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            WHERE p.user_id = %(user_id)s
            AND pi.created_at >= %(start_date)s
            GROUP BY pi.product_name
            ORDER BY purchase_count DESC
            LIMIT 5
        )
        SELECT 
            ps.*,
            (SELECT json_agg(row_to_json(cb)) FROM category_breakdown cb) as top_categories,
            (SELECT json_agg(row_to_json(fi)) FROM frequent_items fi) as top_products
        FROM pantry_summary ps
        """

        pantry_result = db_service.execute_query(
            pantry_stats_query, {"user_id": user_id, "start_date": start_date}
        )

        # 2. Recipe Statistics
        recipe_stats = await user_recipes_service.get_recipe_stats(user_id)

        # 3. Cooking History Statistics
        cooking_history_query = """
        WITH daily_cooking AS (
            SELECT 
                DATE(changed_at) as cook_date,
                COUNT(*) as recipes_cooked
            FROM pantry_history
            WHERE user_id = %(user_id)s
            AND change_source = 'recipe_completion'
            AND changed_at >= %(start_date)s
            GROUP BY DATE(changed_at)
        ),
        cooking_streak AS (
            SELECT 
                cook_date,
                cook_date - (ROW_NUMBER() OVER (ORDER BY cook_date))::int AS grp
            FROM daily_cooking
        ),
        streak_groups AS (
            SELECT 
                MIN(cook_date) as start_date,
                MAX(cook_date) as end_date,
                COUNT(*) as streak_length
            FROM cooking_streak
            GROUP BY grp
            ORDER BY end_date DESC
            LIMIT 1
        )
        SELECT 
            COUNT(DISTINCT DATE(changed_at)) as days_cooked,
            COUNT(*) as total_recipes_cooked,
            COALESCE((SELECT streak_length FROM streak_groups), 0) as current_streak,
            COUNT(CASE WHEN changed_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as cooked_this_week,
            COUNT(CASE WHEN changed_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as cooked_this_month
        FROM pantry_history
        WHERE user_id = %(user_id)s
        AND change_source = 'recipe_completion'
        AND changed_at >= %(start_date)s
        """

        cooking_result = db_service.execute_query(
            cooking_history_query, {"user_id": user_id, "start_date": start_date}
        )

        # 4. Sustainability Metrics
        sustainability_query = """
        WITH waste_prevention AS (
            SELECT 
                COUNT(CASE WHEN pi.expiration_date >= CURRENT_DATE THEN 1 END) as unexpired_items,
                COUNT(CASE WHEN ph.change_source = 'recipe_completion' THEN 1 END) as items_used_in_recipes
            FROM pantry_items pi
            JOIN pantries p ON pi.pantry_id = p.pantry_id
            LEFT JOIN pantry_history ph ON pi.pantry_item_id = ph.pantry_item_id
            WHERE p.user_id = %(user_id)s
        )
        SELECT 
            unexpired_items * 0.3 as food_saved_kg,  -- Avg 0.3kg per item
            unexpired_items * 0.3 * 2.5 as co2_saved_kg,  -- 2.5kg CO2 per kg food
            items_used_in_recipes
        FROM waste_prevention
        """

        sustainability_result = db_service.execute_query(sustainability_query, {"user_id": user_id})

        # 5. Shopping Patterns
        shopping_patterns_query = """
        SELECT 
            DATE_PART('dow', pi.created_at) as day_of_week,
            COUNT(*) as items_added
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = %(user_id)s
        AND pi.created_at >= %(start_date)s
        GROUP BY DATE_PART('dow', pi.created_at)
        ORDER BY day_of_week
        """

        shopping_result = db_service.execute_query(
            shopping_patterns_query, {"user_id": user_id, "start_date": start_date}
        )

        # Compile all statistics
        stats = {
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat(),
            "pantry": {
                "summary": {
                    "total_items": pantry_result[0]["total_items"] if pantry_result else 0,
                    "expired_items": pantry_result[0]["expired_items"] if pantry_result else 0,
                    "expiring_soon": pantry_result[0]["expiring_soon"] if pantry_result else 0,
                    "recently_added": pantry_result[0]["recently_added"] if pantry_result else 0,
                    "avg_quantity": (
                        float(pantry_result[0]["avg_quantity"] or 0) if pantry_result else 0
                    ),
                },
                "top_categories": pantry_result[0]["top_categories"] if pantry_result else [],
                "top_products": pantry_result[0]["top_products"] if pantry_result else [],
            },
            "recipes": {
                **recipe_stats,
                "cooking_history": {
                    "days_cooked": cooking_result[0]["days_cooked"] if cooking_result else 0,
                    "total_cooked": (
                        cooking_result[0]["total_recipes_cooked"] if cooking_result else 0
                    ),
                    "current_streak": cooking_result[0]["current_streak"] if cooking_result else 0,
                    "cooked_this_week": (
                        cooking_result[0]["cooked_this_week"] if cooking_result else 0
                    ),
                    "cooked_this_month": (
                        cooking_result[0]["cooked_this_month"] if cooking_result else 0
                    ),
                },
            },
            "sustainability": {
                "food_saved_kg": (
                    float(sustainability_result[0]["food_saved_kg"] or 0)
                    if sustainability_result
                    else 0
                ),
                "co2_saved_kg": (
                    float(sustainability_result[0]["co2_saved_kg"] or 0)
                    if sustainability_result
                    else 0
                ),
                "items_used_in_recipes": (
                    sustainability_result[0]["items_used_in_recipes"]
                    if sustainability_result
                    else 0
                ),
            },
            "shopping_patterns": {
                "by_day_of_week": [
                    {
                        "day": [
                            "Sunday",
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                        ][int(item["day_of_week"])],
                        "items_added": item["items_added"],
                    }
                    for item in shopping_result
                ]
            },
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting comprehensive stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get(
    "/milestones", response_model=Dict[str, Any], summary="Get user milestones and achievements"
)
async def get_user_milestones(
    user_id: int = Query(111, description="User ID"),
    db_service=Depends(get_database_service),
):
    """Get user milestones and achievements"""
    try:
        milestones_query = """
        WITH user_stats AS (
            SELECT 
                (SELECT COUNT(*) FROM user_pantry_full WHERE user_id = %(user_id)s) as total_pantry_items,
                (SELECT COUNT(*) FROM pantry_history WHERE user_id = %(user_id)s AND change_source = 'recipe_completion') as total_recipes_cooked,
                (SELECT COUNT(DISTINCT DATE(changed_at)) FROM pantry_history WHERE user_id = %(user_id)s AND change_source = 'recipe_completion') as days_cooked,
                (SELECT COUNT(*) FROM user_recipes WHERE user_id = %(user_id)s AND is_favorite = true) as favorite_recipes,
                (SELECT COUNT(*) FROM user_recipes WHERE user_id = %(user_id)s AND rating = 'thumbs_up') as liked_recipes
        )
        SELECT * FROM user_stats
        """

        result = db_service.execute_query(milestones_query, {"user_id": user_id})

        if not result:
            return {"milestones": [], "achievements": []}

        stats = result[0]
        milestones = []

        # Define milestone thresholds
        milestone_definitions = [
            # Pantry milestones
            {
                "condition": stats["total_pantry_items"] >= 1,
                "title": "First Item Added",
                "emoji": "🎉",
                "category": "pantry",
            },
            {
                "condition": stats["total_pantry_items"] >= 10,
                "title": "Pantry Starter",
                "emoji": "📦",
                "category": "pantry",
            },
            {
                "condition": stats["total_pantry_items"] >= 25,
                "title": "Well Stocked",
                "emoji": "🏪",
                "category": "pantry",
            },
            {
                "condition": stats["total_pantry_items"] >= 50,
                "title": "Pantry Pro",
                "emoji": "🌟",
                "category": "pantry",
            },
            {
                "condition": stats["total_pantry_items"] >= 100,
                "title": "Master Stocker",
                "emoji": "👑",
                "category": "pantry",
            },
            # Recipe milestones
            {
                "condition": stats["total_recipes_cooked"] >= 1,
                "title": "First Recipe",
                "emoji": "🍳",
                "category": "cooking",
            },
            {
                "condition": stats["total_recipes_cooked"] >= 5,
                "title": "Getting Started",
                "emoji": "👨‍🍳",
                "category": "cooking",
            },
            {
                "condition": stats["total_recipes_cooked"] >= 10,
                "title": "Home Cook",
                "emoji": "🏠",
                "category": "cooking",
            },
            {
                "condition": stats["total_recipes_cooked"] >= 25,
                "title": "Kitchen Regular",
                "emoji": "🔥",
                "category": "cooking",
            },
            {
                "condition": stats["total_recipes_cooked"] >= 50,
                "title": "Master Chef",
                "emoji": "👨‍🍳",
                "category": "cooking",
            },
            {
                "condition": stats["total_recipes_cooked"] >= 100,
                "title": "Culinary Expert",
                "emoji": "⭐",
                "category": "cooking",
            },
            # Streak milestones
            {
                "condition": stats["days_cooked"] >= 3,
                "title": "3 Day Streak",
                "emoji": "🔥",
                "category": "streak",
            },
            {
                "condition": stats["days_cooked"] >= 7,
                "title": "Week Warrior",
                "emoji": "💪",
                "category": "streak",
            },
            {
                "condition": stats["days_cooked"] >= 30,
                "title": "Monthly Master",
                "emoji": "🏆",
                "category": "streak",
            },
            # Engagement milestones
            {
                "condition": stats["favorite_recipes"] >= 5,
                "title": "Recipe Collector",
                "emoji": "❤️",
                "category": "engagement",
            },
            {
                "condition": stats["liked_recipes"] >= 10,
                "title": "Recipe Critic",
                "emoji": "👍",
                "category": "engagement",
            },
        ]

        # Filter achieved milestones
        achieved_milestones = [m for m in milestone_definitions if m["condition"]]

        return {
            "milestones": achieved_milestones,
            "stats": stats,
            "next_milestones": [
                m
                for m in milestone_definitions
                if not m["condition"]
                and any(am["category"] == m["category"] for am in achieved_milestones)
            ][
                :3
            ],  # Show next 3 potential milestones
        }

    except Exception as e:
        logger.error(f"Error getting milestones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get milestones: {str(e)}")
