#!/usr/bin/env python3
"""
Script to fix pantry item units and categories using the smart unit validator.
This will:
1. Check all pantry items for incorrect units
2. Suggest appropriate units based on food categories
3. Update units that are clearly wrong (e.g., strawberries in mL)
4. Add proper categories to items missing them
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.core.config import settings
from backend_gateway.services.smart_unit_validator import SmartUnitValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Category mapping based on common food items
CATEGORY_MAPPINGS = {
    "produce": [
        "strawberries",
        "blueberries",
        "raspberries",
        "blackberries",
        "grapes",
        "apples",
        "bananas",
        "oranges",
        "lemons",
        "limes",
        "peaches",
        "pears",
        "carrots",
        "celery",
        "lettuce",
        "spinach",
        "broccoli",
        "tomatoes",
        "potatoes",
        "onions",
        "garlic",
        "peppers",
        "cucumber",
        "kale",
    ],
    "dairy": [
        "milk",
        "yogurt",
        "cheese",
        "butter",
        "cream",
        "sour cream",
        "cottage cheese",
        "cream cheese",
        "half and half",
        "eggs",
    ],
    "meat": [
        "chicken",
        "beef",
        "pork",
        "turkey",
        "bacon",
        "sausage",
        "ground beef",
        "steak",
        "ham",
        "lamb",
        "fish",
        "salmon",
        "tuna",
    ],
    "beverages": [
        "juice",
        "soda",
        "water",
        "coffee",
        "tea",
        "beer",
        "wine",
        "energy drink",
        "sports drink",
        "kombucha",
        "coconut water",
    ],
    "grains": [
        "bread",
        "rice",
        "pasta",
        "cereal",
        "oats",
        "quinoa",
        "flour",
        "crackers",
        "tortillas",
        "bagels",
        "muffins",
        "granola",
    ],
    "spices": [
        "salt",
        "pepper",
        "cinnamon",
        "paprika",
        "oregano",
        "basil",
        "thyme",
        "rosemary",
        "garlic powder",
        "onion powder",
        "cumin",
    ],
}


def categorize_item(item_name: str) -> Optional[str]:
    """Determine the category for an item based on its name."""
    item_lower = item_name.lower()

    for category, keywords in CATEGORY_MAPPINGS.items():
        for keyword in keywords:
            if keyword in item_lower:
                return category.title()

    return None


async def analyze_pantry_units(db_pool: asyncpg.Pool, user_id: Optional[int] = None):
    """Analyze all pantry items and identify unit issues."""

    validator = SmartUnitValidator(db_pool)

    # Get all pantry items
    async with db_pool.acquire() as conn:
        if user_id:
            query = """
                SELECT 
                    pi.pantry_item_id as id,
                    pi.product_name as name,
                    pi.quantity as quantity_amount,
                    pi.unit_of_measurement as quantity_unit,
                    pi.category,
                    p.user_id
                FROM pantry_items pi
                JOIN pantries p ON pi.pantry_id = p.pantry_id
                WHERE p.user_id = $1
                AND (pi.status IS NULL OR pi.status != 'consumed')
                ORDER BY pi.product_name
            """
            items = await conn.fetch(query, user_id)
        else:
            query = """
                SELECT 
                    pi.pantry_item_id as id,
                    pi.product_name as name,
                    pi.quantity as quantity_amount,
                    pi.unit_of_measurement as quantity_unit,
                    pi.category,
                    p.user_id
                FROM pantry_items pi
                JOIN pantries p ON pi.pantry_id = p.pantry_id
                WHERE (pi.status IS NULL OR pi.status != 'consumed')
                ORDER BY p.user_id, pi.product_name
            """
            items = await conn.fetch(query)

    logger.info(f"Found {len(items)} pantry items to analyze")

    issues = []
    category_fixes = []

    for item in items:
        # Check unit validation
        validation = await validator.validate_and_suggest_unit(
            item["name"], item["quantity_unit"] or "each", item["quantity_amount"]
        )

        # Check if unit needs fixing
        if validation["severity"] in ["error", "warning"]:
            issues.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "user_id": item["user_id"],
                    "current_unit": item["quantity_unit"],
                    "suggested_unit": validation["suggested_unit"],
                    "reason": validation["reason"],
                    "severity": validation["severity"],
                    "category": validation["category"],
                }
            )

        # Check if category needs fixing
        if not item["category"] or item["category"] == "Other":
            suggested_category = categorize_item(item["name"])
            if suggested_category:
                category_fixes.append(
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "current_category": item["category"],
                        "suggested_category": suggested_category,
                    }
                )

    return issues, category_fixes


async def fix_units(db_pool: asyncpg.Pool, issues: List[Dict], dry_run: bool = True):
    """Fix unit issues in the database."""

    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    fixed_count = 0

    async with db_pool.acquire() as conn:
        for issue in issues:
            if issue["severity"] == "error":  # Only auto-fix errors, not warnings
                if dry_run:
                    logger.info(
                        f"Would fix: {issue['name']} - "
                        f"{issue['current_unit']} → {issue['suggested_unit']} "
                        f"(Reason: {issue['reason']})"
                    )
                else:
                    await conn.execute(
                        "UPDATE pantry_items SET unit_of_measurement = $1 WHERE pantry_item_id = $2",
                        issue["suggested_unit"],
                        issue["id"],
                    )
                    logger.info(
                        f"Fixed: {issue['name']} - "
                        f"{issue['current_unit']} → {issue['suggested_unit']}"
                    )
                fixed_count += 1

    return fixed_count


async def fix_categories(db_pool: asyncpg.Pool, category_fixes: List[Dict], dry_run: bool = True):
    """Fix category issues in the database."""

    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    fixed_count = 0

    async with db_pool.acquire() as conn:
        for fix in category_fixes:
            if dry_run:
                logger.info(
                    f"Would categorize: {fix['name']} - "
                    f"{fix['current_category']} → {fix['suggested_category']}"
                )
            else:
                await conn.execute(
                    "UPDATE pantry_items SET category = $1 WHERE pantry_item_id = $2",
                    fix["suggested_category"],
                    fix["id"],
                )
                logger.info(f"Categorized: {fix['name']} → {fix['suggested_category']}")
            fixed_count += 1

    return fixed_count


async def main():
    """Main function to run the unit fixing script."""

    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Fix pantry item units and categories")
    parser.add_argument("--user-id", type=int, help="Fix items for specific user only")
    parser.add_argument(
        "--apply", action="store_true", help="Actually apply the fixes (default is dry run)"
    )
    parser.add_argument("--units-only", action="store_true", help="Only fix units, not categories")
    parser.add_argument(
        "--categories-only", action="store_true", help="Only fix categories, not units"
    )

    args = parser.parse_args()

    # Create database connection pool
    db_pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DATABASE,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        min_size=1,
        max_size=10,
    )

    try:
        # Analyze pantry items
        logger.info("Analyzing pantry items...")
        issues, category_fixes = await analyze_pantry_units(db_pool, args.user_id)

        # Report findings
        logger.info(f"\nFound {len(issues)} unit issues:")

        errors = [i for i in issues if i["severity"] == "error"]
        warnings = [i for i in issues if i["severity"] == "warning"]

        logger.info(f"  - {len(errors)} errors (will be fixed)")
        logger.info(f"  - {len(warnings)} warnings (will not be auto-fixed)")
        logger.info(f"\nFound {len(category_fixes)} items without proper categories")

        # Show some examples
        if errors:
            logger.info("\nExample errors to fix:")
            for error in errors[:5]:
                logger.info(
                    f"  - {error['name']}: {error['current_unit']} → "
                    f"{error['suggested_unit']} ({error['reason']})"
                )

        if warnings:
            logger.info("\nExample warnings (not auto-fixed):")
            for warning in warnings[:10]:
                logger.info(
                    f"  - {warning['name']}: {warning['current_unit']} → "
                    f"{warning['suggested_unit']} ({warning['reason']})"
                )

        if category_fixes:
            logger.info("\nExample categories to fix:")
            for fix in category_fixes[:5]:
                logger.info(
                    f"  - {fix['name']}: {fix['current_category']} → "
                    f"{fix['suggested_category']}"
                )

        # Apply fixes if requested
        if args.apply:
            logger.info("\nApplying fixes...")

            if not args.categories_only:
                unit_fixed = await fix_units(db_pool, errors, dry_run=False)
                logger.info(f"Fixed {unit_fixed} unit errors")

            if not args.units_only:
                cat_fixed = await fix_categories(db_pool, category_fixes, dry_run=False)
                logger.info(f"Fixed {cat_fixed} categories")
        else:
            logger.info("\nDRY RUN - Use --apply to actually fix the issues")

            if not args.categories_only:
                await fix_units(db_pool, errors, dry_run=True)

            if not args.units_only:
                await fix_categories(db_pool, category_fixes, dry_run=True)

    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
