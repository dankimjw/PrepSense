"""Router for handling recipe consumption and pantry updates"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from backend_gateway.services.pantry_service import PantryService
from backend_gateway.services.spoonacular_service import SpoonacularService
from backend_gateway.config.database import get_database_service, get_pantry_service

logger = logging.getLogger(__name__)


class IngredientUsage(BaseModel):
    """Model for ingredient usage in a recipe"""
    pantry_item_id: int = Field(..., description="ID of the pantry item to use")
    ingredient_name: str = Field(..., description="Name of the ingredient")
    quantity_used: float = Field(..., description="Amount of ingredient used")
    unit: str = Field(..., description="Unit of measurement")


class CookRecipeRequest(BaseModel):
    """Request model for cooking a recipe"""
    user_id: int = Field(..., description="User ID")
    recipe_id: int = Field(..., description="Spoonacular recipe ID")
    recipe_title: str = Field(..., description="Recipe title")
    servings: int = Field(1, description="Number of servings being made")
    ingredients_used: List[IngredientUsage] = Field(..., description="List of ingredients used from pantry")


router = APIRouter(
    prefix="/recipe-consumption",
    tags=["Recipe Consumption"],
    responses={404: {"description": "Not found"}},
)


def get_pantry_service_dep() -> PantryService:
    return get_pantry_service()


def get_spoonacular_service() -> SpoonacularService:
    return SpoonacularService()


@router.post("/cook", summary="Cook a recipe and update pantry")
async def cook_recipe(
    request: CookRecipeRequest,
    pantry_service: PantryService = Depends(get_pantry_service_dep)
) -> Dict[str, Any]:
    """
    Cook a recipe and subtract ingredients from pantry
    
    This endpoint:
    1. Validates that the user has sufficient ingredients
    2. Subtracts the used quantities from pantry items
    3. Records the cooking event
    4. Returns updated pantry state
    """
    try:
        logger.info(f"User {request.user_id} cooking recipe {request.recipe_id}: {request.recipe_title}")
        
        # Track results
        updated_items = []
        depleted_items = []
        errors = []
        
        # Process each ingredient
        for ingredient in request.ingredients_used:
            try:
                # Get current pantry item
                pantry_item = await pantry_service.get_pantry_item_by_id(ingredient.pantry_item_id)
                
                if not pantry_item:
                    errors.append(f"Pantry item {ingredient.pantry_item_id} not found")
                    continue
                
                # Calculate new quantity (convert to float to handle Decimal from DB)
                current_quantity = float(pantry_item.get('quantity', 0))
                new_quantity = current_quantity - ingredient.quantity_used
                
                if new_quantity < 0:
                    errors.append(f"Insufficient {ingredient.ingredient_name}: need {ingredient.quantity_used}, have {current_quantity}")
                    continue
                
                # Update or delete the item
                if new_quantity <= 0:
                    # Delete depleted item
                    await pantry_service.delete_pantry_item(ingredient.pantry_item_id)
                    depleted_items.append({
                        "item_id": ingredient.pantry_item_id,
                        "name": ingredient.ingredient_name,
                        "quantity_used": ingredient.quantity_used
                    })
                else:
                    # Update remaining quantity
                    await pantry_service.update_pantry_item_quantity(
                        pantry_item_id=ingredient.pantry_item_id,
                        new_quantity=new_quantity
                    )
                    updated_items.append({
                        "item_id": ingredient.pantry_item_id,
                        "name": ingredient.ingredient_name,
                        "previous_quantity": float(current_quantity),
                        "quantity_used": float(ingredient.quantity_used),
                        "remaining_quantity": float(new_quantity),
                        "unit": ingredient.unit
                    })
                    
            except Exception as e:
                logger.error(f"Error updating pantry item {ingredient.pantry_item_id}: {str(e)}")
                errors.append(f"Failed to update {ingredient.ingredient_name}: {str(e)}")
        
        # Record the cooking event in history (optional - you could create a cooking_history table)
        cooking_record = {
            "recipe_id": request.recipe_id,
            "recipe_title": request.recipe_title,
            "servings": request.servings,
            "cooked_at": datetime.now().isoformat(),
            "ingredients_used": len(request.ingredients_used),
            "items_updated": len(updated_items),
            "items_depleted": len(depleted_items)
        }
        
        return {
            "success": len(errors) == 0,
            "cooking_record": cooking_record,
            "updated_items": updated_items,
            "depleted_items": depleted_items,
            "errors": errors,
            "message": f"Successfully cooked {request.recipe_title}" if len(errors) == 0 else "Recipe cooked with some issues"
        }
        
    except Exception as e:
        logger.error(f"Error cooking recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process recipe cooking: {str(e)}")


@router.post("/check-ingredients", summary="Check if user has sufficient ingredients")
async def check_ingredients_availability(
    recipe_id: int,
    user_id: int,
    servings: int = 1,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> Dict[str, Any]:
    """
    Check if user has sufficient ingredients to cook a recipe
    
    Returns:
    - Available ingredients with quantities
    - Missing ingredients
    - Partial ingredients (have some but not enough)
    """
    try:
        # Get recipe details
        recipe = await spoonacular_service.get_recipe_information(recipe_id)
        
        # Get user's pantry
        pantry_items = await pantry_service.get_user_pantry_items(user_id)
        
        # Create pantry lookup
        pantry_lookup = {}
        for item in pantry_items:
            name = (item.get('product_name') or item.get('food_category', '')).lower().strip()
            if name not in pantry_lookup:
                pantry_lookup[name] = []
            pantry_lookup[name].append(item)
        
        # Check each recipe ingredient
        available = []
        missing = []
        partial = []
        
        for ingredient in recipe.get('extendedIngredients', []):
            ingredient_name = ingredient.get('name', '').lower().strip()
            required_amount = ingredient.get('amount', 0) * servings
            unit = ingredient.get('unit', '')
            
            if ingredient_name in pantry_lookup:
                # Calculate total available (convert to float to handle Decimal from DB)
                total_available = sum(float(item.get('quantity', 0)) for item in pantry_lookup[ingredient_name])
                
                if total_available >= required_amount:
                    available.append({
                        "name": ingredient_name,
                        "required": required_amount,
                        "available": total_available,
                        "unit": unit,
                        "pantry_items": pantry_lookup[ingredient_name]
                    })
                else:
                    partial.append({
                        "name": ingredient_name,
                        "required": required_amount,
                        "available": total_available,
                        "unit": unit,
                        "pantry_items": pantry_lookup[ingredient_name]
                    })
            else:
                missing.append({
                    "name": ingredient_name,
                    "required": required_amount,
                    "unit": unit
                })
        
        return {
            "recipe_id": recipe_id,
            "recipe_title": recipe.get('title', ''),
            "servings": servings,
            "can_cook": len(missing) == 0 and len(partial) == 0,
            "available_ingredients": available,
            "partial_ingredients": partial,
            "missing_ingredients": missing,
            "summary": {
                "total_ingredients": len(recipe.get('extendedIngredients', [])),
                "available": len(available),
                "partial": len(partial),
                "missing": len(missing)
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check ingredients: {str(e)}")