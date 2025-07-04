-- Add missing columns to match BigQuery schema
-- This migration adds product_id and ensures all required fields exist

-- Add product_id column to pantry_items if it doesn't exist
ALTER TABLE pantry_items 
ADD COLUMN IF NOT EXISTS product_id INTEGER;

-- Ensure UPC code can be stored in metadata
-- The metadata JSONB column already exists in the schema

-- Add index for product_id
CREATE INDEX IF NOT EXISTS idx_pantry_items_product_id ON pantry_items(product_id);

-- Add a comment to clarify that upc_code is stored in metadata
COMMENT ON COLUMN pantry_items.metadata IS 'JSONB field for flexible attributes including upc_code';