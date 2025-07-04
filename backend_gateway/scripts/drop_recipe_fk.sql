-- Drop the foreign key constraint on user_recipes that prevents saving external recipes
ALTER TABLE user_recipes DROP CONSTRAINT IF EXISTS user_recipes_recipe_id_fkey;