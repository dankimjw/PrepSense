#!/usr/bin/env python3
"""
Script to drop the foreign key constraint on user_recipes.recipe_id
This allows storing external recipe IDs without requiring them in the local recipes table
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def run_migration():
    """Run the migration to drop the foreign key constraint"""
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Check if constraint exists
        print("\nChecking for existing foreign key constraint...")
        cur.execute(
            """
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'user_recipes' 
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'recipe_id';
        """
        )

        existing_constraint = cur.fetchone()

        if existing_constraint:
            print(f"Found constraint: {existing_constraint['constraint_name']}")

            # Drop the constraint
            print("\nDropping foreign key constraint...")
            cur.execute(
                "ALTER TABLE user_recipes DROP CONSTRAINT IF EXISTS user_recipes_recipe_id_fkey;"
            )

            # Add comment
            cur.execute(
                """
                COMMENT ON COLUMN user_recipes.recipe_id IS 
                'Recipe ID - can be NULL for custom recipes, or contain external IDs (e.g., Spoonacular). No FK constraint since we support external recipes.';
            """
            )

            conn.commit()
            print("✅ Foreign key constraint dropped successfully!")

        else:
            print("✅ No foreign key constraint found - database is already in the correct state!")

        # Verify the change
        print("\nVerifying constraint removal...")
        cur.execute(
            """
            SELECT COUNT(*) as fk_count
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'user_recipes' 
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'recipe_id';
        """
        )

        result = cur.fetchone()
        if result["fk_count"] == 0:
            print("✅ Verified: No foreign key constraints on user_recipes.recipe_id")
        else:
            print("⚠️  Warning: Foreign key constraint may still exist")

        # Test by showing some sample data
        print("\nChecking user_recipes table...")
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_recipes,
                COUNT(DISTINCT source) as sources,
                COUNT(recipe_id) as with_recipe_id,
                COUNT(*) - COUNT(recipe_id) as without_recipe_id
            FROM user_recipes;
        """
        )

        stats = cur.fetchone()
        print(f"\nUser recipes statistics:")
        print(f"  Total recipes: {stats['total_recipes']}")
        print(f"  Recipe sources: {stats['sources']}")
        print(f"  With recipe_id: {stats['with_recipe_id']}")
        print(f"  Without recipe_id: {stats['without_recipe_id']}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    print("=== Dropping Foreign Key Constraint on user_recipes.recipe_id ===")
    print("\nThis will allow storing external recipe IDs (e.g., from Spoonacular)")
    print("without requiring them to exist in the local recipes table.\n")

    response = input("Proceed with migration? (y/n): ")
    if response.lower() == "y":
        run_migration()
    else:
        print("Migration cancelled.")
