-- Create user_recipes table in BigQuery for storing user's saved recipes
-- This table allows users to save recipes with ratings (thumbs up/down)

CREATE TABLE IF NOT EXISTS `adsp-34002-on02-prep-sense.Inventory.user_recipes` (
  id STRING NOT NULL,
  user_id INTEGER NOT NULL,
  recipe_id INTEGER,
  recipe_title STRING NOT NULL,
  recipe_image STRING,
  recipe_data JSON,
  source STRING NOT NULL,  -- 'spoonacular', 'generated', 'custom'
  rating STRING DEFAULT 'neutral',  -- 'thumbs_up', 'thumbs_down', 'neutral'
  is_favorite BOOL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- Add indexes for performance (BigQuery automatically handles indexing)
-- Primary access patterns:
-- 1. Get all recipes for a user
-- 2. Filter by rating
-- 3. Check if recipe exists for user