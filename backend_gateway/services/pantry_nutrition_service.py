"""
Pantry Nutrition Service
Provides nutritional information for pantry items using USDA data.
"""

import logging
from typing import Any, Optional

import asyncpg

from backend_gateway.services.usda_food_service import USDAFoodService

logger = logging.getLogger(__name__)


class PantryNutritionService:
    """Service for adding nutritional data to pantry items."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.usda_service = USDAFoodService(db_pool)

    async def get_pantry_nutrition_summary(self, user_id: int) -> dict[str, Any]:
        """
        Get nutritional summary of all items in user's pantry.

        Returns:
            Summary with total calories, protein, etc. for all pantry items
        """
        async with self.db_pool.acquire() as conn:
            # Get all pantry items with USDA mappings
            items = await conn.fetch(
                """
                SELECT
                    pi.id,
                    pi.name,
                    pi.quantity_amount,
                    pi.quantity_unit,
                    pum.fdc_id,
                    pum.confidence_score,
                    uf.serving_size,
                    uf.serving_size_unit
                FROM pantry_items pi
                JOIN pantries p ON pi.pantry_id = p.id
                LEFT JOIN pantry_item_usda_mapping pum ON pi.id = pum.pantry_item_id
                LEFT JOIN usda_foods uf ON pum.fdc_id = uf.fdc_id
                WHERE p.user_id = $1
                AND pi.is_consumed = false
                AND pi.expected_expiration > CURRENT_DATE
            """,
                user_id,
            )

            total_nutrition = {
                "calories": 0,
                "protein_g": 0,
                "fat_g": 0,
                "carbs_g": 0,
                "fiber_g": 0,
                "sugar_g": 0,
                "sodium_mg": 0,
            }

            items_with_nutrition = 0
            items_without_nutrition = 0

            for item in items:
                if item["fdc_id"]:
                    # Get nutritional info
                    nutrition = await self._get_item_nutrition(item["fdc_id"])

                    if nutrition:
                        # Calculate based on quantity
                        multiplier = self._calculate_serving_multiplier(
                            item["quantity_amount"],
                            item["quantity_unit"],
                            item["serving_size"],
                            item["serving_size_unit"],
                        )

                        for key in total_nutrition:
                            if key in nutrition:
                                total_nutrition[key] += nutrition[key] * multiplier

                        items_with_nutrition += 1
                    else:
                        items_without_nutrition += 1
                else:
                    items_without_nutrition += 1

            return {
                "total_items": len(items),
                "items_with_nutrition": items_with_nutrition,
                "items_without_nutrition": items_without_nutrition,
                "total_nutrition": {k: round(v, 2) for k, v in total_nutrition.items()},
                "daily_values": {
                    "calories_percent": round((total_nutrition["calories"] / 2000) * 100, 1),
                    "protein_percent": round((total_nutrition["protein_g"] / 50) * 100, 1),
                    "fat_percent": round((total_nutrition["fat_g"] / 65) * 100, 1),
                    "carbs_percent": round((total_nutrition["carbs_g"] / 300) * 100, 1),
                    "fiber_percent": round((total_nutrition["fiber_g"] / 25) * 100, 1),
                    "sodium_percent": round((total_nutrition["sodium_mg"] / 2300) * 100, 1),
                },
            }

    async def match_pantry_items_to_usda(
        self, user_id: int, auto_match: bool = True
    ) -> dict[str, Any]:
        """
        Match pantry items to USDA foods for nutritional data.

        Args:
            user_id: User ID
            auto_match: If True, automatically create matches above confidence threshold

        Returns:
            Summary of matching results
        """
        async with self.db_pool.acquire() as conn:
            # Get unmapped pantry items
            unmapped_items = await conn.fetch(
                """
                SELECT
                    pi.id,
                    pi.name,
                    pi.brand,
                    pi.barcode
                FROM pantry_items pi
                JOIN pantries p ON pi.pantry_id = p.id
                LEFT JOIN pantry_item_usda_mapping pum ON pi.id = pum.pantry_item_id
                WHERE p.user_id = $1
                AND pum.id IS NULL
                AND pi.is_consumed = false
            """,
                user_id,
            )

            matched_count = 0
            failed_count = 0
            results = []

            for item in unmapped_items:
                # Try to match
                matches = await self.usda_service.match_pantry_item(
                    name=item["name"], barcode=item["barcode"]
                )

                if matches and matches[0]["confidence_score"] > 0.7:
                    best_match = matches[0]

                    if auto_match:
                        # Create the mapping
                        success = await self.usda_service.link_pantry_item(
                            pantry_item_id=item["id"],
                            fdc_id=best_match["fdc_id"],
                            confidence_score=best_match["confidence_score"],
                            source=best_match["match_reason"],
                        )

                        if success:
                            matched_count += 1
                        else:
                            failed_count += 1

                    results.append(
                        {
                            "pantry_item": item["name"],
                            "matched_to": best_match["description"],
                            "confidence": best_match["confidence_score"],
                            "auto_matched": auto_match,
                        }
                    )
                else:
                    failed_count += 1
                    results.append(
                        {
                            "pantry_item": item["name"],
                            "matched_to": None,
                            "confidence": 0,
                            "auto_matched": False,
                        }
                    )

            return {
                "total_unmapped": len(unmapped_items),
                "matched": matched_count,
                "failed": failed_count,
                "auto_match_enabled": auto_match,
                "results": results[:20],  # Limit results for response size
            }

    async def get_item_nutrition_by_pantry_id(
        self, pantry_item_id: int
    ) -> Optional[dict[str, Any]]:
        """Get nutritional information for a specific pantry item."""

        nutrition = await self.usda_service.get_pantry_item_nutrition(pantry_item_id)

        if nutrition:
            # Format response
            return {
                "item_name": nutrition["description"],
                "confidence": nutrition["confidence_score"],
                "serving_size": nutrition["serving_size"],
                "serving_size_unit": nutrition["serving_size_unit"],
                "nutrients": {
                    n["name"]: {"amount": n["amount"], "unit": n["unit_name"]}
                    for n in nutrition["nutrients"]
                },
            }

        return None

    async def _get_item_nutrition(self, fdc_id: int) -> dict[str, float]:
        """Get simplified nutrition facts for calculations."""

        async with self.db_pool.acquire() as conn:
            # Get key nutrients
            nutrients = await conn.fetch(
                """
                SELECT
                    n.name,
                    fn.amount
                FROM usda_food_nutrients fn
                JOIN usda_nutrients n ON fn.nutrient_id = n.id
                WHERE fn.fdc_id = $1
                AND n.id IN (1008, 1003, 1004, 1005, 1079, 1235, 1093)
                -- calories, protein, fat, carbs, fiber, sugar, sodium
            """,
                fdc_id,
            )

            nutrition_map = {
                "Energy": "calories",
                "Protein": "protein_g",
                "Total lipid (fat)": "fat_g",
                "Carbohydrate, by difference": "carbs_g",
                "Fiber, total dietary": "fiber_g",
                "Sugars, total including NLEA": "sugar_g",
                "Sodium, Na": "sodium_mg",
            }

            result = {}
            for nutrient in nutrients:
                if nutrient["name"] in nutrition_map:
                    result[nutrition_map[nutrient["name"]]] = nutrient["amount"]

            return result

    def _calculate_serving_multiplier(
        self, quantity: float, unit: str, serving_size: Optional[float], serving_unit: Optional[str]
    ) -> float:
        """
        Calculate multiplier to convert item quantity to servings.

        This is simplified - a full implementation would need
        comprehensive unit conversion.
        """
        if not serving_size or not serving_unit:
            return 1.0

        # Simple same-unit comparison
        if unit and unit.lower() == serving_unit.lower():
            return quantity / serving_size

        # Common conversions
        conversions = {
            ("cup", "tablespoon"): 16,
            ("tablespoon", "teaspoon"): 3,
            ("pound", "ounce"): 16,
            ("kilogram", "gram"): 1000,
            ("liter", "milliliter"): 1000,
        }

        # Try to find conversion
        key = (unit.lower(), serving_unit.lower())
        if key in conversions:
            return (quantity * conversions[key]) / serving_size

        # Reverse conversion
        reverse_key = (serving_unit.lower(), unit.lower())
        if reverse_key in conversions:
            return quantity / (serving_size * conversions[reverse_key])

        # Default to 1:1 if we can't convert
        return quantity / serving_size if serving_size > 0 else 1.0
