-- USDA Database Validation SQL Queries
-- These queries were used in the comprehensive validation process
-- Run these to verify database state and identify issues

-- =====================================================================
-- 1. STRUCTURAL INTEGRITY QUERIES
-- =====================================================================

-- Check core table row counts
SELECT 
    'usda_foods' as table_name,
    COUNT(*) as row_count,
    CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ EMPTY' END as status
FROM usda_foods
UNION ALL
SELECT 
    'usda_food_categories',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ EMPTY' END
FROM usda_food_categories
UNION ALL
SELECT 
    'usda_measure_units',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ EMPTY' END
FROM usda_measure_units
UNION ALL
SELECT 
    'usda_category_unit_mappings',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ EMPTY' END
FROM usda_category_unit_mappings
UNION ALL
SELECT 
    'usda_food_portions',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ CRITICAL - EMPTY' END
FROM usda_food_portions
UNION ALL
SELECT 
    'usda_food_nutrients',
    COUNT(*), 
    CASE WHEN COUNT(*) > 0 THEN '✅ OK' ELSE '❌ CRITICAL - EMPTY' END
FROM usda_food_nutrients;

-- Check for orphaned foods (foods without valid categories)
SELECT 
    COUNT(*) as orphaned_foods,
    CASE WHEN COUNT(*) = 0 THEN '✅ No orphaned foods' 
         ELSE '⚠️  Found orphaned foods' END as status
FROM usda_foods f
LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
WHERE f.food_category_id IS NOT NULL AND fc.id IS NULL;

-- Check NULL percentages in critical columns
SELECT 
    'Food descriptions' as column_check,
    COUNT(CASE WHEN description IS NULL THEN 1 END) as null_count,
    COUNT(*) as total_count,
    ROUND((COUNT(CASE WHEN description IS NULL THEN 1 END) * 100.0 / COUNT(*)), 2) as null_percentage,
    CASE WHEN (COUNT(CASE WHEN description IS NULL THEN 1 END) * 100.0 / COUNT(*)) < 5 
         THEN '✅ OK' ELSE '❌ HIGH NULL %' END as status
FROM usda_foods
UNION ALL
SELECT 
    'Food categories',
    COUNT(CASE WHEN food_category_id IS NULL THEN 1 END),
    COUNT(*),
    ROUND((COUNT(CASE WHEN food_category_id IS NULL THEN 1 END) * 100.0 / COUNT(*)), 2),
    CASE WHEN (COUNT(CASE WHEN food_category_id IS NULL THEN 1 END) * 100.0 / COUNT(*)) < 20 
         THEN '✅ OK' ELSE '❌ CRITICAL NULL %' END
FROM usda_foods;

-- =====================================================================
-- 2. PANTRY COVERAGE QUERIES  
-- =====================================================================

-- Get sample pantry items for coverage testing
SELECT DISTINCT 
    product_name,
    unit_of_measurement,
    COUNT(*) as frequency
FROM pantry_items 
WHERE product_name IS NOT NULL 
AND LENGTH(TRIM(product_name)) > 2
GROUP BY product_name, unit_of_measurement
ORDER BY frequency DESC
LIMIT 20;

-- Test fuzzy matching for sample pantry items
SELECT 
    'chicken breast' as search_term,
    COUNT(*) as usda_matches,
    CASE WHEN COUNT(*) > 0 THEN '✅ Found matches' ELSE '❌ No matches' END as status
FROM usda_foods
WHERE description ILIKE '%chicken breast%'
UNION ALL
SELECT 
    'olive oil',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN '✅ Found matches' ELSE '❌ No matches' END
FROM usda_foods  
WHERE description ILIKE '%olive oil%'
UNION ALL
SELECT 
    'bread',
    COUNT(*),
    CASE WHEN COUNT(*) > 0 THEN '✅ Found matches' ELSE '❌ No matches' END
FROM usda_foods
WHERE description ILIKE '%bread%';

-- Check common pantry units recognition
SELECT 
    unit_of_measurement,
    COUNT(*) as pantry_frequency,
    CASE WHEN EXISTS (
        SELECT 1 FROM usda_measure_units 
        WHERE LOWER(name) = LOWER(unit_of_measurement) 
           OR LOWER(abbreviation) = LOWER(unit_of_measurement)
    ) THEN '✅ Recognized' ELSE '❌ Not recognized' END as recognition_status
FROM pantry_items
WHERE unit_of_measurement IS NOT NULL
GROUP BY unit_of_measurement
ORDER BY pantry_frequency DESC
LIMIT 10;

-- =====================================================================
-- 3. UNIT DISTRIBUTION QUERIES
-- =====================================================================

-- Unit usage distribution analysis
SELECT 
    um.name as unit_name,
    um.abbreviation,
    COUNT(DISTINCT ucm.category_id) as category_count,
    AVG(ucm.usage_percentage) as avg_usage_percentage,
    COUNT(CASE WHEN ucm.is_preferred THEN 1 END) as preferred_count,
    CASE 
        WHEN AVG(ucm.usage_percentage) >= 10 AND COUNT(DISTINCT ucm.category_id) >= 2 
        THEN '✅ Well-used'
        WHEN AVG(ucm.usage_percentage) < 1 
        THEN '⚠️  Rare unit'
        ELSE '◯ Moderate use'
    END as usage_status
FROM usda_measure_units um
LEFT JOIN usda_category_unit_mappings ucm ON um.id = ucm.unit_id
GROUP BY um.id, um.name, um.abbreviation
ORDER BY avg_usage_percentage DESC NULLS LAST;

-- Check for potential duplicate units
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
    array_agg(name) as variants,
    CASE WHEN COUNT(*) > 1 THEN '⚠️  Potential duplicates' ELSE '✅ Unique' END as status
FROM normalized_units
GROUP BY clean_name
HAVING COUNT(*) > 1
ORDER BY variant_count DESC;

-- =====================================================================
-- 4. PERFORMANCE QUERIES
-- =====================================================================

-- Check for existing indexes on critical tables
SELECT 
    indexname,
    tablename,
    CASE 
        WHEN indexname LIKE '%description%' THEN '✅ Search index'
        WHEN indexname LIKE '%category%' THEN '✅ Category index'
        WHEN indexname LIKE '%fdc%' THEN '✅ FDC index'
        ELSE '◯ Other index'
    END as index_type
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('usda_foods', 'usda_category_unit_mappings', 'usda_food_portions')
ORDER BY tablename, indexname;

-- =====================================================================
-- 5. FUNCTIONAL VALIDATION QUERIES
-- =====================================================================

-- Test the validation function with various inputs
SELECT 
    'chicken breast' as food_item,
    'pound' as unit_tested,
    is_valid,
    confidence,
    reason,
    CASE WHEN is_valid THEN '✅ Valid' ELSE '❌ Invalid' END as result_status
FROM validate_unit_for_food('chicken breast', 'pound', NULL)
UNION ALL
SELECT 
    'olive oil',
    'tablespoon',
    is_valid,
    confidence,
    reason,
    CASE WHEN is_valid THEN '✅ Valid' ELSE '❌ Invalid' END
FROM validate_unit_for_food('olive oil', 'tablespoon', NULL)
UNION ALL
SELECT 
    'bread',
    'slice',
    is_valid,
    confidence, 
    reason,
    CASE WHEN is_valid THEN '✅ Valid' ELSE '❌ Invalid' END
FROM validate_unit_for_food('bread', 'slice', NULL);

-- Test search functionality
SELECT 
    'chicken' as search_term,
    COUNT(*) as result_count,
    CASE WHEN COUNT(*) >= 5 THEN '✅ Good results' 
         WHEN COUNT(*) > 0 THEN '⚠️  Few results'
         ELSE '❌ No results' END as search_status
FROM usda_foods 
WHERE description ILIKE '%chicken%'
UNION ALL
SELECT 
    'bread',
    COUNT(*),
    CASE WHEN COUNT(*) >= 5 THEN '✅ Good results'
         WHEN COUNT(*) > 0 THEN '⚠️  Few results' 
         ELSE '❌ No results' END
FROM usda_foods
WHERE description ILIKE '%bread%';

-- =====================================================================
-- 6. PRODUCTION READINESS ASSESSMENT QUERIES
-- =====================================================================

-- Summary query for overall database health
WITH health_metrics AS (
    SELECT 
        (SELECT COUNT(*) FROM usda_foods) as total_foods,
        (SELECT COUNT(*) FROM usda_food_portions) as total_portions,
        (SELECT COUNT(*) FROM usda_food_nutrients) as total_nutrients,
        (SELECT COUNT(CASE WHEN food_category_id IS NULL THEN 1 END) FROM usda_foods) as uncategorized_foods,
        (SELECT COUNT(*) FROM usda_foods) as total_foods_for_pct
)
SELECT 
    'Total Foods' as metric,
    total_foods as value,
    CASE WHEN total_foods > 10000 THEN '✅ Excellent' 
         WHEN total_foods > 1000 THEN '⚠️  Adequate' 
         ELSE '❌ Insufficient' END as status
FROM health_metrics
UNION ALL
SELECT 
    'Food Portions',
    total_portions,
    CASE WHEN total_portions > 10000 THEN '✅ Excellent'
         WHEN total_portions > 1000 THEN '⚠️  Adequate'
         ELSE '❌ CRITICAL - Missing' END
FROM health_metrics
UNION ALL
SELECT 
    'Categorization Rate',
    total_foods_for_pct - uncategorized_foods,
    CASE WHEN (total_foods_for_pct - uncategorized_foods) * 100.0 / total_foods_for_pct > 90 
         THEN '✅ Excellent'
         WHEN (total_foods_for_pct - uncategorized_foods) * 100.0 / total_foods_for_pct > 70 
         THEN '⚠️  Adequate'
         ELSE '❌ Poor categorization' END
FROM health_metrics;

-- Final recommendation query
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM usda_food_portions) = 0 
        THEN '🔴 NOT READY - Missing critical portion data'
        WHEN (SELECT COUNT(CASE WHEN food_category_id IS NULL THEN 1 END) * 100.0 / COUNT(*) FROM usda_foods) > 50 
        THEN '🟡 MAJOR ISSUES - Poor categorization'
        WHEN (SELECT COUNT(*) FROM usda_food_portions) < 1000 
        THEN '🟡 LIMITED - Insufficient portion data'
        ELSE '🟢 READY - Database appears functional'
    END as production_readiness_assessment;