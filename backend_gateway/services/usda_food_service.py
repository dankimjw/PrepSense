"""
USDA Food Database Service
Provides integration with USDA FoodData Central for nutritional information and food matching.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg

logger = logging.getLogger(__name__)


class USDAFoodService:
    """Service for interacting with USDA food data."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def search_foods(
        self, query: str = None, barcode: str = None, category_id: int = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search USDA foods by text query, barcode, or category.

        Args:
            query: Text search query
            barcode: UPC/GTIN barcode
            category_id: Food category ID
            limit: Maximum results to return

        Returns:
            List of matching foods with basic info
        """
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM search_usda_foods($1, $2, $3, $4)
                """,
                query,
                barcode,
                category_id,
                limit,
            )

            return [dict(row) for row in results]

    async def get_food_details(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific food.

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            Food details including nutrients and portions
        """
        async with self.db_pool.acquire() as conn:
            # Get basic food info
            food = await conn.fetchrow(
                """
                SELECT 
                    f.*,
                    fc.description as category_name
                FROM usda_foods f
                LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
                WHERE f.fdc_id = $1
                """,
                fdc_id,
            )

            if not food:
                return None

            food_dict = dict(food)

            # Get nutrients
            nutrients = await conn.fetch(
                """
                SELECT 
                    n.name,
                    n.unit_name,
                    fn.amount
                FROM usda_food_nutrients fn
                JOIN usda_nutrients n ON fn.nutrient_id = n.id
                WHERE fn.fdc_id = $1
                ORDER BY n.rank
                """,
                fdc_id,
            )

            food_dict["nutrients"] = [dict(n) for n in nutrients]

            # Get portions
            portions = await conn.fetch(
                """
                SELECT 
                    p.*,
                    mu.name as unit_name
                FROM usda_food_portions p
                LEFT JOIN usda_measure_units mu ON p.measure_unit_id = mu.id
                WHERE p.fdc_id = $1
                ORDER BY p.seq_num
                """,
                fdc_id,
            )

            food_dict["portions"] = [dict(p) for p in portions]

            return food_dict

    async def match_pantry_item(self, name: str, barcode: str = None) -> List[Dict[str, Any]]:
        """
        Find best USDA food matches for a pantry item.

        Args:
            name: Pantry item name
            barcode: Optional barcode

        Returns:
            List of potential matches with confidence scores
        """
        async with self.db_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM match_pantry_item_to_usda($1, $2)
                """,
                name,
                barcode,
            )

            matches = []
            for row in results:
                match_dict = dict(row)
                # Get additional food details
                food = await conn.fetchrow(
                    """
                    SELECT 
                        brand_owner,
                        brand_name,
                        food_category_id,
                        serving_size,
                        serving_size_unit
                    FROM usda_foods
                    WHERE fdc_id = $1
                    """,
                    row["fdc_id"],
                )
                if food:
                    match_dict.update(dict(food))
                matches.append(match_dict)

            return matches

    async def link_pantry_item(
        self, pantry_item_id: int, fdc_id: int, confidence_score: float, source: str = "manual"
    ) -> bool:
        """
        Create a link between a pantry item and USDA food.

        Args:
            pantry_item_id: PrepSense pantry item ID
            fdc_id: USDA FoodData Central ID
            confidence_score: Match confidence (0.0 to 1.0)
            source: How the match was made ('barcode', 'name_match', 'manual', 'ocr')

        Returns:
            Success status
        """
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO pantry_item_usda_mapping 
                    (pantry_item_id, fdc_id, confidence_score, mapping_source)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (pantry_item_id, fdc_id) DO UPDATE SET
                        confidence_score = EXCLUDED.confidence_score,
                        mapping_source = EXCLUDED.mapping_source
                    """,
                    pantry_item_id,
                    fdc_id,
                    confidence_score,
                    source,
                )
                return True
            except Exception as e:
                logger.error(f"Failed to link pantry item: {e}")
                return False

    async def get_pantry_item_nutrition(self, pantry_item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get nutritional information for a pantry item via USDA mapping.

        Args:
            pantry_item_id: PrepSense pantry item ID

        Returns:
            Nutritional information if available
        """
        async with self.db_pool.acquire() as conn:
            # Get best matching USDA food
            mapping = await conn.fetchrow(
                """
                SELECT 
                    m.fdc_id,
                    m.confidence_score,
                    f.description,
                    f.serving_size,
                    f.serving_size_unit
                FROM pantry_item_usda_mapping m
                JOIN usda_foods f ON m.fdc_id = f.fdc_id
                WHERE m.pantry_item_id = $1
                ORDER BY m.confidence_score DESC
                LIMIT 1
                """,
                pantry_item_id,
            )

            if not mapping:
                return None

            result = dict(mapping)

            # Get key nutrients
            nutrients = await conn.fetch(
                """
                SELECT 
                    n.name,
                    n.unit_name,
                    fn.amount
                FROM usda_food_nutrients fn
                JOIN usda_nutrients n ON fn.nutrient_id = n.id
                WHERE fn.fdc_id = $1
                AND n.id IN (1008, 1003, 1004, 1005, 1079, 1235, 1093)
                -- calories, protein, fat, carbs, fiber, sugar, sodium
                """,
                mapping["fdc_id"],
            )

            result["nutrients"] = [dict(n) for n in nutrients]

            return result

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all food categories."""
        async with self.db_pool.acquire() as conn:
            categories = await conn.fetch(
                """
                SELECT * FROM usda_food_categories
                ORDER BY description
                """
            )
            return [dict(c) for c in categories]

    async def get_units(self, unit_type: str = None) -> List[Dict[str, Any]]:
        """
        Get measure units, optionally filtered by type.

        Args:
            unit_type: Filter by 'volume', 'weight', 'count', 'portion', 'package'
        """
        async with self.db_pool.acquire() as conn:
            if unit_type:
                units = await conn.fetch(
                    """
                    SELECT * FROM usda_measure_units
                    WHERE unit_type = $1
                    ORDER BY name
                    """,
                    unit_type,
                )
            else:
                units = await conn.fetch(
                    """
                    SELECT * FROM usda_measure_units
                    ORDER BY unit_type, name
                    """
                )
            return [dict(u) for u in units]
