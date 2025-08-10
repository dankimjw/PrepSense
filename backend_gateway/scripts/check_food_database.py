#!/usr/bin/env python3
"""
Check if food categorization database is deployed and working
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import from backend_gateway
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def check_food_database():
    """Check what food database tables exist and their content"""

    # Get the database service
    db_service = get_database_service()

    try:
        print("Checking food categorization database tables...")

        # Check for food categorization tables
        food_tables = [
            "food_items_cache",
            "food_unit_mappings",
            "food_categorization_corrections",
            "food_search_history",
            "food_aliases",
            "api_rate_limits",
        ]

        existing_tables = []
        for table_name in food_tables:
            tables = db_service.execute_query(
                """
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %(table_name)s
            """,
                {"table_name": table_name},
            )

            exists = tables[0]["count"] > 0 if tables else False
            if exists:
                existing_tables.append(table_name)
                print(f"  ✅ {table_name} exists")
            else:
                print(f"  ❌ {table_name} missing")

        print(f"\nFood database status: {len(existing_tables)}/{len(food_tables)} tables exist")

        # Check API rate limits table content
        if "api_rate_limits" in existing_tables:
            rate_limits = db_service.execute_query("SELECT * FROM api_rate_limits")
            print(f"\nAPI rate limits configured: {len(rate_limits)} APIs")
            for api in rate_limits:
                print(
                    f"  - {api['api_name']}: {api['requests_today']}/{api['daily_limit']} requests"
                )

        # Check if USDA API key is configured
        usda_key = os.getenv("USDA_API_KEY")
        usda_key_file = Path("config/usda_key.txt")

        print("\nUSDA API Integration:")
        if usda_key:
            print("  ✅ USDA_API_KEY environment variable set")
        elif usda_key_file.exists():
            print(f"  ✅ USDA API key file exists: {usda_key_file}")
        else:
            print("  ❌ No USDA API key configured")
            print(f"     Set USDA_API_KEY environment variable or create {usda_key_file}")
            print("     Get free API key at: https://fdc.nal.usda.gov/api-key-signup.html")

        # Check OpenFoodFacts availability (no key needed)
        print("\nOpenFoodFacts Integration:")
        print("  ✅ Available (no API key required)")

        # Check Spoonacular API key
        spoon_key = os.getenv("SPOONACULAR_API_KEY")
        print("\nSpoonacular API Integration:")
        if spoon_key and spoon_key != "your-spoonacular-api-key":
            print("  ✅ Spoonacular API key configured")
        else:
            print("  ⚠️  Spoonacular API key not configured or using placeholder")

        print("\n🏁 Summary:")
        if len(existing_tables) == len(food_tables):
            print("  ✅ Food categorization database is fully deployed")
        elif len(existing_tables) > 0:
            print("  ⚠️  Food categorization database is partially deployed")
            print(f"     Missing: {set(food_tables) - set(existing_tables)}")
        else:
            print("  ❌ Food categorization database is not deployed")
            print("     Run: python backend_gateway/scripts/deploy_food_categorization.py")

    except Exception as e:
        print(f"\n❌ Error checking food database: {str(e)}")
        raise
    finally:
        db_service.close()


if __name__ == "__main__":
    check_food_database()
