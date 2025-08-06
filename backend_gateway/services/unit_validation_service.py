"""
Enhanced Unit Validation Service for PrepSense
Provides comprehensive unit validation with special case handling
and intelligent suggestions based on food type.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend_gateway.constants.units import Unit, UnitCategory
from backend_gateway.services.food_database_service import FoodDatabaseService

logger = logging.getLogger(__name__)


class UnitValidationService:
    """Service for validating and suggesting appropriate units for food items."""

    def __init__(self, db_service):
        self.db_service = db_service
        self.food_db_service = FoodDatabaseService(db_service)

        # Define unit categories and their members
        self.unit_categories = {
            "volume_metric": ["milliliter", "liter"],
            "volume_imperial": [
                "teaspoon",
                "tablespoon",
                "fluid_ounce",
                "cup",
                "pint",
                "quart",
                "gallon",
            ],
            "weight_metric": ["milligram", "gram", "kilogram"],
            "weight_imperial": ["ounce", "pound"],
            "countable": ["each", "piece", "slice", "dozen"],
            "container": ["package", "bag", "box", "can", "jar", "bottle", "carton", "case"],
            "descriptive": ["small", "medium", "large", "bunch", "head", "clove"],
        }

        # Special validation rules
        self.validation_rules = {
            "solid_items_no_liquid": {
                "patterns": [r"\b(bar|cookie|chip|cracker|bread|cake|sandwich)\b"],
                "forbidden_units": self.unit_categories["volume_metric"]
                + self.unit_categories["volume_imperial"],
                "message": "Solid items like {item} cannot be measured in liquid units",
            },
            "liquid_items_no_each": {
                "patterns": [r"\b(milk|juice|oil|sauce|soup|broth)\b"],
                "forbidden_units": ["each"],
                "exceptions": ["bottle", "can", "carton", "jug"],
                "message": "Liquid items like {item} should use volume measurements unless counting containers",
            },
            "eggs_special": {
                "patterns": [r"\beggs?\b"],
                "allowed_units": ["each", "dozen", "carton", "large", "medium", "small"],
                "message": "Eggs are typically measured as 'each' or 'dozen'",
            },
            "spices_small_units": {
                "patterns": [r"\b(salt|pepper|spice|cinnamon|paprika|cumin|oregano)\b"],
                "preferred_units": ["teaspoon", "tablespoon", "gram", "pinch"],
                "message": "Spices like {item} are typically measured in small quantities",
            },
        }

    async def validate_unit(
        self, item_name: str, unit: str, quantity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive unit validation for a food item.

        Args:
            item_name: Name of the food item
            unit: Unit to validate
            quantity: Optional quantity for context

        Returns:
            Detailed validation result with suggestions
        """
        # Get food categorization
        food_categorization = await self.food_db_service.categorize_food_item(item_name)

        # Convert to dict if it's a dataclass
        if hasattr(food_categorization, "__dict__"):
            food_info = {
                "category": food_categorization.category,
                "allowed_units": food_categorization.allowed_units,
                "default_unit": food_categorization.default_unit,
                "confidence": food_categorization.confidence,
            }
        else:
            food_info = food_categorization

        logger.info(
            f"Food categorization for {item_name}: category={food_info.get('category')}, allowed_units={food_info.get('allowed_units')}"
        )

        # Normalize unit
        normalized_unit = self._normalize_unit(unit)

        # Apply special validation rules
        special_validation = self._apply_special_rules(item_name, normalized_unit, food_info)
        if special_validation:
            return special_validation

        # Check general validity
        validation_result = await self.food_db_service.validate_unit_for_item(
            item_name, normalized_unit
        )

        # Enhance with quantity context
        if quantity:
            validation_result = self._enhance_with_quantity_context(
                validation_result, item_name, normalized_unit, quantity
            )

        # Add conversion suggestions
        if not validation_result["is_valid"]:
            validation_result["conversions"] = await self._suggest_conversions(
                item_name, quantity or 1, unit, validation_result.get("suggestions", [])
            )

        return validation_result

    async def suggest_best_unit(
        self, item_name: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest the best unit for a food item based on context.

        Args:
            item_name: Name of the food item
            context: Optional context ('shopping', 'recipe', 'storage')

        Returns:
            Best unit suggestion with alternatives
        """
        # Get food categorization
        food_categorization = await self.food_db_service.categorize_food_item(item_name)

        # Convert to dict if it's a dataclass
        if hasattr(food_categorization, "__dict__"):
            category = food_categorization.category
        else:
            category = food_categorization.get("category", "general")

        # Get base suggestions
        suggestions = self._get_unit_suggestions_by_category(category, item_name)

        # Adjust based on context
        if context:
            suggestions = self._adjust_for_context(suggestions, context, category)

        # Get typical quantities
        typical_quantities = await self._get_typical_quantities(item_name, suggestions["primary"])

        return {
            "primary_unit": suggestions["primary"],
            "alternatives": suggestions["alternatives"],
            "typical_quantity": typical_quantities.get(suggestions["primary"]),
            "context": context,
            "confidence": food_info.get("confidence", 0.5),
            "reasoning": suggestions.get("reasoning", ""),
        }

    async def convert_unit(
        self, item_name: str, amount: float, from_unit: str, to_unit: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convert between units for a specific food item.

        Args:
            item_name: Name of the food item
            amount: Amount to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Conversion result or None if not possible
        """
        # Normalize units
        from_normalized = self._normalize_unit(from_unit)
        to_normalized = self._normalize_unit(to_unit)

        # Check if conversion makes sense
        validation = await self._validate_conversion(item_name, from_normalized, to_normalized)
        if not validation["is_valid"]:
            return {"error": validation["message"], "possible": False}

        # Try to get conversion
        conversion = await self.food_db_service.get_unit_conversions(
            item_name, amount, from_normalized, to_normalized
        )

        if conversion:
            conversion["validated"] = True
            return conversion

        # Try generic conversions for same category
        generic_conversion = self._get_generic_conversion(from_normalized, to_normalized, amount)

        if generic_conversion:
            generic_conversion["warning"] = (
                f"This is a generic conversion. Actual values may vary for {item_name}"
            )
            return generic_conversion

        return {
            "error": f"Cannot convert {from_unit} to {to_unit} for {item_name}",
            "possible": False,
        }

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit to standard form."""
        unit_lower = unit.lower().strip()

        # Comprehensive unit mappings
        mappings = {
            # Weight
            "g": "gram",
            "gr": "gram",
            "grams": "gram",
            "kg": "kilogram",
            "kilo": "kilogram",
            "kilos": "kilogram",
            "kilograms": "kilogram",
            "mg": "milligram",
            "milligrams": "milligram",
            "oz": "ounce",
            "ounces": "ounce",
            "lb": "pound",
            "lbs": "pound",
            "pounds": "pound",
            # Volume
            "ml": "milliliter",
            "milliliters": "milliliter",
            "millilitres": "milliliter",
            "l": "liter",
            "liters": "liter",
            "litres": "liter",
            "tsp": "teaspoon",
            "teaspoons": "teaspoon",
            "tbsp": "tablespoon",
            "tablespoons": "tablespoon",
            "tbs": "tablespoon",
            "fl oz": "fluid_ounce",
            "fluid oz": "fluid_ounce",
            "fluid ounces": "fluid_ounce",
            "c": "cup",
            "cups": "cup",
            "pt": "pint",
            "pints": "pint",
            "qt": "quart",
            "quarts": "quart",
            "gal": "gallon",
            "gallons": "gallon",
            # Countable
            "ea": "each",
            "pc": "piece",
            "pcs": "piece",
            "pieces": "piece",
            "doz": "dozen",
            "dozens": "dozen",
            # Containers
            "pkg": "package",
            "packages": "package",
            "pack": "package",
            "bags": "bag",
            "boxes": "box",
            "cans": "can",
            "jars": "jar",
            "bottles": "bottle",
            "cartons": "carton",
        }

        return mappings.get(unit_lower, unit_lower)

    def _apply_special_rules(
        self, item_name: str, unit: str, food_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply special validation rules."""
        item_lower = item_name.lower()

        for rule_name, rule in self.validation_rules.items():
            # Check if rule applies
            matches = any(re.search(pattern, item_lower) for pattern in rule["patterns"])
            if not matches:
                continue

            # Check forbidden units
            if "forbidden_units" in rule and unit in rule["forbidden_units"]:
                # Check exceptions
                if "exceptions" in rule:
                    if any(exc in item_lower for exc in rule["exceptions"]):
                        continue

                # Build suggestion list
                allowed = food_info.get("allowed_units", [])
                suggestions = [u for u in allowed if u not in rule["forbidden_units"]][:3]

                return {
                    "is_valid": False,
                    "normalized_unit": unit,
                    "allowed_units": allowed,
                    "suggestions": suggestions,
                    "message": rule["message"].format(item=item_name),
                    "rule_applied": rule_name,
                    "confidence": 0.9,
                }

            # Check allowed units (whitelist)
            if "allowed_units" in rule and unit not in rule["allowed_units"]:
                return {
                    "is_valid": False,
                    "normalized_unit": unit,
                    "allowed_units": rule["allowed_units"],
                    "suggestions": rule["allowed_units"][:3],
                    "message": rule["message"].format(item=item_name),
                    "rule_applied": rule_name,
                    "confidence": 0.9,
                }

            # Check preferred units (soft recommendation)
            if "preferred_units" in rule and unit not in rule["preferred_units"]:
                # This is a warning, not an error
                return {
                    "is_valid": True,
                    "normalized_unit": unit,
                    "allowed_units": food_info.get("allowed_units", []),
                    "suggestions": rule["preferred_units"][:3],
                    "message": rule["message"].format(item=item_name),
                    "warning": True,
                    "rule_applied": rule_name,
                    "confidence": 0.7,
                }

        return None

    def _enhance_with_quantity_context(
        self, validation_result: Dict[str, Any], item_name: str, unit: str, quantity: float
    ) -> Dict[str, Any]:
        """Enhance validation with quantity context."""
        # Check for unreasonable quantities
        warnings = []

        # Weight checks
        if unit in ["gram", "kilogram", "ounce", "pound"]:
            if unit == "gram" and quantity > 5000:
                warnings.append(f"{quantity} grams is quite large. Consider using kilograms.")
            elif unit == "kilogram" and quantity < 0.1:
                warnings.append(f"{quantity} kilograms is quite small. Consider using grams.")
            elif unit == "pound" and quantity > 100:
                warnings.append(f"{quantity} pounds seems excessive for {item_name}.")

        # Volume checks
        elif unit in ["milliliter", "liter", "cup", "gallon"]:
            if unit == "milliliter" and quantity > 2000:
                warnings.append(f"{quantity} milliliters is quite large. Consider using liters.")
            elif unit == "liter" and quantity < 0.1:
                warnings.append(f"{quantity} liters is quite small. Consider using milliliters.")
            elif unit == "gallon" and quantity > 10:
                warnings.append(f"{quantity} gallons seems excessive for {item_name}.")

        # Countable checks
        elif unit == "each" and quantity > 100:
            warnings.append(f"{quantity} items seems like a lot. Consider using cases or boxes.")

        if warnings:
            validation_result["quantity_warnings"] = warnings

        return validation_result

    async def _suggest_conversions(
        self, item_name: str, amount: float, from_unit: str, to_units: List[str]
    ) -> List[Dict[str, Any]]:
        """Suggest conversions to recommended units."""
        conversions = []

        for to_unit in to_units[:3]:  # Limit to top 3 suggestions
            conversion = await self.food_db_service.get_unit_conversions(
                item_name, amount, from_unit, to_unit
            )

            if conversion:
                conversions.append(
                    {
                        "to_unit": to_unit,
                        "amount": conversion.get("targetAmount", amount),
                        "display": f"{amount} {from_unit} ≈ {conversion.get('targetAmount', amount):.2f} {to_unit}",
                    }
                )

        return conversions

    def _get_unit_suggestions_by_category(self, category: str, item_name: str) -> Dict[str, Any]:
        """Get unit suggestions based on food category."""
        suggestions = {
            "produce_countable": {
                "primary": "each",
                "alternatives": ["pound", "kilogram"],
                "reasoning": "Countable produce is typically sold by unit",
            },
            "produce_bulk": {
                "primary": "pound",
                "alternatives": ["kilogram", "cup", "bunch"],
                "reasoning": "Bulk produce is typically sold by weight",
            },
            "dairy": {
                "primary": "cup",
                "alternatives": ["liter", "milliliter", "each"],
                "reasoning": "Dairy products use volume or container measurements",
            },
            "meat_seafood": {
                "primary": "pound",
                "alternatives": ["kilogram", "each", "ounce"],
                "reasoning": "Meat and seafood are typically sold by weight",
            },
            "dry_goods": {
                "primary": "cup",
                "alternatives": ["pound", "gram", "bag"],
                "reasoning": "Dry goods can use volume or weight measurements",
            },
            "bread_bakery": {
                "primary": "each",
                "alternatives": ["loaf", "slice", "package"],
                "reasoning": "Bakery items are typically counted",
            },
            "beverages": {
                "primary": "liter",
                "alternatives": ["bottle", "can", "cup"],
                "reasoning": "Beverages use volume or container measurements",
            },
            "snacks": {
                "primary": "package",
                "alternatives": ["each", "bag", "ounce"],
                "reasoning": "Snacks are typically sold in packages",
            },
            "condiments": {
                "primary": "cup",
                "alternatives": ["tablespoon", "milliliter", "each"],
                "reasoning": "Condiments use small volume measurements",
            },
        }

        default = {
            "primary": "each",
            "alternatives": ["pound", "package", "cup"],
            "reasoning": "Default units for uncategorized items",
        }

        return suggestions.get(category, default)

    def _adjust_for_context(
        self, suggestions: Dict[str, Any], context: str, category: str
    ) -> Dict[str, Any]:
        """Adjust unit suggestions based on usage context."""
        if context == "shopping":
            # Prefer units commonly used in stores
            if category == "produce_bulk":
                suggestions["primary"] = "pound"
            elif category in ["dairy", "beverages"]:
                if "gallon" in suggestions["alternatives"]:
                    suggestions["primary"] = "gallon"

        elif context == "recipe":
            # Prefer precise measurements for recipes
            if category == "dry_goods":
                suggestions["primary"] = "cup"
                suggestions["alternatives"] = ["tablespoon", "teaspoon", "gram"]
            elif category == "dairy":
                suggestions["primary"] = "cup"
                suggestions["alternatives"] = ["tablespoon", "milliliter"]

        elif context == "storage":
            # Prefer container units for storage
            if "package" in suggestions["alternatives"]:
                suggestions["primary"] = "package"
            elif "bag" in suggestions["alternatives"]:
                suggestions["primary"] = "bag"

        return suggestions

    async def _get_typical_quantities(self, item_name: str, unit: str) -> Dict[str, float]:
        """Get typical quantities for an item in different units."""
        # This would query historical data or use predefined values
        # For now, return common quantities
        typical = {
            "each": {"banana": 1, "apple": 1, "egg": 12, "bread": 1},
            "pound": {"chicken": 2, "beef": 1, "apples": 3, "grapes": 1},
            "cup": {"milk": 2, "flour": 2, "sugar": 1, "rice": 1},
            "package": {"cookies": 1, "crackers": 1, "cereal bars": 1},
        }

        item_lower = item_name.lower()
        for key in typical.get(unit, {}):
            if key in item_lower:
                return {unit: typical[unit][key]}

        # Default quantities
        defaults = {"each": 1, "pound": 1, "kilogram": 0.5, "cup": 1, "liter": 1, "package": 1}

        return {unit: defaults.get(unit, 1)}

    async def _validate_conversion(
        self, item_name: str, from_unit: str, to_unit: str
    ) -> Dict[str, bool]:
        """Validate if a conversion makes sense."""
        # Get unit categories
        from_category = self._get_unit_category(from_unit)
        to_category = self._get_unit_category(to_unit)

        # Can't convert between incompatible categories
        incompatible = [
            ("volume_metric", "countable"),
            ("volume_imperial", "countable"),
            ("weight_metric", "countable"),
            ("weight_imperial", "countable"),
        ]

        if (from_category, to_category) in incompatible or (
            to_category,
            from_category,
        ) in incompatible:
            return {
                "is_valid": False,
                "message": f"Cannot convert {from_unit} (${from_category}) to {to_unit} ({to_category})",
            }

        # Special case: volume to weight needs density
        if (from_category.startswith("volume") and to_category.startswith("weight")) or (
            from_category.startswith("weight") and to_category.startswith("volume")
        ):
            return {
                "is_valid": True,
                "message": f"Conversion requires density information for {item_name}",
            }

        return {"is_valid": True, "message": "Conversion possible"}

    def _get_unit_category(self, unit: str) -> Optional[str]:
        """Get the category of a unit."""
        for category, units in self.unit_categories.items():
            if unit in units:
                return category
        return None

    def _get_generic_conversion(
        self, from_unit: str, to_unit: str, amount: float
    ) -> Optional[Dict[str, Any]]:
        """Get generic conversions that don't depend on the item."""
        # Weight conversions
        weight_conversions = {
            ("gram", "kilogram"): 0.001,
            ("gram", "ounce"): 0.035274,
            ("gram", "pound"): 0.00220462,
            ("kilogram", "gram"): 1000,
            ("kilogram", "pound"): 2.20462,
            ("kilogram", "ounce"): 35.274,
            ("ounce", "gram"): 28.3495,
            ("ounce", "pound"): 0.0625,
            ("pound", "ounce"): 16,
            ("pound", "gram"): 453.592,
            ("pound", "kilogram"): 0.453592,
        }

        # Volume conversions
        volume_conversions = {
            ("milliliter", "liter"): 0.001,
            ("milliliter", "cup"): 0.00422675,
            ("milliliter", "fluid_ounce"): 0.033814,
            ("liter", "milliliter"): 1000,
            ("liter", "cup"): 4.22675,
            ("liter", "gallon"): 0.264172,
            ("cup", "milliliter"): 236.588,
            ("cup", "liter"): 0.236588,
            ("cup", "fluid_ounce"): 8,
            ("cup", "tablespoon"): 16,
            ("tablespoon", "teaspoon"): 3,
            ("tablespoon", "milliliter"): 14.7868,
            ("teaspoon", "milliliter"): 4.92892,
            ("gallon", "liter"): 3.78541,
            ("gallon", "cup"): 16,
        }

        # Combine all conversions
        all_conversions = {**weight_conversions, **volume_conversions}

        if (from_unit, to_unit) in all_conversions:
            factor = all_conversions[(from_unit, to_unit)]
            return {
                "sourceAmount": amount,
                "sourceUnit": from_unit,
                "targetAmount": round(amount * factor, 3),
                "targetUnit": to_unit,
                "type": "generic_conversion",
            }

        return None
