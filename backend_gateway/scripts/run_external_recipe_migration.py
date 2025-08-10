#!/usr/bin/env python3
"""
Run migration to support external recipes in user_recipes table
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def run_migration():
    """Run the external recipe support migration"""
    print("Running external recipe support migration...")

    # Get database service
    db_service = get_database_service()

    try:
        # Read the SQL file
        sql_file = Path(__file__).parent / "add_external_recipe_support.sql"
        with open(sql_file) as f:
            sql_content = f.read()

        # Split into individual statements
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        for i, statement in enumerate(statements, 1):
            try:
                print(f"\nExecuting statement {i}...")
                print(f"{statement[:80]}..." if len(statement) > 80 else statement)
                db_service.execute_query(statement + ";")
                print(f"✅ Statement {i} executed successfully")
            except Exception as e:
                print(f"❌ Error executing statement {i}: {e}")
                # Continue with other statements

        # Verify the changes
        print("\n\nVerifying changes...")

        # Check columns
        columns_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_recipes'
            AND column_name IN ('is_external', 'external_source')
            ORDER BY ordinal_position;
        """

        columns = db_service.execute_query(columns_query)
        if columns:
            print("\nNew columns added:")
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")

        # Check constraints
        constraint_query = """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'user_recipes'
            AND constraint_type IN ('CHECK', 'FOREIGN KEY');
        """

        constraints = db_service.execute_query(constraint_query)
        if constraints:
            print("\nCurrent constraints:")
            for c in constraints:
                print(f"  - {c['constraint_name']} ({c['constraint_type']})")

        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Error running migration: {e}")


if __name__ == "__main__":
    run_migration()
