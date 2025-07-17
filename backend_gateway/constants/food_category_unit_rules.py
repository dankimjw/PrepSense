"""
Food Category to Unit Rules Mapping
This defines which unit categories are appropriate for each food category
"""

from typing import Dict, List, Set
from enum import Enum

class UnitCategory(str, Enum):
    MASS = "mass"
    VOLUME = "volume"
    COUNT = "count"

class FoodCategory(str, Enum):
    PRODUCE = "Produce"
    DAIRY = "Dairy"
    MEAT = "Meat"
    GRAINS = "Grains"
    CANNED_GOODS = "Canned Goods"
    BEVERAGES = "Beverages"
    CONDIMENTS = "Condiments"
    SNACKS = "Snacks"
    FROZEN = "Frozen"
    BAKERY = "Bakery"
    SEAFOOD = "Seafood"
    SPICES = "Spices"
    OILS = "Oils"
    BAKING = "Baking"
    PASTA = "Pasta"
    INTERNATIONAL = "International"
    OTHER = "Other"

# Define which unit categories are allowed for each food category
FOOD_CATEGORY_UNIT_RULES: Dict[str, Dict[str, any]] = {
    FoodCategory.PRODUCE: {
        "allowed_categories": [UnitCategory.COUNT, UnitCategory.MASS],
        "default_category": UnitCategory.COUNT,
        "common_items": {
            # Count-based produce
            "apple": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "banana": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "orange": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "lettuce": {"preferred_unit": "head", "category": UnitCategory.COUNT},
            "cabbage": {"preferred_unit": "head", "category": UnitCategory.COUNT},
            "garlic": {"preferred_unit": "head", "category": UnitCategory.COUNT},
            "onion": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "potato": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "tomato": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "avocado": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "lemon": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "lime": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            
            # Mass-based produce (usually smaller items)
            "berries": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "grapes": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "spinach": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "herbs": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "mushrooms": {"preferred_unit": "g", "category": UnitCategory.MASS},
        }
    },
    
    FoodCategory.DAIRY: {
        "allowed_categories": [UnitCategory.VOLUME, UnitCategory.MASS, UnitCategory.COUNT],
        "default_category": UnitCategory.VOLUME,
        "common_items": {
            # Volume-based dairy
            "milk": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "cream": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "yogurt drink": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            
            # Mass-based dairy
            "cheese": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "butter": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "yogurt": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "cream cheese": {"preferred_unit": "g", "category": UnitCategory.MASS},
            
            # Count-based dairy
            "eggs": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "cheese slices": {"preferred_unit": "slice", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.MEAT: {
        "allowed_categories": [UnitCategory.MASS],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "chicken": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "beef": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "pork": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "turkey": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "lamb": {"preferred_unit": "g", "category": UnitCategory.MASS},
        }
    },
    
    FoodCategory.SEAFOOD: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.COUNT],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "fish": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "shrimp": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "salmon": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "lobster": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "crab": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.GRAINS: {
        "allowed_categories": [UnitCategory.MASS],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "rice": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "quinoa": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "oats": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "barley": {"preferred_unit": "g", "category": UnitCategory.MASS},
        }
    },
    
    FoodCategory.BEVERAGES: {
        "allowed_categories": [UnitCategory.VOLUME, UnitCategory.COUNT],
        "default_category": UnitCategory.VOLUME,
        "common_items": {
            "juice": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "soda": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "water": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "beer": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "wine": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            # Count for packaged beverages
            "soda cans": {"preferred_unit": "can", "category": UnitCategory.COUNT},
            "water bottles": {"preferred_unit": "bottle", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.CONDIMENTS: {
        "allowed_categories": [UnitCategory.VOLUME, UnitCategory.MASS],
        "default_category": UnitCategory.VOLUME,
        "common_items": {
            "ketchup": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "mustard": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "mayonnaise": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "soy sauce": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "hot sauce": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "peanut butter": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "jam": {"preferred_unit": "g", "category": UnitCategory.MASS},
        }
    },
    
    FoodCategory.OILS: {
        "allowed_categories": [UnitCategory.VOLUME],
        "default_category": UnitCategory.VOLUME,
        "common_items": {
            "olive oil": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "vegetable oil": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "coconut oil": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "sesame oil": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
        }
    },
    
    FoodCategory.BAKING: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.VOLUME],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "flour": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "sugar": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "baking powder": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "baking soda": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "cocoa powder": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "vanilla extract": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
        }
    },
    
    FoodCategory.SPICES: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.VOLUME],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "salt": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "pepper": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "cinnamon": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "paprika": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "cumin": {"preferred_unit": "g", "category": UnitCategory.MASS},
        }
    },
    
    FoodCategory.PASTA: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.COUNT],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "spaghetti": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "penne": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "lasagna sheets": {"preferred_unit": "box", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.BAKERY: {
        "allowed_categories": [UnitCategory.COUNT, UnitCategory.MASS],
        "default_category": UnitCategory.COUNT,
        "common_items": {
            "bread": {"preferred_unit": "loaf", "category": UnitCategory.COUNT},
            "bagels": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "croissants": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "muffins": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.CANNED_GOODS: {
        "allowed_categories": [UnitCategory.COUNT, UnitCategory.MASS, UnitCategory.VOLUME],
        "default_category": UnitCategory.COUNT,
        "common_items": {
            "canned tomatoes": {"preferred_unit": "can", "category": UnitCategory.COUNT},
            "canned beans": {"preferred_unit": "can", "category": UnitCategory.COUNT},
            "canned corn": {"preferred_unit": "can", "category": UnitCategory.COUNT},
            "canned soup": {"preferred_unit": "can", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.FROZEN: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.COUNT, UnitCategory.VOLUME],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "frozen vegetables": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "ice cream": {"preferred_unit": "ml", "category": UnitCategory.VOLUME},
            "frozen pizza": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.SNACKS: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.COUNT],
        "default_category": UnitCategory.MASS,
        "common_items": {
            "chips": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "cookies": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
            "crackers": {"preferred_unit": "g", "category": UnitCategory.MASS},
            "candy bars": {"preferred_unit": "ea", "category": UnitCategory.COUNT},
        }
    },
    
    FoodCategory.OTHER: {
        "allowed_categories": [UnitCategory.MASS, UnitCategory.VOLUME, UnitCategory.COUNT],
        "default_category": UnitCategory.COUNT,
        "common_items": {}
    }
}

def get_allowed_unit_categories(food_category: str) -> List[UnitCategory]:
    """Get the allowed unit categories for a food category"""
    rules = FOOD_CATEGORY_UNIT_RULES.get(food_category, FOOD_CATEGORY_UNIT_RULES[FoodCategory.OTHER])
    return rules["allowed_categories"]

def get_default_unit_category(food_category: str) -> UnitCategory:
    """Get the default unit category for a food category"""
    rules = FOOD_CATEGORY_UNIT_RULES.get(food_category, FOOD_CATEGORY_UNIT_RULES[FoodCategory.OTHER])
    return rules["default_category"]

def get_preferred_unit(food_category: str, item_name: str) -> tuple[str, UnitCategory]:
    """Get the preferred unit and category for a specific item"""
    rules = FOOD_CATEGORY_UNIT_RULES.get(food_category, FOOD_CATEGORY_UNIT_RULES[FoodCategory.OTHER])
    
    # Check if we have a specific rule for this item
    item_name_lower = item_name.lower()
    for common_item, preferences in rules["common_items"].items():
        if common_item in item_name_lower:
            return preferences["preferred_unit"], preferences["category"]
    
    # Otherwise return defaults
    default_category = rules["default_category"]
    default_units = {
        UnitCategory.MASS: "g",
        UnitCategory.VOLUME: "ml",
        UnitCategory.COUNT: "ea"
    }
    return default_units[default_category], default_category

def validate_unit_for_food_category(food_category: str, unit_category: UnitCategory) -> bool:
    """Check if a unit category is valid for a food category"""
    allowed = get_allowed_unit_categories(food_category)
    return unit_category in allowed