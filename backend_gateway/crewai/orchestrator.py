"""
CrewAI Orchestrator

Main orchestration layer that manages the background/foreground pattern.
Handles cache warming, flow triggering, and API integration.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from .background_flows import BackgroundFlowOrchestrator, PantryFlowInput, PreferenceFlowInput
from .foreground_crew import ForegroundRecipeCrew, get_recipe_recommendations
from .cache_manager import ArtifactCacheManager
from .models import CrewOutput

logger = logging.getLogger(__name__)


class CrewAIOrchestrator:
    """
    Main orchestrator for CrewAI operations.
    
    Manages:
    - Background flow triggering
    - Cache warming strategies  
    - Foreground crew coordination
    - Performance monitoring
    """
    
    def __init__(self):
        self.cache_manager = ArtifactCacheManager()
        self.background_orchestrator = BackgroundFlowOrchestrator()
        self.foreground_crew = ForegroundRecipeCrew()
    
    async def handle_user_query(
        self, 
        user_message: str, 
        user_id: int,
        recipe_candidates: List[Dict[str, Any]] = None,
        context: Dict[str, Any] = None
    ) -> CrewOutput:
        """
        Main entry point for user recipe queries.
        
        Strategy:
        1. Check cache freshness
        2. Warm cache if needed (async)
        3. Use foreground crew for response
        4. Return streaming response
        """
        try:
            # Check if user has fresh cached data
            has_fresh_data = self.cache_manager.has_fresh_data(user_id)
            
            if not has_fresh_data:
                # Trigger background flows asynchronously (don't wait)
                asyncio.create_task(
                    self._warm_user_cache_async(user_id, "query_triggered")
                )
                logger.info(f"Triggered background cache warming for user {user_id}")
            
            # Always attempt foreground crew (handles cache miss gracefully)
            result = await get_recipe_recommendations(
                user_message=user_message,
                user_id=user_id,
                recipe_candidates=recipe_candidates,
                context=context
            )
            
            # Log performance metrics
            self._log_performance_metrics(result, has_fresh_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling user query: {e}")
            return CrewOutput(
                response_text="I'm having trouble right now. Please try again in a moment.",
                recipe_cards=[],
                processing_time_ms=100,
                agents_used=[],
                cache_hit=False,
                metadata={"error": str(e)}
            )
    
    async def handle_pantry_update(self, user_id: int, update_type: str = "crud"):
        """
        Handle pantry updates that should trigger background flows.
        
        Called by:
        - Pantry CRUD operations
        - Image scanning (new items added)
        - Recipe completion (ingredients consumed)
        """
        try:
            logger.info(f"Handling pantry update for user {user_id} - type: {update_type}")
            
            # Invalidate cached pantry data
            self.cache_manager.clear_user_cache(user_id)
            
            # Trigger pantry analysis flow immediately
            await self._warm_user_cache_async(user_id, f"pantry_{update_type}")
            
            logger.info(f"Completed pantry update handling for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling pantry update for user {user_id}: {e}")
    
    async def handle_preference_update(self, user_id: int, update_type: str = "rating"):
        """
        Handle preference updates that should trigger background flows.
        
        Called by:
        - Recipe ratings
        - Dietary restriction changes  
        - Cuisine preference updates
        """
        try:
            logger.info(f"Handling preference update for user {user_id} - type: {update_type}")
            
            # Invalidate cached preference data
            preference_key = f"preference_artifact:{user_id}"
            self.cache_manager.redis_client.delete(preference_key)
            
            # Trigger preference learning flow
            await self._warm_preference_cache_async(user_id, f"preference_{update_type}")
            
            logger.info(f"Completed preference update handling for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling preference update for user {user_id}: {e}")
    
    async def warm_cache_for_user(self, user_id: int, trigger_reason: str = "manual") -> Dict[str, bool]:
        """
        Manually warm cache for a user.
        
        Useful for:
        - App cold start
        - Admin operations
        - Scheduled maintenance
        """
        return await self._warm_user_cache_async(user_id, trigger_reason)
    
    async def batch_warm_cache(self, user_ids: List[int], trigger_reason: str = "scheduled") -> Dict[int, Dict[str, bool]]:
        """
        Warm cache for multiple users in batch.
        
        Used for:
        - Nightly batch processing
        - Pre-warming popular users
        - System maintenance
        """
        results = {}
        
        # Process users in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self._warm_user_cache_async(user_id, trigger_reason)
                for user_id in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for user_id, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to warm cache for user {user_id}: {result}")
                    results[user_id] = {"pantry_flow": False, "preference_flow": False}
                else:
                    results[user_id] = result
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        logger.info(f"Batch cache warming completed for {len(user_ids)} users")
        return results
    
    def get_cache_status(self, user_id: int) -> Dict[str, Any]:
        """Get detailed cache status for a user"""
        try:
            pantry_artifact = self.cache_manager.get_pantry_artifact(user_id)
            preference_artifact = self.cache_manager.get_preference_artifact(user_id)
            
            status = {
                "user_id": user_id,
                "has_fresh_data": bool(pantry_artifact and preference_artifact),
                "pantry_cache": {
                    "exists": bool(pantry_artifact),
                    "last_updated": pantry_artifact.last_updated.isoformat() if pantry_artifact else None,
                    "is_fresh": pantry_artifact.is_fresh() if pantry_artifact else False,
                    "ttl_seconds": pantry_artifact.ttl_seconds if pantry_artifact else None
                },
                "preference_cache": {
                    "exists": bool(preference_artifact),
                    "last_updated": preference_artifact.last_updated.isoformat() if preference_artifact else None,
                    "is_fresh": preference_artifact.is_fresh() if preference_artifact else False,
                    "ttl_seconds": preference_artifact.ttl_seconds if preference_artifact else None
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting cache status for user {user_id}: {e}")
            return {"error": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide performance and cache statistics"""
        try:
            cache_stats = self.cache_manager.get_cache_stats()
            
            # Add CrewAI-specific metrics
            stats = {
                "cache_stats": cache_stats,
                "system_health": {
                    "redis_healthy": self.cache_manager.health_check(),
                    "timestamp": datetime.now().isoformat()
                },
                "performance_targets": {
                    "foreground_latency_target_ms": 3000,
                    "background_flow_timeout_s": 30,
                    "cache_hit_rate_target": 0.8
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
    
    async def _warm_user_cache_async(self, user_id: int, trigger_reason: str) -> Dict[str, bool]:
        """Internal method to warm cache for a user"""
        return await self.background_orchestrator.warm_user_cache(user_id, trigger_reason)
    
    async def _warm_preference_cache_async(self, user_id: int, trigger_reason: str) -> bool:
        """Internal method to warm only preference cache"""
        try:
            from .background_flows import PreferenceLearningFlow
            
            preference_flow = PreferenceLearningFlow()
            result = preference_flow.kickoff(
                inputs=PreferenceFlowInput(user_id=user_id, trigger_reason=trigger_reason)
            )
            
            return "artifact_persisted" in str(result)
            
        except Exception as e:
            logger.error(f"Failed to warm preference cache for user {user_id}: {e}")
            return False
    
    def _log_performance_metrics(self, result: CrewOutput, had_fresh_cache: bool):
        """Log performance metrics for monitoring"""
        metrics = {
            "processing_time_ms": result.processing_time_ms,
            "meets_target": result.meets_performance_target(),
            "cache_hit": result.cache_hit,
            "had_fresh_cache": had_fresh_cache,
            "agents_used": len(result.agents_used),
            "timestamp": datetime.now().isoformat()
        }
        
        if result.processing_time_ms > 3000:
            logger.warning(f"Slow response detected: {metrics}")
        else:
            logger.info(f"Performance metrics: {metrics}")


# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> CrewAIOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CrewAIOrchestrator()
    return _orchestrator


# Convenience functions for API endpoints
async def handle_recipe_query(
    user_message: str,
    user_id: int,
    recipe_candidates: List[Dict[str, Any]] = None,
    context: Dict[str, Any] = None
) -> CrewOutput:
    """Convenience function for recipe queries"""
    orchestrator = get_orchestrator()
    return await orchestrator.handle_user_query(
        user_message=user_message,
        user_id=user_id,
        recipe_candidates=recipe_candidates,
        context=context
    )


async def handle_pantry_change(user_id: int, change_type: str = "update"):
    """Convenience function for pantry changes"""
    orchestrator = get_orchestrator()
    await orchestrator.handle_pantry_update(user_id, change_type)


async def handle_recipe_rating(user_id: int, recipe_id: int, rating: float):
    """Convenience function for recipe ratings"""
    orchestrator = get_orchestrator()
    await orchestrator.handle_preference_update(user_id, "rating")