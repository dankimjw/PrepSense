"""
Item category to unit mapping for PrepSense
Defines which units are appropriate for different types of food items
"""

from .units import Unit


# Define food categories
class FoodCategory:
    PRODUCE_COUNTABLE = "produce_countable"  # Items typically counted (bananas, apples)
    PRODUCE_BULK = "produce_bulk"  # Items typically sold by weight (grapes, berries)
    LIQUIDS = "liquids"  # Milk, juice, oil
    DRY_GOODS = "dry_goods"  # Flour, sugar, rice
    MEAT_SEAFOOD = "meat_seafood"  # Meat, fish, poultry
    DAIRY_SOLID = "dairy_solid"  # Cheese, butter
    EGGS = "eggs"  # Eggs
    BREAD_BAKERY = "bread_bakery"  # Bread, rolls, pastries
    CANNED_JARRED = "canned_jarred"  # Canned goods, jarred items
    CONDIMENTS = "condiments"  # Sauces, dressings, spreads
    SPICES_HERBS = "spices_herbs"  # Spices, herbs, seasonings
    SNACKS = "snacks"  # Chips, crackers, cookies
    FROZEN = "frozen"  # Frozen foods
    BEVERAGES = "beverages"  # Non-liquid beverages (soda cans, bottles)
    GENERAL = "general"  # Default category


# Map categories to allowed units
CATEGORY_UNIT_MAPPING: dict[str, list[str]] = {
    FoodCategory.PRODUCE_COUNTABLE: [
        Unit.EACH,
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.BAG,
        Unit.PACKAGE,
    ],
    FoodCategory.PRODUCE_BULK: [
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.CUP,
        Unit.BAG,
        Unit.PACKAGE,
    ],
    FoodCategory.LIQUIDS: [
        Unit.MILLILITER,
        Unit.LITER,
        Unit.FLUID_OUNCE,
        Unit.CUP,
        Unit.PINT,
        Unit.QUART,
        Unit.GALLON,
        Unit.TABLESPOON,
        Unit.TEASPOON,
        Unit.EACH,  # For bottles/containers
        Unit.PACKAGE,
    ],
    FoodCategory.DRY_GOODS: [
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.CUP,
        Unit.TABLESPOON,
        Unit.TEASPOON,
        Unit.BAG,
        Unit.PACKAGE,
    ],
    FoodCategory.MEAT_SEAFOOD: [
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.EACH,  # For steaks, chops, fillets
        Unit.PACKAGE,
    ],
    FoodCategory.DAIRY_SOLID: [
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.CUP,
        Unit.TABLESPOON,
        Unit.EACH,  # For sticks of butter
        Unit.PACKAGE,
    ],
    FoodCategory.EGGS: [
        Unit.EACH,
        Unit.CARTON,
        Unit.CASE,
    ],
    FoodCategory.BREAD_BAKERY: [
        Unit.EACH,
        Unit.PACKAGE,
        Unit.BAG,
        Unit.GRAM,
        Unit.OUNCE,
        Unit.POUND,
    ],
    FoodCategory.CANNED_JARRED: [
        Unit.EACH,
        Unit.MILLILITER,
        Unit.LITER,
        Unit.FLUID_OUNCE,
        Unit.CUP,
        Unit.GRAM,
        Unit.OUNCE,
        Unit.PACKAGE,
        Unit.CASE,
    ],
    FoodCategory.CONDIMENTS: [
        Unit.MILLILITER,
        Unit.LITER,
        Unit.FLUID_OUNCE,
        Unit.CUP,
        Unit.TABLESPOON,
        Unit.TEASPOON,
        Unit.GRAM,
        Unit.OUNCE,
        Unit.EACH,  # For bottles/jars
        Unit.PACKAGE,
    ],
    FoodCategory.SPICES_HERBS: [
        Unit.GRAM,
        Unit.OUNCE,
        Unit.TABLESPOON,
        Unit.TEASPOON,
        Unit.EACH,  # For containers
        Unit.PACKAGE,
    ],
    FoodCategory.SNACKS: [
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.CUP,
        Unit.EACH,
        Unit.PACKAGE,
        Unit.BAG,
        Unit.CASE,
    ],
    FoodCategory.FROZEN: [
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.CUP,
        Unit.EACH,
        Unit.PACKAGE,
        Unit.BAG,
    ],
    FoodCategory.BEVERAGES: [
        Unit.EACH,
        Unit.PACKAGE,
        Unit.CASE,
        Unit.CARTON,
    ],
    # Default for unknown categories
    FoodCategory.GENERAL: [
        Unit.EACH,
        Unit.GRAM,
        Unit.KILOGRAM,
        Unit.OUNCE,
        Unit.POUND,
        Unit.MILLILITER,
        Unit.LITER,
        Unit.CUP,
        Unit.PACKAGE,
    ],
}

# Keywords to help categorize items
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    FoodCategory.PRODUCE_COUNTABLE: [
        "banana",
        "apple",
        "orange",
        "lemon",
        "lime",
        "peach",
        "pear",
        "plum",
        "avocado",
        "mango",
        "kiwi",
        "onion",
        "potato",
        "tomato",
        "cucumber",
        "pepper",
        "corn",
        "eggplant",
        "zucchini",
    ],
    FoodCategory.PRODUCE_BULK: [
        "grape",
        "berry",
        "berries",
        "strawberry",
        "blueberry",
        "raspberry",
        "blackberry",
        "cherry",
        "cherries",
        "spinach",
        "lettuce",
        "kale",
        "arugula",
        "herbs",
        "cilantro",
        "parsley",
        "basil",
    ],
    FoodCategory.LIQUIDS: [
        "milk",
        "juice",
        "oil",
        "vinegar",
        "water",
        "broth",
        "stock",
        "cream",
        "yogurt",
        "kefir",
        "smoothie",
        "drink",
        "beverage",
    ],
    FoodCategory.DRY_GOODS: [
        "flour",
        "sugar",
        "rice",
        "pasta",
        "noodle",
        "cereal",
        "oats",
        "quinoa",
        "barley",
        "lentil",
        "bean",
        "pea",
        "chickpea",
        "salt",
        "baking powder",
        "baking soda",
        "yeast",
    ],
    FoodCategory.MEAT_SEAFOOD: [
        "chicken",
        "beef",
        "pork",
        "lamb",
        "turkey",
        "duck",
        "fish",
        "salmon",
        "tuna",
        "shrimp",
        "lobster",
        "crab",
        "scallop",
        "steak",
        "ground",
        "mince",
        "chop",
        "breast",
        "thigh",
        "wing",
    ],
    FoodCategory.DAIRY_SOLID: [
        "cheese",
        "butter",
        "margarine",
        "cream cheese",
        "cottage cheese",
        "mozzarella",
        "cheddar",
        "parmesan",
        "feta",
        "brie",
    ],
    FoodCategory.EGGS: ["egg", "eggs"],
    FoodCategory.BREAD_BAKERY: [
        "bread",
        "roll",
        "bagel",
        "muffin",
        "croissant",
        "pastry",
        "cake",
        "cookie",
        "donut",
        "pie",
        "tart",
        "baguette",
        "loaf",
    ],
    FoodCategory.CANNED_JARRED: [
        "can",
        "canned",
        "jar",
        "jarred",
        "sauce",
        "salsa",
        "pickle",
        "olive",
        "preserve",
        "jam",
        "jelly",
        "honey",
        "syrup",
    ],
    FoodCategory.CONDIMENTS: [
        "ketchup",
        "mustard",
        "mayonnaise",
        "mayo",
        "dressing",
        "sauce",
        "hot sauce",
        "soy sauce",
        "worcestershire",
        "bbq sauce",
    ],
    FoodCategory.SPICES_HERBS: [
        "spice",
        "pepper",
        "paprika",
        "cumin",
        "coriander",
        "turmeric",
        "cinnamon",
        "nutmeg",
        "oregano",
        "thyme",
        "rosemary",
        "sage",
    ],
    FoodCategory.SNACKS: [
        "chip",
        "cracker",
        "pretzel",
        "popcorn",
        "nut",
        "candy",
        "chocolate",
        "granola",
        "protein bar",
        "trail mix",
    ],
    FoodCategory.FROZEN: ["frozen", "ice cream", "popsicle", "pizza", "meal", "dinner"],
    FoodCategory.BEVERAGES: ["soda", "cola", "beer", "wine", "spirits", "bottle", "can"],
}


def categorize_item(item_name: str, existing_category: str = None) -> str:
    """
    Categorize an item based on its name
    Returns the most appropriate category
    """
    # If an existing category is provided and valid, use it
    if existing_category and existing_category in CATEGORY_UNIT_MAPPING:
        return existing_category

    item_lower = item_name.lower()

    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in item_lower:
                return category

    # Default to general category
    return FoodCategory.GENERAL


def get_allowed_units(item_name: str, category: str = None) -> list[str]:
    """
    Get the list of allowed units for an item
    """
    item_category = categorize_item(item_name, category)
    return CATEGORY_UNIT_MAPPING.get(item_category, CATEGORY_UNIT_MAPPING[FoodCategory.GENERAL])


def is_unit_allowed(item_name: str, unit: str, category: str = None) -> bool:
    """
    Check if a unit is allowed for a specific item
    """
    allowed_units = get_allowed_units(item_name, category)
    return unit in allowed_units


def get_default_unit(item_name: str, category: str = None) -> str:
    """
    Get the default unit for an item
    """
    item_category = categorize_item(item_name, category)
    allowed_units = CATEGORY_UNIT_MAPPING.get(item_category, [Unit.EACH])

    # Prefer 'each' for countable items
    if item_category in [
        FoodCategory.PRODUCE_COUNTABLE,
        FoodCategory.EGGS,
        FoodCategory.BREAD_BAKERY,
        FoodCategory.BEVERAGES,
    ]:
        return Unit.EACH

    # Prefer weight for bulk items
    elif item_category in [
        FoodCategory.PRODUCE_BULK,
        FoodCategory.MEAT_SEAFOOD,
        FoodCategory.DRY_GOODS,
    ]:
        return Unit.POUND if Unit.POUND in allowed_units else Unit.GRAM

    # Prefer volume for liquids
    elif item_category == FoodCategory.LIQUIDS:
        return Unit.FLUID_OUNCE

    # Default to first allowed unit
    return allowed_units[0] if allowed_units else Unit.EACH
