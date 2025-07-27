-- Migration to add pgvector extension and embedding columns for semantic search
-- Run this migration on your Google Cloud SQL PostgreSQL instance

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding columns to recipes table
ALTER TABLE recipes 
ADD COLUMN IF NOT EXISTS embedding vector(1536),
ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP;

-- Add embedding columns to products table  
ALTER TABLE products
ADD COLUMN IF NOT EXISTS embedding vector(1536),
ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP;

-- Add embedding columns to pantry_items table
ALTER TABLE pantry_items
ADD COLUMN IF NOT EXISTS embedding vector(1536),
ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP;

-- Create indexes for fast similarity search
-- Using HNSW indexes with cosine distance for better performance

-- Recipe embeddings index
CREATE INDEX IF NOT EXISTS idx_recipes_embedding_hnsw 
ON recipes 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
WHERE embedding IS NOT NULL;

-- Product embeddings index
CREATE INDEX IF NOT EXISTS idx_products_embedding_hnsw
ON products
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
WHERE embedding IS NOT NULL;

-- Pantry items embeddings index
CREATE INDEX IF NOT EXISTS idx_pantry_items_embedding_hnsw
ON pantry_items
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64)
WHERE embedding IS NOT NULL;

-- Create a table to cache food item embeddings
CREATE TABLE IF NOT EXISTS food_item_embeddings (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) UNIQUE NOT NULL,
    embedding vector(1536) NOT NULL,
    embedding_text TEXT, -- The text used to generate the embedding
    model VARCHAR(50) DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for food item embeddings
CREATE INDEX IF NOT EXISTS idx_food_item_embeddings_hnsw
ON food_item_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create index on item name for fast lookups
CREATE INDEX IF NOT EXISTS idx_food_item_embeddings_name
ON food_item_embeddings(LOWER(item_name));

-- Create a table to store search query embeddings for analytics
CREATE TABLE IF NOT EXISTS search_query_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50), -- recipe, product, pantry, general
    embedding vector(1536) NOT NULL,
    results_count INTEGER,
    clicked_result_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for analyzing similar searches
CREATE INDEX IF NOT EXISTS idx_search_query_embeddings_hnsw
ON search_query_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Function to find similar recipes
CREATE OR REPLACE FUNCTION find_similar_recipes(
    query_embedding vector(1536),
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    recipe_id INTEGER,
    recipe_name VARCHAR,
    similarity_score FLOAT,
    ingredients TEXT[],
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id as recipe_id,
        r.name as recipe_name,
        1 - (r.embedding <=> query_embedding) as similarity_score,
        r.ingredients,
        r.description
    FROM recipes r
    WHERE r.embedding IS NOT NULL
        AND 1 - (r.embedding <=> query_embedding) > similarity_threshold
    ORDER BY r.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar products
CREATE OR REPLACE FUNCTION find_similar_products(
    query_embedding vector(1536),
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    product_id INTEGER,
    product_name VARCHAR,
    brand VARCHAR,
    category VARCHAR,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id as product_id,
        p.name as product_name,
        p.brand,
        p.category,
        1 - (p.embedding <=> query_embedding) as similarity_score
    FROM products p
    WHERE p.embedding IS NOT NULL
        AND 1 - (p.embedding <=> query_embedding) > similarity_threshold
    ORDER BY p.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function for hybrid recipe search (semantic + ingredient matching)
CREATE OR REPLACE FUNCTION hybrid_recipe_search(
    query_embedding vector(1536),
    available_ingredients TEXT[],
    limit_count INTEGER DEFAULT 10,
    semantic_weight FLOAT DEFAULT 0.6,
    ingredient_weight FLOAT DEFAULT 0.4
)
RETURNS TABLE (
    recipe_id INTEGER,
    recipe_name VARCHAR,
    semantic_score FLOAT,
    ingredient_match_score FLOAT,
    combined_score FLOAT,
    matched_ingredients TEXT[],
    missing_ingredients TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_scores AS (
        SELECT 
            r.id,
            1 - (r.embedding <=> query_embedding) as semantic_score
        FROM recipes r
        WHERE r.embedding IS NOT NULL
    ),
    ingredient_scores AS (
        SELECT 
            r.id,
            ARRAY_AGG(DISTINCT ing) FILTER (WHERE ing = ANY(available_ingredients)) as matched,
            ARRAY_AGG(DISTINCT ing) FILTER (WHERE NOT (ing = ANY(available_ingredients))) as missing,
            COUNT(DISTINCT ing) FILTER (WHERE ing = ANY(available_ingredients))::FLOAT / 
                NULLIF(array_length(r.ingredients, 1), 0) as match_ratio
        FROM recipes r
        CROSS JOIN LATERAL unnest(r.ingredients) as ing
        GROUP BY r.id
    )
    SELECT 
        r.id as recipe_id,
        r.name as recipe_name,
        COALESCE(s.semantic_score, 0) as semantic_score,
        COALESCE(i.match_ratio, 0) as ingredient_match_score,
        (COALESCE(s.semantic_score, 0) * semantic_weight + 
         COALESCE(i.match_ratio, 0) * ingredient_weight) as combined_score,
        COALESCE(i.matched, ARRAY[]::TEXT[]) as matched_ingredients,
        COALESCE(i.missing, ARRAY[]::TEXT[]) as missing_ingredients
    FROM recipes r
    LEFT JOIN semantic_scores s ON r.id = s.id
    LEFT JOIN ingredient_scores i ON r.id = i.id
    WHERE s.semantic_score > 0.2 OR i.match_ratio > 0.3
    ORDER BY combined_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to update timestamp when embedding is updated
CREATE OR REPLACE FUNCTION update_embedding_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.embedding IS DISTINCT FROM OLD.embedding THEN
        NEW.embedding_updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for each table
CREATE TRIGGER update_recipes_embedding_timestamp
BEFORE UPDATE ON recipes
FOR EACH ROW
EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_products_embedding_timestamp
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_embedding_timestamp();

CREATE TRIGGER update_pantry_items_embedding_timestamp
BEFORE UPDATE ON pantry_items
FOR EACH ROW
EXECUTE FUNCTION update_embedding_timestamp();

-- Grant necessary permissions
GRANT SELECT ON food_item_embeddings TO PUBLIC;
GRANT SELECT ON search_query_embeddings TO PUBLIC;
GRANT EXECUTE ON FUNCTION find_similar_recipes TO PUBLIC;
GRANT EXECUTE ON FUNCTION find_similar_products TO PUBLIC;
GRANT EXECUTE ON FUNCTION hybrid_recipe_search TO PUBLIC;