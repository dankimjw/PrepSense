#!/usr/bin/env python3
"""
Deploy database tables using postgres superuser account
This temporarily switches from IAM auth to password auth for table creation
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def deploy_with_superuser():
    """Deploy tables using postgres superuser"""
    
    # Get database connection info
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DATABASE")
    
    # Ask user for postgres password
    import getpass
    postgres_password = getpass.getpass("Enter postgres superuser password: ")
    
    print(f"Connecting to {host}:{port}/{database} as postgres user...")
    
    try:
        # Connect as postgres superuser
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user="postgres",
            password=postgres_password,
            sslmode="require"
        )
        
        print("✅ Connected successfully!")
        
        # Deploy units table first
        print("\n📦 Deploying units table...")
        units_file = Path(__file__).parent / "units_table_complete.sql"
        if units_file.exists():
            with open(units_file, 'r') as f:
                units_sql = f.read()
            
            with conn.cursor() as cursor:
                cursor.execute(units_sql)
                conn.commit()
            print("✅ Units table deployed successfully!")
        else:
            print("❌ Units table SQL file not found")
        
        # Deploy food categorization tables
        print("\n🍎 Deploying food categorization tables...")
        food_file = Path(__file__).parent / "create_food_categorization_tables.sql"
        if food_file.exists():
            with open(food_file, 'r') as f:
                food_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in food_sql.split(';') if stmt.strip()]
            
            with conn.cursor() as cursor:
                for i, statement in enumerate(statements):
                    if statement:
                        print(f"  Executing statement {i+1}/{len(statements)}")
                        cursor.execute(statement)
                conn.commit()
            print("✅ Food categorization tables deployed successfully!")
        else:
            print("❌ Food categorization SQL file not found")
        
        # Grant permissions to IAM user
        print(f"\n🔐 Granting permissions to IAM user...")
        iam_user = os.getenv("POSTGRES_IAM_USER", "danielk7@uchicago.edu")
        
        grant_sql = f"""
        -- Grant permissions to IAM user
        GRANT CONNECT ON DATABASE {database} TO "{iam_user}";
        GRANT USAGE ON SCHEMA public TO "{iam_user}";
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{iam_user}";
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{iam_user}";
        
        -- Grant permissions on future tables
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{iam_user}";
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{iam_user}";
        """
        
        with conn.cursor() as cursor:
            cursor.execute(grant_sql)
            conn.commit()
        print(f"✅ Permissions granted to {iam_user}")
        
        # Verify deployment
        print(f"\n✅ Verifying deployment...")
        with conn.cursor() as cursor:
            # Check units table
            cursor.execute("SELECT COUNT(*) FROM units")
            units_count = cursor.fetchone()[0]
            print(f"  Units table: {units_count} records")
            
            # Check food tables
            food_tables = [
                'food_items_cache',
                'food_unit_mappings', 
                'food_categorization_corrections',
                'food_search_history',
                'food_aliases',
                'api_rate_limits'
            ]
            
            for table in food_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  {table}: {count} records")
                except Exception as e:
                    print(f"  {table}: ❌ {str(e)}")
        
        print(f"\n🎉 Database deployment completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Test the units table: python backend_gateway/scripts/check_existing_tables.py")
        print(f"2. Test food categorization: python backend_gateway/scripts/check_food_database.py")
        print(f"3. Get USDA API key from: https://fdc.nal.usda.gov/api-key-signup.html")
        
    except Exception as e:
        print(f"❌ Error during deployment: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    deploy_with_superuser()