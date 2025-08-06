"""
Enhanced Spoonacular Service with API tracking and deduplication integration.

🟡 IMPLEMENTATION STATUS: PARTIAL
This service wraps the existing SpoonacularService with tracking capabilities
while maintaining backward compatibility.

Features:
- ✅ Transparent API call tracking
- ✅ Automatic recipe deduplication
- ✅ Cost monitoring integration
- ✅ Cache integration
- 🟡 Database logging (requires table)
- 🔴 Full analytics integration
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from backend_gateway.services.recipe_deduplication_service import RecipeDeduplicationService
from backend_gateway.services.spoonacular_api_tracker import SpoonacularAPITracker
from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)


class EnhancedSpoonacularService(SpoonacularService):
    """
    Enhanced Spoonacular service with API tracking and deduplication.

    🟡 IMPLEMENTATION STATUS: PARTIAL
    Extends the existing SpoonacularService with:
    - ✅ Automatic API call tracking
    - ✅ Recipe deduplication on responses
    - ✅ Cost monitoring and analytics
    - ✅ Performance metrics collection
    - 🟡 Database integration (requires setup)

    This service maintains full backward compatibility with existing code.
    """

    def __init__(
        self, db_service=None, enable_tracking: bool = True, enable_deduplication: bool = True
    ):
        """
        Initialize enhanced service.

        Args:
            db_service: Database service for tracking storage
            enable_tracking: Whether to enable API call tracking
            enable_deduplication: Whether to enable recipe deduplication
        """
        # Initialize parent Spoonacular service
        super().__init__()

        # Initialize tracking and deduplication services
        self.enable_tracking = enable_tracking
        self.enable_deduplication = enable_deduplication

        if self.enable_tracking:
            try:
                self.api_tracker = SpoonacularAPITracker(db_service=db_service)
                logger.info("✅ API tracking enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize API tracker: {str(e)}")
                self.api_tracker = None
                self.enable_tracking = False

        if self.enable_deduplication:
            try:
                self.deduplicator = RecipeDeduplicationService()
                logger.info("✅ Recipe deduplication enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize deduplicator: {str(e)}")
                self.deduplicator = None
                self.enable_deduplication = False

    async def search_recipes_by_ingredients(
        self,
        ingredients: List[str],
        number: int = 10,
        ranking: int = 1,
        ignore_pantry: bool = False,
        intolerances: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        enable_deduplication: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with tracking and deduplication.

        Args:
            ingredients: List of ingredients to search with
            number: Number of recipes to return
            ranking: Ranking strategy
            ignore_pantry: Whether to ignore pantry items
            intolerances: List of allergens/intolerances to exclude
            user_id: User ID for tracking (optional)
            enable_deduplication: Override deduplication setting for this call

        Returns:
            List of recipe dictionaries (potentially deduplicated)
        """
        # Determine if deduplication should be applied for this call
        apply_dedup = (
            self.enable_deduplication if enable_deduplication is None else enable_deduplication
        )

        # Track the API call if tracking is enabled
        if self.enable_tracking and self.api_tracker:
            with self.api_tracker.track_api_call(
                endpoint="findByIngredients",
                user_id=user_id,
                request_params={
                    "ingredients": ",".join(ingredients),
                    "number": number,
                    "ranking": ranking,
                    "ignorePantry": ignore_pantry,
                    "intolerances": intolerances,
                },
            ) as context:

                # Call the parent method
                recipes = await super().search_recipes_by_ingredients(
                    ingredients=ingredients,
                    number=number,
                    ranking=ranking,
                    ignore_pantry=ignore_pantry,
                    intolerances=intolerances,
                )

                # Process recipes for deduplication and fingerprinting
                if apply_dedup and self.deduplicator:
                    original_count = len(recipes)

                    # Apply deduplication
                    deduplicated_recipes, duplicate_ids = self.deduplicator.deduplicate_recipes(
                        recipes
                    )

                    # Generate fingerprints for all original recipes
                    fingerprints = [
                        self.deduplicator.generate_recipe_fingerprint(recipe) for recipe in recipes
                    ]

                    # Update tracking context with deduplication info
                    context.set_deduplication_info(
                        duplicate_detected=len(duplicate_ids) > 0,
                        recipe_fingerprints=fingerprints,
                        duplicate_recipe_ids=duplicate_ids,
                    )

                    # Log deduplication results
                    if len(duplicate_ids) > 0:
                        reduction_percent = (len(duplicate_ids) / original_count) * 100
                        logger.info(
                            f"🔍 Deduplication: {original_count} → {len(deduplicated_recipes)} recipes "
                            f"({reduction_percent:.1f}% reduction, {len(duplicate_ids)} duplicates)"
                        )

                    recipes = deduplicated_recipes

                # Update tracking context with response info
                context.set_response_data(response_status=200, recipe_count=len(recipes))

                return recipes
        else:
            # No tracking - just call parent method and optionally deduplicate
            recipes = await super().search_recipes_by_ingredients(
                ingredients=ingredients,
                number=number,
                ranking=ranking,
                ignore_pantry=ignore_pantry,
                intolerances=intolerances,
            )

            # Apply deduplication if enabled
            if apply_dedup and self.deduplicator:
                deduplicated_recipes, duplicate_ids = self.deduplicator.deduplicate_recipes(recipes)
                if len(duplicate_ids) > 0:
                    logger.info(
                        f"🔍 Deduplication (no tracking): {len(recipes)} → {len(deduplicated_recipes)} recipes"
                    )
                recipes = deduplicated_recipes

            return recipes

    async def get_recipe_information(
        self, recipe_id: int, include_nutrition: bool = True, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced recipe information retrieval with tracking.

        Args:
            recipe_id: The ID of the recipe
            include_nutrition: Whether to include nutrition information
            user_id: User ID for tracking (optional)

        Returns:
            Recipe information dictionary
        """
        if self.enable_tracking and self.api_tracker:
            with self.api_tracker.track_api_call(
                endpoint="information",
                user_id=user_id,
                request_params={"recipe_id": recipe_id, "includeNutrition": include_nutrition},
            ) as context:

                # Call parent method
                recipe = await super().get_recipe_information(recipe_id, include_nutrition)

                # Update tracking context
                context.set_response_data(response_status=200, recipe_count=1 if recipe else 0)

                # Generate fingerprint if deduplication is enabled
                if self.enable_deduplication and self.deduplicator and recipe:
                    fingerprint = self.deduplicator.generate_recipe_fingerprint(recipe)
                    context.set_deduplication_info(
                        duplicate_detected=False, recipe_fingerprints=[fingerprint]
                    )

                return recipe
        else:
            # No tracking - just call parent method
            return await super().get_recipe_information(recipe_id, include_nutrition)

    async def search_recipes_complex(
        self,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        diet: Optional[str] = None,
        include_ingredients: Optional[List[str]] = None,
        exclude_ingredients: Optional[List[str]] = None,
        intolerances: Optional[List[str]] = None,
        max_ready_time: Optional[int] = None,
        sort: Optional[str] = None,
        number: int = 10,
        offset: int = 0,
        user_id: Optional[int] = None,
        enable_deduplication: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced complex search with tracking and deduplication.

        Args:
            query: Natural language search query
            cuisine: Cuisine type filter
            diet: Diet type filter
            include_ingredients: Ingredients that must be included
            exclude_ingredients: Ingredients to exclude
            intolerances: Allergens/intolerances to exclude
            max_ready_time: Maximum cooking time
            sort: Sort criteria
            number: Number of results
            offset: Results offset
            user_id: User ID for tracking
            enable_deduplication: Override deduplication setting

        Returns:
            Complex search results with metadata
        """
        # Determine if deduplication should be applied
        apply_dedup = (
            self.enable_deduplication if enable_deduplication is None else enable_deduplication
        )

        if self.enable_tracking and self.api_tracker:
            with self.api_tracker.track_api_call(
                endpoint="complexSearch",
                user_id=user_id,
                request_params={
                    "query": query,
                    "cuisine": cuisine,
                    "diet": diet,
                    "includeIngredients": (
                        ",".join(include_ingredients) if include_ingredients else None
                    ),
                    "excludeIngredients": (
                        ",".join(exclude_ingredients) if exclude_ingredients else None
                    ),
                    "intolerances": ",".join(intolerances) if intolerances else None,
                    "maxReadyTime": max_ready_time,
                    "sort": sort,
                    "number": number,
                    "offset": offset,
                },
            ) as context:

                # Call parent method
                result = await super().search_recipes_complex(
                    query=query,
                    cuisine=cuisine,
                    diet=diet,
                    include_ingredients=include_ingredients,
                    exclude_ingredients=exclude_ingredients,
                    intolerances=intolerances,
                    max_ready_time=max_ready_time,
                    sort=sort,
                    number=number,
                    offset=offset,
                )

                # Extract recipes from result
                recipes = result.get("results", [])
                original_count = len(recipes)

                # Apply deduplication if enabled
                duplicate_ids = []
                fingerprints = []

                if apply_dedup and self.deduplicator and recipes:
                    deduplicated_recipes, duplicate_ids = self.deduplicator.deduplicate_recipes(
                        recipes
                    )

                    # Generate fingerprints for all original recipes
                    fingerprints = [
                        self.deduplicator.generate_recipe_fingerprint(recipe) for recipe in recipes
                    ]

                    # Update result with deduplicated recipes
                    result["results"] = deduplicated_recipes
                    result["totalResults"] = len(deduplicated_recipes)

                    if len(duplicate_ids) > 0:
                        reduction_percent = (len(duplicate_ids) / original_count) * 100
                        logger.info(
                            f"🔍 Complex search deduplication: {original_count} → {len(deduplicated_recipes)} recipes "
                            f"({reduction_percent:.1f}% reduction)"
                        )

                # Update tracking context
                context.set_response_data(
                    response_status=200, recipe_count=len(result.get("results", []))
                )

                context.set_deduplication_info(
                    duplicate_detected=len(duplicate_ids) > 0,
                    recipe_fingerprints=fingerprints,
                    duplicate_recipe_ids=duplicate_ids,
                )

                return result
        else:
            # No tracking - call parent and optionally deduplicate
            result = await super().search_recipes_complex(
                query=query,
                cuisine=cuisine,
                diet=diet,
                include_ingredients=include_ingredients,
                exclude_ingredients=exclude_ingredients,
                intolerances=intolerances,
                max_ready_time=max_ready_time,
                sort=sort,
                number=number,
                offset=offset,
            )

            # Apply deduplication if enabled
            if apply_dedup and self.deduplicator:
                recipes = result.get("results", [])
                if recipes:
                    deduplicated_recipes, duplicate_ids = self.deduplicator.deduplicate_recipes(
                        recipes
                    )
                    result["results"] = deduplicated_recipes
                    result["totalResults"] = len(deduplicated_recipes)
                    if len(duplicate_ids) > 0:
                        logger.info(
                            f"🔍 Complex search deduplication (no tracking): {len(recipes)} → {len(deduplicated_recipes)} recipes"
                        )

            return result

    async def get_random_recipes(
        self, number: int = 10, tags: Optional[List[str]] = None, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhanced random recipe retrieval with tracking.

        Args:
            number: Number of random recipes
            tags: Optional tags to filter by
            user_id: User ID for tracking

        Returns:
            Random recipes response
        """
        if self.enable_tracking and self.api_tracker:
            with self.api_tracker.track_api_call(
                endpoint="random",
                user_id=user_id,
                request_params={"number": number, "tags": ",".join(tags) if tags else None},
            ) as context:

                # Call parent method
                result = await super().get_random_recipes(number, tags)

                # Extract recipes and generate fingerprints
                recipes = result.get("recipes", [])
                fingerprints = []

                if self.enable_deduplication and self.deduplicator and recipes:
                    fingerprints = [
                        self.deduplicator.generate_recipe_fingerprint(recipe) for recipe in recipes
                    ]

                # Update tracking context
                context.set_response_data(response_status=200, recipe_count=len(recipes))

                if fingerprints:
                    context.set_deduplication_info(
                        duplicate_detected=False,  # Random recipes are unlikely to be duplicates
                        recipe_fingerprints=fingerprints,
                    )

                return result
        else:
            # No tracking - just call parent method
            return await super().get_random_recipes(number, tags)

    def get_usage_analytics(self, user_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
        """
        Get usage analytics for this service instance.

        Args:
            user_id: Filter by user ID (optional)
            days: Number of days to analyze

        Returns:
            Usage analytics dictionary
        """
        if self.enable_tracking and self.api_tracker:
            return self.api_tracker.get_usage_stats(user_id=user_id, days=days)
        else:
            return {
                "error": "Tracking not enabled",
                "tracking_enabled": False,
                "deduplication_enabled": self.enable_deduplication,
            }

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of enhanced service features.

        Returns:
            Service status dictionary
        """
        return {
            "service": "EnhancedSpoonacularService",
            "features": {
                "api_tracking": {
                    "enabled": self.enable_tracking,
                    "status": (
                        "🟢 WORKING" if self.enable_tracking and self.api_tracker else "🔴 DISABLED"
                    ),
                },
                "recipe_deduplication": {
                    "enabled": self.enable_deduplication,
                    "status": (
                        "🟢 WORKING"
                        if self.enable_deduplication and self.deduplicator
                        else "🔴 DISABLED"
                    ),
                },
                "database_integration": {
                    "status": "🟡 PARTIAL - Database table required for persistent tracking"
                },
            },
            "backward_compatibility": "🟢 FULL - Drop-in replacement for SpoonacularService",
            "implementation_status": "🟡 PARTIAL - Core features working, database integration pending",
        }
