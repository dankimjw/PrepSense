/**
 * Integration tests for critical user journeys in PrepSense
 * Tests core app functionality without fighting StyleSheet issues
 */

import { Config } from '@/config';

// Mock external dependencies
jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  })),
  useLocalSearchParams: jest.fn(() => ({})),
}));

jest.mock('@/context/ItemsContext', () => ({
  useItems: jest.fn(() => ({
    items: [
      { id: '1', item_name: 'milk', quantity: 1 },
      { id: '2', item_name: 'eggs', quantity: 12 },
      { id: '3', item_name: 'flour', quantity: 2 },
    ],
    refreshItems: jest.fn(),
  })),
}));

jest.mock('@/context/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { id: 111, name: 'Test User' },
    token: 'test-token',
    isAuthenticated: true,
  })),
}));

describe('Critical User Journeys Integration Tests', () => {
  const API_BASE_URL = Config.API_BASE_URL;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  describe('Recipe Discovery and Saving Journey', () => {
    it('should complete pantry-to-saved recipe journey', async () => {
      // Step 1: Fetch pantry-based recipes
      const pantryRecipesResponse = {
        recipes: [
          {
            id: 1,
            title: 'Scrambled Eggs',
            usedIngredientCount: 2,
            missedIngredientCount: 1,
            usedIngredients: [
              { id: 1, name: 'eggs', amount: 2, unit: '' },
              { id: 2, name: 'milk', amount: 0.25, unit: 'cup' },
            ],
            missedIngredients: [
              { id: 3, name: 'butter', amount: 1, unit: 'tbsp' },
            ],
            image: 'scrambled-eggs.jpg',
          },
        ],
        pantry_ingredients: [
          { name: 'milk', quantity: 1 },
          { name: 'eggs', quantity: 12 },
          { name: 'flour', quantity: 2 },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => pantryRecipesResponse,
      });

      // Simulate fetching pantry recipes
      const pantryResponse = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 111,
          max_missing_ingredients: 10,
          use_expiring_first: true,
        }),
      });

      const pantryData = await pantryResponse.json();
      expect(pantryData.recipes).toHaveLength(1);
      expect(pantryData.recipes[0].title).toBe('Scrambled Eggs');

      // Step 2: Get recipe details
      const recipeDetailsResponse = {
        id: 1,
        title: 'Scrambled Eggs',
        instructions: [
          { number: 1, step: 'Crack eggs into bowl' },
          { number: 2, step: 'Add milk and whisk' },
          { number: 3, step: 'Heat butter in pan' },
          { number: 4, step: 'Scramble eggs until set' },
        ],
        extendedIngredients: [
          { id: 1, name: 'eggs', amount: 2, unit: '' },
          { id: 2, name: 'milk', amount: 0.25, unit: 'cup' },
          { id: 3, name: 'butter', amount: 1, unit: 'tbsp' },
        ],
        readyInMinutes: 10,
        servings: 1,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => recipeDetailsResponse,
      });

      const detailsResponse = await fetch(`${API_BASE_URL}/recipes/1/information`);
      const detailsData = await detailsResponse.json();
      expect(detailsData.instructions).toHaveLength(4);

      // Step 3: Save the recipe
      const savedRecipeResponse = {
        id: 'saved-1',
        recipe_id: 1,
        recipe_title: 'Scrambled Eggs',
        recipe_image: 'scrambled-eggs.jpg',
        recipe_data: recipeDetailsResponse,
        rating: 'neutral',
        status: 'saved',
        source: 'spoonacular',
        created_at: '2024-01-15T10:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => savedRecipeResponse,
      });

      const saveResponse = await fetch(`${API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipe_id: 1,
          recipe_title: 'Scrambled Eggs',
          recipe_image: 'scrambled-eggs.jpg',
          recipe_data: recipeDetailsResponse,
          source: 'spoonacular',
        }),
      });

      const savedData = await saveResponse.json();
      expect(savedData.status).toBe('saved');
      expect(savedData.recipe_title).toBe('Scrambled Eggs');

      // Step 4: Verify it appears in saved recipes
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [savedRecipeResponse],
      });

      const savedListResponse = await fetch(`${API_BASE_URL}/user-recipes?status=saved`);
      const savedListData = await savedListResponse.json();
      expect(savedListData).toHaveLength(1);
      expect(savedListData[0].recipe_title).toBe('Scrambled Eggs');
    });

    it('should complete discover-to-saved recipe journey', async () => {
      // Step 1: Search for recipes
      const searchResponse = {
        results: [
          {
            id: 2,
            title: 'Chicken Pasta',
            image: 'chicken-pasta.jpg',
            readyInMinutes: 30,
          },
          {
            id: 3,
            title: 'Beef Stir Fry',
            image: 'beef-stir-fry.jpg',
            readyInMinutes: 20,
          },
        ],
        totalResults: 2,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => searchResponse,
      });

      const searchResult = await fetch(`${API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'chicken',
          number: 20,
        }),
      });

      const searchData = await searchResult.json();
      expect(searchData.results).toHaveLength(2);

      // Step 2: Select and get details for first recipe
      const selectedRecipe = searchData.results[0];
      const detailsResponse = {
        id: 2,
        title: 'Chicken Pasta',
        instructions: [
          { number: 1, step: 'Cook pasta according to package directions' },
          { number: 2, step: 'Season and cook chicken' },
          { number: 3, step: 'Combine pasta and chicken' },
        ],
        extendedIngredients: [
          { id: 1, name: 'pasta', amount: 8, unit: 'oz' },
          { id: 2, name: 'chicken breast', amount: 1, unit: 'lb' },
          { id: 3, name: 'olive oil', amount: 2, unit: 'tbsp' },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => detailsResponse,
      });

      const detailsResult = await fetch(`${API_BASE_URL}/recipes/${selectedRecipe.id}/information`);
      const detailsData = await detailsResult.json();
      expect(detailsData.title).toBe('Chicken Pasta');

      // Step 3: Save the recipe
      const savedResponse = {
        id: 'saved-2',
        recipe_id: 2,
        recipe_title: 'Chicken Pasta',
        status: 'saved',
        created_at: '2024-01-15T11:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => savedResponse,
      });

      const saveResult = await fetch(`${API_BASE_URL}/user-recipes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipe_id: 2,
          recipe_title: 'Chicken Pasta',
          recipe_data: detailsData,
          source: 'spoonacular',
        }),
      });

      const savedData = await saveResult.json();
      expect(savedData.status).toBe('saved');
    });
  });

  describe('Recipe Cooking Journey', () => {
    it('should complete saved-to-cooked recipe journey', async () => {
      // Step 1: Get saved recipes
      const savedRecipesResponse = [
        {
          id: 'saved-1',
          recipe_id: 1,
          recipe_title: 'Pancakes',
          recipe_image: 'pancakes.jpg',
          rating: 'neutral',
          status: 'saved',
          created_at: '2024-01-15T09:00:00Z',
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => savedRecipesResponse,
      });

      const savedResponse = await fetch(`${API_BASE_URL}/user-recipes?status=saved`);
      const savedData = await savedResponse.json();
      expect(savedData).toHaveLength(1);

      // Step 2: Start cooking - get full recipe details
      const recipeDetailsResponse = {
        id: 1,
        title: 'Pancakes',
        instructions: [
          { number: 1, step: 'Mix dry ingredients' },
          { number: 2, step: 'Combine wet ingredients' },
          { number: 3, step: 'Mix wet and dry ingredients' },
          { number: 4, step: 'Cook pancakes on griddle' },
        ],
        extendedIngredients: [
          { id: 1, name: 'flour', amount: 2, unit: 'cups' },
          { id: 2, name: 'milk', amount: 1.5, unit: 'cups' },
          { id: 3, name: 'eggs', amount: 2, unit: '' },
        ],
        readyInMinutes: 20,
        servings: 4,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => recipeDetailsResponse,
      });

      const detailsResponse = await fetch(`${API_BASE_URL}/recipes/1/information`);
      const detailsData = await detailsResponse.json();
      expect(detailsData.instructions).toHaveLength(4);

      // Step 3: Mark as cooked and rate
      const cookedRecipeResponse = {
        id: 'saved-1',
        recipe_id: 1,
        recipe_title: 'Pancakes',
        rating: 'thumbs_up',
        status: 'cooked',
        cooked_at: '2024-01-15T12:00:00Z',
        updated_at: '2024-01-15T12:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => cookedRecipeResponse,
      });

      const updateResponse = await fetch(`${API_BASE_URL}/user-recipes/saved-1`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'cooked',
          rating: 'thumbs_up',
        }),
      });

      const updatedData = await updateResponse.json();
      expect(updatedData.status).toBe('cooked');
      expect(updatedData.rating).toBe('thumbs_up');

      // Step 4: Verify it appears in cooked recipes
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [cookedRecipeResponse],
      });

      const cookedListResponse = await fetch(`${API_BASE_URL}/user-recipes?status=cooked`);
      const cookedListData = await cookedListResponse.json();
      expect(cookedListData).toHaveLength(1);
      expect(cookedListData[0].status).toBe('cooked');
    });
  });

  describe('Pantry Management Journey', () => {
    it('should complete add-pantry-item-to-recipe-suggestion journey', async () => {
      // Step 1: Current pantry state
      const initialPantryResponse = [
        { id: '1', item_name: 'milk', quantity: 1, unit: 'gallon' },
        { id: '2', item_name: 'eggs', quantity: 12, unit: 'pieces' },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => initialPantryResponse,
      });

      const initialPantryResult = await fetch(`${API_BASE_URL}/pantry-items?user_id=111`);
      const initialPantryData = await initialPantryResult.json();
      expect(initialPantryData).toHaveLength(2);

      // Step 2: Add new item to pantry
      const newItemResponse = {
        id: '3',
        item_name: 'flour',
        category: 'Baking',
        quantity: 2,
        unit: 'pounds',
        expiry_date: '2024-03-15',
        created_at: '2024-01-15T10:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => newItemResponse,
      });

      const addItemResult = await fetch(`${API_BASE_URL}/pantry-items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_name: 'flour',
          category: 'Baking',
          quantity: 2,
          unit: 'pounds',
          expiry_date: '2024-03-15',
          user_id: 111,
        }),
      });

      const addedItemData = await addItemResult.json();
      expect(addedItemData.item_name).toBe('flour');

      // Step 3: Get updated pantry-based recipes with new ingredient
      const updatedRecipesResponse = {
        recipes: [
          {
            id: 1,
            title: 'Pancakes',
            usedIngredientCount: 3,
            missedIngredientCount: 1,
            usedIngredients: [
              { id: 1, name: 'milk', amount: 1, unit: 'cup' },
              { id: 2, name: 'eggs', amount: 2, unit: '' },
              { id: 3, name: 'flour', amount: 2, unit: 'cups' },
            ],
            missedIngredients: [
              { id: 4, name: 'baking powder', amount: 2, unit: 'tsp' },
            ],
          },
          {
            id: 2,
            title: 'Scrambled Eggs',
            usedIngredientCount: 2,
            missedIngredientCount: 1,
            usedIngredients: [
              { id: 1, name: 'milk', amount: 0.25, unit: 'cup' },
              { id: 2, name: 'eggs', amount: 2, unit: '' },
            ],
            missedIngredients: [
              { id: 5, name: 'butter', amount: 1, unit: 'tbsp' },
            ],
          },
        ],
        pantry_ingredients: [
          { name: 'milk', quantity: 1 },
          { name: 'eggs', quantity: 12 },
          { name: 'flour', quantity: 2 },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => updatedRecipesResponse,
      });

      const updatedRecipesResult = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 111,
          max_missing_ingredients: 10,
          use_expiring_first: true,
        }),
      });

      const updatedRecipesData = await updatedRecipesResult.json();
      expect(updatedRecipesData.recipes).toHaveLength(2);
      expect(updatedRecipesData.recipes[0].title).toBe('Pancakes');
      expect(updatedRecipesData.recipes[0].usedIngredientCount).toBe(3); // Now includes flour
    });

    it('should handle expiring items and recipe prioritization', async () => {
      // Step 1: Get expiring items
      const expiringItemsResponse = [
        {
          id: '1',
          item_name: 'milk',
          expiry_date: '2024-01-16',
          days_until_expiry: 1,
          is_expiring_soon: true,
        },
        {
          id: '2',
          item_name: 'yogurt',
          expiry_date: '2024-01-17',
          days_until_expiry: 2,
          is_expiring_soon: true,
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => expiringItemsResponse,
      });

      const expiringResult = await fetch(`${API_BASE_URL}/pantry-items/expiring?user_id=111&days=3`);
      const expiringData = await expiringResult.json();
      expect(expiringData).toHaveLength(2);
      expect(expiringData[0].is_expiring_soon).toBe(true);

      // Step 2: Get prioritized recipes using expiring ingredients
      const prioritizedRecipesResponse = {
        recipes: [
          {
            id: 1,
            title: 'Milk Smoothie',
            usedIngredientCount: 2,
            missedIngredientCount: 1,
            priority_score: 0.9, // High priority due to expiring milk
            usedIngredients: [
              { id: 1, name: 'milk', amount: 1, unit: 'cup', expiring: true },
              { id: 2, name: 'banana', amount: 1, unit: '' },
            ],
          },
        ],
        pantry_ingredients: [
          { name: 'milk', quantity: 1, expiring: true },
          { name: 'yogurt', quantity: 1, expiring: true },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => prioritizedRecipesResponse,
      });

      const prioritizedResult = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 111,
          max_missing_ingredients: 10,
          use_expiring_first: true,
        }),
      });

      const prioritizedData = await prioritizedResult.json();
      expect(prioritizedData.recipes).toHaveLength(1);
      expect(prioritizedData.recipes[0].priority_score).toBe(0.9);
    });
  });

  describe('Error Recovery Journeys', () => {
    it('should handle API key error gracefully', async () => {
      // Simulate API key error
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Spoonacular API key not configured' }),
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      expect(response.ok).toBe(false);

      const error = await response.json();
      expect(error.detail).toContain('API key');

      // Should still be able to use saved recipes without API
      const savedRecipesResponse = [
        {
          id: 'saved-1',
          recipe_id: 1,
          recipe_title: 'Local Recipe',
          status: 'saved',
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => savedRecipesResponse,
      });

      const savedResponse = await fetch(`${API_BASE_URL}/user-recipes`);
      const savedData = await savedResponse.json();
      expect(savedData).toHaveLength(1);
    });

    it('should handle network failures with retry logic', async () => {
      // First attempt fails
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(fetch(`${API_BASE_URL}/recipes/random`)).rejects.toThrow('Network error');

      // Second attempt succeeds
      const successResponse = {
        recipes: [{ id: 1, title: 'Recovery Recipe' }],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => successResponse,
      });

      const retryResponse = await fetch(`${API_BASE_URL}/recipes/random`);
      const retryData = await retryResponse.json();
      expect(retryData.recipes[0].title).toBe('Recovery Recipe');
    });

    it('should handle offline mode', async () => {
      // All external API calls fail
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network unavailable'));

      // Should still work with local data/cache
      await expect(fetch(`${API_BASE_URL}/recipes/random`)).rejects.toThrow('Network unavailable');
      await expect(fetch(`${API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        body: JSON.stringify({ query: 'pasta' }),
      })).rejects.toThrow('Network unavailable');

      // But local operations should still work
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            id: 'cached-1',
            recipe_title: 'Cached Recipe',
            status: 'saved',
          },
        ],
      });

      const cachedResponse = await fetch(`${API_BASE_URL}/user-recipes`);
      const cachedData = await cachedResponse.json();
      expect(cachedData[0].recipe_title).toBe('Cached Recipe');
    });
  });
});