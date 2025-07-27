-- Add preference_level column to user_cuisine_preferences table
-- This column allows storing preference levels (positive or negative) for cuisines

ALTER TABLE user_cuisine_preferences 
ADD COLUMN IF NOT EXISTS preference_level INTEGER DEFAULT 1;

-- Add comment to explain the column
COMMENT ON COLUMN user_cuisine_preferences.preference_level IS 'Preference level: positive values indicate liked cuisines, negative values indicate disliked cuisines, 0 is neutral';

-- Example data: -5 = strongly dislike, -1 = dislike, 0 = neutral, 1 = like, 5 = love