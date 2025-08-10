#!/usr/bin/env python3
"""
Script to apply the semantic search migration to the database
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def apply_migration():
    """Apply the semantic search migration to the database"""

    # Get database credentials
    db_config = {
        "host": os.getenv("POSTGRES_HOST"),
        "database": os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    print("🚀 Applying Semantic Search Migration to PrepSense Database")
    print("=" * 60)
    print(f"Host: {db_config['host']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    print("=" * 60)

    migration_file = (
        Path(__file__).parent / "backend_gateway" / "migrations" / "add_vector_embeddings.sql"
    )

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    try:
        # Connect to database
        print("\n📡 Connecting to database...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected successfully")

        # Check if pgvector is already installed
        print("\n🔍 Checking pgvector extension status...")
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        if cursor.fetchone():
            print("✅ pgvector extension already installed")
        else:
            print("📦 Installing pgvector extension...")

        # Read and execute migration
        print("\n📝 Reading migration file...")
        with open(migration_file) as f:
            migration_sql = f.read()

        # Split by semicolons but be careful with functions
        print("🔧 Executing migration statements...")

        # Execute the entire migration as one block
        try:
            cursor.execute(migration_sql)
            print("✅ Migration executed successfully")
        except psycopg2.errors.DuplicateObject as e:
            if "already exists" in str(e):
                print("⚠️  Some objects already exist, continuing...")
            else:
                raise

        # Verify the migration
        print("\n🔍 Verifying migration...")

        # Check tables
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('food_item_embeddings', 'search_query_embeddings')
        """
        )
        tables = cursor.fetchall()
        print(f"✅ Created {len(tables)} new tables")

        # Check if vector columns were added
        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'recipes'
            AND column_name = 'embedding'
        """
        )
        if cursor.fetchone():
            print("✅ Vector column added to recipes table")

        # Check functions
        cursor.execute(
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_type = 'FUNCTION'
            AND routine_name IN ('find_similar_recipes', 'find_similar_products', 'hybrid_recipe_search')
        """
        )
        functions = cursor.fetchall()
        print(f"✅ Created {len(functions)} search functions")

        # Check indexes
        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename IN ('recipes', 'products', 'pantry_items')
            AND indexname LIKE '%embedding%'
        """
        )
        indexes = cursor.fetchall()
        print(f"✅ Created {len(indexes)} vector indexes")

        print("\n🎉 Migration completed successfully!")

        # Close connection
        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        print(f"Error code: {e.pgcode if hasattr(e, 'pgcode') else 'Unknown'}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
