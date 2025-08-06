#!/usr/bin/env python3
"""
Check the recipes table and foreign key constraints
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def check_recipes_constraint():
    """Check recipes table and constraints"""
    print("Checking recipes table and constraints...")

    # Get database service
    db_service = get_database_service()

    try:
        # Check foreign key constraints
        constraint_query = """
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name='user_recipes';
        """

        constraints = db_service.execute_query(constraint_query)
        if constraints:
            print("\nForeign key constraints on user_recipes:")
            for c in constraints:
                print(
                    f"  - {c['column_name']} -> {c['foreign_table_name']}.{c['foreign_column_name']}"
                )
                print(f"    Constraint name: {c['constraint_name']}")

        # Check recipes table structure
        recipes_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'recipes'
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """

        columns = db_service.execute_query(recipes_query)
        if columns:
            print("\n\nColumns in 'recipes' table:")
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")
        else:
            print("\n❌ 'recipes' table does not exist!")

        # Check sample data in recipes table
        sample_query = """
            SELECT recipe_id, recipe_name, cuisine_type
            FROM recipes
            LIMIT 5;
        """

        samples = db_service.execute_query(sample_query)
        if samples:
            print("\n\nSample recipes:")
            for s in samples:
                print(
                    f"  - ID: {s['recipe_id']}, Name: {s.get('recipe_name', 'N/A')}, Cuisine: {s.get('cuisine_type', 'N/A')}"
                )
        else:
            print("\nNo recipes found in recipes table")

    except Exception as e:
        print(f"❌ Error checking constraints: {e}")


if __name__ == "__main__":
    check_recipes_constraint()
