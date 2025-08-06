#!/usr/bin/env python3
"""
Deploy units table to GCP Cloud SQL database
This script should be run from the backend to use the correct database connection
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


def deploy_units_table():
    """Deploy the units table schema to the database"""

    # Get the database service
    db_service = get_database_service()

    # Read the SQL script
    script_path = Path(__file__).parent / "create_units_table.sql"
    with open(script_path, "r") as f:
        sql_script = f.read()

    try:
        print(f"Connecting to database...")

        # Split the script into individual statements
        statements = sql_script.split(";")
        statements = [stmt.strip() for stmt in statements if stmt.strip()]

        print("Creating units tables...")
        for i, statement in enumerate(statements):
            if statement:
                print(f"Executing statement {i+1}/{len(statements)}")
                db_service.execute_query(statement)

        # Verify tables were created
        tables = db_service.execute_query(
            """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('units', 'item_unit_mappings')
        """
        )

        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table['tablename']}")

        # Count records in units table
        count_result = db_service.execute_query("SELECT COUNT(*) FROM units")
        count = count_result[0]["count"] if count_result else 0
        print(f"\nInserted {count} unit records")

        print("\n✅ Units table deployment completed successfully!")

    except Exception as e:
        print(f"\n❌ Error deploying units table: {str(e)}")
        raise
    finally:
        db_service.close()


if __name__ == "__main__":
    deploy_units_table()
