#!/usr/bin/env python3
"""
Check the existing database schema
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service

def check_schema():
    """Check existing tables and columns"""
    print("Checking PostgreSQL schema...")
    
    # Get database service
    db_service = get_database_service()
    
    try:
        # Check what tables exist
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        
        tables = db_service.execute_query(tables_query)
        print("\nExisting tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check if users table exists and its columns
        users_check = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """
        
        columns = db_service.execute_query(users_check)
        if columns:
            print("\nColumns in 'users' table:")
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        else:
            print("\n❌ 'users' table does not exist!")
            
        # Check user_preference table
        pref_check = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_preference'
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """
        
        pref_columns = db_service.execute_query(pref_check)
        if pref_columns:
            print("\nColumns in 'user_preference' table:")
            for col in pref_columns:
                print(f"  - {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        else:
            print("\n❌ 'user_preference' table does not exist!")
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        raise

if __name__ == "__main__":
    check_schema()