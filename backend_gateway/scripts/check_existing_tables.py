#!/usr/bin/env python3
"""
Check existing tables in the GCP Cloud SQL database
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import from backend_gateway
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend_gateway.config.database import get_database_service

def check_existing_tables():
    """Check what tables already exist in the database"""
    
    # Get the database service
    db_service = get_database_service()
    
    try:
        print("Checking existing tables...")
        
        # Check all tables
        tables = db_service.execute_query("""
            SELECT tablename, schemaname
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['tablename']}")
        
        # Check specifically for units table
        units_check = db_service.execute_query("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'units'
        """)
        
        units_exists = units_check[0]['count'] > 0 if units_check else False
        print(f"\nUnits table exists: {units_exists}")
        
        if units_exists:
            # Check units table content
            units_count = db_service.execute_query("SELECT COUNT(*) FROM units")
            count = units_count[0]['count'] if units_count else 0
            print(f"Units table has {count} records")
            
            # Show some sample units
            if count > 0:
                sample_units = db_service.execute_query("SELECT id, label, category FROM units LIMIT 10")
                print("\nSample units:")
                for unit in sample_units:
                    print(f"  - {unit['id']}: {unit['label']} ({unit['category']})")
        
        print("\n✅ Table check completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error checking tables: {str(e)}")
        raise
    finally:
        db_service.close()

if __name__ == "__main__":
    check_existing_tables()