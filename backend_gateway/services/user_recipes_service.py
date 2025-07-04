"""Service for managing user's saved recipes using PostgreSQL"""

import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UserRecipesService:
    """Service for handling user recipe operations with PostgreSQL"""
    
    def __init__(self, db_service):
        self.db_service = db_service
        
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
            # Check if recipe already exists for this user
            check_query = """
            SELECT id FROM user_recipes 
            WHERE user_id = %(user_id)s 
            AND recipe_title = %(recipe_title)s 
            AND source = %(source)s
            """
            
            existing = self.db_service.execute_query(check_query, {
                "user_id": user_id,
                "recipe_title": recipe_title,
                "source": source
            })
            
            if existing:
                # Update existing recipe
                update_query = """
                UPDATE user_recipes 
                SET 
                    recipe_data = %(recipe_data)s,
                    rating = %(rating)s,
                    is_favorite = %(is_favorite)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(id)s
                RETURNING id
                """
                
                result = self.db_service.execute_query(update_query, {
                    "recipe_data": json.dumps(recipe_data),
                    "rating": rating,
                    "is_favorite": is_favorite,
                    "id": existing[0]['id']
                })
                
                logger.info(f"Updated existing recipe for user {user_id}: {recipe_title}")
                return {
                    "success": True,
                    "recipe_id": existing[0]['id'],
                    "message": "Recipe updated successfully",
                    "action": "updated"
                }
            else:
                # For external recipes (spoonacular), we need to handle the foreign key constraint
                # by setting recipe_id to NULL since these recipes don't exist in our local recipes table
                if source == 'spoonacular' and recipe_id:
                    # Store the external recipe_id in the recipe_data for reference
                    recipe_data['external_recipe_id'] = recipe_id
                    recipe_id_to_save = None  # Set to NULL to avoid foreign key constraint
                else:
                    recipe_id_to_save = recipe_id
                
                # Insert new recipe
                insert_query = """
                INSERT INTO user_recipes (
                    user_id, recipe_id, recipe_title, recipe_image, 
                    recipe_data, source, rating, is_favorite
                ) VALUES (
                    %(user_id)s, %(recipe_id)s, %(recipe_title)s, %(recipe_image)s,
                    %(recipe_data)s, %(source)s, %(rating)s, %(is_favorite)s
                ) RETURNING id
                """
                
                result = self.db_service.execute_query(insert_query, {
                    "user_id": user_id,
                    "recipe_id": recipe_id_to_save,
                    "recipe_title": recipe_title,
                    "recipe_image": recipe_image,
                    "recipe_data": json.dumps(recipe_data),
                    "source": source,
                    "rating": rating,
                    "is_favorite": is_favorite
                })
                
                logger.info(f"Recipe saved successfully for user {user_id}: {recipe_title} (source: {source}, favorite: {is_favorite})")
                
                return {
                    "success": True,
                    "recipe_id": result[0]['id'] if result else None,
                    "message": "Recipe saved successfully",
                    "action": "created"
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
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's saved recipes with optional filters"""
        try:
            # Build query with filters
            conditions = ["user_id = %(user_id)s"]
            params = {"user_id": user_id}
            
            if source:
                conditions.append("source = %(source)s")
                params["source"] = source
                
            if is_favorite is not None:
                conditions.append("is_favorite = %(is_favorite)s")
                params["is_favorite"] = is_favorite
                
            if rating:
                conditions.append("rating = %(rating)s")
                params["rating"] = rating
            
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
                created_at,
                updated_at
            FROM user_recipes
            WHERE {" AND ".join(conditions)}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """
            
            results = self.db_service.execute_query(query, params)
            
            # Parse JSON data
            recipes = []
            for row in results:
                recipe = dict(row)
                if recipe.get('recipe_data'):
                    try:
                        recipe['recipe_data'] = json.loads(recipe['recipe_data'])
                    except:
                        recipe['recipe_data'] = {}
                
                # Convert datetime to ISO format
                if recipe.get('created_at'):
                    recipe['created_at'] = recipe['created_at'].isoformat()
                if recipe.get('updated_at'):
                    recipe['updated_at'] = recipe['updated_at'].isoformat()
                    
                recipes.append(recipe)
            
            return recipes
            
        except Exception as e:
            logger.error(f"Error getting user recipes: {str(e)}")
            raise
    
    async def update_recipe_rating(
        self,
        user_id: int,
        recipe_id: int,
        rating: str
    ) -> Dict[str, Any]:
        """Update recipe rating"""
        try:
            update_query = """
            UPDATE user_recipes 
            SET rating = %(rating)s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """
            
            result = self.db_service.execute_query(update_query, {
                "rating": rating,
                "recipe_id": recipe_id,
                "user_id": user_id
            })
            
            return {
                "success": True,
                "message": f"Recipe rating updated to {rating}"
            }
            
        except Exception as e:
            logger.error(f"Error updating recipe rating: {str(e)}")
            raise
    
    async def toggle_favorite(
        self,
        user_id: int,
        recipe_id: int
    ) -> Dict[str, Any]:
        """Toggle recipe favorite status"""
        try:
            # Get current status
            query = """
            SELECT is_favorite FROM user_recipes 
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """
            
            result = self.db_service.execute_query(query, {
                "recipe_id": recipe_id,
                "user_id": user_id
            })
            
            if not result:
                return {
                    "success": False,
                    "message": "Recipe not found"
                }
            
            current_favorite = result[0]['is_favorite']
            new_favorite = not current_favorite
            
            # Update favorite status
            update_query = """
            UPDATE user_recipes 
            SET is_favorite = %(is_favorite)s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """
            
            self.db_service.execute_query(update_query, {
                "is_favorite": new_favorite,
                "recipe_id": recipe_id,
                "user_id": user_id
            })
            
            return {
                "success": True,
                "is_favorite": new_favorite,
                "message": f"Recipe {'added to' if new_favorite else 'removed from'} favorites"
            }
            
        except Exception as e:
            logger.error(f"Error toggling favorite: {str(e)}")
            raise
    
    async def delete_recipe(
        self,
        user_id: int,
        recipe_id: int
    ) -> Dict[str, Any]:
        """Delete a recipe from user's collection"""
        try:
            delete_query = """
            DELETE FROM user_recipes 
            WHERE id = %(recipe_id)s AND user_id = %(user_id)s
            """
            
            result = self.db_service.execute_query(delete_query, {
                "recipe_id": recipe_id,
                "user_id": user_id
            })
            
            if result and result[0].get('affected_rows', 0) > 0:
                return {
                    "success": True,
                    "message": "Recipe deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Recipe not found"
                }
                
        except Exception as e:
            logger.error(f"Error deleting recipe: {str(e)}")
            raise
    
    async def get_recipe_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's recipe statistics"""
        try:
            stats_query = """
            SELECT 
                COUNT(*) as total_recipes,
                COUNT(CASE WHEN is_favorite THEN 1 END) as favorite_recipes,
                COUNT(CASE WHEN source = 'chat' THEN 1 END) as ai_generated_recipes,
                COUNT(CASE WHEN source = 'spoonacular' THEN 1 END) as spoonacular_recipes,
                COUNT(CASE WHEN rating = 'thumbs_up' THEN 1 END) as liked_recipes,
                COUNT(CASE WHEN rating = 'thumbs_down' THEN 1 END) as disliked_recipes
            FROM user_recipes
            WHERE user_id = %(user_id)s
            """
            
            result = self.db_service.execute_query(stats_query, {"user_id": user_id})
            
            if result:
                return dict(result[0])
            else:
                return {
                    "total_recipes": 0,
                    "favorite_recipes": 0,
                    "ai_generated_recipes": 0,
                    "spoonacular_recipes": 0,
                    "liked_recipes": 0,
                    "disliked_recipes": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting recipe stats: {str(e)}")
            raise