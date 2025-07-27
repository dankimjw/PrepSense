-- USDA FoodData Central Integration Tables for PrepSense
-- This schema integrates USDA's comprehensive food database with PrepSense's pantry management system

-- Main food reference table
CREATE TABLE IF NOT EXISTS usda_foods (
    fdc_id INTEGER PRIMARY KEY,  -- USDA FoodData Central ID
    description TEXT NOT NULL,    -- Food name/description
    data_type VARCHAR(50),        -- 'branded_food', 'survey_fndds_food', 'sr_legacy_food', etc.
    food_category_id INTEGER,
    publication_date DATE,
    
    -- Branded food specific fields
    brand_owner VARCHAR(255),
    brand_name VARCHAR(255),
    gtin_upc VARCHAR(20),        -- Barcode for branded products
    ingredients TEXT,
    serving_size DECIMAL(10,2),
    serving_size_unit VARCHAR(50),
    
    -- Search optimization
    search_vector tsvector,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (food_category_id) REFERENCES usda_food_categories(id)
);

-- Food categories table
CREATE TABLE IF NOT EXISTS usda_food_categories (
    id INTEGER PRIMARY KEY,
    code VARCHAR(10),
    description VARCHAR(255) NOT NULL,
    parent_category_id INTEGER,
    
    FOREIGN KEY (parent_category_id) REFERENCES usda_food_categories(id)
);

-- Measure units reference table
CREATE TABLE IF NOT EXISTS usda_measure_units (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(20),
    unit_type VARCHAR(50)  -- 'volume', 'weight', 'count', 'portion', 'package'
);

-- Nutrients reference table
CREATE TABLE IF NOT EXISTS usda_nutrients (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    unit_name VARCHAR(50),
    nutrient_nbr VARCHAR(10),
    rank INTEGER
);

-- Food nutrients junction table (simplified for key nutrients)
CREATE TABLE IF NOT EXISTS usda_food_nutrients (
    id SERIAL PRIMARY KEY,
    fdc_id INTEGER NOT NULL,
    nutrient_id INTEGER NOT NULL,
    amount DECIMAL(15,5),
    
    FOREIGN KEY (fdc_id) REFERENCES usda_foods(fdc_id),
    FOREIGN KEY (nutrient_id) REFERENCES usda_nutrients(id),
    UNIQUE(fdc_id, nutrient_id)
);

-- Food portions table (serving sizes)
CREATE TABLE IF NOT EXISTS usda_food_portions (
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

-- Link table to connect USDA foods with PrepSense pantry items
CREATE TABLE IF NOT EXISTS pantry_item_usda_mapping (
    id SERIAL PRIMARY KEY,
    pantry_item_id INTEGER NOT NULL,
    fdc_id INTEGER NOT NULL,
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00 matching confidence
    mapping_source VARCHAR(50),     -- 'barcode', 'name_match', 'manual', 'ocr'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (pantry_item_id) REFERENCES pantry_items(id) ON DELETE CASCADE,
    FOREIGN KEY (fdc_id) REFERENCES usda_foods(fdc_id),
    UNIQUE(pantry_item_id, fdc_id)
);

-- Indexes for performance
CREATE INDEX idx_usda_foods_search ON usda_foods USING GIN(search_vector);
CREATE INDEX idx_usda_foods_gtin ON usda_foods(gtin_upc) WHERE gtin_upc IS NOT NULL;
CREATE INDEX idx_usda_foods_category ON usda_foods(food_category_id);
CREATE INDEX idx_usda_foods_brand ON usda_foods(brand_owner) WHERE brand_owner IS NOT NULL;
CREATE INDEX idx_food_nutrients_fdc ON usda_food_nutrients(fdc_id);
CREATE INDEX idx_food_portions_fdc ON usda_food_portions(fdc_id);

-- Full text search trigger
CREATE OR REPLACE FUNCTION usda_foods_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.brand_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.brand_owner, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.ingredients, '')), 'D');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_usda_foods_search 
    BEFORE INSERT OR UPDATE ON usda_foods
    FOR EACH ROW EXECUTE FUNCTION usda_foods_search_trigger();

-- Helper view for common queries
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
    -- Key nutrients (will need nutrient IDs from import)
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1008) as calories,
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1003) as protein_g,
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1004) as fat_g,
    (SELECT amount FROM usda_food_nutrients WHERE fdc_id = f.fdc_id AND nutrient_id = 1005) as carbs_g
FROM usda_foods f
LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id;

-- Function to search USDA foods
CREATE OR REPLACE FUNCTION search_usda_foods(
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
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.fdc_id,
        f.description,
        COALESCE(f.brand_owner || ' - ' || f.brand_name, f.brand_owner, f.brand_name) as brand_info,
        fc.description as category,
        f.gtin_upc as barcode,
        CASE 
            WHEN f.gtin_upc = search_usda_foods.barcode THEN 1.0
            WHEN search_query IS NOT NULL THEN 
                ts_rank(f.search_vector, plainto_tsquery('english', search_query))
            ELSE 0.5
        END as rank
    FROM usda_foods f
    LEFT JOIN usda_food_categories fc ON f.food_category_id = fc.id
    WHERE 
        (search_usda_foods.barcode IS NOT NULL AND f.gtin_upc = search_usda_foods.barcode)
        OR (search_query IS NOT NULL AND f.search_vector @@ plainto_tsquery('english', search_query))
        OR (search_usda_foods.category_id IS NOT NULL AND f.food_category_id = search_usda_foods.category_id)
    ORDER BY rank DESC, f.description
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function to match pantry item with USDA food
CREATE OR REPLACE FUNCTION match_pantry_item_to_usda(
    pantry_name TEXT,
    pantry_barcode TEXT DEFAULT NULL
)
RETURNS TABLE(
    fdc_id INTEGER,
    description TEXT,
    confidence_score DECIMAL(3,2),
    match_reason TEXT
) AS $$
BEGIN
    -- First try exact barcode match
    IF pantry_barcode IS NOT NULL THEN
        RETURN QUERY
        SELECT 
            f.fdc_id,
            f.description,
            1.00::DECIMAL(3,2) as confidence_score,
            'barcode_match'::TEXT as match_reason
        FROM usda_foods f
        WHERE f.gtin_upc = pantry_barcode
        LIMIT 1;
        
        IF FOUND THEN
            RETURN;
        END IF;
    END IF;
    
    -- Try text search
    RETURN QUERY
    SELECT 
        f.fdc_id,
        f.description,
        LEAST(ts_rank(f.search_vector, plainto_tsquery('english', pantry_name)), 0.99)::DECIMAL(3,2) as confidence_score,
        'name_match'::TEXT as match_reason
    FROM usda_foods f
    WHERE f.search_vector @@ plainto_tsquery('english', pantry_name)
    ORDER BY ts_rank(f.search_vector, plainto_tsquery('english', pantry_name)) DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;