"""Database tool for CrewAI agents to interact with the database."""

from typing import Dict, List, Any, Optional
import logging
from pydantic import BaseModel, Field

from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)


class DatabaseTool:
    """Tool for database operations used by CrewAI agents."""
    
    name: str = "database_tool"
    description: str = (
        "A tool for querying the database. Can retrieve pantry items, "
        "user preferences, saved recipes, and other data needed for recipe recommendations."
    )
    
    def __init__(self):
        self.db_service = get_database_service()
    
    def _run(self, query_type: str, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Execute a database query based on the query type.
        
        Args:
            query_type: The type of query to execute
            user_id: The user ID for the query
            **kwargs: Additional parameters for the query
            
        Returns:
            Dict containing the query results
        """
        try:
            if query_type == "pantry_items":
                return self._get_pantry_items(user_id)
            elif query_type == "user_preferences":
                return self._get_user_preferences(user_id)
            elif query_type == "saved_recipes":
                return self._get_saved_recipes(user_id, **kwargs)
            elif query_type == "custom_query":
                return self._execute_custom_query(kwargs.get("query", ""), kwargs.get("params", {}))
            else:
                return {"error": f"Unknown query type: {query_type}"}
                
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            return {"error": f"Database query failed: {str(e)}"}
    
    def _get_pantry_items(self, user_id: int) -> Dict[str, Any]:
        """Get pantry items for a user."""
        query = """
            SELECT *
            FROM user_pantry_full
            WHERE user_id = %(user_id)s
            ORDER BY expiration_date ASC
        """
        params = {"user_id": user_id}
        
        results = self.db_service.execute_query(query, params)
        
        return {
            "query_type": "pantry_items",
            "user_id": user_id,
            "count": len(results),
            "items": results
        }
    
    def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences."""
        query = """
            SELECT *
            FROM user_preferences
            WHERE user_id = %(user_id)s
            LIMIT 1
        """
        params = {"user_id": user_id}
        
        results = self.db_service.execute_query(query, params)
        
        if results and results[0].get('preferences'):
            prefs_data = results[0]['preferences']
            preferences = {
                'dietary_preference': prefs_data.get('dietary_restrictions', []),
                'allergens': prefs_data.get('allergens', []),
                'cuisine_preference': prefs_data.get('cuisine_preferences', [])
            }
        else:
            preferences = {
                'dietary_preference': [],
                'allergens': [],
                'cuisine_preference': []
            }
        
        return {
            "query_type": "user_preferences",
            "user_id": user_id,
            "preferences": preferences
        }
    
    def _get_saved_recipes(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Get saved recipes for a user."""
        limit = kwargs.get('limit', 10)
        
        query = """
            SELECT *
            FROM user_saved_recipes
            WHERE user_id = %(user_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """
        params = {"user_id": user_id, "limit": limit}
        
        results = self.db_service.execute_query(query, params)
        
        return {
            "query_type": "saved_recipes",
            "user_id": user_id,
            "count": len(results),
            "recipes": results
        }
    
    def _execute_custom_query(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom SQL query."""
        results = self.db_service.execute_query(query, params)
        
        return {
            "query_type": "custom_query",
            "count": len(results),
            "results": results
        }


# Helper function to create the tool
def create_database_tool() -> DatabaseTool:
    """Create and return a DatabaseTool instance."""
    return DatabaseTool()