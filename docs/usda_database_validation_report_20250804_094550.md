USDA Database Validation Report
==================================================
Generated: 2025-08-04 09:45:50
Overall Assessment: NOT_READY

Test Results Summary:
------------------------------
❌ structural_integrity: FAIL
✅ pantry_coverage: PASS
❌ unit_distribution: FAIL
⚠️ performance_indexing: WARNING
❌ functional_validation: FAIL
❌ production_readiness: NOT_READY

Detailed Results:
--------------------

STRUCTURAL_INTEGRITY:
Status: FAIL
  orphaned_foods: 0
  orphaned_mappings: 0
  orphaned_portions: 0
  table_stats: [Complex data - dict]
  null_hotspots: {'usda_foods.food_category_id': 14475}
  issues: ['NULL hotspots in 1 columns']

PANTRY_COVERAGE:
Status: PASS
  total_pantry_items: 100
  items_tested: 20
  items_matched: 13
  match_percentage: 65.0
  unit_coverage_stats: {'ea': 0, 'can': 0, 'kg': 0, 'g': 0, 'lb': 0, 'pint': 0}
  common_units: [Complex data - dict]

UNIT_DISTRIBUTION:
Status: FAIL
  total_units: 122
  preferred_units: 4
  rare_units: 110
  duplicate_groups: 0
  implausible_conversions: 0
  preferred_unit_names: ['cup', 'piece', 'oz', 'serving']
  duplicate_examples: []
  implausible_examples: []
  issues: ['Too few preferred units: 4', 'Too many rare units: 110/122']

PERFORMANCE_INDEXING:
Status: WARNING
  performance_tests: [Complex data - list]
  slow_query_count: 2
  existing_indexes: 16
  missing_indexes: []
  issues: ['Slow queries: 2']

FUNCTIONAL_VALIDATION:
Status: FAIL
  validation_tests: [Complex data - list]
  validation_success_rate: 33.33
  search_tests: [Complex data - list]
  search_success_rate: 25.0
  overall_success_rate: 29.17

PRODUCTION_READINESS:
Status: NOT_READY
  overall_score: 37.13
  coverage_metrics: [Complex data - dict]
  readiness_level: NOT_READY
  readiness_message: Database has critical issues and is not suitable for production
  recommendations: [Complex data - list]

Identified Issues:
--------------------
1. Structural integrity: NULL hotspots in 1 columns
2. Unit distribution: Too few preferred units: 4
3. Unit distribution: Too many rare units: 110/122
4. Performance: Slow queries: 2
5. Low validation function success rate: 33.3%
6. Low search function success rate: 25.0%

Recommendations:
----------------
1. Fix structural integrity issues: missing tables, orphaned records, NULL values
2. Clean up unit distribution: remove duplicates, fix implausible conversions
3. Optimize performance: add missing indexes, optimize slow queries
4. Fix functional issues: improve validation function accuracy, enhance search results