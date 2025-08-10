"""Service for handling recipe completion with unit conversion support"""

import logging
from typing import Any, Optional

from backend_gateway.constants.units import (
    UnitCategory,
    convert_quantity,
    get_unit_category,
    normalize_unit,
)

logger = logging.getLogger(__name__)


class RecipeCompletionService:
    """Handles recipe completion logic with unit conversion and smart matching"""

    @staticmethod
    def match_ingredient_to_pantry(
        ingredient_name: str, pantry_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Find matching pantry items for a recipe ingredient
        Returns list of matching items sorted by relevance
        """
        matching_items = []
        ingredient_lower = ingredient_name.lower().strip()

        for item in pantry_items:
            item_name_lower = item.get("product_name", "").lower().strip()

            # Score-based matching
            match_score = 0

            # Exact match
            if item_name_lower == ingredient_lower:
                match_score = 100
            # Ingredient is contained in item name
            elif ingredient_lower in item_name_lower:
                match_score = 80
            # Item name is contained in ingredient
            elif item_name_lower in ingredient_lower:
                match_score = 70
            # Singular/plural variations
            elif ingredient_lower.rstrip("s") == item_name_lower.rstrip(
                "s"
            ) or ingredient_lower.rstrip("es") == item_name_lower.rstrip("es"):
                match_score = 90
            # Common substitutions (could be expanded)
            elif RecipeCompletionService._are_substitutable(ingredient_lower, item_name_lower):
                match_score = 60

            if match_score > 0:
                item_copy = item.copy()
                item_copy["match_score"] = match_score
                matching_items.append(item_copy)

        # Sort by match score (descending) then by quantity (ascending for FIFO)
        matching_items.sort(key=lambda x: (-x["match_score"], x.get("quantity", 0)))

        return matching_items

    @staticmethod
    def _are_substitutable(ingredient1: str, ingredient2: str) -> bool:
        """Check if two ingredients are common substitutions"""
        substitutions = [
            {"whole milk", "2% milk", "milk", "low fat milk"},
            {"butter", "margarine"},
            {"sugar", "honey", "maple syrup"},
            {"vegetable oil", "canola oil", "olive oil", "cooking oil"},
        ]

        return any(ingredient1 in group and ingredient2 in group for group in substitutions)

    @staticmethod
    def calculate_quantity_to_use(
        needed_quantity: Optional[float],
        needed_unit: Optional[str],
        available_quantity: float,
        available_unit: str,
    ) -> tuple[Optional[float], str, dict[str, Any]]:
        """
        Calculate how much to subtract considering unit conversions

        Returns:
            - quantity_to_subtract (in pantry item's units)
            - unit_used
            - metadata (conversion info, warnings, etc.)
        """
        metadata = {
            "conversion_performed": False,
            "warnings": [],
            "original_needed": needed_quantity,
            "original_needed_unit": needed_unit,
            "pantry_unit": available_unit,
        }

        # If no quantity specified in recipe, use what's available
        if needed_quantity is None:
            return available_quantity, available_unit, metadata

        # Normalize units
        needed_unit_norm = normalize_unit(needed_unit) if needed_unit else None
        available_unit_norm = normalize_unit(available_unit)

        # If units are the same, simple subtraction
        if needed_unit_norm == available_unit_norm or not needed_unit:
            return min(needed_quantity, available_quantity), available_unit_norm, metadata

        # Try to convert units
        converted_quantity = convert_quantity(
            needed_quantity, needed_unit_norm, available_unit_norm
        )

        if converted_quantity is not None:
            metadata["conversion_performed"] = True
            metadata["converted_quantity"] = converted_quantity
            metadata["conversion_details"] = (
                f"{needed_quantity} {needed_unit} = {converted_quantity:.2f} {available_unit}"
            )
            return min(converted_quantity, available_quantity), available_unit_norm, metadata

        # Units can't be converted (different categories)
        needed_category = get_unit_category(needed_unit_norm)
        available_category = get_unit_category(available_unit_norm)

        if needed_category != available_category:
            metadata["warnings"].append(
                f"Cannot convert between {needed_unit} ({needed_category}) and "
                f"{available_unit} ({available_category}). Using approximate match."
            )

            # For count vs weight/volume, make educated guess
            if needed_category == UnitCategory.COUNT and available_category in [
                UnitCategory.WEIGHT,
                UnitCategory.VOLUME,
            ]:
                # e.g., "2 tomatoes" vs "500g tomatoes"
                # This would need ingredient-specific conversion tables
                metadata["warnings"].append(
                    "Count to weight/volume conversion requires ingredient-specific data"
                )
                return None, available_unit_norm, metadata

        # Same category but no conversion available
        metadata["warnings"].append(
            f"No conversion available between {needed_unit} and {available_unit}"
        )
        return None, available_unit_norm, metadata

    @staticmethod
    def process_ingredient_consumption(
        ingredient: dict[str, Any], matching_items: list[dict[str, Any]], db_service: Any
    ) -> dict[str, Any]:
        """
        Process consumption of a single ingredient from pantry

        Returns summary of what was consumed, what's missing, etc.
        """
        result = {
            "ingredient_name": ingredient["ingredient_name"],
            "requested_quantity": ingredient.get("quantity"),
            "requested_unit": ingredient.get("unit"),
            "consumed_items": [],
            "insufficient": False,
            "missing": False,
            "warnings": [],
        }

        if not matching_items:
            result["missing"] = True
            return result

        # Calculate total available across all matching items
        remaining_needed = ingredient.get("quantity", 0)
        remaining_needed_unit = ingredient.get("unit")

        for pantry_item in matching_items:
            if remaining_needed <= 0:
                break

            current_quantity = pantry_item.get("quantity", 0)
            pantry_unit = pantry_item.get("unit_of_measurement", "unit")

            if current_quantity <= 0:
                continue

            # Calculate how much to use from this item
            quantity_to_use, unit_used, conversion_meta = (
                RecipeCompletionService.calculate_quantity_to_use(
                    remaining_needed, remaining_needed_unit, current_quantity, pantry_unit
                )
            )

            if quantity_to_use is None:
                # Conversion failed
                result["warnings"].extend(conversion_meta.get("warnings", []))
                continue

            # Update the pantry item
            new_quantity = current_quantity - quantity_to_use

            try:
                update_query = """
                UPDATE pantry_items
                SET
                    quantity = %(new_quantity)s,
                    used_quantity = %(new_used_quantity)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE pantry_item_id = %(pantry_item_id)s
                """

                update_params = {
                    "new_quantity": new_quantity,
                    "new_used_quantity": (pantry_item.get("used_quantity", 0) or 0)
                    + quantity_to_use,
                    "pantry_item_id": pantry_item["pantry_item_id"],
                }

                db_service.execute_query(update_query, update_params)

                consumed_item = {
                    "pantry_item_id": pantry_item["pantry_item_id"],
                    "item_name": pantry_item["product_name"],
                    "quantity_used": quantity_to_use,
                    "unit": unit_used,
                    "previous_quantity": current_quantity,
                    "new_quantity": new_quantity,
                    "match_score": pantry_item.get("match_score", 0),
                }

                if conversion_meta.get("conversion_performed"):
                    consumed_item["conversion_details"] = conversion_meta.get("conversion_details")

                result["consumed_items"].append(consumed_item)

                # Update remaining needed
                if conversion_meta.get("conversion_performed"):
                    # If we converted, we need to track in original units
                    if remaining_needed and conversion_meta.get("converted_quantity"):
                        # Calculate how much of the original we consumed
                        proportion_used = quantity_to_use / conversion_meta["converted_quantity"]
                        original_consumed = remaining_needed * proportion_used
                        remaining_needed -= original_consumed
                else:
                    remaining_needed -= quantity_to_use

            except Exception as e:
                logger.error(
                    f"Error updating pantry item {pantry_item['pantry_item_id']}: {str(e)}"
                )
                result["warnings"].append(
                    f"Failed to update {pantry_item['product_name']}: {str(e)}"
                )

        # Check if we consumed enough
        if remaining_needed and remaining_needed > 0.01:  # Small tolerance for float arithmetic
            result["insufficient"] = True
            result["remaining_needed"] = remaining_needed
            result["remaining_needed_unit"] = remaining_needed_unit

        return result
