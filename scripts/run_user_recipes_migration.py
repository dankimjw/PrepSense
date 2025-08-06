#!/usr/bin/env python3
"""Run the user_recipes status column migration"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

# Load environment variables from main project .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


def run_migration():
    """Run the user_recipes status column migration"""

    # Get database connection parameters
    db_params = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT", 5432),
        "database": os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }

    # Check if all required parameters are present
    missing_params = [k for k, v in db_params.items() if not v]
    if missing_params:
        print(f"Error: Missing database parameters: {missing_params}")
        print("Please check your .env file")
        return False

    migration_file = (
        Path(__file__).parent / "backend_gateway" / "migrations" / "add_user_recipes_status.sql"
    )

    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        return False

    try:
        # Connect to database
        print(
            f"Connecting to database at {db_params['host']}:{db_params['port']}/{db_params['database']}..."
        )
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Read migration SQL
        with open(migration_file, "r") as f:
            migration_sql = f.read()

        print("Running migration...")
        cursor.execute(migration_sql)

        # Verify the columns were added
        cursor.execute(
            """
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'user_recipes'
            AND column_name IN ('status', 'cooked_at')
            ORDER BY column_name;
        """
        )

        columns = cursor.fetchall()
        print("\nVerified columns in user_recipes table:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (default: {col[2]})")

        # Check how many records were updated
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_recipes,
                COUNT(CASE WHEN status = 'saved' THEN 1 END) as saved_recipes,
                COUNT(CASE WHEN status = 'cooked' THEN 1 END) as cooked_recipes
            FROM user_recipes;
        """
        )

        stats = cursor.fetchone()
        print(f"\nRecipe statistics after migration:")
        print(f"  - Total recipes: {stats[0]}")
        print(f"  - Saved recipes: {stats[1]}")
        print(f"  - Cooked recipes: {stats[2]}")

        # Commit the transaction
        conn.commit()
        print("\nMigration completed successfully!")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\nError running migration: {str(e)}")
        if "conn" in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
