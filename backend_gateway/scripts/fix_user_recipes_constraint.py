#!/usr/bin/env python3
"""
Fix the user_recipes foreign key constraint to allow external recipes
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def fix_constraint():
    """Remove or modify the foreign key constraint"""
    print("Fixing user_recipes constraint...")

    # Get database service
    db_service = get_database_service()

    try:
        # First, check the constraint name
        get_constraint = """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'user_recipes'
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%recipe_id%';
        """

        constraints = db_service.execute_query(get_constraint)
        if constraints:
            for constraint in constraints:
                constraint_name = constraint["constraint_name"]
                print(f"Found constraint: {constraint_name}")

                # Drop the foreign key constraint
                drop_query = f"""
                    ALTER TABLE user_recipes
                    DROP CONSTRAINT IF EXISTS {constraint_name};
                """

                try:
                    db_service.execute_query(drop_query)
                    print(f"✅ Dropped constraint: {constraint_name}")
                except Exception as e:
                    print(f"Error dropping constraint: {e}")

            # Verify it's gone
            verify = db_service.execute_query(get_constraint)
            if not verify:
                print("✅ Constraint successfully removed!")
            else:
                print("❌ Constraint still exists")
        else:
            print("No recipe_id foreign key constraint found")

    except Exception as e:
        print(f"❌ Error fixing constraint: {e}")


if __name__ == "__main__":
    fix_constraint()
