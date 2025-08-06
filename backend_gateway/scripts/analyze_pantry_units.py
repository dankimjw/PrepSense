"""Script to analyze and fix invalid units in existing pantry items"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from collections import defaultdict

from backend_gateway.config.database import get_database_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_pantry_units():
    """Analyze all pantry items to find invalid unit/item combinations"""

    db_service = get_database_service()

    # Get all pantry items
    query = """
    SELECT 
        pi.pantry_item_id,
        pi.product_name,
        pi.category,
        pi.unit_of_measurement,
        pi.quantity,
        pi.pantry_id,
        p.user_id
    FROM pantry_items pi
    JOIN pantries p ON pi.pantry_id = p.pantry_id
    WHERE pi.status = 'available'
    ORDER BY pi.product_name
    """

    items = db_service.execute_query(query)
    logger.info(f"Found {len(items)} pantry items to analyze")

    # Define invalid combinations
    liquid_units = [
        "ml",
        "l",
        "liter",
        "milliliter",
        "gallon",
        "quart",
        "pint",
        "fluid ounce",
        "fl oz",
        "cup",
        "cups",
    ]
    solid_items = [
        "bread",
        "cookie",
        "chip",
        "cracker",
        "cake",
        "sandwich",
        "bar",
        "pizza",
        "bagel",
    ]

    weight_units = ["g", "gram", "grams", "kg", "kilogram", "oz", "ounce", "lb", "pound", "pounds"]
    count_units = [
        "each",
        "piece",
        "pieces",
        "item",
        "items",
        "loaf",
        "loaves",
        "slice",
        "slices",
        "bag",
        "bags",
        "box",
        "boxes",
        "package",
        "packages",
    ]

    invalid_items = []
    unit_stats = defaultdict(int)
    category_unit_stats = defaultdict(lambda: defaultdict(int))

    for item in items:
        product_name = item["product_name"].lower()
        unit = item["unit_of_measurement"].lower().strip()
        category = item.get("category", "unknown")

        unit_stats[unit] += 1
        category_unit_stats[category][unit] += 1

        # Check for invalid combinations
        is_invalid = False
        reason = ""
        suggested_unit = None

        # Check if solid item is measured in liquid units
        if any(solid in product_name for solid in solid_items) and unit in liquid_units:
            is_invalid = True
            reason = "Solid item measured in liquid units"
            # Suggest appropriate unit based on item type
            if "bread" in product_name or "bagel" in product_name:
                suggested_unit = "loaf" if "loaf" in product_name else "each"
            elif any(x in product_name for x in ["cookie", "chip", "cracker"]):
                suggested_unit = "piece" if "cookie" in product_name else "bag"
            else:
                suggested_unit = "each"

        # Check if liquid item is measured in count units
        liquid_keywords = ["milk", "juice", "water", "oil", "sauce", "soup", "drink", "beverage"]
        if any(liquid in product_name for liquid in liquid_keywords) and unit in count_units:
            is_invalid = True
            reason = "Liquid item measured in count units"
            suggested_unit = "liter" if "water" in product_name else "ml"

        if is_invalid:
            invalid_items.append(
                {
                    "pantry_item_id": item["pantry_item_id"],
                    "product_name": item["product_name"],
                    "current_unit": item["unit_of_measurement"],
                    "suggested_unit": suggested_unit,
                    "reason": reason,
                    "quantity": item["quantity"],
                    "user_id": item["user_id"],
                }
            )

    # Print analysis results
    print("\n=== Pantry Units Analysis ===")
    print(f"Total items analyzed: {len(items)}")
    print(f"Invalid unit combinations found: {len(invalid_items)}")

    print("\n=== Unit Usage Statistics ===")
    for unit, count in sorted(unit_stats.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{unit}: {count} items")

    print("\n=== Invalid Items (First 20) ===")
    for item in invalid_items[:20]:
        print(f"\n{item['product_name']}:")
        print(f"  Current: {item['quantity']} {item['current_unit']}")
        print(f"  Suggested: {item['quantity']} {item['suggested_unit']}")
        print(f"  Reason: {item['reason']}")
        print(f"  User ID: {item['user_id']}")

    return invalid_items


def generate_fix_script(invalid_items):
    """Generate SQL script to fix invalid units"""

    print("\n=== Generating Fix Script ===")

    # Group fixes by suggested unit change
    fixes_by_change = defaultdict(list)
    for item in invalid_items:
        key = f"{item['current_unit']} -> {item['suggested_unit']}"
        fixes_by_change[key].append(item)

    # Create SQL update statements
    sql_statements = []

    for change, items in fixes_by_change.items():
        current_unit = items[0]["current_unit"]
        suggested_unit = items[0]["suggested_unit"]

        # Get all IDs for this change
        item_ids = [str(item["pantry_item_id"]) for item in items]

        sql = f"""
-- Fix {len(items)} items: {change}
UPDATE pantry_items 
SET unit_of_measurement = '{suggested_unit}'
WHERE pantry_item_id IN ({','.join(item_ids)})
AND unit_of_measurement = '{current_unit}';
"""
        sql_statements.append(sql)

    # Write to file
    with open("fix_pantry_units.sql", "w") as f:
        f.write("-- Script to fix invalid unit combinations in pantry items\n")
        f.write("-- Generated by analyze_pantry_units.py\n\n")
        f.write("BEGIN;\n\n")

        for sql in sql_statements:
            f.write(sql)

        f.write("\n-- Review changes before committing\n")
        f.write("-- COMMIT;\n")
        f.write("-- or ROLLBACK;\n")

    print(f"Fix script written to fix_pantry_units.sql")
    print(f"Total updates: {len(invalid_items)}")
    print("\nReview the script before running it on the database!")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    invalid_items = analyze_pantry_units()

    if invalid_items:
        response = input("\nGenerate fix script? (y/n): ")
        if response.lower() == "y":
            generate_fix_script(invalid_items)
    else:
        print("\nNo invalid unit combinations found!")
