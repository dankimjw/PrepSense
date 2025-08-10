"""
Caching service for AI-generated recipes to reduce API calls and improve performance.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import text

from backend_gateway.services.postgres_service import PostgresService


class AIRecipeCacheService:
    """Service for caching AI-generated recipe suggestions"""

    def __init__(self):
        self.db_service = PostgresService()
        self.cache_duration = timedelta(days=7)  # Cache recipes for 7 days
        self._ensure_cache_table()

    def _ensure_cache_table(self):
        """Ensure the AI recipe cache table exists"""
        with self.db_service.get_session() as session:
            # Create table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS ai_recipe_cache (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                cache_key VARCHAR(64) NOT NULL,
                pantry_snapshot JSONB NOT NULL,
                preferences_snapshot JSONB NOT NULL,
                recipes JSONB NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(user_id, cache_key)
            );

            CREATE INDEX IF NOT EXISTS idx_ai_recipe_cache_user_id ON ai_recipe_cache(user_id);
            CREATE INDEX IF NOT EXISTS idx_ai_recipe_cache_expires_at ON ai_recipe_cache(expires_at);
            """
            session.execute(text(create_table_sql))
            session.commit()

    def _generate_cache_key(
        self, user_id: int, pantry_items: list[dict], preferences: dict, max_recipes: int
    ) -> str:
        """Generate a unique cache key based on user's pantry and preferences"""
        # Sort items for consistent hashing
        sorted_items = sorted(pantry_items, key=lambda x: x.get("pantry_item_id", 0))

        # Create a string representation of the cache inputs
        cache_data = {
            "user_id": user_id,
            "items": [
                (item["product_name"], item["available_quantity"], item["unit"])
                for item in sorted_items
            ],
            "preferences": preferences,
            "max_recipes": max_recipes,
        }

        # Generate hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def get_cached_recipes(
        self, user_id: int, pantry_items: list[dict], preferences: dict, max_recipes: int
    ) -> Optional[dict[str, Any]]:
        """Retrieve cached recipes if available and not expired"""
        cache_key = self._generate_cache_key(user_id, pantry_items, preferences, max_recipes)

        with self.db_service.get_session() as session:
            query = text(
                """
                SELECT
                    recipes,
                    metadata,
                    created_at,
                    expires_at
                FROM ai_recipe_cache
                WHERE user_id = :user_id
                    AND cache_key = :cache_key
                    AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
                LIMIT 1
            """
            )

            result = session.execute(query, {"user_id": user_id, "cache_key": cache_key}).fetchone()

            if result:
                return {
                    "success": True,
                    "cached": True,
                    "user_id": user_id,
                    "recipes": result.recipes,
                    "metadata": result.metadata,
                    "cached_at": result.created_at.isoformat(),
                    "expires_at": result.expires_at.isoformat(),
                }

        return None

    def cache_recipes(
        self,
        user_id: int,
        pantry_items: list[dict],
        preferences: dict,
        recipes: list[dict],
        max_recipes: int,
        metadata: Optional[dict] = None,
    ):
        """Cache AI-generated recipes"""
        cache_key = self._generate_cache_key(user_id, pantry_items, preferences, max_recipes)
        expires_at = datetime.now() + self.cache_duration

        with self.db_service.get_session() as session:
            # Delete any existing cache for this key
            delete_query = text(
                """
                DELETE FROM ai_recipe_cache
                WHERE user_id = :user_id AND cache_key = :cache_key
            """
            )
            session.execute(delete_query, {"user_id": user_id, "cache_key": cache_key})

            # Insert new cache entry
            insert_query = text(
                """
                INSERT INTO ai_recipe_cache
                (user_id, cache_key, pantry_snapshot, preferences_snapshot,
                 recipes, metadata, expires_at)
                VALUES
                (:user_id, :cache_key, :pantry_snapshot, :preferences_snapshot,
                 :recipes, :metadata, :expires_at)
            """
            )

            session.execute(
                insert_query,
                {
                    "user_id": user_id,
                    "cache_key": cache_key,
                    "pantry_snapshot": json.dumps(pantry_items),
                    "preferences_snapshot": json.dumps(preferences),
                    "recipes": json.dumps(recipes),
                    "metadata": json.dumps(metadata or {}),
                    "expires_at": expires_at,
                },
            )

            session.commit()

    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cached recipes for a user (e.g., when pantry changes)"""
        with self.db_service.get_session() as session:
            query = text(
                """
                UPDATE ai_recipe_cache
                SET expires_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id AND expires_at > CURRENT_TIMESTAMP
            """
            )

            session.execute(query, {"user_id": user_id})
            session.commit()

    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        with self.db_service.get_session() as session:
            query = text(
                """
                DELETE FROM ai_recipe_cache
                WHERE expires_at < CURRENT_TIMESTAMP
            """
            )

            result = session.execute(query)
            session.commit()

            return result.rowcount

    def get_cache_stats(self, user_id: Optional[int] = None) -> dict[str, Any]:
        """Get cache statistics"""
        with self.db_service.get_session() as session:
            if user_id:
                stats_query = text(
                    """
                    SELECT
                        COUNT(*) as total_entries,
                        COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_entries,
                        COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
                        MIN(created_at) as oldest_entry,
                        MAX(created_at) as newest_entry
                    FROM ai_recipe_cache
                    WHERE user_id = :user_id
                """
                )
                result = session.execute(stats_query, {"user_id": user_id}).fetchone()
            else:
                stats_query = text(
                    """
                    SELECT
                        COUNT(*) as total_entries,
                        COUNT(CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 1 END) as active_entries,
                        COUNT(CASE WHEN expires_at <= CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
                        COUNT(DISTINCT user_id) as unique_users,
                        MIN(created_at) as oldest_entry,
                        MAX(created_at) as newest_entry
                    FROM ai_recipe_cache
                """
                )
                result = session.execute(stats_query).fetchone()

            return {
                "total_entries": result.total_entries,
                "active_entries": result.active_entries,
                "expired_entries": result.expired_entries,
                "unique_users": getattr(result, "unique_users", None),
                "oldest_entry": result.oldest_entry.isoformat() if result.oldest_entry else None,
                "newest_entry": result.newest_entry.isoformat() if result.newest_entry else None,
            }
