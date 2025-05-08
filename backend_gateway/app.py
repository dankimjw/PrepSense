# File: PrepSense/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# This import should now point to the router that uses the corrected service
from backend_gateway.routers.images_router import router as images_router # Or pantry_router if you rename/prefer
import os
from dotenv import load_dotenv
import traceback
import openai

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

app = FastAPI(title="PrepSense Gateway API", version="1.0.0")

# Configure CORS
# For production, be more restrictive with allow_origins
app.add_middleware(
    CORSMiddleware,
        allow_origins=["*"],  # Example: ["http://localhost:3000", "https://yourfrontend.com"]
    )

# Include your primary router for image processing
app.include_router(images_router, prefix="/v1/images", tags=["Pantry Image Processing"])

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the PrepSense Gateway API. Visit /docs for API documentation."}

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Perform a health check."""
    return {"status": "healthy"}

# To run (from the directory containing the PrepSense folder, or if PrepSense is the root):
# If PrepSense is the root directory: uvicorn app:app --reload
# If PrepSense is a package within a larger project: uvicorn PrepSense.app:app --reload