-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_preference table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_preference (
    user_id INTEGER PRIMARY KEY,
    dietary_preference TEXT[],
    allergens TEXT[],
    cuisine_preference TEXT[],
    cooking_time_preference VARCHAR(50),
    taste_preference TEXT[],
    health_goal TEXT[],
    kitchen_equipment TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_preference_user_id ON user_preference(user_id);