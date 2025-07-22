"""
Background Task Service for PrepSense
Handles event-driven pre-computation and cache warming
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks
import schedule
import time
from threading import Thread

from .background_flows import BackgroundFlowManager, CacheManager
from backend_gateway.config.database import get_database_service

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """Service for managing background tasks and cache warming"""
    
    def __init__(self):
        self.flow_manager = BackgroundFlowManager()
        self.cache_manager = CacheManager(self.flow_manager)
        self.db_service = get_database_service()
        self.scheduler_thread = None
        self.is_running = False
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Schedule periodic cache warming
        schedule.every(6).hours.do(self._warm_cache_for_active_users)
        schedule.every(1).days.do(self._cleanup_old_cache)
        schedule.every().day.at("06:00").do(self._morning_cache_refresh)
        
        # Start scheduler thread
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Background task scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Background task scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    async def on_pantry_updated(self, user_id: int, trigger_reason: str = "pantry_update"):
        """Handle pantry update event - trigger cache refresh"""
        try:
            logger.info(f"Pantry updated for user {user_id}, triggering cache refresh")
            
            # Refresh inventory and expiry data
            await self.flow_manager.run_pantry_scan_flow(user_id, self.db_service)
            await self.flow_manager.run_expiry_auditor_flow(user_id)
            
            # Warm up recipe recommendations in background
            asyncio.create_task(self._warm_recipe_cache(user_id, trigger_reason))
            
        except Exception as e:
            logger.error(f"Error handling pantry update for user {user_id}: {str(e)}")
    
    async def on_preferences_updated(self, user_id: int, trigger_reason: str = "preferences_update"):
        """Handle preferences update event"""
        try:
            logger.info(f"Preferences updated for user {user_id}, triggering preference cache refresh")
            
            # Refresh preference vector
            await self.flow_manager.run_preference_vector_builder(user_id, self.db_service)
            
            # Warm up recipe recommendations with new preferences
            asyncio.create_task(self._warm_recipe_cache(user_id, trigger_reason))
            
        except Exception as e:
            logger.error(f"Error handling preferences update for user {user_id}: {str(e)}")
    
    async def on_recipe_interaction(self, user_id: int, recipe_id: str, action: str, 
                                   metadata: Optional[Dict[str, Any]] = None):
        """Handle recipe interaction event"""
        try:
            logger.info(f"Recipe interaction: user {user_id}, recipe {recipe_id}, action {action}")
            
            # Track interaction for preference learning
            # TODO: Re-implement preference learning
            # Previously used lean_crew_ai_service which has been removed
            logger.info("Preference learning temporarily disabled - lean_crew_ai_service removed")
            
            # If it's a significant interaction, refresh preferences
            if action in ['rated', 'cooked', 'saved', 'dismissed']:
                await self.on_preferences_updated(user_id, f"interaction_{action}")
            
        except Exception as e:
            logger.error(f"Error handling recipe interaction: {str(e)}")
    
    async def warm_cache_for_user(self, user_id: int, reason: str = "manual"):
        """Warm cache for a specific user"""
        try:
            logger.info(f"Warming cache for user {user_id} (reason: {reason})")
            
            # Ensure fresh cache
            await self.cache_manager.ensure_fresh_cache(user_id, self.db_service, force_refresh=True)
            
            # Pre-compute recipe recommendations
            await self._warm_recipe_cache(user_id, reason)
            
            logger.info(f"Cache warming completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error warming cache for user {user_id}: {str(e)}")
    
    async def _warm_recipe_cache(self, user_id: int, reason: str):
        """Pre-compute recipe recommendations for faster response"""
        try:
            # TODO: Re-implement cache warming
            # Previously used lean_crew_ai_service which has been removed
            logger.info("Recipe cache warming temporarily disabled - lean_crew_ai_service removed")
            return
                        user_id, query, num_recommendations=5
                    ):
                        if 'error' not in result:
                            recommendations.append(result['recommendation'])
                    
                    logger.debug(f"Pre-computed {len(recommendations)} recommendations for query: {query}")
                    
                except Exception as e:
                    logger.warning(f"Error pre-computing query '{query}': {str(e)}")
            
        except Exception as e:
            logger.error(f"Error warming recipe cache: {str(e)}")
    
    def _warm_cache_for_active_users(self):
        """Periodic task to warm cache for active users"""
        try:
            logger.info("Running periodic cache warming for active users")
            
            # Get active users (users who have interacted in last 7 days)
            query = """
                SELECT DISTINCT user_id 
                FROM user_recipe_interactions 
                WHERE timestamp >= %s
                ORDER BY timestamp DESC
                LIMIT 50
            """
            
            since_date = datetime.now() - timedelta(days=7)
            active_users = self.db_service.execute_query(query, (since_date,))
            
            # Warm cache for each active user
            for user_data in active_users:
                user_id = user_data['user_id']
                asyncio.create_task(self.warm_cache_for_user(user_id, "periodic"))
            
            logger.info(f"Cache warming queued for {len(active_users)} active users")
            
        except Exception as e:
            logger.error(f"Error in periodic cache warming: {str(e)}")
    
    def _cleanup_old_cache(self):
        """Clean up old cache files"""
        try:
            logger.info("Running cache cleanup")
            
            # Check if cache files are older than 7 days
            max_age = timedelta(days=7)
            current_time = datetime.now()
            
            for cache_file in [
                self.flow_manager.inventory_cache,
                self.flow_manager.expiry_cache,
                self.flow_manager.preference_cache
            ]:
                if cache_file.exists():
                    modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if current_time - modified_time > max_age:
                        cache_file.unlink()
                        logger.info(f"Deleted old cache file: {cache_file.name}")
            
        except Exception as e:
            logger.error(f"Error in cache cleanup: {str(e)}")
    
    def _morning_cache_refresh(self):
        """Morning cache refresh for all users"""
        try:
            logger.info("Running morning cache refresh")
            
            # Get all users who have pantry items
            query = """
                SELECT DISTINCT user_id 
                FROM pantry_items 
                WHERE quantity > 0
            """
            
            users = self.db_service.execute_query(query)
            
            # Refresh cache for each user
            for user_data in users:
                user_id = user_data['user_id']
                asyncio.create_task(self.warm_cache_for_user(user_id, "morning_refresh"))
            
            logger.info(f"Morning cache refresh queued for {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error in morning cache refresh: {str(e)}")


# Singleton instance
_background_task_service = None

def get_background_task_service() -> BackgroundTaskService:
    """Get singleton instance of BackgroundTaskService"""
    global _background_task_service
    if _background_task_service is None:
        _background_task_service = BackgroundTaskService()
    return _background_task_service


# FastAPI lifespan events
@asynccontextmanager
async def lifespan(app):
    """Handle startup and shutdown events"""
    # Startup
    task_service = get_background_task_service()
    task_service.start_scheduler()
    
    # Warm cache for demo user on startup
    try:
        await task_service.warm_cache_for_user(111, "startup")
    except Exception as e:
        logger.warning(f"Failed to warm cache on startup: {str(e)}")
    
    yield
    
    # Shutdown
    task_service.stop_scheduler()


# Event handlers for other services to use
async def handle_pantry_update(user_id: int, trigger_reason: str = "pantry_update"):
    """Handle pantry update event"""
    service = get_background_task_service()
    await service.on_pantry_updated(user_id, trigger_reason)


async def handle_preferences_update(user_id: int, trigger_reason: str = "preferences_update"):
    """Handle preferences update event"""
    service = get_background_task_service()
    await service.on_preferences_updated(user_id, trigger_reason)


async def handle_recipe_interaction(user_id: int, recipe_id: str, action: str, 
                                   metadata: Optional[Dict[str, Any]] = None):
    """Handle recipe interaction event"""
    service = get_background_task_service()
    await service.on_recipe_interaction(user_id, recipe_id, action, metadata)


async def warm_user_cache(user_id: int, reason: str = "manual"):
    """Warm cache for a specific user"""
    service = get_background_task_service()
    await service.warm_cache_for_user(user_id, reason)