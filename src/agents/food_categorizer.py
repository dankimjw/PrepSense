import logging
import os

import asyncpg
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


class FoodCategorizer:
    """FoodCategorizer agent for matching food items to USDA database"""

    def __init__(self):
        self.name = "food_categorizer"

    async def run(self, raw_items: list[dict]):
        """
        Input: [{'raw_line': '2 lb chicken breast'}...]
        Output: [{'canonical_name': 'chicken breast', 'category': 'Poultry', 'fdc_id': 123, 'raw_line': '2 lb chicken breast'}...]
        """
        if not raw_items:
            return []

        # Connect to database
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found in environment")
            return []

        try:
            conn = await asyncpg.connect(db_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return []

        try:
            # Quick cache of USDA foods with error handling
            try:
                rows = await conn.fetch(
                    "SELECT description, category, fdc_id FROM usda_foods LIMIT 10000"
                )
                if not rows:
                    logger.warning("No USDA foods found in database")
                    return []
            except Exception as e:
                logger.error(f"Failed to fetch USDA foods: {e}")
                return []

            corpus = [r["description"].lower() for r in rows]
            corpus_dict = {r["description"].lower(): r for r in rows}

            out = []
            for itm in raw_items:
                if "raw_line" not in itm:
                    logger.warning(f"Item missing 'raw_line' field: {itm}")
                    continue

                txt = itm["raw_line"].lower().strip()
                if not txt:
                    continue

                try:
                    match_result = process.extractOne(txt, corpus, scorer=fuzz.WRatio)
                    if not match_result or match_result[1] < 80:
                        logger.debug(f"No good match found for: {txt}")
                        continue

                    match, score = match_result
                    row = corpus_dict[match]

                    out.append(
                        {
                            "canonical_name": row["description"],
                            "category": row["category"],
                            "fdc_id": row["fdc_id"],
                            "match_score": score,
                            **itm,
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing item {txt}: {e}")
                    continue

            logger.info(f"Categorized {len(out)} out of {len(raw_items)} items")
            return out
        finally:
            await conn.close()
