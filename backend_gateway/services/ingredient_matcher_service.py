"""
Ingredient Matcher Service
Advanced ingredient matching with substitution awareness and fuzzy matching
"""

import difflib
import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IngredientMatcherService:
    """Advanced ingredient matching with substitution awareness"""

    def __init__(self):
        # Ingredient categories for better matching
        self.ingredient_categories = {
            "proteins": {
                "chicken": [
                    "chicken breast",
                    "chicken thigh",
                    "chicken wings",
                    "whole chicken",
                    "chicken drumsticks",
                    "rotisserie chicken",
                    "chicken tenders",
                    "ground chicken",
                ],
                "beef": [
                    "ground beef",
                    "beef steak",
                    "beef roast",
                    "beef strips",
                    "sirloin",
                    "ribeye",
                    "chuck roast",
                    "beef tenderloin",
                    "stew meat",
                    "hamburger meat",
                ],
                "pork": [
                    "pork chops",
                    "ground pork",
                    "pork tenderloin",
                    "bacon",
                    "ham",
                    "pork shoulder",
                    "pork belly",
                    "italian sausage",
                    "breakfast sausage",
                    "prosciutto",
                ],
                "seafood": [
                    "salmon",
                    "tuna",
                    "shrimp",
                    "cod",
                    "tilapia",
                    "halibut",
                    "scallops",
                    "crab",
                    "lobster",
                    "mahi mahi",
                    "sea bass",
                    "catfish",
                    "trout",
                    "sardines",
                ],
                "vegetarian": [
                    "tofu",
                    "tempeh",
                    "beans",
                    "lentils",
                    "chickpeas",
                    "black beans",
                    "kidney beans",
                    "pinto beans",
                    "white beans",
                    "quinoa",
                    "eggs",
                    "paneer",
                    "seitan",
                ],
            },
            "grains": {
                "rice": [
                    "white rice",
                    "brown rice",
                    "jasmine rice",
                    "basmati rice",
                    "wild rice",
                    "arborio rice",
                    "sushi rice",
                    "long grain rice",
                    "short grain rice",
                    "instant rice",
                ],
                "pasta": [
                    "spaghetti",
                    "penne",
                    "fusilli",
                    "linguine",
                    "macaroni",
                    "fettuccine",
                    "rigatoni",
                    "angel hair",
                    "bow tie pasta",
                    "orzo",
                    "lasagna noodles",
                    "rotini",
                    "shells",
                ],
                "bread": [
                    "white bread",
                    "whole wheat bread",
                    "sourdough",
                    "baguette",
                    "ciabatta",
                    "focaccia",
                    "naan",
                    "pita bread",
                    "tortillas",
                    "rolls",
                    "english muffins",
                    "bagels",
                ],
                "other_grains": [
                    "quinoa",
                    "couscous",
                    "bulgur",
                    "farro",
                    "barley",
                    "millet",
                    "buckwheat",
                    "polenta",
                    "grits",
                ],
            },
            "dairy": {
                "milk": [
                    "whole milk",
                    "2% milk",
                    "skim milk",
                    "almond milk",
                    "soy milk",
                    "oat milk",
                    "coconut milk",
                    "cashew milk",
                    "evaporated milk",
                    "condensed milk",
                    "buttermilk",
                ],
                "cheese": [
                    "cheddar",
                    "mozzarella",
                    "parmesan",
                    "swiss",
                    "feta",
                    "gouda",
                    "brie",
                    "blue cheese",
                    "goat cheese",
                    "ricotta",
                    "cream cheese",
                    "cottage cheese",
                    "monterey jack",
                ],
                "yogurt": [
                    "plain yogurt",
                    "greek yogurt",
                    "vanilla yogurt",
                    "low-fat yogurt",
                    "non-fat yogurt",
                    "coconut yogurt",
                    "soy yogurt",
                    "kefir",
                ],
                "butter_cream": [
                    "butter",
                    "margarine",
                    "heavy cream",
                    "sour cream",
                    "half and half",
                    "whipping cream",
                    "creme fraiche",
                ],
            },
            "vegetables": {
                "leafy": [
                    "lettuce",
                    "spinach",
                    "kale",
                    "arugula",
                    "romaine",
                    "iceberg lettuce",
                    "mixed greens",
                    "collard greens",
                    "swiss chard",
                    "bok choy",
                    "cabbage",
                ],
                "root": [
                    "potato",
                    "sweet potato",
                    "carrot",
                    "onion",
                    "garlic",
                    "beet",
                    "turnip",
                    "radish",
                    "parsnip",
                    "ginger",
                    "shallot",
                    "yam",
                ],
                "nightshade": [
                    "tomato",
                    "bell pepper",
                    "eggplant",
                    "chili pepper",
                    "jalapeno",
                    "poblano",
                    "cherry tomatoes",
                    "roma tomatoes",
                ],
                "cruciferous": [
                    "broccoli",
                    "cauliflower",
                    "brussels sprouts",
                    "cabbage",
                    "bok choy",
                    "kohlrabi",
                ],
                "squash": [
                    "zucchini",
                    "yellow squash",
                    "butternut squash",
                    "acorn squash",
                    "pumpkin",
                    "spaghetti squash",
                ],
            },
            "pantry_staples": {
                "oils": [
                    "olive oil",
                    "vegetable oil",
                    "canola oil",
                    "coconut oil",
                    "sesame oil",
                    "avocado oil",
                    "grapeseed oil",
                    "peanut oil",
                ],
                "vinegars": [
                    "white vinegar",
                    "apple cider vinegar",
                    "balsamic vinegar",
                    "rice vinegar",
                    "red wine vinegar",
                    "white wine vinegar",
                ],
                "sweeteners": [
                    "sugar",
                    "brown sugar",
                    "honey",
                    "maple syrup",
                    "agave",
                    "corn syrup",
                    "molasses",
                    "stevia",
                    "coconut sugar",
                ],
                "flours": [
                    "all-purpose flour",
                    "whole wheat flour",
                    "bread flour",
                    "cake flour",
                    "almond flour",
                    "coconut flour",
                    "rice flour",
                ],
            },
        }

        # Substitution rules with confidence scores
        self.substitutions = {
            # Dairy substitutions
            "butter": [
                ("margarine", 1.0),
                ("coconut oil", 0.9),
                ("olive oil", 0.8),
                ("vegetable oil", 0.7),
                ("applesauce", 0.6),  # for baking
            ],
            "milk": [
                ("heavy cream", 0.9),  # diluted
                ("yogurt", 0.8),  # thinned
                ("sour cream", 0.7),  # thinned
                ("almond milk", 0.9),
                ("soy milk", 0.9),
                ("oat milk", 0.9),
            ],
            "eggs": [
                ("flax egg", 0.8),  # 1 tbsp ground flax + 3 tbsp water
                ("chia egg", 0.8),  # 1 tbsp chia seeds + 3 tbsp water
                ("applesauce", 0.7),  # 1/4 cup per egg
                ("mashed banana", 0.7),
                ("silken tofu", 0.6),  # 1/4 cup per egg
            ],
            # Sweetener substitutions
            "sugar": [
                ("honey", 0.9),
                ("maple syrup", 0.9),
                ("agave nectar", 0.8),
                ("brown sugar", 1.0),
                ("coconut sugar", 0.9),
            ],
            # Flour substitutions
            "all-purpose flour": [
                ("whole wheat flour", 0.9),
                ("almond flour", 0.7),  # different ratios needed
                ("coconut flour", 0.6),  # very different ratios
                ("oat flour", 0.8),
                ("gluten-free flour blend", 0.9),
            ],
            # Protein substitutions
            "chicken breast": [
                ("chicken thigh", 0.9),
                ("turkey breast", 0.9),
                ("pork tenderloin", 0.8),
                ("firm tofu", 0.7),
                ("tempeh", 0.7),
            ],
            "ground beef": [
                ("ground turkey", 0.9),
                ("ground chicken", 0.9),
                ("ground pork", 0.8),
                ("lentils", 0.7),  # for vegetarian
                ("mushrooms", 0.6),  # for texture
            ],
        }

        # Common unit conversions
        self.unit_conversions = {
            "cup": {"ml": 237, "l": 0.237, "oz": 8, "tbsp": 16, "tsp": 48},
            "tbsp": {"ml": 15, "tsp": 3, "cup": 0.0625, "oz": 0.5},
            "tsp": {"ml": 5, "tbsp": 0.333, "cup": 0.0208},
            "lb": {"kg": 0.453, "g": 453, "oz": 16},
            "oz": {"g": 28.35, "lb": 0.0625, "kg": 0.0283},
            "kg": {"lb": 2.205, "g": 1000, "oz": 35.274},
            "g": {"oz": 0.0353, "lb": 0.0022, "kg": 0.001},
        }

    def match_recipe_to_pantry(
        self,
        recipe_ingredients: List[str],
        pantry_items: List[Dict],
        allow_substitutions: bool = True,
    ) -> Dict:
        """
        Match recipe ingredients to pantry with substitution suggestions

        Args:
            recipe_ingredients: List of recipe ingredient strings
            pantry_items: List of pantry item dictionaries
            allow_substitutions: Whether to suggest substitutions

        Returns:
            Dictionary with matching results
        """
        results = {
            "perfect_matches": [],
            "category_matches": [],
            "possible_substitutions": [],
            "missing_ingredients": [],
            "match_score": 0.0,
            "substitution_score": 0.0,
            "can_make_with_substitutions": False,
            "total_confidence": 0.0,
        }

        # Create searchable pantry
        pantry_search = self._create_pantry_search_index(pantry_items)

        for ingredient in recipe_ingredients:
            # Parse ingredient to extract name and quantity
            parsed = self._parse_ingredient(ingredient)
            ingredient_name = parsed["name"]

            # Try different matching strategies
            match_result = self._find_best_match(ingredient_name, pantry_search, pantry_items)

            if match_result["match_type"] == "perfect":
                results["perfect_matches"].append(
                    {
                        "recipe_ingredient": ingredient,
                        "pantry_item": match_result["pantry_item"],
                        "confidence": match_result["confidence"],
                    }
                )
            elif match_result["match_type"] == "category":
                results["category_matches"].append(
                    {
                        "recipe_ingredient": ingredient,
                        "pantry_item": match_result["pantry_item"],
                        "category": match_result["category"],
                        "confidence": match_result["confidence"],
                    }
                )
            elif allow_substitutions:
                # Look for substitutions
                substitution = self._find_substitution(ingredient_name, pantry_search)
                if substitution:
                    results["possible_substitutions"].append(
                        {
                            "recipe_ingredient": ingredient,
                            "suggested_substitute": substitution["substitute"],
                            "pantry_item": substitution["pantry_item"],
                            "confidence": substitution["confidence"],
                            "notes": substitution.get("notes", ""),
                        }
                    )
                else:
                    results["missing_ingredients"].append(
                        {
                            "ingredient": ingredient,
                            "parsed_name": ingredient_name,
                            "suggestions": self._suggest_alternatives(ingredient_name),
                        }
                    )
            else:
                results["missing_ingredients"].append(
                    {"ingredient": ingredient, "parsed_name": ingredient_name}
                )

        # Calculate scores
        total_ingredients = len(recipe_ingredients)
        if total_ingredients > 0:
            perfect_count = len(results["perfect_matches"])
            category_count = len(results["category_matches"])
            substitution_count = len(results["possible_substitutions"])

            results["match_score"] = (perfect_count + category_count * 0.8) / total_ingredients
            results["substitution_score"] = substitution_count / total_ingredients
            results["can_make_with_substitutions"] = (
                perfect_count + category_count + substitution_count == total_ingredients
            )

            # Calculate total confidence
            total_confidence = 0
            confidence_count = 0

            for match_list in [results["perfect_matches"], results["category_matches"]]:
                for match in match_list:
                    total_confidence += match.get("confidence", 0)
                    confidence_count += 1

            for sub in results["possible_substitutions"]:
                total_confidence += sub.get("confidence", 0) * 0.8  # Lower weight for substitutions
                confidence_count += 1

            results["total_confidence"] = (
                total_confidence / confidence_count if confidence_count > 0 else 0
            )

        return results

    def _create_pantry_search_index(self, pantry_items: List[Dict]) -> Dict:
        """Create searchable index of pantry items"""
        index = {"by_name": {}, "by_category": defaultdict(list), "normalized": {}}

        for item in pantry_items:
            name = item.get("product_name", "").lower()
            if not name:
                continue

            # Store by exact name
            index["by_name"][name] = item

            # Store by normalized name
            normalized = self._normalize_ingredient_name(name)
            index["normalized"][normalized] = item

            # Categorize item
            category = self._categorize_ingredient(name)
            if category:
                index["by_category"][category].append(item)

        return index

    def _parse_ingredient(self, ingredient_string: str) -> Dict:
        """Parse ingredient string to extract components"""
        result = {
            "original": ingredient_string,
            "quantity": None,
            "unit": None,
            "name": ingredient_string,
            "preparation": None,
        }

        # Remove parenthetical notes
        ingredient_clean = re.sub(r"\([^)]*\)", "", ingredient_string).strip()

        # Extract quantity and unit
        quantity_pattern = r"^([\d/.]+)\s*([a-zA-Z]+)?\s+"
        match = re.match(quantity_pattern, ingredient_clean)

        if match:
            result["quantity"] = match.group(1)
            if match.group(2):
                result["unit"] = match.group(2).lower()
            # Rest is the ingredient name
            result["name"] = ingredient_clean[match.end() :].strip()

        # Extract preparation methods
        prep_words = ["chopped", "diced", "sliced", "minced", "grated", "shredded"]
        for prep in prep_words:
            if prep in result["name"].lower():
                result["preparation"] = prep
                result["name"] = result["name"].lower().replace(prep, "").strip()

        return result

    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalize ingredient name for matching"""
        # Convert to lowercase
        normalized = name.lower().strip()

        # Remove common words
        remove_words = [
            "fresh",
            "frozen",
            "canned",
            "dried",
            "organic",
            "large",
            "small",
            "medium",
            "ripe",
            "raw",
            "cooked",
            "whole",
            "ground",
            "powdered",
        ]

        for word in remove_words:
            normalized = normalized.replace(word, "").strip()

        # Remove extra spaces
        normalized = " ".join(normalized.split())

        # Remove plurals (simple)
        if normalized.endswith("es"):
            normalized = normalized[:-2]
        elif normalized.endswith("s") and not normalized.endswith("ss"):
            normalized = normalized[:-1]

        return normalized

    def _categorize_ingredient(self, ingredient_name: str) -> Optional[str]:
        """Categorize an ingredient"""
        ingredient_lower = ingredient_name.lower()

        for main_category, subcategories in self.ingredient_categories.items():
            for subcategory, items in subcategories.items():
                for item in items:
                    if item in ingredient_lower or ingredient_lower in item:
                        return f"{main_category}.{subcategory}"

        return None

    def _find_best_match(
        self, ingredient_name: str, pantry_index: Dict, pantry_items: List[Dict]
    ) -> Dict:
        """Find the best match for an ingredient in the pantry"""
        ingredient_lower = ingredient_name.lower()
        normalized_ingredient = self._normalize_ingredient_name(ingredient_name)

        # 1. Try exact match
        if ingredient_lower in pantry_index["by_name"]:
            return {
                "match_type": "perfect",
                "pantry_item": pantry_index["by_name"][ingredient_lower],
                "confidence": 1.0,
            }

        # 2. Try normalized match
        if normalized_ingredient in pantry_index["normalized"]:
            return {
                "match_type": "perfect",
                "pantry_item": pantry_index["normalized"][normalized_ingredient],
                "confidence": 0.95,
            }

        # 3. Try fuzzy matching
        best_fuzzy_match = self._fuzzy_match_ingredient(
            ingredient_name, list(pantry_index["by_name"].keys())
        )

        if best_fuzzy_match and best_fuzzy_match["score"] > 0.8:
            return {
                "match_type": "perfect",
                "pantry_item": pantry_index["by_name"][best_fuzzy_match["match"]],
                "confidence": best_fuzzy_match["score"],
            }

        # No match found
        return {"match_type": "none", "pantry_item": None, "confidence": 0.0}

    def _fuzzy_match_ingredient(self, ingredient: str, pantry_names: List[str]) -> Optional[Dict]:
        """Perform fuzzy matching for ingredients"""
        if not pantry_names:
            return None

        # Get close matches
        matches = difflib.get_close_matches(ingredient.lower(), pantry_names, n=1, cutoff=0.6)

        if matches:
            # Calculate similarity score
            score = difflib.SequenceMatcher(None, ingredient.lower(), matches[0]).ratio()

            return {"match": matches[0], "score": score}

        return None

    def _find_substitution(self, ingredient_name: str, pantry_index: Dict) -> Optional[Dict]:
        """Find substitution for missing ingredient"""
        ingredient_lower = ingredient_name.lower()

        # Check if we have substitution rules for this ingredient
        for base_ingredient, substitutes in self.substitutions.items():
            if base_ingredient in ingredient_lower or ingredient_lower in base_ingredient:
                # Try each substitute
                for substitute, confidence in substitutes:
                    # Check if substitute is in pantry
                    if substitute in pantry_index["by_name"]:
                        return {
                            "substitute": substitute,
                            "pantry_item": pantry_index["by_name"][substitute],
                            "confidence": confidence,
                            "notes": f"Can use {substitute} instead of {ingredient_name}",
                        }

        return None

    def _suggest_alternatives(self, ingredient_name: str) -> List[str]:
        """Suggest alternative ingredients that might work"""
        suggestions = []

        # Get ingredient category
        category = self._categorize_ingredient(ingredient_name)
        if category:
            main_cat, sub_cat = category.split(".")
            # Suggest other items from the same subcategory
            similar_items = self.ingredient_categories.get(main_cat, {}).get(sub_cat, [])
            suggestions.extend(similar_items[:3])

        # Add any known substitutes
        for base, subs in self.substitutions.items():
            if base.lower() in ingredient_name.lower():
                suggestions.extend([sub[0] for sub in subs[:2]])

        return list(set(suggestions))[:5]  # Return up to 5 unique suggestions

    def calculate_quantity_match(self, recipe_quantity: Dict, pantry_quantity: Dict) -> Dict:
        """
        Calculate if pantry has enough quantity for recipe

        Args:
            recipe_quantity: {'quantity': 2, 'unit': 'cup'}
            pantry_quantity: {'quantity': 500, 'unit': 'ml'}

        Returns:
            Dictionary with match info
        """
        # Convert to common unit
        recipe_unit = recipe_quantity.get("unit", "").lower()
        pantry_unit = pantry_quantity.get("unit", "").lower()

        if recipe_unit == pantry_unit:
            # Direct comparison
            has_enough = pantry_quantity["quantity"] >= recipe_quantity["quantity"]
            percentage = (pantry_quantity["quantity"] / recipe_quantity["quantity"]) * 100
        else:
            # Try to convert
            converted = self._convert_units(recipe_quantity["quantity"], recipe_unit, pantry_unit)

            if converted is not None:
                has_enough = pantry_quantity["quantity"] >= converted
                percentage = (pantry_quantity["quantity"] / converted) * 100
            else:
                # Can't compare - assume we have enough
                has_enough = True
                percentage = 100

        return {
            "has_enough": has_enough,
            "percentage_available": min(percentage, 100),
            "pantry_quantity": pantry_quantity["quantity"],
            "pantry_unit": pantry_unit,
            "recipe_needs": recipe_quantity["quantity"],
            "recipe_unit": recipe_unit,
        }

    def _convert_units(self, quantity: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between units"""
        if from_unit == to_unit:
            return quantity

        # Check if we have direct conversion
        if from_unit in self.unit_conversions:
            if to_unit in self.unit_conversions[from_unit]:
                return quantity * self.unit_conversions[from_unit][to_unit]

        # Try reverse conversion
        if to_unit in self.unit_conversions:
            if from_unit in self.unit_conversions[to_unit]:
                return quantity / self.unit_conversions[to_unit][from_unit]

        return None
