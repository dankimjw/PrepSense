"""
Streaming Chat Router for PrepSense
Provides fast, streaming responses for recipe recommendations
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend_gateway.config.database import get_database_service

# from backend_gateway.services.lean_crew_ai_service import get_lean_crew_service  # Service removed
from backend_gateway.services.background_flows import BackgroundFlowManager, CacheManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat-streaming"])


class ChatRequest(BaseModel):
    message: str
    user_id: int = 111  # Default user for demo
    context: Dict[str, Any] = {}


class ChatStreamingService:
    """Service for handling streaming chat responses"""

    def __init__(self, db_service):
        self.db_service = db_service
        self.lean_crew_service = get_lean_crew_service(db_service)
        self.background_flows = BackgroundFlowManager()
        self.cache_manager = CacheManager(self.background_flows)

    async def process_message_stream(
        self, message: str, user_id: int, context: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Process chat message and stream response"""
        try:
            # Determine if this is a recipe request
            is_recipe_request = self._is_recipe_request(message)

            if is_recipe_request:
                # Stream recipe recommendations
                async for chunk in self._stream_recipe_recommendations(message, user_id, context):
                    yield f"data: {json.dumps(chunk)}\n\n"
            else:
                # Stream general chat response
                async for chunk in self._stream_general_response(message, user_id, context):
                    yield f"data: {json.dumps(chunk)}\n\n"

            # End stream
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Error in chat stream: {str(e)}")
            error_chunk = {
                "type": "error",
                "content": f"Sorry, I encountered an error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"

    def _is_recipe_request(self, message: str) -> bool:
        """Determine if message is asking for recipe recommendations"""
        recipe_keywords = [
            "recipe",
            "cook",
            "make",
            "dinner",
            "lunch",
            "breakfast",
            "meal",
            "ingredient",
            "food",
            "eat",
            "prepare",
            "dish",
            "kitchen",
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in recipe_keywords)

    async def _stream_recipe_recommendations(
        self, message: str, user_id: int, context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream recipe recommendations"""

        # Send initial response
        yield {
            "type": "message_start",
            "content": "🍳 Let me find some great recipe ideas for you...",
            "timestamp": datetime.now().isoformat(),
        }

        # Trigger cache refresh in background if needed
        cache_refresh_task = asyncio.create_task(
            self.cache_manager.ensure_fresh_cache(user_id, self.db_service)
        )

        try:
            # Get streaming recommendations
            recommendation_count = 0
            async for result in self.lean_crew_service.get_recipe_recommendations(
                user_id, message, num_recommendations=3
            ):

                if "error" in result:
                    yield {
                        "type": "error",
                        "content": f'Error getting recommendations: {result["error"]}',
                        "timestamp": datetime.now().isoformat(),
                    }
                    continue

                recommendation = result["recommendation"]
                recommendation_count += 1

                # Stream individual recommendation
                yield {
                    "type": "recipe_recommendation",
                    "content": self._format_recipe_recommendation(recommendation),
                    "recipe_data": recommendation,
                    "index": recommendation_count,
                    "total_found": result.get("total_found", 0),
                    "timing": result.get("timing", {}),
                    "timestamp": datetime.now().isoformat(),
                }

                # Add a small delay to demonstrate streaming
                await asyncio.sleep(0.1)

            # Send completion message
            if recommendation_count > 0:
                yield {
                    "type": "message_complete",
                    "content": f"Found {recommendation_count} great recipes for you! Tap any recipe to see details.",
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                yield {
                    "type": "message_complete",
                    "content": "I couldn't find any recipes that match your pantry right now. Try adding more ingredients!",
                    "timestamp": datetime.now().isoformat(),
                }

        finally:
            # Ensure cache refresh completes
            try:
                await cache_refresh_task
            except Exception as e:
                logger.warning(f"Cache refresh failed: {str(e)}")

    async def _stream_general_response(
        self, message: str, user_id: int, context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream general chat response"""

        # For now, provide a helpful response
        if "help" in message.lower():
            response = "I can help you find recipes based on your pantry items! Try asking me 'What can I make for dinner?' or 'Show me recipes with chicken'."
        elif "pantry" in message.lower():
            response = "I can see what's in your pantry and suggest recipes that use your ingredients. Would you like me to recommend something?"
        else:
            response = "I'm your cooking assistant! I can help you find recipes based on what you have in your pantry. What would you like to cook?"

        # Simulate streaming for consistent UX
        words = response.split()
        current_text = ""

        for i, word in enumerate(words):
            current_text += word + " "

            yield {
                "type": "message_partial",
                "content": current_text.strip(),
                "timestamp": datetime.now().isoformat(),
            }

            # Small delay to show streaming effect
            await asyncio.sleep(0.05)

        # Send final complete message
        yield {
            "type": "message_complete",
            "content": response,
            "timestamp": datetime.now().isoformat(),
        }

    def _format_recipe_recommendation(self, recommendation: Dict[str, Any]) -> str:
        """Format recipe recommendation for display"""
        title = recommendation.get("title", "Unknown Recipe")
        explanation = recommendation.get("explanation", "")
        cooking_time = recommendation.get("cooking_time", 0)
        difficulty = recommendation.get("difficulty", "unknown")

        # Format highlights
        highlights = []
        if cooking_time > 0:
            highlights.append(f"⏱️ {cooking_time} min")

        if difficulty != "unknown":
            difficulty_icons = {"easy": "👌", "medium": "🔧", "hard": "👨‍🍳"}
            highlights.append(f"{difficulty_icons.get(difficulty, '🔧')} {difficulty.title()}")

        if recommendation.get("uses_expiring", False):
            highlights.append("🕐 Uses expiring ingredients")

        highlight_text = " • ".join(highlights) if highlights else ""

        formatted = f"**{title}**\n{explanation}"
        if highlight_text:
            formatted += f"\n\n{highlight_text}"

        return formatted


# Initialize service
chat_streaming_service = None


def get_chat_streaming_service(db_service=None) -> ChatStreamingService:
    """Get singleton instance of ChatStreamingService"""
    global chat_streaming_service
    if chat_streaming_service is None:
        if db_service is None:
            from backend_gateway.config.database import get_database_service

            db_service = get_database_service()
        chat_streaming_service = ChatStreamingService(db_service)
    return chat_streaming_service


@router.post("/stream")
async def chat_stream(request: ChatRequest, db_service=Depends(get_database_service)):
    """
    Stream chat response for recipe recommendations

    Returns a Server-Sent Events (SSE) stream with real-time responses
    """
    service = get_chat_streaming_service(db_service)

    async def generate_stream():
        async for chunk in service.process_message_stream(
            request.message, request.user_id, request.context
        ):
            yield chunk

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


@router.post("/quick")
async def quick_recipe_recommendations(
    request: ChatRequest, db_service=Depends(get_database_service)
):
    """
    Get quick recipe recommendations without streaming
    For clients that don't support SSE
    """
    try:
        service = get_chat_streaming_service(db_service)

        # Collect all recommendations
        recommendations = []
        timing_info = {}

        async for result in service.lean_crew_service.get_recipe_recommendations(
            request.user_id, request.message, num_recommendations=3
        ):
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])

            recommendations.append(result["recommendation"])
            timing_info = result.get("timing", {})

        return {
            "message": request.message,
            "recommendations": recommendations,
            "total_found": len(recommendations),
            "timing": timing_info,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in quick recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_stats(db_service=Depends(get_database_service)):
    """Get performance statistics for the chat service"""
    service = get_chat_streaming_service(db_service)
    stats = service.lean_crew_service.get_performance_stats()

    return {"performance_stats": stats, "timestamp": datetime.now().isoformat()}


@router.post("/cache/refresh")
async def refresh_cache(
    user_id: int = Query(default=111, description="User ID to refresh cache for"),
    db_service=Depends(get_database_service),
):
    """Manually refresh user cache"""
    try:
        service = get_chat_streaming_service(db_service)
        await service.cache_manager.ensure_fresh_cache(user_id, db_service, force_refresh=True)

        return {
            "message": f"Cache refreshed for user {user_id}",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error refreshing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache(
    cache_type: str = Query(
        default="all", description="Type of cache to clear: all, inventory, expiry, preferences"
    ),
    db_service=Depends(get_database_service),
):
    """Clear cache data"""
    try:
        service = get_chat_streaming_service(db_service)
        service.cache_manager.invalidate_cache(cache_type)

        return {"message": f"Cache cleared: {cache_type}", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
