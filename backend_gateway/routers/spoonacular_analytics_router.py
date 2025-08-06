"""
Spoonacular Analytics Router

🟡 IMPLEMENTATION STATUS: PARTIAL - Endpoints working, database integration pending
This router provides API endpoints for Spoonacular API usage analytics,
cost monitoring, and deduplication insights.

Endpoints:
- GET /usage/daily - Daily usage statistics
- GET /usage/user/{user_id} - User-specific usage
- GET /cost/projection - Cost projections and trends
- GET /deduplication/stats - Deduplication effectiveness
- GET /performance/endpoints - Endpoint performance metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# This import will work once the database table is created
try:
    from backend_gateway.config.database import get_database_service
    from backend_gateway.services.recipe_deduplication_service import RecipeDeduplicationService
    from backend_gateway.services.spoonacular_api_tracker import SpoonacularAPITracker
except ImportError as e:
    logging.warning(f"Could not import services: {e}")
    # For development/testing, provide mock implementations
    get_database_service = None
    SpoonacularAPITracker = None
    RecipeDeduplicationService = None

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/spoonacular-analytics",
    tags=["spoonacular-analytics"],
    responses={404: {"description": "Not found"}},
)


# Dependency to get analytics tracker
def get_analytics_tracker():
    """Get the Spoonacular API tracker instance."""
    try:
        db_service = get_database_service() if get_database_service else None
        return SpoonacularAPITracker(db_service=db_service)
    except Exception as e:
        logger.error(f"Error creating analytics tracker: {str(e)}")
        raise HTTPException(status_code=500, detail="Analytics service unavailable")


@router.get("/usage/daily")
async def get_daily_usage(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format, defaults to today"),
    tracker: SpoonacularAPITracker = Depends(get_analytics_tracker),
) -> Dict[str, Any]:
    """
    Get daily Spoonacular API usage statistics.

    🟡 IMPLEMENTATION STATUS: PARTIAL - Endpoint working, database integration pending
    This endpoint provides comprehensive daily usage metrics including:
    - Total API calls and recipe count
    - Cache hit rates and duplicate detection rates
    - Cost analysis and error rates
    - Endpoint performance breakdown

    Args:
        date: Specific date to analyze (YYYY-MM-DD format)

    Returns:
        Daily usage statistics dictionary
    """
    try:
        # Parse date or use today
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            target_date = datetime.now().date()

        # Calculate days from target date to now for the query
        days_back = (datetime.now().date() - target_date).days + 1

        # Get usage statistics for the specific day
        stats = tracker.get_usage_stats(days=days_back)

        # Get call history for detailed breakdown
        call_history = tracker.get_call_history(hours=24 * days_back, limit=1000)

        # Filter calls for the specific date
        target_calls = [
            call
            for call in call_history
            if call.get("call_timestamp", datetime.min).date() == target_date
        ]

        # Analyze endpoint usage
        endpoint_breakdown = {}
        for call in target_calls:
            endpoint = call.get("endpoint", "unknown")
            if endpoint not in endpoint_breakdown:
                endpoint_breakdown[endpoint] = {
                    "call_count": 0,
                    "total_recipes": 0,
                    "total_cost": 0,
                    "cache_hits": 0,
                    "duplicates_detected": 0,
                    "errors": 0,
                    "avg_response_time": 0,
                }

            breakdown = endpoint_breakdown[endpoint]
            breakdown["call_count"] += 1
            breakdown["total_recipes"] += call.get("recipe_count", 0)
            breakdown["total_cost"] += call.get("cost_points", 0)

            if call.get("cache_hit", False):
                breakdown["cache_hits"] += 1
            if call.get("duplicate_detected", False):
                breakdown["duplicates_detected"] += 1
            if call.get("response_status", 200) >= 400:
                breakdown["errors"] += 1

            # Average response time calculation would be done here

        return {
            "date": target_date.isoformat(),
            "summary": {
                "total_calls": len(target_calls),
                "total_recipes": sum(call.get("recipe_count", 0) for call in target_calls),
                "total_cost_points": sum(call.get("cost_points", 0) for call in target_calls),
                "cache_hit_rate": (
                    len([c for c in target_calls if c.get("cache_hit", False)]) / len(target_calls)
                    if target_calls
                    else 0
                ),
                "duplicate_detection_rate": (
                    len([c for c in target_calls if c.get("duplicate_detected", False)])
                    / len(target_calls)
                    if target_calls
                    else 0
                ),
                "error_rate": (
                    len([c for c in target_calls if c.get("response_status", 200) >= 400])
                    / len(target_calls)
                    if target_calls
                    else 0
                ),
                "unique_users": len(
                    set(call.get("user_id") for call in target_calls if call.get("user_id"))
                ),
                "unique_endpoints": len(set(call.get("endpoint") for call in target_calls)),
            },
            "endpoint_breakdown": endpoint_breakdown,
            "implementation_status": "🟡 PARTIAL - Endpoint working, database integration pending",
        }

    except Exception as e:
        logger.error(f"Error getting daily usage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving daily usage: {str(e)}")


@router.get("/usage/user/{user_id}")
async def get_user_usage(
    user_id: int,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze (1-90)"),
    tracker: SpoonacularAPITracker = Depends(get_analytics_tracker),
) -> Dict[str, Any]:
    """
    Get user-specific Spoonacular API usage analytics.

    🟡 IMPLEMENTATION STATUS: PARTIAL - Endpoint working, database integration pending
    This endpoint provides detailed user usage patterns:
    - Personal API consumption patterns
    - Favorite endpoints and usage frequency
    - Cost efficiency metrics
    - Recipe discovery patterns

    Args:
        user_id: ID of the user to analyze
        days: Number of days to analyze (1-90)

    Returns:
        User-specific usage analytics
    """
    try:
        # Get user-specific statistics
        user_stats = tracker.get_usage_stats(user_id=user_id, days=days)

        # Get detailed call history for the user
        user_calls = tracker.get_call_history(user_id=user_id, hours=24 * days, limit=500)

        # Analyze user patterns
        endpoint_preferences = {}
        daily_usage = {}

        for call in user_calls:
            # Endpoint preferences
            endpoint = call.get("endpoint", "unknown")
            endpoint_preferences[endpoint] = endpoint_preferences.get(endpoint, 0) + 1

            # Daily usage pattern
            call_date = call.get("call_timestamp", datetime.min).date().isoformat()
            if call_date not in daily_usage:
                daily_usage[call_date] = {"calls": 0, "recipes": 0}
            daily_usage[call_date]["calls"] += 1
            daily_usage[call_date]["recipes"] += call.get("recipe_count", 0)

        # Calculate efficiency metrics
        total_recipes_found = sum(call.get("recipe_count", 0) for call in user_calls)
        total_cost = sum(call.get("cost_points", 0) for call in user_calls)
        cost_per_recipe = total_cost / total_recipes_found if total_recipes_found > 0 else 0

        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "summary": user_stats,
            "patterns": {
                "favorite_endpoints": dict(
                    sorted(endpoint_preferences.items(), key=lambda x: x[1], reverse=True)
                ),
                "daily_usage": daily_usage,
                "cost_efficiency": {
                    "total_recipes_found": total_recipes_found,
                    "total_cost_points": total_cost,
                    "cost_per_recipe": round(cost_per_recipe, 4),
                    "efficiency_rating": (
                        "high"
                        if cost_per_recipe < 0.1
                        else "medium" if cost_per_recipe < 0.3 else "low"
                    ),
                },
            },
            "recommendations": {
                "cache_utilization": (
                    "good" if user_stats.get("cache_hit_rate", 0) > 0.5 else "could_improve"
                ),
                "suggested_improvements": [
                    (
                        "Use bulk endpoints for multiple recipes"
                        if endpoint_preferences.get("information", 0)
                        > endpoint_preferences.get("informationBulk", 0)
                        else None
                    ),
                    (
                        "Consider caching frequently accessed recipes"
                        if user_stats.get("cache_hit_rate", 0) < 0.3
                        else None
                    ),
                ],
            },
            "implementation_status": "🟡 PARTIAL - Endpoint working, database integration pending",
        }

    except Exception as e:
        logger.error(f"Error getting user usage for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving user usage: {str(e)}")


@router.get("/cost/projection")
async def get_cost_projection(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to project (1-365)"),
    tracker: SpoonacularAPITracker = Depends(get_analytics_tracker),
) -> Dict[str, Any]:
    """
    Get API cost projections based on usage patterns.

    🟡 IMPLEMENTATION STATUS: PARTIAL - Endpoint working, database integration pending
    This endpoint provides:
    - Cost projections based on historical usage
    - Trend analysis and seasonal patterns
    - Budget recommendations
    - Cost optimization suggestions

    Args:
        days_ahead: Number of days ahead for projection

    Returns:
        Cost projection and analysis
    """
    try:
        # Get historical usage for trend analysis
        historical_stats_7d = tracker.get_usage_stats(days=7)
        historical_stats_30d = tracker.get_usage_stats(days=30)

        # Calculate daily average costs
        daily_cost_7d = historical_stats_7d.get("total_cost_points", 0) / 7
        daily_cost_30d = historical_stats_30d.get("total_cost_points", 0) / 30

        # Project based on recent trends (weighted average favoring recent data)
        projected_daily_cost = (daily_cost_7d * 0.7) + (daily_cost_30d * 0.3)
        projected_total_cost = projected_daily_cost * days_ahead

        # Estimate monthly cost (assuming consistent usage)
        monthly_projection = projected_daily_cost * 30

        # Cost efficiency analysis
        daily_recipes_7d = historical_stats_7d.get("total_recipes", 0) / 7
        cost_per_recipe = projected_daily_cost / daily_recipes_7d if daily_recipes_7d > 0 else 0

        # Usage growth trend
        growth_rate = (
            ((daily_cost_7d - daily_cost_30d) / daily_cost_30d * 100) if daily_cost_30d > 0 else 0
        )

        return {
            "projection_period_days": days_ahead,
            "historical_analysis": {
                "last_7_days": {
                    "total_cost_points": historical_stats_7d.get("total_cost_points", 0),
                    "daily_average": round(daily_cost_7d, 2),
                    "total_calls": historical_stats_7d.get("total_calls", 0),
                    "total_recipes": historical_stats_7d.get("total_recipes", 0),
                },
                "last_30_days": {
                    "total_cost_points": historical_stats_30d.get("total_cost_points", 0),
                    "daily_average": round(daily_cost_30d, 2),
                    "total_calls": historical_stats_30d.get("total_calls", 0),
                    "total_recipes": historical_stats_30d.get("total_recipes", 0),
                },
            },
            "projections": {
                "projected_daily_cost": round(projected_daily_cost, 2),
                "projected_total_cost": round(projected_total_cost, 2),
                "projected_monthly_cost": round(monthly_projection, 2),
                "growth_rate_percent": round(growth_rate, 1),
            },
            "efficiency_metrics": {
                "cost_per_recipe": round(cost_per_recipe, 4),
                "projected_recipes_per_day": round(daily_recipes_7d, 1),
                "cache_hit_rate": historical_stats_7d.get("cache_hit_rate", 0),
                "duplicate_detection_rate": historical_stats_7d.get("duplicate_detection_rate", 0),
            },
            "recommendations": {
                "budget_status": (
                    "within_normal"
                    if growth_rate < 20
                    else "increasing_rapidly" if growth_rate > 50 else "growing"
                ),
                "optimization_suggestions": [
                    (
                        "Increase cache hit rate to reduce API calls"
                        if historical_stats_7d.get("cache_hit_rate", 0) < 0.6
                        else None
                    ),
                    (
                        "Enable duplicate detection to reduce redundant calls"
                        if historical_stats_7d.get("duplicate_detection_rate", 0) < 0.1
                        else None
                    ),
                    (
                        "Consider bulk endpoints for multiple recipe requests"
                        if cost_per_recipe > 0.2
                        else None
                    ),
                ],
                "estimated_monthly_budget": round(monthly_projection * 1.2, 2),  # 20% buffer
            },
            "implementation_status": "🟡 PARTIAL - Endpoint working, database integration pending",
        }

    except Exception as e:
        logger.error(f"Error getting cost projection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating cost projection: {str(e)}")


@router.get("/deduplication/stats")
async def get_deduplication_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    tracker: SpoonacularAPITracker = Depends(get_analytics_tracker),
) -> Dict[str, Any]:
    """
    Get recipe deduplication effectiveness statistics.

    🟡 IMPLEMENTATION STATUS: PARTIAL - Endpoint working, database integration pending
    This endpoint provides insights into:
    - Deduplication effectiveness and savings
    - Most commonly duplicated recipes
    - Algorithm accuracy metrics
    - Cost savings from deduplication

    Args:
        days: Number of days to analyze

    Returns:
        Deduplication effectiveness statistics
    """
    try:
        # Get calls with deduplication information
        call_history = tracker.get_call_history(hours=24 * days, limit=1000)

        # Filter calls that had deduplication applied
        dedup_calls = [call for call in call_history if call.get("duplicate_detected", False)]

        # Calculate statistics
        total_calls = len(call_history)
        dedup_call_count = len(dedup_calls)
        dedup_rate = dedup_call_count / total_calls if total_calls > 0 else 0

        # Calculate recipe savings
        total_duplicates_removed = sum(
            len(call.get("duplicate_recipe_ids", [])) for call in dedup_calls
        )
        total_recipes_processed = sum(call.get("recipe_count", 0) for call in call_history)

        # Estimate cost savings (assuming each duplicate would have cost 1 point to fetch individually)
        estimated_cost_savings = total_duplicates_removed * 1  # 1 point per recipe

        # Analyze duplicate patterns
        duplicate_recipe_ids = []
        for call in dedup_calls:
            duplicate_recipe_ids.extend(call.get("duplicate_recipe_ids", []))

        # Count frequency of duplicated recipes
        from collections import Counter

        duplicate_frequency = Counter(duplicate_recipe_ids)
        most_common_duplicates = duplicate_frequency.most_common(10)

        return {
            "analysis_period_days": days,
            "summary": {
                "total_api_calls": total_calls,
                "calls_with_deduplication": dedup_call_count,
                "deduplication_rate": round(dedup_rate, 4),
                "total_recipes_processed": total_recipes_processed,
                "total_duplicates_removed": total_duplicates_removed,
                "duplicate_rate": (
                    round(total_duplicates_removed / total_recipes_processed, 4)
                    if total_recipes_processed > 0
                    else 0
                ),
            },
            "savings": {
                "estimated_cost_savings_points": estimated_cost_savings,
                "percentage_reduction": (
                    round(
                        (
                            total_duplicates_removed
                            / (total_recipes_processed + total_duplicates_removed)
                        )
                        * 100,
                        2,
                    )
                    if total_recipes_processed > 0
                    else 0
                ),
                "api_calls_saved": total_duplicates_removed,  # Assuming 1 call per duplicate that would have been made
            },
            "patterns": {
                "most_common_duplicates": [
                    {"recipe_id": recipe_id, "frequency": count}
                    for recipe_id, count in most_common_duplicates
                ],
                "average_duplicates_per_call": (
                    round(total_duplicates_removed / dedup_call_count, 2)
                    if dedup_call_count > 0
                    else 0
                ),
            },
            "effectiveness": {
                "algorithm_engagement": (
                    "high" if dedup_rate > 0.2 else "medium" if dedup_rate > 0.1 else "low"
                ),
                "savings_impact": (
                    "significant"
                    if estimated_cost_savings > 100
                    else "moderate" if estimated_cost_savings > 20 else "minimal"
                ),
                "recommendation": (
                    "Continue using deduplication"
                    if dedup_rate > 0.05
                    else "Review deduplication threshold settings"
                ),
            },
            "implementation_status": "🟡 PARTIAL - Endpoint working, database integration pending",
        }

    except Exception as e:
        logger.error(f"Error getting deduplication stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving deduplication stats: {str(e)}"
        )


@router.get("/performance/endpoints")
async def get_endpoint_performance(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    tracker: SpoonacularAPITracker = Depends(get_analytics_tracker),
) -> Dict[str, Any]:
    """
    Get performance metrics for different Spoonacular API endpoints.

    🟡 IMPLEMENTATION STATUS: PARTIAL - Endpoint working, database integration pending
    This endpoint provides:
    - Response time analysis by endpoint
    - Success rates and error patterns
    - Usage frequency and efficiency metrics
    - Performance recommendations

    Args:
        days: Number of days to analyze

    Returns:
        Endpoint performance analytics
    """
    try:
        # Get call history for performance analysis
        call_history = tracker.get_call_history(hours=24 * days, limit=2000)

        # Group calls by endpoint
        endpoint_stats = {}

        for call in call_history:
            endpoint = call.get("endpoint", "unknown")

            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "call_count": 0,
                    "total_response_time": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "total_recipes": 0,
                    "total_cost": 0,
                    "cache_hits": 0,
                    "response_times": [],
                }

            stats = endpoint_stats[endpoint]
            stats["call_count"] += 1

            response_time = call.get("response_time_ms", 0)
            if response_time > 0:
                stats["total_response_time"] += response_time
                stats["response_times"].append(response_time)

            status = call.get("response_status", 200)
            if status < 400:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

            stats["total_recipes"] += call.get("recipe_count", 0)
            stats["total_cost"] += call.get("cost_points", 0)

            if call.get("cache_hit", False):
                stats["cache_hits"] += 1

        # Calculate performance metrics for each endpoint
        performance_summary = {}

        for endpoint, stats in endpoint_stats.items():
            call_count = stats["call_count"]
            response_times = stats["response_times"]

            avg_response_time = stats["total_response_time"] / call_count if call_count > 0 else 0
            success_rate = stats["success_count"] / call_count if call_count > 0 else 0
            cache_hit_rate = stats["cache_hits"] / call_count if call_count > 0 else 0
            cost_per_recipe = (
                stats["total_cost"] / stats["total_recipes"] if stats["total_recipes"] > 0 else 0
            )

            # Calculate percentiles for response time
            if response_times:
                response_times.sort()
                p50 = response_times[len(response_times) // 2]
                p95 = response_times[int(len(response_times) * 0.95)]
                p99 = response_times[int(len(response_times) * 0.99)]
            else:
                p50 = p95 = p99 = 0

            performance_summary[endpoint] = {
                "usage": {
                    "call_count": call_count,
                    "total_recipes": stats["total_recipes"],
                    "total_cost_points": stats["total_cost"],
                },
                "performance": {
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "p50_response_time_ms": p50,
                    "p95_response_time_ms": p95,
                    "p99_response_time_ms": p99,
                    "success_rate": round(success_rate, 4),
                    "error_rate": round(1 - success_rate, 4),
                    "cache_hit_rate": round(cache_hit_rate, 4),
                },
                "efficiency": {
                    "recipes_per_call": (
                        round(stats["total_recipes"] / call_count, 2) if call_count > 0 else 0
                    ),
                    "cost_per_recipe": round(cost_per_recipe, 4),
                    "cost_efficiency_rating": (
                        "excellent"
                        if cost_per_recipe < 0.1
                        else "good" if cost_per_recipe < 0.5 else "fair"
                    ),
                },
            }

        # Overall performance summary
        total_calls = sum(stats["call_count"] for stats in endpoint_stats.values())
        total_success = sum(stats["success_count"] for stats in endpoint_stats.values())
        overall_success_rate = total_success / total_calls if total_calls > 0 else 0

        return {
            "analysis_period_days": days,
            "overall_summary": {
                "total_calls": total_calls,
                "overall_success_rate": round(overall_success_rate, 4),
                "endpoints_analyzed": len(endpoint_stats),
                "most_used_endpoint": (
                    max(endpoint_stats.keys(), key=lambda k: endpoint_stats[k]["call_count"])
                    if endpoint_stats
                    else None
                ),
            },
            "endpoint_performance": performance_summary,
            "recommendations": {
                "performance_issues": [
                    f"Endpoint '{endpoint}' has high error rate ({(1-perf['performance']['success_rate'])*100:.1f}%)"
                    for endpoint, perf in performance_summary.items()
                    if perf["performance"]["success_rate"] < 0.95
                ],
                "optimization_opportunities": [
                    f"Endpoint '{endpoint}' has low cache hit rate ({perf['performance']['cache_hit_rate']*100:.1f}%)"
                    for endpoint, perf in performance_summary.items()
                    if perf["performance"]["cache_hit_rate"] < 0.3
                ],
            },
            "implementation_status": "🟡 PARTIAL - Endpoint working, database integration pending",
        }

    except Exception as e:
        logger.error(f"Error getting endpoint performance: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving endpoint performance: {str(e)}"
        )


@router.get("/health")
async def analytics_health_check() -> Dict[str, Any]:
    """
    Health check for the analytics service.

    🟢 IMPLEMENTATION STATUS: WORKING - Health endpoint operational
    This endpoint provides service health information.
    """
    try:
        # Test database connection if available
        db_available = False
        db_table_exists = False
        try:
            if get_database_service:
                db_service = get_database_service()
                # Simple query to test database connectivity
                test_result = db_service.execute_query("SELECT 1 as test")
                db_available = len(test_result) > 0 if test_result else False

                # Check if tracking table exists
                if db_available:
                    table_check = db_service.execute_query(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'spoonacular_api_calls'
                        )
                    """
                    )
                    db_table_exists = table_check[0]["exists"] if table_check else False

        except Exception:
            db_available = False
            db_table_exists = False

        # Test service availability
        tracker_available = False
        try:
            tracker = SpoonacularAPITracker(db_service=None)
            tracker_available = True
        except Exception:
            tracker_available = False

        # Determine feature status based on database table availability
        feature_status = (
            "🟢 WORKING - Database deployed"
            if db_table_exists
            else "🟡 PARTIAL - Endpoint working, database table pending"
        )

        return {
            "service": "Spoonacular Analytics",
            "status": "healthy" if tracker_available else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "connected" if db_available else "unavailable",
                "database_table": "exists" if db_table_exists else "missing",
                "api_tracker": "available" if tracker_available else "unavailable",
                "deduplication_service": (
                    "available" if RecipeDeduplicationService else "unavailable"
                ),
            },
            "features": {
                "daily_usage_analytics": feature_status,
                "user_analytics": feature_status,
                "cost_projections": feature_status,
                "deduplication_stats": feature_status,
                "performance_metrics": feature_status,
            },
            "implementation_status": (
                "🟡 PARTIAL - Endpoints working, database table deployment pending"
                if not db_table_exists
                else "🟢 WORKING - All components operational"
            ),
        }

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "service": "Spoonacular Analytics",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "implementation_status": "🔴 CONCEPT - Service unavailable",
        }
