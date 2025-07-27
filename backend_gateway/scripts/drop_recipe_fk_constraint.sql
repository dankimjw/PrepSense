-- Drop the foreign key constraint on user_recipes table
-- This allows storing external recipe IDs (e.g., from Spoonacular) without requiring them in the local recipes table

-- Drop the foreign key constraint if it exists
ALTER TABLE user_recipes DROP CONSTRAINT IF EXISTS user_recipes_recipe_id_fkey;

-- Add a comment explaining why we don't need this constraint
COMMENT ON COLUMN user_recipes.recipe_id IS 'Recipe ID - can be NULL for custom recipes, or contain external IDs (e.g., Spoonacular). No FK constraint since we support external recipes.';

-- Verify the constraint was dropped
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'user_recipes' 
AND tc.constraint_type = 'FOREIGN KEY'
AND kcu.column_name = 'recipe_id';