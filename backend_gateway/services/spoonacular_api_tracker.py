"""
Spoonacular API Call Tracker Service

🔴 IMPLEMENTATION STATUS: PARTIAL
This service tracks all Spoonacular API calls for usage analytics, cost monitoring,
and deduplication metrics.

Features:
- API call logging with full metadata
- Response time and error tracking
- Recipe fingerprint integration
- Cost point calculation
- Analytics data preparation
"""

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SpoonacularAPITracker:
    """
    Tracks Spoonacular API calls for usage analytics and cost monitoring.

    🔴 IMPLEMENTATION STATUS: PARTIAL
    - ✅ API call logging with comprehensive metadata
    - ✅ Error tracking and retry attempt logging
    - ✅ Recipe fingerprint integration
    - ✅ Cost calculation by endpoint
    - 🟡 Database integration (requires table creation)
    - 🔴 Analytics aggregation not yet implemented
    """

    # Cost points for different Spoonacular endpoints
    ENDPOINT_COSTS = {
        "findByIngredients": 1,
        "complexSearch": 1,
        "informationBulk": 1,  # Per recipe in bulk
        "information": 1,  # Single recipe
        "random": 1,
        "analyzedInstructions": 1,
        "similar": 1,
        "parseIngredients": 0.01,  # Very cheap endpoint
        "substitutes": 0.01,
    }

    def __init__(self, db_service=None):
        """
        Initialize the API tracker.

        Args:
            db_service: Database service instance for logging calls
        """
        self.db_service = db_service
        self._in_memory_calls = []  # Fallback storage if DB unavailable

        # Initialize deduplication service for fingerprinting
        try:
            from backend_gateway.services.recipe_deduplication_service import (
                RecipeDeduplicationService,
            )

            self.deduplicator = RecipeDeduplicationService()
        except ImportError:
            logger.warning("Recipe deduplication service not available")
            self.deduplicator = None

    def get_endpoint_cost(self, endpoint: str, recipe_count: int = 1) -> float:
        """
        Calculate the cost points for an API endpoint call.

        Args:
            endpoint: Spoonacular endpoint name
            recipe_count: Number of recipes returned (for bulk endpoints)

        Returns:
            Cost in points
        """
        base_cost = self.ENDPOINT_COSTS.get(endpoint, 1)

        # For bulk endpoints, cost scales with recipe count
        if endpoint in ["informationBulk"] and recipe_count > 1:
            return base_cost * recipe_count

        return base_cost

    @contextmanager
    def track_api_call(
        self,
        endpoint: str,
        user_id: Optional[int] = None,
        request_params: Optional[dict[str, Any]] = None,
        method: str = "GET",
    ):
        """
        Context manager to track an API call with automatic timing and error handling.

        Args:
            endpoint: Spoonacular endpoint name
            user_id: User making the request
            request_params: Parameters sent to the API
            method: HTTP method

        Yields:
            Tracker context for additional data
        """
        call_data = {
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "request_params": request_params or {},
            "call_timestamp": datetime.now(),
            "start_time": time.time(),
        }

        tracker_context = APICallContext(call_data)

        try:
            yield tracker_context

            # Calculate response time
            call_data["response_time_ms"] = int((time.time() - call_data["start_time"]) * 1000)

            # Set default success values if not already set
            if "response_status" not in call_data:
                call_data["response_status"] = 200

            # Log the successful call
            self.log_api_call(**call_data)

        except Exception as e:
            # Calculate response time even for errors
            call_data["response_time_ms"] = int((time.time() - call_data["start_time"]) * 1000)

            # Set error information
            call_data["error_code"] = type(e).__name__
            call_data["error_message"] = str(e)
            call_data["response_status"] = getattr(e, "status_code", 500)

            # Log the failed call
            self.log_api_call(**call_data)

            # Re-raise the exception
            raise

    def log_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        user_id: Optional[int] = None,
        request_params: Optional[dict[str, Any]] = None,
        response_status: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        recipe_count: int = 0,
        cache_hit: bool = False,
        duplicate_detected: bool = False,
        cost_points: Optional[float] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_attempt: int = 0,
        recipe_fingerprints: Optional[list[str]] = None,
        duplicate_recipe_ids: Optional[list[int]] = None,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
        call_timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> Optional[int]:
        """
        Log an API call to the database.

        Args:
            endpoint: Spoonacular endpoint called
            method: HTTP method used
            user_id: User ID making the request
            request_params: Request parameters
            response_status: HTTP response status code
            response_time_ms: Response time in milliseconds
            recipe_count: Number of recipes returned
            cache_hit: Whether this was served from cache
            duplicate_detected: Whether deduplication was applied
            cost_points: API cost in points (calculated if not provided)
            error_code: Error code if call failed
            error_message: Error message if call failed
            retry_attempt: Retry attempt number (0 for first try)
            recipe_fingerprints: List of recipe fingerprints
            duplicate_recipe_ids: List of duplicate recipe IDs
            request_size_bytes: Request size in bytes
            response_size_bytes: Response size in bytes
            call_timestamp: When the call was made

        Returns:
            Database record ID if successful, None otherwise
        """
        try:
            # Calculate cost if not provided
            if cost_points is None:
                cost_points = self.get_endpoint_cost(endpoint, recipe_count)

            # Set timestamp if not provided
            if call_timestamp is None:
                call_timestamp = datetime.now()

            # Prepare call data
            call_data = {
                "endpoint": endpoint,
                "method": method,
                "call_timestamp": call_timestamp,
                "user_id": user_id,
                "request_params": json.dumps(request_params) if request_params else None,
                "request_size_bytes": request_size_bytes,
                "response_status": response_status,
                "response_size_bytes": response_size_bytes,
                "response_time_ms": response_time_ms,
                "recipe_count": recipe_count,
                "cache_hit": cache_hit,
                "duplicate_detected": duplicate_detected,
                "cost_points": cost_points,
                "error_code": error_code,
                "error_message": error_message,
                "retry_attempt": retry_attempt,
                "recipe_fingerprints": recipe_fingerprints or [],
                "duplicate_recipe_ids": duplicate_recipe_ids or [],
                "api_version": "v1",
                "client_version": "prepsense-1.0",
                "environment": "production",
            }

            # Try to insert into database
            if self.db_service:
                try:
                    # Insert SQL - will be implemented when table is created
                    insert_sql = """
                    INSERT INTO spoonacular_api_calls (
                        endpoint, method, call_timestamp, user_id, request_params,
                        request_size_bytes, response_status, response_size_bytes,
                        response_time_ms, recipe_count, cache_hit, duplicate_detected,
                        cost_points, error_code, error_message, retry_attempt,
                        recipe_fingerprints, duplicate_recipe_ids, api_version,
                        client_version, environment
                    ) VALUES (
                        %(endpoint)s, %(method)s, %(call_timestamp)s, %(user_id)s, %(request_params)s,
                        %(request_size_bytes)s, %(response_status)s, %(response_size_bytes)s,
                        %(response_time_ms)s, %(recipe_count)s, %(cache_hit)s, %(duplicate_detected)s,
                        %(cost_points)s, %(error_code)s, %(error_message)s, %(retry_attempt)s,
                        %(recipe_fingerprints)s, %(duplicate_recipe_ids)s, %(api_version)s,
                        %(client_version)s, %(environment)s
                    ) RETURNING id;
                    """

                    result = self.db_service.execute_query(insert_sql, call_data)
                    if result:
                        call_id = result[0]["id"]
                        logger.debug(
                            f"Logged API call {call_id}: {endpoint} ({response_status}) - "
                            f"{recipe_count} recipes, {response_time_ms}ms"
                        )
                        return call_id

                except Exception as db_error:
                    logger.warning(f"Failed to log API call to database: {str(db_error)}")
                    # Fall back to in-memory storage
                    self._in_memory_calls.append(call_data)
                    return len(self._in_memory_calls)  # Use list index as ID
            else:
                # No database service - store in memory
                self._in_memory_calls.append(call_data)
                return len(self._in_memory_calls)

        except Exception as e:
            logger.error(f"Error logging API call: {str(e)}")
            return None

    def process_recipe_response(
        self, recipes: list[dict[str, Any]], apply_deduplication: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Process recipe response data for fingerprinting and deduplication.

        Args:
            recipes: List of recipe dictionaries from Spoonacular
            apply_deduplication: Whether to apply deduplication

        Returns:
            Tuple of (processed_recipes, metadata)
        """
        metadata = {
            "original_count": len(recipes),
            "recipe_fingerprints": [],
            "duplicate_detected": False,
            "duplicate_recipe_ids": [],
            "final_count": len(recipes),
        }

        if not recipes or not self.deduplicator:
            return recipes, metadata

        try:
            # Generate fingerprints for all recipes
            for recipe in recipes:
                fingerprint = self.deduplicator.generate_recipe_fingerprint(recipe)
                metadata["recipe_fingerprints"].append(fingerprint)

            # Apply deduplication if requested
            if apply_deduplication:
                deduplicated_recipes, duplicate_ids = self.deduplicator.deduplicate_recipes(recipes)

                metadata["duplicate_detected"] = len(duplicate_ids) > 0
                metadata["duplicate_recipe_ids"] = duplicate_ids
                metadata["final_count"] = len(deduplicated_recipes)

                return deduplicated_recipes, metadata

            return recipes, metadata

        except Exception as e:
            logger.warning(f"Error processing recipe response: {str(e)}")
            return recipes, metadata

    def get_call_history(
        self,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Retrieve recent API call history.

        Args:
            user_id: Filter by user ID
            endpoint: Filter by endpoint
            hours: Hours of history to retrieve
            limit: Maximum number of calls to return

        Returns:
            List of API call records
        """
        if not self.db_service:
            # Return in-memory calls if no database
            return self._in_memory_calls[-limit:] if self._in_memory_calls else []

        try:
            # Build query conditions
            conditions = ["call_timestamp >= %s"]
            params = [datetime.now() - timedelta(hours=hours)]

            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            if endpoint:
                conditions.append("endpoint = %s")
                params.append(endpoint)

            query = f"""
                SELECT * FROM spoonacular_api_calls
                WHERE {' AND '.join(conditions)}
                ORDER BY call_timestamp DESC
                LIMIT %s
            """
            params.append(limit)

            return self.db_service.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error retrieving call history: {str(e)}")
            return []

    def get_usage_stats(self, user_id: Optional[int] = None, days: int = 7) -> dict[str, Any]:
        """
        Get usage statistics for the specified period.

        Args:
            user_id: Filter by user ID (None for all users)
            days: Number of days to analyze

        Returns:
            Usage statistics dictionary
        """
        if not self.db_service:
            return self._calculate_in_memory_stats(user_id, days)

        try:
            # Base query conditions
            conditions = ["call_timestamp >= %s"]
            params = [datetime.now() - timedelta(days=days)]

            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            where_clause = " AND ".join(conditions)

            # Execute aggregation query
            query = f"""
                SELECT
                    COUNT(*) as total_calls,
                    COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits,
                    COUNT(*) FILTER (WHERE duplicate_detected = true) as duplicate_detections,
                    COUNT(*) FILTER (WHERE response_status >= 400) as error_calls,
                    SUM(cost_points) as total_cost_points,
                    SUM(recipe_count) as total_recipes,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(DISTINCT endpoint) as unique_endpoints
                FROM spoonacular_api_calls
                WHERE {where_clause}
            """

            result = self.db_service.execute_query(query, params)
            if result:
                stats = result[0]

                # Calculate derived metrics
                total_calls = stats.get("total_calls", 0)
                cache_hits = stats.get("cache_hits", 0)
                duplicate_detections = stats.get("duplicate_detections", 0)
                error_calls = stats.get("error_calls", 0)

                return {
                    "period_days": days,
                    "total_calls": total_calls,
                    "cache_hit_rate": (cache_hits / total_calls) if total_calls > 0 else 0,
                    "duplicate_detection_rate": (
                        (duplicate_detections / total_calls) if total_calls > 0 else 0
                    ),
                    "error_rate": (error_calls / total_calls) if total_calls > 0 else 0,
                    "total_cost_points": float(stats.get("total_cost_points", 0)),
                    "total_recipes": stats.get("total_recipes", 0),
                    "avg_response_time_ms": float(stats.get("avg_response_time", 0) or 0),
                    "unique_endpoints": stats.get("unique_endpoints", 0),
                }

        except Exception as e:
            logger.error(f"Error calculating usage stats: {str(e)}")

        return {
            "period_days": days,
            "total_calls": 0,
            "cache_hit_rate": 0,
            "duplicate_detection_rate": 0,
            "error_rate": 0,
            "total_cost_points": 0,
            "total_recipes": 0,
            "avg_response_time_ms": 0,
            "unique_endpoints": 0,
        }

    def _calculate_in_memory_stats(self, user_id: Optional[int], days: int) -> dict[str, Any]:
        """Calculate statistics from in-memory call data."""
        cutoff = datetime.now() - timedelta(days=days)
        relevant_calls = [
            call
            for call in self._in_memory_calls
            if call.get("call_timestamp", datetime.min) >= cutoff
            and (user_id is None or call.get("user_id") == user_id)
        ]

        if not relevant_calls:
            return {
                "period_days": days,
                "total_calls": 0,
                "cache_hit_rate": 0,
                "duplicate_detection_rate": 0,
                "error_rate": 0,
                "total_cost_points": 0,
                "total_recipes": 0,
                "avg_response_time_ms": 0,
                "unique_endpoints": 0,
            }

        total_calls = len(relevant_calls)
        cache_hits = sum(1 for call in relevant_calls if call.get("cache_hit", False))
        duplicates = sum(1 for call in relevant_calls if call.get("duplicate_detected", False))
        errors = sum(1 for call in relevant_calls if call.get("response_status", 200) >= 400)

        return {
            "period_days": days,
            "total_calls": total_calls,
            "cache_hit_rate": cache_hits / total_calls,
            "duplicate_detection_rate": duplicates / total_calls,
            "error_rate": errors / total_calls,
            "total_cost_points": sum(call.get("cost_points", 0) for call in relevant_calls),
            "total_recipes": sum(call.get("recipe_count", 0) for call in relevant_calls),
            "avg_response_time_ms": sum(call.get("response_time_ms", 0) for call in relevant_calls)
            / total_calls,
            "unique_endpoints": len({call.get("endpoint") for call in relevant_calls}),
        }


class APICallContext:
    """Context object for tracking API call data."""

    def __init__(self, call_data: dict[str, Any]):
        self.call_data = call_data

    def set_response_data(
        self, response_status: int, response_size_bytes: int = 0, recipe_count: int = 0
    ):
        """Set response data for the API call."""
        self.call_data.update(
            {
                "response_status": response_status,
                "response_size_bytes": response_size_bytes,
                "recipe_count": recipe_count,
            }
        )

    def set_cache_info(self, cache_hit: bool):
        """Set cache hit information."""
        self.call_data["cache_hit"] = cache_hit

    def set_deduplication_info(
        self,
        duplicate_detected: bool,
        recipe_fingerprints: list[str] = None,
        duplicate_recipe_ids: list[int] = None,
    ):
        """Set deduplication information."""
        self.call_data.update(
            {
                "duplicate_detected": duplicate_detected,
                "recipe_fingerprints": recipe_fingerprints or [],
                "duplicate_recipe_ids": duplicate_recipe_ids or [],
            }
        )

    def set_retry_info(self, retry_attempt: int):
        """Set retry attempt information."""
        self.call_data["retry_attempt"] = retry_attempt
