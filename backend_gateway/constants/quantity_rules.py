"""
Quantity validation rules for different types of items
"""

import re
from typing import Optional

# Items that must have whole number quantities only
WHOLE_NUMBER_ITEMS = [
    # Fruits
    "banana",
    "bananas",
    "apple",
    "apples",
    "orange",
    "oranges",
    "pear",
    "pears",
    "avocado",
    "avocados",
    "lemon",
    "lemons",
    "lime",
    "limes",
    "mango",
    "mangos",
    "mangoes",
    "peach",
    "peaches",
    "plum",
    "plums",
    "kiwi",
    "kiwis",
    "coconut",
    "coconuts",
    "pineapple",
    "pineapples",
    "melon",
    "melons",
    "watermelon",
    "watermelons",
    "cantaloupe",
    "cantaloupes",
    "honeydew",
    "grapefruit",
    "grapefruits",
    # Vegetables
    "potato",
    "potatoes",
    "onion",
    "onions",
    "tomato",
    "tomatoes",
    "cucumber",
    "cucumbers",
    "bell pepper",
    "bell peppers",
    "pepper",
    "peppers",
    "carrot",
    "carrots",
    "zucchini",
    "zucchinis",
    "eggplant",
    "eggplants",
    "corn",
    "corn cob",
    "corn cobs",
    "cabbage",
    "cabbages",
    "lettuce",
    "lettuces",
    "cauliflower",
    "cauliflowers",
    "broccoli",
    "brocolis",
    "squash",
    "squashes",
    "sweet potato",
    "sweet potatoes",
    # Proteins
    "egg",
    "eggs",
    "chicken breast",
    "chicken breasts",
    "chicken thigh",
    "chicken thighs",
    "chicken leg",
    "chicken legs",
    "drumstick",
    "drumsticks",
    "chicken wing",
    "chicken wings",
    "pork chop",
    "pork chops",
    "steak",
    "steaks",
    "fish fillet",
    "fish fillets",
    "salmon fillet",
    "salmon fillets",
    "shrimp",
    "shrimps",
    # Packaged items
    "can",
    "cans",
    "bottle",
    "bottles",
    "jar",
    "jars",
    "box",
    "boxes",
    "package",
    "packages",
    "bag",
    "bags",
    "pack",
    "packs",
    "tube",
    "tubes",
    "container",
    "containers",
    "carton",
    "cartons",
    "loaf",
    "loaves",
    "roll",
    "rolls",
    "stick",
    "sticks",
    "bar",
    "bars",
    "block",
    "blocks",
    # Bakery
    "bread",
    "breads",
    "bagel",
    "bagels",
    "muffin",
    "muffins",
    "croissant",
    "croissants",
    "donut",
    "donuts",
    "doughnut",
    "doughnuts",
    "cookie",
    "cookies",
    "cracker",
    "crackers",
    # Other countable items
    "pill",
    "pills",
    "tablet",
    "tablets",
    "capsule",
    "capsules",
    "slice",
    "slices",
    "piece",
    "pieces",
    "item",
    "items",
]

# Units that typically indicate whole items
WHOLE_NUMBER_UNITS = [
    "each",
    "piece",
    "pieces",
    "item",
    "items",
    "pcs",
    "pc",
    "bottle",
    "bottles",
    "can",
    "cans",
    "jar",
    "jars",
    "package",
    "packages",
    "pkg",
    "pack",
    "packs",
    "bag",
    "bags",
    "box",
    "boxes",
    "carton",
    "cartons",
    "container",
    "containers",
    "tube",
    "tubes",
    "roll",
    "rolls",
    "stick",
    "sticks",
    "bar",
    "bars",
    "block",
    "blocks",
    "loaf",
    "loaves",
    "slice",
    "slices",
]


def should_allow_decimals(item_name: str, unit: str) -> bool:
    """
    Determines if an item should only allow whole number quantities
    """
    normalized_name = item_name.lower().strip()
    normalized_unit = unit.lower().strip()

    # Check if unit requires whole numbers
    if normalized_unit in WHOLE_NUMBER_UNITS:
        return False

    # Check if item name contains any whole number keywords
    return all(item not in normalized_name for item in WHOLE_NUMBER_ITEMS)


def get_quantity_rules(item_name: str, unit: str) -> dict:
    """
    Gets quantity validation rules for an item
    """
    allow_decimals = should_allow_decimals(item_name, unit)

    return {
        "allow_decimals": allow_decimals,
        "min_value": 0.1 if allow_decimals else 1,
        "step": 0.1 if allow_decimals else 1,
    }


def validate_quantity(quantity: float, item_name: str, unit: str) -> tuple[bool, Optional[str]]:
    """
    Validates a quantity value against the rules
    Returns (is_valid, error_message)
    """
    rules = get_quantity_rules(item_name, unit)

    if quantity <= 0:
        return False, "Quantity must be greater than 0"

    if not rules["allow_decimals"] and quantity != int(quantity):
        return False, f"{item_name} must be a whole number (no decimals)"

    if rules.get("min_value") and quantity < rules["min_value"]:
        return False, f'Minimum quantity is {rules["min_value"]}'

    if rules.get("max_value") and quantity > rules["max_value"]:
        return False, f'Maximum quantity is {rules["max_value"]}'

    return True, None


def format_quantity_input(input_str: str, item_name: str, unit: str) -> str:
    """
    Formats input string according to quantity rules
    """
    rules = get_quantity_rules(item_name, unit)

    if not rules["allow_decimals"]:
        # Remove any decimal points and everything after them
        return re.sub(r"\..*", "", input_str)

    # For decimal-allowed items, allow one decimal point
    cleaned = re.sub(r"[^0-9.]", "", input_str)
    parts = cleaned.split(".")

    if len(parts) > 2:
        # Only allow one decimal point
        return parts[0] + "." + "".join(parts[1:])

    return cleaned
