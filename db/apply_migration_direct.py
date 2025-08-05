#!/usr/bin/env python3
"""
Direct migration application script
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply migration directly"""
    try:
        # Connect to database
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        database = os.getenv("POSTGRES_DATABASE", "prepsense")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        conn = psycopg2.connect(
            host=host, port=port, database=database,
            user=user, password=password
        )
        
        print("✅ Connected to database")
        
        # Read migration file
        migration_file = "db/migrations/001_fix_usda_critical_issues.sql"
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"📄 Loaded migration from {migration_file}")
        
        # Execute migration
        cur = conn.cursor()
        cur.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration applied successfully")
        
        # Verify key tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('usda_food_portions', 'usda_food_nutrients', 'product_aliases')
        """)
        
        created_tables = [row[0] for row in cur.fetchall()]
        print(f"📋 Created tables: {created_tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)