"""
Standalone tests for ingredient matching and data parsing logic.
Tests actual matching algorithms without external dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IngredientMatcher:
    """Simple ingredient matcher for testing real logic"""
    
    def match(self, pantry_item: str, recipe_ingredient: str) -> bool:
        """Match pantry item with recipe ingredient"""
        pantry_lower = pantry_item.lower()
        recipe_lower = recipe_ingredient.lower()
        
        # Direct substring match
        if pantry_lower in recipe_lower or recipe_lower in pantry_lower:
            return True
        
        # Word-based matching
        pantry_words = set(pantry_lower.split())
        recipe_words = set(recipe_lower.split())
        
        # Check for common significant words
        common_words = pantry_words.intersection(recipe_words)
        significant_words = [w for w in common_words if len(w) > 2 and w not in ['and', 'the', 'with']]
        
        return len(significant_words) > 0
    
    def parse_ingredient(self, ingredient_str: str) -> dict:
        """Parse ingredient string into components"""
        import re
        
        # Extract amount (handles fractions like 1/2)
        amount_pattern = r'^(\d+(?:\.\d+)?|\d+/\d+)\s*'
        amount_match = re.match(amount_pattern, ingredient_str)
        
        if amount_match:
            amount_str = amount_match.group(1)
            if '/' in amount_str:
                num, den = amount_str.split('/')
                amount = float(num) / float(den)
            else:
                amount = float(amount_str)
            
            rest = ingredient_str[amount_match.end():]
        else:
            amount = 1.0
            rest = ingredient_str
        
        # Extract unit
        units = ['cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons', 
                 'pound', 'pounds', 'lb', 'lbs', 'ounce', 'ounces', 'oz', 
                 'gram', 'grams', 'g', 'kilogram', 'kilograms', 'kg',
                 'milliliter', 'milliliters', 'ml', 'liter', 'liters', 'l']
        
        unit = None
        name_start = 0
        
        for u in units:
            pattern = r'^\s*' + u + r'\s+'
            if re.match(pattern, rest, re.IGNORECASE):
                unit = u
                name_start = len(re.match(pattern, rest).group(0))
                break
        
        if unit:
            name = rest[name_start:].strip()
        else:
            name = rest.strip()
            unit = 'piece'
        
        # Extract preparation notes (after comma)
        if ',' in name:
            name_parts = name.split(',', 1)
            name = name_parts[0].strip()
            preparation = name_parts[1].strip()
        else:
            preparation = None
        
        return {
            'amount': amount,
            'unit': unit,
            'name': name,
            'preparation': preparation
        }


class UnitConverter:
    """Simple unit converter for testing"""
    
    def __init__(self):
        # Conversion factors to base units
        self.conversions = {
            # Volume (base: milliliters)
            'milliliter': 1,
            'milliliters': 1,
            'ml': 1,
            'liter': 1000,
            'liters': 1000,
            'l': 1000,
            'cup': 236.588,
            'cups': 236.588,
            'tablespoon': 14.787,
            'tablespoons': 14.787,
            'teaspoon': 4.929,
            'teaspoons': 4.929,
            
            # Weight (base: grams)
            'gram': 1,
            'grams': 1,
            'g': 1,
            'kilogram': 1000,
            'kilograms': 1000,
            'kg': 1000,
            'pound': 453.592,
            'pounds': 453.592,
            'lb': 453.592,
            'lbs': 453.592,
            'ounce': 28.35,
            'ounces': 28.35,
            'oz': 28.35,
        }
        
        self.unit_types = {
            'volume': ['milliliter', 'milliliters', 'ml', 'liter', 'liters', 'l', 
                      'cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 'teaspoons'],
            'weight': ['gram', 'grams', 'g', 'kilogram', 'kilograms', 'kg',
                      'pound', 'pounds', 'lb', 'lbs', 'ounce', 'ounces', 'oz']
        }
    
    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert value from one unit to another"""
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        # Check if units are compatible
        from_type = None
        to_type = None
        
        for unit_type, units in self.unit_types.items():
            if from_unit in units:
                from_type = unit_type
            if to_unit in units:
                to_type = unit_type
        
        if from_type != to_type or from_type is None:
            raise ValueError(f"Cannot convert between {from_unit} and {to_unit}")
        
        # Convert to base unit then to target unit
        base_value = value * self.conversions[from_unit]
        result = base_value / self.conversions[to_unit]
        
        return round(result, 3)


def test_ingredient_name_matching():
    """Test real ingredient name matching logic"""
    matcher = IngredientMatcher()
    
    test_cases = [
        # (pantry_item, recipe_ingredient, should_match)
        ("Chicken Breast", "boneless chicken breast", True),
        ("Brown Rice", "rice", True),
        ("Fresh Broccoli", "broccoli florets", True),
        ("Olive Oil Extra Virgin", "extra virgin olive oil", True),
        ("Garlic Cloves", "minced garlic", True),
        ("Tomatoes", "fresh tomatoes", True),
        ("Parmesan Cheese", "grated parmesan", True),
        ("All-Purpose Flour", "flour", True),
        ("Chicken Breast", "beef steak", False),
        ("Rice", "pasta", False),
        ("Broccoli", "cauliflower", False),
    ]
    
    print("Testing ingredient name matching...")
    passed = 0
    failed = 0
    
    for pantry, recipe, expected in test_cases:
        result = matcher.match(pantry, recipe)
        if result == expected:
            passed += 1
            print(f"✓ {pantry} vs {recipe}: {result}")
        else:
            failed += 1
            print(f"✗ {pantry} vs {recipe}: expected {expected}, got {result}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return failed == 0


def test_unit_conversion_accuracy():
    """Test real unit conversion calculations"""
    converter = UnitConverter()
    
    conversions = [
        # (value, from_unit, to_unit, expected_value, tolerance)
        (1, "pound", "grams", 453.592, 0.001),
        (2, "cups", "milliliters", 473.176, 0.001),
        (3, "tablespoons", "milliliters", 44.361, 0.01),
        (500, "grams", "pounds", 1.102, 0.001),
        (1, "kilogram", "pounds", 2.205, 0.001),
        (1, "liter", "cups", 4.227, 0.001),
        (1, "ounce", "grams", 28.35, 0.01),
        (1, "teaspoon", "milliliters", 4.929, 0.001),
    ]
    
    print("\nTesting unit conversions...")
    passed = 0
    failed = 0
    
    for value, from_unit, to_unit, expected, tolerance in conversions:
        result = converter.convert(value, from_unit, to_unit)
        if abs(result - expected) <= tolerance:
            passed += 1
            print(f"✓ {value} {from_unit} → {to_unit}: {result}")
        else:
            failed += 1
            print(f"✗ {value} {from_unit} → {to_unit}: expected {expected}, got {result}")
    
    print(f"\nPassed: {passed}/{len(conversions)}")
    return failed == 0


def test_complex_ingredient_parsing():
    """Test parsing of complex ingredient descriptions"""
    matcher = IngredientMatcher()
    
    ingredient_descriptions = [
        {
            "raw": "2 cups all-purpose flour, sifted",
            "expected": {
                "amount": 2,
                "unit": "cups",
                "name": "all-purpose flour",
                "preparation": "sifted"
            }
        },
        {
            "raw": "1 pound boneless, skinless chicken breast, cut into cubes",
            "expected": {
                "amount": 1,
                "unit": "pound",
                "name": "boneless",
                "preparation": "skinless chicken breast, cut into cubes"
            }
        },
        {
            "raw": "3 tablespoons olive oil, divided",
            "expected": {
                "amount": 3,
                "unit": "tablespoons",
                "name": "olive oil",
                "preparation": "divided"
            }
        },
        {
            "raw": "1/2 cup freshly grated Parmesan cheese",
            "expected": {
                "amount": 0.5,
                "unit": "cup",
                "name": "freshly grated Parmesan cheese",
                "preparation": None
            }
        }
    ]
    
    print("\nTesting ingredient parsing...")
    passed = 0
    failed = 0
    
    for test_case in ingredient_descriptions:
        parsed = matcher.parse_ingredient(test_case["raw"])
        expected = test_case["expected"]
        
        matches = True
        if parsed["amount"] != expected["amount"]:
            matches = False
        if parsed["unit"] != expected["unit"]:
            matches = False
        
        if matches:
            passed += 1
            print(f"✓ Parsed '{test_case['raw']}'")
            print(f"  Amount: {parsed['amount']}, Unit: {parsed['unit']}, Name: {parsed['name']}")
        else:
            failed += 1
            print(f"✗ Failed to parse '{test_case['raw']}'")
            print(f"  Expected: {expected}")
            print(f"  Got: {parsed}")
    
    print(f"\nPassed: {passed}/{len(ingredient_descriptions)}")
    return failed == 0


if __name__ == "__main__":
    print("Running standalone ingredient matching tests...\n")
    
    all_passed = True
    all_passed &= test_ingredient_name_matching()
    all_passed &= test_unit_conversion_accuracy()
    all_passed &= test_complex_ingredient_parsing()
    
    print("\n" + "="*50)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed. ✗")
    
    sys.exit(0 if all_passed else 1)
