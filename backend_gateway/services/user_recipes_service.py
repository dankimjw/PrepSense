"""Service for managing user's saved recipes using PostgreSQL"""

import json
import logging
from typing import Any, Optional

from backend_gateway.services.recipe_enrichment_service import RecipeEnrichmentService

logger = logging.getLogger(__name__)


class UserRecipesService:
    """Service for handling user recipe operations with PostgreSQL"""

    def __init__(self, db_service):
        self.db_service = db_service
        self.enrichment_service = RecipeEnrichmentService()

    async def save_recipe(
        self,
        user_id: int,
        recipe_id: Optional[int],
        recipe_title: str,
        recipe_image: Optional[str],
        recipe_data: dict[str, Any],
        source: str,
        rating: str = "neutral",
        is_favorite: bool = False,
        notes: Optional[str] = None,
        tags: Optional[list[str]] = None,
        status: str = "saved",
        is_demo: bool = False,
    ) -> dict[str, Any]:
        """Save a recipe to user's collection"""
        try:
            # Check if recipe already exists for this user
            check_query = """
            SELECT id FROM user_recipes
            WHERE user_id = %(user_id)s
            AND recipe_title = %(recipe_title)s
            AND source = %(source)s
            """

            existing = self.db_service.execute_query(
                check_query, {"user_id": user_id, "recipe_title": recipe_title, "source": source}
            )

            if existing:
                # Update existing recipe
                update_query = """
                UPDATE user_recipes
                SET
                    recipe_data = %(recipe_data)s,
                    rating = %(rating)s,
                    is_favorite = %(is_favorite)s,
                    is_demo = %(is_demo)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(id)s
                RETURNING id
                """

                result = self.db_service.execute_query(
                    update_query,
                    {
                        "recipe_data": json.dumps(recipe_data),
                        "rating": rating,
                        "is_favorite": is_favorite,
                        "is_demo": is_demo,
                        "id": existing[0]["id"],
                    },
                )

                logger.info(f"Updated existing recipe for user {user_id}: {recipe_title}")
                return {
                    "success": True,
                    "recipe_id": existing[0]["id"],
                    "message": "Recipe updated successfully",
                    "action": "updated",
                }
            else:
                # For external recipes (spoonacular), we need to handle the foreign key constraint
                # by setting recipe_id to NULL since these recipes don't exist in our local recipes table
                if source == "spoonacular" and recipe_id:
                    # Store the external recipe_id in the recipe_data for reference
                    recipe_data["external_recipe_id"] = recipe_id
                    recipe_id_to_save = None  # Set to NULL to avoid foreign key constraint
                else:
                    recipe_id_to_save = recipe_id

                # Automatically mark recipes with IDs 2001-2005 as demo recipes
                if recipe_id and 2001 <= recipe_id <= 2005 or source == "demo":
                    is_demo = True

                # Insert new recipe - handle is_demo column existence
                try:
                    # First, check if is_demo column exists
                    column_check = """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'user_recipes' AND column_name = 'is_demo'
                    );
                    """
                    column_exists_result = self.db_service.execute_query(column_check)
                    has_is_demo = (
                        column_exists_result[0]["exists"] if column_exists_result else False
                    )

                    if has_is_demo:
                        # Use query with is_demo column
                        insert_query = """
                        INSERT INTO user_recipes (
                            user_id, recipe_id, recipe_title, recipe_image,
                            recipe_data, source, rating, is_favorite, status, is_demo
                        ) VALUES (
                            %(user_id)s, %(recipe_id)s, %(recipe_title)s, %(recipe_image)s,
                            %(recipe_data)s, %(source)s, %(rating)s, %(is_favorite)s, %(status)s, %(is_demo)s
                        ) RETURNING id
                        """

                        result = self.db_service.execute_query(
                            insert_query,
                            {
                                "user_id": user_id,
                                "recipe_id": recipe_id_to_save,
                                "recipe_title": recipe_title,
                                "recipe_image": recipe_image,
                                "recipe_data": json.dumps(recipe_data),
                                "source": source,
                                "rating": rating,
                                "is_favorite": is_favorite,
                                "status": status,
                                "is_demo": is_demo,
                            },
                        )
                    else:
                        # Use query without is_demo column (fallback)
                        insert_query = """
                        INSERT INTO user_recipes (
                            user_id, recipe_id, recipe_title, recipe_image,
                            recipe_data, source, rating, is_favorite, status
                        ) VALUES (
                            %(user_id)s, %(recipe_id)s, %(recipe_title)s, %(recipe_image)s,
                            %(recipe_data)s, %(source)s, %(rating)s, %(is_favorite)s, %(status)s
                        ) RETURNING id
                        """

                        result = self.db_service.execute_query(
                            insert_query,
                            {
                                "user_id": user_id,
                                "recipe_id": recipe_id_to_save,
                                "recipe_title": recipe_title,
                                "recipe_image": recipe_image,
                                "recipe_data": json.dumps(recipe_data),
                                "source": source,
                                "rating": rating,
                                "is_favorite": is_favorite,
                                "status": status,
                            },
                        )

                        logger.warning("is_demo column not found, recipe saved without demo flag")

                except Exception as insert_error:
                    logger.error(f"Error during recipe insert: {insert_error}")
                    raise

                logger.info(
                    f"Recipe saved successfully for user {user_id}: {recipe_title} (source: {source}, demo: {is_demo})"
                )

                return {
                    "success": True,
                    "recipe_id": result[0]["id"] if result else None,
                    "message": "Recipe saved successfully",
                    "action": "created",
                }

        except Exception as e:
            logger.error(f"Error saving recipe: {str(e)}")
            raise

    async def get_user_recipes(
        self,
        user_id: int,
        source: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        rating: Optional[str] = None,
        status: Optional[str] = None,
        demo_only: bool = False,
        include_external: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get user's saved recipes with optional filters, with support for demo filtering

        Args:
            user_id: User ID to get recipes for
            source: Filter by specific source (if provided, will include that source even if external)
            is_favorite: Filter by favorite status
            rating: Filter by rating
            status: Filter by status
            demo_only: Only return demo recipes
            include_external: Include external recipes (like Spoonacular) - defaults to False for My Recipes
            limit: Maximum number of recipes to return
            offset: Offset for pagination
        """
        try:
            # Build query with filters
            conditions = ["user_id = %(user_id)s"]
            params = {"user_id": user_id}

            # CRITICAL FIX: Exclude external recipes by default unless explicitly requested
            if not include_external and not source:
                # Exclude Spoonacular and other external sources from My Recipes by default
                conditions.append("source NOT IN ('spoonacular')")
                logger.info(f"Excluding external recipes for My Recipes view for user {user_id}")

            if source:
                conditions.append("source = %(source)s")
                params["source"] = source

            if is_favorite is not None:
                conditions.append("is_favorite = %(is_favorite)s")
                params["is_favorite"] = is_favorite

            if rating:
                conditions.append("rating = %(rating)s")
                params["rating"] = rating

            # Filter by status if provided
            if status:
                conditions.append("status = %(status)s")
                params["status"] = status

            # Check if is_demo column exists
            column_check = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_recipes' AND column_name = 'is_demo'
            );
            """
            column_exists_result = self.db_service.execute_query(column_check)
            has_is_demo = column_exists_result[0]["exists"] if column_exists_result else False

            if has_is_demo:
                # Use is_demo column for filtering
                if demo_only:
                    conditions.append("is_demo = TRUE")

                query = f"""
                SELECT
                    id,
                    recipe_id,
                    recipe_title,
                    recipe_image,
                    recipe_data,
                    source,
                    rating,
                    is_favorite,
                    status,
                    cooked_at,
                    created_at,
                    updated_at,
                    is_demo
                FROM user_recipes
                WHERE {" AND ".join(conditions)}
                ORDER BY
                    is_demo DESC,
                    is_favorite DESC,
                    CASE rating
                        WHEN 'thumbs_up' THEN 1
                        WHEN 'neutral' THEN 2
                        WHEN 'thumbs_down' THEN 3
                    END,
                    created_at DESC
                LIMIT {limit} OFFSET {offset}
                """
            else:
                # Fallback to old ID-based demo detection for backward compatibility
                if demo_only:
                    conditions.append(
                        """
                        COALESCE(recipe_id,
                            CAST(recipe_data->>'external_recipe_id' AS INTEGER),
                            CAST(recipe_data->>'id' AS INTEGER)
                        ) BETWEEN 2001 AND 2005
                    """
                    )

                query = f"""
                SELECT
                    id,
                    recipe_id,
                    recipe_title,
                    recipe_image,
                    recipe_data,
                    source,
                    rating,
                    is_favorite,
                    status,
                    cooked_at,
                    created_at,
                    updated_at,
                    CASE
                        WHEN COALESCE(recipe_id,
                            CAST(recipe_data->>'external_recipe_id' AS INTEGER),
                            CAST(recipe_data->>'id' AS INTEGER)
                        ) BETWEEN 2001 AND 2005
                        THEN TRUE
                        ELSE FALSE
                    END as is_demo
                FROM user_recipes
                WHERE {" AND ".join(conditions)}
                ORDER BY
                    (CASE
                        WHEN COALESCE(recipe_id,
                            CAST(recipe_data->>'external_recipe_id' AS INTEGER),
                            CAST(recipe_data->>'id' AS INTEGER)
                        ) BETWEEN 2001 AND 2005
                        THEN 1 ELSE 0
                    END) DESC,
                    is_favorite DESC,
                    CASE rating
                        WHEN 'thumbs_up' THEN 1
                        WHEN 'neutral' THEN 2
                        WHEN 'thumbs_down' THEN 3
                    END,
                    created_at DESC
                LIMIT {limit} OFFSET {offset}
                """

            results = self.db_service.execute_query(query, params)

            # Parse JSON data
            recipes = []
            for row in results:
                recipe = dict(row)

                # PostgreSQL JSONB columns are automatically converted to Python dicts
                # Only parse if it's a string (shouldn't happen with JSONB)
                if recipe.get("recipe_data") and isinstance(recipe["recipe_data"], str):
                    try:
                        recipe["recipe_data"] = json.loads(recipe["recipe_data"])
                    except Exception:
                        recipe["recipe_data"] = {}

                # Convert datetime to ISO format
                if recipe.get("created_at"):
                    recipe["created_at"] = recipe["created_at"].isoformat()
                if recipe.get("updated_at"):
                    recipe["updated_at"] = recipe["updated_at"].isoformat()
                if recipe.get("cooked_at"):
                    recipe["cooked_at"] = recipe["cooked_at"].isoformat()

                # Enrich chat-generated recipes that lack Spoonacular-style structure
                recipe_data = recipe.get("recipe_data", {})
                source = recipe.get("source", "")

                if (source in {"chat", "openai"}) and recipe_data:
                    # Check if recipe needs enrichment
                    if not recipe_data.get("extendedIngredients") or not recipe_data.get(
                        "nutrition"
                    ):
                        try:
                            logger.info(
                                f"Enriching saved recipe: {recipe.get('recipe_title', 'Unknown')}"
                            )
                            enriched_data = self.enrichment_service.enrich_recipe(
                                recipe_data, user_id
                            )
                            recipe["recipe_data"] = enriched_data
                        except Exception as e:
                            logger.error(f"Error enriching saved recipe: {e}")

                recipes.append(recipe)

            logger.info(
                f"Retrieved {len(recipes)} recipes for user {user_id} (include_external={include_external})"
            )
            return recipes

        except Exception as e:
            logger.error(f"Error getting user recipes: {str(e)}")
            raise

    async def get_bookmarked_external_recipes(
        self, user_id: int, source: Optional[str] = "spoonacular", limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get user's bookmarked external recipes (Spoonacular, etc.) - separate from My Recipes

        This is a dedicated method for external recipe bookmarks that won't pollute My Recipes.
        """
        try:
            return await self.get_user_recipes(
                user_id=user_id,
                source=source,
                include_external=True,  # Explicitly include external recipes
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"Error getting bookmarked external recipes: {str(e)}")
            raise

    async def update_recipe_rating(
        self, user_id: int, recipe_id: int, rating: str
    ) -> dict[str, Any]:
        """Update recipe rating"""
        try:
            update_query = """
            UPDATE user_recipes
            SET rating = %(rating)s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """

            self.db_service.execute_query(
                update_query, {"rating": rating, "recipe_id": recipe_id, "user_id": user_id}
            )

            return {"success": True, "message": f"Recipe rating updated to {rating}"}

        except Exception as e:
            logger.error(f"Error updating recipe rating: {str(e)}")
            raise

    async def toggle_favorite(self, user_id: int, recipe_id: int) -> dict[str, Any]:
        """Toggle recipe favorite status"""
        try:
            # Get current status
            query = """
            SELECT is_favorite FROM user_recipes
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """

            result = self.db_service.execute_query(
                query, {"recipe_id": recipe_id, "user_id": user_id}
            )

            if not result:
                return {"success": False, "message": "Recipe not found"}

            current_favorite = result[0]["is_favorite"]
            new_favorite = not current_favorite

            # Update favorite status
            update_query = """
            UPDATE user_recipes
            SET is_favorite = %(is_favorite)s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """

            self.db_service.execute_query(
                update_query,
                {"is_favorite": new_favorite, "recipe_id": recipe_id, "user_id": user_id},
            )

            return {
                "success": True,
                "is_favorite": new_favorite,
                "message": f"Recipe {'added to' if new_favorite else 'removed from'} favorites",
            }

        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            raise

    async def delete_recipe(self, user_id: int, recipe_id: int) -> dict[str, Any]:
        """Delete a recipe from user's collection"""
        try:
            delete_query = """
            DELETE FROM user_recipes
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """

            result = self.db_service.execute_query(
                delete_query, {"recipe_id": recipe_id, "user_id": user_id}
            )

            if result and result[0].get("affected_rows", 0) > 0:
                return {"success": True, "message": "Recipe deleted successfully"}
            else:
                return {"success": False, "message": "Recipe not found"}

        except Exception as e:
            logger.error(f"Error deleting recipe: {str(e)}")
            raise

    async def mark_recipe_as_cooked(self, user_id: int, recipe_id: str) -> dict[str, Any]:
        """Mark a recipe as cooked"""
        try:
            # Check if status column exists
            check_column_query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'user_recipes'
                AND column_name = 'status'
            );
            """

            column_exists = self.db_service.execute_query(check_column_query)
            has_status_column = column_exists[0]["exists"] if column_exists else False

            if has_status_column:
                update_query = """
                UPDATE user_recipes
                SET
                    status = 'cooked',
                    cooked_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(recipe_id)s AND user_id = %(user_id)s
                RETURNING id, status, cooked_at
                """

                result = self.db_service.execute_query(
                    update_query, {"recipe_id": recipe_id, "user_id": user_id}
                )

                if result:
                    logger.info(f"Recipe {recipe_id} marked as cooked for user {user_id}")
                    return {
                        "success": True,
                        "message": "Recipe marked as cooked",
                        "recipe_id": result[0]["id"],
                        "status": result[0]["status"],
                        "cooked_at": (
                            result[0]["cooked_at"].isoformat() if result[0]["cooked_at"] else None
                        ),
                    }
            else:
                # If column doesn't exist, just update the timestamp
                update_query = """
                UPDATE user_recipes
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = %(recipe_id)s AND user_id = %(user_id)s
                RETURNING id
                """

                result = self.db_service.execute_query(
                    update_query, {"recipe_id": recipe_id, "user_id": user_id}
                )

                if result:
                    logger.info(
                        f"Recipe {recipe_id} marked as cooked for user {user_id} (status column pending migration)"
                    )
                    return {
                        "success": True,
                        "message": "Recipe marked as cooked (migration pending)",
                        "recipe_id": result[0]["id"],
                        "status": "cooked",
                        "cooked_at": None,
                    }

            return {"success": False, "message": "Recipe not found"}

        except Exception as e:
            logger.error(f"Error marking recipe as cooked: {str(e)}")
            raise

    async def get_recipe_stats(self, user_id: int) -> dict[str, Any]:
        """Get user's recipe statistics"""
        try:
            # Check if status column exists
            check_column_query = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'user_recipes'
                AND column_name = 'status'
            );
            """

            column_exists = self.db_service.execute_query(check_column_query)
            has_status_column = column_exists[0]["exists"] if column_exists else False

            if has_status_column:
                # Updated stats query to exclude external recipes from main counts
                stats_query = """
                SELECT
                    COUNT(CASE WHEN source NOT IN ('spoonacular') THEN 1 END) as total_recipes,
                    COUNT(CASE WHEN is_favorite AND source NOT IN ('spoonacular') THEN 1 END) as favorite_recipes,
                    COUNT(CASE WHEN source = 'chat' THEN 1 END) as ai_generated_recipes,
                    COUNT(CASE WHEN source = 'spoonacular' THEN 1 END) as bookmarked_external_recipes,
                    COUNT(CASE WHEN rating = 'thumbs_up' AND source NOT IN ('spoonacular') THEN 1 END) as liked_recipes,
                    COUNT(CASE WHEN rating = 'thumbs_down' AND source NOT IN ('spoonacular') THEN 1 END) as disliked_recipes,
                    COUNT(CASE WHEN status = 'saved' AND source NOT IN ('spoonacular') THEN 1 END) as saved_recipes,
                    COUNT(CASE WHEN status = 'cooked' AND source NOT IN ('spoonacular') THEN 1 END) as cooked_recipes
                FROM user_recipes
                WHERE user_id = %(user_id)s
                """
            else:
                # Fallback query without status column, still excluding external recipes
                stats_query = """
                SELECT
                    COUNT(CASE WHEN source NOT IN ('spoonacular') THEN 1 END) as total_recipes,
                    COUNT(CASE WHEN is_favorite AND source NOT IN ('spoonacular') THEN 1 END) as favorite_recipes,
                    COUNT(CASE WHEN source = 'chat' THEN 1 END) as ai_generated_recipes,
                    COUNT(CASE WHEN source = 'spoonacular' THEN 1 END) as bookmarked_external_recipes,
                    COUNT(CASE WHEN rating = 'thumbs_up' AND source NOT IN ('spoonacular') THEN 1 END) as liked_recipes,
                    COUNT(CASE WHEN rating = 'thumbs_down' AND source NOT IN ('spoonacular') THEN 1 END) as disliked_recipes
                FROM user_recipes
                WHERE user_id = %(user_id)s
                """

            result = self.db_service.execute_query(stats_query, {"user_id": user_id})

            if result:
                stats = dict(result[0])
                # Add default values if status column doesn't exist
                if not has_status_column:
                    stats["saved_recipes"] = stats["total_recipes"]
                    stats["cooked_recipes"] = 0
                return stats
            else:
                return {
                    "total_recipes": 0,
                    "favorite_recipes": 0,
                    "ai_generated_recipes": 0,
                    "bookmarked_external_recipes": 0,
                    "liked_recipes": 0,
                    "disliked_recipes": 0,
                    "saved_recipes": 0,
                    "cooked_recipes": 0,
                }

        except Exception as e:
            logger.error(f"Error getting recipe stats: {str(e)}")
            raise

    async def match_recipes_with_pantry(
        self, user_id: int, pantry_items: list[dict[str, Any]], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Match user's saved recipes with current pantry items, prioritizing demo recipes.

        NOTE: Only matches against user's actual recipes, excludes external bookmarks like Spoonacular.
        """
        try:
            # Get user's saved recipes (exclude external sources, prioritize demo recipes, favorites and liked)
            query = """
            SELECT
                id,
                recipe_title,
                recipe_image,
                recipe_data,
                rating,
                is_favorite,
                source,
                created_at,
                CASE
                    WHEN is_demo = TRUE THEN 1
                    WHEN COALESCE(recipe_id, CAST(recipe_data->>'external_recipe_id' AS INTEGER), CAST(recipe_data->>'id' AS INTEGER)) BETWEEN 2001 AND 2005
                    THEN 1
                    ELSE 0
                END as is_demo_recipe
            FROM user_recipes
            WHERE user_id = %(user_id)s
            AND source NOT IN ('spoonacular')
            ORDER BY
                is_demo_recipe DESC,
                is_favorite DESC,
                CASE rating
                    WHEN 'thumbs_up' THEN 1
                    WHEN 'neutral' THEN 2
                    WHEN 'thumbs_down' THEN 3
                END,
                created_at DESC
            LIMIT %(limit)s
            """

            recipes = self.db_service.execute_query(
                query, {"user_id": user_id, "limit": limit * 2}  # Get more to filter
            )

            if not recipes:
                return []

            # Extract pantry ingredient names for matching
            pantry_ingredients = set()
            for item in pantry_items:
                if item.get("product_name"):
                    # Clean ingredient name
                    name = item["product_name"].lower().strip()
                    # Remove size/weight info
                    if "–" in name:
                        name = name.split("–")[0].strip()
                    pantry_ingredients.add(name)

            matched_recipes = []

            for recipe in recipes:
                recipe_data = recipe.get("recipe_data", {})
                is_demo = recipe.pop("is_demo_recipe", 0)

                # Extract ingredients from recipe
                recipe_ingredients = []
                if "ingredients" in recipe_data:
                    # Handle both string and dict ingredient formats
                    for ing in recipe_data["ingredients"]:
                        if isinstance(ing, str):
                            recipe_ingredients.append(ing.lower())
                        elif isinstance(ing, dict) and "name" in ing:
                            recipe_ingredients.append(ing["name"].lower())

                # Count matching ingredients
                matched_ingredients = []
                missing_ingredients = []

                for ingredient in recipe_ingredients:
                    found = False
                    # Check if any pantry item matches this ingredient
                    for pantry_item in pantry_ingredients:
                        if pantry_item in ingredient or ingredient in pantry_item:
                            matched_ingredients.append(ingredient)
                            found = True
                            break

                    if not found:
                        missing_ingredients.append(ingredient)

                # Calculate match score
                total_ingredients = len(recipe_ingredients)
                if total_ingredients > 0:
                    match_score = len(matched_ingredients) / total_ingredients

                    # Include recipe with match info
                    matched_recipe = {
                        "id": recipe["id"],
                        "title": recipe["recipe_title"],
                        "image": recipe["recipe_image"],
                        "source": recipe["source"],
                        "rating": recipe["rating"],
                        "is_favorite": recipe["is_favorite"],
                        "is_demo_recipe": bool(is_demo),
                        "match_score": round(match_score, 2),
                        "matched_ingredients": matched_ingredients,
                        "missing_ingredients": missing_ingredients,
                        "total_ingredients": total_ingredients,
                        "can_make": len(missing_ingredients) == 0,
                        "recipe_data": recipe_data,
                    }

                    # Only include recipes with reasonable match
                    if match_score > 0.3:  # At least 30% ingredients available
                        matched_recipes.append(matched_recipe)

            # Sort by demo recipes first, then match score and user preference
            matched_recipes.sort(
                key=lambda x: (
                    x["is_demo_recipe"],  # Demo recipes first
                    x["can_make"],  # Recipes you can make
                    x["is_favorite"],  # Then favorites
                    x["rating"] == "thumbs_up",  # Then liked recipes
                    x["match_score"],  # Then by match score
                ),
                reverse=True,
            )

            return matched_recipes[:limit]

        except Exception as e:
            logger.error(f"Error matching recipes with pantry: {str(e)}")
            raise
