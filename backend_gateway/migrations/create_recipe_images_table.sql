-- Migration: Create recipe_images table for tracking AI-generated recipe images
-- This table tracks both GCS signed URLs and local backup images

CREATE TABLE IF NOT EXISTS recipe_images (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL UNIQUE,
    recipe_title VARCHAR(500),
    gcs_signed_url TEXT,
    gcs_blob_path VARCHAR(500),
    local_file_path VARCHAR(500),
    url_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT unique_recipe_id UNIQUE (recipe_id)
);

-- Index for efficient expiration checks
CREATE INDEX IF NOT EXISTS idx_recipe_images_expires_at ON recipe_images(url_expires_at);
CREATE INDEX IF NOT EXISTS idx_recipe_images_recipe_id ON recipe_images(recipe_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_recipe_images_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to call the function
DROP TRIGGER IF EXISTS trigger_update_recipe_images_updated_at ON recipe_images;
CREATE TRIGGER trigger_update_recipe_images_updated_at
    BEFORE UPDATE ON recipe_images
    FOR EACH ROW
    EXECUTE FUNCTION update_recipe_images_updated_at();

-- Comments for documentation
COMMENT ON TABLE recipe_images IS 'Tracks AI-generated recipe images with GCS URLs and local backups';
COMMENT ON COLUMN recipe_images.recipe_id IS 'Spoonacular recipe ID';
COMMENT ON COLUMN recipe_images.recipe_title IS 'Recipe name for file naming';
COMMENT ON COLUMN recipe_images.gcs_signed_url IS 'Current 7-day signed URL from Google Cloud Storage';
COMMENT ON COLUMN recipe_images.gcs_blob_path IS 'Path to blob in GCS bucket (for regenerating signed URLs)';
COMMENT ON COLUMN recipe_images.local_file_path IS 'Relative path to local backup image';
COMMENT ON COLUMN recipe_images.url_expires_at IS 'When the current signed URL expires';