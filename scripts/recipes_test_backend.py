#!/usr/bin/env python3
"""
Recipes Test Backend - Minimal FastAPI app with only recipes-related endpoints
for testing the iOS app's recipes tab functionality.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()
print("Successfully loaded .env file.")

# Load OpenAI API key from file if specified
key_path = os.getenv("OPENAI_API_KEY_FILE")
if key_path and Path(key_path).exists():
    try:
        api_key = Path(key_path).read_text().strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            print(f"Loaded OpenAI API key from {key_path}")
    except Exception as e:
        print(f"Error reading OpenAI API key from {key_path}: {e}")

# Create FastAPI app
app = FastAPI(
    title="PrepSense Recipes Test API",
    version="1.0.0",
    description="Test backend for recipes tab functionality",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for recipes
class Recipe(BaseModel):
    id: int
    title: str
    ingredients: List[str]
    instructions: List[str]
    readyInMinutes: int
    servings: int
    image: Optional[str] = None
    sourceUrl: Optional[str] = None
    summary: Optional[str] = None


class RecipeSearchRequest(BaseModel):
    query: Optional[str] = None
    diet: Optional[str] = None
    cuisine: Optional[str] = None
    type: Optional[str] = None
    number: int = 10


class PantryRecipeRequest(BaseModel):
    user_id: int = 111


# Mock data for testing
MOCK_RECIPES = [
    {
        "id": 1,
        "title": "Spaghetti Carbonara",
        "ingredients": ["spaghetti", "eggs", "bacon", "parmesan cheese", "black pepper"],
        "instructions": ["Cook spaghetti", "Fry bacon", "Mix eggs and cheese", "Combine all"],
        "readyInMinutes": 20,
        "servings": 4,
        "image": "https://example.com/carbonara.jpg",
        "summary": "Classic Italian pasta dish",
    },
    {
        "id": 2,
        "title": "Chicken Stir Fry",
        "ingredients": ["chicken breast", "bell peppers", "onion", "soy sauce", "garlic"],
        "instructions": ["Cut chicken", "Heat oil", "Stir fry vegetables", "Add chicken and sauce"],
        "readyInMinutes": 15,
        "servings": 2,
        "image": "https://example.com/stirfry.jpg",
        "summary": "Quick and healthy stir fry",
    },
    {
        "id": 3,
        "title": "Vegetable Soup",
        "ingredients": ["carrots", "celery", "onion", "vegetable broth", "tomatoes"],
        "instructions": ["Chop vegetables", "Sauté onions", "Add broth", "Simmer 30 minutes"],
        "readyInMinutes": 45,
        "servings": 6,
        "image": "https://example.com/soup.jpg",
        "summary": "Hearty vegetable soup",
    },
]


# Basic endpoints
@app.get("/")
async def root():
    return {"message": "PrepSense Recipes Test Backend is running!"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "PrepSense Recipes Test Backend"}


# Recipes tab endpoints
@app.post("/api/v1/recipes/search/from-pantry")
async def search_recipes_from_pantry(request: PantryRecipeRequest):
    """
    Get recipe recommendations based on pantry items.
    This endpoint is called by the 'Pantry' tab in the iOS app.
    """
    print(f"Searching recipes from pantry for user {request.user_id}")

    # Return mock recipes for testing
    return {
        "results": MOCK_RECIPES,
        "totalResults": len(MOCK_RECIPES),
        "message": "Recipes based on your pantry items",
    }


@app.post("/api/v1/recipes/search/complex")
async def search_recipes_complex(request: RecipeSearchRequest):
    """
    Search recipes with complex filters.
    This endpoint is called by the 'Discover' tab in the iOS app.
    """
    print(
        f"Complex recipe search: query='{request.query}', diet='{request.diet}', cuisine='{request.cuisine}'"
    )

    # Filter mock recipes based on query (simple text matching)
    filtered_recipes = MOCK_RECIPES
    if request.query:
        filtered_recipes = [
            recipe
            for recipe in MOCK_RECIPES
            if request.query.lower() in recipe["title"].lower()
            or any(
                request.query.lower() in ingredient.lower() for ingredient in recipe["ingredients"]
            )
        ]

    return {
        "results": filtered_recipes[: request.number],
        "totalResults": len(filtered_recipes),
        "message": f"Found {len(filtered_recipes)} recipes",
    }


@app.get("/api/v1/recipes/random")
async def get_random_recipes(number: int = 10):
    """
    Get random recipes for discovery.
    This endpoint is called by the 'Discover' tab when no search query is provided.
    """
    print(f"Getting {number} random recipes")

    return {
        "recipes": MOCK_RECIPES[:number],
        "message": f"Random selection of {len(MOCK_RECIPES)} recipes",
    }


@app.get("/api/v1/user-recipes")
async def get_user_recipes(user_id: int = 111):
    """
    Get user's saved recipes.
    This endpoint is called by the 'My Recipes' tab in the iOS app.
    """
    print(f"Getting saved recipes for user {user_id}")

    # Return mock saved recipes
    saved_recipes = [
        {**recipe, "isFavorite": True, "userRating": 5, "dateAdded": "2024-01-15"}
        for recipe in MOCK_RECIPES[:2]  # First 2 recipes as "saved"
    ]

    return {
        "recipes": saved_recipes,
        "totalCount": len(saved_recipes),
        "message": f"Found {len(saved_recipes)} saved recipes",
    }


# Additional test endpoints
@app.get("/api/v1/test/recipes-endpoints")
async def test_recipes_endpoints():
    """Test endpoint to verify all recipes endpoints are working."""
    return {
        "endpoints": [
            "POST /api/v1/recipes/search/from-pantry",
            "POST /api/v1/recipes/search/complex",
            "GET /api/v1/recipes/random",
            "GET /api/v1/user-recipes",
        ],
        "status": "All recipes endpoints are available",
        "mock_data_count": len(MOCK_RECIPES),
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting PrepSense Recipes Test Backend on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
