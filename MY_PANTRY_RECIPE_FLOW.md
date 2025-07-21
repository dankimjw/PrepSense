# My Pantry Recipe Flow Documentation

## Overview
The "From Pantry" tab in the Recipe screen shows recipes that can be made with ingredients currently in the user's pantry. This document traces the complete data flow from backend to frontend.

## Frontend Implementation

### Key Files
- **Main Screen**: `ios-app/app/(tabs)/recipes.tsx`
- **Supporting Utils**: `ios-app/utils/ingredientMatcher.ts`

### Frontend Flow

1. **Tab Selection** (recipes.tsx:1063-1069)
   - User clicks "From Pantry" tab
   - Sets `activeTab = 'pantry'`
   - Triggers `useEffect` to call `fetchRecipesFromPantry()`

2. **Fetch Recipes** (recipes.tsx:169-232)
   ```typescript
   const fetchRecipesFromPantry = useCallback(async () => {
     // API call to backend
     const response = await fetch(`${Config.API_BASE_URL}/recipes/search/from-pantry`, {
       method: 'POST',
       body: JSON.stringify({
         user_id: 111,  // Hardcoded demo user
         max_missing_ingredients: 10,
         use_expiring_first: true,
       }),
     });
   ```

3. **Process Response** (recipes.tsx:194-226)
   - Receives recipes and pantry ingredients from backend
   - Stores pantry ingredients for count calculation
   - Filters to only include valid Spoonacular recipes
   - Recalculates ingredient counts using `recalculateIngredientCounts()`

4. **Ingredient Matching** (recipes.tsx:140-167)
   - Uses `calculateIngredientAvailability()` from `ingredientMatcher.ts`
   - Matches recipe ingredients against pantry items
   - Returns accurate have/missing counts

5. **Display Recipes** (recipes.tsx:887-933)
   - Renders recipe cards in a grid
   - Shows ingredient badges: ✓ X have, ✗ Y missing
   - Allows bookmarking and navigation to details

## Backend Implementation

### Key Files
- **Router**: `backend_gateway/routers/spoonacular_router.py`
- **Services**: 
  - `backend_gateway/services/spoonacular_service.py`
  - `backend_gateway/services/pantry_service.py`

### Backend Flow

1. **Endpoint Handler** (spoonacular_router.py:283-289)
   ```python
   @router.post("/search/from-pantry")
   async def search_recipes_from_pantry(
       request: RecipeFromPantryRequest,
       spoonacular_service: SpoonacularService = Depends(),
       pantry_service: PantryService = Depends(),
       db_service = Depends()
   ):
   ```

2. **Get Pantry Items** (spoonacular_router.py:294-346)
   - Fetches user's pantry items from database
   - Aggregates quantities by ingredient name
   - Identifies expiring items (within 3 days)
   - Normalizes and cleans ingredient names

3. **Prioritize Ingredients** (spoonacular_router.py:348-372)
   - If `use_expiring_first=true`: prioritizes expiring items
   - Otherwise: sorts by quantity (use items with more quantity)
   - Limits to top 5 ingredients to avoid API timeouts
   - Cleans ingredient names (removes brand names)

4. **Get User Preferences** (spoonacular_router.py:376-390)
   - Fetches user allergens from database
   - Gets cuisine preferences if available

5. **Search Spoonacular API** (spoonacular_service.py)
   - Calls `search_recipes_by_ingredients()` method
   - If allergens exist: uses `complexSearch` endpoint for better filtering
   - Otherwise: uses `findByIngredients` endpoint
   - Parameters:
     - ingredients: cleaned ingredient list
     - number: max recipes to return
     - ranking: 1 (minimize missing ingredients)
     - intolerances: user allergens

6. **Process Results** (spoonacular_router.py:400-450)
   - Formats recipe data
   - Adds match percentage calculation
   - Returns:
     ```json
     {
       "recipes": [...],
       "pantry_ingredients": [...],
       "total_pantry_items": 25,
       "message": "Found X recipes using Y pantry items"
     }
     ```

## Database Queries

### Get Pantry Items
```sql
SELECT * FROM pantry_items 
WHERE user_id = %(user_id)s 
  AND (expiration_date IS NULL OR expiration_date > CURRENT_DATE)
ORDER BY expiration_date ASC NULLS LAST
```

### Get User Allergens
```sql
SELECT allergen FROM user_allergens 
WHERE user_id = %(user_id)s
```

### Get Cuisine Preferences
```sql
SELECT cuisine_type, preference_level 
FROM cuisine_preferences 
WHERE user_id = %(user_id)s 
ORDER BY preference_level DESC
```

## Key Features

1. **Expiring Items Priority**: Recipes using soon-to-expire items appear first
2. **Allergen Filtering**: Excludes recipes with user's allergens
3. **Ingredient Aggregation**: Combines same ingredients from multiple pantry entries
4. **Smart Matching**: Uses normalized names for better recipe matching
5. **Performance Optimization**: 
   - Limits to 5 ingredients for API calls
   - Caches results for 30 minutes
   - Validates recipe quality before displaying

## Data Transformation Pipeline

1. **Pantry Items** → Normalized ingredients list
2. **Ingredients** → Spoonacular API search
3. **API Results** → Filtered & validated recipes
4. **Recipes** → Recalculated have/missing counts
5. **Final Data** → UI recipe cards with badges

## Error Handling

- Missing API key: Shows alert with setup instructions
- Empty pantry: Returns empty recipe list with message
- API failures: Shows error alert, allows retry
- Invalid recipes: Filters out using `isValidRecipe()`