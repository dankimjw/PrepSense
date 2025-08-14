#!/usr/bin/env python3
"""
Minimal FastAPI app for CrewAI chat-only debug mode.
This stripped-down version only includes the essential endpoints for chat functionality.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend_gateway.core.config import settings
from backend_gateway.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting CrewAI Chat-Only Debug Mode")

    # Set environment variables for CrewAI
    os.environ["CREWAI_ENABLED"] = "true"

    yield

    logger.info("Shutting down CrewAI Chat-Only Debug Mode")


# Create FastAPI app
app = FastAPI(
    title="PrepSense Chat-Only Debug API",
    description="Minimal API for CrewAI chat debugging",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in debug mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mode": "chat-only-debug",
        "services": {
            "crewai": {"status": "enabled", "enabled": True},
            "chat": {"status": "enabled", "enabled": True},
        },
    }


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "PrepSense Chat-Only Debug Mode",
        "docs": "/docs",
        "health": "/health",
    }


# Include only essential routers
try:
    # Chat router (includes CrewAI chat functionality)
    from backend_gateway.routers.chat_router import router as chat_router
    app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
    logger.info("Chat router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load chat router: {e}")

try:
    # CrewAI router (for direct CrewAI operations if needed)
    from backend_gateway.routers.crewai_router import router as crewai_router
    app.include_router(crewai_router, prefix=f"{settings.API_V1_STR}/crewai", tags=["crewai"])
    logger.info("CrewAI router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load CrewAI router: {e}")

try:
    # User router (minimal - just for authentication context)
    from backend_gateway.routers.users_router import router as users_router
    app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
    logger.info("Users router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load users router: {e}")

try:
    # Preferences router (for user preferences in chat)
    from backend_gateway.routers.preferences_router import router as preferences_router
    app.include_router(preferences_router, prefix=f"{settings.API_V1_STR}/preferences", tags=["preferences"])
    logger.info("Preferences router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load preferences router: {e}")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "message": str(exc),
        },
    )


# API info endpoint
@app.get(f"{settings.API_V1_STR}")
async def api_info() -> dict[str, Any]:
    """API information endpoint."""
    return {
        "title": "PrepSense Chat-Only Debug API",
        "version": "1.0.0",
        "mode": "chat-only-debug",
        "endpoints": {
            "chat": f"{settings.API_V1_STR}/chat",
            "crewai": f"{settings.API_V1_STR}/crewai",
            "users": f"{settings.API_V1_STR}/users",
            "preferences": f"{settings.API_V1_STR}/preferences",
            "health": "/health",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting chat-only server on {host}:{port}")

    uvicorn.run(
        "backend_gateway.app_chat_only:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
