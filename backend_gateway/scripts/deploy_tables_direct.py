#!/usr/bin/env python3
"""
Deploy database tables directly using postgres credentials from .env
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables from the correct path
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
print(f"Loaded .env from: {env_path}")
print(f"POSTGRES_PASSWORD loaded: {'Yes' if os.getenv('POSTGRES_PASSWORD') else 'No'}")


def deploy_tables_direct():
    """Deploy tables using direct postgres connection"""

    # Get database connection info from .env
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")

    if not all([host, database, password]):
        print("❌ Missing required database configuration in .env file")
        print(f"   POSTGRES_HOST: {host}")
        print(f"   POSTGRES_DATABASE: {database}")
        print(f"   POSTGRES_PASSWORD: {'***' if password else 'MISSING'}")
        return

    print(f"Connecting to {host}:{port}/{database} as {user}...")

    try:
        # Connect directly with postgres credentials
        conn = psycopg2.connect(
            host=host, port=port, database=database, user=user, password=password, sslmode="require"
        )

        print("✅ Connected successfully!")

        # Check if units table exists
        print("\n📦 Checking units table...")
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'units'
            """
            )
            units_exists = cursor.fetchone()[0] > 0

        if units_exists:
            print("✅ Units table already exists")
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM units")
                count = cursor.fetchone()[0]
                print(f"   📊 {count} units available")
        else:
            print("   Deploying units table...")
            units_file = Path(__file__).parent / "units_table_complete.sql"
            if units_file.exists():
                with open(units_file, "r") as f:
                    units_sql = f.read()

                with conn.cursor() as cursor:
                    cursor.execute(units_sql)
                    conn.commit()
                print("✅ Units table deployed successfully!")

                # Check units count
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM units")
                    count = cursor.fetchone()[0]
                    print(f"   📊 {count} units inserted")
            else:
                print("❌ Units table SQL file not found")

        # Check if food categorization tables exist
        print("\n🍎 Checking food categorization tables...")
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'food_items_cache'
            """
            )
            food_exists = cursor.fetchone()[0] > 0

        if food_exists:
            print("✅ Food categorization tables already exist")
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM api_rate_limits")
                count = cursor.fetchone()[0]
                print(f"   📊 {count} API configurations available")
        else:
            print("   Deploying food categorization tables...")
            food_file = Path(__file__).parent / "create_food_categorization_tables.sql"
            if food_file.exists():
                with open(food_file, "r") as f:
                    food_sql = f.read()

                # Execute the entire SQL as one block (handles functions and triggers properly)
                with conn.cursor() as cursor:
                    print(f"  Executing food categorization schema...")
                    cursor.execute(food_sql)
                    conn.commit()
                print("✅ Food categorization tables deployed successfully!")

                # Check API rate limits
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM api_rate_limits")
                    count = cursor.fetchone()[0]
                    print(f"   📊 {count} API configurations inserted")
            else:
                print("❌ Food categorization SQL file not found")

        # List all tables to verify
        print(f"\n📋 Verifying tables...")
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
            )
            tables = cursor.fetchall()

            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")

        print(f"\n🎉 Database deployment completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Test: python backend_gateway/scripts/check_existing_tables.py")
        print(f"2. Test: python backend_gateway/scripts/check_food_database.py")
        print(f"3. Get USDA API key: https://fdc.nal.usda.gov/api-key-signup.html")

    except Exception as e:
        print(f"❌ Error during deployment: {str(e)}")
        print(f"Check your database credentials and network connectivity")
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    deploy_tables_direct()
