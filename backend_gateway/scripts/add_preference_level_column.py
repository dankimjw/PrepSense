#!/usr/bin/env python3
"""Add missing preference_level column to user_cuisine_preferences table"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_gateway.config.database import DatabaseService


def add_preference_level_column():
    """Add the missing preference_level column"""
    db = DatabaseService()

    print("🔧 Adding preference_level column to user_cuisine_preferences table...")

    # First check if the column already exists
    check_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'user_cuisine_preferences'
        AND column_name = 'preference_level'
    """

    result = db.execute_query(check_query)

    if result:
        print("✓ Column 'preference_level' already exists")
        return

    # Add the column if it doesn't exist
    alter_query = """
        ALTER TABLE user_cuisine_preferences
        ADD COLUMN preference_level INTEGER DEFAULT 1
    """

    try:
        db.execute_query(alter_query)
        print("✅ Successfully added preference_level column")

        # Add a comment to explain the column
        comment_query = """
            COMMENT ON COLUMN user_cuisine_preferences.preference_level IS
            'Preference level: positive values = liked, negative = disliked, 0 = neutral'
        """
        db.execute_query(comment_query)
        print("✅ Added column comment")

        # Show current table structure
        print("\n📊 Current table structure:")
        structure_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'user_cuisine_preferences'
            ORDER BY ordinal_position
        """

        columns = db.execute_query(structure_query)
        for col in columns:
            print(
                f"   - {col['column_name']}: {col['data_type']} "
                f"(nullable: {col['is_nullable']}, default: {col['column_default']})"
            )

        # Check sample data
        print("\n📊 Sample data:")
        sample_query = """
            SELECT * FROM user_cuisine_preferences
            LIMIT 5
        """

        samples = db.execute_query(sample_query)
        if samples:
            for row in samples:
                print(
                    f"   User {row['user_id']}: {row['cuisine']} "
                    f"(preference: {row.get('preference_level', 'N/A')})"
                )
        else:
            print("   No data in table yet")

    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False

    return True


if __name__ == "__main__":
    add_preference_level_column()
