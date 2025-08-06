"""Enhanced Pantry Item Manager with Food Categorization Integration"""

import asyncio
import logging
import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from backend_gateway.services.food_database_service import FoodDatabaseService
from backend_gateway.services.pantry_item_manager import PantryItemManager
from backend_gateway.services.unit_validation_service import UnitValidationService

logger = logging.getLogger(__name__)


class PantryItemManagerEnhanced(PantryItemManager):
    """Enhanced pantry item manager that uses food categorization for better data quality."""

    def __init__(self, db_service):
        super().__init__(db_service)
        self.food_service = FoodDatabaseService(db_service)
        self.unit_service = UnitValidationService(db_service)

    async def add_items_batch_enhanced(
        self, user_id: int, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enhanced version that categorizes items and validates units before saving.

        Args:
            user_id: The user ID to add items for
            items: List of items with format:
                {
                    'item_name': str,
                    'quantity_amount': float,
                    'quantity_unit': str,
                    'expected_expiration': str,
                    'brand': str (optional),
                    'category': str (optional - will be auto-detected)
                }

        Returns:
            Dict with enhanced results including categorization info
        """
        start_time = datetime.now()

        # Get or create pantry
        pantry_id = self.get_or_create_pantry(user_id)

        # Process items with categorization
        enhanced_items = []
        categorization_errors = []

        logger.info(f"Starting categorization for {len(items)} items")

        # Categorize items in parallel for better performance
        categorization_tasks = []
        for item in items:
            task = self._process_item_with_categorization(item)
            categorization_tasks.append(task)

        # Wait for all categorizations to complete
        categorized_results = await asyncio.gather(*categorization_tasks, return_exceptions=True)

        # Process results
        for idx, result in enumerate(categorized_results):
            if isinstance(result, Exception):
                logger.error(f"Categorization error for {items[idx]['item_name']}: {str(result)}")
                categorization_errors.append(
                    {"item_name": items[idx]["item_name"], "error": str(result)}
                )
                # Still add the item with default values
                enhanced_items.append(items[idx])
            else:
                enhanced_items.append(result)

        # Now save the enhanced items using the parent method
        save_result = self.add_items_batch(user_id, enhanced_items)

        # Enhance the result with categorization info
        save_result["categorization_errors"] = categorization_errors
        save_result["enhanced_count"] = len(enhanced_items) - len(categorization_errors)

        total_time = (datetime.now() - start_time).total_seconds()
        save_result["total_time_with_categorization"] = total_time

        logger.info(f"Enhanced save completed in {total_time}s")

        return save_result

    async def _process_item_with_categorization(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single item with categorization and unit validation."""
        try:
            item_name = item.get("item_name", "")
            brand = item.get("brand")
            unit = item.get("quantity_unit", "each")
            quantity = item.get("quantity_amount", 1.0)

            # Step 1: Categorize the item
            categorization = await self.food_service.categorize_food_item(item_name, brand)

            # Step 2: Validate the unit
            unit_validation = await self.unit_service.validate_unit(item_name, unit, quantity)

            # Create enhanced item
            enhanced_item = item.copy()

            # Update category if not provided or if we have high confidence
            if not item.get("category") or categorization["confidence"] > 0.7:
                enhanced_item["category"] = categorization["category"]

            # Handle unit validation
            if not unit_validation["is_valid"]:
                # Log warning but don't block the save
                logger.warning(
                    f"Unit validation failed for {item_name}: {unit_validation['message']}"
                )

                # If we have suggestions and high confidence, use the primary suggestion
                if unit_validation.get("suggestions") and unit_validation["confidence"] > 0.8:
                    suggested_unit = unit_validation["suggestions"][0]

                    # Try to convert the quantity
                    conversion = await self.food_service.get_unit_conversions(
                        item_name, quantity, unit, suggested_unit
                    )

                    if conversion:
                        enhanced_item["quantity_unit"] = suggested_unit
                        enhanced_item["quantity_amount"] = conversion["targetAmount"]
                        enhanced_item["unit_corrected"] = True
                        enhanced_item["original_unit"] = unit
                        enhanced_item["original_quantity"] = quantity
                        logger.info(
                            f"Converted {quantity} {unit} to "
                            f"{conversion['targetAmount']} {suggested_unit} for {item_name}"
                        )

            # Add metadata
            enhanced_item["metadata"] = {
                "categorization_source": categorization.get("data_source"),
                "categorization_confidence": categorization.get("confidence"),
                "unit_validated": unit_validation["is_valid"],
                "processed_at": datetime.now().isoformat(),
            }

            # Add subcategory if available
            if categorization.get("subcategory"):
                enhanced_item["subcategory"] = categorization["subcategory"]

            return enhanced_item

        except Exception as e:
            logger.error(f"Error processing item {item.get('item_name')}: {str(e)}")
            # Return original item on error
            return item

    async def validate_and_fix_existing_items(
        self, user_id: int, fix_units: bool = True, fix_categories: bool = True
    ) -> Dict[str, Any]:
        """
        Validate and fix existing pantry items for a user.

        This method goes through existing items and:
        1. Validates their units
        2. Updates their categories if needed
        3. Records any corrections made
        """
        try:
            # Get existing items
            items = self.db_service.get_user_pantry_items(user_id)

            fixed_count = 0
            errors = []
            corrections = []

            for item in items:
                try:
                    item_name = item.get("product_name", "")
                    current_unit = item.get("unit_of_measurement", "each")
                    current_category = item.get("category", "Uncategorized")
                    pantry_item_id = item["pantry_item_id"]

                    updates_needed = {}

                    # Validate unit if requested
                    if fix_units:
                        unit_validation = await self.unit_service.validate_unit(
                            item_name, current_unit
                        )

                        if not unit_validation["is_valid"] and unit_validation.get("suggestions"):
                            # Use the first suggestion
                            new_unit = unit_validation["suggestions"][0]
                            updates_needed["unit_of_measurement"] = new_unit

                            corrections.append(
                                {
                                    "item_name": item_name,
                                    "correction_type": "unit",
                                    "old_value": current_unit,
                                    "new_value": new_unit,
                                    "reason": unit_validation["message"],
                                }
                            )

                    # Fix category if requested
                    if fix_categories and current_category in ["Uncategorized", "General", None]:
                        categorization = await self.food_service.categorize_food_item(item_name)

                        if categorization["confidence"] > 0.6:
                            updates_needed["category"] = categorization["category"]

                            corrections.append(
                                {
                                    "item_name": item_name,
                                    "correction_type": "category",
                                    "old_value": current_category,
                                    "new_value": categorization["category"],
                                    "confidence": categorization["confidence"],
                                }
                            )

                    # Apply updates if needed
                    if updates_needed:
                        update_query = """
                            UPDATE pantry_items
                            SET {updates}, updated_at = CURRENT_TIMESTAMP
                            WHERE pantry_item_id = %(pantry_item_id)s
                        """.format(
                            updates=", ".join([f"{k} = %({k})s" for k in updates_needed.keys()])
                        )

                        params = {"pantry_item_id": pantry_item_id, **updates_needed}
                        self.db_service.execute_query(update_query, params)

                        fixed_count += 1

                except Exception as e:
                    logger.error(f"Error fixing item {item.get('product_name')}: {str(e)}")
                    errors.append({"item_name": item.get("product_name"), "error": str(e)})

            return {
                "success": True,
                "total_items": len(items),
                "fixed_count": fixed_count,
                "error_count": len(errors),
                "corrections": corrections,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error in validate_and_fix_existing_items: {str(e)}")
            return {"success": False, "error": str(e)}

    async def smart_add_item(self, user_id: int, item_description: str) -> Dict[str, Any]:
        """
        Smart add that parses natural language item descriptions.

        Examples:
        - "2 pounds of chicken breast"
        - "Trader Joe's Cereal Bars"
        - "1 gallon of milk"
        - "dozen eggs"
        """
        try:
            # Parse the description
            parsed = self._parse_item_description(item_description)

            # Categorize the item
            categorization = await self.food_service.categorize_food_item(
                parsed["item_name"], parsed.get("brand")
            )

            # Validate the unit
            unit_validation = await self.unit_service.validate_unit(
                parsed["item_name"], parsed["unit"], parsed["quantity"]
            )

            # Build item object
            item_data = {
                "item_name": parsed["item_name"],
                "quantity_amount": parsed["quantity"],
                "quantity_unit": parsed["unit"],
                "category": categorization.category,
                "brand": parsed.get("brand", "Generic"),
                "expected_expiration": (datetime.now() + timedelta(days=30)).strftime("%m/%d/%Y"),
            }

            # Handle unit correction if needed
            if not unit_validation["is_valid"] and unit_validation.get("suggestions"):
                # Convert to suggested unit
                suggested_unit = unit_validation["suggestions"][0]
                conversion = await self.food_service.get_unit_conversions(
                    parsed["item_name"], parsed["quantity"], parsed["unit"], suggested_unit
                )

                if conversion:
                    item_data["quantity_unit"] = suggested_unit
                    item_data["quantity_amount"] = conversion["targetAmount"]
                    item_data["metadata"] = {
                        "original_description": item_description,
                        "unit_converted": True,
                        "original_unit": parsed["unit"],
                        "original_quantity": parsed["quantity"],
                    }

            # Add the item
            result = await self.add_items_batch_enhanced(user_id, [item_data])

            if result["saved_count"] > 0:
                return {
                    "success": True,
                    "item": result["saved_items"][0],
                    "parsed": parsed,
                    "categorization": categorization,
                    "message": f"Added {item_description} to pantry",
                }
            else:
                return {"success": False, "error": result.get("errors", ["Failed to add item"])[0]}

        except Exception as e:
            logger.error(f"Error in smart_add_item: {str(e)}")
            return {"success": False, "error": str(e)}

    def _parse_item_description(self, description: str) -> Dict[str, Any]:
        """Parse natural language item description."""
        import re

        # Default values
        result = {"quantity": 1.0, "unit": "each", "item_name": description, "brand": None}

        # Pattern for quantity + unit + item
        # Matches: "2 pounds of chicken", "1 gallon milk", "dozen eggs"
        pattern1 = r"^(\d+(?:\.\d+)?)\s+(\w+)\s+(?:of\s+)?(.+)$"
        match1 = re.match(pattern1, description, re.IGNORECASE)

        if match1:
            result["quantity"] = float(match1.group(1))
            result["unit"] = match1.group(2)
            result["item_name"] = match1.group(3)
        else:
            # Pattern for "dozen eggs" or "case of soda"
            pattern2 = r"^(dozen|case|box|package|bag)\s+(?:of\s+)?(.+)$"
            match2 = re.match(pattern2, description, re.IGNORECASE)

            if match2:
                result["quantity"] = 1.0
                result["unit"] = match2.group(1)
                result["item_name"] = match2.group(2)
            else:
                # Pattern for brand detection
                # Look for possessive (Trader Joe's) or common brand patterns
                brand_pattern = r"^([\w\s]+(?:'s)?)\s+(.+)$"
                brand_match = re.match(brand_pattern, description)

                if brand_match:
                    potential_brand = brand_match.group(1)
                    # Check if it looks like a brand (capitalized, possessive, etc.)
                    if potential_brand[0].isupper() and (
                        "'" in potential_brand
                        or potential_brand
                        in ["Trader Joe", "Great Value", "Kirkland", "Store Brand"]
                    ):
                        result["brand"] = potential_brand
                        result["item_name"] = brand_match.group(2)

        # Clean up item name
        result["item_name"] = result["item_name"].strip()

        # Normalize unit
        unit_service = UnitValidationService(self.db_service)
        result["unit"] = unit_service._normalize_unit(result["unit"])

        return result

    async def get_expiring_items(self, user_id: int, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get items expiring within specified days, with smart categorization."""
        query = """
            SELECT 
                pi.*,
                p.product_name,
                p.brand_name,
                p.category
            FROM pantry_items pi
            JOIN products p ON pi.pantry_item_id = p.pantry_item_id
            JOIN pantries pt ON pi.pantry_id = pt.pantry_id
            WHERE pt.user_id = %(user_id)s
            AND pi.status = 'available'
            AND pi.expiration_date <= CURRENT_DATE + INTERVAL '%(days)s days'
            AND pi.expiration_date >= CURRENT_DATE
            ORDER BY pi.expiration_date ASC
        """

        params = {"user_id": user_id, "days": days_ahead}

        items = self.db_service.execute_query(query, params)

        # Enhance with usage suggestions based on category
        for item in items:
            days_until_expiry = (item["expiration_date"] - date.today()).days
            item["days_until_expiry"] = days_until_expiry
            item["urgency"] = "high" if days_until_expiry <= 2 else "medium"

            # Add usage suggestions based on category
            item["usage_suggestions"] = self._get_usage_suggestions(
                item["category"], item["product_name"]
            )

        return items

    def _get_usage_suggestions(self, category: str, item_name: str) -> List[str]:
        """Get usage suggestions based on item category."""
        suggestions = {
            "produce_countable": [
                "Add to a salad",
                "Use in a smoothie",
                "Roast with other vegetables",
                "Add to a stir-fry",
            ],
            "produce_bulk": [
                "Make a salad",
                "Add to sandwiches",
                "Use in a smoothie",
                "Sauté as a side dish",
            ],
            "dairy": [
                "Use in baking",
                "Add to coffee or tea",
                "Make a sauce",
                "Use in breakfast dishes",
            ],
            "meat_seafood": [
                "Grill or pan-fry for dinner",
                "Add to pasta or rice dishes",
                "Use in meal prep",
                "Freeze for later use",
            ],
            "bread_bakery": [
                "Make sandwiches",
                "Toast for breakfast",
                "Use for French toast",
                "Make breadcrumbs if stale",
            ],
        }

        return suggestions.get(
            category, ["Use in a recipe", "Consume soon", "Consider freezing if possible"]
        )
