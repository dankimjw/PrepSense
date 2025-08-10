#!/usr/bin/env python3
"""
Robust CSV import pipeline for 13k+ backup recipes.
Includes data cleaning, ingredient parsing, and batch processing.

🟡 PARTIAL - Import pipeline implementation (requires manual execution)
"""

import asyncio
import csv
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import asyncpg

from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)

# File paths
CSV_FILE_PATH = "/Users/danielkim/_Capstone/PrepSense/Food Data/recipe-dataset-main/13k-recipes.csv"
IMAGES_DIR = "/Users/danielkim/_Capstone/PrepSense/Food Data/kaggle-recipes-with-images/Food Images/Food Images/"


@dataclass
class RecipeImportStats:
    """Track import statistics."""

    total_processed: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    duplicate_titles: int = 0
    missing_images: int = 0
    parsing_errors: int = 0
    start_time: float = 0

    def log_progress(self, batch_size: int = 100):
        """Log progress every batch_size records."""
        if self.total_processed % batch_size == 0:
            elapsed = time.time() - self.start_time
            rate = self.total_processed / elapsed if elapsed > 0 else 0
            logger.info(
                f"📊 Progress: {self.total_processed} processed, {self.successful_imports} imported, "
                f"{self.failed_imports} failed, Rate: {rate:.1f} records/sec"
            )


class IngredientParser:
    """Parse ingredient strings into structured components."""

    # Common unit patterns
    UNIT_PATTERNS = {
        "volume": r"\b(cup|cups|tsp|teaspoon|teaspoons|tbsp|tablespoon|tablespoons|fl\.?\s?oz|fluid\s+ounce|pint|pints|quart|quarts|gallon|gallons|ml|milliliter|liter|l)\b",
        "weight": r"\b(oz|ounce|ounces|lb|lbs|pound|pounds|g|gram|grams|kg|kilogram|kilograms)\b",
        "count": r"\b(piece|pieces|slice|slices|clove|cloves|head|heads|bunch|bunches|can|cans|jar|jars|package|packages|container|containers)\b",
    }

    # Quantity patterns
    QUANTITY_PATTERN = (
        r"^(\d+(?:\.\d+)?(?:\s*[-/]\s*\d+(?:\.\d+)?)?|\d+\s*\(\d+[^)]*\)|\½|⅓|⅔|¼|¾|⅛|⅜|⅝|⅞)"
    )

    def parse_ingredient(self, ingredient_text: str) -> dict[str, str]:
        """Parse a single ingredient string."""
        if not ingredient_text or not isinstance(ingredient_text, str):
            return {
                "name": "",
                "quantity": "",
                "unit": "",
                "original": ingredient_text or "",
                "confidence": 0.0,
            }

        cleaned = ingredient_text.strip()
        original = cleaned

        # Extract quantity
        quantity_match = re.match(self.QUANTITY_PATTERN, cleaned, re.IGNORECASE)
        quantity = quantity_match.group(1) if quantity_match else ""

        if quantity:
            cleaned = cleaned[len(quantity) :].strip()

        # Extract unit
        unit = ""
        confidence = 0.8  # Default confidence

        for _unit_type, pattern in self.UNIT_PATTERNS.items():
            unit_match = re.search(pattern, cleaned, re.IGNORECASE)
            if unit_match:
                unit = unit_match.group(1)
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
                break

        # Clean up ingredient name
        name = self._clean_ingredient_name(cleaned)

        # Adjust confidence based on parsing success
        if not quantity and not unit:
            confidence = 0.5
        elif not quantity or not unit:
            confidence = 0.7

        return {
            "name": name,
            "quantity": quantity,
            "unit": unit,
            "original": original,
            "confidence": confidence,
        }

    def _clean_ingredient_name(self, name: str) -> str:
        """Clean and normalize ingredient name."""
        # Remove common prefixes/suffixes
        name = re.sub(
            r"^(fresh|dried|chopped|minced|sliced|diced|grated|frozen)\s+",
            "",
            name,
            flags=re.IGNORECASE,
        )
        name = re.sub(
            r"\s+(fresh|dried|chopped|minced|sliced|diced|grated|frozen)$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        # Remove parenthetical notes
        name = re.sub(r"\([^)]*\)", "", name)

        # Remove extra whitespace
        name = " ".join(name.split())

        return name.lower().strip()


class RecipeDataProcessor:
    """Process recipe data including time estimation and classification."""

    CUISINE_KEYWORDS = {
        "italian": ["pasta", "parmesan", "basil", "mozzarella", "marinara", "pesto"],
        "mexican": ["cilantro", "jalapeño", "cumin", "lime", "avocado", "tortilla"],
        "asian": ["soy sauce", "ginger", "garlic", "sesame", "rice", "noodles"],
        "indian": ["curry", "turmeric", "cumin", "coriander", "garam masala", "yogurt"],
        "mediterranean": ["olive oil", "olives", "feta", "lemon", "oregano", "tomato"],
        "american": ["bacon", "cheese", "beef", "barbecue", "corn", "potato"],
    }

    DIFFICULTY_INDICATORS = {
        "easy": ["simple", "quick", "easy", "basic", "beginner"],
        "hard": ["advanced", "complex", "gourmet", "professional", "technique", "sous vide"],
    }

    def estimate_times(self, instructions: str) -> tuple[int, int]:
        """Estimate prep and cook times from instructions."""
        if not instructions:
            return 15, 30  # Default values

        text = instructions.lower()

        # Look for explicit time mentions
        time_patterns = [
            r"(\d+)\s*(?:to\s*)?(\d+)?\s*(?:hours?|hrs?)",
            r"(\d+)\s*(?:to\s*)?(\d+)?\s*(?:minutes?|mins?)",
        ]

        total_time = 0
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match[1]:  # Range given, take average
                    time_val = (int(match[0]) + int(match[1])) / 2
                else:
                    time_val = int(match[0])

                if "hour" in pattern:
                    time_val *= 60

                total_time += time_val

        # If no explicit times found, estimate based on content
        if total_time == 0:
            instruction_count = len(instructions.split("."))
            if instruction_count <= 3:
                total_time = 20
            elif instruction_count <= 6:
                total_time = 35
            else:
                total_time = 50

        # Split into prep and cook time (rough estimation)
        prep_time = min(int(total_time * 0.3), 30)
        cook_time = max(int(total_time * 0.7), 10)

        return prep_time, cook_time

    def classify_cuisine(self, title: str, ingredients_text: str) -> str:
        """Classify recipe cuisine based on title and ingredients."""
        text = f"{title} {ingredients_text}".lower()

        cuisine_scores = {}
        for cuisine, keywords in self.CUISINE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                cuisine_scores[cuisine] = score

        if cuisine_scores:
            return max(cuisine_scores.items(), key=lambda x: x[1])[0]

        return "american"  # Default cuisine

    def estimate_difficulty(self, title: str, instructions: str) -> str:
        """Estimate recipe difficulty."""
        text = f"{title} {instructions}".lower()

        for difficulty, indicators in self.DIFFICULTY_INDICATORS.items():
            if any(indicator in text for indicator in indicators):
                return difficulty

        # Estimate based on instruction complexity
        instruction_count = len(instructions.split("."))
        if instruction_count <= 4:
            return "easy"
        elif instruction_count >= 8:
            return "hard"

        return "medium"


class BackupRecipeImporter:
    """Main importer class for backup recipes."""

    def __init__(self):
        self.ingredient_parser = IngredientParser()
        self.data_processor = RecipeDataProcessor()
        self.stats = RecipeImportStats()

    async def import_recipes(
        self, batch_size: int = 100, start_from: int = 0, max_records: Optional[int] = None
    ):
        """Import recipes from CSV with batch processing."""

        # Connect to database
        db_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"

        conn = await asyncpg.connect(db_url)

        try:
            self.stats.start_time = time.time()
            logger.info(f"🚀 Starting recipe import from {CSV_FILE_PATH}")
            logger.info(
                f"📋 Batch size: {batch_size}, Start from: {start_from}, Max records: {max_records}"
            )

            # Prepare batch for insertion
            batch_recipes = []
            batch_ingredients = []

            with open(CSV_FILE_PATH, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                # Skip to start position
                for _ in range(start_from):
                    next(reader, None)

                for row in reader:
                    if max_records and self.stats.total_processed >= max_records:
                        break

                    self.stats.total_processed += 1

                    try:
                        # Process recipe data
                        recipe_data, ingredients_data = await self._process_recipe_row(row)

                        if recipe_data:
                            batch_recipes.append(recipe_data)
                            batch_ingredients.extend(ingredients_data)
                            self.stats.successful_imports += 1
                        else:
                            self.stats.failed_imports += 1

                        # Process batch when full
                        if len(batch_recipes) >= batch_size:
                            await self._insert_batch(conn, batch_recipes, batch_ingredients)
                            batch_recipes.clear()
                            batch_ingredients.clear()

                        self.stats.log_progress(batch_size)

                    except Exception as e:
                        logger.error(f"❌ Error processing row {self.stats.total_processed}: {e}")
                        self.stats.failed_imports += 1
                        self.stats.parsing_errors += 1

            # Insert remaining batch
            if batch_recipes:
                await self._insert_batch(conn, batch_recipes, batch_ingredients)

            # Log final statistics
            elapsed = time.time() - self.stats.start_time
            logger.info(f"🎉 Import completed in {elapsed:.1f} seconds")
            logger.info(
                f"📊 Final stats: {self.stats.successful_imports} imported, {self.stats.failed_imports} failed"
            )

        finally:
            await conn.close()

    async def _process_recipe_row(self, row: dict) -> tuple[Optional[dict], list[dict]]:
        """Process a single CSV row into recipe and ingredients data."""
        try:
            title = row.get("Title", "").strip()
            if not title:
                return None, []

            ingredients_raw = row.get("Ingredients", "")
            instructions = row.get("Instructions", "")
            image_name = row.get("Image_Name", "")
            cleaned_ingredients = row.get("Cleaned_Ingredients", "")

            # Parse ingredients list
            ingredients_list = self._parse_ingredients_list(ingredients_raw)

            # Process recipe metadata
            prep_time, cook_time = self.data_processor.estimate_times(instructions)
            cuisine_type = self.data_processor.classify_cuisine(title, ingredients_raw)
            difficulty = self.data_processor.estimate_difficulty(title, instructions)

            # Estimate servings (simple heuristic)
            servings = self._estimate_servings(ingredients_raw)

            # Check if image exists
            image_path = Path(IMAGES_DIR) / image_name if image_name else None
            if image_name and not (image_path and image_path.exists()):
                self.stats.missing_images += 1
                image_name = None

            # Create recipe record
            recipe_data = {
                "title": title[:500],  # Truncate to fit DB constraint
                "ingredients": ingredients_raw,
                "instructions": instructions,
                "image_name": image_name,
                "cleaned_ingredients": cleaned_ingredients,
                "prep_time": prep_time,
                "cook_time": cook_time,
                "servings": servings,
                "difficulty": difficulty,
                "cuisine_type": cuisine_type,
            }

            # Create ingredient records
            ingredients_data = []
            for ingredient in ingredients_list:
                parsed = self.ingredient_parser.parse_ingredient(ingredient)
                if parsed["name"]:  # Only add if we got a valid ingredient name
                    ingredients_data.append(
                        {
                            "ingredient_name": parsed["name"][:255],  # Truncate to fit DB
                            "original_text": parsed["original"],
                            "quantity": parsed["quantity"][:50] if parsed["quantity"] else None,
                            "unit": parsed["unit"][:50] if parsed["unit"] else None,
                            "confidence": parsed["confidence"],
                        }
                    )

            return recipe_data, ingredients_data

        except Exception as e:
            logger.error(f"Error processing recipe row: {e}")
            return None, []

    def _parse_ingredients_list(self, ingredients_text: str) -> list[str]:
        """Parse ingredients list from CSV format."""
        if not ingredients_text:
            return []

        try:
            # Try to parse as JSON array
            if ingredients_text.startswith("[") and ingredients_text.endswith("]"):
                ingredients_list = json.loads(ingredients_text)
                return [ing.strip() for ing in ingredients_list if ing.strip()]
        except json.JSONDecodeError:
            pass

        # Fall back to simple splitting
        return [ing.strip() for ing in ingredients_text.split(",") if ing.strip()]

    def _estimate_servings(self, ingredients_text: str) -> int:
        """Estimate servings from ingredients text."""
        # Look for serving indicators
        text = ingredients_text.lower()

        serving_patterns = [r"serves?\s+(\d+)", r"(\d+)\s+servings?", r"(\d+)\s+portions?"]

        for pattern in serving_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        # Default estimate based on quantity indicators
        if any(word in text for word in ["large", "whole", "entire"]):
            return 6
        elif any(word in text for word in ["small", "individual"]):
            return 2

        return 4  # Default serving size

    async def _insert_batch(
        self, conn: asyncpg.Connection, recipes: list[dict], ingredients: list[dict]
    ):
        """Insert a batch of recipes and ingredients."""
        try:
            # Insert recipes first
            recipe_insert_query = """
                INSERT INTO backup_recipes (
                    title, ingredients, instructions, image_name, cleaned_ingredients,
                    prep_time, cook_time, servings, difficulty, cuisine_type
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING backup_recipe_id
            """

            recipe_ids = []
            for recipe in recipes:
                recipe_id = await conn.fetchval(
                    recipe_insert_query,
                    recipe["title"],
                    recipe["ingredients"],
                    recipe["instructions"],
                    recipe["image_name"],
                    recipe["cleaned_ingredients"],
                    recipe["prep_time"],
                    recipe["cook_time"],
                    recipe["servings"],
                    recipe["difficulty"],
                    recipe["cuisine_type"],
                )
                recipe_ids.append(recipe_id)

            # Insert ingredients with recipe IDs
            if ingredients and recipe_ids:
                ingredient_insert_query = """
                    INSERT INTO backup_recipe_ingredients (
                        backup_recipe_id, ingredient_name, original_text, quantity, unit, confidence
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """

                ingredient_records = []
                ingredients_per_recipe = len(ingredients) // len(recipe_ids) if recipe_ids else 0

                for i, recipe_id in enumerate(recipe_ids):
                    start_idx = i * ingredients_per_recipe
                    end_idx = (
                        start_idx + ingredients_per_recipe
                        if i < len(recipe_ids) - 1
                        else len(ingredients)
                    )

                    for ingredient in ingredients[start_idx:end_idx]:
                        ingredient_records.append(
                            (
                                recipe_id,
                                ingredient["ingredient_name"],
                                ingredient["original_text"],
                                ingredient["quantity"],
                                ingredient["unit"],
                                ingredient["confidence"],
                            )
                        )

                if ingredient_records:
                    await conn.executemany(ingredient_insert_query, ingredient_records)

        except Exception as e:
            logger.error(f"Error inserting batch: {e}")
            raise


async def main():
    """Main function to run the import."""
    import argparse

    parser = argparse.ArgumentParser(description="Import backup recipes from CSV")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--start-from", type=int, default=0, help="Record number to start from")
    parser.add_argument("--max-records", type=int, help="Maximum number of records to process")
    parser.add_argument("--test-run", action="store_true", help="Import only first 100 records")

    args = parser.parse_args()

    if args.test_run:
        args.max_records = 100
        logger.info("🧪 Running in test mode - importing only 100 records")

    importer = BackupRecipeImporter()
    await importer.import_recipes(
        batch_size=args.batch_size, start_from=args.start_from, max_records=args.max_records
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    asyncio.run(main())
