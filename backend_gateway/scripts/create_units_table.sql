-- Create Units table with category-based constraints
-- This enforces unit compatibility at the database level

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS item_unit_mappings CASCADE;
DROP TABLE IF EXISTS units CASCADE;
DROP TYPE IF EXISTS unit_category CASCADE;

-- Create enum for unit categories
CREATE TYPE unit_category AS ENUM ('mass', 'volume', 'count');

-- Create the Units table
CREATE TABLE units (
    id VARCHAR(10) PRIMARY KEY,  -- e.g., 'ml', 'g', 'ea'
    label VARCHAR(50) NOT NULL,   -- e.g., 'millilitre', 'gram', 'each'
    category unit_category NOT NULL,
    to_base_factor DECIMAL(10, 6) NOT NULL DEFAULT 1.0,  -- multiply by this to get base unit
    is_base_unit BOOLEAN NOT NULL DEFAULT FALSE,
    is_metric BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 999,  -- for UI ordering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for category filtering
CREATE INDEX idx_units_category ON units(category);
CREATE INDEX idx_units_display_order ON units(display_order);

-- Insert base units (these are the canonical storage units)
INSERT INTO units (id, label, category, to_base_factor, is_base_unit, display_order) VALUES
    -- Base units
    ('g', 'gram', 'mass', 1.0, TRUE, 1),
    ('ml', 'millilitre', 'volume', 1.0, TRUE, 1),
    ('ea', 'each', 'count', 1.0, TRUE, 1);

-- Insert common metric units
INSERT INTO units (id, label, category, to_base_factor, display_order) VALUES
    -- Mass - Metric
    ('mg', 'milligram', 'mass', 0.001, 2),
    ('kg', 'kilogram', 'mass', 1000.0, 3),
    
    -- Volume - Metric
    ('l', 'litre', 'volume', 1000.0, 2),
    ('dl', 'decilitre', 'volume', 100.0, 3),
    ('cl', 'centilitre', 'volume', 10.0, 4);

-- Insert common US units
INSERT INTO units (id, label, category, to_base_factor, is_metric, display_order) VALUES
    -- Mass - US
    ('oz', 'ounce', 'mass', 28.3495, FALSE, 10),
    ('lb', 'pound', 'mass', 453.592, FALSE, 11),
    
    -- Volume - US
    ('tsp', 'teaspoon', 'volume', 4.92892, FALSE, 10),
    ('tbsp', 'tablespoon', 'volume', 14.7868, FALSE, 11),
    ('floz', 'fluid ounce', 'volume', 29.5735, FALSE, 12),
    ('cup', 'cup', 'volume', 236.588, FALSE, 13),
    ('pt', 'pint', 'volume', 473.176, FALSE, 14),
    ('qt', 'quart', 'volume', 946.353, FALSE, 15),
    ('gal', 'gallon', 'volume', 3785.41, FALSE, 16);

-- Insert count-based units
INSERT INTO units (id, label, category, to_base_factor, display_order) VALUES
    ('dozen', 'dozen', 'count', 12.0, 20),
    ('pair', 'pair', 'count', 2.0, 21);

-- Create table for custom unit mappings (e.g., loaf -> slices)
CREATE TABLE item_unit_mappings (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,  -- e.g., 'bread'
    from_unit_id VARCHAR(10) NOT NULL REFERENCES units(id),
    to_unit_id VARCHAR(10) NOT NULL REFERENCES units(id),
    conversion_factor DECIMAL(10, 6) NOT NULL,  -- e.g., 1 loaf = 20 slices
    notes TEXT,
    created_by INTEGER,  -- user_id who created this mapping
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure units are in same category
    CONSTRAINT same_category CHECK (
        (SELECT category FROM units WHERE id = from_unit_id) = 
        (SELECT category FROM units WHERE id = to_unit_id)
    ),
    
    -- Prevent duplicate mappings
    UNIQUE(item_name, from_unit_id, to_unit_id)
);

-- Create function to validate unit conversions
CREATE OR REPLACE FUNCTION validate_unit_conversion(
    from_unit VARCHAR(10),
    to_unit VARCHAR(10)
) RETURNS BOOLEAN AS $$
DECLARE
    from_category unit_category;
    to_category unit_category;
BEGIN
    -- Get categories
    SELECT category INTO from_category FROM units WHERE id = from_unit;
    SELECT category INTO to_category FROM units WHERE id = to_unit;
    
    -- If either unit doesn't exist, return false
    IF from_category IS NULL OR to_category IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Units are convertible only if they're in the same category
    RETURN from_category = to_category;
END;
$$ LANGUAGE plpgsql;

-- Add some common custom units that users might need
INSERT INTO units (id, label, category, to_base_factor, display_order) VALUES
    -- Cooking-specific count units
    ('slice', 'slice', 'count', 1.0, 30),
    ('loaf', 'loaf', 'count', 20.0, 31),  -- 1 loaf = 20 slices
    ('stick', 'stick', 'count', 1.0, 32),  -- for butter sticks
    ('clove', 'clove', 'count', 1.0, 33),  -- for garlic
    ('head', 'head', 'count', 1.0, 34),   -- for lettuce, cabbage
    
    -- Ambiguous units that need context
    ('pinch', 'pinch', 'volume', 0.3, 40),     -- ~0.3ml
    ('dash', 'dash', 'volume', 0.6, 41),       -- ~0.6ml
    ('drop', 'drop', 'volume', 0.05, 42),      -- ~0.05ml
    ('handful', 'handful', 'volume', 60.0, 43), -- ~1/4 cup
    
    -- Package-based units (these would need item-specific mappings)
    ('can', 'can', 'count', 1.0, 50),
    ('jar', 'jar', 'count', 1.0, 51),
    ('bottle', 'bottle', 'count', 1.0, 52),
    ('box', 'box', 'count', 1.0, 53),
    ('bag', 'bag', 'count', 1.0, 54),
    ('bunch', 'bunch', 'count', 1.0, 55);

-- Create view for commonly used units per category
CREATE OR REPLACE VIEW common_units AS
SELECT id, label, category, to_base_factor, is_metric
FROM units
WHERE display_order < 20
ORDER BY category, display_order;

-- Grant permissions
GRANT SELECT ON units TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON item_unit_mappings TO authenticated_users;
GRANT SELECT ON common_units TO PUBLIC;