-- Add support for external recipe IDs in user_recipes table
-- This allows storing references to Spoonacular recipes without requiring them in the local recipes table

-- First, add a column to distinguish between local and external recipes
ALTER TABLE user_recipes 
ADD COLUMN IF NOT EXISTS is_external BOOLEAN DEFAULT FALSE;

-- Add a column for external recipe source (e.g., 'spoonacular')
ALTER TABLE user_recipes
ADD COLUMN IF NOT EXISTS external_source VARCHAR(50);

-- Create an index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_user_recipes_external 
ON user_recipes(user_id, is_external, external_source);

-- Update the constraint to be conditional (only check FK for local recipes)
-- First, we need to drop the existing constraint if it exists
DO $$ 
BEGIN 
    ALTER TABLE user_recipes DROP CONSTRAINT IF EXISTS user_recipes_recipe_id_fkey;
EXCEPTION 
    WHEN undefined_object THEN 
        NULL;
END $$;

-- Add a check constraint instead of foreign key to allow external recipes
ALTER TABLE user_recipes
ADD CONSTRAINT check_recipe_reference CHECK (
    (is_external = FALSE AND recipe_id IN (SELECT recipe_id FROM recipes))
    OR 
    (is_external = TRUE AND external_source IS NOT NULL)
);

-- Comment on the new columns
COMMENT ON COLUMN user_recipes.is_external IS 'TRUE if recipe is from external source (e.g., Spoonacular), FALSE if local';
COMMENT ON COLUMN user_recipes.external_source IS 'Source of external recipe (e.g., spoonacular)';