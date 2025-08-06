#!/usr/bin/env python3
"""
Update user preferences to include household_size in the preferences JSON
"""

import json
import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
load_dotenv(os.path.join(parent_dir, ".env"))

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def update_preferences(user_id=111):
    """Update preferences to include household_size in JSON"""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # First, get current preferences
        cur.execute(
            """
            SELECT preference_id, household_size, preferences 
            FROM user_preferences 
            WHERE user_id = %s
        """,
            (user_id,),
        )

        result = cur.fetchone()

        if result:
            current_prefs = result["preferences"] or {}
            household_size = result["household_size"] or 2

            # Add household_size to preferences JSON
            current_prefs["household_size"] = household_size

            # Update the preferences
            cur.execute(
                """
                UPDATE user_preferences 
                SET preferences = %s
                WHERE user_id = %s
            """,
                (Json(current_prefs), user_id),
            )

            conn.commit()

            print(f"✅ Updated preferences for user {user_id}")
            print(f"   Household size: {household_size}")
            print(f"   Updated preferences: {json.dumps(current_prefs, indent=2)}")

        else:
            print(f"❌ No preferences found for user {user_id}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating preferences: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 111
    print(f"Updating preferences for user ID: {user_id}")
    update_preferences(user_id)
