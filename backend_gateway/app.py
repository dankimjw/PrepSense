"""FastAPI application entry point for the PrepSense backend gateway."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import os
from dotenv import load_dotenv
import traceback
import openai

# Import routers
from backend_gateway.routers.images_router import router as images_router
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
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai  #  use the openai module directly

app = FastAPI(
    title="PrepSense Gateway API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router, prefix=f"{settings.API_V1_STR}", tags=["users"])
app.include_router(images_router, prefix=f"{settings.API_V1_STR}/images", tags=["Pantry Image Processing"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the PrepSense Gateway API. Visit /docs for API documentation."}

@app.on_event("startup")
async def startup_event():
    """Initialize data on startup"""
    # Create default user if it doesn't exist
    user_service = UserService()
    await user_service.create_default_user()

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Perform a health check."""
    return {"status": "healthy"}

# To run (from the directory containing the PrepSense folder, or if PrepSense is the root):
# If PrepSense is the root directory: uvicorn app:app --reload
# If PrepSense is a package within a larger project: uvicorn PrepSense.app:app --reload