"""
Utility to convert decimal quantities to user-friendly fractions
"""
from fractions import Fraction
from typing import Union


def decimal_to_fraction(value: Union[float, str], max_denominator: int = 16) -> str:
    """
    Convert a decimal value to a readable fraction string.
    
    Args:
        value: The decimal value to convert (float or string)
        max_denominator: Maximum denominator for fraction simplification
        
    Returns:
        String representation of the fraction (e.g., "3/4", "1 1/2", "2")
    """
    if not value or value == 0:
        return "0"
    
    try:
        # Convert to float if string
        if isinstance(value, str):
            decimal_value = float(value)
        else:
            decimal_value = float(value)
            
        # Handle negative values
        is_negative = decimal_value < 0
        decimal_value = abs(decimal_value)
        
        # Convert to fraction
        frac = Fraction(decimal_value).limit_denominator(max_denominator)
        
        # Handle whole numbers
        if frac.denominator == 1:
            result = str(frac.numerator)
        else:
            # Handle mixed numbers (e.g., 1 1/2)
            whole_part = frac.numerator // frac.denominator
            remainder = frac.numerator % frac.denominator
            
            if whole_part > 0:
                if remainder > 0:
                    result = f"{whole_part} {remainder}/{frac.denominator}"
                else:
                    result = str(whole_part)
            else:
                result = f"{remainder}/{frac.denominator}"
        
        return f"-{result}" if is_negative else result
        
    except (ValueError, TypeError):
        # If conversion fails, return original value as string
        return str(value)


def format_quantity_with_fraction(quantity: Union[float, str], unit: str = "") -> str:
    """
    Format a quantity with proper fraction display and unit.
    
    Args:
        quantity: The quantity to format
        unit: The unit of measurement
        
    Returns:
        Formatted string (e.g., "3/4 cups", "1 1/2 tsp")
    """
    fraction_str = decimal_to_fraction(quantity)
    
    if unit and unit.strip():
        return f"{fraction_str} {unit.strip()}"
    return fraction_str


# Common fraction mappings for quick lookup
COMMON_FRACTIONS = {
    0.125: "1/8",
    0.25: "1/4", 
    0.333: "1/3",
    0.375: "3/8",
    0.5: "1/2",
    0.625: "5/8",
    0.667: "2/3",
    0.75: "3/4",
    0.875: "7/8",
    1.25: "1 1/4",
    1.33: "1 1/3",
    1.5: "1 1/2",
    1.67: "1 2/3",
    1.75: "1 3/4",
    2.5: "2 1/2",
    2.67: "2 2/3",
    2.75: "2 3/4"
}


def quick_fraction_lookup(value: Union[float, str]) -> str:
    """
    Quick lookup for common fractions, fallback to calculation.
    """
    try:
        decimal_value = float(value) if isinstance(value, str) else value
        
        # Round to 3 decimal places for lookup
        rounded = round(decimal_value, 3)
        
        if rounded in COMMON_FRACTIONS:
            return COMMON_FRACTIONS[rounded]
            
        # Fallback to calculation
        return decimal_to_fraction(decimal_value)
        
    except (ValueError, TypeError):
        return str(value)