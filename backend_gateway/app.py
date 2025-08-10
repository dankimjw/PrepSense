"""FastAPI application entry point for the PrepSense backend gateway."""

import os
import sys

# Add parent directory to Python path to handle imports when run from different locations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import os
import traceback
from contextlib import asynccontextmanager

import openai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend_gateway.core.logging_config import get_logger, setup_logging

# Import monitoring and logging configuration
from backend_gateway.core.monitoring import setup_monitoring

# Import enhanced OpenAPI configuration
from backend_gateway.core.openapi_config import (
    custom_openapi_schema,
    export_openapi_schema,
    setup_enhanced_docs,
)

# from backend_gateway.core.observability import setup_observability  # Temporarily disabled


# Setup structured logging first
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_format=os.getenv("LOG_FORMAT", "").lower() == "json",
    enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true",
)

logger = get_logger(__name__)

from backend_gateway.core.config import settings

# Import routers
from backend_gateway.routers import admin_router, health_router, images_router, ocr_router
from backend_gateway.routers.users import router as users_router
from backend_gateway.services.user_service import UserService

# Load environment variables from the .env file
try:
    if load_dotenv():
        print("Successfully loaded .env file.")
        # For debugging - confirm key is loaded (remove for production)
        # print(f"OPENAI_API_KEY Check from app.py: {os.getenv('OPENAI_API_KEY')}")
    else:
        print(".env file not found. Ensure it's in the project root and contains OPENAI_API_KEY.")
except Exception as e:
    print(f"Exception occurred during .env loading: {e}")
    traceback.print_exc()
    # Consider if the application should fail to start if the .env or key is critical
    # raise RuntimeError(f"Error loading environment variables: {str(e)}")

# OpenAI module is imported; use directly where needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up PrepSense backend...")

    # Setup monitoring and observability
    environment = os.getenv("ENVIRONMENT", "development")
    try:
        setup_monitoring(app, environment)
        # setup_observability(app, environment=environment)  # Temporarily disabled
        logger.info("Monitoring configured", environment=environment)
    except Exception as e:
        logger.error("Failed to setup monitoring", error=str(e), exc_info=True)

    # Setup enhanced OpenAPI documentation
    try:
        setup_enhanced_docs(app)
        logger.info("Enhanced OpenAPI documentation configured")

        # Export OpenAPI schema for contract testing
        if os.getenv("EXPORT_OPENAPI_SCHEMA", "true").lower() == "true":
            try:
                export_openapi_schema(app, "openapi.json")
                logger.info("OpenAPI schema exported for contract testing")
            except Exception as e:
                logger.warning(f"Failed to export OpenAPI schema: {e}")

    except Exception as e:
        logger.error("Failed to setup enhanced OpenAPI documentation", error=str(e), exc_info=True)

    # Create default user if it doesn't exist
    try:
        user_service = UserService()
        await user_service.create_default_user_if_not_exists()
        logger.info("Default user setup completed")
    except Exception as e:
        logger.error("Failed to create default user", error=str(e), exc_info=True)

    logger.info("PrepSense backend startup completed successfully")
    yield

    # Shutdown
    logger.info("Shutting down PrepSense backend...")
    logger.info("PrepSense backend shutdown completed")


# Initialize the FastAPI app with enhanced OpenAPI configuration
app = FastAPI(
    title="PrepSense Gateway API",
    description="Your Smart Pantry Assistant - AI-powered recipe recommendations and pantry management",
    version="1.4.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health check and system monitoring"},
        {"name": "users", "description": "User management and authentication"},
        {"name": "pantry", "description": "Pantry management and inventory tracking"},
        {"name": "recipes", "description": "Recipe management and AI recommendations"},
        {"name": "ocr", "description": "Receipt processing with OCR"},
        {"name": "images", "description": "Image processing and uploads"},
        {"name": "crewai", "description": "AI agent operations"},
        {"name": "monitoring", "description": "Application monitoring"},
        {"name": "admin", "description": "Administrative operations"},
    ],
    contact={
        "name": "PrepSense Development Team",
        "url": "https://github.com/dankimjw/PrepSense",
        "email": "dev@prepsense.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8001",
            "description": "Development server",
        },
        {
            "url": "http://localhost:8002",
            "description": "Testing server",
        },
        {
            "url": "https://api.prepsense.com",
            "description": "Production server",
        },
    ],
)

# Set custom OpenAPI schema generation
app.openapi = lambda: custom_openapi_schema(app)

# Configure CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Mount static files for recipe images
from pathlib import Path

# Mount the new static directory with imported recipe images
static_path = Path("backend_gateway/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Mounted static directory at {static_path.absolute()}")
else:
    # Try relative path from current file
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        logger.info(f"Mounted static directory at {static_path.absolute()}")
    else:
        logger.warning("Static directory not found")

# Also mount old Recipe Images directory if it exists
recipe_images_path = Path("Recipe Images")
if recipe_images_path.exists():
    app.mount(
        "/Recipe Images", StaticFiles(directory=str(recipe_images_path)), name="recipe_images"
    )
    logger.info(f"Mounted Recipe Images directory at {recipe_images_path.absolute()}")

# Include routers
# Health endpoint without prefix for readiness probes
app.include_router(health_router)
app.include_router(users_router, prefix=f"{settings.API_V1_STR}", tags=["users"])
app.include_router(images_router, prefix=f"{settings.API_V1_STR}/images", tags=["images"])
# BigQuery router removed - using PostgreSQL instead

# Import pantry router after other routers to avoid circular imports
from backend_gateway.routers.pantry_router import router as pantry_router

app.include_router(pantry_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import chat router
from backend_gateway.routers.chat_router import router as chat_router

app.include_router(chat_router, prefix=f"{settings.API_V1_STR}", tags=["recipes"])


# Import spoonacular router
from backend_gateway.routers.spoonacular_router import router as spoonacular_router

app.include_router(spoonacular_router, prefix=f"{settings.API_V1_STR}", tags=["recipes"])

# Import recipe consumption router
from backend_gateway.routers.recipe_consumption_router import router as recipe_consumption_router

app.include_router(recipe_consumption_router, prefix=f"{settings.API_V1_STR}", tags=["recipes"])

# Import user recipes router (PostgreSQL version)
from backend_gateway.routers.user_recipes_router import router as user_recipes_router

app.include_router(user_recipes_router, prefix=f"{settings.API_V1_STR}", tags=["recipes"])

# Import shopping list router
from backend_gateway.routers.shopping_list_router import router as shopping_list_router

app.include_router(shopping_list_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import demo router (for testing)
from backend_gateway.routers.demo_router import router as demo_router

app.include_router(demo_router, prefix=f"{settings.API_V1_STR}", tags=["admin"])

# Import cooking history router
from backend_gateway.routers.cooking_history_router import router as cooking_history_router

app.include_router(cooking_history_router, prefix=f"{settings.API_V1_STR}", tags=["recipes"])

# Import units router
from backend_gateway.routers.units_router import router as units_router

app.include_router(units_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import OCR router
from backend_gateway.routers.ocr_router import router as ocr_router

app.include_router(ocr_router, prefix=f"{settings.API_V1_STR}", tags=["ocr"])

# Import stats router
from backend_gateway.routers.stats_router import router as stats_router

app.include_router(stats_router, prefix=f"{settings.API_V1_STR}", tags=["monitoring"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}", tags=["admin"])

# Import nutrition router
from backend_gateway.routers.nutrition_router import router as nutrition_router

app.include_router(nutrition_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import preferences router
from backend_gateway.routers.preferences_router import router as preferences_router

app.include_router(preferences_router, prefix=f"{settings.API_V1_STR}", tags=["users"])

# Import mock recipe router for testing
from backend_gateway.routers.mock_recipe_router import router as mock_recipe_router

app.include_router(mock_recipe_router, prefix=f"{settings.API_V1_STR}", tags=["admin"])

# Import remote control router for centralized mock data control
from backend_gateway.routers.remote_control_router import router as remote_control_router

app.include_router(remote_control_router, prefix=f"{settings.API_V1_STR}", tags=["admin"])

# Import sustainability router for environmental impact
from backend_gateway.routers.sustainability_router import router as sustainability_router

app.include_router(sustainability_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import waste reduction router for food waste prevention
from backend_gateway.routers.waste_reduction_router import router as waste_reduction_router

app.include_router(waste_reduction_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import semantic search router
from backend_gateway.routers.semantic_search_router import router as semantic_search_router

app.include_router(semantic_search_router, prefix=f"{settings.API_V1_STR}", tags=["recipes"])

# Import supply chain impact router
from backend_gateway.routers.supply_chain_impact_router import router as supply_chain_router

app.include_router(supply_chain_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Import USDA router for nutritional data
from backend_gateway.routers.usda_router import router as usda_router

app.include_router(usda_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# USDA unit validation router
from backend_gateway.routers.usda_unit_router import router as usda_unit_router

app.include_router(usda_unit_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# Unit validation for smart unit checking
from backend_gateway.routers.unit_validation_router import router as unit_validation_router

app.include_router(unit_validation_router, prefix=f"{settings.API_V1_STR}", tags=["pantry"])

# CrewAI intelligent recipe recommendation system - TEMPORARILY DISABLED
# from backend_gateway.routers.crewai_router import router as crewai_router
# app.include_router(crewai_router, prefix=f"{settings.API_V1_STR}", tags=["crewai"])

# AI-powered recipe generation using CrewAI
# from backend_gateway.routers.ai_recipes_router import router as ai_recipes_router
# app.include_router(ai_recipes_router, tags=["AI Recipes"])

# Import recipe image router (disabled until google-cloud-storage is installed)
# from backend_gateway.routers.recipe_image_router import router as recipe_image_router
# app.include_router(recipe_image_router, prefix=f"{settings.API_V1_STR}", tags=["Recipe Images"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the PrepSense Gateway API",
        "version": "1.4.0",
        "documentation": "/docs",
        "api_reference": "/redoc",
        "health_check": "/api/v1/health",
        "status_page": "/api/status",
        "metrics": "/metrics",
    }


# Startup event handler has been moved to the lifespan context manager above


@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns detailed system status including:
    - API service health
    - External service configurations
    - Database connectivity
    - AI service availability
    - Monitoring system status
    """
    from backend_gateway.core.config_utils import get_openai_api_key

    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be updated by monitoring
        "version": "1.4.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {
            "api": {"status": "healthy", "response_time_ms": 0},
            "database": {"status": "unknown", "connected": False},
            "openai": {"status": "unknown", "configured": False, "valid": False},
            "spoonacular": {"status": "unknown", "configured": False},
            "crewai": {"status": "unknown", "enabled": False},
        },
        "monitoring": {
            "sentry_enabled": bool(os.getenv("SENTRY_DSN")),
            "metrics_enabled": True,
            "logging_enabled": True,
        },
    }

    # Check OpenAI configuration
    try:
        openai_key = get_openai_api_key()
        if openai_key:
            health_status["services"]["openai"]["configured"] = True
            health_status["services"]["openai"]["status"] = "configured"

            # Test OpenAI API (basic validation)
            try:
                import openai

                client = openai.OpenAI(api_key=openai_key)
                # Quick test call (doesn't count against quota much)
                client.models.list()
                health_status["services"]["openai"]["valid"] = True
                health_status["services"]["openai"]["status"] = "healthy"
            except Exception as e:
                logger.warning(f"OpenAI API test failed: {e}")
                health_status["services"]["openai"]["status"] = "error"
                health_status["services"]["openai"]["error"] = str(e)
    except Exception as e:
        logger.warning(f"OpenAI configuration check failed: {e}")
        health_status["services"]["openai"]["status"] = "error"
        health_status["services"]["openai"]["error"] = str(e)

    # Check Spoonacular configuration
    spoonacular_key = os.getenv("SPOONACULAR_KEY")
    if spoonacular_key:
        health_status["services"]["spoonacular"]["configured"] = True
        health_status["services"]["spoonacular"]["status"] = "configured"

    # Check database configuration
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        health_status["services"]["database"]["configured"] = True
        health_status["services"]["database"]["status"] = "configured"
        # TODO: Add actual database connectivity test

    # Check CrewAI system - DISABLED
    # try:
    #     sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
    #     from src.crews.prepsense_main import PrepSenseMainCrew
    #     health_status["services"]["crewai"]["enabled"] = True
    #     health_status["services"]["crewai"]["status"] = "healthy"
    # except ImportError:
    #     logger.info("CrewAI system not available")
    #     health_status["services"]["crewai"]["status"] = "not_available"

    # Overall health determination
    service_statuses = [service["status"] for service in health_status["services"].values()]
    if any(status == "error" for status in service_statuses):
        health_status["status"] = "degraded"
    elif all(status in ["healthy", "configured", "not_available"] for status in service_statuses):
        health_status["status"] = "healthy"
    else:
        health_status["status"] = "unknown"

    return health_status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
