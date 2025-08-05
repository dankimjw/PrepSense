-- Migration: Fix Critical USDA Database Issues
-- Date: 2025-08-04
-- Purpose: Address critical issues found in USDA database analysis
--
-- Issues Addressed:
-- 1. Create missing usda_food_portions table
-- 2. Create missing usda_food_nutrients table  
-- 3. Add performance indexes
-- 4. Create product alias table for better coverage
-- 5. Add trigram search for fuzzy matching
-- 6. Fix unit validation function

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================================
-- 1. CREATE MISSING CRITICAL TABLES
-- =====================================================================

-- Create usda_food_portions table (CRITICAL for unit conversions)
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

-- Create usda_food_nutrients table (for nutritional data)
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

-- =====================================================================
-- 2. CREATE PRODUCT ALIAS TABLE FOR BETTER COVERAGE
-- =====================================================================

-- This table maps common pantry item names to USDA FDC IDs
CREATE TABLE IF NOT EXISTS product_aliases (
    id SERIAL PRIMARY KEY,
    pantry_name VARCHAR(255) NOT NULL,
    usda_fdc_id INTEGER NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    match_type VARCHAR(50) DEFAULT 'manual', -- 'manual', 'fuzzy', 'exact', 'brand'
    created_by VARCHAR(50) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usda_fdc_id) REFERENCES usda_foods(fdc_id) ON DELETE CASCADE,
    UNIQUE(pantry_name)
);

-- Add some common aliases based on analysis results
INSERT INTO product_aliases (pantry_name, usda_fdc_id, confidence_score, match_type) VALUES
('colavita extra virgin olive oil', (SELECT fdc_id FROM usda_foods WHERE description ILIKE '%olive oil%' AND description ILIKE '%extra virgin%' LIMIT 1), 0.90, 'brand'),
('pacific organic low sodium chicken broth', (SELECT fdc_id FROM usda_foods WHERE description ILIKE '%chicken broth%' LIMIT 1), 0.85, 'brand'),
('trader joe''s blueberry cereal bars', (SELECT fdc_id FROM usda_foods WHERE description ILIKE '%cereal bar%' AND description ILIKE '%blueberry%' LIMIT 1), 0.80, 'brand'),
('roma tomatoes', (SELECT fdc_id FROM usda_foods WHERE description ILIKE '%tomato%' AND description ILIKE '%roma%' LIMIT 1), 0.95, 'exact')
ON CONFLICT (pantry_name) DO NOTHING;

-- =====================================================================
-- 3. ADD PERFORMANCE INDEXES
-- =====================================================================

-- Composite index for category unit lookups (addresses 72ms slow query)
CREATE INDEX IF NOT EXISTS idx_usda_category_unit_perf 
ON usda_category_unit_mappings (category_id, usage_percentage DESC, is_preferred);

-- Trigram index for fuzzy food name matching
CREATE INDEX IF NOT EXISTS idx_usda_foods_description_trgm 
ON usda_foods USING GIN (description gin_trgm_ops);

-- Index for food portions lookups
CREATE INDEX IF NOT EXISTS idx_usda_food_portions_fdc 
ON usda_food_portions (fdc_id);

CREATE INDEX IF NOT EXISTS idx_usda_food_portions_unit 
ON usda_food_portions (measure_unit_id);

-- Index for food nutrients lookups
CREATE INDEX IF NOT EXISTS idx_usda_food_nutrients_fdc 
ON usda_food_nutrients (fdc_id);

CREATE INDEX IF NOT EXISTS idx_usda_food_nutrients_nutrient 
ON usda_food_nutrients (nutrient_id);

-- Index for product aliases
CREATE INDEX IF NOT EXISTS idx_product_aliases_pantry_name 
ON product_aliases (pantry_name);

CREATE INDEX IF NOT EXISTS idx_product_aliases_fdc 
ON product_aliases (usda_fdc_id);

-- =====================================================================
-- 4. CREATE ENHANCED UNIT VALIDATION FUNCTION
-- =====================================================================

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS validate_unit_for_food(TEXT, TEXT, INTEGER);

-- Create enhanced unit validation function
CREATE OR REPLACE FUNCTION validate_unit_for_food(
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
    -- First try to find food through product aliases
    SELECT pa.usda_fdc_id INTO v_fdc_id
    FROM product_aliases pa
    WHERE LOWER(pa.pantry_name) = LOWER(p_food_name)
    LIMIT 1;
    
    -- If not found in aliases, try direct USDA search with fuzzy matching
    IF v_fdc_id IS NULL THEN
        SELECT uf.fdc_id INTO v_fdc_id
        FROM usda_foods uf
        WHERE uf.description % p_food_name  -- trigram similarity
        ORDER BY similarity(uf.description, p_food_name) DESC
        LIMIT 1;
    END IF;
    
    -- If still not found, try ILIKE search
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
       OR name ILIKE p_unit_name || '%'
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
            CASE 
                WHEN v_fdc_id IS NULL THEN 'Food not found in database'
                WHEN v_category_id IS NULL THEN 'Food category not determined'
                WHEN v_unit_id IS NULL THEN 'Unit not recognized'
                ELSE 'Could not validate unit'
            END,
            v_fdc_id,
            v_category_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 5. CREATE ENHANCED FOOD SEARCH FUNCTION
-- =====================================================================

CREATE OR REPLACE FUNCTION search_foods_enhanced(
    search_query TEXT,
    barcode TEXT DEFAULT NULL,
    category_id INTEGER DEFAULT NULL,
    limit_results INTEGER DEFAULT 20
)
RETURNS TABLE(
    fdc_id INTEGER,
    description TEXT,
    brand_info TEXT,
    category TEXT,
    barcode TEXT,
    confidence REAL,
    source TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH ranked_results AS (
        -- First: Exact barcode match
        SELECT 
            f.fdc_id,
            f.description,
            COALESCE(f.brand_owner || ' - ' || f.brand_name, f.brand_owner, f.brand_name) as brand_info,
            fc.description as category,
            f.gtin_upc as barcode,
            1.0::REAL as confidence,
            'barcode'::TEXT as source,
            1 as priority
        FROM usda_foods f
        LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
        WHERE search_foods_enhanced.barcode IS NOT NULL 
        AND f.gtin_upc = search_foods_enhanced.barcode
        
        UNION ALL
        
        -- Second: Product aliases
        SELECT 
            f.fdc_id,
            f.description,
            COALESCE(f.brand_owner || ' - ' || f.brand_name, f.brand_owner, f.brand_name) as brand_info,
            fc.description as category,
            f.gtin_upc as barcode,
            pa.confidence_score::REAL as confidence,
            'alias'::TEXT as source,
            2 as priority
        FROM product_aliases pa
        JOIN usda_foods f ON pa.usda_fdc_id = f.fdc_id
        LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
        WHERE search_query IS NOT NULL 
        AND LOWER(pa.pantry_name) = LOWER(search_query)
        
        UNION ALL
        
        -- Third: Trigram similarity search
        SELECT 
            f.fdc_id,
            f.description,
            COALESCE(f.brand_owner || ' - ' || f.brand_name, f.brand_owner, f.brand_name) as brand_info,
            fc.description as category,
            f.gtin_upc as barcode,
            similarity(f.description, search_query)::REAL as confidence,
            'fuzzy'::TEXT as source,
            3 as priority
        FROM usda_foods f
        LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
        WHERE search_query IS NOT NULL 
        AND f.description % search_query
        AND similarity(f.description, search_query) > 0.3
        
        UNION ALL
        
        -- Fourth: Full-text search
        SELECT 
            f.fdc_id,
            f.description,
            COALESCE(f.brand_owner || ' - ' || f.brand_name, f.brand_owner, f.brand_name) as brand_info,
            fc.description as category,
            f.gtin_upc as barcode,
            CASE 
                WHEN search_query IS NOT NULL THEN 
                    ts_rank(f.search_vector, plainto_tsquery('english', search_query))::REAL
                ELSE 0.5::REAL
            END as confidence,
            'fulltext'::TEXT as source,
            4 as priority
        FROM usda_foods f
        LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
        WHERE 
            (search_query IS NOT NULL AND f.search_vector @@ plainto_tsquery('english', search_query))
            OR (search_foods_enhanced.category_id IS NOT NULL AND f.food_category_id = search_foods_enhanced.category_id)
    )
    SELECT 
        r.fdc_id,
        r.description,
        r.brand_info,
        r.category,
        r.barcode,
        r.confidence,
        r.source
    FROM ranked_results r
    ORDER BY r.priority, r.confidence DESC, r.description
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 6. CREATE UNIT CONVERSION HELPER FUNCTION
-- =====================================================================

CREATE OR REPLACE FUNCTION get_unit_conversion(
    p_fdc_id INTEGER,
    p_from_unit_name TEXT,
    p_to_unit_name TEXT DEFAULT 'gram'
)
RETURNS TABLE(
    from_unit TEXT,
    to_unit TEXT,
    conversion_factor DECIMAL,
    from_amount DECIMAL,
    to_amount DECIMAL
) AS $$
DECLARE
    v_from_unit_id INTEGER;
    v_to_unit_id INTEGER;
    v_from_gram_weight DECIMAL;
    v_to_gram_weight DECIMAL;
BEGIN
    -- Get unit IDs
    SELECT id INTO v_from_unit_id
    FROM usda_measure_units
    WHERE LOWER(name) = LOWER(p_from_unit_name)
       OR LOWER(abbreviation) = LOWER(p_from_unit_name)
    LIMIT 1;
    
    SELECT id INTO v_to_unit_id
    FROM usda_measure_units
    WHERE LOWER(name) = LOWER(p_to_unit_name)
       OR LOWER(abbreviation) = LOWER(p_to_unit_name)
    LIMIT 1;
    
    -- Get gram weights from food portions
    SELECT gram_weight INTO v_from_gram_weight
    FROM usda_food_portions
    WHERE fdc_id = p_fdc_id AND measure_unit_id = v_from_unit_id
    LIMIT 1;
    
    -- For gram conversion, to_gram_weight is 1
    IF LOWER(p_to_unit_name) = 'gram' OR LOWER(p_to_unit_name) = 'g' THEN
        v_to_gram_weight := 1.0;
    ELSE
        SELECT gram_weight INTO v_to_gram_weight
        FROM usda_food_portions
        WHERE fdc_id = p_fdc_id AND measure_unit_id = v_to_unit_id
        LIMIT 1;
    END IF;
    
    -- Return conversion if both weights are available
    IF v_from_gram_weight IS NOT NULL AND v_to_gram_weight IS NOT NULL THEN
        RETURN QUERY SELECT 
            p_from_unit_name,
            p_to_unit_name,
            (v_from_gram_weight / v_to_gram_weight)::DECIMAL,
            1.0::DECIMAL,
            (v_from_gram_weight / v_to_gram_weight)::DECIMAL;
    ELSE
        -- Return null conversion
        RETURN QUERY SELECT 
            p_from_unit_name,
            p_to_unit_name,
            NULL::DECIMAL,
            NULL::DECIMAL,
            NULL::DECIMAL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 7. UPDATE EXISTING VIEW WITH ENHANCED DATA
-- =====================================================================

-- Drop and recreate enhanced food summary view
DROP VIEW IF EXISTS usda_food_summary;

CREATE OR REPLACE VIEW usda_food_summary AS
SELECT 
    f.fdc_id,
    f.description,
    f.brand_owner,
    f.brand_name,
    f.gtin_upc,
    fc.description as category,
    f.serving_size,
    f.serving_size_unit,
    f.data_type,
    
    -- Key nutrients (with error handling)
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1008 LIMIT 1) as calories,
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1003 LIMIT 1) as protein_g,
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1004 LIMIT 1) as fat_g,
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1005 LIMIT 1) as carbs_g,
    
    -- Portion info
    (SELECT COUNT(*) FROM usda_food_portions WHERE fdc_id = f.fdc_id) as portion_count,
    (SELECT array_agg(DISTINCT um.name) 
     FROM usda_food_portions fp 
     JOIN usda_measure_units um ON fp.measure_unit_id = um.id 
     WHERE fp.fdc_id = f.fdc_id
    ) as available_units,
    
    -- Alias info
    (SELECT pa.pantry_name FROM product_aliases pa WHERE pa.usda_fdc_id = f.fdc_id LIMIT 1) as common_name,
    
    f.created_at,
    f.updated_at
FROM usda_foods f
LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id;

-- =====================================================================
-- 8. CREATE ANALYSIS AND MONITORING VIEWS
-- =====================================================================

-- View for monitoring unit validation performance
CREATE OR REPLACE VIEW usda_validation_stats AS
SELECT 
    fc.description as category,
    COUNT(DISTINCT f.fdc_id) as food_count,
    COUNT(DISTINCT ucm.unit_id) as unit_count,
    COUNT(DISTINCT fp.id) as portion_count,
    ROUND(AVG(ucm.usage_percentage), 2) as avg_unit_usage,
    COUNT(CASE WHEN ucm.is_preferred THEN 1 END) as preferred_unit_count
FROM usda_food_categories fc
LEFT JOIN usda_foods f ON fc.id = f.food_category_id
LEFT JOIN usda_category_unit_mappings ucm ON fc.id = ucm.category_id
LEFT JOIN usda_food_portions fp ON f.fdc_id = fp.fdc_id
GROUP BY fc.id, fc.description
ORDER BY food_count DESC;

-- View for monitoring coverage gaps
CREATE OR REPLACE VIEW pantry_coverage_analysis AS
WITH pantry_stats AS (
    SELECT 
        LOWER(TRIM(product_name)) as clean_name,
        product_name,
        unit_of_measurement,
        COUNT(*) as frequency
    FROM pantry_items 
    WHERE product_name IS NOT NULL AND product_name != ''
    GROUP BY product_name, unit_of_measurement
),
usda_matches AS (
    SELECT 
        ps.*,
        CASE 
            WHEN pa.usda_fdc_id IS NOT NULL THEN 'alias'
            WHEN uf.fdc_id IS NOT NULL THEN 'direct'
            ELSE 'none'
        END as match_type,
        COALESCE(pa.usda_fdc_id, uf.fdc_id) as matched_fdc_id
    FROM pantry_stats ps
    LEFT JOIN product_aliases pa ON LOWER(pa.pantry_name) = ps.clean_name
    LEFT JOIN usda_foods uf ON uf.description ILIKE '%' || ps.clean_name || '%' AND pa.usda_fdc_id IS NULL
)
SELECT 
    product_name,
    unit_of_measurement,
    frequency,
    match_type,
    matched_fdc_id,
    CASE WHEN matched_fdc_id IS NOT NULL THEN TRUE ELSE FALSE END as has_usda_match
FROM usda_matches
ORDER BY frequency DESC;

-- =====================================================================
-- 9. GRANT PERMISSIONS
-- =====================================================================

-- Grant permissions on new tables to application user
-- Note: Adjust role name based on your setup
-- GRANT SELECT, INSERT, UPDATE, DELETE ON usda_food_portions TO prepsense_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON usda_food_nutrients TO prepsense_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON product_aliases TO prepsense_app;
-- GRANT USAGE ON SEQUENCE usda_food_portions_id_seq TO prepsense_app;
-- GRANT USAGE ON SEQUENCE usda_food_nutrients_id_seq TO prepsense_app;
-- GRANT USAGE ON SEQUENCE product_aliases_id_seq TO prepsense_app;

-- =====================================================================
-- 10. FINAL COMMENTS AND NEXT STEPS
-- =====================================================================

-- Migration completed. Next steps:
-- 1. Import food portion data using: python backend_gateway/scripts/import_usda_data.py
-- 2. Import food nutrient data 
-- 3. Test unit validation function
-- 4. Monitor performance with new indexes
-- 5. Add more product aliases based on user data

-- To verify migration success, run:
-- SELECT 'usda_food_portions' as table_name, COUNT(*) as row_count FROM usda_food_portions
-- UNION ALL
-- SELECT 'usda_food_nutrients', COUNT(*) FROM usda_food_nutrients
-- UNION ALL  
-- SELECT 'product_aliases', COUNT(*) FROM product_aliases;

COMMENT ON TABLE usda_food_portions IS 'USDA food portion data for unit conversions - Created by migration 001';
COMMENT ON TABLE usda_food_nutrients IS 'USDA food nutrient data - Created by migration 001';
COMMENT ON TABLE product_aliases IS 'Product name aliases for better pantry item matching - Created by migration 001';