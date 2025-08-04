#!/usr/bin/env python3
"""
Database migration script for backup recipe system.
Creates tables for storing 13k backup recipes from CSV dataset.

🟡 PARTIAL - Database schema design (requires manual execution)
"""

import asyncio
import asyncpg
import logging
from backend_gateway.core.config import settings

logger = logging.getLogger(__name__)

# Database schema for backup recipes
BACKUP_RECIPES_SCHEMA = """
-- Backup recipes table for 13k+ recipe dataset
CREATE TABLE IF NOT EXISTS backup_recipes (
    backup_recipe_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    ingredients TEXT NOT NULL,  -- Raw ingredients list as JSON array string
    instructions TEXT NOT NULL, -- Raw instructions text
    image_name VARCHAR(255),    -- Original image filename
    cleaned_ingredients TEXT,   -- Processed ingredients if available
    source VARCHAR(50) DEFAULT 'csv_dataset',
    prep_time INTEGER,          -- Estimated prep time (to be calculated)
    cook_time INTEGER,          -- Estimated cook time (to be calculated) 
    servings INTEGER,           -- Estimated servings (to be calculated)
    difficulty VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    cuisine_type VARCHAR(100),  -- To be inferred from title/ingredients
    search_vector TSVECTOR,     -- Full-text search vector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parsed ingredients from backup recipes for search functionality
CREATE TABLE IF NOT EXISTS backup_recipe_ingredients (
    backup_recipe_id INTEGER NOT NULL REFERENCES backup_recipes(backup_recipe_id) ON DELETE CASCADE,
    ingredient_name VARCHAR(255) NOT NULL,
    original_text TEXT,         -- Original ingredient line from CSV
    quantity VARCHAR(50),       -- Parsed quantity (as string due to varied formats)
    unit VARCHAR(50),          -- Parsed unit
    is_optional BOOLEAN DEFAULT FALSE,
    confidence DECIMAL(3,2) DEFAULT 1.0,  -- Parsing confidence score
    PRIMARY KEY (backup_recipe_id, ingredient_name)
);

-- Backup recipe search metadata for performance
CREATE TABLE IF NOT EXISTS backup_recipe_search_metadata (
    backup_recipe_id INTEGER PRIMARY KEY REFERENCES backup_recipes(backup_recipe_id) ON DELETE CASCADE,
    main_ingredients TEXT[],    -- Array of primary ingredients
    cuisine_keywords TEXT[],    -- Keywords for cuisine classification
    difficulty_score DECIMAL(3,2) DEFAULT 0.5,  -- 0=easy, 0.5=medium, 1=hard
    estimated_cost_level INTEGER DEFAULT 2,      -- 1=cheap, 2=moderate, 3=expensive
    dietary_tags TEXT[] DEFAULT '{}',            -- vegetarian, vegan, gluten-free, etc.
    cooking_methods TEXT[] DEFAULT '{}',         -- bake, fry, grill, etc.
    meal_type TEXT[] DEFAULT '{}',               -- breakfast, lunch, dinner, snack
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_backup_recipes_title ON backup_recipes(title);
CREATE INDEX IF NOT EXISTS idx_backup_recipes_cuisine ON backup_recipes(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_backup_recipes_difficulty ON backup_recipes(difficulty);
CREATE INDEX IF NOT EXISTS idx_backup_recipes_search_vector ON backup_recipes USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_backup_recipes_source ON backup_recipes(source);

-- Ingredient search indexes
CREATE INDEX IF NOT EXISTS idx_backup_ingredients_name ON backup_recipe_ingredients(ingredient_name);
CREATE INDEX IF NOT EXISTS idx_backup_ingredients_recipe ON backup_recipe_ingredients(backup_recipe_id);

-- Search metadata indexes
CREATE INDEX IF NOT EXISTS idx_backup_search_main_ingredients ON backup_recipe_search_metadata USING GIN(main_ingredients);
CREATE INDEX IF NOT EXISTS idx_backup_search_dietary_tags ON backup_recipe_search_metadata USING GIN(dietary_tags);
CREATE INDEX IF NOT EXISTS idx_backup_search_cooking_methods ON backup_recipe_search_metadata USING GIN(cooking_methods);
CREATE INDEX IF NOT EXISTS idx_backup_search_meal_type ON backup_recipe_search_metadata USING GIN(meal_type);

-- Update timestamp trigger for backup_recipes
CREATE OR REPLACE FUNCTION update_backup_recipes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER backup_recipes_updated_at_trigger
    BEFORE UPDATE ON backup_recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_backup_recipes_updated_at();

-- Update timestamp trigger for search metadata
CREATE TRIGGER backup_search_metadata_updated_at_trigger
    BEFORE UPDATE ON backup_recipe_search_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_backup_recipes_updated_at();

-- Function to update search vector automatically
CREATE OR REPLACE FUNCTION update_backup_recipe_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.cuisine_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.ingredients, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.instructions, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER backup_recipes_search_vector_trigger
    BEFORE INSERT OR UPDATE ON backup_recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_backup_recipe_search_vector();

-- View for easy recipe searching with ingredient matching
CREATE OR REPLACE VIEW backup_recipes_with_ingredients AS
SELECT 
    br.backup_recipe_id,
    br.title,
    br.cuisine_type,
    br.difficulty,
    br.prep_time,
    br.cook_time,
    br.servings,
    br.image_name,
    br.source,
    array_agg(DISTINCT bri.ingredient_name) as ingredients_list,
    brsm.main_ingredients,
    brsm.dietary_tags,
    brsm.cooking_methods,
    brsm.meal_type,
    br.created_at
FROM backup_recipes br
LEFT JOIN backup_recipe_ingredients bri ON br.backup_recipe_id = bri.backup_recipe_id
LEFT JOIN backup_recipe_search_metadata brsm ON br.backup_recipe_id = brsm.backup_recipe_id
GROUP BY br.backup_recipe_id, brsm.main_ingredients, brsm.dietary_tags, brsm.cooking_methods, brsm.meal_type;

-- Function to search recipes by available ingredients
CREATE OR REPLACE FUNCTION search_backup_recipes_by_ingredients(
    available_ingredients TEXT[],
    min_match_ratio DECIMAL DEFAULT 0.3,
    limit_count INTEGER DEFAULT 20
) RETURNS TABLE (
    backup_recipe_id INTEGER,
    title VARCHAR(500),
    match_ratio DECIMAL,
    missing_ingredients TEXT[],
    matched_ingredients TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    WITH recipe_matches AS (
        SELECT 
            br.backup_recipe_id,
            br.title,
            array_agg(DISTINCT bri.ingredient_name) as recipe_ingredients
        FROM backup_recipes br
        JOIN backup_recipe_ingredients bri ON br.backup_recipe_id = bri.backup_recipe_id
        GROUP BY br.backup_recipe_id, br.title
    ),
    ingredient_analysis AS (
        SELECT 
            rm.backup_recipe_id,
            rm.title,
            rm.recipe_ingredients,
            available_ingredients & rm.recipe_ingredients as matched,
            rm.recipe_ingredients - available_ingredients as missing,
            CASE 
                WHEN array_length(rm.recipe_ingredients, 1) > 0 
                THEN ROUND((array_length(available_ingredients & rm.recipe_ingredients, 1)::DECIMAL / array_length(rm.recipe_ingredients, 1)::DECIMAL), 3)
                ELSE 0
            END as match_ratio
        FROM recipe_matches rm
    )
    SELECT 
        ia.backup_recipe_id,
        ia.title,
        ia.match_ratio,
        ia.missing,
        ia.matched
    FROM ingredient_analysis ia
    WHERE ia.match_ratio >= min_match_ratio
    ORDER BY ia.match_ratio DESC, array_length(ia.missing, 1) ASC NULLS LAST
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
"""


async def run_migration():
    """Execute the backup recipes database migration."""
    try:
        # Connect to database
        db_url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
        
        conn = await asyncpg.connect(db_url)
        
        logger.info("🔄 Starting backup recipes database migration...")
        
        # Execute schema creation
        await conn.execute(BACKUP_RECIPES_SCHEMA)
        
        logger.info("✅ Backup recipes tables created successfully")
        
        # Verify tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%backup%'
        """)
        
        logger.info(f"📊 Created tables: {[row['table_name'] for row in tables]}")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())