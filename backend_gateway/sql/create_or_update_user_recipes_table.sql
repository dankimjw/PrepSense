-- Create or update user_recipes table in BigQuery for storing user's saved recipes
-- This table integrates with the existing schema and adds useful enhancements

-- Drop existing table if you want to recreate it (uncomment if needed)
-- DROP TABLE IF EXISTS `adsp-34002-on02-prep-sense.Inventory.user_recipes`;

-- Create the enhanced user_recipes table
CREATE TABLE IF NOT EXISTS `adsp-34002-on02-prep-sense.Inventory.user_recipes` (
  -- Primary fields
  id STRING NOT NULL,  -- UUID for this saved recipe entry
  user_id INTEGER NOT NULL,  -- References user.user_id (not users.id)
  
  -- Recipe identification
  recipe_id INTEGER,  -- Spoonacular recipe ID (if applicable)
  recipe_title STRING NOT NULL,
  recipe_image STRING,
  
  -- Recipe details
  recipe_data JSON NOT NULL,  -- Complete recipe data including ingredients, instructions, etc.
  source STRING NOT NULL,  -- 'spoonacular', 'generated', 'custom', 'chat'
  source_reference STRING,  -- Additional reference (e.g., chat session ID, custom recipe ID)
  
  -- User interaction
  rating STRING DEFAULT 'neutral',  -- 'thumbs_up', 'thumbs_down', 'neutral'
  is_favorite BOOL DEFAULT FALSE,
  notes STRING,  -- User's personal notes about the recipe
  
  -- Recipe metadata
  prep_time INTEGER,  -- Preparation time in minutes
  cook_time INTEGER,  -- Cooking time in minutes
  total_time INTEGER,  -- Total time in minutes
  servings INTEGER,  -- Number of servings
  difficulty STRING,  -- 'easy', 'medium', 'hard'
  
  -- Categorization
  cuisine ARRAY<STRING>,  -- e.g., ['italian', 'mexican']
  dish_type ARRAY<STRING>,  -- e.g., ['main course', 'dessert']
  diet_labels ARRAY<STRING>,  -- e.g., ['vegetarian', 'gluten-free']
  tags ARRAY<STRING>,  -- User-defined tags
  
  -- Tracking fields
  times_cooked INTEGER DEFAULT 0,  -- How many times user has cooked this
  last_cooked_at TIMESTAMP,  -- When user last cooked this recipe
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

-- Create a view that joins user_recipes with user information for easier querying
CREATE OR REPLACE VIEW `adsp-34002-on02-prep-sense.Inventory.user_recipes_with_user` AS
SELECT 
  ur.*,
  u.user_name,
  u.first_name,
  u.last_name,
  u.email
FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes` ur
JOIN `adsp-34002-on02-prep-sense.Inventory.user` u ON ur.user_id = u.user_id;

-- Create a view to analyze recipe popularity across all users
CREATE OR REPLACE VIEW `adsp-34002-on02-prep-sense.Inventory.popular_recipes` AS
SELECT 
  recipe_id,
  recipe_title,
  recipe_image,
  source,
  COUNT(DISTINCT user_id) as saved_by_users,
  COUNTIF(rating = 'thumbs_up') as thumbs_up_count,
  COUNTIF(rating = 'thumbs_down') as thumbs_down_count,
  COUNTIF(is_favorite = TRUE) as favorite_count,
  SUM(times_cooked) as total_times_cooked,
  ARRAY_AGG(DISTINCT cuisine IGNORE NULLS) as cuisines,
  ARRAY_AGG(DISTINCT dish_type IGNORE NULLS) as dish_types
FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`,
  UNNEST(cuisine) as cuisine,
  UNNEST(dish_type) as dish_type
WHERE recipe_id IS NOT NULL
GROUP BY recipe_id, recipe_title, recipe_image, source
ORDER BY saved_by_users DESC;

-- Add sample data to test the table (optional - uncomment to use)
/*
INSERT INTO `adsp-34002-on02-prep-sense.Inventory.user_recipes` 
(id, user_id, recipe_id, recipe_title, recipe_image, recipe_data, source, rating, is_favorite, 
 prep_time, cook_time, total_time, servings, difficulty, cuisine, dish_type, diet_labels, 
 created_at, updated_at)
VALUES
(
  GENERATE_UUID(),
  111,  -- Samantha Smith's user_id
  654959,  -- Example Spoonacular recipe ID
  'Pasta Carbonara',
  'https://spoonacular.com/recipeImages/654959-312x231.jpg',
  JSON '{"ingredients": ["pasta", "eggs", "bacon", "parmesan"], "instructions": "..."}',
  'spoonacular',
  'thumbs_up',
  TRUE,
  15,
  20,
  35,
  4,
  'medium',
  ['italian'],
  ['main course', 'dinner'],
  [],
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
*/

-- Query examples for common use cases:

-- 1. Get all recipes saved by a user with their ratings
/*
SELECT * FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
WHERE user_id = 111
ORDER BY created_at DESC;
*/

-- 2. Get only liked recipes for a user
/*
SELECT * FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
WHERE user_id = 111 AND rating = 'thumbs_up'
ORDER BY created_at DESC;
*/

-- 3. Get recipes by cuisine type
/*
SELECT * FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
WHERE user_id = 111 AND 'italian' IN UNNEST(cuisine);
*/

-- 4. Get quick recipes (total time < 30 minutes)
/*
SELECT * FROM `adsp-34002-on02-prep-sense.Inventory.user_recipes`
WHERE user_id = 111 AND total_time < 30
ORDER BY total_time ASC;
*/