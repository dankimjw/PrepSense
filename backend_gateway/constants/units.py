"""
Unit constants and conversions for the PrepSense backend
"""

from enum import Enum
from typing import Dict, Optional


class UnitCategory(str, Enum):
    WEIGHT = "weight"
    VOLUME = "volume"
    COUNT = "count"


class Unit(str, Enum):
    # Weight
    MILLIGRAM = "mg"
    GRAM = "g"
    KILOGRAM = "kg"
    OUNCE = "oz"
    POUND = "lb"
    
    # Volume
    MILLILITER = "ml"
    LITER = "l"
    FLUID_OUNCE = "fl oz"
    CUP = "cup"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"
    PINT = "pt"
    QUART = "qt"
    GALLON = "gal"
    
    # Count & Packaging
    EACH = "each"
    PACKAGE = "package"
    BAG = "bag"
    CASE = "case"
    CARTON = "carton"
    GROSS = "gross"


# Unit metadata
UNIT_INFO = {
    Unit.MILLIGRAM: {"label": "Milligram", "category": UnitCategory.WEIGHT, "abbreviation": "mg"},
    Unit.GRAM: {"label": "Gram", "category": UnitCategory.WEIGHT, "abbreviation": "g"},
    Unit.KILOGRAM: {"label": "Kilogram", "category": UnitCategory.WEIGHT, "abbreviation": "kg"},
    Unit.OUNCE: {"label": "Ounce", "category": UnitCategory.WEIGHT, "abbreviation": "oz"},
    Unit.POUND: {"label": "Pound", "category": UnitCategory.WEIGHT, "abbreviation": "lb"},
    
    Unit.MILLILITER: {"label": "Milliliter", "category": UnitCategory.VOLUME, "abbreviation": "mL"},
    Unit.LITER: {"label": "Liter", "category": UnitCategory.VOLUME, "abbreviation": "L"},
    Unit.FLUID_OUNCE: {"label": "Fluid Ounce", "category": UnitCategory.VOLUME, "abbreviation": "fl oz"},
    Unit.CUP: {"label": "Cup", "category": UnitCategory.VOLUME, "abbreviation": "cup"},
    Unit.TABLESPOON: {"label": "Tablespoon", "category": UnitCategory.VOLUME, "abbreviation": "Tbsp"},
    Unit.TEASPOON: {"label": "Teaspoon", "category": UnitCategory.VOLUME, "abbreviation": "tsp"},
    Unit.PINT: {"label": "Pint", "category": UnitCategory.VOLUME, "abbreviation": "pt"},
    Unit.QUART: {"label": "Quart", "category": UnitCategory.VOLUME, "abbreviation": "qt"},
    Unit.GALLON: {"label": "Gallon", "category": UnitCategory.VOLUME, "abbreviation": "gal"},
    
    Unit.EACH: {"label": "Each", "category": UnitCategory.COUNT, "abbreviation": "each"},
    Unit.PACKAGE: {"label": "Package", "category": UnitCategory.COUNT, "abbreviation": "pkg"},
    Unit.BAG: {"label": "Bag", "category": UnitCategory.COUNT, "abbreviation": "bag"},
    Unit.CASE: {"label": "Case", "category": UnitCategory.COUNT, "abbreviation": "case"},
    Unit.CARTON: {"label": "Carton", "category": UnitCategory.COUNT, "abbreviation": "carton"},
    Unit.GROSS: {"label": "Gross", "category": UnitCategory.COUNT, "abbreviation": "gross"},
}


# Conversion factors (to base units: grams for weight, milliliters for volume)
UNIT_CONVERSIONS = {
    # Weight conversions to grams
    Unit.MILLIGRAM: 0.001,
    Unit.GRAM: 1.0,
    Unit.KILOGRAM: 1000.0,
    Unit.OUNCE: 28.3495,
    Unit.POUND: 453.592,
    
    # Volume conversions to milliliters
    Unit.MILLILITER: 1.0,
    Unit.LITER: 1000.0,
    Unit.FLUID_OUNCE: 29.5735,
    Unit.CUP: 236.588,
    Unit.TABLESPOON: 14.7868,
    Unit.TEASPOON: 4.92892,
    Unit.PINT: 473.176,
    Unit.QUART: 946.353,
    Unit.GALLON: 3785.41,
}


# Common unit variations mapping
UNIT_VARIATIONS = {
    # Weight
    "milligram": Unit.MILLIGRAM,
    "milligrams": Unit.MILLIGRAM,
    "gram": Unit.GRAM,
    "grams": Unit.GRAM,
    "g": Unit.GRAM,
    "kilogram": Unit.KILOGRAM,
    "kilograms": Unit.KILOGRAM,
    "kg": Unit.KILOGRAM,
    "ounce": Unit.OUNCE,
    "ounces": Unit.OUNCE,
    "oz": Unit.OUNCE,
    "pound": Unit.POUND,
    "pounds": Unit.POUND,
    "lb": Unit.POUND,
    "lbs": Unit.POUND,
    
    # Volume
    "milliliter": Unit.MILLILITER,
    "milliliters": Unit.MILLILITER,
    "ml": Unit.MILLILITER,
    "liter": Unit.LITER,
    "liters": Unit.LITER,
    "l": Unit.LITER,
    "fluid ounce": Unit.FLUID_OUNCE,
    "fluid ounces": Unit.FLUID_OUNCE,
    "fl oz": Unit.FLUID_OUNCE,
    "cup": Unit.CUP,
    "cups": Unit.CUP,
    "tablespoon": Unit.TABLESPOON,
    "tablespoons": Unit.TABLESPOON,
    "tbsp": Unit.TABLESPOON,
    "teaspoon": Unit.TEASPOON,
    "teaspoons": Unit.TEASPOON,
    "tsp": Unit.TEASPOON,
    "pint": Unit.PINT,
    "pints": Unit.PINT,
    "pt": Unit.PINT,
    "quart": Unit.QUART,
    "quarts": Unit.QUART,
    "qt": Unit.QUART,
    "gallon": Unit.GALLON,
    "gallons": Unit.GALLON,
    "gal": Unit.GALLON,
    
    # Count
    "each": Unit.EACH,
    "package": Unit.PACKAGE,
    "packages": Unit.PACKAGE,
    "pkg": Unit.PACKAGE,
    "bag": Unit.BAG,
    "bags": Unit.BAG,
    "case": Unit.CASE,
    "cases": Unit.CASE,
    "carton": Unit.CARTON,
    "cartons": Unit.CARTON,
    "gross": Unit.GROSS,
    
    # Legacy units from existing data
    "pcs": Unit.EACH,
    "pieces": Unit.EACH,
    "piece": Unit.EACH,
    "pack": Unit.PACKAGE,
    "bottle": Unit.EACH,
    "can": Unit.EACH,
}


def normalize_unit(unit_string: str) -> str:
    """
    Normalize a unit string to standard format
    """
    if not unit_string:
        return Unit.EACH
    
    normalized = unit_string.lower().strip()
    return UNIT_VARIATIONS.get(normalized, unit_string)


def get_unit_category(unit: str) -> Optional[UnitCategory]:
    """
    Get the category for a unit
    """
    unit_enum = normalize_unit(unit)
    unit_data = UNIT_INFO.get(unit_enum)
    return unit_data["category"] if unit_data else None


def convert_quantity(quantity: float, from_unit: str, to_unit: str) -> Optional[float]:
    """
    Convert quantity from one unit to another
    Returns None if conversion is not possible (different categories)
    """
    from_unit_norm = normalize_unit(from_unit)
    to_unit_norm = normalize_unit(to_unit)
    
    # Check if units are in the same category
    from_category = get_unit_category(from_unit_norm)
    to_category = get_unit_category(to_unit_norm)
    
    if from_category != to_category or not from_category:
        return None
    
    # Count units don't convert
    if from_category == UnitCategory.COUNT:
        return quantity if from_unit_norm == to_unit_norm else None
    
    # Get conversion factors
    from_factor = UNIT_CONVERSIONS.get(from_unit_norm)
    to_factor = UNIT_CONVERSIONS.get(to_unit_norm)
    
    if from_factor is None or to_factor is None:
        return None
    
    # Convert to base unit then to target unit
    base_quantity = quantity * from_factor
    return base_quantity / to_factor