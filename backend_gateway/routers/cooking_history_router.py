"""Router for cooking history and trends data"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query

from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cooking-history",
    tags=["Cooking History"],
    responses={404: {"description": "Not found"}},
)


@router.get("/trends", summary="Get cooking trends data")
async def get_cooking_trends(
    user_id: int = Query(111, description="User ID"),
    days: int = Query(30, description="Number of days to look back"),
    db_service=Depends(get_database_service),
) -> dict[str, Any]:
    """
    Get cooking trends data from pantry history

    Returns cooking frequency and popular recipes based on pantry usage
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query for recipe-based pantry changes
        query = """
        SELECT
            DATE(changed_at) as cook_date,
            recipe_name,
            recipe_id,
            COUNT(DISTINCT changed_at) as times_cooked
        FROM pantry_history
        WHERE user_id = %(user_id)s
          AND changed_at >= %(start_date)s
          AND recipe_name IS NOT NULL
          AND change_source = 'recipe'
        GROUP BY DATE(changed_at), recipe_name, recipe_id
        ORDER BY cook_date DESC
        """

        cooking_events = db_service.execute_query(
            query, {"user_id": user_id, "start_date": start_date}
        )

        # Process data for daily counts
        daily_counts = {}
        recipe_counts = {}

        for event in cooking_events:
            # Daily cooking frequency
            date_str = event["cook_date"].strftime("%Y-%m-%d")
            if date_str not in daily_counts:
                daily_counts[date_str] = 0
            daily_counts[date_str] += 1

            # Recipe popularity
            recipe_name = event["recipe_name"]
            if recipe_name not in recipe_counts:
                recipe_counts[recipe_name] = 0
            recipe_counts[recipe_name] += event["times_cooked"]

        # Get recipes cooked in different time periods
        week_ago = end_date - timedelta(days=7)
        month_ago = end_date - timedelta(days=30)

        week_query = """
        SELECT COUNT(DISTINCT DATE(changed_at)) as days_cooked,
               COUNT(DISTINCT recipe_name) as unique_recipes
        FROM pantry_history
        WHERE user_id = %(user_id)s
          AND changed_at >= %(start_date)s
          AND recipe_name IS NOT NULL
          AND change_source = 'recipe'
        """

        week_stats = db_service.execute_query(
            week_query, {"user_id": user_id, "start_date": week_ago}
        )[0]

        month_stats = db_service.execute_query(
            week_query, {"user_id": user_id, "start_date": month_ago}
        )[0]

        # Calculate cooking streak
        streak_query = """
        SELECT DISTINCT DATE(changed_at) as cook_date
        FROM pantry_history
        WHERE user_id = %(user_id)s
          AND recipe_name IS NOT NULL
          AND change_source = 'recipe'
        ORDER BY cook_date DESC
        """

        cook_dates = db_service.execute_query(streak_query, {"user_id": user_id})

        # Calculate streak
        streak = 0
        if cook_dates:
            today = datetime.now().date()
            expected_date = today

            for record in cook_dates:
                cook_date = record["cook_date"]
                if cook_date == expected_date:
                    streak += 1
                    expected_date = expected_date - timedelta(days=1)
                else:
                    break

        # Sort recipes by popularity
        top_recipes = sorted(recipe_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "summary": {
                "total_days": days,
                "days_cooked_this_week": week_stats["days_cooked"] or 0,
                "days_cooked_this_month": month_stats["days_cooked"] or 0,
                "unique_recipes_this_week": week_stats["unique_recipes"] or 0,
                "unique_recipes_this_month": month_stats["unique_recipes"] or 0,
                "cooking_streak": streak,
            },
            "daily_counts": daily_counts,
            "top_recipes": [{"name": name, "count": count} for name, count in top_recipes],
            "cooking_events": len(cooking_events),
        }

    except Exception as e:
        logger.error(f"Error fetching cooking trends: {str(e)}")
        return {
            "summary": {
                "total_days": days,
                "days_cooked_this_week": 0,
                "days_cooked_this_month": 0,
                "unique_recipes_this_week": 0,
                "unique_recipes_this_month": 0,
                "cooking_streak": 0,
            },
            "daily_counts": {},
            "top_recipes": [],
            "cooking_events": 0,
            "error": str(e),
        }


@router.get("/calendar", summary="Get cooking calendar data")
async def get_cooking_calendar(
    user_id: int = Query(111, description="User ID"),
    year: int = Query(datetime.now().year, description="Year"),
    month: int = Query(datetime.now().month, description="Month"),
    db_service=Depends(get_database_service),
) -> dict[str, Any]:
    """
    Get cooking calendar data for a specific month
    """
    try:
        # Calculate date range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        query = """
        SELECT
            DATE(changed_at) as cook_date,
            recipe_name,
            COUNT(*) as ingredients_used
        FROM pantry_history
        WHERE user_id = %(user_id)s
          AND changed_at >= %(start_date)s
          AND changed_at <= %(end_date)s
          AND recipe_name IS NOT NULL
          AND change_source = 'recipe'
        GROUP BY DATE(changed_at), recipe_name
        ORDER BY cook_date
        """

        events = db_service.execute_query(
            query, {"user_id": user_id, "start_date": start_date, "end_date": end_date}
        )

        # Group by date
        calendar_data = {}
        for event in events:
            date_str = event["cook_date"].strftime("%Y-%m-%d")
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            calendar_data[date_str].append(
                {"recipe": event["recipe_name"], "ingredients_used": event["ingredients_used"]}
            )

        return {
            "year": year,
            "month": month,
            "cooking_days": calendar_data,
            "total_cooking_days": len(calendar_data),
            "total_recipes": len(events),
        }

    except Exception as e:
        logger.error(f"Error fetching cooking calendar: {str(e)}")
        return {
            "year": year,
            "month": month,
            "cooking_days": {},
            "total_cooking_days": 0,
            "total_recipes": 0,
            "error": str(e),
        }
