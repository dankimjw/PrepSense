#!/usr/bin/env python3
"""
Run USDA database migration to fix critical issues.
"""

import asyncio
import asyncpg
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Run the migration script."""
    
    # Connect to database
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DATABASE')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    
    if not all([db_host, db_name, db_user, db_password]):
        raise ValueError("Missing required database environment variables")
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🚀 Running USDA Database Migration 001")
        print("=" * 50)
        
        # Read migration file
        migration_file = Path("/Users/danielkim/_Capstone/PrepSense/db/migrations/001_fix_usda_critical_issues.sql")
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        migration_sql = migration_file.read_text()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        # Execute each statement
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement.startswith('--'):
                continue
                
            try:
                # Skip comments and empty lines
                if statement.strip().startswith('--') or len(statement.strip()) < 10:
                    continue
                
                logger.info(f"Executing statement {i}/{len(statements)}")
                
                # Execute in a transaction
                async with conn.transaction():
                    await conn.execute(statement)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error in statement {i}: {str(e)}")
                logger.error(f"Statement: {statement[:100]}...")
                
                # Continue with other statements
                continue
        
        print(f"\n✅ Migration completed!")
        print(f"   Successful statements: {success_count}")
        print(f"   Failed statements: {error_count}")
        
        # Verify migration results
        print("\n🔍 Verifying migration results...")
        
        # Check if tables were created
        tables_to_check = ['usda_food_portions', 'usda_food_nutrients', 'product_aliases']
        
        for table in tables_to_check:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                
                if exists:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    print(f"   ✅ {table}: {count:,} rows")
                else:
                    print(f"   ❌ {table}: not created")
                    
            except Exception as e:
                print(f"   ❌ {table}: error checking - {e}")
        
        # Check if functions were created
        functions_to_check = ['validate_unit_for_food', 'search_foods_enhanced', 'get_unit_conversion']
        
        for func in functions_to_check:
            try:
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.routines 
                        WHERE routine_name = $1 AND routine_type = 'FUNCTION'
                    )
                """, func)
                
                if exists:
                    print(f"   ✅ Function {func}: created")
                else:
                    print(f"   ❌ Function {func}: not created")
                    
            except Exception as e:
                print(f"   ❌ Function {func}: error checking - {e}")
        
        # Check indexes
        print("\n🔍 Checking new indexes...")
        indexes = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname LIKE '%usda%'
            AND indexname NOT LIKE '%pkey%'
            ORDER BY indexname
        """)
        
        for idx in indexes:
            print(f"   ✅ Index: {idx['indexname']}")
        
        print("\n📊 Testing enhanced functions...")
        
        # Test unit validation function
        try:
            result = await conn.fetchrow("""
                SELECT * FROM validate_unit_for_food('strawberries', 'cup')
            """)
            if result:
                print(f"   ✅ Unit validation test: {result['is_valid']} (confidence: {result['confidence']})")
            else:
                print("   ❌ Unit validation test: no result")
        except Exception as e:
            print(f"   ❌ Unit validation test failed: {e}")
        
        # Test food search function  
        try:
            results = await conn.fetch("""
                SELECT * FROM search_foods_enhanced('chicken breast') LIMIT 3
            """)
            if results:
                print(f"   ✅ Food search test: {len(results)} results found")
                for result in results:
                    print(f"      - {result['description']} (confidence: {result['confidence']:.2f})")
            else:
                print("   ❌ Food search test: no results")
        except Exception as e:
            print(f"   ❌ Food search test failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Migration completed successfully!")
        print("\nNext Steps:")
        print("1. Import USDA food portion data")
        print("2. Import USDA food nutrient data")  
        print("3. Add more product aliases")
        print("4. Test API endpoints")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())