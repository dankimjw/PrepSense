#!/usr/bin/env python3
"""
Check all table names in the database
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def check_tables():
    """List all tables"""
    print("Checking all tables in database...")

    # Get database service
    db_service = get_database_service()

    try:
        # Get all tables
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """

        tables = db_service.execute_query(tables_query)
        print("\nAll tables:")
        for table in tables:
            print(f"  - {table['table_name']}")

        # Check specifically for pantry-related tables
        print("\nPantry-related tables:")
        for table in tables:
            name = table["table_name"]
            if "pantry" in name.lower():
                print(f"  - {name}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    check_tables()
