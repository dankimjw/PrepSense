"""Food lookup tool for USDA database integration and nutrition data."""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import requests

from backend_gateway.models.nutrition import FoodItem, NutrientProfile

logger = logging.getLogger(__name__)


@dataclass
class USDAFoodItem:
    """USDA food item data structure."""

    fdc_id: str
    description: str
    brand_name: Optional[str] = None
    food_category: Optional[str] = None
    nutrients: Optional[dict[str, float]] = None
    serving_size: Optional[float] = None
    serving_unit: Optional[str] = None


class FoodLookupTool:
    """Tool for looking up food nutrition data from USDA database."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the food lookup tool."""
        self.api_key = api_key or "DEMO_KEY"  # USDA provides demo key with rate limits
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.session = requests.Session()

        # Common nutrient IDs in USDA database
        self.nutrient_mapping = {
            "1008": "calories",  # Energy
            "1003": "protein",  # Protein
            "1004": "total_fat",  # Total lipid (fat)
            "1005": "carbohydrates",  # Carbohydrate, by difference
            "1079": "fiber",  # Fiber, total dietary
            "1258": "saturated_fat",  # Fatty acids, total saturated
            "1235": "sugar",  # Sugars, total including NLEA
            "1093": "sodium",  # Sodium
            "1087": "calcium",  # Calcium
            "1089": "iron",  # Iron
            "1162": "vitamin_c",  # Vitamin C
            "1106": "vitamin_a",  # Vitamin A, RAE
            "1114": "vitamin_d",  # Vitamin D
            "1109": "vitamin_e",  # Vitamin E
            "1185": "potassium",  # Potassium
            "1090": "magnesium",  # Magnesium
            "1091": "phosphorus",  # Phosphorus
            "1095": "zinc",  # Zinc
            "1098": "copper",  # Copper
            "1176": "folate",  # Folate, total
            "1165": "thiamin",  # Thiamin
            "1166": "riboflavin",  # Riboflavin
            "1167": "niacin",  # Niacin
            "1175": "vitamin_b6",  # Vitamin B-6
            "1178": "vitamin_b12",  # Vitamin B-12
            "1253": "cholesterol",  # Cholesterol
        }

    @lru_cache(maxsize=1000)
    def search_foods(self, query: str, page_size: int = 10) -> list[USDAFoodItem]:
        """Search for foods in USDA database."""
        try:
            logger.info(f"Searching USDA database for: {query}")

            url = f"{self.base_url}/foods/search"
            params = {
                "api_key": self.api_key,
                "query": query,
                "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],
                "pageSize": page_size,
                "pageNumber": 1,
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            foods = []

            for food_data in data.get("foods", []):
                food_item = USDAFoodItem(
                    fdc_id=str(food_data.get("fdcId", "")),
                    description=food_data.get("description", ""),
                    brand_name=food_data.get("brandName"),
                    food_category=food_data.get("foodCategory"),
                )
                foods.append(food_item)

            logger.info(f"Found {len(foods)} foods for query: {query}")
            return foods

        except Exception as e:
            logger.error(f"Error searching USDA database: {e}")
            return []

    @lru_cache(maxsize=500)
    def get_food_details(self, fdc_id: str) -> Optional[USDAFoodItem]:
        """Get detailed nutrition information for a specific food."""
        try:
            logger.info(f"Getting food details for FDC ID: {fdc_id}")

            url = f"{self.base_url}/food/{fdc_id}"
            params = {"api_key": self.api_key, "nutrients": list(self.nutrient_mapping.keys())}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract nutrients
            nutrients = {}
            for nutrient in data.get("foodNutrients", []):
                nutrient_id = str(nutrient.get("nutrient", {}).get("id", ""))
                if nutrient_id in self.nutrient_mapping:
                    nutrient_name = self.nutrient_mapping[nutrient_id]
                    amount = nutrient.get("amount", 0)
                    nutrients[nutrient_name] = amount

            # Extract serving size information
            serving_size = 100.0  # Default to 100g
            serving_unit = "g"

            # Look for serving size in food portions
            for portion in data.get("foodPortions", []):
                if portion.get("modifier") and "serving" in portion.get("modifier", "").lower():
                    serving_size = portion.get("gramWeight", 100.0)
                    break

            food_item = USDAFoodItem(
                fdc_id=fdc_id,
                description=data.get("description", ""),
                brand_name=data.get("brandName"),
                food_category=data.get("foodCategory"),
                nutrients=nutrients,
                serving_size=serving_size,
                serving_unit=serving_unit,
            )

            logger.info(f"Retrieved details for: {food_item.description}")
            return food_item

        except Exception as e:
            logger.error(f"Error getting food details: {e}")
            return None

    def lookup_food_nutrition(self, food_name: str, quantity: float = 1.0) -> Optional[FoodItem]:
        """Look up nutrition information for a food item."""
        try:
            # Search for the food
            search_results = self.search_foods(food_name)

            if not search_results:
                logger.warning(f"No results found for: {food_name}")
                return None

            # Get details for the first result
            best_match = search_results[0]
            food_details = self.get_food_details(best_match.fdc_id)

            if not food_details or not food_details.nutrients:
                logger.warning(f"No nutrition data found for: {food_name}")
                return None

            # Convert to our NutrientProfile
            nutrient_profile = NutrientProfile(
                calories=food_details.nutrients.get("calories", 0),
                protein=food_details.nutrients.get("protein", 0),
                carbohydrates=food_details.nutrients.get("carbohydrates", 0),
                fiber=food_details.nutrients.get("fiber", 0),
                total_fat=food_details.nutrients.get("total_fat", 0),
                saturated_fat=food_details.nutrients.get("saturated_fat", 0),
                sugar=food_details.nutrients.get("sugar", 0),
                sodium=food_details.nutrients.get("sodium", 0),
                calcium=food_details.nutrients.get("calcium", 0),
                iron=food_details.nutrients.get("iron", 0),
                vitamin_c=food_details.nutrients.get("vitamin_c", 0),
                vitamin_a=food_details.nutrients.get("vitamin_a", 0),
                vitamin_d=food_details.nutrients.get("vitamin_d", 0),
                vitamin_e=food_details.nutrients.get("vitamin_e", 0),
                potassium=food_details.nutrients.get("potassium", 0),
                magnesium=food_details.nutrients.get("magnesium", 0),
                phosphorus=food_details.nutrients.get("phosphorus", 0),
                zinc=food_details.nutrients.get("zinc", 0),
                copper=food_details.nutrients.get("copper", 0),
                folate=food_details.nutrients.get("folate", 0),
                thiamin=food_details.nutrients.get("thiamin", 0),
                riboflavin=food_details.nutrients.get("riboflavin", 0),
                niacin=food_details.nutrients.get("niacin", 0),
                vitamin_b6=food_details.nutrients.get("vitamin_b6", 0),
                vitamin_b12=food_details.nutrients.get("vitamin_b12", 0),
                cholesterol=food_details.nutrients.get("cholesterol", 0),
            )

            # Adjust for quantity
            if quantity != 1.0:
                nutrient_profile = nutrient_profile * quantity

            # Create FoodItem
            food_item = FoodItem(
                name=food_details.description,
                usda_id=food_details.fdc_id,
                brand=food_details.brand_name,
                serving_size=food_details.serving_size or 100.0,
                serving_unit=food_details.serving_unit or "g",
                nutrients=nutrient_profile,
            )

            logger.info(f"Successfully looked up nutrition for: {food_name}")
            return food_item

        except Exception as e:
            logger.error(f"Error looking up food nutrition: {e}")
            return None

    def batch_lookup_foods(self, food_names: list[str]) -> dict[str, Optional[FoodItem]]:
        """Look up nutrition information for multiple foods."""
        results = {}

        for food_name in food_names:
            try:
                food_item = self.lookup_food_nutrition(food_name)
                results[food_name] = food_item
            except Exception as e:
                logger.error(f"Error looking up {food_name}: {e}")
                results[food_name] = None

        return results

    def get_food_suggestions(self, partial_name: str, max_suggestions: int = 5) -> list[str]:
        """Get food name suggestions based on partial input."""
        try:
            search_results = self.search_foods(partial_name, page_size=max_suggestions)

            suggestions = []
            for food in search_results:
                # Clean up the description for better suggestions
                description = food.description.lower()
                if food.brand_name:
                    description = f"{food.brand_name} {description}"
                suggestions.append(description.title())

            return suggestions

        except Exception as e:
            logger.error(f"Error getting food suggestions: {e}")
            return []

    def estimate_nutrition_from_ingredients(self, ingredients: list[str]) -> NutrientProfile:
        """Estimate nutrition for a list of ingredients."""
        total_nutrition = NutrientProfile()

        for ingredient in ingredients:
            try:
                # Parse ingredient to extract quantity and name
                food_name, quantity = self._parse_ingredient(ingredient)

                # Look up nutrition
                food_item = self.lookup_food_nutrition(food_name, quantity)

                if food_item:
                    # Add nutrients per serving
                    serving_nutrients = food_item.get_nutrients_per_serving()
                    total_nutrition = total_nutrition + serving_nutrients

            except Exception as e:
                logger.warning(
                    f"Could not estimate nutrition for ingredient: {ingredient}, error: {e}"
                )
                continue

        return total_nutrition

    def _parse_ingredient(self, ingredient: str) -> tuple[str, float]:
        """Parse ingredient string to extract food name and quantity."""
        import re

        # Simple parsing - look for numbers at the beginning
        match = re.match(
            r"^(\d+(?:\.\d+)?)\s*(?:cups?|tbsp|tsp|oz|lbs?|g|kg|ml|l)?\s*(.+)", ingredient.strip()
        )

        if match:
            quantity = float(match.group(1))
            food_name = match.group(2).strip()
        else:
            quantity = 1.0
            food_name = ingredient.strip()

        # Clean up common cooking terms
        food_name = re.sub(
            r"\b(chopped|diced|sliced|minced|fresh|frozen|dried|cooked)\b", "", food_name
        )
        food_name = " ".join(food_name.split())  # Remove extra whitespace

        return food_name, quantity


# Create a singleton instance
food_lookup_tool = FoodLookupTool()
