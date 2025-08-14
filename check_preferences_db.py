#!/usr/bin/env python3
"""Check user preferences in the database."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend_gateway.services.database_service import get_database_service
import json

def check_preferences():
    """Check preferences for user 111 in the database."""
    try:
        db = get_database_service()
        query = "SELECT * FROM user_preferences WHERE user_id = %(user_id)s"
        params = {"user_id": 111}
        result = db.execute_query(query, params)
        
        if result:
            row = result[0]
            print("✅ User preferences found in database:")
            print(f"  user_id: {row['user_id']}")
            print(f"  household_size: {row['household_size']}")
            print(f"  updated_at: {row['updated_at']}")
            print(f"  preferences: {json.dumps(row['preferences'], indent=4)}")
        else:
            print("❌ No preferences found for user 111 in database")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_preferences()
