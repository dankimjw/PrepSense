"""Service for managing user's saved recipes"""

import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.cloud import bigquery

from backend_gateway.services.bigquery_service import BigQueryService

logger = logging.getLogger(__name__)


class UserRecipesService:
    """Service for handling user recipe operations"""
    
    def __init__(self, bq_service: BigQueryService):
        self.bq_service = bq_service
        self.table_name = f"{self.bq_service.project_id}.{self.bq_service.dataset_id}.user_recipes"
        
    async def save_recipe(
        self,
        user_id: int,
        recipe_id: Optional[int],
        recipe_title: str,
        recipe_image: Optional[str],
        recipe_data: Dict[str, Any],
        source: str,
        rating: str = "neutral",
        is_favorite: bool = False,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Save a recipe to user's collection"""
        try:
            recipe_uuid = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Extract metadata from recipe_data if available
            prep_time = None
            cook_time = None
            total_time = None
            servings = None
            cuisine = []
            dish_type = []
            diet_labels = []
            
            # Extract from Spoonacular data format
            if source == "spoonacular" and isinstance(recipe_data, dict):
                prep_time = recipe_data.get("preparationMinutes")
                cook_time = recipe_data.get("cookingMinutes")
                total_time = recipe_data.get("readyInMinutes")
                servings = recipe_data.get("servings")
                cuisine = recipe_data.get("cuisines", [])
                dish_type = recipe_data.get("dishTypes", [])
                diet_labels = recipe_data.get("diets", [])
            
            # Prepare the data for BigQuery
            row_to_insert = {
                "id": recipe_uuid,
                "user_id": user_id,
                "recipe_id": recipe_id,
                "recipe_title": recipe_title,
                "recipe_image": recipe_image,
                "recipe_data": recipe_data,  # This will be stored as JSON
                "source": source,
                "rating": rating,
                "is_favorite": is_favorite,
                "notes": notes,
                "prep_time": prep_time,
                "cook_time": cook_time,
                "total_time": total_time,
                "servings": servings,
                "cuisine": cuisine,
                "dish_type": dish_type,
                "diet_labels": diet_labels,
                "tags": tags or [],
                "times_cooked": 0,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            # Insert into BigQuery
            query = f"""
            INSERT INTO `{self.table_name}` 
            (id, user_id, recipe_id, recipe_title, recipe_image, recipe_data, 
             source, rating, is_favorite, notes, prep_time, cook_time, total_time,
             servings, cuisine, dish_type, diet_labels, tags, times_cooked,
             created_at, updated_at)
            VALUES 
            (@id, @user_id, @recipe_id, @recipe_title, @recipe_image, 
             PARSE_JSON(@recipe_data), @source, @rating, @is_favorite, @notes,
             @prep_time, @cook_time, @total_time, @servings, @cuisine, @dish_type,
             @diet_labels, @tags, @times_cooked,
             TIMESTAMP(@created_at), TIMESTAMP(@updated_at))
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", recipe_uuid),
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id),
                    bigquery.ScalarQueryParameter("recipe_id", "INTEGER", recipe_id),
                    bigquery.ScalarQueryParameter("recipe_title", "STRING", recipe_title),
                    bigquery.ScalarQueryParameter("recipe_image", "STRING", recipe_image),
                    bigquery.ScalarQueryParameter("recipe_data", "STRING", json.dumps(recipe_data)),
                    bigquery.ScalarQueryParameter("source", "STRING", source),
                    bigquery.ScalarQueryParameter("rating", "STRING", rating),
                    bigquery.ScalarQueryParameter("is_favorite", "BOOL", is_favorite),
                    bigquery.ScalarQueryParameter("notes", "STRING", notes),
                    bigquery.ScalarQueryParameter("prep_time", "INTEGER", prep_time),
                    bigquery.ScalarQueryParameter("cook_time", "INTEGER", cook_time),
                    bigquery.ScalarQueryParameter("total_time", "INTEGER", total_time),
                    bigquery.ScalarQueryParameter("servings", "INTEGER", servings),
                    bigquery.ArrayQueryParameter("cuisine", "STRING", cuisine),
                    bigquery.ArrayQueryParameter("dish_type", "STRING", dish_type),
                    bigquery.ArrayQueryParameter("diet_labels", "STRING", diet_labels),
                    bigquery.ArrayQueryParameter("tags", "STRING", tags or []),
                    bigquery.ScalarQueryParameter("times_cooked", "INTEGER", 0),
                    bigquery.ScalarQueryParameter("created_at", "STRING", now.isoformat()),
                    bigquery.ScalarQueryParameter("updated_at", "STRING", now.isoformat()),
                ]
            )
            
            self.bq_service.client.query(query, job_config=job_config).result()
            
            logger.info(f"Recipe saved successfully for user {user_id}: {recipe_title} (source: {source}, favorite: {is_favorite})")
            return {
                "id": recipe_uuid,
                "message": "Recipe saved successfully",
                "recipe_title": recipe_title,
                "source": source,
                "is_favorite": is_favorite
            }
            
        except Exception as e:
            logger.error(f"Error saving recipe: {str(e)}")
            raise
            
    async def get_user_recipes(
        self,
        user_id: int,
        rating_filter: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's saved recipes with optional filtering"""
        try:
            query = f"""
            SELECT 
                id,
                recipe_id,
                recipe_title,
                recipe_image,
                TO_JSON_STRING(recipe_data) as recipe_data,
                source,
                rating,
                is_favorite,
                notes,
                prep_time,
                cook_time,
                total_time,
                servings,
                cuisine,
                dish_type,
                diet_labels,
                tags,
                times_cooked,
                last_cooked_at,
                created_at,
                updated_at
            FROM `{self.table_name}`
            WHERE user_id = @user_id
            """
            
            query_params = [
                bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id)
            ]
            
            if rating_filter and rating_filter in ["thumbs_up", "thumbs_down"]:
                query += " AND rating = @rating"
                query_params.append(
                    bigquery.ScalarQueryParameter("rating", "STRING", rating_filter)
                )
            
            if is_favorite is not None:
                query += " AND is_favorite = @is_favorite"
                query_params.append(
                    bigquery.ScalarQueryParameter("is_favorite", "BOOL", is_favorite)
                )
                
            query += " ORDER BY created_at DESC"
            query += f" LIMIT {limit} OFFSET {offset}"
            
            job_config = bigquery.QueryJobConfig(query_parameters=query_params)
            
            results = self.bq_service.client.query(query, job_config=job_config).result()
            
            recipes = []
            for row in results:
                recipe = dict(row)
                # Parse the JSON string back to dict
                if recipe.get('recipe_data'):
                    recipe['recipe_data'] = json.loads(recipe['recipe_data'])
                recipes.append(recipe)
                
            return recipes
            
        except Exception as e:
            logger.error(f"Error getting user recipes: {str(e)}")
            raise
            
    async def update_recipe_rating(
        self,
        user_id: int,
        recipe_id: str,
        rating: str
    ) -> Dict[str, Any]:
        """Update the rating of a saved recipe"""
        try:
            if rating not in ["thumbs_up", "thumbs_down", "neutral"]:
                raise ValueError("Invalid rating value")
                
            query = f"""
            UPDATE `{self.table_name}`
            SET 
                rating = @rating,
                is_favorite = @is_favorite,
                updated_at = TIMESTAMP(@updated_at)
            WHERE id = @id AND user_id = @user_id
            """
            
            now = datetime.utcnow()
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("rating", "STRING", rating),
                    bigquery.ScalarQueryParameter("is_favorite", "BOOL", rating == "thumbs_up"),
                    bigquery.ScalarQueryParameter("updated_at", "STRING", now.isoformat()),
                    bigquery.ScalarQueryParameter("id", "STRING", recipe_id),
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id),
                ]
            )
            
            result = self.bq_service.client.query(query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                return {
                    "success": True,
                    "message": f"Recipe rating updated to {rating}"
                }
            else:
                return {
                    "success": False,
                    "message": "Recipe not found or unauthorized"
                }
                
        except Exception as e:
            logger.error(f"Error updating recipe rating: {str(e)}")
            raise
            
    async def update_recipe_favorite(
        self,
        user_id: int,
        recipe_id: str,
        is_favorite: bool
    ) -> Dict[str, Any]:
        """Update the favorite status of a recipe"""
        try:
            query = f"""
            UPDATE `{self.table_name}`
            SET 
                is_favorite = @is_favorite,
                updated_at = CURRENT_TIMESTAMP()
            WHERE id = @id AND user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", recipe_id),
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id),
                    bigquery.ScalarQueryParameter("is_favorite", "BOOL", is_favorite),
                ]
            )
            
            result = self.bq_service.client.query(query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                return {
                    "success": True,
                    "message": f"Recipe {'added to' if is_favorite else 'removed from'} favorites"
                }
            else:
                return {
                    "success": False,
                    "message": "Recipe not found or unauthorized"
                }
                
        except Exception as e:
            logger.error(f"Error updating recipe favorite: {str(e)}")
            raise
            
    async def delete_user_recipe(
        self,
        user_id: int,
        recipe_id: str
    ) -> Dict[str, Any]:
        """Delete a recipe from user's collection"""
        try:
            query = f"""
            DELETE FROM `{self.table_name}`
            WHERE id = @id AND user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", recipe_id),
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id),
                ]
            )
            
            result = self.bq_service.client.query(query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                return {
                    "success": True,
                    "message": "Recipe deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Recipe not found or unauthorized"
                }
                
        except Exception as e:
            logger.error(f"Error deleting recipe: {str(e)}")
            raise
            
    async def check_recipe_exists(
        self,
        user_id: int,
        recipe_id: int
    ) -> Optional[Dict[str, Any]]:
        """Check if a recipe already exists in user's collection"""
        try:
            query = f"""
            SELECT id, rating, is_favorite
            FROM `{self.table_name}`
            WHERE user_id = @user_id AND recipe_id = @recipe_id
            LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id),
                    bigquery.ScalarQueryParameter("recipe_id", "INTEGER", recipe_id),
                ]
            )
            
            results = self.bq_service.client.query(query, job_config=job_config).result()
            
            for row in results:
                return dict(row)
                
            return None
            
        except Exception as e:
            logger.error(f"Error checking recipe existence: {str(e)}")
            raise
            
    async def increment_times_cooked(
        self,
        user_id: int,
        recipe_id: str
    ) -> Dict[str, Any]:
        """Increment the times_cooked counter for a recipe"""
        try:
            query = f"""
            UPDATE `{self.table_name}`
            SET 
                times_cooked = times_cooked + 1,
                last_cooked_at = CURRENT_TIMESTAMP(),
                updated_at = CURRENT_TIMESTAMP()
            WHERE id = @id AND user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id", "STRING", recipe_id),
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id),
                ]
            )
            
            result = self.bq_service.client.query(query, job_config=job_config).result()
            
            if result.num_dml_affected_rows > 0:
                return {
                    "success": True,
                    "message": "Recipe cooking count updated"
                }
            else:
                return {
                    "success": False,
                    "message": "Recipe not found or unauthorized"
                }
                
        except Exception as e:
            logger.error(f"Error incrementing times cooked: {str(e)}")
            raise
            
    async def get_user_recipe_stats(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get statistics about user's saved recipes"""
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_saved,
                COUNTIF(rating = 'thumbs_up') as thumbs_up_count,
                COUNTIF(rating = 'thumbs_down') as thumbs_down_count,
                COUNTIF(is_favorite = TRUE) as favorite_count,
                SUM(times_cooked) as total_times_cooked,
                ARRAY_AGG(DISTINCT cuisine IGNORE NULLS) as unique_cuisines,
                ARRAY_AGG(DISTINCT source IGNORE NULLS) as recipe_sources
            FROM `{self.table_name}`,
            UNNEST(cuisine) as cuisine
            WHERE user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "INTEGER", user_id)
                ]
            )
            
            results = self.bq_service.client.query(query, job_config=job_config).result()
            
            for row in results:
                return dict(row)
                
            return {
                "total_saved": 0,
                "thumbs_up_count": 0,
                "thumbs_down_count": 0,
                "favorite_count": 0,
                "total_times_cooked": 0,
                "unique_cuisines": [],
                "recipe_sources": []
            }
            
        except Exception as e:
            logger.error(f"Error getting user recipe stats: {str(e)}")
            raise