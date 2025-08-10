"""
Backend fallback unit service for OCR processing.
Provides intelligent unit fallbacks and validates extracted quantities/units.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Invalid units that should never be allowed (from receipt price formatting)
INVALID_UNITS = [
    "B",
    "b",  # Price formatting characters
    "$",
    "¢",  # Currency symbols
    "%",  # Percentage
    "#",  # Hash/pound symbol
    "&",  # Ampersand
    "@",  # At symbol
    "!",
    "?",  # Punctuation
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "0",  # Pure numbers
]

# Food category fallback mappings
FOOD_CATEGORY_FALLBACKS = {
    "Produce": {
        "default_unit": "each",
        "alternatives": ["lb", "oz", "bunch", "bag"],
        "patterns": {
            "fruits": "each",
            "berries": "cup",
            "leafy_greens": "cup",
            "root_vegetables": "each",
            "cruciferous": "cup",
            "tomatoes_peppers": "each",
        },
    },
    "Meat": {
        "default_unit": "oz",
        "alternatives": ["lb", "piece"],
        "patterns": {"meat_poultry": "oz", "ground_meat": "oz"},
    },
    "Seafood": {
        "default_unit": "oz",
        "alternatives": ["fillet", "piece"],
        "patterns": {"fish": "oz"},
    },
    "Dairy": {
        "default_unit": "cup",
        "alternatives": ["oz", "gallon", "quart"],
        "patterns": {
            "milk": "cup",
            "cheese": "oz",
            "yogurt": "cup",
            "butter": "tbsp",
            "eggs": "each",
        },
    },
    "Pantry": {
        "default_unit": "cup",
        "alternatives": ["oz", "lb", "bag", "box"],
        "patterns": {
            "grains_cooked": "cup",
            "pasta_cooked": "cup",
            "beans_cooked": "cup",
            "nuts": "oz",
            "oils": "tbsp",
            "nut_butters": "tbsp",
            "seeds": "tbsp",
            "spices": "tsp",
        },
    },
    "Bakery": {
        "default_unit": "slice",
        "alternatives": ["each", "piece", "oz"],
        "patterns": {"bread": "slice", "cookies": "each", "muffins": "each", "cake": "slice"},
    },
    "Beverages": {
        "default_unit": "cup",
        "alternatives": ["fl oz", "ml", "bottle"],
        "patterns": {"default": "cup", "alcohol": "fl oz"},
    },
    "Snacks": {
        "default_unit": "oz",
        "alternatives": ["bag", "each", "serving"],
        "patterns": {"chips_crackers": "oz", "bars": "each"},
    },
    "Canned Goods": {
        "default_unit": "can",
        "alternatives": ["cup", "oz"],
        "patterns": {"soups": "cup", "vegetables": "cup"},
    },
    "Frozen": {
        "default_unit": "cup",
        "alternatives": ["oz", "bag", "each"],
        "patterns": {"vegetables": "cup", "meals": "each"},
    },
}

# Specific food item patterns for more precise matching
FOOD_ITEM_PATTERNS = {
    # Fruits
    "apple": "each",
    "banana": "each",
    "orange": "each",
    "strawberry": "cup",
    "blueberry": "cup",
    "raspberry": "cup",
    "grape": "cup",
    "cherry": "cup",
    "avocado": "each",
    # Vegetables
    "potato": "each",
    "onion": "each",
    "carrot": "each",
    "tomato": "each",
    "bell pepper": "each",
    "pepper": "each",
    "spinach": "cup",
    "lettuce": "cup",
    "broccoli": "cup",
    "cauliflower": "cup",
    # Proteins
    "chicken": "oz",
    "beef": "oz",
    "pork": "oz",
    "fish": "oz",
    "salmon": "oz",
    "tuna": "oz",
    "egg": "each",
    "tofu": "oz",
    # Dairy
    "milk": "cup",
    "cheese": "oz",
    "yogurt": "cup",
    "butter": "tbsp",
    # Grains
    "rice": "cup",
    "pasta": "cup",
    "bread": "slice",
    "cereal": "cup",
    "oats": "cup",
    # Condiments
    "ketchup": "tbsp",
    "mustard": "tbsp",
    "mayo": "tbsp",
    "oil": "tbsp",
    "vinegar": "tbsp",
    "salt": "tsp",
    "pepper": "tsp",
}


class FallbackUnitService:
    """Service for handling unit fallbacks and validation in OCR processing."""

    def is_invalid_unit(self, unit: str) -> bool:
        """Check if a unit is invalid and should be rejected."""
        if not unit:
            return True
        return unit.strip() in INVALID_UNITS

    def is_likely_price(self, quantity: float, unit: str, item_name: str) -> bool:
        """
        Detect if a quantity/unit combination is likely a price rather than actual quantity.
        """
        # Check for price-like patterns
        if self.is_invalid_unit(unit):
            return True

        # Check for price-like quantities (common price ranges)
        if 0.50 <= quantity <= 50.00:
            # If unit is invalid or looks like price formatting
            if unit in ["B", "b", "$", "¢"] or not unit:
                return True

        # Check if quantity has decimal places typical of prices
        if quantity != int(quantity) and len(str(quantity).split(".")[-1]) == 2:
            # Two decimal places often indicate price (e.g., 3.99, 12.49)
            if unit in INVALID_UNITS or not unit:
                return True

        return False

    def get_fallback_unit(self, item_name: str, category: Optional[str] = None) -> str:
        """Get fallback unit for a food item based on its name and category."""
        if not item_name:
            return "each"

        normalized_name = item_name.lower().strip()

        # Step 1: Check for specific food item patterns
        for pattern, unit in FOOD_ITEM_PATTERNS.items():
            if pattern in normalized_name:
                logger.info(
                    f"Found specific pattern '{pattern}' for '{item_name}', using unit: {unit}"
                )
                return unit

        # Step 2: Use category-based fallback
        if category and category in FOOD_CATEGORY_FALLBACKS:
            category_info = FOOD_CATEGORY_FALLBACKS[category]

            # Try to find subcategory patterns
            for pattern_key, pattern_unit in category_info["patterns"].items():
                if self._matches_subcategory(normalized_name, pattern_key):
                    logger.info(
                        f"Found subcategory pattern '{pattern_key}' for '{item_name}', using unit: {pattern_unit}"
                    )
                    return pattern_unit

            # Fall back to category default
            default_unit = category_info["default_unit"]
            logger.info(
                f"Using category default unit for '{item_name}' in '{category}': {default_unit}"
            )
            return default_unit

        # Step 3: General fallbacks based on common patterns
        if self._is_liquid(normalized_name):
            return "cup"
        elif self._is_spice(normalized_name):
            return "tsp"
        elif self._is_condiment(normalized_name):
            return "tbsp"

        # Step 4: Final fallback
        logger.info(f"Using final fallback unit 'each' for '{item_name}'")
        return "each"

    def validate_and_fix_quantity_unit(
        self, item_name: str, quantity: float, unit: str, category: Optional[str] = None
    ) -> tuple[float, str]:
        """
        Validate and fix quantity/unit pairs, applying fallbacks for invalid data.
        Returns (corrected_quantity, corrected_unit)
        """
        logger.info(f"Validating quantity/unit for '{item_name}': {quantity} {unit}")

        # Check if this looks like a price
        if self.is_likely_price(quantity, unit, item_name):
            logger.warning(
                f"Detected price-like data for '{item_name}': {quantity} {unit}, applying fallback"
            )
            fallback_unit = self.get_fallback_unit(item_name, category)
            return 1.0, fallback_unit  # Default to quantity 1 with appropriate unit

        # Check if unit is invalid
        if self.is_invalid_unit(unit):
            logger.warning(f"Invalid unit '{unit}' for '{item_name}', applying fallback")
            fallback_unit = self.get_fallback_unit(item_name, category)
            return quantity if quantity > 0 else 1.0, fallback_unit

        # Validate quantity
        if quantity <= 0:
            logger.warning(f"Invalid quantity {quantity} for '{item_name}', defaulting to 1")
            quantity = 1.0

        # Unit seems valid, but normalize it
        normalized_unit = self._normalize_unit(unit)
        if normalized_unit != unit:
            logger.info(f"Normalized unit for '{item_name}': '{unit}' -> '{normalized_unit}'")
            unit = normalized_unit

        return quantity, unit

    def _matches_subcategory(self, item_name: str, subcategory: str) -> bool:
        """Check if item name matches a subcategory pattern."""
        subcategory_patterns = {
            "berries": ["berry", "strawberry", "blueberry", "raspberry", "blackberry", "cranberry"],
            "leafy_greens": ["spinach", "lettuce", "kale", "arugula", "chard", "greens"],
            "root_vegetables": ["potato", "carrot", "beet", "turnip", "radish", "sweet potato"],
            "cruciferous": ["broccoli", "cauliflower", "cabbage", "brussels sprouts"],
            "tomatoes_peppers": ["tomato", "pepper", "bell pepper", "jalapeño"],
            "meat_poultry": ["chicken", "beef", "pork", "turkey", "lamb"],
            "ground_meat": ["ground beef", "ground turkey", "ground chicken", "hamburger"],
            "fish": ["salmon", "tuna", "cod", "tilapia", "fish"],
            "milk": ["milk", "almond milk", "soy milk", "oat milk"],
            "cheese": ["cheese", "cheddar", "mozzarella", "swiss"],
            "yogurt": ["yogurt", "greek yogurt"],
            "butter": ["butter", "margarine"],
            "eggs": ["egg", "eggs"],
            "grains_cooked": ["rice", "quinoa", "barley", "cooked"],
            "pasta_cooked": ["pasta", "spaghetti", "penne", "noodles"],
            "beans_cooked": ["beans", "lentils", "chickpeas", "black beans"],
            "nuts": ["nuts", "almonds", "walnuts", "peanuts", "cashews"],
            "oils": ["oil", "olive oil", "vegetable oil", "coconut oil"],
            "nut_butters": ["peanut butter", "almond butter", "nut butter"],
            "seeds": ["seeds", "sunflower seeds", "chia seeds", "flax seeds"],
            "spices": ["salt", "pepper", "cinnamon", "paprika", "cumin"],
            "bread": ["bread", "toast", "baguette", "roll"],
            "cookies": ["cookie", "biscuit"],
            "muffins": ["muffin"],
            "cake": ["cake", "cupcake"],
            "alcohol": ["wine", "beer", "vodka", "whiskey", "rum"],
            "chips_crackers": ["chips", "crackers", "pretzels"],
            "bars": ["bar", "granola bar", "protein bar"],
            "soups": ["soup", "broth", "stew"],
            "meals": ["meal", "dinner", "entree"],
        }

        patterns = subcategory_patterns.get(subcategory, [])
        return any(pattern in item_name for pattern in patterns)

    def _is_liquid(self, item_name: str) -> bool:
        """Check if item is likely a liquid."""
        liquid_patterns = ["juice", "milk", "water", "soda", "tea", "coffee", "broth", "stock"]
        return any(pattern in item_name for pattern in liquid_patterns)

    def _is_spice(self, item_name: str) -> bool:
        """Check if item is likely a spice."""
        spice_patterns = [
            "salt",
            "pepper",
            "cinnamon",
            "paprika",
            "cumin",
            "oregano",
            "basil",
            "thyme",
        ]
        return any(pattern in item_name for pattern in spice_patterns)

    def _is_condiment(self, item_name: str) -> bool:
        """Check if item is likely a condiment."""
        condiment_patterns = ["ketchup", "mustard", "mayo", "sauce", "dressing", "oil", "vinegar"]
        return any(pattern in item_name for pattern in condiment_patterns)

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit variations to standard forms."""
        if not unit:
            return "each"

        normalized = unit.lower().strip()

        # Handle common variations
        variations = {
            "cups": "cup",
            "tablespoon": "tbsp",
            "tablespoons": "tbsp",
            "teaspoon": "tsp",
            "teaspoons": "tsp",
            "pound": "lb",
            "pounds": "lb",
            "lbs": "lb",
            "ounce": "oz",
            "ounces": "oz",
            "fluid ounce": "fl oz",
            "fluid ounces": "fl oz",
            "milliliter": "ml",
            "milliliters": "ml",
            "liter": "l",
            "liters": "l",
            "pint": "pt",
            "pints": "pt",
            "quart": "qt",
            "quarts": "qt",
            "gallon": "gal",
            "gallons": "gal",
            "package": "package",
            "packages": "package",
            "pkg": "package",
            "packs": "pack",
            "pieces": "pcs",
            "pc": "pcs",
            "piece": "pcs",
            "bags": "bag",
            "cases": "case",
            "cartons": "carton",
            "bottles": "bottle",
            "jars": "jar",
            "cans": "can",
            "boxes": "box",
            "loaves": "loaf",
            "units": "each",
            "unit": "each",
        }

        return variations.get(normalized, normalized)


# Global instance
fallback_unit_service = FallbackUnitService()
