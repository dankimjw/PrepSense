#!/usr/bin/env python3
"""
Comprehensive USDA Database Analysis for PrepSense
This script runs through a systematic evaluation of USDA tables following the database-first checklist.
"""

import asyncio
import asyncpg
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv('/Users/danielkim/_Capstone/PrepSense/.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class USDADatabaseAnalyzer:
    """Comprehensive analysis of USDA tables in PrepSense PostgreSQL database."""
    
    def __init__(self):
        """Initialize analyzer with database connection."""
        self.conn = None
        self.results = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "structural_integrity": {},
            "coverage_analysis": {},
            "unit_distribution": {},
            "performance_metrics": {},
            "functional_tests": {},
            "recommendations": []
        }
    
    async def connect(self):
        """Connect to database using environment variables."""
        db_host = os.getenv('POSTGRES_HOST')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DATABASE')
        db_user = os.getenv('POSTGRES_USER')
        db_password = os.getenv('POSTGRES_PASSWORD')
        
        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Missing required database environment variables")
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.conn = await asyncpg.connect(db_url)
        logger.info(f"Connected to database: {db_name} on {db_host}")
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            result = await self.conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name
            )
            return result
        except Exception as e:
            logger.warning(f"Error checking table {table_name}: {e}")
            return False
    
    async def analyze_structural_integrity(self):
        """Run structural integrity checks on USDA tables."""
        logger.info("🔍 Analyzing structural integrity...")
        
        integrity_results = {}
        
        # Check if USDA tables exist
        usda_tables = [
            'usda_foods', 'usda_food_categories', 'usda_measure_units',
            'usda_nutrients', 'usda_food_nutrients', 'usda_food_portions',
            'usda_category_unit_mappings'
        ]
        
        table_status = {}
        for table in usda_tables:
            exists = await self.check_table_exists(table)
            table_status[table] = exists
            if not exists:
                logger.warning(f"❌ Table {table} does not exist")
        
        integrity_results['table_existence'] = table_status
        
        # Only proceed with integrity checks if core tables exist
        if not table_status.get('usda_measure_units', False):
            integrity_results['foreign_key_health'] = "SKIPPED - usda_measure_units table not found"
            integrity_results['primary_key_density'] = "SKIPPED - usda_measure_units table not found"
            self.results['structural_integrity'] = integrity_results
            return
        
        # 1.1 Foreign-key health check
        try:
            if table_status.get('usda_food_portions') and table_status.get('usda_measure_units'):
                orphaned_portions = await self.conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM usda_food_portions fp 
                    LEFT JOIN usda_measure_units mu ON mu.id = fp.measure_unit_id 
                    WHERE mu.id IS NULL
                """)
                integrity_results['foreign_key_health'] = {
                    'orphaned_food_portions': orphaned_portions,
                    'status': 'PASS' if orphaned_portions == 0 else 'FAIL'
                }
            else:
                integrity_results['foreign_key_health'] = "SKIPPED - Required tables not found"
        except Exception as e:
            integrity_results['foreign_key_health'] = f"ERROR: {str(e)}"
        
        # 1.2 Primary-key density check
        try:
            pk_stats = await self.conn.fetchrow("""
                SELECT COUNT(*) AS total_count, COUNT(DISTINCT id) AS distinct_count 
                FROM usda_measure_units
            """)
            if pk_stats:
                integrity_results['primary_key_density'] = {
                    'total_rows': pk_stats['total_count'],
                    'distinct_ids': pk_stats['distinct_count'],
                    'density_ratio': float(pk_stats['distinct_count']) / float(pk_stats['total_count']) if pk_stats['total_count'] > 0 else 0,
                    'status': 'PASS' if pk_stats['total_count'] == pk_stats['distinct_count'] else 'FAIL'
                }
        except Exception as e:
            integrity_results['primary_key_density'] = f"ERROR: {str(e)}"
        
        # 1.3 NULL hot-spots check
        try:
            if table_status.get('usda_food_portions'):
                null_stats = await self.conn.fetchrow("""
                    SELECT 
                        COUNT(*) FILTER (WHERE gram_weight IS NULL) AS null_gram_weights,
                        COUNT(*) AS total_portions
                    FROM usda_food_portions
                """)
                if null_stats:
                    null_ratio = float(null_stats['null_gram_weights']) / float(null_stats['total_portions']) if null_stats['total_portions'] > 0 else 0
                    integrity_results['null_hotspots'] = {
                        'null_gram_weights': null_stats['null_gram_weights'],
                        'total_portions': null_stats['total_portions'],
                        'null_ratio_percent': round(null_ratio * 100, 2),
                        'status': 'PASS' if null_ratio < 0.01 else 'FAIL'
                    }
            else:
                integrity_results['null_hotspots'] = "SKIPPED - usda_food_portions table not found"
        except Exception as e:
            integrity_results['null_hotspots'] = f"ERROR: {str(e)}"
        
        self.results['structural_integrity'] = integrity_results
    
    async def analyze_coverage_for_pantry_items(self):
        """Analyze coverage of USDA data for actual pantry items."""
        logger.info("🔍 Analyzing coverage for pantry items...")
        
        coverage_results = {}
        
        try:
            # Check if pantry_items table exists
            pantry_exists = await self.check_table_exists('pantry_items')
            usda_foods_exists = await self.check_table_exists('usda_foods')
            
            if not pantry_exists:
                coverage_results['pantry_coverage'] = "SKIPPED - pantry_items table not found"
                self.results['coverage_analysis'] = coverage_results
                return
            
            if not usda_foods_exists:
                coverage_results['pantry_coverage'] = "SKIPPED - usda_foods table not found"
                self.results['coverage_analysis'] = coverage_results
                return
            
            # Get sample of pantry items
            pantry_sample = await self.conn.fetch("""
                SELECT DISTINCT LOWER(TRIM(product_name)) AS item_name, COUNT(*) as frequency
                FROM pantry_items 
                WHERE product_name IS NOT NULL AND product_name != ''
                GROUP BY LOWER(TRIM(product_name))
                ORDER BY COUNT(*) DESC
                LIMIT 100
            """)
            
            coverage_results['total_unique_pantry_items'] = len(pantry_sample)
            
            if len(pantry_sample) == 0:
                coverage_results['pantry_coverage'] = "No pantry items found"
                self.results['coverage_analysis'] = coverage_results
                return
            
            # Check USDA food matches
            matched_items = 0
            unmatched_items = []
            
            for item in pantry_sample:
                item_name = item['item_name']
                match = await self.conn.fetchval("""
                    SELECT fdc_id 
                    FROM usda_foods 
                    WHERE LOWER(description) LIKE $1
                    LIMIT 1
                """, f"%{item_name}%")
                
                if match:
                    matched_items += 1
                else:
                    unmatched_items.append(item_name)
            
            match_ratio = matched_items / len(pantry_sample) if len(pantry_sample) > 0 else 0
            
            coverage_results['pantry_coverage'] = {
                'total_sampled': len(pantry_sample),
                'matched_items': matched_items,
                'unmatched_items': len(unmatched_items),
                'match_ratio_percent': round(match_ratio * 100, 2),
                'status': 'PASS' if match_ratio >= 0.95 else 'NEEDS_IMPROVEMENT',
                'sample_unmatched': unmatched_items[:10]  # First 10 unmatched items
            }
            
            # Check unit coverage for matched foods
            if matched_items > 0 and await self.check_table_exists('usda_food_portions'):
                unit_coverage = await self.conn.fetchval("""
                    WITH matched_foods AS (
                        SELECT DISTINCT uf.fdc_id
                        FROM pantry_items pi
                        JOIN usda_foods uf ON LOWER(uf.description) LIKE '%' || LOWER(TRIM(pi.product_name)) || '%'
                        WHERE pi.product_name IS NOT NULL AND pi.product_name != ''
                        LIMIT 100
                    )
                    SELECT COUNT(*) 
                    FROM matched_foods mf
                    LEFT JOIN usda_food_portions fp ON fp.fdc_id = mf.fdc_id
                    WHERE fp.fdc_id IS NULL
                """)
                
                coverage_results['unit_coverage'] = {
                    'foods_without_portions': unit_coverage,
                    'status': 'PASS' if unit_coverage < (matched_items * 0.02) else 'NEEDS_IMPROVEMENT'
                }
        
        except Exception as e:
            coverage_results['error'] = str(e)
            logger.error(f"Error in coverage analysis: {e}")
        
        self.results['coverage_analysis'] = coverage_results
    
    async def analyze_unit_distribution(self):
        """Analyze unit distribution and identify outliers."""
        logger.info("🔍 Analyzing unit distribution...")
        
        distribution_results = {}
        
        try:
            # Check if required tables exist
            if not await self.check_table_exists('usda_category_unit_mappings'):
                distribution_results['unit_distribution'] = "SKIPPED - usda_category_unit_mappings table not found"
                self.results['unit_distribution'] = distribution_results
                return
            
            # 3.1 Check for rare units that might be set as preferred
            rare_preferred_units = await self.conn.fetch("""
                SELECT 
                    ucm.category_id,
                    ucm.unit_id,
                    ucm.usage_percentage,
                    fc.description as category_name,
                    um.name as unit_name
                FROM usda_category_unit_mappings ucm
                LEFT JOIN usda_food_categories fc ON ucm.category_id = fc.id
                LEFT JOIN usda_measure_units um ON ucm.unit_id = um.id
                WHERE ucm.usage_percentage < 0.5 AND ucm.is_preferred = TRUE
                ORDER BY ucm.usage_percentage
                LIMIT 20
            """)
            
            distribution_results['rare_preferred_units'] = [
                {
                    'category': row['category_name'],
                    'unit': row['unit_name'],
                    'usage_percent': float(row['usage_percentage'])
                }
                for row in rare_preferred_units
            ]
            
            # 3.2 Check for duplicate semantic units
            if await self.check_table_exists('usda_measure_units'):
                duplicate_units = await self.conn.fetch("""
                    SELECT LOWER(name) as unit_name, COUNT(*) as count
                    FROM usda_measure_units 
                    GROUP BY LOWER(name)
                    HAVING COUNT(*) > 1
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                
                distribution_results['duplicate_units'] = [
                    {
                        'unit_name': row['unit_name'],
                        'duplicate_count': row['count']
                    }
                    for row in duplicate_units
                ]
            
            # 3.3 Check for implausible conversions
            if await self.check_table_exists('usda_food_portions'):
                implausible_conversions = await self.conn.fetch("""
                    SELECT 
                        fp.fdc_id,
                        fp.amount,
                        fp.gram_weight,
                        um.name as unit_name,
                        uf.description as food_name
                    FROM usda_food_portions fp
                    LEFT JOIN usda_measure_units um ON fp.measure_unit_id = um.id
                    LEFT JOIN usda_foods uf ON fp.fdc_id = uf.fdc_id
                    WHERE fp.gram_weight < 0.1 OR fp.gram_weight > 5000
                    ORDER BY fp.gram_weight
                    LIMIT 20
                """)
                
                distribution_results['implausible_conversions'] = [
                    {
                        'food_name': row['food_name'],
                        'amount': float(row['amount']) if row['amount'] else None,
                        'unit': row['unit_name'],
                        'gram_weight': float(row['gram_weight']) if row['gram_weight'] else None
                    }
                    for row in implausible_conversions
                ]
        
        except Exception as e:
            distribution_results['error'] = str(e)
            logger.error(f"Error in unit distribution analysis: {e}")
        
        self.results['unit_distribution'] = distribution_results
    
    async def analyze_performance(self):
        """Analyze query performance for key operations."""
        logger.info("🔍 Analyzing performance...")
        
        performance_results = {}
        
        try:
            # Test category unit lookup performance
            if await self.check_table_exists('usda_category_unit_mappings'):
                start_time = datetime.utcnow()
                
                # Sample query - get units for a category
                await self.conn.fetch("""
                    SELECT * FROM usda_category_unit_mappings 
                    WHERE category_id = 1 
                    ORDER BY usage_percentage DESC 
                    LIMIT 5
                """)
                
                category_lookup_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['category_lookup_ms'] = round(category_lookup_time, 2)
            
            # Test unit validation function if it exists
            try:
                start_time = datetime.utcnow()
                
                validation_result = await self.conn.fetchrow("""
                    SELECT * FROM validate_unit_for_food('strawberries', 'ml')
                """)
                
                validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['unit_validation_ms'] = round(validation_time, 2)
                performance_results['validation_function_exists'] = True
                
            except Exception as e:
                performance_results['validation_function_exists'] = False
                performance_results['validation_error'] = str(e)
            
            # Performance status
            category_time = performance_results.get('category_lookup_ms', 0)
            validation_time = performance_results.get('unit_validation_ms', 0)
            
            performance_results['performance_status'] = {
                'category_lookup': 'EXCELLENT' if category_time < 10 else 'GOOD' if category_time < 50 else 'NEEDS_IMPROVEMENT',
                'unit_validation': 'EXCELLENT' if validation_time < 10 else 'GOOD' if validation_time < 50 else 'NEEDS_IMPROVEMENT'
            }
        
        except Exception as e:
            performance_results['error'] = str(e)
            logger.error(f"Error in performance analysis: {e}")
        
        self.results['performance_metrics'] = performance_results
    
    async def run_functional_tests(self):
        """Run functional tests on unit validation."""
        logger.info("🔍 Running functional tests...")
        
        test_results = {}
        test_cases = [
            {
                'name': 'strawberries_ml_invalid',
                'food': 'strawberries',
                'unit': 'ml',
                'expected_valid': False,
                'expected_confidence_max': 0.3
            },
            {
                'name': 'olive_oil_ml_valid',
                'food': 'olive oil',
                'unit': 'ml',
                'expected_valid': True,
                'expected_confidence_min': 0.5
            },
            {
                'name': 'eggs_dozen_valid',
                'food': 'eggs',
                'unit': 'dozen',
                'expected_valid': True,
                'expected_confidence_min': 0.3
            }
        ]
        
        try:
            # Check if validation function exists
            function_exists = await self.conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.routines 
                    WHERE specific_name = 'validate_unit_for_food'
                )
            """)
            
            if not function_exists:
                test_results['status'] = 'SKIPPED - validate_unit_for_food function not found'
                self.results['functional_tests'] = test_results
                return
            
            test_results['individual_tests'] = {}
            passed_tests = 0
            
            for test_case in test_cases:
                try:
                    result = await self.conn.fetchrow("""
                        SELECT * FROM validate_unit_for_food($1, $2)
                    """, test_case['food'], test_case['unit'])
                    
                    if result:
                        test_passed = True
                        reasons = []
                        
                        # Check validity expectation
                        if result['is_valid'] != test_case['expected_valid']:
                            test_passed = False
                            reasons.append(f"Expected valid={test_case['expected_valid']}, got {result['is_valid']}")
                        
                        # Check confidence bounds
                        confidence = float(result['confidence']) if result['confidence'] else 0.0
                        if test_case.get('expected_confidence_max') and confidence > test_case['expected_confidence_max']:
                            test_passed = False
                            reasons.append(f"Confidence {confidence} > expected max {test_case['expected_confidence_max']}")
                        
                        if test_case.get('expected_confidence_min') and confidence < test_case['expected_confidence_min']:
                            test_passed = False
                            reasons.append(f"Confidence {confidence} < expected min {test_case['expected_confidence_min']}")
                        
                        test_results['individual_tests'][test_case['name']] = {
                            'passed': test_passed,
                            'actual_valid': result['is_valid'],
                            'actual_confidence': confidence,
                            'suggested_units': result['suggested_units'],
                            'reason': result['reason'],
                            'failure_reasons': reasons if not test_passed else []
                        }
                        
                        if test_passed:
                            passed_tests += 1
                    
                except Exception as e:
                    test_results['individual_tests'][test_case['name']] = {
                        'passed': False,
                        'error': str(e)
                    }
            
            test_results['summary'] = {
                'total_tests': len(test_cases),
                'passed_tests': passed_tests,
                'success_rate': round((passed_tests / len(test_cases)) * 100, 1),
                'status': 'PASS' if passed_tests == len(test_cases) else 'PARTIAL' if passed_tests > 0 else 'FAIL'
            }
        
        except Exception as e:
            test_results['error'] = str(e)
            logger.error(f"Error in functional tests: {e}")
        
        self.results['functional_tests'] = test_results
    
    def generate_recommendations(self):
        """Generate recommendations based on analysis results."""
        logger.info("📋 Generating recommendations...")
        
        recommendations = []
        
        # Structural integrity recommendations
        integrity = self.results.get('structural_integrity', {})
        table_status = integrity.get('table_existence', {})
        
        missing_tables = [table for table, exists in table_status.items() if not exists]
        if missing_tables:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Missing Tables',
                'issue': f"Missing USDA tables: {', '.join(missing_tables)}",
                'action': 'Run USDA data import scripts to create missing tables',
                'impact': 'Unit validation system will not function'
            })
        
        # Foreign key health
        fk_health = integrity.get('foreign_key_health', {})
        if isinstance(fk_health, dict) and fk_health.get('status') == 'FAIL':
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Integrity',
                'issue': f"Found {fk_health['orphaned_food_portions']} orphaned food portion records",
                'action': 'Clean up orphaned records or update foreign key constraints',
                'impact': 'Data inconsistency affects unit validation accuracy'
            })
        
        # Coverage analysis recommendations
        coverage = self.results.get('coverage_analysis', {})
        pantry_coverage = coverage.get('pantry_coverage', {})
        
        if isinstance(pantry_coverage, dict):
            match_ratio = pantry_coverage.get('match_ratio_percent', 0)
            if match_ratio < 95:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Coverage',
                    'issue': f"Only {match_ratio}% of pantry items match USDA foods",
                    'action': 'Create alias table for pantry → FDC lookup gaps or improve matching algorithm',
                    'impact': 'Poor unit validation coverage for actual user items'
                })
        
        # Performance recommendations
        performance = self.results.get('performance_metrics', {})
        perf_status = performance.get('performance_status', {})
        
        if perf_status.get('category_lookup') == 'NEEDS_IMPROVEMENT':
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Performance',
                'issue': f"Category lookup taking {performance.get('category_lookup_ms', 0)}ms",
                'action': 'Add index on (category_id, usage_percentage DESC)',
                'impact': 'Slow API response times'
            })
        
        # Functional test recommendations
        functional = self.results.get('functional_tests', {})
        if isinstance(functional, dict) and functional.get('summary', {}).get('status') != 'PASS':
            success_rate = functional.get('summary', {}).get('success_rate', 0)
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Functionality',
                'issue': f"Unit validation tests {success_rate}% success rate",
                'action': 'Debug and fix unit validation function logic',
                'impact': 'Unit validation returning incorrect results'
            })
        
        # Overall system status
        critical_issues = len([r for r in recommendations if r['priority'] == 'HIGH'])
        if critical_issues == 0 and match_ratio >= 95:
            recommendations.append({
                'priority': 'INFO',
                'category': 'System Status',
                'issue': 'USDA database appears production-ready',
                'action': 'Wire smart_unit_validator.py to current database',
                'impact': 'Ready for MVP deployment'
            })
        elif critical_issues > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'System Status',
                'issue': f"Found {critical_issues} critical issues",
                'action': 'Schedule data-quality remediation sprint',
                'impact': 'System not ready for production use'
            })
        
        self.results['recommendations'] = recommendations
    
    async def run_complete_analysis(self):
        """Run the complete database analysis."""
        logger.info("🚀 Starting comprehensive USDA database analysis...")
        
        try:
            await self.connect()
            
            await self.analyze_structural_integrity()
            await self.analyze_coverage_for_pantry_items()
            await self.analyze_unit_distribution()
            await self.analyze_performance()
            await self.run_functional_tests()
            
            self.generate_recommendations()
            
            logger.info("✅ Analysis completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            self.results['error'] = str(e)
            raise
        finally:
            await self.close()
        
        return self.results
    
    def save_results(self, output_file: str = None):
        """Save analysis results to JSON file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/Users/danielkim/_Capstone/PrepSense/db/usda_analysis_{timestamp}.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"📊 Analysis results saved to: {output_path}")
        return output_path


async def main():
    """Main entry point for the analysis."""
    analyzer = USDADatabaseAnalyzer()
    
    try:
        results = await analyzer.run_complete_analysis()
        output_file = analyzer.save_results()
        
        # Print summary
        print("\n" + "="*80)
        print("📊 USDA DATABASE ANALYSIS SUMMARY")
        print("="*80)
        
        # Table existence
        table_status = results.get('structural_integrity', {}).get('table_existence', {})
        missing_tables = [table for table, exists in table_status.items() if not exists]
        
        if missing_tables:
            print(f"❌ Missing Tables: {', '.join(missing_tables)}")
        else:
            print("✅ All USDA tables exist")
        
        # Coverage
        coverage = results.get('coverage_analysis', {}).get('pantry_coverage', {})
        if isinstance(coverage, dict):
            match_ratio = coverage.get('match_ratio_percent', 0)
            print(f"📈 Pantry Item Coverage: {match_ratio}%")
        
        # Performance
        performance = results.get('performance_metrics', {})
        if 'category_lookup_ms' in performance:
            print(f"⚡ Category Lookup: {performance['category_lookup_ms']}ms")
        if 'unit_validation_ms' in performance:
            print(f"⚡ Unit Validation: {performance['unit_validation_ms']}ms")
        
        # Functional tests
        functional = results.get('functional_tests', {})
        if isinstance(functional, dict) and 'summary' in functional:
            success_rate = functional['summary'].get('success_rate', 0)
            print(f"🧪 Functional Tests: {success_rate}% success rate")
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
        
        if high_priority:
            print(f"\n🚨 HIGH PRIORITY ISSUES ({len(high_priority)}):")
            for rec in high_priority:
                print(f"  • {rec['issue']}")
                print(f"    Action: {rec['action']}")
        else:
            print("\n✅ No high-priority issues found")
        
        print(f"\n📄 Full report saved to: {output_file}")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())