-- Units table creation and data for PrepSense
-- This script should be run with database administrator privileges

-- Create the unit_category enum type and tables
CREATE TYPE unit_category AS ENUM ('mass', 'volume', 'count');

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

CREATE INDEX idx_units_category ON units(category);

CREATE INDEX idx_units_display_order ON units(display_order);

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
-- Note: Category matching enforced at application level
UNIQUE(item_name, from_unit_id, to_unit_id)
);

-- Insert units data
INSERT INTO units (id, label, category, to_base_factor, is_base_unit, display_order) VALUES
('g', 'gram', 'mass', 1.0, TRUE, 1),
('ml', 'millilitre', 'volume', 1.0, TRUE, 1),
('ea', 'each', 'count', 1.0, TRUE, 1);

INSERT INTO units (id, label, category, to_base_factor, display_order) VALUES
('mg', 'milligram', 'mass', 0.001, 2),
('kg', 'kilogram', 'mass', 1000.0, 3),
('l', 'litre', 'volume', 1000.0, 2),
('dl', 'decilitre', 'volume', 100.0, 3),
('cl', 'centilitre', 'volume', 10.0, 4);

INSERT INTO units (id, label, category, to_base_factor, is_metric, display_order) VALUES
('oz', 'ounce', 'mass', 28.3495, FALSE, 10),
('lb', 'pound', 'mass', 453.592, FALSE, 11),
('tsp', 'teaspoon', 'volume', 4.92892, FALSE, 10),
('tbsp', 'tablespoon', 'volume', 14.7868, FALSE, 11),
('floz', 'fluid ounce', 'volume', 29.5735, FALSE, 12),
('cup', 'cup', 'volume', 236.588, FALSE, 13),
('pt', 'pint', 'volume', 473.176, FALSE, 14),
('qt', 'quart', 'volume', 946.353, FALSE, 15),
('gal', 'gallon', 'volume', 3785.41, FALSE, 16);

INSERT INTO units (id, label, category, to_base_factor, display_order) VALUES
('dozen', 'dozen', 'count', 12.0, 20),
('pair', 'pair', 'count', 2.0, 21);

INSERT INTO units (id, label, category, to_base_factor, display_order) VALUES
('slice', 'slice', 'count', 1.0, 30),
('loaf', 'loaf', 'count', 20.0, 31),  -- 1 loaf = 20 slices
('stick', 'stick', 'count', 1.0, 32),  -- for butter sticks
('clove', 'clove', 'count', 1.0, 33),  -- for garlic
('head', 'head', 'count', 1.0, 34),   -- for lettuce, cabbage
('pinch', 'pinch', 'volume', 0.3, 40),     -- ~0.3ml
('dash', 'dash', 'volume', 0.6, 41),       -- ~0.6ml
('drop', 'drop', 'volume', 0.05, 42),      -- ~0.05ml
('handful', 'handful', 'volume', 60.0, 43), -- ~1/4 cup
('can', 'can', 'count', 1.0, 50),
('jar', 'jar', 'count', 1.0, 51),
('bottle', 'bottle', 'count', 1.0, 52),
('box', 'box', 'count', 1.0, 53),
('bag', 'bag', 'count', 1.0, 54),
('bunch', 'bunch', 'count', 1.0, 55);

