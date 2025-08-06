#!/usr/bin/env python3
"""
Analyze pantry_history and user_preferences tables
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables from the main .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Add the backend_gateway to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

from backend_gateway.core.config import settings
from backend_gateway.services.postgres_service import PostgresService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_pantry_history(postgres_service: PostgresService):
    """Analyze the pantry_history table"""
    print("=== PANTRY_HISTORY ANALYSIS ===")
    print()

    # 1. Operations being tracked
    query = """
        SELECT operation, COUNT(*) as count 
        FROM pantry_history 
        GROUP BY operation 
        ORDER BY count DESC
    """
    results = postgres_service.execute_query(query)
    print("Operations tracked:")
    for row in results:
        print(f"  {row['operation']}: {row['count']} records")
    print()

    # 2. Unique pantry items
    query = "SELECT COUNT(DISTINCT pantry_item_id) as unique_items FROM pantry_history"
    result = postgres_service.execute_query(query, fetch="one")
    print(f"Unique pantry items tracked: {result['unique_items']}")
    print()

    # 3. Date range
    query = """
        SELECT 
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest,
            COUNT(*) as total_records
        FROM pantry_history
    """
    result = postgres_service.execute_query(query, fetch="one")
    print(f"Date range: {result['earliest']} to {result['latest']}")
    print(f"Total records: {result['total_records']}")
    print()

    # 4. Average records per pantry item
    query = """
        SELECT AVG(record_count) as avg_records_per_item
        FROM (
            SELECT pantry_item_id, COUNT(*) as record_count
            FROM pantry_history
            GROUP BY pantry_item_id
        ) as item_counts
    """
    result = postgres_service.execute_query(query, fetch="one")
    avg_records = float(result["avg_records_per_item"])
    print(f"Average history records per pantry item: {avg_records:.2f}")
    print()

    # 5. Sample recent entries
    query = """
        SELECT 
            ph.operation,
            ph.timestamp,
            ph.details,
            pi.name as item_name,
            ph.pantry_item_id
        FROM pantry_history ph
        LEFT JOIN pantry_items pi ON ph.pantry_item_id = pi.id
        ORDER BY ph.timestamp DESC
        LIMIT 10
    """
    results = postgres_service.execute_query(query)
    print("Recent history entries (last 10):")
    for row in results:
        details = json.loads(row["details"]) if row["details"] else {}
        print(
            f"  [{row['timestamp']}] {row['operation']} - {row['item_name'] or 'Unknown'} (ID: {row['pantry_item_id']})"
        )
        if details:
            print(f"    Details: {json.dumps(details, indent=6)}")
    print()

    # Additional analysis: Operations by pantry item
    query = """
        SELECT 
            pi.name as item_name,
            ph.pantry_item_id,
            COUNT(*) as history_count,
            STRING_AGG(DISTINCT ph.operation, ', ' ORDER BY ph.operation) as operations
        FROM pantry_history ph
        LEFT JOIN pantry_items pi ON ph.pantry_item_id = pi.id
        GROUP BY ph.pantry_item_id, pi.name
        ORDER BY history_count DESC
        LIMIT 10
    """
    results = postgres_service.execute_query(query)
    print("Top 10 pantry items by history count:")
    for row in results:
        print(
            f"  {row['item_name'] or 'Unknown'} (ID: {row['pantry_item_id']}): {row['history_count']} records"
        )
        print(f"    Operations: {row['operations']}")
    print()


def analyze_user_preferences(postgres_service: PostgresService):
    """Analyze the user_preferences table"""
    print("=== USER_PREFERENCES ANALYSIS ===")
    print()

    # 1. Check total users vs preferences
    query = "SELECT COUNT(*) as total_users FROM users"
    result = postgres_service.execute_query(query, fetch="one")
    total_users = result["total_users"]
    print(f"Total users in system: {total_users}")

    query = "SELECT COUNT(*) as total_prefs FROM user_preferences"
    result = postgres_service.execute_query(query, fetch="one")
    total_prefs = result["total_prefs"]
    print(f"Total user preferences records: {total_prefs}")
    print()

    # 2. Which users have preferences
    query = """
        SELECT 
            up.user_id,
            u.username,
            up.preference_type,
            up.preference_value,
            up.created_at
        FROM user_preferences up
        JOIN users u ON up.user_id = u.id
        ORDER BY up.user_id
    """
    results = postgres_service.execute_query(query)
    print("Users with preferences:")
    if results:
        for row in results:
            print(
                f"  User {row['user_id']} ({row['username']}): {row['preference_type']} = {row['preference_value']}"
            )
            print(f"    Created: {row['created_at']}")
    else:
        print("  No user preferences found")
    print()

    # 3. Users without preferences
    query = """
        SELECT u.id, u.username, u.created_at
        FROM users u
        LEFT JOIN user_preferences up ON u.id = up.user_id
        WHERE up.user_id IS NULL
        ORDER BY u.id
    """
    results = postgres_service.execute_query(query)
    print("Users WITHOUT preferences:")
    if results:
        for row in results:
            print(f"  User {row['id']} ({row['username']}) - created {row['created_at']}")
    else:
        print("  All users have preferences")
    print()

    # 4. Check preference table structure
    query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'user_preferences'
        ORDER BY ordinal_position
    """
    results = postgres_service.execute_query(query)
    print("User preferences table structure:")
    for row in results:
        nullable = "NULL" if row["is_nullable"] == "YES" else "NOT NULL"
        default = f" DEFAULT {row['column_default']}" if row["column_default"] else ""
        print(f"  {row['column_name']}: {row['data_type']} {nullable}{default}")
    print()

    # 5. Check if there are any unique constraints
    query = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_name = 'user_preferences'
        GROUP BY tc.constraint_name, tc.constraint_type
    """
    results = postgres_service.execute_query(query)
    if results:
        print("Constraints on user_preferences:")
        for row in results:
            print(f"  {row['constraint_name']} ({row['constraint_type']}): {row['columns']}")
    print()


def main():
    """Main function"""
    try:
        # Initialize PostgreSQL service
        postgres_service = PostgresService(
            {
                "host": settings.POSTGRES_HOST,
                "port": settings.POSTGRES_PORT,
                "database": settings.POSTGRES_DATABASE,
                "user": settings.POSTGRES_USER,
                "password": settings.POSTGRES_PASSWORD,
            }
        )

        # Analyze pantry_history
        analyze_pantry_history(postgres_service)

        print("\n" + "=" * 60 + "\n")

        # Analyze user_preferences
        analyze_user_preferences(postgres_service)

    except Exception as e:
        logger.error(f"Error analyzing database: {e}")
        raise


if __name__ == "__main__":
    main()
