-- Fix the search functions to use correct column names

-- Drop existing functions
DROP FUNCTION IF EXISTS find_similar_recipes;
DROP FUNCTION IF EXISTS find_similar_products;
DROP FUNCTION IF EXISTS hybrid_recipe_search;

-- Recreate function to find similar recipes with correct column names
CREATE OR REPLACE FUNCTION find_similar_recipes(
    query_embedding vector(1536),
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    recipe_id INTEGER,
    recipe_name VARCHAR,
    similarity_score FLOAT,
    ingredients TEXT,
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.recipe_id,
        r.recipe_name,
        1 - (r.embedding <=> query_embedding) as similarity_score,
        r.recipe_data->>'ingredients' as ingredients,
        r.recipe_data->>'description' as description
    FROM recipes r
    WHERE r.embedding IS NOT NULL
        AND 1 - (r.embedding <=> query_embedding) > similarity_threshold
    ORDER BY r.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar products with correct column names
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
        p.product_id,
        p.product_name,
        p.brand_name as brand,
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
            r.recipe_id,
            1 - (r.embedding <=> query_embedding) as semantic_score
        FROM recipes r
        WHERE r.embedding IS NOT NULL
    ),
    ingredient_data AS (
        SELECT 
            r.recipe_id,
            ARRAY(
                SELECT jsonb_array_elements_text(
                    CASE 
                        WHEN jsonb_typeof(r.recipe_data->'ingredients') = 'array' 
                        THEN r.recipe_data->'ingredients'
                        ELSE '[]'::jsonb
                    END
                )
            ) as recipe_ingredients
        FROM recipes r
    ),
    ingredient_scores AS (
        SELECT 
            i.recipe_id,
            ARRAY_AGG(DISTINCT ing) FILTER (WHERE ing = ANY(available_ingredients)) as matched,
            ARRAY_AGG(DISTINCT ing) FILTER (WHERE NOT (ing = ANY(available_ingredients))) as missing,
            COUNT(DISTINCT ing) FILTER (WHERE ing = ANY(available_ingredients))::FLOAT / 
                NULLIF(array_length(i.recipe_ingredients, 1), 0) as match_ratio
        FROM ingredient_data i
        CROSS JOIN LATERAL unnest(i.recipe_ingredients) as ing
        GROUP BY i.recipe_id
    )
    SELECT 
        r.recipe_id,
        r.recipe_name,
        COALESCE(s.semantic_score, 0) as semantic_score,
        COALESCE(i.match_ratio, 0) as ingredient_match_score,
        (COALESCE(s.semantic_score, 0) * semantic_weight + 
         COALESCE(i.match_ratio, 0) * ingredient_weight) as combined_score,
        COALESCE(i.matched, ARRAY[]::TEXT[]) as matched_ingredients,
        COALESCE(i.missing, ARRAY[]::TEXT[]) as missing_ingredients
    FROM recipes r
    LEFT JOIN semantic_scores s ON r.recipe_id = s.recipe_id
    LEFT JOIN ingredient_scores i ON r.recipe_id = i.recipe_id
    WHERE s.semantic_score > 0.2 OR i.match_ratio > 0.3
    ORDER BY combined_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION find_similar_recipes TO PUBLIC;
GRANT EXECUTE ON FUNCTION find_similar_products TO PUBLIC;
GRANT EXECUTE ON FUNCTION hybrid_recipe_search TO PUBLIC;