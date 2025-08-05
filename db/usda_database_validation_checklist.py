#!/usr/bin/env python3
"""
USDA Database Validation Checklist
==================================

Comprehensive validation suite to assess if the current PostgreSQL USDA data 
is production-ready for PrepSense's unit validation pipeline.

This script runs through:
1. Structural Integrity Tests
2. Coverage for PrepSense Pantry Items
3. Unit Distribution & Outliers
4. Performance & Indexing
5. Functional Tests
6. Decision Rules Assessment
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Load environment variables
load_dotenv()

# Add parent directory to path to import from backend_gateway
sys.path.append(str(Path(__file__).parent.parent))

from backend_gateway.config.database import get_database_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USDAValidationResults:
    """Container for validation results"""
    
    def __init__(self):
        self.results = {}
        self.metrics = {}
        self.issues = []
        self.recommendations = []
        self.overall_assessment = "UNKNOWN"
        
    def add_result(self, test_name: str, status: str, details: Dict[str, Any], metrics: Dict[str, Any] = None):
        """Add a test result"""
        self.results[test_name] = {
            "status": status,  # PASS, FAIL, WARNING
            "details": details,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        }
        
    def add_issue(self, issue: str):
        """Add an identified issue"""
        self.issues.append(issue)
        
    def add_recommendation(self, recommendation: str):
        """Add a recommendation"""
        self.recommendations.append(recommendation)

class USDADatabaseValidator:
    """Main validator class"""
    
    def __init__(self):
        self.db_service = None
        self.results = USDAValidationResults()
        
    def connect_database(self):
        """Establish database connection"""
        try:
            self.db_service = get_database_service()
            logger.info("✅ Connected to database successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {str(e)}")
            self.results.add_issue(f"Database connection failed: {str(e)}")
            return False
            
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query with error handling"""
        try:
            return self.db_service.execute_query(query, params or {})
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            logger.error(f"Query: {query}")
            return []
            
    def get_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        result = self.execute_query("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %(table_name)s
        """, {"table_name": table_name})
        
        return result[0]['count'] > 0 if result else False

    def test_structural_integrity(self):
        """Test 1: Structural Integrity Tests"""
        logger.info("🔍 Running Structural Integrity Tests...")
        
        # Check required tables exist
        required_tables = [
            'usda_foods',
            'usda_food_categories', 
            'usda_measure_units',
            'usda_category_unit_mappings',
            'usda_food_portions',
            'usda_food_nutrients'
        ]
        
        missing_tables = []
        for table in required_tables:
            if not self.get_table_exists(table):
                missing_tables.append(table)
                
        if missing_tables:
            self.results.add_result("structural_integrity", "FAIL", {
                "missing_tables": missing_tables,
                "message": "Critical USDA tables are missing"
            })
            self.results.add_issue(f"Missing critical tables: {', '.join(missing_tables)}")
            return
            
        # Foreign key health check - orphaned rows
        logger.info("  Checking foreign key integrity...")
        
        # Check orphaned foods (foods without categories)
        orphaned_foods = self.execute_query("""
            SELECT COUNT(*) as count
            FROM usda_foods f
            LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
            WHERE f.food_category_id IS NOT NULL AND fc.id IS NULL
        """)
        
        # Check orphaned category mappings
        orphaned_mappings = self.execute_query("""
            SELECT COUNT(*) as count
            FROM usda_category_unit_mappings m
            LEFT JOIN usda_food_categories fc ON m.category_id = fc.id
            LEFT JOIN usda_measure_units um ON m.unit_id = um.id
            WHERE fc.id IS NULL OR um.id IS NULL
        """)
        
        # Check orphaned food portions
        orphaned_portions = self.execute_query("""
            SELECT COUNT(*) as count
            FROM usda_food_portions fp
            LEFT JOIN usda_foods f ON fp.fdc_id = f.fdc_id
            WHERE f.fdc_id IS NULL
        """)
        
        # Primary key density analysis
        logger.info("  Analyzing primary key density...")
        
        table_stats = {}
        for table in required_tables:
            stats = self.execute_query(f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT COALESCE(id, fdc_id)) as unique_keys
                FROM {table}
            """)
            if stats:
                table_stats[table] = stats[0]
                
        # NULL hotspots in critical columns
        logger.info("  Checking NULL hotspots...")
        
        null_checks = {
            "usda_foods": ["description", "food_category_id"],
            "usda_category_unit_mappings": ["category_id", "unit_id", "usage_percentage"],
            "usda_food_portions": ["fdc_id", "gram_weight"],
            "usda_measure_units": ["name"]
        }
        
        null_hotspots = {}
        for table, columns in null_checks.items():
            if self.get_table_exists(table):
                for column in columns:
                    null_count = self.execute_query(f"""
                        SELECT COUNT(*) as count
                        FROM {table}
                        WHERE {column} IS NULL
                    """)
                    if null_count and null_count[0]['count'] > 0:
                        null_hotspots[f"{table}.{column}"] = null_count[0]['count']
        
        # Determine status
        issues = []
        if orphaned_foods and orphaned_foods[0]['count'] > 0:
            issues.append(f"Orphaned foods: {orphaned_foods[0]['count']}")
        if orphaned_mappings and orphaned_mappings[0]['count'] > 0:
            issues.append(f"Orphaned mappings: {orphaned_mappings[0]['count']}")
        if orphaned_portions and orphaned_portions[0]['count'] > 0:
            issues.append(f"Orphaned portions: {orphaned_portions[0]['count']}")
        if null_hotspots:
            issues.append(f"NULL hotspots in {len(null_hotspots)} columns")
            
        status = "FAIL" if issues else "PASS"
        
        self.results.add_result("structural_integrity", status, {
            "orphaned_foods": orphaned_foods[0]['count'] if orphaned_foods else 0,
            "orphaned_mappings": orphaned_mappings[0]['count'] if orphaned_mappings else 0,
            "orphaned_portions": orphaned_portions[0]['count'] if orphaned_portions else 0,
            "table_stats": table_stats,
            "null_hotspots": null_hotspots,
            "issues": issues
        })
        
        if issues:
            for issue in issues:
                self.results.add_issue(f"Structural integrity: {issue}")

    def test_pantry_coverage(self):
        """Test 2: Coverage for PrepSense Pantry Items"""
        logger.info("🔍 Testing PrepSense Pantry Item Coverage...")
        
        # Check if pantry_items table exists
        if not self.get_table_exists('pantry_items'):
            self.results.add_result("pantry_coverage", "FAIL", {
                "message": "pantry_items table not found - cannot assess coverage"
            })
            self.results.add_issue("pantry_items table missing - required for coverage analysis")
            return
            
        # Extract sample pantry items
        sample_pantry_items = self.execute_query("""
            SELECT DISTINCT 
                product_name,
                unit_of_measurement,
                COUNT(*) as frequency
            FROM pantry_items 
            WHERE product_name IS NOT NULL 
            AND product_name != ''
            AND LENGTH(product_name) > 2
            GROUP BY product_name, unit_of_measurement
            ORDER BY frequency DESC
            LIMIT 100
        """)
        
        if not sample_pantry_items:
            self.results.add_result("pantry_coverage", "WARNING", {
                "message": "No pantry items found for coverage analysis"
            })
            return
            
        # Test matching pantry items to USDA foods
        logger.info("  Testing pantry item matching...")
        
        matched_items = 0
        unit_coverage_stats = {}
        
        for item in sample_pantry_items[:20]:  # Test first 20 items
            product_name = item['product_name']
            unit_name = item['unit_of_measurement']
            
            # Try exact alias match first
            alias_match = self.execute_query("""
                SELECT pa.usda_fdc_id, pa.confidence_score
                FROM product_aliases pa
                WHERE LOWER(pa.pantry_name) = LOWER(%(product_name)s)
                LIMIT 1
            """, {"product_name": product_name})
            
            # Try fuzzy USDA search
            usda_match = self.execute_query("""
                SELECT f.fdc_id, similarity(f.description, %(product_name)s) as sim_score
                FROM usda_foods f
                WHERE f.description %% %(product_name)s
                ORDER BY similarity(f.description, %(product_name)s) DESC
                LIMIT 1
            """, {"product_name": product_name})
            
            if alias_match or (usda_match and usda_match[0]['sim_score'] > 0.3):
                matched_items += 1
                
                # Check unit coverage for matched item
                fdc_id = alias_match[0]['usda_fdc_id'] if alias_match else usda_match[0]['fdc_id']
                
                unit_available = self.execute_query("""
                    SELECT COUNT(*) as count
                    FROM usda_food_portions fp
                    JOIN usda_measure_units um ON fp.measure_unit_id = um.id
                    WHERE fp.fdc_id = %(fdc_id)s
                    AND (LOWER(um.name) = LOWER(%(unit_name)s) 
                         OR LOWER(um.abbreviation) = LOWER(%(unit_name)s))
                """, {"fdc_id": fdc_id, "unit_name": unit_name})
                
                unit_coverage_stats[unit_name] = unit_coverage_stats.get(unit_name, 0) + (1 if unit_available[0]['count'] > 0 else 0)
        
        # Calculate coverage metrics
        total_tested = min(20, len(sample_pantry_items))
        match_percentage = (matched_items / total_tested) * 100 if total_tested > 0 else 0
        
        # Unit coverage analysis
        common_units = {}
        unit_frequency = self.execute_query("""
            SELECT 
                unit_of_measurement,
                COUNT(*) as frequency
            FROM pantry_items
            WHERE unit_of_measurement IS NOT NULL
            GROUP BY unit_of_measurement
            ORDER BY frequency DESC
            LIMIT 10
        """)
        
        for unit_info in unit_frequency:
            unit_name = unit_info['unit_of_measurement']
            frequency = unit_info['frequency']
            
            # Check if this unit exists in USDA measure_units
            unit_exists = self.execute_query("""
                SELECT COUNT(*) as count
                FROM usda_measure_units
                WHERE LOWER(name) = LOWER(%(unit_name)s)
                OR LOWER(abbreviation) = LOWER(%(unit_name)s)
                OR name ILIKE %(unit_pattern)s
            """, {"unit_name": unit_name, "unit_pattern": f"%{unit_name}%"})
            
            common_units[unit_name] = {
                "frequency": frequency,
                "exists_in_usda": unit_exists[0]['count'] > 0 if unit_exists else False
            }
        
        # Determine status
        status = "PASS" if match_percentage >= 60 else "WARNING" if match_percentage >= 30 else "FAIL"
        
        self.results.add_result("pantry_coverage", status, {
            "total_pantry_items": len(sample_pantry_items),
            "items_tested": total_tested,
            "items_matched": matched_items,
            "match_percentage": round(match_percentage, 2),
            "unit_coverage_stats": unit_coverage_stats,
            "common_units": common_units
        })
        
        if match_percentage < 50:
            self.results.add_issue(f"Low pantry item coverage: only {match_percentage:.1f}% of items matched")
            self.results.add_recommendation("Consider expanding product aliases table with more pantry item mappings")

    def test_unit_distribution(self):
        """Test 3: Unit Distribution & Outliers"""
        logger.info("🔍 Testing Unit Distribution & Outliers...")
        
        # Preferred vs rare units analysis
        unit_usage_stats = self.execute_query("""
            SELECT 
                um.name as unit_name,
                um.abbreviation,
                COUNT(DISTINCT ucm.category_id) as category_count,
                AVG(ucm.usage_percentage) as avg_usage,
                MAX(ucm.usage_percentage) as max_usage,
                COUNT(CASE WHEN ucm.is_preferred THEN 1 END) as preferred_count,
                COUNT(*) as total_mappings
            FROM usda_measure_units um
            LEFT JOIN usda_category_unit_mappings ucm ON um.id = ucm.unit_id
            GROUP BY um.id, um.name, um.abbreviation
            HAVING COUNT(*) > 0
            ORDER BY avg_usage DESC NULLS LAST
        """)
        
        # Identify preferred units (high usage, used across many categories)
        preferred_units = []
        rare_units = []
        
        for unit_stat in unit_usage_stats:
            avg_usage = unit_stat['avg_usage'] or 0
            category_count = unit_stat['category_count'] or 0
            
            if avg_usage >= 10 and category_count >= 5:
                preferred_units.append(unit_stat)
            elif avg_usage <= 1 or category_count <= 1:
                rare_units.append(unit_stat)
        
        # Duplicate semantic units detection
        logger.info("  Checking for duplicate semantic units...")
        
        potential_duplicates = self.execute_query("""
            WITH unit_variations AS (
                SELECT 
                    name,
                    abbreviation,
                    LOWER(REGEXP_REPLACE(name, '[^a-zA-Z]', '', 'g')) as clean_name
                FROM usda_measure_units
                WHERE name IS NOT NULL
            )
            SELECT 
                clean_name,
                COUNT(*) as variant_count,
                array_agg(name) as variants,
                array_agg(abbreviation) as abbreviations
            FROM unit_variations
            GROUP BY clean_name
            HAVING COUNT(*) > 1
            ORDER BY variant_count DESC
        """)
        
        # Implausible conversion identification
        logger.info("  Checking for implausible conversions...")
        
        implausible_conversions = self.execute_query("""
            SELECT 
                f.description as food_name,
                um.name as unit_name,
                fp.amount,
                fp.gram_weight,
                fp.portion_description,
                CASE 
                    WHEN fp.gram_weight > 5000 THEN 'Very heavy portion (>5kg)'
                    WHEN fp.gram_weight < 0.1 THEN 'Very light portion (<0.1g)'
                    WHEN fp.amount > 1000 THEN 'Large amount (>1000 units)'
                    WHEN fp.amount <= 0 THEN 'Invalid amount (≤0)'
                    ELSE 'OK'
                END as concern_type
            FROM usda_food_portions fp
            JOIN usda_foods f ON fp.fdc_id = f.fdc_id
            JOIN usda_measure_units um ON fp.measure_unit_id = um.id
            WHERE fp.gram_weight > 5000 
               OR fp.gram_weight < 0.1 
               OR fp.amount > 1000
               OR fp.amount <= 0
            ORDER BY fp.gram_weight DESC
            LIMIT 50
        """)
        
        # Calculate metrics
        total_units = len(unit_usage_stats)
        preferred_unit_count = len(preferred_units)
        rare_unit_count = len(rare_units)
        duplicate_groups = len(potential_duplicates)
        implausible_count = len(implausible_conversions)
        
        # Determine status
        issues = []
        if preferred_unit_count < 20:
            issues.append(f"Too few preferred units: {preferred_unit_count}")
        if rare_unit_count > total_units * 0.5:
            issues.append(f"Too many rare units: {rare_unit_count}/{total_units}")
        if duplicate_groups > 10:
            issues.append(f"Many duplicate unit groups: {duplicate_groups}")
        if implausible_count > 100:
            issues.append(f"Many implausible conversions: {implausible_count}")
            
        status = "FAIL" if len(issues) >= 2 else "WARNING" if issues else "PASS"
        
        self.results.add_result("unit_distribution", status, {
            "total_units": total_units,
            "preferred_units": preferred_unit_count,
            "rare_units": rare_unit_count,
            "duplicate_groups": duplicate_groups,
            "implausible_conversions": implausible_count,
            "preferred_unit_names": [u['unit_name'] for u in preferred_units[:10]],
            "duplicate_examples": potential_duplicates[:5],
            "implausible_examples": implausible_conversions[:5],
            "issues": issues
        })
        
        for issue in issues:
            self.results.add_issue(f"Unit distribution: {issue}")

    def test_performance_indexing(self):
        """Test 4: Performance & Indexing"""
        logger.info("🔍 Testing Performance & Indexing...")
        
        # Test key lookup scenarios with timing
        test_queries = [
            {
                "name": "food_search_by_name",
                "query": """
                    SELECT fdc_id, description 
                    FROM usda_foods 
                    WHERE description ILIKE '%chicken%' 
                    LIMIT 10
                """,
                "params": {},
                "expected_max_ms": 100
            },
            {
                "name": "category_unit_lookup",
                "query": """
                    SELECT um.name, ucm.usage_percentage
                    FROM usda_category_unit_mappings ucm
                    JOIN usda_measure_units um ON ucm.unit_id = um.id
                    WHERE ucm.category_id = 1
                    ORDER BY ucm.usage_percentage DESC
                    LIMIT 10
                """,
                "params": {},
                "expected_max_ms": 50
            },
            {
                "name": "food_portions_lookup",
                "query": """
                    SELECT fp.amount, fp.gram_weight, um.name
                    FROM usda_food_portions fp
                    JOIN usda_measure_units um ON fp.measure_unit_id = um.id
                    WHERE fp.fdc_id = (SELECT fdc_id FROM usda_foods LIMIT 1)
                """,
                "params": {},
                "expected_max_ms": 25
            },
            {
                "name": "validate_unit_function",
                "query": """
                    SELECT * FROM validate_unit_for_food('chicken breast', 'pound', NULL)
                """,
                "params": {},
                "expected_max_ms": 200
            }
        ]
        
        performance_results = []
        
        for test in test_queries:
            start_time = time.time()
            try:
                result = self.execute_query(test["query"], test["params"])
                end_time = time.time()
                
                duration_ms = (end_time - start_time) * 1000
                
                performance_results.append({
                    "test_name": test["name"],
                    "duration_ms": round(duration_ms, 2),
                    "expected_max_ms": test["expected_max_ms"],
                    "passed": duration_ms <= test["expected_max_ms"],
                    "result_count": len(result) if result else 0
                })
                
            except Exception as e:
                performance_results.append({
                    "test_name": test["name"],
                    "duration_ms": None,
                    "expected_max_ms": test["expected_max_ms"],
                    "passed": False,
                    "error": str(e)
                })
        
        # Check for required indexes
        logger.info("  Checking database indexes...")
        
        existing_indexes = self.execute_query("""
            SELECT indexname, tablename, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename IN ('usda_foods', 'usda_category_unit_mappings', 
                             'usda_food_portions', 'product_aliases')
            ORDER BY tablename, indexname
        """)
        
        required_indexes = [
            "idx_usda_foods_description_trgm",
            "idx_usda_category_unit_perf",
            "idx_usda_food_portions_fdc",
            "idx_product_aliases_pantry_name"
        ]
        
        missing_indexes = []
        for req_idx in required_indexes:
            if not any(idx['indexname'] == req_idx for idx in existing_indexes):
                missing_indexes.append(req_idx)
        
        # Determine status
        slow_queries = [r for r in performance_results if not r.get('passed', False)]
        
        issues = []
        if slow_queries:
            issues.append(f"Slow queries: {len(slow_queries)}")
        if missing_indexes:
            issues.append(f"Missing indexes: {len(missing_indexes)}")
            
        status = "FAIL" if len(issues) >= 2 else "WARNING" if issues else "PASS"
        
        self.results.add_result("performance_indexing", status, {
            "performance_tests": performance_results,
            "slow_query_count": len(slow_queries),
            "existing_indexes": len(existing_indexes),
            "missing_indexes": missing_indexes,
            "issues": issues
        })
        
        for issue in issues:
            self.results.add_issue(f"Performance: {issue}")
            
        if missing_indexes:
            self.results.add_recommendation(f"Create missing indexes: {', '.join(missing_indexes)}")

    def test_functional_validation(self):
        """Test 5: Functional Tests"""
        logger.info("🔍 Running Functional Validation Tests...")
        
        # Test specific food/unit combinations
        test_cases = [
            {"food": "chicken breast", "unit": "pound", "should_validate": True},
            {"food": "chicken breast", "unit": "ounce", "should_validate": True},
            {"food": "chicken breast", "unit": "gallon", "should_validate": False},
            {"food": "olive oil", "unit": "tablespoon", "should_validate": True},
            {"food": "olive oil", "unit": "cup", "should_validate": True},
            {"food": "olive oil", "unit": "each", "should_validate": False},
            {"food": "bread", "unit": "slice", "should_validate": True},
            {"food": "bread", "unit": "loaf", "should_validate": True},
            {"food": "bread", "unit": "fluid ounce", "should_validate": False}
        ]
        
        function_test_results = []
        
        for test_case in test_cases:
            try:
                result = self.execute_query("""
                    SELECT is_valid, confidence, reason
                    FROM validate_unit_for_food(%(food)s, %(unit)s, NULL)
                """, {"food": test_case["food"], "unit": test_case["unit"]})
                
                if result:
                    is_valid = result[0]['is_valid']
                    confidence = float(result[0]['confidence']) if result[0]['confidence'] else 0
                    reason = result[0]['reason']
                    
                    # Check if result matches expectation
                    test_passed = is_valid == test_case["should_validate"]
                    
                    function_test_results.append({
                        "food": test_case["food"],
                        "unit": test_case["unit"],
                        "expected_valid": test_case["should_validate"],
                        "actual_valid": is_valid,
                        "confidence": confidence,
                        "reason": reason,
                        "test_passed": test_passed
                    })
                else:
                    function_test_results.append({
                        "food": test_case["food"],
                        "unit": test_case["unit"],
                        "expected_valid": test_case["should_validate"],
                        "actual_valid": None,
                        "test_passed": False,
                        "error": "No result returned"
                    })
                    
            except Exception as e:
                function_test_results.append({
                    "food": test_case["food"],
                    "unit": test_case["unit"],
                    "expected_valid": test_case["should_validate"],
                    "test_passed": False,
                    "error": str(e)
                })
        
        # Test search functionality
        logger.info("  Testing search functionality...")
        
        search_test_cases = [
            {"query": "chicken", "min_results": 5},
            {"query": "olive oil", "min_results": 3},
            {"query": "bread", "min_results": 5},
            {"query": "nonexistentfooditem12345", "min_results": 0}
        ]
        
        search_test_results = []
        
        for search_case in search_test_cases:
            try:
                result = self.execute_query("""
                    SELECT * FROM search_foods_enhanced(%(query)s, NULL, NULL, 10)
                """, {"query": search_case["query"]})
                
                result_count = len(result) if result else 0
                test_passed = result_count >= search_case["min_results"]
                
                search_test_results.append({
                    "query": search_case["query"],
                    "expected_min_results": search_case["min_results"],
                    "actual_results": result_count,
                    "test_passed": test_passed
                })
                
            except Exception as e:
                search_test_results.append({
                    "query": search_case["query"],
                    "test_passed": False,
                    "error": str(e)
                })
        
        # Calculate success rates
        validation_passed = sum(1 for r in function_test_results if r.get('test_passed', False))
        validation_total = len(function_test_results)
        validation_success_rate = (validation_passed / validation_total) * 100 if validation_total > 0 else 0
        
        search_passed = sum(1 for r in search_test_results if r.get('test_passed', False))
        search_total = len(search_test_results)
        search_success_rate = (search_passed / search_total) * 100 if search_total > 0 else 0
        
        # Determine status
        status = "PASS" if validation_success_rate >= 80 and search_success_rate >= 75 else "WARNING" if validation_success_rate >= 60 else "FAIL"
        
        self.results.add_result("functional_validation", status, {
            "validation_tests": function_test_results,
            "validation_success_rate": round(validation_success_rate, 2),
            "search_tests": search_test_results,
            "search_success_rate": round(search_success_rate, 2),
            "overall_success_rate": round((validation_success_rate + search_success_rate) / 2, 2)
        })
        
        if validation_success_rate < 70:
            self.results.add_issue(f"Low validation function success rate: {validation_success_rate:.1f}%")
        if search_success_rate < 70:
            self.results.add_issue(f"Low search function success rate: {search_success_rate:.1f}%")

    def assess_production_readiness(self):
        """Test 6: Decision Rules Assessment"""
        logger.info("🔍 Assessing Production Readiness...")
        
        # Calculate overall coverage percentages and thresholds
        coverage_metrics = {}
        
        # Data completeness
        if 'structural_integrity' in self.results.results:
            structural_status = self.results.results['structural_integrity']['status']
            coverage_metrics['structural_integrity'] = 100 if structural_status == 'PASS' else 50 if structural_status == 'WARNING' else 0
        
        # Pantry coverage
        if 'pantry_coverage' in self.results.results:
            pantry_details = self.results.results['pantry_coverage']['details']
            coverage_metrics['pantry_coverage'] = pantry_details.get('match_percentage', 0)
        
        # Unit distribution quality
        if 'unit_distribution' in self.results.results:
            unit_status = self.results.results['unit_distribution']['status']
            coverage_metrics['unit_distribution'] = 100 if unit_status == 'PASS' else 60 if unit_status == 'WARNING' else 30
        
        # Performance adequacy
        if 'performance_indexing' in self.results.results:
            perf_status = self.results.results['performance_indexing']['status']
            coverage_metrics['performance'] = 100 if perf_status == 'PASS' else 70 if perf_status == 'WARNING' else 40
        
        # Functional correctness
        if 'functional_validation' in self.results.results:
            func_details = self.results.results['functional_validation']['details']
            coverage_metrics['functional'] = func_details.get('overall_success_rate', 0)
        
        # Calculate weighted overall score
        weights = {
            'structural_integrity': 0.25,
            'pantry_coverage': 0.25,
            'unit_distribution': 0.20,
            'performance': 0.15,
            'functional': 0.15
        }
        
        overall_score = sum(coverage_metrics.get(metric, 0) * weight for metric, weight in weights.items())
        
        # Determine production readiness
        if overall_score >= 80:
            readiness_level = "PRODUCTION_READY"
            readiness_message = "Database meets MVP thresholds and is ready for production use"
        elif overall_score >= 60:
            readiness_level = "CONDITIONALLY_READY"
            readiness_message = "Database meets minimum requirements but has areas for improvement"
        elif overall_score >= 40:
            readiness_level = "NEEDS_IMPROVEMENT"
            readiness_message = "Database has significant gaps that should be addressed before production"
        else:
            readiness_level = "NOT_READY"
            readiness_message = "Database has critical issues and is not suitable for production"
        
        # Generate specific recommendations based on scores
        recommendations = []
        
        if coverage_metrics.get('structural_integrity', 0) < 80:
            recommendations.append("Fix structural integrity issues: missing tables, orphaned records, NULL values")
        
        if coverage_metrics.get('pantry_coverage', 0) < 60:
            recommendations.append("Improve pantry item coverage: add more product aliases, enhance fuzzy matching")
        
        if coverage_metrics.get('unit_distribution', 0) < 70:
            recommendations.append("Clean up unit distribution: remove duplicates, fix implausible conversions")
        
        if coverage_metrics.get('performance', 0) < 80:
            recommendations.append("Optimize performance: add missing indexes, optimize slow queries")
        
        if coverage_metrics.get('functional', 0) < 75:
            recommendations.append("Fix functional issues: improve validation function accuracy, enhance search results")
        
        self.results.overall_assessment = readiness_level
        
        self.results.add_result("production_readiness", readiness_level, {
            "overall_score": round(overall_score, 2),
            "coverage_metrics": coverage_metrics,
            "readiness_level": readiness_level,
            "readiness_message": readiness_message,
            "recommendations": recommendations
        })
        
        for rec in recommendations:
            self.results.add_recommendation(rec)

    def run_all_tests(self):
        """Run the complete validation checklist"""
        logger.info("🚀 Starting USDA Database Validation Checklist")
        logger.info("=" * 60)
        
        if not self.connect_database():
            return self.results
            
        try:
            # Run all validation tests
            self.test_structural_integrity()
            self.test_pantry_coverage()
            self.test_unit_distribution()
            self.test_performance_indexing()
            self.test_functional_validation()
            self.assess_production_readiness()
            
            logger.info("✅ All validation tests completed")
            
        except Exception as e:
            logger.error(f"❌ Validation failed with error: {str(e)}")
            self.results.add_issue(f"Validation failed with error: {str(e)}")
        finally:
            if self.db_service:
                self.db_service.close()
                
        return self.results
        
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        report_lines = []
        report_lines.append("USDA Database Validation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Overall Assessment: {self.results.overall_assessment}")
        report_lines.append("")
        
        # Test Results Summary
        report_lines.append("Test Results Summary:")
        report_lines.append("-" * 30)
        
        for test_name, result in self.results.results.items():
            status_emoji = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARNING' else "❌"
            report_lines.append(f"{status_emoji} {test_name}: {result['status']}")
            
        report_lines.append("")
        
        # Detailed Results
        report_lines.append("Detailed Results:")
        report_lines.append("-" * 20)
        
        for test_name, result in self.results.results.items():
            report_lines.append(f"\n{test_name.upper()}:")
            report_lines.append(f"Status: {result['status']}")
            
            if 'details' in result:
                for key, value in result['details'].items():
                    if isinstance(value, (list, dict)) and len(str(value)) > 100:
                        report_lines.append(f"  {key}: [Complex data - {type(value).__name__}]")
                    else:
                        report_lines.append(f"  {key}: {value}")
        
        # Issues and Recommendations
        if self.results.issues:
            report_lines.append("\nIdentified Issues:")
            report_lines.append("-" * 20)
            for i, issue in enumerate(self.results.issues, 1):
                report_lines.append(f"{i}. {issue}")
        
        if self.results.recommendations:
            report_lines.append("\nRecommendations:")
            report_lines.append("-" * 16)
            for i, recommendation in enumerate(self.results.recommendations, 1):
                report_lines.append(f"{i}. {recommendation}")
        
        return "\n".join(report_lines)

def main():
    """Main execution function"""
    validator = USDADatabaseValidator()
    
    # Run validation
    results = validator.run_all_tests()
    
    # Generate and save report
    report = validator.generate_report()
    
    # Save to docs folder
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    report_filename = f"usda_database_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = docs_dir / report_filename
    
    try:
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"✅ Validation report saved to: {report_path}")
    except Exception as e:
        print(f"❌ Failed to save report: {str(e)}")
        print("\nReport content:")
        print(report)
    
    # Print summary to console
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Overall Assessment: {results.overall_assessment}")
    
    if results.issues:
        print(f"\n❌ Issues Found: {len(results.issues)}")
        for issue in results.issues[:5]:  # Show first 5 issues
            print(f"  • {issue}")
        if len(results.issues) > 5:
            print(f"  ... and {len(results.issues) - 5} more issues")
    
    if results.recommendations:
        print(f"\n💡 Recommendations: {len(results.recommendations)}")
        for rec in results.recommendations[:3]:  # Show first 3 recommendations
            print(f"  • {rec}")
        if len(results.recommendations) > 3:
            print(f"  ... and {len(results.recommendations) - 3} more recommendations")
    
    print(f"\n📋 Full report available at: {report_path}")
    
    return results.overall_assessment in ["PRODUCTION_READY", "CONDITIONALLY_READY"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)