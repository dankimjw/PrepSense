"""
Smart Unit Validator using USDA data
Fixes the core issue of inappropriate units for produce and other items.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple

import asyncpg

logger = logging.getLogger(__name__)


class SmartUnitValidator:
    """Validates and corrects units based on food categories and real-world usage."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

        # Define what units are appropriate for each food category
        self.category_unit_rules = {
            # Fresh produce - typically sold by weight or container
            "Produce": {
                "fruits": {
                    "allowed": [
                        "lb",
                        "oz",
                        "kg",
                        "g",
                        "each",
                        "pint",
                        "quart",
                        "basket",
                        "bag",
                        "container",
                    ],
                    "forbidden": ["ml", "l", "fl oz", "cup", "gallon"],
                    "preferred": ["lb", "oz", "each", "container"],
                    "examples": "strawberries sold by lb or pint container, not mL",
                },
                "vegetables": {
                    "allowed": ["lb", "oz", "kg", "g", "each", "bunch", "head", "bag", "package"],
                    "forbidden": ["ml", "l", "fl oz", "cup", "gallon"],
                    "preferred": ["lb", "oz", "each", "bunch"],
                    "examples": "carrots by lb, lettuce by head, celery by bunch",
                },
            },
            # Dairy - mostly volume but some by weight
            "Dairy and Egg Products": {
                "liquid_dairy": {
                    "allowed": [
                        "ml",
                        "l",
                        "fl oz",
                        "cup",
                        "pint",
                        "quart",
                        "gallon",
                        "bottle",
                        "carton",
                    ],
                    "forbidden": ["each", "slice"],
                    "preferred": ["gallon", "quart", "pint", "fl oz"],
                    "examples": "milk sold by gallon or quart, not each",
                },
                "solid_dairy": {
                    "allowed": ["oz", "lb", "g", "kg", "slice", "stick", "block", "package"],
                    "forbidden": ["ml", "l", "fl oz", "cup"],
                    "preferred": ["oz", "lb", "slice", "stick"],
                    "examples": "cheese by oz or slice, butter by stick",
                },
                "eggs": {
                    "allowed": ["each", "dozen", "carton"],
                    "forbidden": ["ml", "l", "oz", "lb"],
                    "preferred": ["dozen", "each"],
                    "examples": "eggs sold by dozen, not by weight",
                },
            },
            # Beverages - volume only
            "Beverages": {
                "default": {
                    "allowed": [
                        "ml",
                        "l",
                        "fl oz",
                        "cup",
                        "pint",
                        "quart",
                        "gallon",
                        "bottle",
                        "can",
                        "container",
                    ],
                    "forbidden": ["each", "slice", "oz", "lb"],
                    "preferred": ["bottle", "can", "gallon", "liter"],
                    "examples": "juice by bottle or gallon, soda by can",
                }
            },
            # Meat - weight based
            "Meat": {
                "default": {
                    "allowed": ["lb", "oz", "kg", "g", "piece", "slice", "package"],
                    "forbidden": ["ml", "l", "fl oz", "cup", "each"],
                    "preferred": ["lb", "oz", "piece"],
                    "examples": "ground beef by lb, chicken breast by piece",
                }
            },
            # Spices - small units only
            "Spices and Herbs": {
                "default": {
                    "allowed": ["tsp", "tbsp", "g", "oz", "container", "jar"],
                    "forbidden": ["lb", "kg", "l", "gallon", "each"],
                    "preferred": ["oz", "container", "jar"],
                    "examples": "spices sold in small containers, not by pound",
                }
            },
        }

        # Common OCR/input corrections
        self.unit_corrections = {
            "ea": "each",
            "pcs": "piece",
            "pc": "piece",
            "ct": "count",
            "pkg": "package",
            "cont": "container",
            "btl": "bottle",
            "cn": "can",
            "jar": "jar",
            "bag": "bag",
            "box": "box",
            "lbs": "lb",
            "ounce": "oz",
            "ounces": "oz",
            "pounds": "lb",
            "milliliter": "ml",
            "milliliters": "ml",
            "liter": "l",
            "liters": "l",
            "fluid_ounce": "fl oz",
            "teaspoon": "tsp",
            "tablespoon": "tbsp",
        }

        # Item-specific patterns for better detection
        self.item_patterns = {
            "strawberries": {"category": "Produce", "subcategory": "fruits"},
            "blueberries": {"category": "Produce", "subcategory": "fruits"},
            "raspberries": {"category": "Produce", "subcategory": "fruits"},
            "blackberries": {"category": "Produce", "subcategory": "fruits"},
            "grapes": {"category": "Produce", "subcategory": "fruits"},
            "apples": {"category": "Produce", "subcategory": "fruits"},
            "bananas": {"category": "Produce", "subcategory": "fruits"},
            "oranges": {"category": "Produce", "subcategory": "fruits"},
            "carrots": {"category": "Produce", "subcategory": "vegetables"},
            "celery": {"category": "Produce", "subcategory": "vegetables"},
            "lettuce": {"category": "Produce", "subcategory": "vegetables"},
            "spinach": {"category": "Produce", "subcategory": "vegetables"},
            "broccoli": {"category": "Produce", "subcategory": "vegetables"},
            "milk": {"category": "Dairy and Egg Products", "subcategory": "liquid_dairy"},
            "yogurt": {"category": "Dairy and Egg Products", "subcategory": "liquid_dairy"},
            "cheese": {"category": "Dairy and Egg Products", "subcategory": "solid_dairy"},
            "butter": {"category": "Dairy and Egg Products", "subcategory": "solid_dairy"},
            "eggs": {"category": "Dairy and Egg Products", "subcategory": "eggs"},
            "chicken": {"category": "Meat", "subcategory": "default"},
            "beef": {"category": "Meat", "subcategory": "default"},
            "pork": {"category": "Meat", "subcategory": "default"},
            "salt": {"category": "Spices and Herbs", "subcategory": "default"},
            "pepper": {"category": "Spices and Herbs", "subcategory": "default"},
            "cinnamon": {"category": "Spices and Herbs", "subcategory": "default"},
        }

    async def validate_and_suggest_unit(
        self, item_name: str, current_unit: str, quantity: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Validate unit and suggest corrections based on food category.

        Returns:
            {
                'is_valid': bool,
                'suggested_unit': str,
                'suggested_units': List[str],
                'reason': str,
                'category': str,
                'confidence': float
            }
        """
        # Clean and normalize inputs
        clean_item = item_name.lower().strip()
        clean_unit = self._normalize_unit(current_unit)

        # Detect food category
        category_info = await self._detect_food_category(clean_item)

        # Get unit rules for this category
        unit_rules = self._get_unit_rules(category_info)

        # Validate current unit
        is_valid = clean_unit in unit_rules.get("allowed", [])
        is_forbidden = clean_unit in unit_rules.get("forbidden", [])

        # Suggest better unit
        suggested_unit = self._suggest_best_unit(clean_item, clean_unit, unit_rules, quantity)

        # Build response
        result = {
            "is_valid": is_valid and not is_forbidden,
            "current_unit": clean_unit,
            "suggested_unit": suggested_unit,
            "suggested_units": unit_rules.get("preferred", []),
            "category": category_info.get("category", "Unknown"),
            "subcategory": category_info.get("subcategory", ""),
            "confidence": category_info.get("confidence", 0.5),
        }

        # Add explanation
        if is_forbidden:
            result["reason"] = (
                f"{item_name} cannot be measured in {clean_unit}. {unit_rules.get('examples', '')}"
            )
            result["severity"] = "error"
        elif not is_valid:
            result["reason"] = (
                f"Unusual unit for {item_name}. Consider: {', '.join(unit_rules.get('preferred', []))}"
            )
            result["severity"] = "warning"
        else:
            result["reason"] = f"Unit {clean_unit} is appropriate for {item_name}"
            result["severity"] = "info"

        return result

    async def bulk_validate_pantry(self, user_id: int) -> Dict[str, any]:
        """
        Validate all pantry items and find unit problems.
        """
        async with self.db_pool.acquire() as conn:
            # Get all pantry items
            items = await conn.fetch(
                """
                SELECT 
                    pi.id,
                    pi.name,
                    pi.quantity_amount,
                    pi.quantity_unit
                FROM pantry_items pi
                JOIN pantries p ON pi.pantry_id = p.id
                WHERE p.user_id = $1
                AND pi.is_consumed = false
            """,
                user_id,
            )

            validation_results = []
            error_count = 0
            warning_count = 0

            for item in items:
                validation = await self.validate_and_suggest_unit(
                    item["name"], item["quantity_unit"] or "each", item["quantity_amount"]
                )

                validation["pantry_item_id"] = item["id"]
                validation_results.append(validation)

                if validation["severity"] == "error":
                    error_count += 1
                elif validation["severity"] == "warning":
                    warning_count += 1

            return {
                "total_items": len(items),
                "errors": error_count,
                "warnings": warning_count,
                "valid_items": len(items) - error_count - warning_count,
                "validation_results": validation_results,
            }

    async def fix_pantry_units(self, user_id: int, auto_fix: bool = False) -> Dict[str, any]:
        """
        Fix unit issues in pantry items.
        """
        validation = await self.bulk_validate_pantry(user_id)

        fixed_count = 0
        fix_results = []

        async with self.db_pool.acquire() as conn:
            for result in validation["validation_results"]:
                if not result["is_valid"] and result["suggested_unit"]:
                    if auto_fix:
                        # Update the unit
                        await conn.execute(
                            """
                            UPDATE pantry_items 
                            SET quantity_unit = $1
                            WHERE id = $2
                        """,
                            result["suggested_unit"],
                            result["pantry_item_id"],
                        )

                        fixed_count += 1

                    fix_results.append(
                        {
                            "pantry_item_id": result["pantry_item_id"],
                            "old_unit": result["current_unit"],
                            "new_unit": result["suggested_unit"],
                            "fixed": auto_fix,
                        }
                    )

        return {
            "total_issues": len(fix_results),
            "fixed": fixed_count,
            "auto_fix_enabled": auto_fix,
            "fixes": fix_results,
        }

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit string."""
        if not unit:
            return "each"

        clean = unit.lower().strip()
        return self.unit_corrections.get(clean, clean)

    async def _detect_food_category(self, item_name: str) -> Dict[str, any]:
        """Detect food category for an item."""

        # Check specific patterns first
        for pattern, info in self.item_patterns.items():
            if pattern in item_name:
                return {**info, "confidence": 0.9}

        # Check broader patterns
        if any(berry in item_name for berry in ["berry", "berries"]):
            return {"category": "Produce", "subcategory": "fruits", "confidence": 0.8}

        if any(word in item_name for word in ["milk", "yogurt", "cream"]):
            return {
                "category": "Dairy and Egg Products",
                "subcategory": "liquid_dairy",
                "confidence": 0.8,
            }

        # Try USDA lookup if available
        try:
            async with self.db_pool.acquire() as conn:
                usda_match = await conn.fetchrow(
                    """
                    SELECT fc.description as category
                    FROM usda_foods uf
                    JOIN usda_food_categories fc ON uf.food_category_id = fc.id
                    WHERE uf.description ILIKE $1
                    LIMIT 1
                """,
                    f"%{item_name}%",
                )

                if usda_match:
                    category = usda_match["category"]
                    return {"category": category, "subcategory": "default", "confidence": 0.7}
        except Exception as e:
            logger.warning(f"USDA lookup failed: {e}")

        # Default
        return {"category": "Unknown", "subcategory": "default", "confidence": 0.3}

    def _get_unit_rules(self, category_info: Dict[str, any]) -> Dict[str, List[str]]:
        """Get unit rules for a food category."""

        category = category_info.get("category", "Unknown")
        subcategory = category_info.get("subcategory", "default")

        # Look up rules
        if category in self.category_unit_rules:
            if subcategory in self.category_unit_rules[category]:
                return self.category_unit_rules[category][subcategory]
            elif "default" in self.category_unit_rules[category]:
                return self.category_unit_rules[category]["default"]

        # Fallback - allow most units but prefer common ones
        return {
            "allowed": ["each", "lb", "oz", "g", "kg", "ml", "l", "cup", "package"],
            "forbidden": [],
            "preferred": ["each", "lb", "oz"],
            "examples": "Common units",
        }

    def _suggest_best_unit(
        self,
        item_name: str,
        current_unit: str,
        unit_rules: Dict[str, List[str]],
        quantity: Optional[float],
    ) -> str:
        """Suggest the best unit for an item."""

        preferred = unit_rules.get("preferred", [])
        allowed = unit_rules.get("allowed", [])

        # If current unit is good, keep it
        if current_unit in preferred:
            return current_unit

        # If current unit is allowed but not preferred, might suggest better
        if current_unit in allowed and preferred:
            return preferred[0]

        # If current unit is forbidden, suggest alternative
        if preferred:
            return preferred[0]
        elif allowed:
            return allowed[0]
        else:
            return "each"
