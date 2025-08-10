"""Service for parsing and normalizing ingredient quantities and units"""

import logging
import re
from fractions import Fraction
from typing import Any

import httpx

from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)


class IngredientParserService:
    """Service for parsing ingredient strings into structured data"""

    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        if not self.api_key:
            # Try to read from file as fallback
            try:
                with open("config/spoonacular_key.txt") as f:
                    self.api_key = f.read().strip()
            except FileNotFoundError:
                logger.warning("Spoonacular API key not found")

        self.base_url = "https://api.spoonacular.com"

        # Common unit conversions to standardize
        self.unit_conversions = {
            # Volume
            "tsp": "teaspoon",
            "tsps": "teaspoon",
            "teaspoons": "teaspoon",
            "tbsp": "tablespoon",
            "tbsps": "tablespoon",
            "tablespoons": "tablespoon",
            "c": "cup",
            "cups": "cup",
            "pt": "pint",
            "pts": "pint",
            "pints": "pint",
            "qt": "quart",
            "qts": "quart",
            "quarts": "quart",
            "gal": "gallon",
            "gallons": "gallon",
            "ml": "milliliter",
            "l": "liter",
            # Weight
            "oz": "ounce",
            "ounces": "ounce",
            "lb": "pound",
            "lbs": "pound",
            "pounds": "pound",
            "g": "gram",
            "grams": "gram",
            "kg": "kilogram",
            "kilograms": "kilogram",
            # Count
            "pcs": "piece",
            "pieces": "piece",
            "items": "item",
            "cloves": "clove",
            "heads": "head",
            "bunches": "bunch",
            "sprigs": "sprig",
            "leaves": "leaf",
            "slices": "slice",
            # Other
            "pkg": "package",
            "pkgs": "package",
            "packages": "package",
            "can": "can",
            "cans": "can",
            "jar": "jar",
            "jars": "jar",
            "bottle": "bottle",
            "bottles": "bottle",
            "box": "box",
            "boxes": "box",
        }

        # Volume conversions to cups (for aggregation)
        self.to_cups = {
            "teaspoon": 1 / 48,
            "tablespoon": 1 / 16,
            "cup": 1,
            "pint": 2,
            "quart": 4,
            "gallon": 16,
            "milliliter": 0.00422675,
            "liter": 4.22675,
        }

        # Weight conversions to grams (for aggregation)
        self.to_grams = {"ounce": 28.3495, "pound": 453.592, "gram": 1, "kilogram": 1000}

    async def parse_ingredients_bulk(self, ingredient_strings: list[str]) -> list[dict[str, Any]]:
        """
        Parse multiple ingredient strings using Spoonacular API

        Args:
            ingredient_strings: List of ingredient strings like "1/2 cup sugar"

        Returns:
            List of parsed ingredient data
        """
        if not self.api_key:
            # Fallback to local parsing
            return [self._parse_ingredient_locally(ing) for ing in ingredient_strings]

        try:
            async with httpx.AsyncClient() as client:
                # Spoonacular's parseIngredients endpoint
                response = await client.post(
                    f"{self.base_url}/recipes/parseIngredients",
                    params={"apiKey": self.api_key},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"ingredientList": "\n".join(ingredient_strings), "servings": 1},
                )

                if response.status_code == 200:
                    parsed_data = response.json()

                    # Enhance with local parsing for better aggregation
                    for i, ingredient in enumerate(parsed_data):
                        ingredient["original_string"] = ingredient_strings[i]
                        ingredient["aggregatable"] = self._enhance_parsed_data(ingredient)

                    return parsed_data
                else:
                    logger.warning(f"Spoonacular API error: {response.status_code}")
                    # Fallback to local parsing
                    return [self._parse_ingredient_locally(ing) for ing in ingredient_strings]

        except Exception as e:
            logger.error(f"Error calling Spoonacular parseIngredients: {e}")
            # Fallback to local parsing
            return [self._parse_ingredient_locally(ing) for ing in ingredient_strings]

    def _parse_ingredient_locally(self, ingredient_string: str) -> dict[str, Any]:
        """
        Parse ingredient string locally without API

        Args:
            ingredient_string: String like "1/2 cup sugar" or "1/4 tsp + 3 tbsp flour"

        Returns:
            Parsed ingredient data
        """
        # Pattern to match quantities and units
        # Handles fractions, decimals, ranges, and additions
        quantity_pattern = r"(\d+\/\d+|\d+\.\d+|\d+)\s*(?:to|-)\s*(\d+\/\d+|\d+\.\d+|\d+)?"
        unit_pattern = r"([a-zA-Z]+\.?)"

        # Look for quantity + unit patterns
        matches = re.findall(f"{quantity_pattern}\\s*{unit_pattern}", ingredient_string)

        total_quantity = 0
        unit = None
        name = ingredient_string

        if matches:
            # Process all quantity/unit pairs (for additions like "1/4 cup + 2 tbsp")
            quantities_by_unit = {}

            for match in matches:
                qty_str = match[0]
                qty_str2 = match[1]  # For ranges
                unit_str = match[2]

                # Parse quantity
                quantity = float(Fraction(qty_str)) if "/" in qty_str else float(qty_str)

                # Handle ranges (take average)
                if qty_str2:
                    quantity2 = float(Fraction(qty_str2)) if "/" in qty_str2 else float(qty_str2)
                    quantity = (quantity + quantity2) / 2

                # Normalize unit
                normalized_unit = self._normalize_unit(unit_str.lower())

                if normalized_unit not in quantities_by_unit:
                    quantities_by_unit[normalized_unit] = 0
                quantities_by_unit[normalized_unit] += quantity

                # Remove the matched part from the name
                name = name.replace(match[0] + " " + match[2], "")
                if match[1]:  # Range
                    name = name.replace(" " + match[1], "")

            # Convert all to common unit if possible
            if quantities_by_unit:
                unit, total_quantity = self._aggregate_quantities(quantities_by_unit)

            # Clean up the ingredient name
            name = re.sub(r"\s+", " ", name).strip()
            # Remove leading/trailing punctuation
            name = name.strip(",-+ ")

        return {
            "name": name,
            "quantity": total_quantity,
            "unit": unit,
            "original_string": ingredient_string,
            "aggregatable": {
                "quantity": total_quantity,
                "unit": unit,
                "name": self._normalize_ingredient_name(name),
            },
        }

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit to standard form"""
        unit = unit.lower().strip(".")
        return self.unit_conversions.get(unit, unit)

    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalize ingredient name for matching"""
        # Remove common descriptors
        descriptors = [
            "fresh",
            "frozen",
            "canned",
            "dried",
            "chopped",
            "diced",
            "sliced",
            "minced",
            "crushed",
            "ground",
            "whole",
            "large",
            "small",
            "medium",
            "ripe",
            "raw",
            "cooked",
            "peeled",
            "seedless",
            "boneless",
            "skinless",
            "lean",
            "extra virgin",
            "virgin",
            "pure",
            "organic",
            "unsalted",
            "salted",
            "sweetened",
            "unsweetened",
            "low-fat",
            "fat-free",
            "all-purpose",
            "self-rising",
            "instant",
            "quick",
            "old-fashioned",
        ]

        normalized = name.lower()
        for descriptor in descriptors:
            normalized = normalized.replace(descriptor, "").strip()

        # Remove extra spaces
        normalized = " ".join(normalized.split())

        # Handle common variations
        variations = {
            "sugar": ["granulated sugar", "white sugar"],
            "brown sugar": ["light brown sugar", "dark brown sugar"],
            "flour": ["all purpose flour", "all-purpose flour", "ap flour"],
            "butter": ["unsalted butter", "salted butter"],
            "oil": ["vegetable oil", "cooking oil", "neutral oil"],
            "milk": ["whole milk", "2% milk", "skim milk"],
            "cream": ["heavy cream", "whipping cream", "heavy whipping cream"],
            "cheese": ["shredded cheese", "grated cheese"],
            "chicken": ["chicken breast", "chicken breasts", "chicken thighs"],
            "beef": ["ground beef", "beef chuck", "beef sirloin"],
            "tomatoes": ["tomato", "diced tomatoes", "crushed tomatoes"],
            "onion": ["onions", "yellow onion", "white onion"],
            "garlic": ["garlic clove", "garlic cloves"],
            "pepper": ["bell pepper", "peppers"],
            "salt": ["table salt", "sea salt", "kosher salt"],
        }

        for base, variants in variations.items():
            if normalized in variants:
                return base

        return normalized

    def _aggregate_quantities(self, quantities_by_unit: dict[str, float]) -> tuple[str, float]:
        """
        Aggregate quantities with different units to a common unit

        Args:
            quantities_by_unit: Dict of unit -> quantity

        Returns:
            Tuple of (common_unit, total_quantity)
        """
        # Separate by measurement type
        volume_units = set(self.to_cups.keys())
        weight_units = set(self.to_grams.keys())

        has_volume = any(unit in volume_units for unit in quantities_by_unit)
        has_weight = any(unit in weight_units for unit in quantities_by_unit)

        if has_volume and not has_weight:
            # Convert all to cups
            total_cups = 0
            for unit, qty in quantities_by_unit.items():
                if unit in self.to_cups:
                    total_cups += qty * self.to_cups[unit]
                else:
                    # Can't convert, just return the first unit/quantity
                    return list(quantities_by_unit.items())[0]

            # Convert back to appropriate unit
            if total_cups >= 4:
                return ("quart", total_cups / 4)
            elif total_cups >= 1:
                return ("cup", total_cups)
            elif total_cups >= 1 / 16:
                return ("tablespoon", total_cups * 16)
            else:
                return ("teaspoon", total_cups * 48)

        elif has_weight and not has_volume:
            # Convert all to grams
            total_grams = 0
            for unit, qty in quantities_by_unit.items():
                if unit in self.to_grams:
                    total_grams += qty * self.to_grams[unit]
                else:
                    # Can't convert, just return the first unit/quantity
                    return list(quantities_by_unit.items())[0]

            # Convert back to appropriate unit
            if total_grams >= 1000:
                return ("kilogram", total_grams / 1000)
            elif total_grams >= 453.592:
                return ("pound", total_grams / 453.592)
            elif total_grams >= 28.3495:
                return ("ounce", total_grams / 28.3495)
            else:
                return ("gram", total_grams)

        else:
            # Mixed or no standard units, return the first one
            return list(quantities_by_unit.items())[0] if quantities_by_unit else (None, 0)

    def _enhance_parsed_data(self, parsed_ingredient: dict[str, Any]) -> dict[str, Any]:
        """
        Enhance Spoonacular parsed data with aggregation info

        Args:
            parsed_ingredient: Data from Spoonacular API

        Returns:
            Enhanced aggregation data
        """
        # Extract relevant fields from Spoonacular response
        name = parsed_ingredient.get("name", "")
        amount = parsed_ingredient.get("amount", 0)
        unit = parsed_ingredient.get("unit", "")

        # Normalize for aggregation
        normalized_unit = self._normalize_unit(unit)
        normalized_name = self._normalize_ingredient_name(name)

        return {"quantity": amount, "unit": normalized_unit, "name": normalized_name}

    def aggregate_ingredients(self, ingredients: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Aggregate ingredients with the same name

        Args:
            ingredients: List of parsed ingredients

        Returns:
            Aggregated list of ingredients
        """
        from collections import defaultdict

        # Group by normalized name
        grouped = defaultdict(list)

        for ingredient in ingredients:
            agg_data = ingredient.get("aggregatable", {})
            if agg_data and agg_data.get("name"):
                grouped[agg_data["name"]].append(agg_data)

        # Aggregate each group
        aggregated = []
        for name, group in grouped.items():
            if len(group) == 1:
                # Single item, no aggregation needed
                aggregated.append(
                    {
                        "item_name": name,
                        "quantity": group[0].get("quantity", 0),
                        "unit": group[0].get("unit", "unit"),
                        "category": self._guess_category(name),
                    }
                )
            else:
                # Multiple items, need to aggregate
                quantities_by_unit = {}
                for item in group:
                    unit = item.get("unit", "unit")
                    qty = item.get("quantity", 0)
                    if unit not in quantities_by_unit:
                        quantities_by_unit[unit] = 0
                    quantities_by_unit[unit] += qty

                # Try to convert to common unit
                unit, total_quantity = self._aggregate_quantities(quantities_by_unit)

                aggregated.append(
                    {
                        "item_name": name,
                        "quantity": round(total_quantity, 2) if total_quantity else 0,
                        "unit": unit or "unit",
                        "category": self._guess_category(name),
                    }
                )

        return aggregated

    def _guess_category(self, ingredient_name: str) -> str:
        """Guess the category of an ingredient based on its name"""
        categories = {
            "Produce": [
                "tomato",
                "onion",
                "garlic",
                "pepper",
                "carrot",
                "celery",
                "lettuce",
                "spinach",
                "broccoli",
                "cauliflower",
                "potato",
                "apple",
                "banana",
                "orange",
                "lemon",
                "lime",
                "berry",
                "corn",
                "bean",
                "pea",
                "squash",
                "zucchini",
                "cucumber",
            ],
            "Dairy": [
                "milk",
                "cheese",
                "butter",
                "yogurt",
                "cream",
                "sour cream",
                "cottage cheese",
                "ice cream",
            ],
            "Meat": [
                "chicken",
                "beef",
                "pork",
                "turkey",
                "lamb",
                "bacon",
                "sausage",
                "ham",
                "ground beef",
                "steak",
            ],
            "Seafood": [
                "fish",
                "salmon",
                "tuna",
                "shrimp",
                "crab",
                "lobster",
                "scallop",
                "tilapia",
                "cod",
            ],
            "Grains": [
                "rice",
                "pasta",
                "bread",
                "flour",
                "oat",
                "quinoa",
                "cereal",
                "noodle",
                "couscous",
                "barley",
            ],
            "Pantry": [
                "oil",
                "vinegar",
                "sugar",
                "salt",
                "pepper",
                "spice",
                "sauce",
                "ketchup",
                "mustard",
                "mayo",
                "honey",
                "syrup",
                "jam",
            ],
            "Beverages": ["juice", "soda", "water", "coffee", "tea", "wine", "beer"],
            "Bakery": ["bread", "bagel", "muffin", "croissant", "roll", "tortilla"],
            "Frozen": ["frozen", "ice cream", "frozen vegetable", "frozen fruit"],
        }

        ingredient_lower = ingredient_name.lower()

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in ingredient_lower:
                    return category

        return "Other"
