#!/usr/bin/env python3
"""
USDA Database Validation Summary
Quick summary of key validation findings
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def quick_validation_summary():
    """Generate a quick validation summary"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DATABASE", "prepsense"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            cursor_factory=RealDictCursor
        )
        
        cur = conn.cursor()
        
        print("🔍 USDA Database Validation Summary")
        print("=" * 50)
        
        # Core table status
        print("\n📊 Core Data Status:")
        tables = {
            'usda_foods': 'Food items',
            'usda_food_categories': 'Food categories',
            'usda_measure_units': 'Measurement units',
            'usda_category_unit_mappings': 'Unit mappings',
            'usda_food_portions': 'Portion conversions',
            'usda_food_nutrients': 'Nutritional data'
        }
        
        critical_missing = 0
        for table, description in tables.items():
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cur.fetchone()['count']
            
            if count == 0 and table in ['usda_food_portions', 'usda_food_nutrients']:
                status = "❌ CRITICAL"
                critical_missing += 1
            elif count == 0:
                status = "❌ EMPTY"
            elif count < 100:
                status = "⚠️  LOW"
            else:
                status = "✅ OK"
                
            print(f"  {status} {table}: {count:,} rows ({description})")
        
        # Data quality check
        print("\n🔍 Data Quality Issues:")
        
        # NULL food categories
        cur.execute("""
            SELECT 
                COUNT(CASE WHEN food_category_id IS NULL THEN 1 END) as null_categories,
                COUNT(*) as total_foods
            FROM usda_foods
        """)
        result = cur.fetchone()
        null_pct = (result['null_categories'] / result['total_foods']) * 100
        
        status = "❌ CRITICAL" if null_pct > 50 else "⚠️  WARNING" if null_pct > 20 else "✅ OK"
        print(f"  {status} Foods without categories: {result['null_categories']:,}/{result['total_foods']:,} ({null_pct:.1f}%)")
        
        # Unit validation test
        print("\n🧪 Quick Function Test:")
        
        try:
            cur.execute("SELECT * FROM validate_unit_for_food('chicken breast', 'pound', NULL)")
            result = cur.fetchone()
            
            if result:
                is_valid = result['is_valid']
                confidence = result['confidence']
                reason = result['reason']
                
                status = "✅ WORKS" if is_valid else "⚠️  LIMITED"
                print(f"  {status} validate_unit_for_food: valid={is_valid}, confidence={confidence}")
                print(f"    Reason: {reason}")
            else:
                print("  ❌ validate_unit_for_food: No result")
                
        except Exception as e:
            print(f"  ❌ validate_unit_for_food: Error - {str(e)}")
        
        # Overall assessment
        print("\n🎯 Overall Assessment:")
        
        if critical_missing >= 2:
            assessment = "🔴 NOT READY"
            message = "Critical tables missing - unit validation impossible"
        elif critical_missing >= 1:
            assessment = "🟡 MAJOR ISSUES"
            message = "Missing essential data for full functionality"
        elif null_pct > 50:
            assessment = "🟡 DATA QUALITY ISSUES"
            message = "Significant data quality problems"
        else:
            assessment = "🟢 READY"
            message = "Database appears ready for production"
        
        print(f"  Status: {assessment}")
        print(f"  Summary: {message}")
        
        # Key recommendations
        print(f"\n💡 Key Recommendations:")
        
        if critical_missing > 0:
            print(f"  1. Import missing USDA data (food_portions, food_nutrients)")
        
        if null_pct > 20:
            print(f"  2. Fix food categorization issues ({null_pct:.1f}% uncategorized)")
        
        print(f"  3. Add performance indexes for production use")
        print(f"  4. Expand product aliases for better pantry coverage")
        
        print(f"\n📋 Full detailed report available at:")
        print(f"     docs/usda_database_comprehensive_validation_report.md")
        
        return assessment != "🔴 NOT READY"
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = quick_validation_summary()
    exit(0 if success else 1)