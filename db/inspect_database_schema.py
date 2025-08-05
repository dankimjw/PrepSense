#!/usr/bin/env python3
"""
Simple database schema inspector
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

def get_direct_connection():
    """Get direct database connection"""
    try:
        # Try to get connection parameters from environment
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        database = os.getenv("POSTGRES_DATABASE", "prepsense")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return None

def inspect_schema():
    """Inspect database schema"""
    conn = get_direct_connection()
    if not conn:
        print("❌ Could not connect to database")
        return False
        
    try:
        cur = conn.cursor()
        
        print("🔍 Inspecting Database Schema...")
        print("=" * 50)
        
        # List all tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = [row['table_name'] for row in cur.fetchall()]
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  • {table}")
        
        # Check specific USDA-related tables
        usda_tables = [t for t in tables if 'usda' in t.lower()]
        print(f"\n🍎 USDA-related tables ({len(usda_tables)}):")
        for table in usda_tables:
            print(f"  • {table}")
        
        # Inspect column structure for key tables
        key_tables = ['usda_foods', 'usda_food_categories', 'usda_measure_units']
        
        for table in key_tables:
            if table in tables:
                print(f"\n📊 Columns in {table}:")
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position
                """)
                
                columns = cur.fetchall()
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"  • {col['column_name']}: {col['data_type']} ({nullable})")
                    
                # Check row count
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cur.fetchone()['count']
                print(f"    Total rows: {count:,}")
            else:
                print(f"\n❌ Table {table} not found")
        
        # Check for functions
        print(f"\n🔧 Checking for custom functions...")
        cur.execute("""
            SELECT proname, prosrc
            FROM pg_proc 
            WHERE proname LIKE '%validate%' OR proname LIKE '%search%'
        """)
        functions = cur.fetchall()
        if functions:
            print(f"Found {len(functions)} relevant functions:")
            for func in functions:
                print(f"  • {func['proname']}")
        else:
            print("No custom validation/search functions found")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema inspection failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = inspect_schema()
    sys.exit(0 if success else 1)