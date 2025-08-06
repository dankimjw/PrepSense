import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend_gateway.config.database import get_database_service
from backend_gateway.services.ingredient_parser_service import IngredientParserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/shopping-list",
    tags=["Shopping List"],
    responses={404: {"description": "Not found"}},
)


class ShoppingListItem(BaseModel):
    item_name: str = Field(..., description="Name of the item")
    quantity: Optional[float] = Field(None, description="Quantity needed")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    category: Optional[str] = Field(None, description="Category of the item")
    recipe_name: Optional[str] = Field(None, description="Associated recipe")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_checked: Optional[bool] = Field(False, description="Whether item is checked off")
    priority: Optional[int] = Field(0, description="Priority level (0=normal, 1=high, 2=urgent)")


class RecipeIngredientsRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    recipe_name: str = Field(..., description="Recipe name")
    ingredients: List[str] = Field(..., description="List of ingredient strings from recipe")


class ParsedIngredient(BaseModel):
    original_string: str
    parsed_name: str
    quantity: float
    unit: str
    category: str


@router.post(
    "/add-from-recipe",
    response_model=Dict[str, Any],
    summary="Add Recipe Ingredients to Shopping List",
)
async def add_recipe_ingredients_to_shopping_list(
    request: RecipeIngredientsRequest, db_service=Depends(get_database_service)
):
    """
    Parse recipe ingredients and add them to shopping list intelligently.
    This endpoint parses complex ingredient strings and aggregates quantities.
    """
    try:
        parser = IngredientParserService()

        # Parse all ingredients
        parsed_ingredients = await parser.parse_ingredients_bulk(request.ingredients)

        # Aggregate by ingredient name
        aggregated = parser.aggregate_ingredients(parsed_ingredients)

        added_count = 0
        updated_count = 0
        parsed_details = []

        for item in aggregated:
            # Check if ingredient already exists in shopping list
            check_query = """
            SELECT shopping_list_item_id, quantity, unit
            FROM shopping_list_items
            WHERE user_id = @user_id 
            AND LOWER(item_name) = LOWER(@item_name)
            AND is_checked = false
            AND (recipe_name IS NULL OR recipe_name != @recipe_name)
            """

            existing = db_service.execute_query(
                check_query,
                {
                    "user_id": request.user_id,
                    "item_name": item["item_name"],
                    "recipe_name": request.recipe_name,
                },
            )

            if existing:
                # Update quantity if units are compatible
                existing_item = existing[0]
                if existing_item["unit"] == item["unit"]:
                    # Same unit, can add quantities
                    update_query = """
                    UPDATE shopping_list_items
                    SET quantity = quantity + @additional_quantity,
                        notes = CASE 
                            WHEN notes IS NULL THEN @note
                            ELSE notes || ', ' || @note
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE shopping_list_item_id = @item_id
                    """

                    db_service.execute_query(
                        update_query,
                        {
                            "additional_quantity": item["quantity"],
                            "note": f"Added from {request.recipe_name}",
                            "item_id": existing_item["shopping_list_item_id"],
                        },
                    )
                    updated_count += 1
                else:
                    # Different units, add as separate item with note
                    insert_query = """
                    INSERT INTO shopping_list_items (
                        user_id, item_name, quantity, unit, category, 
                        recipe_name, notes, is_checked, priority
                    ) VALUES (
                        @user_id, @item_name, @quantity, @unit, @category,
                        @recipe_name, @notes, false, 0
                    )
                    """

                    db_service.execute_query(
                        insert_query,
                        {
                            "user_id": request.user_id,
                            "item_name": item["item_name"],
                            "quantity": item["quantity"],
                            "unit": item["unit"],
                            "category": item["category"],
                            "recipe_name": request.recipe_name,
                            "notes": f"Different unit from existing ({existing_item['unit']})",
                        },
                    )
                    added_count += 1
            else:
                # Insert new item
                insert_query = """
                INSERT INTO shopping_list_items (
                    user_id, item_name, quantity, unit, category, 
                    recipe_name, notes, is_checked, priority
                ) VALUES (
                    @user_id, @item_name, @quantity, @unit, @category,
                    @recipe_name, @notes, false, 0
                )
                """

                db_service.execute_query(
                    insert_query,
                    {
                        "user_id": request.user_id,
                        "item_name": item["item_name"],
                        "quantity": item["quantity"],
                        "unit": item["unit"],
                        "category": item["category"],
                        "recipe_name": request.recipe_name,
                        "notes": None,
                    },
                )
                added_count += 1

            parsed_details.append(
                {
                    "ingredient": item["item_name"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "category": item["category"],
                }
            )

        return {
            "message": "Recipe ingredients processed successfully",
            "items_added": added_count,
            "items_updated": updated_count,
            "total_ingredients": len(request.ingredients),
            "parsed_details": parsed_details,
        }

    except Exception as e:
        logger.error(f"Error adding recipe ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add ingredients: {str(e)}")


@router.get(
    "/user/{user_id}/items/grouped",
    response_model=Dict[str, List[Dict[str, Any]]],
    summary="Get Shopping List Grouped by Category",
)
async def get_shopping_list_grouped(user_id: int, db_service=Depends(get_database_service)):
    """
    Get shopping list items grouped by category for easier shopping.
    """
    try:
        query = """
        SELECT 
            shopping_list_item_id,
            item_name,
            quantity,
            unit,
            COALESCE(category, 'Other') as category,
            recipe_name,
            notes,
            is_checked,
            priority,
            added_date,
            updated_at
        FROM shopping_list_items
        WHERE user_id = @user_id
        ORDER BY 
            category,
            is_checked ASC,
            priority DESC,
            item_name ASC
        """

        items = db_service.execute_query(query, {"user_id": user_id})

        # Group by category
        grouped = {}
        for item in items:
            category = item["category"]
            if category not in grouped:
                grouped[category] = []

            # Convert datetime objects to ISO format strings
            if item.get("added_date"):
                item["added_date"] = item["added_date"].isoformat()
            if item.get("updated_at"):
                item["updated_at"] = item["updated_at"].isoformat()

            grouped[category].append(item)

        # Order categories for shopping flow
        category_order = [
            "Produce",
            "Dairy",
            "Meat",
            "Seafood",
            "Bakery",
            "Grains",
            "Pantry",
            "Frozen",
            "Beverages",
            "Other",
        ]

        ordered_grouped = {}
        for category in category_order:
            if category in grouped:
                ordered_grouped[category] = grouped[category]

        # Add any remaining categories
        for category, items in grouped.items():
            if category not in ordered_grouped:
                ordered_grouped[category] = items

        return ordered_grouped

    except Exception as e:
        logger.error(f"Error getting grouped shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get shopping list: {str(e)}")


@router.post(
    "/parse-ingredients", response_model=List[ParsedIngredient], summary="Parse Ingredient Strings"
)
async def parse_ingredients(ingredients: List[str]):
    """
    Parse ingredient strings to extract quantities, units, and names.
    Useful for testing the parsing functionality.
    """
    try:
        parser = IngredientParserService()
        parsed = await parser.parse_ingredients_bulk(ingredients)

        result = []
        for i, parsed_item in enumerate(parsed):
            result.append(
                ParsedIngredient(
                    original_string=ingredients[i],
                    parsed_name=parsed_item.get("aggregatable", {}).get(
                        "name", parsed_item.get("name", "")
                    ),
                    quantity=parsed_item.get("aggregatable", {}).get(
                        "quantity", parsed_item.get("quantity", 0)
                    ),
                    unit=parsed_item.get("aggregatable", {}).get(
                        "unit", parsed_item.get("unit", "")
                    ),
                    category=parser._guess_category(parsed_item.get("name", "")),
                )
            )

        return result

    except Exception as e:
        logger.error(f"Error parsing ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse ingredients: {str(e)}")


@router.post(
    "/check-pantry-availability",
    response_model=Dict[str, Any],
    summary="Check Shopping List Against Pantry",
)
async def check_shopping_list_pantry_availability(
    user_id: int, db_service=Depends(get_database_service)
):
    """
    Check which shopping list items are already available in pantry.
    """
    try:
        # Get shopping list items
        shopping_query = """
        SELECT 
            sli.shopping_list_item_id,
            sli.item_name,
            sli.quantity as needed_quantity,
            sli.unit as needed_unit,
            sli.category
        FROM shopping_list_items sli
        WHERE sli.user_id = @user_id
        AND sli.is_checked = false
        """

        shopping_items = db_service.execute_query(shopping_query, {"user_id": user_id})

        # Get pantry items
        pantry_query = """
        SELECT 
            pi.product_name,
            pi.quantity,
            pi.unit_of_measurement,
            pi.expiration_date
        FROM pantry_items pi
        JOIN pantries p ON pi.pantry_id = p.pantry_id
        WHERE p.user_id = @user_id
        AND pi.quantity > 0
        AND pi.status = 'available'
        """

        pantry_items = db_service.execute_query(pantry_query, {"user_id": user_id})

        # Create lookup for pantry items
        pantry_lookup = {}
        for item in pantry_items:
            name = item["product_name"].lower()
            if name not in pantry_lookup:
                pantry_lookup[name] = []
            pantry_lookup[name].append(item)

        # Check availability
        available_items = []
        partially_available = []
        not_available = []

        for shopping_item in shopping_items:
            item_name_lower = shopping_item["item_name"].lower()
            found_in_pantry = False

            # Check exact match or partial match
            for pantry_name, pantry_entries in pantry_lookup.items():
                if item_name_lower in pantry_name or pantry_name in item_name_lower:
                    # Found a match
                    total_pantry_quantity = sum(entry["quantity"] for entry in pantry_entries)

                    if shopping_item["needed_unit"] == pantry_entries[0]["unit_of_measurement"]:
                        # Same unit, can compare directly
                        if total_pantry_quantity >= shopping_item["needed_quantity"]:
                            available_items.append(
                                {
                                    **shopping_item,
                                    "pantry_quantity": total_pantry_quantity,
                                    "status": "fully_available",
                                }
                            )
                        else:
                            partially_available.append(
                                {
                                    **shopping_item,
                                    "pantry_quantity": total_pantry_quantity,
                                    "status": "partially_available",
                                }
                            )
                    else:
                        # Different units, mark as partially available
                        partially_available.append(
                            {
                                **shopping_item,
                                "pantry_quantity": total_pantry_quantity,
                                "pantry_unit": pantry_entries[0]["unit_of_measurement"],
                                "status": "different_units",
                            }
                        )
                    found_in_pantry = True
                    break

            if not found_in_pantry:
                not_available.append({**shopping_item, "status": "not_in_pantry"})

        return {
            "fully_available": available_items,
            "partially_available": partially_available,
            "not_available": not_available,
            "summary": {
                "total_items": len(shopping_items),
                "fully_available_count": len(available_items),
                "partially_available_count": len(partially_available),
                "not_available_count": len(not_available),
            },
        }

    except Exception as e:
        logger.error(f"Error checking pantry availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check availability: {str(e)}")
