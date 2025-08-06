import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


class FreshFilter:
    name = "fresh_filter"

    async def run(
        self, canonicalized_items: list[dict], user_id: str = None, freshness_days: int = 7
    ):
        """
        Input: [{'canonical_name': 'chicken breast', 'category': 'Poultry', 'fdc_id': 123, 'raw_line': '2 lb chicken breast',
                'qty_canon': Decimal('0.907'), 'canon_unit': 'kilogram'}...]
        Output: Same items but filtered for freshness and enriched with expiration info
        """
        if not canonicalized_items:
            return []

        # If ENABLE_FRESH_FILTER_AGENT is False, pass through all items
        enable_filter = os.getenv("ENABLE_FRESH_FILTER_AGENT", "true").lower() == "true"
        if not enable_filter:
            logger.info("Fresh filter disabled by environment variable")
            return canonicalized_items

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return canonicalized_items

        try:
            conn = await asyncpg.connect(db_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return canonicalized_items

        try:
            # Get food loss rates and expiration estimates
            food_loss_data = await self._get_food_loss_data(conn)

            out = []
            cutoff_date = datetime.now() + timedelta(days=freshness_days)

            for item in canonicalized_items:
                try:
                    # Estimate expiration date based on category and food loss data
                    category = item.get("category", "").lower()
                    estimated_expiry = self._estimate_expiration_date(category, food_loss_data)

                    # Calculate freshness score (0-1, where 1 is very fresh, 0 is expired)
                    freshness_score = self._calculate_freshness_score(estimated_expiry)

                    # Determine if item is fresh enough
                    is_fresh = estimated_expiry is None or estimated_expiry > cutoff_date

                    # Add freshness metadata
                    enriched_item = {
                        **item,
                        "estimated_expiry": (
                            estimated_expiry.isoformat() if estimated_expiry else None
                        ),
                        "freshness_score": freshness_score,
                        "is_fresh": is_fresh,
                        "days_until_expiry": (
                            (estimated_expiry - datetime.now()).days if estimated_expiry else None
                        ),
                    }

                    # Only include if fresh or if we can't determine freshness
                    if is_fresh:
                        out.append(enriched_item)
                    else:
                        logger.debug(f"Filtered out expired item: {item.get('canonical_name')}")

                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")
                    # If error, include item without freshness data
                    out.append({**item, "freshness_error": str(e)})

            logger.info(f"Fresh filter: kept {len(out)} out of {len(canonicalized_items)} items")
            return out

        finally:
            await conn.close()

    async def _get_food_loss_data(self, conn) -> dict:
        """Get food loss rates from database"""
        try:
            rows = await conn.fetch(
                """
                SELECT category, avg_shelf_life_days, loss_rate_percent 
                FROM food_loss_rates
            """
            )
            return {row["category"].lower(): row for row in rows} if rows else {}
        except Exception as e:
            logger.warning(f"Could not fetch food loss data: {e}")
            return {}

    def _estimate_expiration_date(self, category: str, food_loss_data: dict) -> Optional[datetime]:
        """Estimate expiration date based on category"""
        # Default shelf life by category (in days)
        default_shelf_life = {
            "dairy and egg products": 7,
            "meat products": 3,
            "poultry products": 3,
            "beef products": 3,
            "pork products": 3,
            "lamb, veal, and game products": 3,
            "finfish and shellfish products": 2,
            "vegetables and vegetable products": 5,
            "fruits and fruit juices": 7,
            "bakery products": 3,
            "beverages": 30,
            "fats and oils": 365,
            "nut and seed products": 180,
            "legumes and legume products": 365,
            "grains and cereals": 365,
            "soups, sauces, and gravies": 14,
            "spices and herbs": 730,
        }

        # Use database data if available, otherwise use defaults
        if category in food_loss_data:
            shelf_life_days = food_loss_data[category]["avg_shelf_life_days"]
        else:
            shelf_life_days = default_shelf_life.get(category, 7)  # Default to 7 days

        if shelf_life_days is None:
            return None

        return datetime.now() + timedelta(days=shelf_life_days)

    def _calculate_freshness_score(self, estimated_expiry: Optional[datetime]) -> float:
        """Calculate freshness score from 0 (expired) to 1 (very fresh)"""
        if estimated_expiry is None:
            return 0.5  # Unknown freshness

        now = datetime.now()
        if estimated_expiry <= now:
            return 0.0  # Expired

        # Calculate days until expiry
        days_until_expiry = (estimated_expiry - now).days

        # Score based on days remaining (assuming 14 days is "very fresh")
        if days_until_expiry >= 14:
            return 1.0
        elif days_until_expiry >= 7:
            return 0.8
        elif days_until_expiry >= 3:
            return 0.6
        elif days_until_expiry >= 1:
            return 0.4
        else:
            return 0.2
