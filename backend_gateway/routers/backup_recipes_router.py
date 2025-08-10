"""
Backup recipes router providing local recipe search and retrieval.
Compatible with Spoonacular API format for seamless fallback integration.

🟡 PARTIAL - API router implementation (requires app.py registration)
"""

import logging
from datetime import datetime
from typing import Any, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import FileResponse

from backend_gateway.core.database import get_db_pool
from backend_gateway.services.backup_recipe_image_service import serve_backup_recipe_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backup-recipes", tags=["backup-recipes"])


# Response models matching Spoonacular format for compatibility
class BackupRecipeSearchResult:
    """Recipe search result compatible with Spoonacular API."""

    def __init__(self, db_row: dict):
        self.id = db_row.get("backup_recipe_id")
        self.title = db_row.get("title")
        self.image = (
            f"/api/v1/backup-recipes/images/{db_row.get('image_name')}"
            if db_row.get("image_name")
            else None
        )
        self.imageType = "jpg"
        self.usedIngredientCount = db_row.get("matched_ingredient_count", 0)
        self.missedIngredientCount = db_row.get("missing_ingredient_count", 0)
        self.missedIngredients = db_row.get("missing_ingredients", [])
        self.usedIngredients = db_row.get("matched_ingredients", [])
        self.unusedIngredients = []
        self.likes = 0  # Not available in our dataset
        self.match_ratio = db_row.get("match_ratio", 0.0)


class BackupRecipeDetail:
    """Detailed recipe information compatible with Spoonacular API."""

    def __init__(self, db_row: dict, ingredients: list[dict]):
        self.id = db_row.get("backup_recipe_id")
        self.title = db_row.get("title")
        self.image = (
            f"/api/v1/backup-recipes/images/{db_row.get('image_name')}"
            if db_row.get("image_name")
            else None
        )
        self.imageType = "jpg"
        self.servings = db_row.get("servings", 4)
        self.readyInMinutes = db_row.get("prep_time", 15) + db_row.get("cook_time", 30)
        self.cookingMinutes = db_row.get("cook_time", 30)
        self.preparationMinutes = db_row.get("prep_time", 15)
        self.cuisines = [db_row.get("cuisine_type", "american")]
        self.dishTypes = []
        self.diets = []
        self.instructions = self._parse_instructions(db_row.get("instructions", ""))
        self.extendedIngredients = self._format_ingredients(ingredients)
        self.summary = f"A delicious {db_row.get('cuisine_type', 'american')} recipe for {db_row.get('title', 'Unknown Recipe')}."
        self.spoonacularSourceUrl = None
        self.sourceUrl = None
        self.creditsText = "Recipe Dataset"
        self.sourceName = "Backup Recipe Database"

    def _parse_instructions(self, instructions_text: str) -> list[dict]:
        """Parse instructions into Spoonacular-compatible format."""
        if not instructions_text:
            return []

        # Split by sentences or paragraphs
        steps = [step.strip() for step in instructions_text.split("\n") if step.strip()]
        if not steps:
            steps = [step.strip() for step in instructions_text.split(".") if step.strip()]

        return [
            {
                "number": i + 1,
                "step": step,
                "ingredients": [],  # Would require parsing to extract
                "equipment": [],  # Would require parsing to extract
            }
            for i, step in enumerate(steps)
        ]

    def _format_ingredients(self, ingredients: list[dict]) -> list[dict]:
        """Format ingredients into Spoonacular-compatible format."""
        return [
            {
                "id": i + 1,
                "aisle": "Unknown",
                "image": None,
                "consistency": "solid",
                "name": ing.get("ingredient_name", ""),
                "nameClean": ing.get("ingredient_name", ""),
                "original": ing.get("original_text", ""),
                "originalName": ing.get("ingredient_name", ""),
                "amount": self._parse_amount(ing.get("quantity", "")),
                "unit": ing.get("unit", ""),
                "meta": [],
                "measures": {
                    "us": {
                        "amount": self._parse_amount(ing.get("quantity", "")),
                        "unitShort": ing.get("unit", ""),
                        "unitLong": ing.get("unit", ""),
                    },
                    "metric": {
                        "amount": self._parse_amount(ing.get("quantity", "")),
                        "unitShort": ing.get("unit", ""),
                        "unitLong": ing.get("unit", ""),
                    },
                },
            }
            for i, ing in enumerate(ingredients)
        ]

    def _parse_amount(self, quantity_str: str) -> float:
        """Parse quantity string to float."""
        if not quantity_str:
            return 0.0

        try:
            # Handle simple fractions
            if "/" in quantity_str:
                parts = quantity_str.split("/")
                if len(parts) == 2:
                    return float(parts[0]) / float(parts[1])

            # Handle ranges (take average)
            if "-" in quantity_str:
                parts = quantity_str.split("-")
                if len(parts) == 2:
                    return (float(parts[0]) + float(parts[1])) / 2

            return float(quantity_str)
        except (ValueError, ZeroDivisionError):
            return 0.0


@router.get("/search")
async def search_backup_recipes(
    query: Optional[str] = Query(None, description="Search query for recipe title"),
    ingredients: Optional[str] = Query(
        None, description="Comma-separated list of available ingredients"
    ),
    cuisine: Optional[str] = Query(None, description="Cuisine type filter"),
    diet: Optional[str] = Query(None, description="Diet type filter"),
    intolerances: Optional[str] = Query(None, description="Food intolerances to avoid"),
    equipment: Optional[str] = Query(None, description="Available equipment"),
    includeNutrition: bool = Query(False, description="Include nutrition information"),
    instructionsRequired: bool = Query(True, description="Only return recipes with instructions"),
    fillIngredients: bool = Query(
        False, description="Add information about used and missed ingredients"
    ),
    addRecipeInformation: bool = Query(False, description="Add meta information about the recipes"),
    maxReadyTime: Optional[int] = Query(None, description="Maximum ready time in minutes"),
    minReadyTime: Optional[int] = Query(None, description="Minimum ready time in minutes"),
    sort: Optional[str] = Query("popularity", description="Sort order"),
    sortDirection: Optional[str] = Query("desc", description="Sort direction"),
    offset: int = Query(0, description="Number of results to skip"),
    number: int = Query(10, description="Number of results to return"),
    limitLicense: bool = Query(True, description="Whether to limit to recipes with a license"),
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, Any]:
    """
    Search backup recipes with filters.
    Compatible with Spoonacular complexSearch API.
    """
    try:
        # Build search query
        where_conditions = []
        query_params = []
        param_count = 0

        # Text search
        if query:
            param_count += 1
            where_conditions.append(f"search_vector @@ plainto_tsquery('english', ${param_count})")
            query_params.append(query)

        # Cuisine filter
        if cuisine:
            param_count += 1
            where_conditions.append(f"cuisine_type ILIKE ${param_count}")
            query_params.append(f"%{cuisine}%")

        # Ready time filters
        if maxReadyTime:
            param_count += 1
            where_conditions.append(f"(prep_time + cook_time) <= ${param_count}")
            query_params.append(maxReadyTime)

        if minReadyTime:
            param_count += 1
            where_conditions.append(f"(prep_time + cook_time) >= ${param_count}")
            query_params.append(minReadyTime)

        # Instructions required
        if instructionsRequired:
            where_conditions.append("instructions IS NOT NULL AND instructions != ''")

        # Build ingredient-based search if provided
        ingredient_join = ""
        ingredient_select = ""
        if ingredients and fillIngredients:
            ingredient_list = [ing.strip().lower() for ing in ingredients.split(",")]
            param_count += 1

            # Use the custom search function for ingredient matching
            ingredient_search_query = f"""
                SELECT * FROM search_backup_recipes_by_ingredients(
                    ${param_count}, 0.1, {number + offset}
                ) sr
                WHERE sr.backup_recipe_id = br.backup_recipe_id
            """
            query_params.append(ingredient_list)
            ingredient_join = f"JOIN ({ingredient_search_query}) ingredient_matches ON true"
            ingredient_select = """
                , ingredient_matches.match_ratio,
                ingredient_matches.missing_ingredients,
                ingredient_matches.matched_ingredients,
                array_length(ingredient_matches.matched_ingredients, 1) as matched_ingredient_count,
                array_length(ingredient_matches.missing_ingredients, 1) as missing_ingredient_count
            """

        # Combine WHERE conditions
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Build ORDER BY clause
        order_clause = "ORDER BY created_at DESC"
        if ingredients and fillIngredients:
            order_clause = (
                "ORDER BY ingredient_matches.match_ratio DESC, (prep_time + cook_time) ASC"
            )
        elif sort == "time":
            order_clause = f"ORDER BY (prep_time + cook_time) {sortDirection.upper()}"
        elif sort == "popularity":
            order_clause = f"ORDER BY title {sortDirection.upper()}"

        # Build final query
        search_query = f"""
            SELECT
                br.backup_recipe_id,
                br.title,
                br.image_name,
                br.prep_time,
                br.cook_time,
                br.servings,
                br.difficulty,
                br.cuisine_type
                {ingredient_select}
            FROM backup_recipes br
            {ingredient_join}
            {where_clause}
            {order_clause}
            LIMIT {number} OFFSET {offset}
        """

        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM backup_recipes br
            {ingredient_join}
            {where_clause}
        """

        async with pool.acquire() as conn:
            # Execute searches
            recipes = await conn.fetch(search_query, *query_params)
            total_results = await conn.fetchval(count_query, *query_params)

            # Format results
            formatted_recipes = []
            for recipe in recipes:
                recipe_dict = dict(recipe)
                search_result = BackupRecipeSearchResult(recipe_dict)
                formatted_recipes.append(search_result.__dict__)

            return {
                "results": formatted_recipes,
                "offset": offset,
                "number": len(formatted_recipes),
                "totalResults": total_results or 0,
            }

    except Exception as e:
        logger.error(f"Error searching backup recipes: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@router.get("/{recipe_id}")
async def get_backup_recipe_details(
    recipe_id: int = Path(..., description="Backup recipe ID"),
    includeNutrition: bool = Query(False, description="Include nutrition information"),
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, Any]:
    """
    Get detailed backup recipe information.
    Compatible with Spoonacular recipe information API.
    """
    try:
        async with pool.acquire() as conn:
            # Get recipe details
            recipe = await conn.fetchrow(
                """
                SELECT * FROM backup_recipes
                WHERE backup_recipe_id = $1
            """,
                recipe_id,
            )

            if not recipe:
                raise HTTPException(status_code=404, detail="Recipe not found")

            # Get ingredients
            ingredients = await conn.fetch(
                """
                SELECT * FROM backup_recipe_ingredients
                WHERE backup_recipe_id = $1
                ORDER BY ingredient_name
            """,
                recipe_id,
            )

            # Format response
            recipe_detail = BackupRecipeDetail(dict(recipe), [dict(ing) for ing in ingredients])

            return recipe_detail.__dict__

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recipe {recipe_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recipe: {str(e)}") from e


@router.get("/images/{image_name}")
async def serve_recipe_image(
    image_name: str = Path(..., description="Image filename"),
    optimized: bool = Query(True, description="Return optimized version"),
):
    """Serve backup recipe images."""
    try:
        image_path, metadata = await serve_backup_recipe_image(image_name, optimized)

        if not image_path or not metadata.get("exists"):
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(path=str(image_path), media_type="image/jpeg", filename=image_name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {image_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image") from e


@router.get("/random")
async def get_random_backup_recipes(
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    number: int = Query(1, description="Number of random recipes"),
    pool: asyncpg.Pool = Depends(get_db_pool),
) -> dict[str, Any]:
    """Get random backup recipes."""
    try:
        # Build tag filter if provided
        where_clause = ""
        query_params = []

        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            # Simple tag matching in title or cuisine
            where_clause = "WHERE " + " OR ".join(
                [f"title ILIKE '%{tag}%' OR cuisine_type ILIKE '%{tag}%'" for tag in tag_list]
            )

        query = f"""
            SELECT
                backup_recipe_id,
                title,
                image_name,
                prep_time,
                cook_time,
                servings,
                difficulty,
                cuisine_type
            FROM backup_recipes
            {where_clause}
            ORDER BY RANDOM()
            LIMIT {number}
        """

        async with pool.acquire() as conn:
            recipes = await conn.fetch(query, *query_params)

            formatted_recipes = []
            for recipe in recipes:
                recipe_dict = dict(recipe)
                search_result = BackupRecipeSearchResult(recipe_dict)
                formatted_recipes.append(search_result.__dict__)

            return {"recipes": formatted_recipes}

    except Exception as e:
        logger.error(f"Error getting random recipes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get random recipes: {str(e)}"
        ) from e


@router.get("/stats")
async def get_backup_recipe_stats(pool: asyncpg.Pool = Depends(get_db_pool)) -> dict[str, Any]:
    """Get statistics about the backup recipe database."""
    try:
        async with pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_recipes,
                    COUNT(DISTINCT cuisine_type) as cuisine_count,
                    COUNT(CASE WHEN image_name IS NOT NULL THEN 1 END) as recipes_with_images,
                    AVG(prep_time + cook_time) as avg_total_time,
                    COUNT(CASE WHEN difficulty = 'easy' THEN 1 END) as easy_recipes,
                    COUNT(CASE WHEN difficulty = 'medium' THEN 1 END) as medium_recipes,
                    COUNT(CASE WHEN difficulty = 'hard' THEN 1 END) as hard_recipes
                FROM backup_recipes
            """
            )

            ingredient_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(DISTINCT ingredient_name) as unique_ingredients,
                    AVG(ingredient_count.cnt) as avg_ingredients_per_recipe
                FROM (
                    SELECT backup_recipe_id, COUNT(*) as cnt
                    FROM backup_recipe_ingredients
                    GROUP BY backup_recipe_id
                ) ingredient_count
            """
            )

            return {
                "total_recipes": stats["total_recipes"],
                "cuisine_count": stats["cuisine_count"],
                "recipes_with_images": stats["recipes_with_images"],
                "avg_total_time_minutes": round(stats["avg_total_time"] or 0, 1),
                "difficulty_distribution": {
                    "easy": stats["easy_recipes"],
                    "medium": stats["medium_recipes"],
                    "hard": stats["hard_recipes"],
                },
                "unique_ingredients": ingredient_stats["unique_ingredients"],
                "avg_ingredients_per_recipe": round(
                    ingredient_stats["avg_ingredients_per_recipe"] or 0, 1
                ),
                "last_updated": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error getting backup recipe stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") from e


@router.post("/reindex")
async def reindex_search_vectors(pool: asyncpg.Pool = Depends(get_db_pool)) -> dict[str, str]:
    """Manually trigger search vector reindexing."""
    try:
        async with pool.acquire() as conn:
            # Update all search vectors
            await conn.execute(
                """
                UPDATE backup_recipes SET updated_at = CURRENT_TIMESTAMP
            """
            )

            return {"message": "Search vectors reindexed successfully"}

    except Exception as e:
        logger.error(f"Error reindexing search vectors: {e}")
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}") from e
