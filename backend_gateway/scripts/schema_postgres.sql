-- PrepSense Cloud SQL PostgreSQL Schema
-- Optimized for transactional operations with PostgreSQL features

-- Create database (if not exists)
-- CREATE DATABASE prepsense;

-- Connect to the database
-- \c prepsense;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for email and username lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Pantries table
CREATE TABLE IF NOT EXISTS pantries (
    pantry_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    pantry_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pantries_user_id ON pantries(user_id);

-- Pantry items table (optimized for frequent updates)
CREATE TABLE IF NOT EXISTS pantry_items (
    pantry_item_id SERIAL PRIMARY KEY,
    pantry_id INTEGER NOT NULL REFERENCES pantries(pantry_id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
    unit_of_measurement VARCHAR(50),
    expiration_date DATE,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    source VARCHAR(20) DEFAULT 'manual' CHECK (source IN ('manual', 'vision_detected', 'receipt_scan')),
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'consumed', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consumed_at TIMESTAMP,
    used_quantity DECIMAL(10, 2) DEFAULT 0,
    -- PostgreSQL JSONB for flexible attributes
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for pantry items
CREATE INDEX IF NOT EXISTS idx_pantry_items_pantry_id ON pantry_items(pantry_id);
CREATE INDEX IF NOT EXISTS idx_pantry_items_expiration ON pantry_items(expiration_date);
CREATE INDEX IF NOT EXISTS idx_pantry_items_status ON pantry_items(status);
CREATE INDEX IF NOT EXISTS idx_pantry_items_category ON pantry_items(category);
CREATE INDEX IF NOT EXISTS idx_pantry_items_metadata ON pantry_items USING GIN(metadata);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    household_size INTEGER DEFAULT 1,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dietary preferences (using PostgreSQL arrays)
CREATE TABLE IF NOT EXISTS user_dietary_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    preference VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, preference)
);

-- Allergens
CREATE TABLE IF NOT EXISTS user_allergens (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    allergen VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, allergen)
);

-- Cuisine preferences
CREATE TABLE IF NOT EXISTS user_cuisine_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cuisine VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, cuisine)
);

-- Recipes table with JSONB for flexible recipe data
CREATE TABLE IF NOT EXISTS recipes (
    recipe_id SERIAL PRIMARY KEY,
    recipe_name VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100),
    prep_time INTEGER,
    cook_time INTEGER,
    servings INTEGER,
    difficulty VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    recipe_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_recipes_data ON recipes USING GIN(recipe_data);

-- Recipe ingredients
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id INTEGER NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2),
    unit VARCHAR(50),
    is_optional BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (recipe_id, ingredient_name)
);

-- User saved recipes
CREATE TABLE IF NOT EXISTS user_recipes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES recipes(recipe_id),
    recipe_title VARCHAR(255) NOT NULL,
    recipe_image TEXT,
    recipe_data JSONB DEFAULT '{}'::jsonb,
    rating VARCHAR(20) DEFAULT 'neutral' CHECK (rating IN ('thumbs_up', 'thumbs_down', 'neutral')),
    is_favorite BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_recipes_user_rating ON user_recipes(user_id, rating);
CREATE INDEX IF NOT EXISTS idx_user_recipes_user_favorite ON user_recipes(user_id, is_favorite);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pantry_items_updated_at BEFORE UPDATE ON pantry_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_recipes_updated_at BEFORE UPDATE ON user_recipes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create default demo user
INSERT INTO users (user_id, username, email, first_name, last_name, role)
VALUES (111, 'demo_user', 'demo@prepsense.com', 'Demo', 'User', 'user')
ON CONFLICT (user_id) DO NOTHING;

-- Create default pantry for demo user
INSERT INTO pantries (user_id, pantry_name)
SELECT 111, 'My Pantry'
WHERE NOT EXISTS (
    SELECT 1 FROM pantries WHERE user_id = 111
);

-- Create view for user pantry items (similar to BigQuery view)
CREATE OR REPLACE VIEW user_pantry_full AS
SELECT 
    pi.pantry_item_id,
    pi.pantry_id,
    p.user_id,
    pi.product_name,
    pi.brand_name,
    pi.category,
    pi.quantity,
    pi.unit_of_measurement,
    pi.expiration_date,
    pi.unit_price,
    pi.total_price,
    pi.source,
    pi.status,
    pi.created_at,
    pi.updated_at,
    pi.metadata
FROM pantry_items pi
JOIN pantries p ON pi.pantry_id = p.pantry_id;

-- Grant permissions for IAM users (when using IAM authentication)
-- This will be done after creating IAM database users
