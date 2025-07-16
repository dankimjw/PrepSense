-- Food Categorization Cache Tables for PrepSense
-- These tables store food item information from external APIs
-- and learn from user corrections over time

-- Food items cache table
-- Stores normalized food item information from various sources
CREATE TABLE IF NOT EXISTS food_items_cache (
    item_id SERIAL PRIMARY KEY,
    normalized_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    brand VARCHAR(255),
    barcode VARCHAR(50),
    -- Nutrition information (optional)
    calories_per_100g DECIMAL(10, 2),
    protein_per_100g DECIMAL(10, 2),
    carbs_per_100g DECIMAL(10, 2),
    fat_per_100g DECIMAL(10, 2),
    -- Source information
    data_source VARCHAR(50) NOT NULL, -- 'usda', 'openfoodfacts', 'spoonacular', 'user_verified'
    source_id VARCHAR(255), -- ID in the source system
    confidence_score DECIMAL(3, 2) DEFAULT 0.5, -- 0-1 confidence in categorization
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,
    -- Create unique constraint on normalized name and brand
    CONSTRAINT unique_food_item UNIQUE (normalized_name, brand)
);

-- Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_food_items_normalized_name ON food_items_cache(normalized_name);
CREATE INDEX IF NOT EXISTS idx_food_items_category ON food_items_cache(category);
CREATE INDEX IF NOT EXISTS idx_food_items_barcode ON food_items_cache(barcode);
CREATE INDEX IF NOT EXISTS idx_food_items_source ON food_items_cache(data_source);
CREATE INDEX IF NOT EXISTS idx_food_items_metadata ON food_items_cache USING GIN(metadata);

-- Food unit mappings table
-- Stores valid units for each food item with conversion factors
CREATE TABLE IF NOT EXISTS food_unit_mappings (
    mapping_id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES food_items_cache(item_id) ON DELETE CASCADE,
    unit VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    conversion_to_grams DECIMAL(10, 4), -- NULL for non-weight units
    conversion_to_ml DECIMAL(10, 4), -- NULL for non-volume units
    typical_amount DECIMAL(10, 2), -- Typical amount in this unit
    confidence_score DECIMAL(3, 2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_item_unit UNIQUE (item_id, unit)
);

CREATE INDEX IF NOT EXISTS idx_food_unit_mappings_item ON food_unit_mappings(item_id);

-- User corrections table
-- Tracks when users correct categorizations or units
CREATE TABLE IF NOT EXISTS food_categorization_corrections (
    correction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    original_name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    -- Original values
    original_category VARCHAR(100),
    original_unit VARCHAR(50),
    -- Corrected values
    corrected_category VARCHAR(100),
    corrected_unit VARCHAR(50),
    -- Additional context
    correction_type VARCHAR(50) NOT NULL, -- 'category', 'unit', 'both'
    confidence_boost DECIMAL(3, 2) DEFAULT 0.1, -- How much to boost confidence
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_corrections_normalized_name ON food_categorization_corrections(normalized_name);
CREATE INDEX IF NOT EXISTS idx_corrections_user ON food_categorization_corrections(user_id);

-- Food search history table
-- Tracks searches to identify popular items and cache misses
CREATE TABLE IF NOT EXISTS food_search_history (
    search_id SERIAL PRIMARY KEY,
    search_term VARCHAR(255) NOT NULL,
    normalized_term VARCHAR(255) NOT NULL,
    found_in_cache BOOLEAN DEFAULT FALSE,
    data_source VARCHAR(50), -- Which API found it
    response_time_ms INTEGER,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_history_term ON food_search_history(normalized_term);
CREATE INDEX IF NOT EXISTS idx_search_history_date ON food_search_history(created_at);

-- Common food aliases table
-- Maps common misspellings and variations to normalized names
CREATE TABLE IF NOT EXISTS food_aliases (
    alias_id SERIAL PRIMARY KEY,
    alias VARCHAR(255) NOT NULL UNIQUE,
    normalized_name VARCHAR(255) NOT NULL,
    confidence_score DECIMAL(3, 2) DEFAULT 0.8,
    created_by VARCHAR(50) DEFAULT 'system', -- 'system', 'user', 'ml_model'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_food_aliases_alias ON food_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_food_aliases_normalized ON food_aliases(normalized_name);

-- API rate limits tracking
CREATE TABLE IF NOT EXISTS api_rate_limits (
    api_name VARCHAR(50) PRIMARY KEY,
    requests_today INTEGER DEFAULT 0,
    daily_limit INTEGER NOT NULL,
    last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN DEFAULT TRUE
);

-- Insert default API limits
INSERT INTO api_rate_limits (api_name, daily_limit) VALUES
    ('usda', 1000),
    ('spoonacular', 150),
    ('openfoodfacts', 10000)
ON CONFLICT (api_name) DO NOTHING;

-- Function to update confidence scores based on user corrections
CREATE OR REPLACE FUNCTION update_food_confidence_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the confidence score for the food item
    UPDATE food_items_cache
    SET confidence_score = LEAST(
        confidence_score + NEW.confidence_boost,
        1.0  -- Cap at 1.0
    ),
    updated_at = CURRENT_TIMESTAMP
    WHERE normalized_name = NEW.normalized_name;
    
    -- If category was corrected, update it
    IF NEW.corrected_category IS NOT NULL THEN
        UPDATE food_items_cache
        SET category = NEW.corrected_category,
            data_source = 'user_verified'
        WHERE normalized_name = NEW.normalized_name;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- Create trigger for confidence updates
CREATE TRIGGER update_confidence_on_correction
AFTER INSERT ON food_categorization_corrections
FOR EACH ROW EXECUTE FUNCTION update_food_confidence_score();

-- View for most corrected items (helps identify problem areas)
CREATE OR REPLACE VIEW most_corrected_foods AS
SELECT 
    normalized_name,
    COUNT(*) as correction_count,
    MAX(created_at) as last_corrected,
    array_agg(DISTINCT corrected_category) as suggested_categories,
    array_agg(DISTINCT corrected_unit) as suggested_units
FROM food_categorization_corrections
GROUP BY normalized_name
ORDER BY correction_count DESC;

-- View for API usage statistics
CREATE OR REPLACE VIEW api_usage_stats AS
SELECT 
    api_name,
    requests_today,
    daily_limit,
    ROUND((requests_today::numeric / daily_limit) * 100, 2) as usage_percentage,
    is_available,
    last_reset
FROM api_rate_limits
ORDER BY usage_percentage DESC;