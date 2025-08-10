#!/usr/bin/env python3
"""
Fix existing pantry items units to match our standardized units table
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables from the correct path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


def fix_pantry_units():
    """Fix existing pantry items to use standardized units"""

    # Get database connection info from .env
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")

    if not all([host, database, password]):
        print("❌ Missing required database configuration")
        return

    print(f"Connecting to {host}:{port}/{database} as {user}...")

    try:
        # Connect directly with postgres credentials
        conn = psycopg2.connect(
            host=host, port=port, database=database, user=user, password=password, sslmode="require"
        )

        print("✅ Connected successfully!")

        # First, get current pantry items with invalid units
        print("\n📊 Analyzing current pantry items...")
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT unit_of_measurement, COUNT(*) as count
                FROM pantry_items
                WHERE unit_of_measurement IS NOT NULL
                GROUP BY unit_of_measurement
                ORDER BY count DESC
            """
            )
            current_units = cursor.fetchall()

            print(f"Found {len(current_units)} different units:")
            for unit, count in current_units:
                print(f"  - '{unit}': {count} items")

        # Get valid units from our units table
        print("\n📋 Getting valid units from units table...")
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, label, category FROM units ORDER BY display_order")
            valid_units = cursor.fetchall()

            print(f"Valid units ({len(valid_units)}):")
            for unit_id, label, category in valid_units:
                print(f"  - {unit_id} ({label}) - {category}")

        # Create unit mapping for common incorrect units
        unit_mapping = {
            # Mass units
            "grams": "g",
            "gram": "g",
            "kilograms": "kg",
            "kilogram": "kg",
            "kgs": "kg",
            "pounds": "lb",
            "pound": "lb",
            "lbs": "lb",
            "ounces": "oz",
            "ounce": "oz",
            "ozs": "oz",
            # Volume units
            "milliliters": "ml",
            "milliliter": "ml",
            "mls": "ml",
            "liters": "l",
            "liter": "l",
            "litres": "l",
            "litre": "l",
            "cups": "cup",
            "tablespoons": "tbsp",
            "tablespoon": "tbsp",
            "teaspoons": "tsp",
            "teaspoon": "tsp",
            "fluid ounces": "floz",
            "fluid ounce": "floz",
            "fl oz": "floz",
            "gallons": "gal",
            "gallon": "gal",
            "pints": "pt",
            "pint": "pt",
            "quarts": "qt",
            "quart": "qt",
            # Count units
            "pieces": "ea",
            "piece": "ea",
            "items": "ea",
            "item": "ea",
            "each": "ea",
            "dozens": "dozen",
            "pairs": "pair",
            "slices": "slice",
            "loaves": "loaf",
            "sticks": "stick",
            "cloves": "clove",
            "heads": "head",
            # Container units
            "cans": "can",
            "jars": "jar",
            "bottles": "bottle",
            "boxes": "box",
            "bags": "bag",
            "packages": "package",
            "bunches": "bunch",
            # Common variations
            "": "ea",  # Empty string defaults to each
            "null": "ea",
            "None": "ea",
        }

        # Apply unit corrections
        print("\n🔧 Applying unit corrections...")
        corrections_made = 0

        with conn.cursor() as cursor:
            for old_unit, new_unit in unit_mapping.items():
                # Check if the new unit exists in our units table
                cursor.execute("SELECT COUNT(*) FROM units WHERE id = %s", (new_unit,))
                if cursor.fetchone()[0] == 0:
                    print(
                        f"  ⚠️  Skipping {old_unit} -> {new_unit} (target unit not in units table)"
                    )
                    continue

                # Update pantry items
                cursor.execute(
                    """
                    UPDATE pantry_items
                    SET unit_of_measurement = %s
                    WHERE LOWER(TRIM(unit_of_measurement)) = LOWER(%s)
                """,
                    (new_unit, old_unit),
                )

                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    print(f"  ✅ {old_unit} -> {new_unit}: {rows_affected} items updated")
                    corrections_made += rows_affected

        # Handle remaining unmapped units
        print("\n🔍 Checking for remaining unmapped units...")
        with conn.cursor() as cursor:
            # Get units that don't exist in our units table
            cursor.execute(
                """
                SELECT DISTINCT pi.unit_of_measurement, COUNT(*) as count
                FROM pantry_items pi
                LEFT JOIN units u ON pi.unit_of_measurement = u.id
                WHERE pi.unit_of_measurement IS NOT NULL
                AND u.id IS NULL
                GROUP BY pi.unit_of_measurement
                ORDER BY count DESC
            """
            )
            unmapped_units = cursor.fetchall()

            if unmapped_units:
                print(f"Found {len(unmapped_units)} unmapped units:")
                for unit, count in unmapped_units:
                    print(f"  - '{unit}': {count} items")

                    # Try to guess appropriate mapping
                    suggested_unit = "ea"  # Default fallback
                    unit_lower = str(unit).lower().strip()

                    if any(
                        word in unit_lower
                        for word in ["ml", "liter", "cup", "gallon", "pint", "quart", "fluid"]
                    ):
                        suggested_unit = "ml"
                    elif any(
                        word in unit_lower for word in ["gram", "kg", "pound", "lb", "oz", "ounce"]
                    ):
                        suggested_unit = "g"
                    elif any(
                        word in unit_lower
                        for word in ["bottle", "can", "jar", "box", "bag", "package"]
                    ):
                        suggested_unit = (
                            unit_lower
                            if unit_lower in ["bottle", "can", "jar", "box", "bag", "package"]
                            else "ea"
                        )

                    # Update to suggested unit
                    cursor.execute(
                        """
                        UPDATE pantry_items
                        SET unit_of_measurement = %s
                        WHERE unit_of_measurement = %s
                    """,
                        (suggested_unit, unit),
                    )

                    rows_affected = cursor.rowcount
                    print(f"    → Auto-corrected to '{suggested_unit}': {rows_affected} items")
                    corrections_made += rows_affected
            else:
                print("  ✅ All units are now standardized!")

        # Commit all changes
        conn.commit()

        # Final verification
        print("\n📈 Final verification...")
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_items,
                    COUNT(DISTINCT unit_of_measurement) as unique_units,
                    SUM(CASE WHEN u.id IS NOT NULL THEN 1 ELSE 0 END) as valid_units,
                    SUM(CASE WHEN u.id IS NULL THEN 1 ELSE 0 END) as invalid_units
                FROM pantry_items pi
                LEFT JOIN units u ON pi.unit_of_measurement = u.id
                WHERE pi.unit_of_measurement IS NOT NULL
            """
            )
            stats = cursor.fetchone()

            total, unique, valid, invalid = stats
            print(f"  📊 Total items: {total}")
            print(f"  📊 Unique units: {unique}")
            print(f"  ✅ Valid units: {valid}")
            print(f"  ❌ Invalid units: {invalid}")

            if invalid == 0:
                print("\n🎉 Unit standardization completed successfully!")
                print(f"   Made {corrections_made} corrections total")
            else:
                print(f"\n⚠️  {invalid} items still have invalid units")

    except Exception as e:
        print(f"❌ Error fixing pantry units: {str(e)}")
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    fix_pantry_units()
