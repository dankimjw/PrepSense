-- Add interaction tracking table for preference learning
-- This table tracks all user interactions with recipes for learning preferences

-- Create user_recipe_interactions table
CREATE TABLE IF NOT EXISTS user_recipe_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipe_id VARCHAR(255) NOT NULL,  -- Can be from any source (saved, spoonacular, etc.)
    action VARCHAR(50) NOT NULL CHECK (action IN (
        'viewed', 'saved', 'cooked', 'rated', 'dismissed', 
        'rated_positive', 'rated_negative', 'removed', 'modified'
    )),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    context JSONB DEFAULT '{}',  -- Context info like time of day, location, etc.
    metadata JSONB DEFAULT '{}', -- Additional data like rating value, modifications
    
    -- Indexes for performance
    CONSTRAINT idx_unique_interaction UNIQUE (user_id, recipe_id, action, timestamp)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_interactions_user_timestamp 
    ON user_recipe_interactions(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_interactions_user_action 
    ON user_recipe_interactions(user_id, action);

CREATE INDEX IF NOT EXISTS idx_interactions_recipe 
    ON user_recipe_interactions(recipe_id);

CREATE INDEX IF NOT EXISTS idx_interactions_metadata 
    ON user_recipe_interactions USING GIN(metadata);

-- Add preference learning columns to user_preferences if they don't exist
ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS learned_weights JSONB DEFAULT '{}';

ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS preference_confidence DECIMAL(3,2) DEFAULT 0.5;

ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS last_preference_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add columns to track ingredient preferences
CREATE TABLE IF NOT EXISTS user_ingredient_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    ingredient VARCHAR(255) NOT NULL,
    preference_score DECIMAL(3,2) DEFAULT 0.0 CHECK (preference_score BETWEEN -1.0 AND 1.0),
    interaction_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, ingredient)
);

CREATE INDEX IF NOT EXISTS idx_ingredient_prefs_user 
    ON user_ingredient_preferences(user_id);

CREATE INDEX IF NOT EXISTS idx_ingredient_prefs_score 
    ON user_ingredient_preferences(user_id, preference_score DESC);

-- Add table for learned cuisine preferences with scores
CREATE TABLE IF NOT EXISTS user_cuisine_scores (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cuisine VARCHAR(100) NOT NULL,
    score DECIMAL(3,2) DEFAULT 0.0 CHECK (score BETWEEN -1.0 AND 1.0),
    positive_interactions INTEGER DEFAULT 0,
    negative_interactions INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, cuisine)
);

CREATE INDEX IF NOT EXISTS idx_cuisine_scores_user 
    ON user_cuisine_scores(user_id, score DESC);

-- Add table for cooking time preferences by meal type
CREATE TABLE IF NOT EXISTS user_time_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    meal_type VARCHAR(50) NOT NULL CHECK (meal_type IN (
        'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'any'
    )),
    preferred_max_minutes INTEGER DEFAULT 60,
    average_actual_minutes INTEGER,
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, meal_type)
);

-- Function to update preference scores based on interactions
CREATE OR REPLACE FUNCTION update_preference_scores()
RETURNS TRIGGER AS $$
BEGIN
    -- Update last_preference_update timestamp
    UPDATE user_preferences 
    SET last_preference_update = CURRENT_TIMESTAMP 
    WHERE user_id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update preferences on new interactions
DROP TRIGGER IF EXISTS trigger_update_preferences ON user_recipe_interactions;
CREATE TRIGGER trigger_update_preferences
    AFTER INSERT ON user_recipe_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_preference_scores();

-- Add comments for documentation
COMMENT ON TABLE user_recipe_interactions IS 'Tracks all user interactions with recipes for preference learning';
COMMENT ON TABLE user_ingredient_preferences IS 'Learned ingredient preferences based on user behavior';
COMMENT ON TABLE user_cuisine_scores IS 'Cuisine preference scores learned from user interactions';
COMMENT ON TABLE user_time_preferences IS 'Cooking time preferences by meal type';

-- Sample data for testing (optional)
-- INSERT INTO user_recipe_interactions (user_id, recipe_id, action, metadata)
-- VALUES 
--     (111, 'spoon_12345', 'cooked', '{"rating": 5, "cook_time": 25}'::jsonb),
--     (111, 'saved_001', 'saved', '{}'::jsonb),
--     (111, 'spoon_67890', 'dismissed', '{"reason": "too_complex"}'::jsonb);