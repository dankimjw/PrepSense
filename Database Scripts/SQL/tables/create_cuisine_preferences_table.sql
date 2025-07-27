-- Create table for storing user cuisine preferences with positive/negative weights
-- This allows users to indicate both liked and disliked cuisines

CREATE TABLE IF NOT EXISTS user_cuisine_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cuisine VARCHAR(100) NOT NULL,
    preference_level INTEGER NOT NULL CHECK (preference_level BETWEEN -5 AND 5),
    -- -5 = strongly dislike, 0 = neutral, 5 = strongly like
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique cuisine preference per user
    UNIQUE(user_id, cuisine)
);

-- Create index for faster lookups
CREATE INDEX idx_user_cuisine_preferences_user_id ON user_cuisine_preferences(user_id);
CREATE INDEX idx_user_cuisine_preferences_level ON user_cuisine_preferences(preference_level);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cuisine_preferences_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cuisine_preferences_timestamp
BEFORE UPDATE ON user_cuisine_preferences
FOR EACH ROW
EXECUTE FUNCTION update_cuisine_preferences_timestamp();

-- Insert some example data for testing
INSERT INTO user_cuisine_preferences (user_id, cuisine, preference_level) VALUES
(111, 'italian', 5),    -- Strongly likes Italian
(111, 'japanese', 4),   -- Likes Japanese
(111, 'mexican', 3),    -- Somewhat likes Mexican
(111, 'indian', -2),    -- Dislikes Indian (maybe too spicy)
(111, 'german', -4),    -- Strongly dislikes German
(111, 'thai', 1),       -- Slightly likes Thai
(111, 'french', 2),     -- Likes French
(111, 'chinese', 3),    -- Somewhat likes Chinese
(111, 'mediterranean', 4), -- Likes Mediterranean
(111, 'american', 0)    -- Neutral about American
ON CONFLICT (user_id, cuisine) DO NOTHING;

-- Function to get user's liked cuisines
CREATE OR REPLACE FUNCTION get_liked_cuisines(p_user_id INTEGER)
RETURNS TABLE(cuisine VARCHAR, preference_level INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT ucp.cuisine, ucp.preference_level
    FROM user_cuisine_preferences ucp
    WHERE ucp.user_id = p_user_id
    AND ucp.preference_level > 0
    ORDER BY ucp.preference_level DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's disliked cuisines
CREATE OR REPLACE FUNCTION get_disliked_cuisines(p_user_id INTEGER)
RETURNS TABLE(cuisine VARCHAR, preference_level INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT ucp.cuisine, ucp.preference_level
    FROM user_cuisine_preferences ucp
    WHERE ucp.user_id = p_user_id
    AND ucp.preference_level < 0
    ORDER BY ucp.preference_level ASC;
END;
$$ LANGUAGE plpgsql;

-- View for easy access to preferences
CREATE OR REPLACE VIEW user_cuisine_preference_summary AS
SELECT 
    user_id,
    COUNT(CASE WHEN preference_level > 0 THEN 1 END) as liked_cuisines,
    COUNT(CASE WHEN preference_level < 0 THEN 1 END) as disliked_cuisines,
    COUNT(CASE WHEN preference_level = 0 THEN 1 END) as neutral_cuisines,
    AVG(preference_level) as average_preference
FROM user_cuisine_preferences
GROUP BY user_id;