#!/usr/bin/env python3
"""
Comprehensive backup recipe import pipeline for PrepSense.
Imports 13k+ recipes from CSV to PostgreSQL with robust error handling.
"""

import asyncio
import csv
import hashlib
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

# Add the backend_gateway directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from core.database import get_db_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("recipe_import.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class RecipeData:
    """Structured recipe data from CSV."""

    title: str
    ingredients: List[str]
    instructions: str
    image_name: Optional[str]
    cleaned_ingredients: List[str]
    recipe_hash: str


@dataclass
class ImportStats:
    """Import statistics tracking."""

    total_processed: int = 0
    successful_imports: int = 0
    skipped_duplicates: int = 0
    failed_imports: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class RecipeImporter:
    """Handles the import of backup recipes from CSV to PostgreSQL."""

    def __init__(self, csv_file_path: str, batch_size: int = 100):
        self.csv_file_path = Path(csv_file_path)
        self.batch_size = batch_size
        self.stats = ImportStats()
        self.db_pool = None

        # Validation patterns
        self.ingredient_pattern = re.compile(r"'([^']+)'")
        self.cleanup_pattern = re.compile(r"[^\w\s-]")

    async def initialize(self):
        """Initialize database connection."""
        try:
            self.db_pool = await get_db_pool()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    def parse_ingredients(self, ingredients_str: str) -> List[str]:
        """Parse ingredients string into list."""
        if not ingredients_str or ingredients_str.strip() == "":
            return []

        try:
            # Handle list-like string format
            if ingredients_str.startswith("[") and ingredients_str.endswith("]"):
                # Extract quoted ingredients
                matches = self.ingredient_pattern.findall(ingredients_str)
                return [self.clean_ingredient(ing) for ing in matches if ing.strip()]
            else:
                # Split by common delimiters
                ingredients = re.split(r"[,;\\n]", ingredients_str)
                return [self.clean_ingredient(ing) for ing in ingredients if ing.strip()]
        except Exception as e:
            logger.warning(f"Failed to parse ingredients: {ingredients_str[:100]}... Error: {e}")
            return []

    def clean_ingredient(self, ingredient: str) -> str:
        """Clean and normalize ingredient name."""
        if not ingredient:
            return ""

        # Remove extra whitespace and special characters
        cleaned = re.sub(r"\\s+", " ", ingredient.strip())
        # Remove measurement patterns like "1 cup", "2 tbsp"
        cleaned = re.sub(r"^\\d+\\s*\\w*\\s+", "", cleaned)
        # Remove parenthetical notes
        cleaned = re.sub(r"\\([^)]*\\)", "", cleaned)
        # Clean up remaining artifacts
        cleaned = cleaned.strip(" ,-")

        return cleaned[:255]  # Ensure it fits in database field

    def extract_recipe_metadata(self, title: str, instructions: str) -> Dict[str, Any]:
        """Extract metadata from recipe title and instructions."""
        metadata = {
            "cuisine_type": None,
            "prep_time": None,
            "cook_time": None,
            "servings": None,
            "difficulty": "medium",
        }

        # Extract cuisine from title
        cuisine_patterns = {
            "italian": r"\\b(italian|pasta|pizza|risotto)\\b",
            "asian": r"\\b(asian|chinese|japanese|thai|korean|vietnamese)\\b",
            "mexican": r"\\b(mexican|taco|burrito|salsa)\\b",
            "french": r"\\b(french|croissant|baguette)\\b",
            "indian": r"\\b(indian|curry|naan|tikka)\\b",
            "american": r"\\b(american|bbq|burger)\\b",
        }

        title_lower = title.lower()
        for cuisine, pattern in cuisine_patterns.items():
            if re.search(pattern, title_lower):
                metadata["cuisine_type"] = cuisine
                break

        # Extract timing information from instructions
        if instructions:
            # Look for time patterns
            time_matches = re.findall(
                r"(\\d+)\\s*(minutes?|mins?|hours?|hrs?)", instructions.lower()
            )
            times = []
            for match in time_matches:
                value, unit = match
                if "hour" in unit or "hr" in unit:
                    times.append(int(value) * 60)
                else:
                    times.append(int(value))

            if times:
                total_time = sum(times)
                metadata["cook_time"] = total_time
                if total_time > 60:
                    metadata["prep_time"] = min(30, total_time // 3)

        # Estimate difficulty based on ingredient count and instructions length
        ingredient_count = len(title.split(",")) if "," in title else 2
        instruction_length = len(instructions) if instructions else 100

        if ingredient_count <= 5 and instruction_length < 500:
            metadata["difficulty"] = "easy"
        elif ingredient_count > 10 or instruction_length > 1500:
            metadata["difficulty"] = "hard"

        return metadata

    def generate_recipe_hash(self, title: str, ingredients: List[str]) -> str:
        """Generate hash for duplicate detection."""
        content = f"{title.lower()}{''.join(sorted([ing.lower() for ing in ingredients]))}"
        return hashlib.md5(content.encode()).hexdigest()

    def parse_csv_row(self, row: Dict[str, str]) -> Optional[RecipeData]:
        """Parse a single CSV row into RecipeData."""
        try:
            title = row.get("Title", "").strip()
            if not title:
                return None

            ingredients_raw = row.get("Ingredients", "")
            cleaned_ingredients_raw = row.get("Cleaned_Ingredients", "")
            instructions = row.get("Instructions", "").strip()
            image_name = row.get("Image_Name", "").strip() or None

            # Parse ingredients
            ingredients = self.parse_ingredients(ingredients_raw)
            cleaned_ingredients = self.parse_ingredients(cleaned_ingredients_raw)

            # Use cleaned ingredients if available, otherwise use regular ingredients
            final_ingredients = cleaned_ingredients if cleaned_ingredients else ingredients

            if not final_ingredients:
                logger.warning(f"No ingredients found for recipe: {title}")
                return None

            # Generate hash for duplicate detection
            recipe_hash = self.generate_recipe_hash(title, final_ingredients)

            return RecipeData(
                title=title[:255],  # Ensure it fits in database
                ingredients=final_ingredients,
                instructions=instructions,
                image_name=image_name,
                cleaned_ingredients=cleaned_ingredients,
                recipe_hash=recipe_hash,
            )

        except Exception as e:
            logger.error(f"Failed to parse CSV row: {row}. Error: {e}")
            return None

    async def check_recipe_exists(self, recipe_hash: str) -> bool:
        """Check if recipe already exists in database."""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT 1 FROM recipes WHERE backup_recipe_id = $1 OR "
                "md5(LOWER(recipe_name) || array_to_string(ARRAY(SELECT LOWER(ingredient_name) FROM recipe_ingredients WHERE recipe_id = recipes.recipe_id ORDER BY ingredient_name), '')) = $1",
                recipe_hash,
            )
            return result is not None

    async def insert_recipe_batch(self, recipes: List[RecipeData]) -> Tuple[int, int]:
        """Insert a batch of recipes into the database."""
        successful = 0
        skipped = 0

        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for recipe in recipes:
                    try:
                        # Check for duplicates
                        if await self.check_recipe_exists(recipe.recipe_hash):
                            skipped += 1
                            continue

                        # Extract metadata
                        metadata = self.extract_recipe_metadata(recipe.title, recipe.instructions)

                        # Insert recipe
                        recipe_id = await conn.fetchval(
                            """
                            INSERT INTO recipes (
                                recipe_name, cuisine_type, prep_time, cook_time, 
                                servings, difficulty, instructions, source, 
                                image_path, backup_recipe_id, recipe_data
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            RETURNING recipe_id
                        """,
                            recipe.title,
                            metadata["cuisine_type"],
                            metadata["prep_time"],
                            metadata["cook_time"],
                            metadata.get("servings", 4),
                            metadata["difficulty"],
                            recipe.instructions,
                            "local",  # source
                            recipe.image_name,
                            int(recipe.recipe_hash, 16)
                            % 2147483647,  # Convert hash to int for backup_recipe_id
                            json.dumps(
                                {
                                    "original_ingredients": recipe.ingredients,
                                    "cleaned_ingredients": recipe.cleaned_ingredients,
                                    "import_source": "csv_backup",
                                    "import_timestamp": datetime.now().isoformat(),
                                }
                            ),
                        )

                        # Insert ingredients
                        for ingredient in recipe.ingredients:
                            if ingredient:  # Skip empty ingredients
                                await conn.execute(
                                    """
                                    INSERT INTO recipe_ingredients (recipe_id, ingredient_name, is_optional)
                                    VALUES ($1, $2, $3)
                                    ON CONFLICT (recipe_id, ingredient_name) DO NOTHING
                                """,
                                    recipe_id,
                                    ingredient,
                                    False,
                                )

                        successful += 1

                    except Exception as e:
                        logger.error(f"Failed to insert recipe '{recipe.title}': {e}")
                        self.stats.errors.append(f"Recipe '{recipe.title}': {str(e)}")

        return successful, skipped

    async def import_recipes(self) -> ImportStats:
        """Main import process."""
        logger.info(f"Starting import from {self.csv_file_path}")

        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")

        await self.initialize()

        batch = []
        row_count = 0

        try:
            with open(self.csv_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    row_count += 1
                    self.stats.total_processed += 1

                    # Parse row
                    recipe_data = self.parse_csv_row(row)
                    if recipe_data:
                        batch.append(recipe_data)

                    # Process batch when full
                    if len(batch) >= self.batch_size:
                        successful, skipped = await self.insert_recipe_batch(batch)
                        self.stats.successful_imports += successful
                        self.stats.skipped_duplicates += skipped
                        self.stats.failed_imports += len(batch) - successful - skipped

                        logger.info(
                            f"Processed {row_count} rows. "
                            f"Success: {self.stats.successful_imports}, "
                            f"Skipped: {self.stats.skipped_duplicates}, "
                            f"Failed: {self.stats.failed_imports}"
                        )

                        batch = []

                # Process remaining batch
                if batch:
                    successful, skipped = await self.insert_recipe_batch(batch)
                    self.stats.successful_imports += successful
                    self.stats.skipped_duplicates += skipped
                    self.stats.failed_imports += len(batch) - successful - skipped

            # Refresh materialized view
            logger.info("Refreshing recipe search view...")
            async with self.db_pool.acquire() as conn:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY recipe_search_view")

            logger.info("Import completed successfully")

        except Exception as e:
            logger.error(f"Import failed: {e}")
            self.stats.errors.append(f"Import failure: {str(e)}")
            raise

        return self.stats

    def print_summary(self):
        """Print import summary."""
        print("\\n" + "=" * 50)
        print("RECIPE IMPORT SUMMARY")
        print("=" * 50)
        print(f"Total processed: {self.stats.total_processed}")
        print(f"Successfully imported: {self.stats.successful_imports}")
        print(f"Skipped duplicates: {self.stats.skipped_duplicates}")
        print(f"Failed imports: {self.stats.failed_imports}")
        print(
            f"Success rate: {(self.stats.successful_imports/self.stats.total_processed*100):.1f}%"
        )

        if self.stats.errors:
            print(f"\\nErrors ({len(self.stats.errors)}):")
            for error in self.stats.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats.errors) > 10:
                print(f"  ... and {len(self.stats.errors) - 10} more errors")

        print("=" * 50)


async def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Import backup recipes from CSV")
    parser.add_argument(
        "--csv-file",
        default="/Users/danielkim/_Capstone/PrepSense/Food Data/recipe-dataset-main/13k-recipes.csv",
        help="Path to CSV file",
    )
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for imports")
    parser.add_argument("--dry-run", action="store_true", help="Parse CSV without importing")

    args = parser.parse_args()

    importer = RecipeImporter(args.csv_file, args.batch_size)

    try:
        if args.dry_run:
            logger.info("DRY RUN MODE - No data will be imported")
            # TODO: Implement dry run validation
            return

        stats = await importer.import_recipes()
        importer.print_summary()

        if stats.failed_imports > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
