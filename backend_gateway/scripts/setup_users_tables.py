#!/usr/bin/env python3
"""
Setup users and user_preference tables in PostgreSQL
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service


def setup_users_tables():
    """Create users and user_preference tables"""
    print("Setting up users tables in PostgreSQL...")

    # Get database service
    db_service = get_database_service()

    # Read SQL file
    sql_file = Path(__file__).parent / "create_users_table.sql"
    with open(sql_file, "r") as f:
        sql_content = f.read()

    # Execute SQL statements
    try:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        for statement in statements:
            if statement:
                print(f"Executing: {statement[:50]}...")
                db_service.execute_query(statement)

        print("✅ Users tables created successfully!")

        # Verify tables exist
        check_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'user_preference')
            ORDER BY table_name;
        """

        tables = db_service.execute_query(check_query)
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table['table_name']}")

    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        raise


if __name__ == "__main__":
    setup_users_tables()
