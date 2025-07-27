-- Add environmental impact columns to products table
-- This migration adds columns for storing OWID environmental data

-- Add environmental impact columns
ALTER TABLE products ADD COLUMN IF NOT EXISTS ghg_kg_co2e_per_kg DECIMAL(10, 2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS land_m2_per_kg DECIMAL(10, 2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS water_l_per_kg DECIMAL(10, 2);
ALTER TABLE products ADD COLUMN IF NOT EXISTS eutrophying_g_per_kg DECIMAL(10, 2);

-- Add sustainability profile columns
ALTER TABLE products ADD COLUMN IF NOT EXISTS impact_category VARCHAR(20);
ALTER TABLE products ADD COLUMN IF NOT EXISTS planet_score INTEGER CHECK (planet_score >= 1 AND planet_score <= 10);
ALTER TABLE products ADD COLUMN IF NOT EXISTS ghg_visual VARCHAR(10);

-- Add metadata columns
ALTER TABLE products ADD COLUMN IF NOT EXISTS owid_product VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS environmental_data_updated_at TIMESTAMP;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_impact_category ON products(impact_category);
CREATE INDEX IF NOT EXISTS idx_products_planet_score ON products(planet_score);
CREATE INDEX IF NOT EXISTS idx_products_ghg ON products(ghg_kg_co2e_per_kg);

-- Add comments for documentation
COMMENT ON COLUMN products.ghg_kg_co2e_per_kg IS 'Greenhouse gas emissions in kg CO2 equivalent per kg of product (from OWID)';
COMMENT ON COLUMN products.land_m2_per_kg IS 'Land use in square meters per kg of product (from OWID)';
COMMENT ON COLUMN products.water_l_per_kg IS 'Water withdrawal in liters per kg of product (from OWID)';
COMMENT ON COLUMN products.eutrophying_g_per_kg IS 'Eutrophying emissions in grams PO4 equivalent per kg (from OWID)';
COMMENT ON COLUMN products.impact_category IS 'Environmental impact category: very_low, low, medium, high, very_high';
COMMENT ON COLUMN products.planet_score IS 'Sustainability score from 1 (worst) to 10 (best)';
COMMENT ON COLUMN products.ghg_visual IS 'Visual indicator emoji for environmental impact';
COMMENT ON COLUMN products.owid_product IS 'Original product name from Our World in Data dataset';
COMMENT ON COLUMN products.environmental_data_updated_at IS 'Timestamp of last environmental data update';