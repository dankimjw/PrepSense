"""
API Router for AI-powered recipe generation using CrewAI
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend_gateway.routers.users import get_current_user
from backend_gateway.services.crew_ai_service import CrewAIService

router = APIRouter(prefix="/api/v1/ai-recipes", tags=["AI Recipes"])

# Initialize CrewAI service
crew_ai_service = None


def get_crew_ai_service():
    """Get or create CrewAI service instance"""
    global crew_ai_service
    if crew_ai_service is None:
        crew_ai_service = CrewAIService()
    return crew_ai_service


@router.post("/generate")
async def generate_ai_recipes(
    max_recipes: Optional[int] = 3,
    current_user: dict = Depends(get_current_user),
    service: CrewAIService = Depends(get_crew_ai_service),
) -> dict[str, Any]:
    """
    Generate AI-powered recipe suggestions based on user's pantry items.

    This endpoint uses CrewAI with multiple specialized agents to:
    1. Scan user's pantry for available ingredients
    2. Filter out expired items
    3. Search for suitable recipes
    4. Evaluate nutritional content
    5. Apply dietary restrictions
    6. Score and rank recipes
    7. Format results

    Args:
        max_recipes: Maximum number of recipes to return (default: 3)
        current_user: Authenticated user

    Returns:
        Generated recipe suggestions with ingredients and instructions
    """
    try:
        user_id = current_user["user_id"]

        # Generate recipes using CrewAI
        result = await asyncio.to_thread(
            service.generate_recipes, user_id=user_id, max_recipes=max_recipes
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate recipes: {result.get('error', 'Unknown error')}",
            )

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "generated_at": result["generated_at"],
                "recipes": result["recipes"],
                "recipe_count": len(result["recipes"]),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating AI recipes: {str(e)}") from e


@router.get("/pantry-summary")
async def get_pantry_summary(
    current_user: dict = Depends(get_current_user),
    service: CrewAIService = Depends(get_crew_ai_service),
) -> dict[str, Any]:
    """
    Get a summary of user's pantry for recipe generation.

    Returns:
        - Total items count
        - Fresh (non-expired) items count
        - User dietary preferences
        - Items grouped by category
    """
    try:
        user_id = current_user["user_id"]

        # Get pantry summary
        summary = await asyncio.to_thread(service.get_pantry_summary, user_id=user_id)

        if not summary["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get pantry summary: {summary.get('error', 'Unknown error')}",
            )

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "total_items": summary["total_items"],
                "fresh_items": summary["fresh_items"],
                "preferences": summary["preferences"],
                "items_by_category": summary["items_by_category"],
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting pantry summary: {str(e)}"
        ) from e


@router.post("/generate-async")
async def generate_ai_recipes_async(
    background_tasks: BackgroundTasks,
    max_recipes: Optional[int] = 3,
    webhook_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: CrewAIService = Depends(get_crew_ai_service),
) -> dict[str, Any]:
    """
    Generate AI recipes asynchronously (for long-running operations).

    Args:
        max_recipes: Maximum number of recipes to return
        webhook_url: Optional URL to POST results when complete
        current_user: Authenticated user

    Returns:
        Task ID for tracking progress
    """
    try:
        user_id = current_user["user_id"]
        task_id = f"ai_recipe_{user_id}_{datetime.now().timestamp()}"

        # Add background task
        background_tasks.add_task(
            _generate_recipes_background,
            service=service,
            user_id=user_id,
            max_recipes=max_recipes,
            task_id=task_id,
            webhook_url=webhook_url,
        )

        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "processing",
                "message": "Recipe generation started. Check back for results.",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting recipe generation: {str(e)}"
        ) from e


async def _generate_recipes_background(
    service: CrewAIService,
    user_id: int,
    max_recipes: int,
    task_id: str,
    webhook_url: Optional[str] = None,
):
    """Background task for recipe generation"""
    try:
        # Generate recipes
        result = await asyncio.to_thread(
            service.generate_recipes, user_id=user_id, max_recipes=max_recipes
        )

        # If webhook URL provided, send results
        if webhook_url and result["success"]:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(
                    webhook_url, json={"task_id": task_id, "status": "completed", "result": result}
                )

    except Exception as e:
        print(f"Error in background recipe generation: {str(e)}")
        # If webhook URL provided, send error
        if webhook_url:
            import httpx

            async with httpx.AsyncClient() as client:
                await client.post(
                    webhook_url, json={"task_id": task_id, "status": "failed", "error": str(e)}
                )


@router.get("/health")
async def ai_recipes_health() -> dict[str, Any]:
    """Check health of AI recipe generation service"""
    try:
        service = get_crew_ai_service()

        # Check if tools are initialized
        tools_status = {
            "pantry_tool": service.pantry_tool is not None,
            "ingredient_filter_tool": service.ingredient_filter_tool is not None,
            "user_restriction_tool": service.user_restriction_tool is not None,
            "search_tool": service.search_tool is not None,
            "scrape_tool": service.scrape_tool is not None,
        }

        # Check if agents are initialized
        agents_status = {
            "pantry_scan_agent": hasattr(service, "pantry_scan_agent"),
            "ingredient_filter_agent": hasattr(service, "ingredient_filter_agent"),
            "recipe_search_agent": hasattr(service, "recipe_search_agent"),
            "nutritional_agent": hasattr(service, "nutritional_agent"),
            "user_preferences_agent": hasattr(service, "user_preferences_agent"),
            "recipe_scoring_agent": hasattr(service, "recipe_scoring_agent"),
            "response_formatting_agent": hasattr(service, "response_formatting_agent"),
        }

        all_tools_ok = all(tools_status.values())
        all_agents_ok = all(agents_status.values())

        return {
            "status": "healthy" if (all_tools_ok and all_agents_ok) else "degraded",
            "service": "AI Recipe Generation",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "tools": tools_status,
                "agents": agents_status,
                "external_apis": {
                    "serper_configured": service.search_tool is not None,
                    "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
                },
            },
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "AI Recipe Generation",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }
