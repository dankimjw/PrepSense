"""
Enhanced food database service that integrates multiple external sources
for better food categorization and unit validation
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from backend_gateway.services.spoonacular_service import SpoonacularService

logger = logging.getLogger(__name__)


@dataclass
class FoodCategorization:
    item_name: str
    category: str
    allowed_units: list[str]
    default_unit: str
    confidence: float
    source: str
    metadata: dict[str, Any] = None


class FoodDatabaseService:
    """
    Service that integrates multiple food databases to provide
    accurate categorization and unit validation
    """

    def __init__(self, db_service=None):
        self.db_service = db_service
        self.spoonacular = SpoonacularService()
        self.cache = {}  # In-memory cache
        self.cache_expiry = timedelta(hours=24)

        # API credentials
        self.usda_api_key = self._get_usda_key()
        self.client = httpx.AsyncClient(timeout=10.0)

        # Enhanced categorization patterns
        self.category_patterns = {
            "produce_countable": [
                r"\b(apple|banana|orange|lemon|lime|avocado|tomato|potato|onion|carrot|bell pepper|cucumber|zucchini)\b",
                r"\b(egg|eggs)\b",
            ],
            "produce_measurable": [
                r"\b(lettuce|spinach|kale|broccoli|cauliflower|cabbage|herbs|cilantro|parsley|basil)\b",
                r"\b(berries|grapes|cherries)\b",
            ],
            "liquids": [
                r"\b(milk|water|juice|oil|vinegar|broth|stock|wine|beer|soda|coffee|tea)\b",
                r"\b(syrup|honey|sauce|dressing)\b",
            ],
            "dry_goods": [
                r"\b(flour|sugar|salt|pepper|rice|pasta|quinoa|oats|cereal)\b",
                r"\b(spice|seasoning|powder|extract)\b",
            ],
            "meat_seafood": [
                r"\b(chicken|beef|pork|turkey|fish|salmon|tuna|shrimp|lamb)\b",
                r"\b(breast|thigh|ground|fillet)\b",
            ],
            "bakery": [
                r"\b(bread|loaf|roll|bun|bagel|croissant|muffin|cake|pie|pastry|donut|cookie)\b",
                r"\b(toast|baguette|focaccia|sourdough|wheat|rye|white bread)\b",
            ],
            "dairy": [r"\b(cheese|yogurt|butter|cream|sour cream|cottage cheese)\b"],
            "snacks_bars": [
                r"\b(bar|bars)\b.*\b(cereal|granola|protein|energy|snack)\b",
                r"\b(cereal|granola|protein|energy|snack)\b.*\b(bar|bars)\b",
                r"\btrader joe\'?s.*bar\b",
                r"\bkind.*bar\b",
                r"\bclif.*bar\b",
            ],
            "packaged_snacks": [
                r"\b(chips|crackers|cookies|pretzels|popcorn)\b",
                r"\b(nuts|trail mix|dried fruit)\b",
            ],
        }

        # Unit mappings per category
        self.category_unit_mappings = {
            "produce_countable": {
                "allowed": ["each", "piece", "whole", "bag", "package", "g", "oz", "lb", "kg"],
                "default": "each",
                "forbidden": ["ml", "l", "fl oz", "cup", "tbsp", "tsp", "gallon", "pint", "quart"],
            },
            "produce_measurable": {
                "allowed": ["g", "oz", "lb", "kg", "cup", "bunch", "head", "bag", "package"],
                "default": "oz",
                "forbidden": ["ml", "l", "fl oz", "tbsp", "tsp", "gallon", "pint", "quart"],
            },
            "liquids": {
                "allowed": [
                    "ml",
                    "l",
                    "fl oz",
                    "cup",
                    "tbsp",
                    "tsp",
                    "gallon",
                    "pint",
                    "quart",
                    "bottle",
                    "can",
                ],
                "default": "fl oz",
                "forbidden": ["each", "piece", "whole"],
            },
            "dry_goods": {
                "allowed": ["g", "oz", "lb", "kg", "cup", "tbsp", "tsp", "bag", "package", "box"],
                "default": "oz",
                "forbidden": ["ml", "l", "fl oz", "gallon", "pint", "quart"],
            },
            "meat_seafood": {
                "allowed": ["g", "oz", "lb", "kg", "piece", "fillet", "package"],
                "default": "lb",
                "forbidden": ["ml", "l", "fl oz", "cup", "tbsp", "tsp", "gallon"],
            },
            "dairy": {
                "allowed": [
                    "g",
                    "oz",
                    "lb",
                    "kg",
                    "ml",
                    "l",
                    "fl oz",
                    "cup",
                    "container",
                    "package",
                ],
                "default": "oz",
                "forbidden": ["each", "piece", "whole"],
            },
            "bakery": {
                "allowed": ["each", "loaf", "slice", "piece", "package", "bag", "g", "oz", "lb"],
                "default": "each",
                "forbidden": ["ml", "l", "fl oz", "cup", "tbsp", "tsp", "gallon", "pint", "quart"],
            },
            "snacks_bars": {
                "allowed": ["each", "piece", "bar", "package", "box", "g", "oz"],
                "default": "each",
                "forbidden": ["ml", "l", "fl oz", "cup", "tbsp", "tsp", "gallon", "pint", "quart"],
            },
            "packaged_snacks": {
                "allowed": ["g", "oz", "bag", "package", "box", "container"],
                "default": "oz",
                "forbidden": ["ml", "l", "fl oz", "cup", "tbsp", "tsp", "gallon"],
            },
            "other": {
                "allowed": ["g", "oz", "lb", "kg", "ml", "l", "cup", "each", "piece", "package"],
                "default": "each",
                "forbidden": [],
            },
        }

    def _get_usda_key(self) -> Optional[str]:
        """Get USDA API key from file or environment"""
        try:
            if os.path.exists("config/usda_key.txt"):
                with open("config/usda_key.txt") as f:
                    return f.read().strip()
            return os.environ.get("USDA_API_KEY")
        except Exception:
            return None

    async def categorize_food_item(
        self, item_name: str, use_cache: bool = True
    ) -> FoodCategorization:
        """
        Categorize a food item using multiple sources with fallback
        """
        item_name_lower = item_name.lower().strip()

        # Check cache first
        if use_cache and item_name_lower in self.cache:
            cached_result = self.cache[item_name_lower]
            if datetime.now() - cached_result["timestamp"] < self.cache_expiry:
                return cached_result["categorization"]

        # Check database cache
        if self.db_service and use_cache:
            db_result = await self._get_from_db_cache(item_name_lower)
            if db_result:
                return db_result

        # Try external sources in order of preference
        categorization = None

        # 1. Try Spoonacular (best for ingredients)
        try:
            categorization = await self._categorize_with_spoonacular(item_name)
            if categorization and categorization.confidence > 0.7:
                await self._cache_result(item_name_lower, categorization)
                return categorization
        except Exception as e:
            logger.warning(f"Spoonacular categorization failed: {e}")

        # 2. Try USDA FoodData Central (authoritative for US foods)
        if self.usda_api_key:
            try:
                categorization = await self._categorize_with_usda(item_name)
                if categorization and categorization.confidence > 0.6:
                    await self._cache_result(item_name_lower, categorization)
                    return categorization
            except Exception as e:
                logger.warning(f"USDA categorization failed: {e}")

        # 3. Try OpenFoodFacts (good for packaged foods)
        try:
            categorization = await self._categorize_with_openfoodfacts(item_name)
            if categorization and categorization.confidence > 0.5:
                await self._cache_result(item_name_lower, categorization)
                return categorization
        except Exception as e:
            logger.warning(f"OpenFoodFacts categorization failed: {e}")

        # 4. Fallback to pattern matching
        categorization = self._categorize_with_patterns(item_name)
        await self._cache_result(item_name_lower, categorization)

        return categorization

    async def _categorize_with_spoonacular(self, item_name: str) -> Optional[FoodCategorization]:
        """Categorize using Spoonacular API"""
        try:
            # Use the parse ingredients endpoint
            parsed = await self.spoonacular.openai_service.parse_ingredients_from_text(item_name)
            if parsed and len(parsed) > 0:
                ingredient = parsed[0]

                # Map Spoonacular category to our categories
                spoon_category = ingredient.get("category", "").lower()
                our_category = self._map_spoonacular_category(spoon_category, item_name)

                return FoodCategorization(
                    item_name=item_name,
                    category=our_category,
                    allowed_units=self.category_unit_mappings[our_category]["allowed"],
                    default_unit=self.category_unit_mappings[our_category]["default"],
                    confidence=0.8,
                    source="spoonacular",
                    metadata={"original_category": spoon_category},
                )
        except Exception as e:
            logger.error(f"Spoonacular categorization error: {e}")
            return None

    async def _categorize_with_usda(self, item_name: str) -> Optional[FoodCategorization]:
        """Categorize using USDA FoodData Central API"""
        if not self.usda_api_key:
            return None

        try:
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {"api_key": self.usda_api_key, "query": item_name, "pageSize": 5}

            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                foods = data.get("foods", [])

                if foods:
                    # Use the first match
                    food = foods[0]
                    food_category = food.get("foodCategory", "").lower()
                    our_category = self._map_usda_category(food_category, item_name)

                    return FoodCategorization(
                        item_name=item_name,
                        category=our_category,
                        allowed_units=self.category_unit_mappings[our_category]["allowed"],
                        default_unit=self.category_unit_mappings[our_category]["default"],
                        confidence=0.7,
                        source="usda",
                        metadata={"usda_category": food_category, "usda_id": food.get("fdcId")},
                    )
        except Exception as e:
            logger.error(f"USDA categorization error: {e}")
            return None

    async def _categorize_with_openfoodfacts(self, item_name: str) -> Optional[FoodCategorization]:
        """Categorize using OpenFoodFacts API"""
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                "search_terms": item_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5,
            }

            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])

                if products:
                    # Use the first match
                    product = products[0]
                    categories = product.get("categories", "").lower()
                    our_category = self._map_openfoodfacts_category(categories, item_name)

                    return FoodCategorization(
                        item_name=item_name,
                        category=our_category,
                        allowed_units=self.category_unit_mappings[our_category]["allowed"],
                        default_unit=self.category_unit_mappings[our_category]["default"],
                        confidence=0.6,
                        source="openfoodfacts",
                        metadata={"off_categories": categories},
                    )
        except Exception as e:
            logger.error(f"OpenFoodFacts categorization error: {e}")
            return None

    def _categorize_with_patterns(self, item_name: str) -> FoodCategorization:
        """Fallback categorization using regex patterns"""
        item_lower = item_name.lower()

        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, item_lower):
                    return FoodCategorization(
                        item_name=item_name,
                        category=category,
                        allowed_units=self.category_unit_mappings[category]["allowed"],
                        default_unit=self.category_unit_mappings[category]["default"],
                        confidence=0.4,
                        source="patterns",
                        metadata={"matched_pattern": pattern},
                    )

        # Default to 'other' category
        return FoodCategorization(
            item_name=item_name,
            category="other",
            allowed_units=self.category_unit_mappings["other"]["allowed"],
            default_unit=self.category_unit_mappings["other"]["default"],
            confidence=0.2,
            source="default",
        )

    def _map_spoonacular_category(self, spoon_category: str, item_name: str) -> str:
        """Map Spoonacular category to our internal categories"""
        category_mapping = {
            "produce": (
                "produce_countable"
                if any(word in item_name.lower() for word in ["apple", "banana", "onion"])
                else "produce_measurable"
            ),
            "dairy": "dairy",
            "meat": "meat_seafood",
            "seafood": "meat_seafood",
            "beverage": "liquids",
            "condiment": "liquids",
            "baking": "dry_goods",
            "snack": "packaged_snacks",
        }
        return category_mapping.get(spoon_category, "other")

    def _map_usda_category(self, usda_category: str, item_name: str) -> str:
        """Map USDA category to our internal categories"""
        if "vegetable" in usda_category or "fruit" in usda_category:
            return (
                "produce_countable"
                if any(word in item_name.lower() for word in ["apple", "banana", "onion"])
                else "produce_measurable"
            )
        elif "dairy" in usda_category:
            return "dairy"
        elif "meat" in usda_category or "poultry" in usda_category or "fish" in usda_category:
            return "meat_seafood"
        elif "beverage" in usda_category:
            return "liquids"
        elif "grain" in usda_category or "cereal" in usda_category:
            return "dry_goods"
        elif "snack" in usda_category or "bar" in item_name.lower():
            return "snacks_bars" if "bar" in item_name.lower() else "packaged_snacks"
        return "other"

    def _map_openfoodfacts_category(self, off_categories: str, item_name: str) -> str:
        """Map OpenFoodFacts categories to our internal categories"""
        if "fruits" in off_categories or "vegetables" in off_categories:
            return (
                "produce_countable"
                if any(word in item_name.lower() for word in ["apple", "banana", "onion"])
                else "produce_measurable"
            )
        elif "dairy" in off_categories or "milk" in off_categories:
            return "dairy"
        elif "meat" in off_categories or "fish" in off_categories:
            return "meat_seafood"
        elif "beverage" in off_categories or "drink" in off_categories:
            return "liquids"
        elif "cereals" in off_categories or "pasta" in off_categories:
            return "dry_goods"
        elif "snack" in off_categories or "bar" in off_categories or "bar" in item_name.lower():
            return "snacks_bars" if "bar" in item_name.lower() else "packaged_snacks"
        return "other"

    async def validate_unit_for_item(self, item_name: str, unit: str) -> dict[str, Any]:
        """
        Validate if a unit is appropriate for a given item
        Returns validation result with suggestions
        """
        categorization = await self.categorize_food_item(item_name)

        unit_lower = unit.lower().strip()
        allowed_units = [u.lower() for u in categorization.allowed_units]
        forbidden_units = [
            u.lower()
            for u in self.category_unit_mappings.get(categorization.category, {}).get(
                "forbidden", []
            )
        ]

        is_valid = unit_lower in allowed_units
        is_forbidden = unit_lower in forbidden_units

        result = {
            "is_valid": is_valid and not is_forbidden,
            "item_name": item_name,
            "unit": unit,
            "category": categorization.category,
            "confidence": categorization.confidence,
            "source": categorization.source,
        }

        if not is_valid or is_forbidden:
            result["error"] = (
                f"Unit '{unit}' is not appropriate for {item_name} (category: {categorization.category})"
            )
            result["suggested_units"] = categorization.allowed_units[:5]  # Top 5 suggestions
            result["default_unit"] = categorization.default_unit

            # Special handling for common mistakes
            if "bar" in item_name.lower() and unit_lower in ["cup", "ml", "l", "fl oz"]:
                result["error"] = (
                    f"Bars cannot be measured in liquid units like '{unit}'. Try 'each' or 'package'."
                )

        return result

    async def _get_from_db_cache(self, item_name: str) -> Optional[FoodCategorization]:
        """Get categorization from database cache"""
        if not self.db_service:
            return None

        try:
            query = """
            SELECT category, allowed_units, default_unit, confidence, source, metadata, updated_at
            FROM food_categorization_cache
            WHERE LOWER(item_name) = LOWER(%s)
            AND updated_at > %s
            """
            cutoff_time = datetime.now() - self.cache_expiry
            result = self.db_service.fetch_one(query, (item_name, cutoff_time))

            if result:
                return FoodCategorization(
                    item_name=item_name,
                    category=result["category"],
                    allowed_units=json.loads(result["allowed_units"]),
                    default_unit=result["default_unit"],
                    confidence=float(result["confidence"]),
                    source=result["source"],
                    metadata=json.loads(result["metadata"]) if result["metadata"] else {},
                )
        except Exception as e:
            logger.error(f"Database cache lookup error: {e}")

        return None

    async def _cache_result(self, item_name: str, categorization: FoodCategorization):
        """Cache categorization result in memory and database"""
        # Memory cache
        self.cache[item_name] = {"categorization": categorization, "timestamp": datetime.now()}

        # Database cache
        if self.db_service:
            try:
                query = """
                INSERT INTO food_categorization_cache
                (item_name, category, allowed_units, default_unit, confidence, source, metadata, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                allowed_units = VALUES(allowed_units),
                default_unit = VALUES(default_unit),
                confidence = VALUES(confidence),
                source = VALUES(source),
                metadata = VALUES(metadata),
                updated_at = VALUES(updated_at)
                """

                self.db_service.execute_query(
                    query,
                    (
                        item_name,
                        categorization.category,
                        json.dumps(categorization.allowed_units),
                        categorization.default_unit,
                        categorization.confidence,
                        categorization.source,
                        json.dumps(categorization.metadata) if categorization.metadata else None,
                        datetime.now(),
                    ),
                )
            except Exception as e:
                logger.error(f"Database cache save error: {e}")

    async def record_user_correction(
        self, item_name: str, old_category: str, new_category: str, user_id: int
    ):
        """Record when a user corrects a categorization for learning"""
        if not self.db_service:
            return

        try:
            query = """
            INSERT INTO food_categorization_corrections
            (item_name, old_category, new_category, user_id, correction_date)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.db_service.execute_query(
                query, (item_name, old_category, new_category, user_id, datetime.now())
            )

            # Update cache with higher confidence
            if new_category in self.category_unit_mappings:
                improved_categorization = FoodCategorization(
                    item_name=item_name,
                    category=new_category,
                    allowed_units=self.category_unit_mappings[new_category]["allowed"],
                    default_unit=self.category_unit_mappings[new_category]["default"],
                    confidence=0.9,  # High confidence from user correction
                    source="user_correction",
                )
                await self._cache_result(item_name.lower(), improved_categorization)

        except Exception as e:
            logger.error(f"Error recording user correction: {e}")


# Global service instance
_food_db_service = None


def get_food_database_service(db_service=None) -> FoodDatabaseService:
    """Get singleton instance of FoodDatabaseService"""
    global _food_db_service
    if _food_db_service is None:
        _food_db_service = FoodDatabaseService(db_service)
    return _food_db_service
