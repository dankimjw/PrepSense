"""Nutrient database configuration and RDA (Recommended Daily Allowance) values."""

from typing import Dict, Any

# USDA-based nutrient RDA values (adult averages)
# Based on FDA Daily Values and USDA Dietary Guidelines
RDA_VALUES = {
    # Macronutrients (grams)
    "protein": 50.0,
    "carbohydrates": 300.0,
    "fiber": 25.0,
    "total_fat": 65.0,
    "saturated_fat": 20.0,
    "trans_fat": 0.0,  # No safe level
    "sugar": 50.0,
    
    # Vitamins (mg unless noted)
    "vitamin_c": 90.0,
    "vitamin_a": 0.9,  # mg (900 mcg)
    "vitamin_d": 0.02,  # mg (20 mcg)
    "vitamin_e": 15.0,
    "vitamin_k": 0.12,  # mg (120 mcg)
    "thiamin": 1.2,
    "riboflavin": 1.3,
    "niacin": 16.0,
    "vitamin_b6": 1.7,
    "folate": 0.4,  # mg (400 mcg)
    "vitamin_b12": 0.0024,  # mg (2.4 mcg)
    "biotin": 0.03,  # mg (30 mcg)
    "pantothenic_acid": 5.0,
    
    # Minerals (mg unless noted)
    "calcium": 1000.0,
    "iron": 18.0,
    "magnesium": 400.0,
    "phosphorus": 1000.0,
    "potassium": 3500.0,
    "sodium": 2300.0,  # Upper limit (not minimum)
    "zinc": 11.0,
    "copper": 0.9,
    "manganese": 2.3,
    "selenium": 0.055,  # mg (55 mcg)
    "chromium": 0.035,  # mg (35 mcg)
    "molybdenum": 0.045,  # mg (45 mcg)
    
    # Special nutrients
    "cholesterol": 300.0,  # Upper limit (not minimum)
    "omega_3": 1.6,  # Alpha-linolenic acid (grams)
    "omega_6": 17.0,  # Linoleic acid (grams)
}

# Nutrients that should be minimized (upper limits)
UPPER_LIMIT_NUTRIENTS = {
    "sodium", "saturated_fat", "trans_fat", "cholesterol", "sugar"
}

# Nutrients that are essential (deficiencies should be flagged)
ESSENTIAL_NUTRIENTS = {
    "protein", "fiber", "vitamin_c", "vitamin_d", "calcium", "iron", "potassium"
}

# Nutrient categories for grouping
NUTRIENT_CATEGORIES = {
    "macronutrients": [
        "protein", "carbohydrates", "fiber", "total_fat", "saturated_fat", "sugar"
    ],
    "vitamins": [
        "vitamin_c", "vitamin_a", "vitamin_d", "vitamin_e", "vitamin_k",
        "thiamin", "riboflavin", "niacin", "vitamin_b6", "folate", "vitamin_b12"
    ],
    "minerals": [
        "calcium", "iron", "magnesium", "phosphorus", "potassium", 
        "sodium", "zinc", "copper", "selenium"
    ],
    "special": [
        "cholesterol", "omega_3", "omega_6"
    ]
}

# Display names for nutrients
NUTRIENT_DISPLAY_NAMES = {
    "protein": "Protein",
    "carbohydrates": "Carbohydrates", 
    "fiber": "Fiber",
    "total_fat": "Total Fat",
    "saturated_fat": "Saturated Fat",
    "trans_fat": "Trans Fat",
    "sugar": "Sugar",
    "vitamin_c": "Vitamin C",
    "vitamin_a": "Vitamin A",
    "vitamin_d": "Vitamin D",
    "vitamin_e": "Vitamin E",
    "vitamin_k": "Vitamin K",
    "thiamin": "Thiamin (B1)",
    "riboflavin": "Riboflavin (B2)",
    "niacin": "Niacin (B3)",
    "vitamin_b6": "Vitamin B6",
    "folate": "Folate",
    "vitamin_b12": "Vitamin B12",
    "calcium": "Calcium",
    "iron": "Iron",
    "magnesium": "Magnesium",
    "phosphorus": "Phosphorus",
    "potassium": "Potassium",
    "sodium": "Sodium",
    "zinc": "Zinc",
    "copper": "Copper",
    "selenium": "Selenium",
    "cholesterol": "Cholesterol",
    "omega_3": "Omega-3 Fatty Acids",
    "omega_6": "Omega-6 Fatty Acids"
}

# Units for display
NUTRIENT_UNITS = {
    "protein": "g",
    "carbohydrates": "g",
    "fiber": "g", 
    "total_fat": "g",
    "saturated_fat": "g",
    "trans_fat": "g",
    "sugar": "g",
    "vitamin_c": "mg",
    "vitamin_a": "mg",
    "vitamin_d": "mg",
    "vitamin_e": "mg",
    "vitamin_k": "mg",
    "thiamin": "mg",
    "riboflavin": "mg",
    "niacin": "mg",
    "vitamin_b6": "mg",
    "folate": "mg",
    "vitamin_b12": "mg",
    "calcium": "mg",
    "iron": "mg",
    "magnesium": "mg",
    "phosphorus": "mg",
    "potassium": "mg",
    "sodium": "mg",
    "zinc": "mg",
    "copper": "mg",
    "selenium": "mg",
    "cholesterol": "mg",
    "omega_3": "g",
    "omega_6": "g"
}

def get_nutrient_gap(consumed: float, nutrient: str) -> float:
    """Calculate nutrient gap (negative = deficit, positive = excess)."""
    rda = RDA_VALUES.get(nutrient, 0)
    
    if nutrient in UPPER_LIMIT_NUTRIENTS:
        # For nutrients with upper limits, positive gap = excess (bad)
        return consumed - rda
    else:
        # For essential nutrients, negative gap = deficit (bad)
        return consumed - rda

def is_nutrient_deficient(consumed: float, nutrient: str, threshold: float = 0.8) -> bool:
    """Check if nutrient consumption is below threshold of RDA."""
    rda = RDA_VALUES.get(nutrient, 0)
    if rda == 0:
        return False
    
    if nutrient in UPPER_LIMIT_NUTRIENTS:
        # For upper limit nutrients, not deficient if under limit
        return False
    else:
        # For essential nutrients, deficient if under threshold
        return consumed < (rda * threshold)

def is_nutrient_excessive(consumed: float, nutrient: str, threshold: float = 1.2) -> bool:
    """Check if nutrient consumption exceeds safe threshold."""
    rda = RDA_VALUES.get(nutrient, 0)
    if rda == 0:
        return False
    
    if nutrient in UPPER_LIMIT_NUTRIENTS:
        # For upper limit nutrients, excessive if over limit
        return consumed > rda
    else:
        # For essential nutrients, excessive if over threshold
        return consumed > (rda * threshold)

def get_priority_nutrients() -> list:
    """Get list of nutrients to prioritize in gap analysis."""
    return list(ESSENTIAL_NUTRIENTS) + ["sodium", "saturated_fat", "sugar"]

def format_nutrient_value(value: float, nutrient: str) -> str:
    """Format nutrient value for display."""
    unit = NUTRIENT_UNITS.get(nutrient, "g")
    
    if value < 0.1:
        return f"{value:.2f} {unit}"
    elif value < 1:
        return f"{value:.1f} {unit}"
    else:
        return f"{value:.0f} {unit}"