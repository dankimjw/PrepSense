-- Update user_recipes table to support bookmark/saved/cooked status system
-- This migration adds status field and cooked_at timestamp

-- Add status column with ENUM type
ALTER TABLE user_recipes 
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'saved' CHECK (status IN ('saved', 'cooked'));

-- Add cooked_at timestamp
ALTER TABLE user_recipes 
ADD COLUMN cooked_at TIMESTAMP NULL;

-- Update existing records based on rating
-- If a recipe has been rated, it was likely cooked
UPDATE user_recipes 
SET status = 'cooked', 
    cooked_at = updated_at 
WHERE rating IN ('thumbs_up', 'thumbs_down');

-- Create indexes for better query performance
CREATE INDEX idx_user_recipes_status ON user_recipes(user_id, status);
CREATE INDEX idx_user_recipes_cooked_at ON user_recipes(cooked_at);

-- Add comment to clarify the purpose of the fields
COMMENT ON COLUMN user_recipes.status IS 'Recipe lifecycle: saved (bookmarked for later) or cooked (already made)';
COMMENT ON COLUMN user_recipes.cooked_at IS 'Timestamp when the recipe was marked as cooked';