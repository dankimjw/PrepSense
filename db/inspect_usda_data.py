#!/usr/bin/env python3
"""
Inspect existing USDA data in the database to understand current state.
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


async def inspect_usda_data():
    """Inspect what USDA data currently exists."""
    
    # Connect to database
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DATABASE')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = await asyncpg.connect(db_url)
    
    try:
        print("="*80)
        print("🔍 USDA DATA INSPECTION")
        print("="*80)
        
        # Check usda_foods table
        print("\n📊 USDA Foods Table:")
        foods_count = await conn.fetchval("SELECT COUNT(*) FROM usda_foods")
        print(f"  Total foods: {foods_count:,}")
        
        if foods_count > 0:
            sample_foods = await conn.fetch("""
                SELECT fdc_id, description, data_type, brand_owner, brand_name
                FROM usda_foods 
                ORDER BY fdc_id
                LIMIT 5
            """)
            print("  Sample records:")
            for food in sample_foods:
                brand_info = f" ({food['brand_owner']})" if food['brand_owner'] else ""
                print(f"    {food['fdc_id']}: {food['description']}{brand_info} [{food['data_type']}]")
        
        # Check usda_food_categories table
        print("\n📊 USDA Food Categories Table:")
        categories_count = await conn.fetchval("SELECT COUNT(*) FROM usda_food_categories")
        print(f"  Total categories: {categories_count}")
        
        if categories_count > 0:
            sample_categories = await conn.fetch("""
                SELECT id, description 
                FROM usda_food_categories 
                ORDER BY id 
                LIMIT 10
            """)
            print("  Sample categories:")
            for cat in sample_categories:
                print(f"    {cat['id']}: {cat['description']}")
        
        # Check usda_measure_units table
        print("\n📊 USDA Measure Units Table:")
        units_count = await conn.fetchval("SELECT COUNT(*) FROM usda_measure_units")
        print(f"  Total units: {units_count}")
        
        if units_count > 0:
            sample_units = await conn.fetch("""
                SELECT id, name, abbreviation, unit_type 
                FROM usda_measure_units 
                ORDER BY id 
                LIMIT 10
            """)
            print("  Sample units:")
            for unit in sample_units:
                abbrev = f" ({unit['abbreviation']})" if unit['abbreviation'] else ""
                unit_type = f" [{unit['unit_type']}]" if unit['unit_type'] else ""
                print(f"    {unit['id']}: {unit['name']}{abbrev}{unit_type}")
        
        # Check usda_nutrients table
        print("\n📊 USDA Nutrients Table:")
        nutrients_count = await conn.fetchval("SELECT COUNT(*) FROM usda_nutrients")
        print(f"  Total nutrients: {nutrients_count}")
        
        if nutrients_count > 0:
            sample_nutrients = await conn.fetch("""
                SELECT id, name, unit_name 
                FROM usda_nutrients 
                ORDER BY id 
                LIMIT 10
            """)
            print("  Sample nutrients:")
            for nutrient in sample_nutrients:
                unit = f" ({nutrient['unit_name']})" if nutrient['unit_name'] else ""
                print(f"    {nutrient['id']}: {nutrient['name']}{unit}")
        
        # Check usda_category_unit_mappings table
        print("\n📊 USDA Category Unit Mappings Table:")
        mappings_count = await conn.fetchval("SELECT COUNT(*) FROM usda_category_unit_mappings")
        print(f"  Total mappings: {mappings_count}")
        
        if mappings_count > 0:
            sample_mappings = await conn.fetch("""
                SELECT 
                    ucm.category_id,
                    fc.description as category_name,
                    ucm.unit_id,
                    um.name as unit_name,
                    ucm.usage_percentage,
                    ucm.is_preferred
                FROM usda_category_unit_mappings ucm
                JOIN usda_food_categories fc ON ucm.category_id = fc.id
                JOIN usda_measure_units um ON ucm.unit_id = um.id
                ORDER BY ucm.category_id, ucm.usage_percentage DESC
                LIMIT 10
            """)
            print("  Sample mappings:")
            for mapping in sample_mappings:
                preferred = " ⭐" if mapping['is_preferred'] else ""
                print(f"    {mapping['category_name']} → {mapping['unit_name']} ({mapping['usage_percentage']:.1f}%){preferred}")
        
        # Check for missing critical tables
        print("\n❌ Missing Tables:")
        missing_tables = []
        
        # Check usda_food_nutrients
        try:
            food_nutrients_count = await conn.fetchval("SELECT COUNT(*) FROM usda_food_nutrients")
            print(f"  usda_food_nutrients: {food_nutrients_count:,} records")
        except:
            missing_tables.append("usda_food_nutrients")
        
        # Check usda_food_portions
        try:
            food_portions_count = await conn.fetchval("SELECT COUNT(*) FROM usda_food_portions")
            print(f"  usda_food_portions: {food_portions_count:,} records")
        except:
            missing_tables.append("usda_food_portions")
        
        if missing_tables:
            print(f"  Missing: {', '.join(missing_tables)}")
        
        print("\n🔧 Functions and Views:")
        # Check for validation functions
        functions = await conn.fetch("""
            SELECT specific_name, routine_type
            FROM information_schema.routines 
            WHERE specific_schema = 'public' 
            AND specific_name LIKE '%usda%' OR specific_name LIKE '%validate%'
        """)
        
        if functions:
            print("  Available functions:")
            for func in functions:
                print(f"    {func['specific_name']} ({func['routine_type']})")
        else:
            print("  No USDA-related functions found")
        
        # Check for views
        views = await conn.fetch("""
            SELECT table_name
            FROM information_schema.views 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%usda%'
        """)
        
        if views:
            print("  Available views:")
            for view in views:
                print(f"    {view['table_name']}")
        else:
            print("  No USDA-related views found")
        
        print("\n" + "="*80)
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(inspect_usda_data())