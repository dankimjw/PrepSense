"""Router for handling recipe consumption and pantry updates"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, date

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


class IngredientCheckRequest(BaseModel):
    """Request model for checking ingredient availability"""
    user_id: int = Field(..., description="User ID")
    recipe_id: int = Field(..., description="Spoonacular recipe ID")
    servings: int = Field(1, description="Number of servings being made")


class IngredientSelection(BaseModel):
    """Model for ingredient selection in quick complete"""
    ingredient_name: str = Field(..., description="Name of the ingredient")
    pantry_item_id: int = Field(..., description="Selected pantry item ID")
    quantity_to_use: float = Field(..., description="Quantity to use")
    unit: str = Field(..., description="Unit of measurement")


class QuickCompleteRequest(BaseModel):
    """Request model for quick completing a recipe"""
    user_id: int = Field(..., description="User ID")
    recipe_id: int = Field(..., description="Spoonacular recipe ID")
    servings: int = Field(1, description="Number of servings being made")
    ingredient_selections: List[IngredientSelection] = Field(..., description="Selected ingredients")


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
    request: IngredientCheckRequest,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> Dict[str, Any]:
    """
    Check if user has sufficient ingredients to cook a recipe
    
    Returns data in format expected by QuickCompleteModal frontend
    """
    try:
        # Get recipe details
        recipe = await spoonacular_service.get_recipe_information(request.recipe_id)
        
        # Get user's pantry
        pantry_items = await pantry_service.get_user_pantry_items(request.user_id)
        
        # Helper function to calculate days until expiry
        def calculate_days_until_expiry(expiration_date_str):
            if not expiration_date_str:
                return None
            try:
                exp_date = datetime.fromisoformat(expiration_date_str.replace('Z', '+00:00')).date()
                today = date.today()
                return (exp_date - today).days
            except:
                return None
        
        # Create pantry lookup by ingredient name
        pantry_lookup = {}
        for item in pantry_items:
            name = (item.get('product_name') or item.get('food_category', '')).lower().strip()
            if name not in pantry_lookup:
                pantry_lookup[name] = []
            pantry_lookup[name].append(item)
        
        # Process each recipe ingredient in format expected by frontend
        ingredients_result = []
        
        for ingredient in recipe.get('extendedIngredients', []):
            ingredient_name = ingredient.get('name', '').strip()
            required_amount = ingredient.get('amount', 0) * request.servings
            unit = ingredient.get('unit', '')
            
            # Find matching pantry items
            pantry_matches = []
            status = 'missing'
            
            ingredient_key = ingredient_name.lower()
            if ingredient_key in pantry_lookup:
                total_available = 0
                
                for pantry_item in pantry_lookup[ingredient_key]:
                    quantity = float(pantry_item.get('quantity', 0))
                    total_available += quantity
                    
                    # Calculate days until expiry
                    days_until_expiry = calculate_days_until_expiry(pantry_item.get('expiration_date'))
                    
                    pantry_matches.append({
                        "pantry_item_id": pantry_item.get('item_id'),
                        "pantry_item_name": pantry_item.get('product_name', ingredient_name),
                        "quantity_available": quantity,
                        "unit": pantry_item.get('quantity_unit', unit),
                        "expiration_date": pantry_item.get('expiration_date'),
                        "created_at": pantry_item.get('created_at'),
                        "days_until_expiry": days_until_expiry
                    })
                
                # Sort by expiration date (closest first), then by creation date (newest first)
                pantry_matches.sort(key=lambda x: (
                    x['days_until_expiry'] if x['days_until_expiry'] is not None else 999,
                    -(datetime.fromisoformat((x['created_at'] or '1970-01-01').replace('Z', '+00:00')).timestamp())
                ))
                
                # Determine status
                if total_available >= required_amount:
                    status = 'available'
                elif total_available > 0:
                    status = 'partial'
            
            ingredients_result.append({
                "ingredient_name": ingredient_name,
                "required_quantity": required_amount,
                "required_unit": unit,
                "pantry_matches": pantry_matches,
                "status": status
            })
        
        return {
            "ingredients": ingredients_result
        }
        
    except Exception as e:
        logger.error(f"Error checking ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check ingredients: {str(e)}")


@router.post("/quick-complete", summary="Quick complete a recipe")
async def quick_complete_recipe(
    request: QuickCompleteRequest,
    pantry_service: PantryService = Depends(get_pantry_service_dep),
    spoonacular_service: SpoonacularService = Depends(get_spoonacular_service)
) -> Dict[str, Any]:
    """
    Quick complete a recipe by updating pantry quantities based on ingredient selections
    """
    try:
        logger.info(f"User {request.user_id} quick completing recipe {request.recipe_id}")
        
        # Get recipe details for logging
        try:
            recipe = await spoonacular_service.get_recipe_information(request.recipe_id)
            recipe_title = recipe.get('title', f'Recipe {request.recipe_id}')
        except:
            recipe_title = f'Recipe {request.recipe_id}'
        
        # Track results
        updated_items = []
        depleted_items = []
        errors = []
        
        # Process each ingredient selection
        for selection in request.ingredient_selections:
            try:
                # Get current pantry item
                pantry_item = await pantry_service.get_pantry_item_by_id(selection.pantry_item_id)
                
                if not pantry_item:
                    errors.append(f"Pantry item {selection.pantry_item_id} not found")
                    continue
                
                # Calculate new quantity
                current_quantity = float(pantry_item.get('quantity', 0))
                quantity_to_use = min(selection.quantity_to_use, current_quantity)
                new_quantity = current_quantity - quantity_to_use
                
                if quantity_to_use <= 0:
                    continue  # Skip if nothing to use
                
                # Update or delete the item
                if new_quantity <= 0:
                    # Delete depleted item
                    await pantry_service.delete_pantry_item(selection.pantry_item_id)
                    depleted_items.append({
                        "item_id": selection.pantry_item_id,
                        "name": selection.ingredient_name,
                        "quantity_used": quantity_to_use,
                        "pantry_item_name": pantry_item.get('product_name', selection.ingredient_name)
                    })
                else:
                    # Update remaining quantity
                    await pantry_service.update_pantry_item_quantity(
                        pantry_item_id=selection.pantry_item_id,
                        new_quantity=new_quantity
                    )
                    updated_items.append({
                        "item_id": selection.pantry_item_id,
                        "name": selection.ingredient_name,
                        "pantry_item_name": pantry_item.get('product_name', selection.ingredient_name),
                        "previous_quantity": current_quantity,
                        "quantity_used": quantity_to_use,
                        "remaining_quantity": new_quantity,
                        "unit": selection.unit
                    })
                    
            except Exception as e:
                logger.error(f"Error updating pantry item {selection.pantry_item_id}: {str(e)}")
                errors.append(f"Failed to update {selection.ingredient_name}: {str(e)}")
        
        # Create completion record
        completion_record = {
            "recipe_id": request.recipe_id,
            "recipe_title": recipe_title,
            "servings": request.servings,
            "completed_at": datetime.now().isoformat(),
            "ingredients_used": len(request.ingredient_selections),
            "items_updated": len(updated_items),
            "items_depleted": len(depleted_items),
            "completion_type": "quick_complete"
        }
        
        success = len(errors) == 0
        message = f"Successfully completed {recipe_title}!" if success else f"Completed {recipe_title} with some issues"
        
        if len(updated_items) > 0:
            message += f" Updated {len(updated_items)} pantry items."
        if len(depleted_items) > 0:
            message += f" Removed {len(depleted_items)} depleted items."
        
        return {
            "success": success,
            "message": message,
            "completion_record": completion_record,
            "updated_items": updated_items,
            "depleted_items": depleted_items,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in quick complete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete recipe: {str(e)}")
