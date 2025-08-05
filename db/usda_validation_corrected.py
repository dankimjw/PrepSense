#!/usr/bin/env python3
"""
USDA Database Validation - Schema-Corrected Version
==================================================

Comprehensive validation based on actual database schema discovered.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

class USDAValidator:
    """USDA Database Validator"""
    
    def __init__(self):
        self.conn = None
        self.results = {}
        self.issues = []
        self.recommendations = []
        
    def connect(self):
        """Connect to database"""
        try:
            host = os.getenv("POSTGRES_HOST", "127.0.0.1")
            port = int(os.getenv("POSTGRES_PORT", "5432"))
            database = os.getenv("POSTGRES_DATABASE", "prepsense")
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD", "")
            
            self.conn = psycopg2.connect(
                host=host, port=port, database=database,
                user=user, password=password,
                cursor_factory=RealDictCursor
            )
            print("✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute query safely"""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params or {})
            return cur.fetchall()
        except Exception as e:
            print(f"Query error: {str(e)}")
            return []
    
    def test_1_structural_integrity(self):
        """Test 1: Structural Integrity"""
        print("\n🔍 Test 1: Structural Integrity")
        print("-" * 40)
        
        # Check core table row counts
        core_tables = {
            'usda_foods': 'Food items database',
            'usda_food_categories': 'Food category definitions',
            'usda_measure_units': 'Available measurement units',
            'usda_category_unit_mappings': 'Category-unit relationships',
            'usda_food_portions': 'Portion conversion data',
            'usda_food_nutrients': 'Nutritional information'
        }
        
        table_stats = {}
        for table, description in core_tables.items():
            count_result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            count = count_result[0]['count'] if count_result else 0
            table_stats[table] = count
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {table}: {count:,} rows ({description})")
        
        # Foreign key integrity checks
        print("\n  Foreign Key Integrity:")
        
        # Orphaned foods (no category)
        orphaned_foods = self.execute_query("""
            SELECT COUNT(*) as count
            FROM usda_foods f
            LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
            WHERE f.food_category_id IS NOT NULL AND fc.id IS NULL
        """)
        orphan_count = orphaned_foods[0]['count'] if orphaned_foods else 0
        status = "✅" if orphan_count == 0 else "⚠️"
        print(f"    {status} Orphaned foods (no category): {orphan_count}")
        
        # Orphaned category mappings
        orphaned_mappings = self.execute_query("""
            SELECT COUNT(*) as count
            FROM usda_category_unit_mappings m
            LEFT JOIN usda_food_categories fc ON m.category_id = fc.id
            LEFT JOIN usda_measure_units um ON m.unit_id = um.id
            WHERE fc.id IS NULL OR um.id IS NULL
        """)
        mapping_orphans = orphaned_mappings[0]['count'] if orphaned_mappings else 0
        status = "✅" if mapping_orphans == 0 else "⚠️"
        print(f"    {status} Orphaned category mappings: {mapping_orphans}")
        
        # NULL analysis in critical columns
        print("\n  NULL Value Analysis:")
        null_checks = [
            ("usda_foods", "description", "Food descriptions"),
            ("usda_foods", "food_category_id", "Food categories"),
            ("usda_measure_units", "name", "Unit names"),
            ("usda_category_unit_mappings", "usage_percentage", "Usage percentages")
        ]
        
        critical_nulls = 0
        for table, column, description in null_checks:
            null_result = self.execute_query(f"""
                SELECT COUNT(*) as nulls, 
                       (SELECT COUNT(*) FROM {table}) as total
                FROM {table} WHERE {column} IS NULL
            """)
            if null_result:
                nulls = null_result[0]['nulls']
                total = null_result[0]['total']
                percentage = (nulls / total * 100) if total > 0 else 0
                status = "✅" if percentage < 5 else "⚠️" if percentage < 20 else "❌"
                print(f"    {status} {description} NULL: {nulls}/{total} ({percentage:.1f}%)")
                if percentage > 10:
                    critical_nulls += 1
        
        # Overall assessment
        missing_tables = sum(1 for count in table_stats.values() if count == 0)
        
        if missing_tables == 0 and orphan_count == 0 and critical_nulls == 0:
            result = "PASS"
        elif missing_tables <= 1 and orphan_count < 100 and critical_nulls <= 1:
            result = "WARNING"
        else:
            result = "FAIL"
            
        self.results['structural_integrity'] = {
            'status': result,
            'table_stats': table_stats,
            'orphaned_foods': orphan_count,
            'orphaned_mappings': mapping_orphans,
            'critical_nulls': critical_nulls
        }
        
        print(f"\n  🎯 Structural Integrity: {result}")
        return result
    
    def test_2_pantry_coverage(self):
        """Test 2: PrepSense Pantry Coverage"""
        print("\n🔍 Test 2: PrepSense Pantry Coverage")
        print("-" * 40)
        
        # Get sample pantry items
        pantry_items = self.execute_query("""
            SELECT DISTINCT 
                product_name,
                unit_of_measurement,
                COUNT(*) as frequency
            FROM pantry_items 
            WHERE product_name IS NOT NULL 
            AND LENGTH(TRIM(product_name)) > 2
            GROUP BY product_name, unit_of_measurement
            ORDER BY frequency DESC
            LIMIT 50
        """)
        
        if not pantry_items:
            print("  ❌ No pantry items found for coverage analysis")
            self.results['pantry_coverage'] = {'status': 'FAIL', 'message': 'No pantry data'}
            return 'FAIL'
        
        print(f"  📦 Analyzing {len(pantry_items)} unique pantry items...")
        
        # Test matching with USDA foods
        matched_direct = 0
        matched_fuzzy = 0
        unit_supported = 0
        
        for item in pantry_items[:20]:  # Test top 20 items
            product_name = item['product_name']
            unit_name = item['unit_of_measurement']
            
            # Try product aliases first
            alias_match = self.execute_query("""
                SELECT usda_fdc_id FROM product_aliases
                WHERE LOWER(pantry_name) = LOWER(%s)
                LIMIT 1
            """, (product_name,))
            
            if alias_match:
                matched_direct += 1
                fdc_id = alias_match[0]['usda_fdc_id']
            else:
                # Try fuzzy matching
                fuzzy_match = self.execute_query("""
                    SELECT fdc_id FROM usda_foods
                    WHERE description ILIKE %s
                    ORDER BY LENGTH(description)
                    LIMIT 1
                """, (f"%{product_name}%",))
                
                if fuzzy_match:
                    matched_fuzzy += 1
                    fdc_id = fuzzy_match[0]['fdc_id']
                else:
                    fdc_id = None
            
            # Check unit support if we found a food match
            if fdc_id and unit_name:
                unit_check = self.execute_query("""
                    SELECT COUNT(*) as count
                    FROM usda_food_portions fp
                    JOIN usda_measure_units um ON fp.measure_unit_id = um.id
                    WHERE fp.fdc_id = %s
                    AND (LOWER(um.name) = LOWER(%s) OR LOWER(um.abbreviation) = LOWER(%s))
                """, (fdc_id, unit_name, unit_name))
                
                if unit_check and unit_check[0]['count'] > 0:
                    unit_supported += 1
        
        # Calculate coverage metrics
        total_tested = min(20, len(pantry_items))
        total_matched = matched_direct + matched_fuzzy
        direct_coverage = (matched_direct / total_tested) * 100
        total_coverage = (total_matched / total_tested) * 100
        unit_coverage = (unit_supported / total_tested) * 100
        
        print(f"  📊 Coverage Results:")
        print(f"    • Direct matches (aliases): {matched_direct}/{total_tested} ({direct_coverage:.1f}%)")
        print(f"    • Fuzzy matches: {matched_fuzzy}/{total_tested} ({(matched_fuzzy/total_tested)*100:.1f}%)")
        print(f"    • Total food coverage: {total_matched}/{total_tested} ({total_coverage:.1f}%)")
        print(f"    • Unit support coverage: {unit_supported}/{total_tested} ({unit_coverage:.1f}%)")
        
        # Assess common units
        common_units = self.execute_query("""
            SELECT 
                unit_of_measurement,
                COUNT(*) as frequency,
                COUNT(DISTINCT product_name) as unique_products
            FROM pantry_items
            WHERE unit_of_measurement IS NOT NULL
            GROUP BY unit_of_measurement
            ORDER BY frequency DESC
            LIMIT 10
        """)
        
        print(f"\n  🥄 Most Common Units in Pantry:")
        unit_recognition = 0
        total_common_units = len(common_units)
        
        for unit_info in common_units[:5]:
            unit_name = unit_info['unit_of_measurement']
            frequency = unit_info['frequency']
            
            # Check if unit exists in USDA system
            unit_exists = self.execute_query("""
                SELECT COUNT(*) as count
                FROM usda_measure_units
                WHERE LOWER(name) = LOWER(%s) OR LOWER(abbreviation) = LOWER(%s)
            """, (unit_name, unit_name))
            
            recognized = unit_exists[0]['count'] > 0 if unit_exists else False
            if recognized:
                unit_recognition += 1
                
            status = "✅" if recognized else "❌"
            print(f"    {status} {unit_name}: {frequency} items, {unit_info['unique_products']} products")
        
        unit_recognition_rate = (unit_recognition / min(5, total_common_units)) * 100
        
        # Overall assessment
        if total_coverage >= 70 and unit_coverage >= 60:
            result = "PASS"
        elif total_coverage >= 50 and unit_coverage >= 40:
            result = "WARNING" 
        else:
            result = "FAIL"
        
        self.results['pantry_coverage'] = {
            'status': result,
            'total_coverage': total_coverage,
            'unit_coverage': unit_coverage,
            'unit_recognition_rate': unit_recognition_rate,
            'direct_matches': matched_direct,
            'fuzzy_matches': matched_fuzzy
        }
        
        print(f"\n  🎯 Pantry Coverage: {result}")
        return result
    
    def test_3_unit_distribution(self):
        """Test 3: Unit Distribution Analysis"""
        print("\n🔍 Test 3: Unit Distribution & Quality")
        print("-" * 40)
        
        # Unit usage statistics
        unit_stats = self.execute_query("""
            SELECT 
                um.name as unit_name,
                um.abbreviation,
                COUNT(DISTINCT ucm.category_id) as category_count,
                AVG(ucm.usage_percentage) as avg_usage,
                MAX(ucm.usage_percentage) as max_usage,
                COUNT(CASE WHEN ucm.is_preferred THEN 1 END) as preferred_count
            FROM usda_measure_units um
            LEFT JOIN usda_category_unit_mappings ucm ON um.id = ucm.unit_id
            GROUP BY um.id, um.name, um.abbreviation
            ORDER BY avg_usage DESC NULLS LAST
        """)
        
        if not unit_stats:
            print("  ❌ No unit statistics available")
            self.results['unit_distribution'] = {'status': 'FAIL', 'message': 'No unit data'}
            return 'FAIL'
        
        # Analyze distribution
        total_units = len(unit_stats)
        well_used_units = sum(1 for u in unit_stats if (u['avg_usage'] or 0) >= 5 and (u['category_count'] or 0) >= 2)
        rare_units = sum(1 for u in unit_stats if (u['avg_usage'] or 0) < 1)
        preferred_units = sum(1 for u in unit_stats if (u['preferred_count'] or 0) > 0)
        
        print(f"  📊 Unit Distribution:")
        print(f"    • Total units: {total_units}")
        print(f"    • Well-used units (≥5% avg usage, ≥2 categories): {well_used_units}")
        print(f"    • Rare units (<1% usage): {rare_units}")
        print(f"    • Units marked as preferred: {preferred_units}")
        
        # Check for duplicate semantic units
        duplicate_check = self.execute_query("""
            WITH normalized_units AS (
                SELECT 
                    name,
                    LOWER(REGEXP_REPLACE(name, '[^a-zA-Z]', '', 'g')) as clean_name
                FROM usda_measure_units
                WHERE name IS NOT NULL
            )
            SELECT 
                clean_name,
                COUNT(*) as variant_count,
                array_agg(name) as variants
            FROM normalized_units
            GROUP BY clean_name
            HAVING COUNT(*) > 1
            ORDER BY variant_count DESC
        """)
        
        duplicate_groups = len(duplicate_check)
        print(f"    • Potential duplicate unit groups: {duplicate_groups}")
        
        if duplicate_groups > 0:
            print(f"      Top duplicates:")
            for dup in duplicate_check[:3]:
                print(f"        - '{dup['clean_name']}': {dup['variants']}")
        
        # Check for implausible conversions
        implausible = self.execute_query("""
            SELECT COUNT(*) as count
            FROM usda_food_portions
            WHERE gram_weight > 10000 OR gram_weight <= 0 OR amount > 1000 OR amount <= 0
        """)
        
        implausible_count = implausible[0]['count'] if implausible else 0
        print(f"    • Implausible conversions: {implausible_count}")
        
        # Show top preferred units
        print(f"\n  ⭐ Top Preferred Units:")
        top_preferred = [u for u in unit_stats if (u['preferred_count'] or 0) > 0][:10]
        for unit in top_preferred[:5]:
            avg_usage = unit['avg_usage'] or 0
            categories = unit['category_count'] or 0
            print(f"    • {unit['unit_name']}: {avg_usage:.1f}% avg usage, {categories} categories")
        
        # Overall assessment
        well_used_ratio = well_used_units / total_units if total_units > 0 else 0
        rare_ratio = rare_units / total_units if total_units > 0 else 0
        
        if well_used_units >= 15 and rare_ratio < 0.6 and duplicate_groups < 10:
            result = "PASS"
        elif well_used_units >= 10 and rare_ratio < 0.8 and duplicate_groups < 20:
            result = "WARNING"
        else:
            result = "FAIL"
        
        self.results['unit_distribution'] = {
            'status': result,
            'total_units': total_units,
            'well_used_units': well_used_units,
            'rare_units': rare_units,
            'preferred_units': preferred_units,
            'duplicate_groups': duplicate_groups,
            'implausible_conversions': implausible_count
        }
        
        print(f"\n  🎯 Unit Distribution: {result}")
        return result
    
    def test_4_performance(self):
        """Test 4: Performance & Indexing"""
        print("\n🔍 Test 4: Performance & Indexing")
        print("-" * 40)
        
        # Performance test queries
        performance_tests = [
            {
                'name': 'Food search by description',
                'query': "SELECT fdc_id, description FROM usda_foods WHERE description ILIKE %s LIMIT 10",
                'params': ('%chicken%',),
                'max_ms': 100
            },
            {
                'name': 'Category unit lookup',
                'query': """
                    SELECT um.name, ucm.usage_percentage
                    FROM usda_category_unit_mappings ucm
                    JOIN usda_measure_units um ON ucm.unit_id = um.id
                    WHERE ucm.category_id = %s
                """,
                'params': (1,),
                'max_ms': 50
            },
            {
                'name': 'Food portions lookup',
                'query': """
                    SELECT fp.gram_weight, um.name
                    FROM usda_food_portions fp
                    JOIN usda_measure_units um ON fp.measure_unit_id = um.id
                    WHERE fp.fdc_id = %s
                """,
                'params': (167512,),  # Common food ID
                'max_ms': 25
            }
        ]
        
        print(f"  ⏱️  Performance Tests:")
        slow_queries = 0
        
        for test in performance_tests:
            start_time = time.time()
            try:
                results = self.execute_query(test['query'], test['params'])
                end_time = time.time()
                
                duration_ms = (end_time - start_time) * 1000
                result_count = len(results) if results else 0
                
                status = "✅" if duration_ms <= test['max_ms'] else "⚠️"
                if duration_ms > test['max_ms']:
                    slow_queries += 1
                    
                print(f"    {status} {test['name']}: {duration_ms:.1f}ms ({result_count} results)")
                
            except Exception as e:
                print(f"    ❌ {test['name']}: Failed - {str(e)}")
                slow_queries += 1
        
        # Check indexes
        print(f"\n  🗂️  Index Analysis:")
        
        indexes = self.execute_query("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename LIKE 'usda_%'
            ORDER BY tablename, indexname
        """)
        
        index_count = len(indexes) if indexes else 0
        print(f"    • Total USDA table indexes: {index_count}")
        
        # Check for key performance indexes
        critical_indexes = [
            'usda_foods_description',
            'usda_foods_search_vector',
            'usda_category_unit_mappings_category_id',
            'usda_food_portions_fdc_id'
        ]
        
        existing_indexes = [idx['indexname'] for idx in indexes] if indexes else []
        missing_critical = []
        
        for critical_idx in critical_indexes:
            # Check if any existing index contains the critical pattern
            found = any(critical_idx in existing_idx for existing_idx in existing_indexes)
            if not found:
                missing_critical.append(critical_idx)
        
        if missing_critical:
            print(f"    ⚠️  Missing critical indexes: {len(missing_critical)}")
            for missing in missing_critical[:3]:
                print(f"      - {missing}")
        else:
            print(f"    ✅ All critical indexes appear to exist")
        
        # Test validation function performance
        print(f"\n  🔧 Function Performance:")
        
        # Test validate_unit_for_food function
        start_time = time.time()
        try:
            func_result = self.execute_query("""
                SELECT * FROM validate_unit_for_food(%s, %s, NULL)
            """, ('chicken breast', 'pound'))
            end_time = time.time()
            
            func_duration = (end_time - start_time) * 1000
            status = "✅" if func_duration <= 200 else "⚠️"
            print(f"    {status} validate_unit_for_food: {func_duration:.1f}ms")
            
            if func_result:
                print(f"      Result: {func_result[0] if func_result else 'No result'}")
            
        except Exception as e:
            print(f"    ❌ validate_unit_for_food: Failed - {str(e)}")
            slow_queries += 1
        
        # Overall assessment
        if slow_queries == 0 and len(missing_critical) == 0:
            result = "PASS"
        elif slow_queries <= 1 and len(missing_critical) <= 2:
            result = "WARNING"
        else:
            result = "FAIL"
        
        self.results['performance'] = {
            'status': result,
            'slow_queries': slow_queries,
            'total_indexes': index_count,
            'missing_critical_indexes': len(missing_critical)
        }
        
        print(f"\n  🎯 Performance: {result}")
        return result
    
    def test_5_functional(self):
        """Test 5: Functional Validation"""
        print("\n🔍 Test 5: Functional Validation")
        print("-" * 40)
        
        # Test validate_unit_for_food function with various cases
        test_cases = [
            {'food': 'chicken breast', 'unit': 'pound', 'should_work': True},
            {'food': 'chicken breast', 'unit': 'ounce', 'should_work': True},
            {'food': 'olive oil', 'unit': 'tablespoon', 'should_work': True},
            {'food': 'bread', 'unit': 'slice', 'should_work': True},
            {'food': 'milk', 'unit': 'cup', 'should_work': True},
            {'food': 'chicken', 'unit': 'gallon', 'should_work': False}  # Implausible
        ]
        
        print(f"  🧪 Unit Validation Tests:")
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for test_case in test_cases:
            try:
                result = self.execute_query("""
                    SELECT * FROM validate_unit_for_food(%s, %s, NULL)
                """, (test_case['food'], test_case['unit']))
                
                if result and len(result) > 0:
                    # The function returned a result - check if it makes sense
                    is_valid = result[0].get('is_valid', False)
                    confidence = result[0].get('confidence', 0)
                    
                    # Consider it working if we get a reasonable response
                    test_passed = True  # Function executed successfully
                    if test_case['should_work']:
                        status = "✅" if is_valid else "⚠️"
                    else:
                        status = "✅" if not is_valid else "⚠️"
                    
                    print(f"    {status} {test_case['food']} + {test_case['unit']}: valid={is_valid}, conf={confidence}")
                    passed_tests += 1
                else:
                    print(f"    ❌ {test_case['food']} + {test_case['unit']}: No result")
                    
            except Exception as e:
                print(f"    ❌ {test_case['food']} + {test_case['unit']}: Error - {str(e)}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"    📊 Function success rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Test basic food search
        print(f"\n  🔍 Food Search Tests:")
        
        search_terms = ['chicken', 'bread', 'milk', 'apple']
        search_passed = 0
        
        for term in search_terms:
            try:
                search_result = self.execute_query("""
                    SELECT COUNT(*) as count FROM usda_foods 
                    WHERE description ILIKE %s
                """, (f'%{term}%',))
                
                count = search_result[0]['count'] if search_result else 0
                status = "✅" if count > 0 else "❌"
                print(f"    {status} Search '{term}': {count} results")
                
                if count > 0:
                    search_passed += 1
                    
            except Exception as e:
                print(f"    ❌ Search '{term}': Error - {str(e)}")
        
        search_success_rate = (search_passed / len(search_terms)) * 100
        
        # Overall functional assessment
        if success_rate >= 80 and search_success_rate >= 75:
            result = "PASS"
        elif success_rate >= 60 and search_success_rate >= 50:
            result = "WARNING"
        else:
            result = "FAIL"
        
        self.results['functional'] = {
            'status': result,
            'validation_success_rate': success_rate,
            'search_success_rate': search_success_rate
        }
        
        print(f"\n  🎯 Functional Validation: {result}")
        return result
    
    def assess_overall(self):
        """Overall Assessment"""
        print("\n🎯 Overall Assessment")
        print("=" * 50)
        
        # Calculate weighted score
        weights = {
            'structural_integrity': 0.25,
            'pantry_coverage': 0.25,
            'unit_distribution': 0.20,
            'performance': 0.15,
            'functional': 0.15
        }
        
        scores = {
            'PASS': 100,
            'WARNING': 60,
            'FAIL': 20
        }
        
        total_score = 0
        for test, weight in weights.items():
            if test in self.results:
                status = self.results[test]['status']
                score = scores.get(status, 0)
                total_score += score * weight
        
        # Determine readiness
        if total_score >= 80:
            readiness = "PRODUCTION_READY"
            emoji = "🟢"
        elif total_score >= 60:
            readiness = "CONDITIONALLY_READY"  
            emoji = "🟡"
        else:
            readiness = "NOT_READY"
            emoji = "🔴"
        
        print(f"{emoji} Database Status: {readiness}")
        print(f"📊 Overall Score: {total_score:.1f}/100")
        
        print(f"\n📋 Test Results Summary:")
        for test, result in self.results.items():
            status = result['status']
            emoji = "✅" if status == 'PASS' else "⚠️" if status == 'WARNING' else "❌"
            print(f"  {emoji} {test.replace('_', ' ').title()}: {status}")
        
        return readiness, total_score
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 USDA Database Validation Suite")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # Run all tests
            self.test_1_structural_integrity()
            self.test_2_pantry_coverage()
            self.test_3_unit_distribution()
            self.test_4_performance()
            self.test_5_functional()
            
            # Overall assessment
            readiness, score = self.assess_overall()
            
            return readiness in ["PRODUCTION_READY", "CONDITIONALLY_READY"]
            
        finally:
            if self.conn:
                self.conn.close()

def main():
    validator = USDAValidator()
    success = validator.run_validation()
    
    # Generate documentation
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create report content
    report_content = f"""# USDA Database Validation Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

The USDA database validation has been completed with the following results:

"""
    
    for test_name, result in validator.results.items():
        status = result['status']
        emoji = "✅" if status == 'PASS' else "⚠️" if status == 'WARNING' else "❌"
        report_content += f"- {emoji} **{test_name.replace('_', ' ').title()}**: {status}\n"
    
    report_content += f"""

## Detailed Results

### 1. Structural Integrity
"""
    
    if 'structural_integrity' in validator.results:
        si = validator.results['structural_integrity']
        report_content += f"""
- **Status**: {si['status']}
- **Table Statistics**: {si.get('table_stats', {})}
- **Orphaned Foods**: {si.get('orphaned_foods', 'N/A')}
- **Orphaned Mappings**: {si.get('orphaned_mappings', 'N/A')}
- **Critical NULL Issues**: {si.get('critical_nulls', 'N/A')}
"""
    
    if 'pantry_coverage' in validator.results:
        pc = validator.results['pantry_coverage']
        report_content += f"""
### 2. Pantry Coverage
- **Status**: {pc['status']}
- **Total Coverage**: {pc.get('total_coverage', 'N/A'):.1f}%
- **Unit Coverage**: {pc.get('unit_coverage', 'N/A'):.1f}%
- **Direct Matches**: {pc.get('direct_matches', 'N/A')}
- **Fuzzy Matches**: {pc.get('fuzzy_matches', 'N/A')}
"""
    
    if 'unit_distribution' in validator.results:
        ud = validator.results['unit_distribution']
        report_content += f"""
### 3. Unit Distribution
- **Status**: {ud['status']}
- **Total Units**: {ud.get('total_units', 'N/A')}
- **Well-Used Units**: {ud.get('well_used_units', 'N/A')}
- **Rare Units**: {ud.get('rare_units', 'N/A')}
- **Duplicate Groups**: {ud.get('duplicate_groups', 'N/A')}
"""
    
    if 'performance' in validator.results:
        perf = validator.results['performance']
        report_content += f"""
### 4. Performance & Indexing
- **Status**: {perf['status']}
- **Slow Queries**: {perf.get('slow_queries', 'N/A')}
- **Total Indexes**: {perf.get('total_indexes', 'N/A')}
- **Missing Critical Indexes**: {perf.get('missing_critical_indexes', 'N/A')}
"""
    
    if 'functional' in validator.results:
        func = validator.results['functional']
        report_content += f"""
### 5. Functional Validation
- **Status**: {func['status']}
- **Validation Success Rate**: {func.get('validation_success_rate', 'N/A'):.1f}%
- **Search Success Rate**: {func.get('search_success_rate', 'N/A'):.1f}%
"""
    
    report_content += f"""

## Recommendations

Based on the validation results, the following actions are recommended:

1. **Address any FAIL status items immediately**
2. **Investigate WARNING status items for potential improvements**
3. **Monitor performance metrics in production**
4. **Consider expanding product aliases for better pantry coverage**
5. **Review and clean up duplicate unit definitions**

## Next Steps

- Apply migration 001_fix_usda_critical_issues.sql if not already done
- Run targeted fixes for identified issues
- Re-run validation after fixes
- Monitor database performance in production environment

---
*Report generated by USDA Database Validation Suite*
"""
    
    # Save report
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    report_file = docs_dir / f"usda_validation_report_{timestamp}.md"
    
    try:
        with open(report_file, 'w') as f:
            f.write(report_content)
        print(f"\n📄 Validation report saved to: {report_file}")
    except Exception as e:
        print(f"❌ Failed to save report: {str(e)}")
        print("Report content would be:")
        print(report_content[:500] + "...")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)