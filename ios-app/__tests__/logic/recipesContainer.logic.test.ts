/**
 * Test the business logic of RecipesContainer without importing the component
 * This bypasses StyleSheet.create issues and focuses on pure logic testing
 */

import {
  recipesReducer,
  getInitialState,
  recalculateIngredientCounts,
  filterSavedRecipes,
  filterValidRecipes,
  sortRecipes,
  sortSavedRecipes,
  buildApiFilterParams,
  shouldUsePreloadedData,
  processApiError,
  updateRecipesWithCounts,
  Recipe,
  SavedRecipe,
  RecipesState,
  RecipesAction,
  MyRecipesFilter,
  MyRecipesTab,
  SortOption
} from '../../logic/recipesContainer.logic';

describe('RecipesContainer Logic Tests', () => {
  
  describe('Initial State', () => {
    it('should return correct initial state', () => {
      const initialState = getInitialState();
      
      expect(initialState.recipes).toEqual([]);
      expect(initialState.savedRecipes).toEqual([]);
      expect(initialState.loading).toBe(false);
      expect(initialState.refreshing).toBe(false);
      expect(initialState.searchQuery).toBe('');
      expect(initialState.activeTab).toBe('pantry');
      expect(initialState.selectedFilters).toEqual([]);
      expect(initialState.myRecipesFilter).toBe('all');
      expect(initialState.myRecipesTab).toBe('saved');
      expect(initialState.sortBy).toBe('name');
      expect(initialState.showSortModal).toBe(false);
      expect(initialState.searchFocused).toBe(false);
      expect(initialState.filtersCollapsed).toBe(false);
      expect(initialState.scrollOffset).toBe(0);
      expect(initialState.pantryIngredients).toEqual([]);
    });
  });

  describe('Recipes Reducer', () => {
    let initialState: RecipesState;

    beforeEach(() => {
      initialState = getInitialState();
    });

    it('should handle SET_RECIPES action', () => {
      const recipes: Recipe[] = [
        {
          id: 1,
          title: 'Test Recipe',
          image: 'test.jpg',
          imageType: 'jpg',
          usedIngredientCount: 2,
          missedIngredientCount: 1,
          missedIngredients: [],
          usedIngredients: [],
          likes: 10
        }
      ];

      const action: RecipesAction = { type: 'SET_RECIPES', payload: recipes };
      const newState = recipesReducer(initialState, action);

      expect(newState.recipes).toEqual(recipes);
      expect(newState.recipes).not.toBe(initialState.recipes); // Ensure immutability
    });

    it('should handle SET_LOADING action', () => {
      const action: RecipesAction = { type: 'SET_LOADING', payload: true };
      const newState = recipesReducer(initialState, action);

      expect(newState.loading).toBe(true);
      expect(newState).not.toBe(initialState); // Ensure immutability
    });

    it('should handle SET_ACTIVE_TAB action', () => {
      const action: RecipesAction = { type: 'SET_ACTIVE_TAB', payload: 'discover' };
      const newState = recipesReducer(initialState, action);

      expect(newState.activeTab).toBe('discover');
    });

    it('should handle UPDATE_SAVED_RECIPE action', () => {
      const savedRecipes: SavedRecipe[] = [
        {
          id: '1',
          recipe_id: 100,
          recipe_title: 'Saved Recipe',
          recipe_image: 'saved.jpg',
          recipe_data: {},
          rating: 'neutral',
          source: 'spoonacular',
          created_at: '2024-01-01',
          updated_at: '2024-01-01'
        }
      ];

      const stateWithSavedRecipes = { ...initialState, savedRecipes };
      
      const action: RecipesAction = {
        type: 'UPDATE_SAVED_RECIPE',
        payload: { id: '1', updates: { rating: 'thumbs_up', is_favorite: true } }
      };
      
      const newState = recipesReducer(stateWithSavedRecipes, action);

      expect(newState.savedRecipes[0].rating).toBe('thumbs_up');
      expect(newState.savedRecipes[0].is_favorite).toBe(true);
      expect(newState.savedRecipes[0].recipe_title).toBe('Saved Recipe'); // Unchanged
    });

    it('should return unchanged state for unknown action', () => {
      const unknownAction = { type: 'UNKNOWN_ACTION' } as any;
      const newState = recipesReducer(initialState, unknownAction);

      expect(newState).toBe(initialState);
    });
  });

  describe('Ingredient Count Recalculation', () => {
    const mockCalculateAvailability = jest.fn();

    beforeEach(() => {
      mockCalculateAvailability.mockClear();
    });

    it('should recalculate ingredient counts correctly', () => {
      const recipe: Recipe = {
        id: 1,
        title: 'Test Recipe',
        image: 'test.jpg',
        imageType: 'jpg',
        usedIngredientCount: 2,
        missedIngredientCount: 1,
        missedIngredients: [
          { id: 1, amount: 1, unit: 'cup', name: 'flour', image: 'flour.jpg' }
        ],
        usedIngredients: [
          { id: 2, amount: 2, unit: 'pcs', name: 'eggs', image: 'eggs.jpg' }
        ],
        likes: 10
      };

      const pantryItems = ['eggs', 'milk'];

      mockCalculateAvailability.mockReturnValue({
        availableCount: 1,
        missingCount: 2
      });

      const result = recalculateIngredientCounts(recipe, pantryItems, mockCalculateAvailability);

      expect(result.usedCount).toBe(1);
      expect(result.missedCount).toBe(2);
      expect(mockCalculateAvailability).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ name: 'flour' }),
          expect.objectContaining({ name: 'eggs' })
        ]),
        expect.arrayContaining([
          { product_name: 'eggs' },
          { product_name: 'milk' }
        ])
      );
    });

    it('should handle recipes with no ingredients', () => {
      const recipe: Recipe = {
        id: 1,
        title: 'Test Recipe',
        image: 'test.jpg',
        imageType: 'jpg',
        usedIngredientCount: 0,
        missedIngredientCount: 0,
        missedIngredients: [],
        usedIngredients: [],
        likes: 10
      };

      mockCalculateAvailability.mockReturnValue({
        availableCount: 0,
        missingCount: 0
      });

      const result = recalculateIngredientCounts(recipe, [], mockCalculateAvailability);

      expect(result.usedCount).toBe(0);
      expect(result.missedCount).toBe(0);
    });
  });

  describe('Saved Recipes Filtering', () => {
    const savedRecipes: SavedRecipe[] = [
      {
        id: '1',
        recipe_id: 100,
        recipe_title: 'Recipe 1',
        recipe_image: 'recipe1.jpg',
        recipe_data: {},
        rating: 'thumbs_up',
        is_favorite: true,
        source: 'spoonacular',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
      },
      {
        id: '2',
        recipe_id: 101,
        recipe_title: 'Recipe 2',
        recipe_image: 'recipe2.jpg',
        recipe_data: {},
        rating: 'thumbs_down',
        source: 'spoonacular',
        created_at: '2024-01-02',
        updated_at: '2024-01-02'
      },
      {
        id: '3',
        recipe_id: 102,
        recipe_title: 'Recipe 3',
        recipe_image: 'recipe3.jpg',
        recipe_data: {},
        rating: 'neutral',
        is_favorite: true,
        source: 'spoonacular',
        created_at: '2024-01-03',
        updated_at: '2024-01-03'
      }
    ];

    it('should filter by thumbs_up rating', () => {
      const result = filterSavedRecipes(savedRecipes, 'thumbs_up', 'saved');
      
      expect(result).toHaveLength(1);
      expect(result[0].rating).toBe('thumbs_up');
    });

    it('should filter by thumbs_down rating', () => {
      const result = filterSavedRecipes(savedRecipes, 'thumbs_down', 'saved');
      
      expect(result).toHaveLength(1);
      expect(result[0].rating).toBe('thumbs_down');
    });

    it('should filter by favorites', () => {
      const result = filterSavedRecipes(savedRecipes, 'favorites', 'saved');
      
      expect(result).toHaveLength(2);
      expect(result.every(recipe => recipe.is_favorite)).toBe(true);
    });

    it('should return all recipes for all filter', () => {
      const result = filterSavedRecipes(savedRecipes, 'all', 'saved');
      
      expect(result).toHaveLength(3);
      expect(result).toEqual(savedRecipes);
    });
  });

  describe('Recipe Validation', () => {
    const mockIsValidRecipe = jest.fn();

    beforeEach(() => {
      mockIsValidRecipe.mockClear();
    });

    it('should filter out recipes with invalid IDs', () => {
      const recipes = [
        { id: 1, title: 'Valid Recipe' },
        { id: null, title: 'Invalid - No ID' },
        { id: 'string', title: 'Invalid - String ID' },
        { id: 0, title: 'Invalid - Zero ID' },
        { id: -1, title: 'Invalid - Negative ID' },
        { id: 2, title: 'Another Valid Recipe' }
      ] as Recipe[];

      const result = filterValidRecipes(recipes);

      expect(result).toHaveLength(2);
      expect(result[0].title).toBe('Valid Recipe');
      expect(result[1].title).toBe('Another Valid Recipe');
    });

    it('should apply additional validation when provided', () => {
      const recipes = [
        { id: 1, title: 'Recipe 1' },
        { id: 2, title: 'Recipe 2' },
        { id: 3, title: 'Recipe 3' }
      ] as Recipe[];

      mockIsValidRecipe
        .mockReturnValueOnce(true)
        .mockReturnValueOnce(false)
        .mockReturnValueOnce(true);

      const result = filterValidRecipes(recipes, mockIsValidRecipe);

      expect(result).toHaveLength(2);
      expect(result[0].title).toBe('Recipe 1');
      expect(result[1].title).toBe('Recipe 3');
      expect(mockIsValidRecipe).toHaveBeenCalledTimes(3);
    });
  });

  describe('Recipe Sorting', () => {
    const recipes: Recipe[] = [
      {
        id: 1,
        title: 'Banana Bread',
        image: 'banana.jpg',
        imageType: 'jpg',
        usedIngredientCount: 3,
        missedIngredientCount: 1,
        missedIngredients: [],
        usedIngredients: [],
        likes: 50
      },
      {
        id: 2,
        title: 'Apple Pie',
        image: 'apple.jpg',
        imageType: 'jpg',
        usedIngredientCount: 2,
        missedIngredientCount: 3,
        missedIngredients: [],
        usedIngredients: [],
        likes: 100
      },
      {
        id: 3,
        title: 'Chocolate Cake',
        image: 'chocolate.jpg',
        imageType: 'jpg',
        usedIngredientCount: 1,
        missedIngredientCount: 2,
        missedIngredients: [],
        usedIngredients: [],
        likes: 75
      }
    ];

    it('should sort by name alphabetically', () => {
      const result = sortRecipes(recipes, 'name');
      
      expect(result[0].title).toBe('Apple Pie');
      expect(result[1].title).toBe('Banana Bread');
      expect(result[2].title).toBe('Chocolate Cake');
    });

    it('should sort by missing ingredients count', () => {
      const result = sortRecipes(recipes, 'missing');
      
      expect(result[0].missedIngredientCount).toBe(1);
      expect(result[1].missedIngredientCount).toBe(2);
      expect(result[2].missedIngredientCount).toBe(3);
    });

    it('should sort by rating (likes) descending', () => {
      const result = sortRecipes(recipes, 'rating');
      
      expect(result[0].likes).toBe(100);
      expect(result[1].likes).toBe(75);
      expect(result[2].likes).toBe(50);
    });

    it('should preserve original order for date sort', () => {
      const result = sortRecipes(recipes, 'date');
      
      expect(result).toEqual(recipes);
    });

    it('should not mutate original array', () => {
      const originalOrder = recipes.map(r => r.title);
      sortRecipes(recipes, 'name');
      
      expect(recipes.map(r => r.title)).toEqual(originalOrder);
    });
  });

  describe('Saved Recipe Sorting', () => {
    const savedRecipes: SavedRecipe[] = [
      {
        id: '1',
        recipe_id: 100,
        recipe_title: 'Zebra Cake',
        recipe_image: 'zebra.jpg',
        recipe_data: {},
        rating: 'thumbs_up',
        source: 'spoonacular',
        created_at: '2024-01-01T10:00:00Z',
        updated_at: '2024-01-01T10:00:00Z'
      },
      {
        id: '2',
        recipe_id: 101,
        recipe_title: 'Apple Tart',
        recipe_image: 'apple.jpg',
        recipe_data: {},
        rating: 'neutral',
        source: 'spoonacular',
        created_at: '2024-01-03T10:00:00Z',
        updated_at: '2024-01-03T10:00:00Z'
      },
      {
        id: '3',
        recipe_id: 102,
        recipe_title: 'Banana Muffins',
        recipe_image: 'banana.jpg',
        recipe_data: {},
        rating: 'thumbs_down',
        source: 'spoonacular',
        created_at: '2024-01-02T10:00:00Z',
        updated_at: '2024-01-02T10:00:00Z'
      }
    ];

    it('should sort by name alphabetically', () => {
      const result = sortSavedRecipes(savedRecipes, 'name');
      
      expect(result[0].recipe_title).toBe('Apple Tart');
      expect(result[1].recipe_title).toBe('Banana Muffins');
      expect(result[2].recipe_title).toBe('Zebra Cake');
    });

    it('should sort by date descending (newest first)', () => {
      const result = sortSavedRecipes(savedRecipes, 'date');
      
      expect(result[0].created_at).toBe('2024-01-03T10:00:00Z');
      expect(result[1].created_at).toBe('2024-01-02T10:00:00Z');
      expect(result[2].created_at).toBe('2024-01-01T10:00:00Z');
    });

    it('should sort by rating (thumbs_up > neutral > thumbs_down)', () => {
      const result = sortSavedRecipes(savedRecipes, 'rating');
      
      expect(result[0].rating).toBe('thumbs_up');
      expect(result[1].rating).toBe('neutral');
      expect(result[2].rating).toBe('thumbs_down');
    });
  });

  describe('API Filter Parameters', () => {
    it('should build filter params for saved recipes', () => {
      const result = buildApiFilterParams('saved', 'thumbs_up');
      
      expect(result.statusFilter).toBe('?status=saved');
      expect(result.additionalFilters).toBe('&rating=thumbs_up');
      expect(result.fullPath).toBe('?status=saved&rating=thumbs_up');
    });

    it('should build filter params for cooked recipes', () => {
      const result = buildApiFilterParams('cooked', 'all');
      
      expect(result.statusFilter).toBe('?status=cooked');
      expect(result.additionalFilters).toBe('');
      expect(result.fullPath).toBe('?status=cooked');
    });

    it('should build filter params for favorites', () => {
      const result = buildApiFilterParams('saved', 'favorites');
      
      expect(result.statusFilter).toBe('?status=saved');
      expect(result.additionalFilters).toBe('&is_favorite=true');
      expect(result.fullPath).toBe('?status=saved&is_favorite=true');
    });

    it('should handle no status filter', () => {
      // Simulating when myRecipesTab is neither 'saved' nor 'cooked'
      const result = buildApiFilterParams('' as MyRecipesTab, 'thumbs_up');
      
      expect(result.statusFilter).toBe('');
      expect(result.additionalFilters).toBe('?rating=thumbs_up');
      expect(result.fullPath).toBe('?rating=thumbs_up');
    });
  });

  describe('Preloaded Data Logic', () => {
    it('should use preloaded data when available and not refreshing', () => {
      const result = shouldUsePreloadedData({ recipes: [] }, false);
      expect(result).toBe(true);
    });

    it('should not use preloaded data when refreshing', () => {
      const result = shouldUsePreloadedData({ recipes: [] }, true);
      expect(result).toBe(false);
    });

    it('should not use preloaded data when not available', () => {
      const result = shouldUsePreloadedData(null, false);
      expect(result).toBe(false);
    });
  });

  describe('API Error Processing', () => {
    it('should identify API key errors', () => {
      const response = { status: 400 } as Response;
      const errorData = { detail: 'Spoonacular API key not configured' };
      
      const result = processApiError(response, errorData);
      
      expect(result.isApiKeyError).toBe(true);
      expect(result.shouldShowApiKeyAlert).toBe(true);
      expect(result.errorMessage).toBe('Spoonacular API key not configured');
    });

    it('should identify non-API key errors', () => {
      const response = { status: 500 } as Response;
      const errorData = { detail: 'Internal server error' };
      
      const result = processApiError(response, errorData);
      
      expect(result.isApiKeyError).toBe(false);
      expect(result.shouldShowApiKeyAlert).toBe(false);
      expect(result.errorMessage).toBe('API request failed');
    });
  });

  describe('Update Recipes with Counts', () => {
    const mockCalculateAvailability = jest.fn();

    beforeEach(() => {
      mockCalculateAvailability.mockClear();
    });

    it('should update all recipes with recalculated counts', () => {
      const recipes: Recipe[] = [
        {
          id: 1,
          title: 'Recipe 1',
          image: 'recipe1.jpg',
          imageType: 'jpg',
          usedIngredientCount: 2,
          missedIngredientCount: 1,
          missedIngredients: [],
          usedIngredients: [],
          likes: 10
        },
        {
          id: 2,
          title: 'Recipe 2',
          image: 'recipe2.jpg',
          imageType: 'jpg',
          usedIngredientCount: 1,
          missedIngredientCount: 2,
          missedIngredients: [],
          usedIngredients: [],
          likes: 5
        }
      ];

      const pantryIngredients = ['flour', 'eggs'];

      mockCalculateAvailability
        .mockReturnValueOnce({ availableCount: 3, missingCount: 0 })
        .mockReturnValueOnce({ availableCount: 1, missingCount: 1 });

      const result = updateRecipesWithCounts(recipes, pantryIngredients, mockCalculateAvailability);

      expect(result).toHaveLength(2);
      expect(result[0].usedIngredientCount).toBe(3);
      expect(result[0].missedIngredientCount).toBe(0);
      expect(result[1].usedIngredientCount).toBe(1);
      expect(result[1].missedIngredientCount).toBe(1);
      
      // Ensure original recipes are not mutated
      expect(recipes[0].usedIngredientCount).toBe(2);
      expect(recipes[1].usedIngredientCount).toBe(1);
    });
  });
});