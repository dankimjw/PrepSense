-- Migration: Add status and cooked_at columns to user_recipes table
-- Date: 2025-01-27
-- Purpose: Support recipe lifecycle tracking (saved/bookmarked vs cooked)

-- Check if columns already exist before adding them
DO $$ 
BEGIN
    -- Add status column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_recipes' 
        AND column_name = 'status'
    ) THEN
        ALTER TABLE user_recipes 
        ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'saved' 
        CHECK (status IN ('saved', 'cooked'));
        
        -- Add comment for clarity
        COMMENT ON COLUMN user_recipes.status IS 'Recipe lifecycle: saved (bookmarked for later) or cooked (already made)';
    END IF;

    -- Add cooked_at column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_recipes' 
        AND column_name = 'cooked_at'
    ) THEN
        ALTER TABLE user_recipes 
        ADD COLUMN cooked_at TIMESTAMP NULL;
        
        -- Add comment for clarity
        COMMENT ON COLUMN user_recipes.cooked_at IS 'Timestamp when the recipe was marked as cooked';
    END IF;
END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_user_recipes_status ON user_recipes(user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_recipes_cooked_at ON user_recipes(cooked_at);

-- Update existing records based on rating (optional - only run once)
-- Recipes that have been rated were likely cooked
UPDATE user_recipes 
SET status = 'cooked', 
    cooked_at = COALESCE(cooked_at, updated_at)
WHERE rating IN ('thumbs_up', 'thumbs_down')
AND status = 'saved';  -- Only update if not already marked as cooked