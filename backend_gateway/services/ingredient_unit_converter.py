"""
Ingredient-specific unit conversion service for common cooking ingredients.
This service provides conversions between different unit types (volume, weight, count)
for specific ingredients where such conversions are known and reliable.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class IngredientUnitConverter:
    """Service for converting between different unit types for specific ingredients."""

    def __init__(self):
        # Common ingredient conversion factors
        # Format: ingredient_name -> {(from_unit, to_unit): conversion_factor}
        self.conversion_factors = {
            "butter": {
                ("cup", "pound"): 0.5,  # 1 cup butter = 0.5 pounds
                ("pound", "cup"): 2.0,  # 1 pound butter = 2 cups
                ("cup", "gram"): 227,  # 1 cup butter = 227 grams
                ("gram", "cup"): 1 / 227,
                ("cup", "ounce"): 8,  # 1 cup butter = 8 ounces
                ("ounce", "cup"): 1 / 8,
            },
            "sugar": {
                ("cup", "gram"): 200,  # 1 cup granulated sugar = 200 grams
                ("gram", "cup"): 1 / 200,
                ("cup", "pound"): 0.44,  # 1 cup sugar = 0.44 pounds
                ("pound", "cup"): 1 / 0.44,
                ("cup", "ounce"): 7,  # 1 cup sugar = 7 ounces
                ("ounce", "cup"): 1 / 7,
            },
            "flour": {
                ("cup", "gram"): 120,  # 1 cup all-purpose flour = 120 grams
                ("gram", "cup"): 1 / 120,
                ("cup", "kilogram"): 0.12,  # 1 cup flour = 0.12 kg
                ("kilogram", "cup"): 1 / 0.12,
                ("cup", "ounce"): 4.25,  # 1 cup flour = 4.25 ounces
                ("ounce", "cup"): 1 / 4.25,
                ("cup", "pound"): 0.27,  # 1 cup flour = 0.27 pounds
                ("pound", "cup"): 1 / 0.27,
            },
            "salt": {
                ("teaspoon", "gram"): 6,  # 1 tsp salt = 6 grams
                ("gram", "teaspoon"): 1 / 6,
                ("tablespoon", "gram"): 18,  # 1 tbsp salt = 18 grams
                ("gram", "tablespoon"): 1 / 18,
                ("cup", "gram"): 288,  # 1 cup salt = 288 grams
                ("gram", "cup"): 1 / 288,
            },
            "milk": {
                ("cup", "milliliter"): 240,  # 1 cup milk = 240 ml
                ("milliliter", "cup"): 1 / 240,
                ("cup", "liter"): 0.24,  # 1 cup milk = 0.24 liters
                ("liter", "cup"): 1 / 0.24,
                ("cup", "ounce"): 8,  # 1 cup milk = 8 fl oz
                ("ounce", "cup"): 1 / 8,
            },
            "oil": {
                ("cup", "milliliter"): 240,  # 1 cup oil = 240 ml
                ("milliliter", "cup"): 1 / 240,
                ("cup", "liter"): 0.24,  # 1 cup oil = 0.24 liters
                ("liter", "cup"): 1 / 0.24,
                ("tablespoon", "milliliter"): 15,  # 1 tbsp oil = 15 ml
                ("milliliter", "tablespoon"): 1 / 15,
            },
            "eggs": {
                ("large", "each"): 1,  # 1 large egg = 1 egg
                ("each", "large"): 1,
                ("medium", "each"): 1,  # 1 medium egg = 1 egg
                ("each", "medium"): 1,
                ("small", "each"): 1,  # 1 small egg = 1 egg
                ("each", "small"): 1,
            },
            "rice": {
                ("cup", "gram"): 185,  # 1 cup uncooked rice = 185 grams
                ("gram", "cup"): 1 / 185,
                ("cup", "ounce"): 6.5,  # 1 cup rice = 6.5 ounces
                ("ounce", "cup"): 1 / 6.5,
            },
            "pasta": {
                ("cup", "gram"): 100,  # 1 cup dry pasta = 100 grams (approximate)
                ("gram", "cup"): 1 / 100,
                ("cup", "ounce"): 3.5,  # 1 cup pasta = 3.5 ounces
                ("ounce", "cup"): 1 / 3.5,
            },
        }

        # Unit normalization mapping
        self.unit_aliases = {
            "c": "cup",
            "cups": "cup",
            "tsp": "teaspoon",
            "teaspoons": "teaspoon",
            "tbsp": "tablespoon",
            "tablespoons": "tablespoon",
            "fl oz": "fluid ounce",
            "fluid ounces": "fluid ounce",
            "floz": "fluid ounce",
            "oz": "ounce",
            "ounces": "ounce",
            "lb": "pound",
            "lbs": "pound",
            "pounds": "pound",
            "g": "gram",
            "grams": "gram",
            "kg": "kilogram",
            "kilograms": "kilogram",
            "ml": "milliliter",
            "milliliters": "milliliter",
            "l": "liter",
            "liters": "liter",
            "ea": "each",
            "pcs": "piece",
            "pieces": "piece",
        }

    def normalize_unit(self, unit: str) -> str:
        """Normalize unit to standard form."""
        if not unit:
            return "unit"

        unit_lower = unit.lower().strip()
        return self.unit_aliases.get(unit_lower, unit_lower)

    def normalize_ingredient(self, ingredient_name: str) -> str:
        """Normalize ingredient name to match conversion factors."""
        if not ingredient_name:
            return ingredient_name

        ingredient_lower = ingredient_name.lower().strip()

        # Check for common ingredient patterns
        if any(word in ingredient_lower for word in ["butter", "margarine"]):
            return "butter"
        elif any(word in ingredient_lower for word in ["sugar", "granulated"]):
            return "sugar"
        elif any(word in ingredient_lower for word in ["flour", "all-purpose"]):
            return "flour"
        elif "salt" in ingredient_lower:
            return "salt"
        elif any(word in ingredient_lower for word in ["milk", "whole milk"]):
            return "milk"
        elif any(word in ingredient_lower for word in ["oil", "olive oil", "vegetable oil"]):
            return "oil"
        elif any(word in ingredient_lower for word in ["egg", "eggs"]):
            return "eggs"
        elif "rice" in ingredient_lower:
            return "rice"
        elif any(word in ingredient_lower for word in ["pasta", "spaghetti", "macaroni"]):
            return "pasta"

        return ingredient_name.lower()

    def convert_ingredient_unit(
        self, ingredient_name: str, from_amount: float, from_unit: str, to_unit: str
    ) -> dict[str, Any]:
        """
        Convert amount from one unit to another for a specific ingredient.

        Args:
            ingredient_name: Name of the ingredient
            from_amount: Amount in source unit
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Conversion result with success status and converted amount
        """
        try:
            # Normalize inputs
            normalized_ingredient = self.normalize_ingredient(ingredient_name)
            normalized_from_unit = self.normalize_unit(from_unit)
            normalized_to_unit = self.normalize_unit(to_unit)

            # Check if conversion is needed
            if normalized_from_unit == normalized_to_unit:
                return {
                    "success": True,
                    "converted_amount": from_amount,
                    "conversion_factor": 1.0,
                    "method": "same_unit",
                    "message": f"No conversion needed: {from_unit} = {to_unit}",
                }

            # Look up conversion factor
            if normalized_ingredient in self.conversion_factors:
                factors = self.conversion_factors[normalized_ingredient]
                conversion_key = (normalized_from_unit, normalized_to_unit)

                if conversion_key in factors:
                    factor = factors[conversion_key]
                    converted_amount = from_amount * factor

                    return {
                        "success": True,
                        "converted_amount": round(converted_amount, 3),
                        "conversion_factor": factor,
                        "method": "ingredient_specific",
                        "message": f"Converted {from_amount} {from_unit} to {converted_amount:.3f} {to_unit} for {ingredient_name}",
                    }

            # No conversion available
            return {
                "success": False,
                "converted_amount": from_amount,
                "conversion_factor": None,
                "method": "no_conversion",
                "message": f"No conversion available from {from_unit} to {to_unit} for {ingredient_name}",
            }

        except Exception as e:
            logger.error(f"Error converting units for {ingredient_name}: {str(e)}")
            return {
                "success": False,
                "converted_amount": from_amount,
                "conversion_factor": None,
                "method": "error",
                "message": f"Error during conversion: {str(e)}",
            }

    def suggest_best_unit(self, ingredient_name: str, current_unit: str) -> dict[str, Any]:
        """
        Suggest the best unit for an ingredient based on common cooking practices.

        Args:
            ingredient_name: Name of the ingredient
            current_unit: Current unit being used

        Returns:
            Suggestion with best unit and reasoning
        """
        normalized_ingredient = self.normalize_ingredient(ingredient_name)
        normalized_current = self.normalize_unit(current_unit)

        # Define best units for different ingredient types
        best_units = {
            "butter": ["cup", "tablespoon", "pound"],
            "sugar": ["cup", "tablespoon", "teaspoon"],
            "flour": ["cup", "tablespoon"],
            "salt": ["teaspoon", "tablespoon"],
            "milk": ["cup", "tablespoon", "teaspoon"],
            "oil": ["cup", "tablespoon", "teaspoon"],
            "eggs": ["each", "large", "medium"],
            "rice": ["cup"],
            "pasta": ["cup", "ounce"],
        }

        if normalized_ingredient in best_units:
            suggested_units = best_units[normalized_ingredient]
            best_unit = suggested_units[0]

            return {
                "current_unit": current_unit,
                "best_unit": best_unit,
                "alternatives": suggested_units,
                "is_optimal": normalized_current in suggested_units,
                "reasoning": f"For {ingredient_name}, {best_unit} is typically the most convenient unit for cooking",
            }

        return {
            "current_unit": current_unit,
            "best_unit": current_unit,
            "alternatives": [current_unit],
            "is_optimal": True,
            "reasoning": f"No specific recommendations for {ingredient_name}",
        }
