#!/usr/bin/env python3
"""
Detailed USDA Database Analysis - Based on current data state
Focus on existing tables and provide specific optimization recommendations.
"""

import asyncio
import asyncpg
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def detailed_usda_analysis():
    """Run detailed analysis on existing USDA data."""
    
    # Connect to database
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_name = os.getenv('POSTGRES_DATABASE')
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = await asyncpg.connect(db_url)
    
    analysis_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "data_quality": {},
        "performance_analysis": {},
        "coverage_analysis": {},
        "indexing_recommendations": [],
        "data_completeness": {},
        "integration_points": {}
    }
    
    try:
        print("="*80)
        print("🔬 DETAILED USDA DATABASE ANALYSIS")
        print("="*80)
        
        # 1. DATA QUALITY ANALYSIS
        print("\n📊 1. DATA QUALITY ANALYSIS")
        print("-" * 40)
        
        # Food data quality
        print("🔍 Food Data Quality:")
        
        # Check for duplicate foods by description
        duplicates = await conn.fetch("""
            SELECT description, COUNT(*) as count
            FROM usda_foods 
            GROUP BY description 
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        duplicate_count = len(duplicates)
        total_foods = await conn.fetchval("SELECT COUNT(*) FROM usda_foods")
        
        print(f"  • Total foods: {total_foods:,}")
        print(f"  • Duplicate descriptions: {duplicate_count}")
        if duplicates:
            print("    Top duplicates:")
            for dup in duplicates[:5]:
                print(f"      '{dup['description']}': {dup['count']} entries")
        
        # Data type distribution
        data_types = await conn.fetch("""
            SELECT data_type, COUNT(*) as count
            FROM usda_foods 
            GROUP BY data_type 
            ORDER BY COUNT(*) DESC
        """)
        
        print("  • Data type distribution:")
        for dt in data_types:
            percentage = (dt['count'] / total_foods) * 100
            print(f"      {dt['data_type']}: {dt['count']:,} ({percentage:.1f}%)")
        
        analysis_results["data_quality"]["foods"] = {
            "total_foods": total_foods,
            "duplicate_descriptions": duplicate_count,
            "data_types": {dt['data_type']: dt['count'] for dt in data_types}
        }
        
        # Brand data quality
        branded_foods = await conn.fetchval("""
            SELECT COUNT(*) FROM usda_foods 
            WHERE data_type = 'branded_food'
        """)
        
        foods_with_brands = await conn.fetchval("""
            SELECT COUNT(*) FROM usda_foods 
            WHERE brand_owner IS NOT NULL
        """)
        
        foods_with_barcodes = await conn.fetchval("""
            SELECT COUNT(*) FROM usda_foods 
            WHERE gtin_upc IS NOT NULL AND gtin_upc != ''
        """)
        
        print(f"  • Branded foods: {branded_foods:,}")
        print(f"  • Foods with brand owner: {foods_with_brands:,}")
        print(f"  • Foods with barcodes: {foods_with_barcodes:,}")
        
        analysis_results["data_quality"]["brand_data"] = {
            "branded_foods": branded_foods,
            "foods_with_brands": foods_with_brands,
            "foods_with_barcodes": foods_with_barcodes
        }
        
        # 2. CATEGORY ANALYSIS
        print("\n🔍 Category Analysis:")
        
        # Category distribution
        category_distribution = await conn.fetch("""
            SELECT 
                fc.description as category_name,
                COUNT(f.fdc_id) as food_count
            FROM usda_food_categories fc
            LEFT JOIN usda_foods f ON fc.id = f.food_category_id
            GROUP BY fc.id, fc.description
            ORDER BY COUNT(f.fdc_id) DESC
        """)
        
        print("  • Top 10 categories by food count:")
        for i, cat in enumerate(category_distribution[:10]):
            print(f"      {i+1:2d}. {cat['category_name']}: {cat['food_count']:,} foods")
        
        # Categories with no foods
        empty_categories = [cat for cat in category_distribution if cat['food_count'] == 0]
        if empty_categories:
            print(f"  • Empty categories: {len(empty_categories)}")
            for cat in empty_categories[:5]:
                print(f"      - {cat['category_name']}")
        
        analysis_results["data_quality"]["categories"] = {
            "total_categories": len(category_distribution),
            "empty_categories": len(empty_categories),
            "distribution": {cat['category_name']: cat['food_count'] for cat in category_distribution}
        }
        
        # 3. UNIT MAPPING ANALYSIS
        print("\n🔍 Unit Mapping Analysis:")
        
        # Unit type distribution
        unit_types = await conn.fetch("""
            SELECT 
                unit_type, 
                COUNT(*) as count,
                ARRAY_AGG(name ORDER BY name) as examples
            FROM usda_measure_units 
            WHERE unit_type IS NOT NULL
            GROUP BY unit_type 
            ORDER BY COUNT(*) DESC
        """)
        
        print("  • Unit types:")
        for ut in unit_types:
            examples = ', '.join(ut['examples'][:3])  # First 3 examples
            print(f"      {ut['unit_type']}: {ut['count']} units ({examples}...)")
        
        # Category-unit mapping coverage
        mapping_coverage = await conn.fetch("""
            SELECT 
                fc.description as category_name,
                COUNT(ucm.id) as mapping_count,
                COUNT(CASE WHEN ucm.is_preferred THEN 1 END) as preferred_count
            FROM usda_food_categories fc
            LEFT JOIN usda_category_unit_mappings ucm ON fc.id = ucm.category_id
            GROUP BY fc.id, fc.description
            ORDER BY COUNT(ucm.id) DESC
        """)
        
        print("  • Category mapping coverage:")
        categories_with_mappings = sum(1 for m in mapping_coverage if m['mapping_count'] > 0)
        total_categories = len(mapping_coverage)
        print(f"      Categories with mappings: {categories_with_mappings}/{total_categories}")
        
        for mapping in mapping_coverage[:5]:
            if mapping['mapping_count'] > 0:
                print(f"      {mapping['category_name']}: {mapping['mapping_count']} units ({mapping['preferred_count']} preferred)")
        
        analysis_results["data_quality"]["unit_mappings"] = {
            "categories_with_mappings": categories_with_mappings,
            "total_categories": total_categories,
            "unit_types": {ut['unit_type']: ut['count'] for ut in unit_types}
        }
        
        # 4. PERFORMANCE ANALYSIS
        print("\n⚡ 2. PERFORMANCE ANALYSIS")
        print("-" * 40)
        
        # Index analysis
        indexes = await conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename LIKE '%usda%'
            ORDER BY tablename, indexname
        """)
        
        print("🔍 Existing Indexes:")
        current_table = None
        for idx in indexes:
            if idx['tablename'] != current_table:
                print(f"  • {idx['tablename']}:")
                current_table = idx['tablename']
            index_type = "GIN" if "gin" in idx['indexdef'].lower() else "BTREE"
            print(f"      - {idx['indexname']} ({index_type})")
        
        # Query performance tests
        print("\n🔍 Query Performance Tests:")
        
        # Test 1: Food search by description
        start_time = datetime.utcnow()
        search_results = await conn.fetch("""
            SELECT fdc_id, description 
            FROM usda_foods 
            WHERE description ILIKE '%chicken%'
            LIMIT 10
        """)
        search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        print(f"  • Food search ('chicken'): {search_time:.2f}ms ({len(search_results)} results)")
        
        # Test 2: Category unit lookup
        start_time = datetime.utcnow()
        category_units = await conn.fetch("""
            SELECT um.name, ucm.usage_percentage
            FROM usda_category_unit_mappings ucm
            JOIN usda_measure_units um ON ucm.unit_id = um.id
            WHERE ucm.category_id = 1
            ORDER BY ucm.usage_percentage DESC
        """)
        category_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        print(f"  • Category unit lookup: {category_time:.2f}ms ({len(category_units)} results)")
        
        # Test 3: Food by category
        start_time = datetime.utcnow()
        category_foods = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM usda_foods 
            WHERE food_category_id = 1
        """)
        category_food_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        print(f"  • Foods by category: {category_food_time:.2f}ms")
        
        analysis_results["performance_analysis"] = {
            "indexes": [{"table": idx['tablename'], "name": idx['indexname']} for idx in indexes],
            "query_times": {
                "food_search_ms": round(search_time, 2),
                "category_units_ms": round(category_time, 2),
                "foods_by_category_ms": round(category_food_time, 2)
            }
        }
        
        # 5. COVERAGE FOR PREPSENSE ITEMS
        print("\n🎯 3. PREPSENSE INTEGRATION ANALYSIS")
        print("-" * 40)
        
        # Sample pantry items
        pantry_items = await conn.fetch("""
            SELECT 
                product_name,
                category,
                unit_of_measurement,
                COUNT(*) as frequency
            FROM pantry_items 
            WHERE product_name IS NOT NULL 
            AND product_name != ''
            GROUP BY product_name, category, unit_of_measurement
            ORDER BY COUNT(*) DESC
            LIMIT 20
        """)
        
        print("🔍 Top Pantry Items vs USDA Coverage:")
        matched_items = 0
        total_tested = 0
        
        for item in pantry_items:
            total_tested += 1
            product_name = item['product_name'].lower().strip()
            
            # Try to find match in USDA
            usda_match = await conn.fetchval("""
                SELECT fdc_id 
                FROM usda_foods 
                WHERE LOWER(description) LIKE $1
                LIMIT 1
            """, f"%{product_name}%")
            
            match_status = "✅" if usda_match else "❌"
            if usda_match:
                matched_items += 1
            
            print(f"  {match_status} {item['product_name']} ({item['unit_of_measurement']}) - {item['frequency']} times")
        
        coverage_percentage = (matched_items / total_tested) * 100 if total_tested > 0 else 0
        print(f"\n📊 Coverage: {matched_items}/{total_tested} ({coverage_percentage:.1f}%)")
        
        # Unit validation analysis
        print("\n🔍 Unit Validation Analysis:")
        
        # Check most common pantry units vs USDA units
        pantry_units = await conn.fetch("""
            SELECT 
                unit_of_measurement,
                COUNT(*) as frequency
            FROM pantry_items 
            WHERE unit_of_measurement IS NOT NULL
            GROUP BY unit_of_measurement
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        
        print("  • Most common pantry units:")
        for unit in pantry_units:
            # Check if unit exists in USDA
            usda_unit = await conn.fetchval("""
                SELECT id FROM usda_measure_units 
                WHERE LOWER(name) = LOWER($1) 
                OR LOWER(abbreviation) = LOWER($1)
            """, unit['unit_of_measurement'])
            
            status = "✅" if usda_unit else "❌"
            print(f"      {status} {unit['unit_of_measurement']}: {unit['frequency']} items")
        
        analysis_results["integration_points"] = {
            "pantry_item_coverage": {
                "matched": matched_items,
                "total_tested": total_tested,
                "coverage_percentage": round(coverage_percentage, 1)
            },
            "unit_coverage": {unit['unit_of_measurement']: {
                "frequency": unit['frequency'],
                "in_usda": bool(await conn.fetchval("""
                    SELECT id FROM usda_measure_units 
                    WHERE LOWER(name) = LOWER($1) 
                    OR LOWER(abbreviation) = LOWER($1)
                """, unit['unit_of_measurement']))
            } for unit in pantry_units}
        }
        
        # 6. RECOMMENDATIONS
        print("\n💡 4. RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = []
        
        # Critical missing tables
        recommendations.append({
            "priority": "CRITICAL",
            "category": "Missing Data",
            "issue": "usda_food_portions and usda_food_nutrients tables are missing",
            "impact": "Cannot perform unit conversions or provide nutritional data",
            "action": "Import missing USDA data files (food_portion.csv, food_nutrient.csv)",
            "sql": """
-- Import food portions for unit conversions
CREATE TABLE usda_food_portions (
    id SERIAL PRIMARY KEY,
    fdc_id INTEGER NOT NULL,
    seq_num INTEGER,
    amount DECIMAL(10,3),
    measure_unit_id INTEGER,
    portion_description VARCHAR(255),
    modifier VARCHAR(255),
    gram_weight DECIMAL(10,3),
    
    FOREIGN KEY (fdc_id) REFERENCES usda_foods(fdc_id),
    FOREIGN KEY (measure_unit_id) REFERENCES usda_measure_units(id)
);
            """
        })
        
        # Performance improvements
        if category_time > 50:
            recommendations.append({
                "priority": "HIGH",
                "category": "Performance",
                "issue": f"Category unit lookup taking {category_time:.1f}ms",
                "impact": "Slow API responses for unit validation",
                "action": "Add composite index on category_unit_mappings",
                "sql": "CREATE INDEX idx_usda_category_unit_perf ON usda_category_unit_mappings (category_id, usage_percentage DESC, is_preferred);"
            })
        
        # Coverage improvements
        if coverage_percentage < 80:
            recommendations.append({
                "priority": "HIGH",
                "category": "Coverage",
                "issue": f"Only {coverage_percentage:.1f}% of pantry items match USDA foods",
                "impact": "Poor unit validation for real user items",
                "action": "Create fuzzy matching or alias table for common products",
                "sql": """
-- Create product alias table
CREATE TABLE product_aliases (
    id SERIAL PRIMARY KEY,
    pantry_name VARCHAR(255) NOT NULL,
    usda_fdc_id INTEGER NOT NULL,
    confidence_score DECIMAL(3,2),
    created_by VARCHAR(50) DEFAULT 'system',
    
    FOREIGN KEY (usda_fdc_id) REFERENCES usda_foods(fdc_id),
    UNIQUE(pantry_name)
);
            """
            })
        
        # Search optimization
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Search Performance",
            "issue": "Food text search could be improved",
            "impact": "Slower food matching for pantry items",
            "action": "Implement full-text search with trigram matching",
            "sql": """
-- Add trigram extension and index
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_usda_foods_description_trgm ON usda_foods USING GIN (description gin_trgm_ops);
            """
        })
        
        # Data quality improvements
        if duplicate_count > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Data Quality",
                "issue": f"Found {duplicate_count} duplicate food descriptions",
                "impact": "Inconsistent matching and user confusion",
                "action": "Deduplicate foods or add preference ranking",
                "sql": """
-- Find and review duplicates
SELECT description, COUNT(*), ARRAY_AGG(fdc_id) as fdc_ids
FROM usda_foods 
GROUP BY description 
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
            """
            })
        
        print("🎯 Priority Actions:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['priority']}] {rec['issue']}")
            print(f"   Action: {rec['action']}")
            print(f"   Impact: {rec['impact']}")
            print()
        
        analysis_results["recommendations"] = recommendations
        
        print("="*80)
        
    finally:
        await conn.close()
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/Users/danielkim/_Capstone/PrepSense/db/usda_detailed_analysis_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"📊 Detailed analysis saved to: {output_file}")
    return analysis_results


if __name__ == "__main__":
    asyncio.run(detailed_usda_analysis())