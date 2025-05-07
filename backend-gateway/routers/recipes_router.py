from fastapi import APIRouter
from services.recipe_service import generate_recipe

router = APIRouter()

@router.get("/suggestions")
async def get_recipe_suggestions():
    return generate_recipe()