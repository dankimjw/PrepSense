"""FastAPI application entry point for the PrepSense backend gateway."""

import sys
import os
# Add parent directory to Python path to handle imports when run from different locations
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from typing import Optional
import os
from dotenv import load_dotenv
import traceback
import openai
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Import routers
from backend_gateway.routers import images_router, ocr_router, health_router, admin_router
from backend_gateway.routers.users import router as users_router
from backend_gateway.services.user_service import UserService
from backend_gateway.core.config import settings

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

# Set OpenAI API key
client = openai  #  use the openai module directly

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting up PrepSense backend...")
    # Create default user if it doesn't exist
    try:
        user_service = UserService()
        await user_service.create_default_user_if_not_exists()
    except Exception as e:
        logger.error(f"Failed to create default user: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PrepSense backend...")

# Initialize the FastAPI app
app = FastAPI(
    title="PrepSense Gateway API",
    description="Your Smart Pantry Assistant - AI-powered recipe recommendations and pantry management",
    version="1.4.0",
    lifespan=lifespan
)

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
        logger.warning(f"Static directory not found")

# Also mount old Recipe Images directory if it exists
recipe_images_path = Path("Recipe Images")
if recipe_images_path.exists():
    app.mount("/Recipe Images", StaticFiles(directory=str(recipe_images_path)), name="recipe_images")
    logger.info(f"Mounted Recipe Images directory at {recipe_images_path.absolute()}")

# Include routers
# Health endpoint without prefix for readiness probes
app.include_router(health_router)
app.include_router(users_router, prefix=f"{settings.API_V1_STR}", tags=["users"])
app.include_router(images_router, prefix=f"{settings.API_V1_STR}/images", tags=["Pantry Image Processing"])
# BigQuery router removed - using PostgreSQL instead

# Import pantry router after other routers to avoid circular imports
from backend_gateway.routers.pantry_router import router as pantry_router
app.include_router(pantry_router, prefix=f"{settings.API_V1_STR}", tags=["Pantry"])

# Import chat router
from backend_gateway.routers.chat_router import router as chat_router
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}", tags=["Chat"])


# Import spoonacular router
from backend_gateway.routers.spoonacular_router import router as spoonacular_router
app.include_router(spoonacular_router, prefix=f"{settings.API_V1_STR}", tags=["Spoonacular Recipes"])

# Import recipe consumption router
from backend_gateway.routers.recipe_consumption_router import router as recipe_consumption_router
app.include_router(recipe_consumption_router, prefix=f"{settings.API_V1_STR}", tags=["Recipe Consumption"])

# Import user recipes router (PostgreSQL version)
from backend_gateway.routers.user_recipes_router import router as user_recipes_router
app.include_router(user_recipes_router, prefix=f"{settings.API_V1_STR}", tags=["User Recipes"])

# Import shopping list router
from backend_gateway.routers.shopping_list_router import router as shopping_list_router
app.include_router(shopping_list_router, prefix=f"{settings.API_V1_STR}", tags=["Shopping List"])

# Import demo router (for testing)
from backend_gateway.routers.demo_router import router as demo_router
app.include_router(demo_router, prefix=f"{settings.API_V1_STR}", tags=["Demo"])

# Import cooking history router
from backend_gateway.routers.cooking_history_router import router as cooking_history_router
app.include_router(cooking_history_router, prefix=f"{settings.API_V1_STR}", tags=["Cooking History"])

# Import units router
from backend_gateway.routers.units_router import router as units_router
app.include_router(units_router, prefix=f"{settings.API_V1_STR}", tags=["Units"])

# Import OCR router
from backend_gateway.routers.ocr_router import router as ocr_router
app.include_router(ocr_router, prefix=f"{settings.API_V1_STR}", tags=["OCR"])

# Import stats router
from backend_gateway.routers.stats_router import router as stats_router
app.include_router(stats_router, prefix=f"{settings.API_V1_STR}", tags=["Statistics"])
app.include_router(admin_router, tags=["Admin"])

# Import OCR router
from backend_gateway.routers.ocr_router import router as ocr_router
app.include_router(ocr_router, prefix=f"{settings.API_V1_STR}", tags=["OCR"])

# Import nutrition router
from backend_gateway.routers.nutrition_router import router as nutrition_router
app.include_router(nutrition_router, tags=["Nutrition"])

# Import preferences router
from backend_gateway.routers.preferences_router import router as preferences_router
app.include_router(preferences_router, prefix=f"{settings.API_V1_STR}", tags=["User Preferences"])

# Import mock recipe router for testing
from backend_gateway.routers.mock_recipe_router import router as mock_recipe_router
app.include_router(mock_recipe_router, prefix=f"{settings.API_V1_STR}", tags=["Mock Data"])

# Import remote control router for centralized mock data control
from backend_gateway.routers.remote_control_router import router as remote_control_router
app.include_router(remote_control_router, prefix=f"{settings.API_V1_STR}", tags=["Remote Control"])

# Import sustainability router for environmental impact
from backend_gateway.routers.sustainability_router import router as sustainability_router
app.include_router(sustainability_router, tags=["Sustainability"])

# Import waste reduction router for food waste prevention
from backend_gateway.routers.waste_reduction_router import router as waste_reduction_router
app.include_router(waste_reduction_router, tags=["Waste Reduction"])

# Import semantic search router
from backend_gateway.routers.semantic_search_router import router as semantic_search_router
app.include_router(semantic_search_router, tags=["Semantic Search"])

# Import supply chain impact router
from backend_gateway.routers.supply_chain_impact_router import router as supply_chain_impact_router
app.include_router(supply_chain_impact_router, tags=["Supply Chain Impact"])

# Import USDA router for nutritional data
from backend_gateway.routers.usda_router import router as usda_router
app.include_router(usda_router, tags=["USDA Food Database"])

# USDA unit validation router
from backend_gateway.routers.usda_unit_router import router as usda_unit_router
app.include_router(usda_unit_router, tags=["USDA Unit Validation"])

# Unit validation for smart unit checking
from backend_gateway.routers.unit_validation_router import router as unit_validation_router
app.include_router(unit_validation_router, tags=["Unit Validation"])

# CrewAI intelligent recipe recommendation system
from backend_gateway.routers.crewai_router import router as crewai_router
app.include_router(crewai_router, prefix=f"{settings.API_V1_STR}", tags=["CrewAI Intelligence"])

# AI-powered recipe generation using CrewAI
# from backend_gateway.routers.ai_recipes_router import router as ai_recipes_router
# app.include_router(ai_recipes_router, tags=["AI Recipes"])

# Import recipe image router (disabled until google-cloud-storage is installed)
# from backend_gateway.routers.recipe_image_router import router as recipe_image_router
# app.include_router(recipe_image_router, prefix=f"{settings.API_V1_STR}", tags=["Recipe Images"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the PrepSense Gateway API. Visit /docs for API documentation."}

# Startup event handler has been moved to the lifespan context manager above

@app.get(f"{settings.API_V1_STR}/health", tags=["Health Check"])
async def health_check():
    """Perform a health check and return environment status."""
    from backend_gateway.core.config_utils import get_openai_api_key

    health_status = {
        "status": "healthy",
        "environment": {
            "openai_configured": False,
            "openai_valid": False,
            "spoonacular_configured": False,
            "database_configured": False,
            "crewai_enabled": False
        },
        "version": "1.4.0"
    }

    # Check OpenAI configuration
    try:
        openai_key = get_openai_api_key()
        if openai_key:
            health_status["environment"]["openai_configured"] = True
            # Test OpenAI API (basic validation)
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                # Quick test call (doesn't count against quota much)
                response = client.models.list()
                health_status["environment"]["openai_valid"] = True
            except Exception as e:
                logger.warning(f"OpenAI API test failed: {e}")
    except Exception as e:
        logger.warning(f"OpenAI configuration check failed: {e}")

    # Check Spoonacular configuration
    spoonacular_key = os.getenv("SPOONACULAR_KEY")
    if spoonacular_key:
        health_status["environment"]["spoonacular_configured"] = True

    # Check database configuration
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        health_status["environment"]["database_configured"] = True

    # Check CrewAI system
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
        from src.crews.prepsense_main import PrepSenseMainCrew
        health_status["environment"]["crewai_enabled"] = True
    except ImportError:
        logger.info("CrewAI system not available")

    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)