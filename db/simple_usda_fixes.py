#!/usr/bin/env python3
"""
Simple USDA database fixes - Execute critical improvements step by step.
"""

import asyncio
import asyncpg
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_usda_fixes():
    """Apply critical USDA database fixes."""
    
    # Connect to database
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DATABASE')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = await asyncpg.connect(db_url)
    
    try:
        print("🔧 Applying Critical USDA Database Fixes")
        print("=" * 50)
        
        # 1. Create missing tables
        print("\n1️⃣ Creating missing tables...")
        
        # Enable trigram extension
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            print("   ✅ pg_trgm extension enabled")
        except Exception as e:
            print(f"   ⚠️ pg_trgm extension: {e}")
        
        # Create usda_food_portions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usda_food_portions (
                id SERIAL PRIMARY KEY,
                fdc_id INTEGER NOT NULL,
                seq_num INTEGER,
                amount DECIMAL(10,3),
                measure_unit_id INTEGER,
                portion_description VARCHAR(255),
                modifier VARCHAR(255),
                gram_weight DECIMAL(10,3),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (fdc_id) REFERENCES usda_foods(fdc_id) ON DELETE CASCADE,
                FOREIGN KEY (measure_unit_id) REFERENCES usda_measure_units(id)
            );
        """)
        print("   ✅ usda_food_portions table created")
        
        # Create usda_food_nutrients table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usda_food_nutrients (
                id SERIAL PRIMARY KEY,
                fdc_id INTEGER NOT NULL,
                nutrient_id INTEGER NOT NULL,
                amount DECIMAL(15,5),
                data_points INTEGER,
                derivation_id INTEGER,
                min_amount DECIMAL(15,5),
                max_amount DECIMAL(15,5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (fdc_id) REFERENCES usda_foods(fdc_id) ON DELETE CASCADE,
                FOREIGN KEY (nutrient_id) REFERENCES usda_nutrients(id),
                UNIQUE(fdc_id, nutrient_id)
            );
        """)
        print("   ✅ usda_food_nutrients table created")
        
        # Create product_aliases table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_aliases (
                id SERIAL PRIMARY KEY,
                pantry_name VARCHAR(255) NOT NULL,
                usda_fdc_id INTEGER NOT NULL,
                confidence_score DECIMAL(3,2) DEFAULT 1.00,
                match_type VARCHAR(50) DEFAULT 'manual',
                created_by VARCHAR(50) DEFAULT 'system',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (usda_fdc_id) REFERENCES usda_foods(fdc_id) ON DELETE CASCADE,
                UNIQUE(pantry_name)
            );
        """)
        print("   ✅ product_aliases table created")
        
        # 2. Add performance indexes
        print("\n2️⃣ Adding performance indexes...")
        
        indexes = [
            ("idx_usda_category_unit_perf", "usda_category_unit_mappings", "(category_id, usage_percentage DESC, is_preferred)"),
            ("idx_usda_foods_description_trgm", "usda_foods", "USING GIN (description gin_trgm_ops)"),
            ("idx_usda_food_portions_fdc", "usda_food_portions", "(fdc_id)"),
            ("idx_usda_food_portions_unit", "usda_food_portions", "(measure_unit_id)"),
            ("idx_usda_food_nutrients_fdc", "usda_food_nutrients", "(fdc_id)"),
            ("idx_usda_food_nutrients_nutrient", "usda_food_nutrients", "(nutrient_id)"),
            ("idx_product_aliases_pantry_name", "product_aliases", "(pantry_name)"),
            ("idx_product_aliases_fdc", "product_aliases", "(usda_fdc_id)")
        ]
        
        for index_name, table_name, columns in indexes:
            try:
                await conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} {columns};")
                print(f"   ✅ {index_name}")
            except Exception as e:
                print(f"   ❌ {index_name}: {e}")
        
        # 3. Add sample product aliases
        print("\n3️⃣ Adding sample product aliases...")
        
        # First, find some FDC IDs for common products
        sample_aliases = []
        
        # Try to find olive oil
        olive_oil_fdc = await conn.fetchval("""
            SELECT fdc_id FROM usda_foods 
            WHERE description ILIKE '%olive oil%' 
            AND description ILIKE '%extra virgin%' 
            LIMIT 1
        """)
        if olive_oil_fdc:
            sample_aliases.append(('colavita extra virgin olive oil', olive_oil_fdc, 0.90, 'brand'))
        
        # Try to find chicken broth
        broth_fdc = await conn.fetchval("""
            SELECT fdc_id FROM usda_foods 
            WHERE description ILIKE '%chicken broth%' 
            LIMIT 1
        """)
        if broth_fdc:
            sample_aliases.append(('pacific organic low sodium chicken broth', broth_fdc, 0.85, 'brand'))
        
        # Insert aliases
        for pantry_name, fdc_id, confidence, match_type in sample_aliases:
            await conn.execute("""
                INSERT INTO product_aliases (pantry_name, usda_fdc_id, confidence_score, match_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (pantry_name) DO NOTHING
            """, pantry_name, fdc_id, confidence, match_type)
            print(f"   ✅ Added alias: {pantry_name}")
        
        # 4. Update unit validation function
        print("\n4️⃣ Updating unit validation function...")
        
        await conn.execute("""
            CREATE OR REPLACE FUNCTION validate_unit_for_food_enhanced(
                p_food_name TEXT,
                p_unit_name TEXT,
                p_category_id INTEGER DEFAULT NULL
            ) RETURNS TABLE (
                is_valid BOOLEAN,
                confidence DECIMAL,
                suggested_units TEXT[],
                reason TEXT,
                fdc_id INTEGER,
                category_name TEXT
            ) AS $$
            DECLARE
                v_category_id INTEGER;
                v_unit_id INTEGER;
                v_usage_percentage DECIMAL;
                v_preferred_units TEXT[];
                v_fdc_id INTEGER;
                v_category_name TEXT;
            BEGIN
                -- Try to find food through product aliases first
                SELECT pa.usda_fdc_id INTO v_fdc_id
                FROM product_aliases pa
                WHERE LOWER(pa.pantry_name) = LOWER(p_food_name)
                LIMIT 1;
                
                -- If not found in aliases, try direct USDA search
                IF v_fdc_id IS NULL THEN
                    SELECT uf.fdc_id INTO v_fdc_id
                    FROM usda_foods uf
                    WHERE uf.description ILIKE '%' || p_food_name || '%'
                    LIMIT 1;
                END IF;
                
                -- Get category from found food or use provided category
                IF p_category_id IS NULL AND v_fdc_id IS NOT NULL THEN
                    SELECT uf.food_category_id, fc.description 
                    INTO v_category_id, v_category_name
                    FROM usda_foods uf
                    LEFT JOIN usda_food_categories fc ON uf.food_category_id = fc.id
                    WHERE uf.fdc_id = v_fdc_id;
                ELSE
                    v_category_id := p_category_id;
                    SELECT description INTO v_category_name
                    FROM usda_food_categories
                    WHERE id = v_category_id;
                END IF;
                
                -- Get unit ID with flexible matching
                SELECT id INTO v_unit_id
                FROM usda_measure_units
                WHERE LOWER(name) = LOWER(p_unit_name)
                   OR LOWER(abbreviation) = LOWER(p_unit_name)
                LIMIT 1;
                
                -- Check if unit is valid for category
                IF v_category_id IS NOT NULL AND v_unit_id IS NOT NULL THEN
                    SELECT usage_percentage INTO v_usage_percentage
                    FROM usda_category_unit_mappings
                    WHERE category_id = v_category_id AND unit_id = v_unit_id;
                    
                    -- Get preferred units for this category
                    SELECT ARRAY_AGG(um.name ORDER BY ucm.usage_percentage DESC)
                    INTO v_preferred_units
                    FROM usda_category_unit_mappings ucm
                    JOIN usda_measure_units um ON ucm.unit_id = um.id
                    WHERE ucm.category_id = v_category_id 
                    AND ucm.is_preferred = TRUE;
                    
                    IF v_usage_percentage IS NOT NULL THEN
                        RETURN QUERY SELECT 
                            TRUE,
                            LEAST(v_usage_percentage / 100.0, 0.99)::DECIMAL,
                            COALESCE(v_preferred_units, ARRAY['each', 'lb', 'oz']::TEXT[]),
                            'Unit is used in ' || v_usage_percentage || '% of similar foods',
                            v_fdc_id,
                            v_category_name;
                    ELSE
                        RETURN QUERY SELECT 
                            FALSE,
                            0.2::DECIMAL,
                            COALESCE(v_preferred_units, ARRAY['each', 'lb', 'oz']::TEXT[]),
                            'Unit not commonly used for this food category',
                            v_fdc_id,
                            v_category_name;
                    END IF;
                ELSE
                    -- Fallback suggestions
                    RETURN QUERY SELECT 
                        FALSE,
                        0.1::DECIMAL,
                        ARRAY['each', 'lb', 'oz', 'cup']::TEXT[],
                        'Food not found or category/unit not recognized',
                        v_fdc_id,
                        v_category_name;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("   ✅ Enhanced unit validation function created")
        
        # 5. Test the fixes
        print("\n5️⃣ Testing the fixes...")
        
        # Test enhanced function
        result = await conn.fetchrow("""
            SELECT * FROM validate_unit_for_food_enhanced('strawberries', 'cup')
        """)
        if result:
            print(f"   ✅ Enhanced validation test: {result['is_valid']} (confidence: {result['confidence']})")
        
        # Test alias matching
        if olive_oil_fdc:
            result = await conn.fetchrow("""
                SELECT * FROM validate_unit_for_food_enhanced('colavita extra virgin olive oil', 'ml')
            """)
            if result:
                print(f"   ✅ Alias matching test: found FDC {result['fdc_id']}")
        
        # Test performance
        import time
        start_time = time.time() 
        
        await conn.fetch("""
            SELECT um.name, ucm.usage_percentage
            FROM usda_category_unit_mappings ucm
            JOIN usda_measure_units um ON ucm.unit_id = um.id
            WHERE ucm.category_id = 1
            ORDER BY ucm.usage_percentage DESC
        """)
        
        query_time = (time.time() - start_time) * 1000
        print(f"   ✅ Category lookup performance: {query_time:.2f}ms")
        
        # 6. Show summary
        print("\n📊 SUMMARY")
        print("-" * 30)
        
        # Check table row counts
        for table in ['usda_food_portions', 'usda_food_nutrients', 'product_aliases']:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"   {table}: {count:,} rows")
        
        # Check function exists
        func_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.routines 
                WHERE routine_name = 'validate_unit_for_food_enhanced'
            )
        """)
        print(f"   Enhanced validation function: {'✅' if func_exists else '❌'}")
        
        # Show coverage improvement needed
        pantry_items = await conn.fetchval("SELECT COUNT(DISTINCT product_name) FROM pantry_items WHERE product_name IS NOT NULL")
        aliases = await conn.fetchval("SELECT COUNT(*) FROM product_aliases")
        
        print(f"\n🎯 Next Steps:")
        print(f"   • Import USDA food portion data (0 rows currently)")
        print(f"   • Import USDA food nutrient data (0 rows currently)")
        print(f"   • Add more product aliases ({aliases} of ~{pantry_items} pantry items)")
        print(f"   • Test API endpoints with new functions")
        
        print("\n" + "=" * 50)
        print("✅ Critical fixes applied successfully!")
        
    except Exception as e:
        logger.error(f"Error applying fixes: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(apply_usda_fixes())