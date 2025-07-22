"""
Real tests for ingredient matching and data parsing logic.
Tests actual matching algorithms without mocks.
"""

import pytest
from backend_gateway.services.ingredient_matcher import IngredientMatcher
from backend_gateway.services.unit_converter import UnitConverter


class TestRealIngredientMatching:
    """Test actual ingredient matching and unit conversion logic"""
    
    @pytest.fixture
    def ingredient_matcher(self):
        """Create real ingredient matcher instance"""
        return IngredientMatcher()
    
    @pytest.fixture
    def unit_converter(self):
        """Create real unit converter instance"""
        return UnitConverter()
    
    def test_ingredient_name_matching(self, ingredient_matcher):
        """Test real ingredient name matching logic"""
        
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
        
        for pantry, recipe, expected in test_cases:
            result = ingredient_matcher.match(pantry, recipe)
            assert result == expected, f"Failed: {pantry} vs {recipe}, expected {expected}, got {result}"
    
    def test_unit_conversion_accuracy(self, unit_converter):
        """Test real unit conversion calculations"""
        
        conversions = [
            # (value, from_unit, to_unit, expected_value, tolerance)
            (1, "pound", "grams", 453.592, 0.001),
            (2, "cups", "milliliters", 473.176, 0.001),
            (3, "tablespoons", "milliliters", 44.36, 0.01),
            (500, "grams", "pounds", 1.102, 0.001),
            (1, "kilogram", "pounds", 2.205, 0.001),
            (1, "liter", "cups", 4.227, 0.001),
            (1, "ounce", "grams", 28.35, 0.01),
            (1, "teaspoon", "milliliters", 4.929, 0.001),
        ]
        
        for value, from_unit, to_unit, expected, tolerance in conversions:
            result = unit_converter.convert(value, from_unit, to_unit)
            assert abs(result - expected) <= tolerance, \
                f"Conversion failed: {value} {from_unit} to {to_unit}, expected {expected}, got {result}"
    
    def test_complex_ingredient_parsing(self, ingredient_matcher):
        """Test parsing of complex ingredient descriptions"""
        
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
                    "name": "chicken breast",
                    "preparation": "boneless, skinless, cut into cubes"
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
                    "name": "Parmesan cheese",
                    "preparation": "freshly grated"
                }
            }
        ]
        
        for test_case in ingredient_descriptions:
            parsed = ingredient_matcher.parse_ingredient(test_case["raw"])
            expected = test_case["expected"]
            
            assert parsed["amount"] == expected["amount"]
            assert parsed["unit"] == expected["unit"]
            assert expected["name"].lower() in parsed["name"].lower()
    
    def test_fuzzy_matching_with_typos(self, ingredient_matcher):
        """Test ingredient matching with common typos and variations"""
        
        typo_cases = [
            ("chicken breast", "chiken breast", True),  # Single letter typo
            ("broccoli", "brocoli", True),  # Missing letter
            ("tomatoes", "tomatos", True),  # Common misspelling
            ("zucchini", "zuchini", True),  # Common misspelling
            ("worcestershire sauce", "worchester sauce", True),  # Common abbreviation
        ]
        
        for correct, typo, should_match in typo_cases:
            result = ingredient_matcher.fuzzy_match(correct, typo, threshold=0.8)
            assert result == should_match, f"Fuzzy match failed: {correct} vs {typo}"
    
    def test_ingredient_category_detection(self, ingredient_matcher):
        """Test automatic category detection for ingredients"""
        
        category_tests = [
            ("Chicken Breast", "protein"),
            ("Ground Beef", "protein"),
            ("Salmon Fillet", "protein"),
            ("White Rice", "grain"),
            ("Pasta", "grain"),
            ("Bread", "grain"),
            ("Broccoli", "vegetable"),
            ("Carrots", "vegetable"),
            ("Spinach", "vegetable"),
            ("Apple", "fruit"),
            ("Banana", "fruit"),
            ("Milk", "dairy"),
            ("Cheddar Cheese", "dairy"),
            ("Yogurt", "dairy"),
            ("Olive Oil", "oil"),
            ("Butter", "dairy"),
            ("Salt", "seasoning"),
            ("Black Pepper", "seasoning"),
        ]
        
        for ingredient, expected_category in category_tests:
            category = ingredient_matcher.detect_category(ingredient)
            assert category == expected_category, \
                f"Category detection failed for {ingredient}: expected {expected_category}, got {category}"
    
    def test_quantity_compatibility(self, unit_converter):
        """Test checking if quantities are compatible for subtraction"""
        
        compatibility_tests = [
            # (unit1, unit2, compatible)
            ("cups", "milliliters", True),  # Volume to volume
            ("pounds", "grams", True),  # Weight to weight
            ("cups", "pounds", False),  # Volume to weight
            ("teaspoons", "tablespoons", True),  # Same measurement type
            ("pieces", "grams", False),  # Count to weight
            ("cloves", "teaspoons", False),  # Count to volume
        ]
        
        for unit1, unit2, expected in compatibility_tests:
            result = unit_converter.are_compatible(unit1, unit2)
            assert result == expected, \
                f"Compatibility check failed: {unit1} and {unit2}, expected {expected}, got {result}"
    
    def test_ingredient_substitution_suggestions(self, ingredient_matcher):
        """Test ingredient substitution logic"""
        
        substitution_tests = [
            ("butter", ["margarine", "coconut oil", "olive oil"]),
            ("all-purpose flour", ["whole wheat flour", "almond flour", "coconut flour"]),
            ("milk", ["almond milk", "soy milk", "oat milk"]),
            ("eggs", ["flax eggs", "chia eggs", "applesauce"]),
            ("sugar", ["honey", "maple syrup", "stevia"]),
        ]
        
        for ingredient, expected_subs in substitution_tests:
            substitutions = ingredient_matcher.get_substitutions(ingredient)
            
            # Check that at least some expected substitutions are suggested
            found_subs = [sub for sub in expected_subs if sub in substitutions]
            assert len(found_subs) > 0, \
                f"No expected substitutions found for {ingredient}. Got: {substitutions}"
    
    def test_recipe_ingredient_aggregation(self, ingredient_matcher):
        """Test aggregating same ingredients with different units"""
        
        recipe_ingredients = [
            {"name": "olive oil", "amount": 2, "unit": "tablespoons"},
            {"name": "olive oil", "amount": 1, "unit": "teaspoon"},
            {"name": "chicken breast", "amount": 1, "unit": "pound"},
            {"name": "chicken breast", "amount": 200, "unit": "grams"},
        ]
        
        aggregated = ingredient_matcher.aggregate_ingredients(recipe_ingredients)
        
        # Should have only 2 ingredients after aggregation
        assert len(aggregated) == 2
        
        # Check olive oil aggregation (2 tbsp + 1 tsp = ~2.33 tbsp)
        olive_oil = next(ing for ing in aggregated if ing["name"] == "olive oil")
        assert olive_oil["unit"] == "tablespoons"
        assert abs(olive_oil["amount"] - 2.33) < 0.1
        
        # Check chicken aggregation (1 lb + 200g = ~1.44 lb)
        chicken = next(ing for ing in aggregated if ing["name"] == "chicken breast")
        assert chicken["unit"] == "pound"
        assert abs(chicken["amount"] - 1.44) < 0.1
