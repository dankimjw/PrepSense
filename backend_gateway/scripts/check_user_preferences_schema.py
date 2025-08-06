#!/usr/bin/env python3
"""
Check the user_preferences table schema
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def check_user_preferences():
    """Check user_preferences table structure"""
    print("Checking user_preferences table...")

    # Get database service
    db_service = get_database_service()

    try:
        # Check columns
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_preferences'
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """

        columns = db_service.execute_query(query)
        if columns:
            print("\nColumns in 'user_preferences' table:")
            for col in columns:
                print(
                    f"  - {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}"
                )
        else:
            print("\n❌ 'user_preferences' table does not exist!")

        # Check sample data
        sample_query = """
            SELECT * FROM user_preferences
            WHERE user_id = 111
            LIMIT 1;
        """

        sample = db_service.execute_query(sample_query)
        if sample:
            print(f"\nSample data for user 111:")
            for key, value in sample[0].items():
                print(f"  - {key}: {value}")
        else:
            print("\nNo preferences found for user 111")

    except Exception as e:
        print(f"❌ Error checking schema: {e}")


if __name__ == "__main__":
    check_user_preferences()
