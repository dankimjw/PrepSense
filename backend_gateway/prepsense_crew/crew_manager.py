"""CrewAI Workflow Manager

Centralized manager for all CrewAI workflows with FastAPI integration support.
Phase 2: Production-ready crew management with async support and error handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import time
from dataclasses import dataclass

from backend_gateway.crewai.crews.recipe_recommendation_crew import RecipeRecommendationCrew
from backend_gateway.crewai.crews.pantry_normalization_crew import PantryNormalizationCrew

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Available workflow types"""
    RECIPE_RECOMMENDATION = "recipe_recommendation"
    PANTRY_NORMALIZATION = "pantry_normalization"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowResult:
    """Standardized workflow result container"""
    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    result_data: Dict[str, Any]
    processing_time_ms: int
    error_message: Optional[str] = None
    created_at: float = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class CrewAIManager:
    """Centralized manager for all CrewAI workflows with production-ready features"""
    
    def __init__(self):
        """Initialize crew manager with workflow tracking"""
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.workflow_history: List[WorkflowResult] = []
        self._next_workflow_id = 1
        
        # Initialize crew instances (cached for performance)
        self._recipe_crew: Optional[RecipeRecommendationCrew] = None
        self._pantry_crew: Optional[PantryNormalizationCrew] = None
    
    @property
    def recipe_crew(self) -> RecipeRecommendationCrew:
        """Lazy-loaded recipe recommendation crew"""
        if self._recipe_crew is None:
            self._recipe_crew = RecipeRecommendationCrew()
        return self._recipe_crew
    
    @property
    def pantry_crew(self) -> PantryNormalizationCrew:
        """Lazy-loaded pantry normalization crew"""
        if self._pantry_crew is None:
            self._pantry_crew = PantryNormalizationCrew()
        return self._pantry_crew
    
    def generate_workflow_id(self) -> str:
        """Generate unique workflow ID"""
        workflow_id = f"wf_{self._next_workflow_id:06d}"
        self._next_workflow_id += 1
        return workflow_id
    
    async def execute_recipe_recommendation(
        self, 
        user_id: str, 
        user_message: str,
        include_images: bool = True,
        max_recipes: int = 5
    ) -> WorkflowResult:
        """Execute recipe recommendation workflow"""
        
        workflow_id = self.generate_workflow_id()
        
        # Create workflow tracking entry
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.RECIPE_RECOMMENDATION,
            status=WorkflowStatus.PENDING,
            result_data={},
            processing_time_ms=0
        )
        
        self.active_workflows[workflow_id] = workflow_result
        
        try:
            logger.info(f"Starting recipe recommendation workflow {workflow_id} for user {user_id}")
            
            # Update status to running
            workflow_result.status = WorkflowStatus.RUNNING
            
            # Prepare inputs
            inputs = {
                "user_id": user_id,
                "user_message": user_message,
                "include_images": include_images,
                "max_recipes": max_recipes,
                "workflow_id": workflow_id
            }
            
            # Execute crew workflow
            start_time = time.time()
            crew_result = await self.recipe_crew.kickoff(inputs)
            processing_time = int((time.time() - start_time) * 1000)
            
            # Update workflow result
            workflow_result.status = WorkflowStatus.COMPLETED
            workflow_result.result_data = crew_result
            workflow_result.processing_time_ms = processing_time
            workflow_result.completed_at = time.time()
            
            logger.info(f"Recipe recommendation workflow {workflow_id} completed in {processing_time}ms")
            
        except Exception as e:
            logger.error(f"Recipe recommendation workflow {workflow_id} failed: {e}")
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.error_message = str(e)
            workflow_result.result_data = {
                "status": "error",
                "error": str(e),
                "recipes": [],
                "processing_time_ms": 0
            }
            workflow_result.completed_at = time.time()
        
        finally:
            # Move to history and clean up active tracking
            self.workflow_history.append(workflow_result)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
        
        return workflow_result
    
    async def execute_pantry_normalization(
        self,
        user_id: str,
        raw_pantry_items: List[Dict[str, Any]],
        processing_mode: str = "full"
    ) -> WorkflowResult:
        """Execute pantry normalization workflow"""
        
        workflow_id = self.generate_workflow_id()
        
        # Create workflow tracking entry
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.PANTRY_NORMALIZATION,
            status=WorkflowStatus.PENDING,
            result_data={},
            processing_time_ms=0
        )
        
        self.active_workflows[workflow_id] = workflow_result
        
        try:
            logger.info(f"Starting pantry normalization workflow {workflow_id} for user {user_id}")
            
            # Update status to running
            workflow_result.status = WorkflowStatus.RUNNING
            
            # Prepare inputs
            inputs = {
                "user_id": user_id,
                "raw_pantry_items": raw_pantry_items,
                "processing_mode": processing_mode,
                "workflow_id": workflow_id
            }
            
            # Execute crew workflow
            start_time = time.time()
            crew_result = await self.pantry_crew.kickoff(inputs)
            processing_time = int((time.time() - start_time) * 1000)
            
            # Update workflow result
            workflow_result.status = WorkflowStatus.COMPLETED
            workflow_result.result_data = crew_result
            workflow_result.processing_time_ms = processing_time
            workflow_result.completed_at = time.time()
            
            logger.info(f"Pantry normalization workflow {workflow_id} completed in {processing_time}ms")
            
        except Exception as e:
            logger.error(f"Pantry normalization workflow {workflow_id} failed: {e}")
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.error_message = str(e)
            workflow_result.result_data = {
                "status": "error",
                "error": str(e),
                "normalized_items": [],
                "processing_time_ms": 0
            }
            workflow_result.completed_at = time.time()
        
        finally:
            # Move to history and clean up active tracking
            self.workflow_history.append(workflow_result)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
        
        return workflow_result
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get status of a specific workflow"""
        # Check active workflows first
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Check history
        for result in self.workflow_history:
            if result.workflow_id == workflow_id:
                return result
        
        return None
    
    def get_active_workflows(self) -> List[WorkflowResult]:
        """Get all currently active workflows"""
        return list(self.active_workflows.values())
    
    def get_workflow_history(self, limit: int = 50) -> List[WorkflowResult]:
        """Get recent workflow history"""
        return sorted(
            self.workflow_history[-limit:], 
            key=lambda x: x.created_at, 
            reverse=True
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        total_workflows = len(self.workflow_history)
        
        if total_workflows == 0:
            return {
                "total_workflows": 0,
                "active_workflows": len(self.active_workflows),
                "success_rate": 0.0,
                "avg_processing_time_ms": 0,
                "workflow_type_counts": {}
            }
        
        successful = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.FAILED)
        
        # Calculate average processing time for completed workflows
        completed_workflows = [w for w in self.workflow_history if w.status == WorkflowStatus.COMPLETED]
        avg_time = (
            sum(w.processing_time_ms for w in completed_workflows) / len(completed_workflows)
            if completed_workflows else 0
        )
        
        # Count workflow types
        type_counts = {}
        for workflow in self.workflow_history:
            workflow_type = workflow.workflow_type.value
            type_counts[workflow_type] = type_counts.get(workflow_type, 0) + 1
        
        return {
            "total_workflows": total_workflows,
            "active_workflows": len(self.active_workflows),
            "successful_workflows": successful,
            "failed_workflows": failed,
            "success_rate": (successful / total_workflows) * 100 if total_workflows > 0 else 0,
            "avg_processing_time_ms": int(avg_time),
            "workflow_type_counts": type_counts
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all crew components"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
            "active_workflows": len(self.active_workflows),
            "total_processed": len(self.workflow_history)
        }
        
        try:
            # Check recipe crew initialization
            recipe_crew_status = "healthy" if self._recipe_crew is not None else "uninitialized"
            health_status["components"]["recipe_crew"] = {
                "status": recipe_crew_status,
                "agents_count": 4  # recipe_search, nutri_check, user_preferences, judge_thyme
            }
            
            # Check pantry crew initialization
            pantry_crew_status = "healthy" if self._pantry_crew is not None else "uninitialized"
            health_status["components"]["pantry_crew"] = {
                "status": pantry_crew_status,
                "agents_count": 3  # food_categorizer, unit_canon, fresh_filter
            }
            
            # Check if any workflows are stuck (running for more than 5 minutes)
            current_time = time.time()
            stuck_workflows = []
            for workflow_id, workflow in self.active_workflows.items():
                if workflow.status == WorkflowStatus.RUNNING:
                    if current_time - workflow.created_at > 300:  # 5 minutes
                        stuck_workflows.append(workflow_id)
            
            if stuck_workflows:
                health_status["status"] = "degraded"
                health_status["warnings"] = [f"Workflows may be stuck: {stuck_workflows}"]
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    def cleanup_old_history(self, max_history: int = 1000):
        """Clean up old workflow history to prevent memory issues"""
        if len(self.workflow_history) > max_history:
            # Keep the most recent workflows
            self.workflow_history = sorted(
                self.workflow_history,
                key=lambda x: x.created_at,
                reverse=True
            )[:max_history]
            logger.info(f"Cleaned up workflow history, keeping {max_history} most recent entries")


# Global manager instance for FastAPI integration
crew_manager = CrewAIManager()


# FastAPI Integration Functions

async def process_recipe_request(
    user_id: str,
    user_message: str,
    include_images: bool = True,
    max_recipes: int = 5
) -> Dict[str, Any]:
    """FastAPI-compatible recipe recommendation function"""
    result = await crew_manager.execute_recipe_recommendation(
        user_id=user_id,
        user_message=user_message,
        include_images=include_images,
        max_recipes=max_recipes
    )
    
    # Return the result data with additional metadata
    return {
        **result.result_data,
        "workflow_id": result.workflow_id,
        "workflow_status": result.status.value,
        "processing_time_ms": result.processing_time_ms
    }


async def process_pantry_normalization(
    user_id: str,
    raw_pantry_items: List[Dict[str, Any]],
    processing_mode: str = "full"
) -> Dict[str, Any]:
    """FastAPI-compatible pantry normalization function"""
    result = await crew_manager.execute_pantry_normalization(
        user_id=user_id,
        raw_pantry_items=raw_pantry_items,
        processing_mode=processing_mode
    )
    
    # Return the result data with additional metadata
    return {
        **result.result_data,
        "workflow_id": result.workflow_id,
        "workflow_status": result.status.value,
        "processing_time_ms": result.processing_time_ms
    }


async def get_crewai_health() -> Dict[str, Any]:
    """FastAPI-compatible health check function"""
    return await crew_manager.health_check()


def get_crewai_statistics() -> Dict[str, Any]:
    """FastAPI-compatible statistics function"""
    return crew_manager.get_statistics()


# Background task functions for FastAPI BackgroundTasks

async def background_pantry_normalization(
    user_id: str,
    raw_pantry_items: List[Dict[str, Any]],
    processing_mode: str = "full"
) -> str:
    """Background task for pantry normalization - returns workflow ID"""
    result = await crew_manager.execute_pantry_normalization(
        user_id=user_id,
        raw_pantry_items=raw_pantry_items,
        processing_mode=processing_mode
    )
    
    logger.info(f"Background pantry normalization completed: {result.workflow_id}")
    return result.workflow_id