"""
Recipe fallback service providing intelligent fallback logic:
Local Backup Recipes → Spoonacular API → OpenAI Generation

🟡 PARTIAL - Fallback service implementation (requires service integration)
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import asyncpg

from backend_gateway.core.database import get_db_pool
from backend_gateway.routers.backup_recipes_router import (
    get_backup_recipe_details,
    search_backup_recipes,
)
from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)


class RecipeSource(Enum):
    """Recipe source indicators."""

    BACKUP_LOCAL = "backup_local"
    SPOONACULAR = "spoonacular"
    OPENAI = "openai_generated"
    CREW_AI = "crew_ai"
    UNKNOWN = "unknown"


@dataclass
class RecipeSearchConfig:
    """Configuration for recipe search fallback behavior."""

    enable_backup_recipes: bool = True
    enable_spoonacular: bool = True
    enable_openai: bool = True
    backup_min_match_ratio: float = 0.3
    max_results_per_source: int = 10
    total_max_results: int = 20
    timeout_seconds: int = 30
    prefer_images: bool = True
    require_instructions: bool = True


@dataclass
class RecipeResult:
    """Unified recipe result with source tracking."""

    id: Union[int, str]
    title: str
    source: RecipeSource
    image_url: Optional[str] = None
    ready_in_minutes: Optional[int] = None
    servings: Optional[int] = None
    used_ingredients: List[str] = None
    missed_ingredients: List[str] = None
    match_ratio: Optional[float] = None
    cuisine_type: Optional[str] = None
    difficulty: Optional[str] = None
    spoonacular_id: Optional[int] = None  # For compatibility
    backup_recipe_id: Optional[int] = None  # For local recipes
    raw_data: Dict[str, Any] = None


class RecipeFallbackService:
    """
    Intelligent recipe fallback service that tries multiple sources.
    """

    def __init__(self):
        self.spoonacular_service = None  # Will be initialized when needed
        self._performance_stats = {
            "backup_queries": 0,
            "spoonacular_queries": 0,
            "openai_queries": 0,
            "backup_success_rate": 0.0,
            "spoonacular_success_rate": 0.0,
            "avg_response_time": 0.0,
        }

    async def search_recipes(
        self,
        user_id: Optional[int] = None,
        ingredients: Optional[List[str]] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        diet_type: Optional[str] = None,
        max_ready_time: Optional[int] = None,
        config: Optional[RecipeSearchConfig] = None,
    ) -> List[RecipeResult]:
        """
        Search for recipes using fallback logic.

        Priority order:
        1. Local backup recipes (fastest, always available)
        2. Spoonacular API (good quality, requires API)
        3. OpenAI generation (fallback for edge cases)
        """
        if config is None:
            config = RecipeSearchConfig()

        start_time = time.time()
        all_results = []

        try:
            # Step 1: Try backup recipes first (always fast and available)
            if config.enable_backup_recipes:
                logger.info("🔍 Searching backup recipes database...")
                backup_results = await self._search_backup_recipes(
                    ingredients=ingredients,
                    query=query,
                    cuisine=cuisine,
                    max_ready_time=max_ready_time,
                    max_results=config.max_results_per_source,
                    min_match_ratio=config.backup_min_match_ratio,
                )

                all_results.extend(backup_results)
                logger.info(f"✅ Found {len(backup_results)} backup recipes")

                # If we have enough good results from backup, we can return early
                high_quality_backup = [
                    r for r in backup_results if r.match_ratio and r.match_ratio > 0.7
                ]
                if len(high_quality_backup) >= config.total_max_results // 2:
                    logger.info("🎯 High-quality backup recipes found, skipping external APIs")
                    return all_results[: config.total_max_results]

            # Step 2: Try Spoonacular if we need more results
            if config.enable_spoonacular and len(all_results) < config.total_max_results:

                logger.info("🌐 Searching Spoonacular API...")
                try:
                    spoonacular_results = await self._search_spoonacular(
                        user_id=user_id,
                        ingredients=ingredients,
                        query=query,
                        cuisine=cuisine,
                        diet_type=diet_type,
                        max_ready_time=max_ready_time,
                        max_results=config.max_results_per_source,
                    )

                    all_results.extend(spoonacular_results)
                    logger.info(f"✅ Found {len(spoonacular_results)} Spoonacular recipes")

                except Exception as e:
                    logger.warning(f"⚠️ Spoonacular search failed: {e}")

            # Step 3: Try OpenAI/CrewAI generation as last resort
            if config.enable_openai and len(all_results) < config.total_max_results // 2:

                logger.info("🤖 Trying AI recipe generation...")
                try:
                    ai_results = await self._generate_ai_recipes(
                        user_id=user_id,
                        ingredients=ingredients,
                        query=query,
                        cuisine=cuisine,
                        max_results=min(3, config.max_results_per_source),
                    )

                    all_results.extend(ai_results)
                    logger.info(f"✅ Generated {len(ai_results)} AI recipes")

                except Exception as e:
                    logger.warning(f"⚠️ AI generation failed: {e}")

            # Sort results by quality and source preference
            sorted_results = self._sort_and_prioritize_results(all_results, config)

            # Track performance
            elapsed_time = time.time() - start_time
            self._update_performance_stats(elapsed_time, all_results)

            logger.info(
                f"🎉 Recipe search completed in {elapsed_time:.2f}s, returning {len(sorted_results)} results"
            )

            return sorted_results[: config.total_max_results]

        except Exception as e:
            logger.error(f"❌ Recipe search failed: {e}")
            # Return any partial results we got
            return all_results[: config.total_max_results] if all_results else []

    async def get_recipe_details(
        self, recipe_id: Union[int, str], source: RecipeSource, include_nutrition: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get detailed recipe information from the appropriate source."""
        try:
            if source == RecipeSource.BACKUP_LOCAL:
                return await self._get_backup_recipe_details(int(recipe_id), include_nutrition)
            elif source == RecipeSource.SPOONACULAR:
                return await self._get_spoonacular_recipe_details(int(recipe_id), include_nutrition)
            else:
                logger.warning(f"Unsupported recipe source for details: {source}")
                return None

        except Exception as e:
            logger.error(f"Error getting recipe details for {recipe_id} from {source}: {e}")
            return None

    async def _search_backup_recipes(
        self,
        ingredients: Optional[List[str]] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        max_ready_time: Optional[int] = None,
        max_results: int = 10,
        min_match_ratio: float = 0.3,
    ) -> List[RecipeResult]:
        """Search local backup recipes database."""
        try:
            pool = await get_db_pool()

            # Format ingredients for search
            ingredients_str = ",".join(ingredients) if ingredients else None

            # Use the backup recipes router logic (simulated API call)
            search_response = await search_backup_recipes(
                query=query,
                ingredients=ingredients_str,
                cuisine=cuisine,
                maxReadyTime=max_ready_time,
                fillIngredients=bool(ingredients),
                number=max_results,
                pool=pool,
            )

            results = []
            for recipe_data in search_response.get("results", []):
                # Filter by match ratio if ingredients were provided
                if ingredients and recipe_data.get("match_ratio", 0) < min_match_ratio:
                    continue

                result = RecipeResult(
                    id=recipe_data["id"],
                    title=recipe_data["title"],
                    source=RecipeSource.BACKUP_LOCAL,
                    backup_recipe_id=recipe_data["id"],
                    image_url=recipe_data.get("image"),
                    ready_in_minutes=recipe_data.get("readyInMinutes"),
                    servings=recipe_data.get("servings"),
                    used_ingredients=recipe_data.get("usedIngredients", []),
                    missed_ingredients=recipe_data.get("missedIngredients", []),
                    match_ratio=recipe_data.get("match_ratio"),
                    raw_data=recipe_data,
                )
                results.append(result)

            self._performance_stats["backup_queries"] += 1
            return results

        except Exception as e:
            logger.error(f"Backup recipe search failed: {e}")
            return []

    async def _search_spoonacular(
        self,
        user_id: Optional[int] = None,
        ingredients: Optional[List[str]] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        diet_type: Optional[str] = None,
        max_ready_time: Optional[int] = None,
        max_results: int = 10,
    ) -> List[RecipeResult]:
        """Search Spoonacular API."""
        try:
            # Initialize Spoonacular service if needed
            if self.spoonacular_service is None:
                from backend_gateway.services.spoonacular_service import SpoonacularService

                self.spoonacular_service = SpoonacularService()

            # Call Spoonacular service
            spoonacular_recipes = await self.spoonacular_service.search_recipes_by_ingredients(
                ingredients=ingredients or [], number=max_results, ranking=1, ignore_pantry=True
            )

            results = []
            for recipe_data in spoonacular_recipes:
                result = RecipeResult(
                    id=recipe_data.get("id"),
                    title=recipe_data.get("title"),
                    source=RecipeSource.SPOONACULAR,
                    spoonacular_id=recipe_data.get("id"),
                    image_url=recipe_data.get("image"),
                    ready_in_minutes=recipe_data.get("readyInMinutes"),
                    used_ingredients=[
                        ing.get("name", "") for ing in recipe_data.get("usedIngredients", [])
                    ],
                    missed_ingredients=[
                        ing.get("name", "") for ing in recipe_data.get("missedIngredients", [])
                    ],
                    match_ratio=recipe_data.get("usedIngredientCount", 0)
                    / max(1, len(ingredients or [])),
                    raw_data=recipe_data,
                )
                results.append(result)

            self._performance_stats["spoonacular_queries"] += 1
            return results

        except Exception as e:
            logger.error(f"Spoonacular search failed: {e}")
            return []

    async def _generate_ai_recipes(
        self,
        user_id: Optional[int] = None,
        ingredients: Optional[List[str]] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        max_results: int = 3,
    ) -> List[RecipeResult]:
        """Generate recipes using AI (OpenAI/CrewAI)."""
        try:
            # This would integrate with existing AI recipe generation
            # For now, return empty list as AI generation is complex
            logger.info("AI recipe generation not yet implemented in fallback service")
            return []

        except Exception as e:
            logger.error(f"AI recipe generation failed: {e}")
            return []

    async def _get_backup_recipe_details(
        self, recipe_id: int, include_nutrition: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get detailed backup recipe information."""
        try:
            pool = await get_db_pool()
            recipe_details = await get_backup_recipe_details(
                recipe_id=recipe_id, includeNutrition=include_nutrition, pool=pool
            )
            return recipe_details

        except Exception as e:
            logger.error(f"Failed to get backup recipe details for {recipe_id}: {e}")
            return None

    async def _get_spoonacular_recipe_details(
        self, recipe_id: int, include_nutrition: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get detailed Spoonacular recipe information."""
        try:
            if self.spoonacular_service is None:
                from backend_gateway.services.spoonacular_service import SpoonacularService

                self.spoonacular_service = SpoonacularService()

            return await self.spoonacular_service.get_recipe_information(
                recipe_id=recipe_id, include_nutrition=include_nutrition
            )

        except Exception as e:
            logger.error(f"Failed to get Spoonacular recipe details for {recipe_id}: {e}")
            return None

    def _sort_and_prioritize_results(
        self, results: List[RecipeResult], config: RecipeSearchConfig
    ) -> List[RecipeResult]:
        """Sort and prioritize results based on quality and preferences."""

        def sort_key(result: RecipeResult) -> tuple:
            # Priority factors (lower is better for sorting)
            source_priority = {
                RecipeSource.BACKUP_LOCAL: 1,  # Prefer local first
                RecipeSource.SPOONACULAR: 2,
                RecipeSource.OPENAI: 3,
                RecipeSource.CREW_AI: 3,
            }.get(result.source, 4)

            # Match ratio (higher is better, so negate)
            match_score = -(result.match_ratio or 0.0)

            # Image preference (lower is better)
            image_score = 0 if result.image_url else (1 if config.prefer_images else 0)

            # Ready time preference (shorter is better)
            time_score = result.ready_in_minutes or 999

            return (source_priority, match_score, image_score, time_score)

        return sorted(results, key=sort_key)

    def _update_performance_stats(self, elapsed_time: float, results: List[RecipeResult]):
        """Update performance tracking statistics."""
        # Update average response time
        self._performance_stats["avg_response_time"] = (
            self._performance_stats["avg_response_time"] + elapsed_time
        ) / 2

        # Calculate success rates
        total_queries = (
            self._performance_stats["backup_queries"]
            + self._performance_stats["spoonacular_queries"]
            + self._performance_stats["openai_queries"]
        )

        if total_queries > 0:
            backup_success = len([r for r in results if r.source == RecipeSource.BACKUP_LOCAL])
            spoonacular_success = len([r for r in results if r.source == RecipeSource.SPOONACULAR])

            self._performance_stats["backup_success_rate"] = backup_success / max(
                1, self._performance_stats["backup_queries"]
            )
            self._performance_stats["spoonacular_success_rate"] = spoonacular_success / max(
                1, self._performance_stats["spoonacular_queries"]
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return self._performance_stats.copy()


# Global service instance
recipe_fallback_service = RecipeFallbackService()


def get_recipe_fallback_service() -> RecipeFallbackService:
    """Get the recipe fallback service instance."""
    return recipe_fallback_service
