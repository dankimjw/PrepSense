-- Spoonacular API Call Tracking Table
-- Purpose: Track all API calls for usage analytics and cost monitoring
-- Compatible with GCP Cloud SQL PostgreSQL

CREATE TABLE IF NOT EXISTS spoonacular_api_calls (
    id SERIAL PRIMARY KEY,
    
    -- API Call Metadata
    endpoint VARCHAR(100) NOT NULL,  -- e.g., 'findByIngredients', 'complexSearch'
    method VARCHAR(10) NOT NULL DEFAULT 'GET',
    call_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Request Details
    user_id INTEGER,  -- Optional: track user-specific usage
    request_params JSONB,  -- Store request parameters as JSON
    request_size_bytes INTEGER DEFAULT 0,
    
    -- Response Details
    response_status INTEGER,  -- HTTP status code
    response_size_bytes INTEGER DEFAULT 0,
    response_time_ms INTEGER,  -- Response time in milliseconds
    
    -- API Usage Tracking  
    recipe_count INTEGER DEFAULT 0,  -- Number of recipes returned
    cache_hit BOOLEAN DEFAULT FALSE,  -- Whether this was served from cache
    duplicate_detected BOOLEAN DEFAULT FALSE,  -- Whether deduplication occurred
    cost_points INTEGER DEFAULT 1,  -- API cost in points (based on endpoint)
    
    -- Error Handling
    error_code VARCHAR(50),  -- Error code if call failed
    error_message TEXT,  -- Error message if call failed
    retry_attempt INTEGER DEFAULT 0,  -- Retry attempt number (0 = first try)
    
    -- Recipe Fingerprinting
    recipe_fingerprints TEXT[],  -- Array of recipe fingerprints returned
    duplicate_recipe_ids INTEGER[],  -- Array of duplicate recipe IDs detected
    
    -- Additional Metadata
    api_version VARCHAR(10) DEFAULT 'v1',
    client_version VARCHAR(20) DEFAULT 'prepsense-1.0',
    environment VARCHAR(20) DEFAULT 'production',
    
    -- Indexes for performance
    INDEX idx_spoonacular_calls_timestamp (call_timestamp),
    INDEX idx_spoonacular_calls_user_id (user_id),
    INDEX idx_spoonacular_calls_endpoint (endpoint),
    INDEX idx_spoonacular_calls_status (response_status),
    INDEX idx_spoonacular_calls_cache_hit (cache_hit)
);

-- Add comments for documentation
COMMENT ON TABLE spoonacular_api_calls IS 'Tracks all Spoonacular API calls for usage analytics and cost monitoring';
COMMENT ON COLUMN spoonacular_api_calls.endpoint IS 'Spoonacular API endpoint called (findByIngredients, complexSearch, etc.)';
COMMENT ON COLUMN spoonacular_api_calls.request_params IS 'JSON storage of request parameters for debugging and analytics';
COMMENT ON COLUMN spoonacular_api_calls.cost_points IS 'API cost in points based on endpoint pricing';
COMMENT ON COLUMN spoonacular_api_calls.recipe_fingerprints IS 'Array of recipe fingerprints for deduplication tracking';
COMMENT ON COLUMN spoonacular_api_calls.duplicate_recipe_ids IS 'Array of recipe IDs that were detected as duplicates';

-- Create materialized view for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS spoonacular_api_analytics AS
SELECT 
    DATE(call_timestamp) as call_date,
    endpoint,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits,
    COUNT(*) FILTER (WHERE cache_hit = false) as cache_misses,
    COUNT(*) FILTER (WHERE duplicate_detected = true) as duplicate_detections,
    SUM(cost_points) as total_cost_points,
    SUM(recipe_count) as total_recipes_returned,
    AVG(response_time_ms) as avg_response_time_ms,
    COUNT(*) FILTER (WHERE response_status >= 400) as error_count
FROM spoonacular_api_calls
GROUP BY DATE(call_timestamp), endpoint
ORDER BY call_date DESC, endpoint;

-- Refresh the materialized view daily (can be set up as a cron job)
COMMENT ON MATERIALIZED VIEW spoonacular_api_analytics IS 'Daily analytics view for Spoonacular API usage - refresh daily';