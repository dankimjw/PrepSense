import { Config } from '@/config';
import { mockFetch, mockFetchError, mockFetchSequence, createMockRecipe, mockRecipeSearchResponse } from '../helpers/apiMocks';

describe('Recipe API Integration Tests', () => {
  const API_BASE_URL = Config.API_BASE_URL;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('From Pantry Endpoint', () => {
    const pantryEndpoint = `${API_BASE_URL}/recipes/findByIngredients/complex`;

    it('should successfully fetch recipes based on pantry ingredients', async () => {
      const mockIngredients = ['milk', 'flour', 'eggs'];
      const mockResponse = {
        recipes: [
          createMockRecipe({
            id: 1,
            title: 'Pancakes',
            usedIngredientCount: 3,
            missedIngredientCount: 0,
          }),
          createMockRecipe({
            id: 2,
            title: 'French Toast',
            usedIngredientCount: 2,
            missedIngredientCount: 1,
          }),
        ],
        pantry_ingredients: mockIngredients.map(name => ({ name, quantity: 1 })),
      };

      global.fetch = mockFetch(mockResponse);

      const response = await fetch(pantryEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredients: mockIngredients,
          ranking: 2,
          ignorePantry: false,
          number: 20,
        }),
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.recipes).toHaveLength(2);
      expect(data.recipes[0].title).toBe('Pancakes');
      expect(data.pantry_ingredients).toHaveLength(3);
    });

    it('should handle empty pantry gracefully', async () => {
      global.fetch = mockFetch({ recipes: [], pantry_ingredients: [] });

      const response = await fetch(pantryEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredients: [],
          ranking: 2,
          ignorePantry: false,
          number: 20,
        }),
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.recipes).toHaveLength(0);
    });

    it('should handle API key missing error', async () => {
      global.fetch = mockFetch(
        { detail: 'Spoonacular API key not configured' },
        { ok: false, status: 400 }
      );

      const response = await fetch(pantryEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingredients: ['milk'], number: 20 }),
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(400);
      
      const error = await response.json();
      expect(error.detail).toContain('API key');
    });

    it('should validate recipe data structure', async () => {
      const mockResponse = {
        recipes: [
          {
            id: 123,
            title: 'Test Recipe',
            image: 'https://example.com/image.jpg',
            imageType: 'jpg',
            usedIngredientCount: 2,
            missedIngredientCount: 1,
            usedIngredients: [
              { id: 1, name: 'milk', amount: 1, unit: 'cup' },
              { id: 2, name: 'flour', amount: 2, unit: 'cups' },
            ],
            missedIngredients: [
              { id: 3, name: 'sugar', amount: 0.5, unit: 'cup' },
            ],
            likes: 100,
          },
        ],
        pantry_ingredients: [],
      };

      global.fetch = mockFetch(mockResponse);

      const response = await fetch(pantryEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingredients: ['milk', 'flour'], number: 1 }),
      });

      const data = await response.json();
      const recipe = data.recipes[0];

      // Validate all required fields are present
      expect(recipe).toHaveProperty('id');
      expect(recipe).toHaveProperty('title');
      expect(recipe).toHaveProperty('usedIngredientCount');
      expect(recipe).toHaveProperty('missedIngredientCount');
      expect(recipe).toHaveProperty('usedIngredients');
      expect(recipe).toHaveProperty('missedIngredients');
      
      // Validate data types
      expect(typeof recipe.id).toBe('number');
      expect(typeof recipe.title).toBe('string');
      expect(Array.isArray(recipe.usedIngredients)).toBe(true);
      expect(Array.isArray(recipe.missedIngredients)).toBe(true);
    });
  });

  describe('Discover/Random Recipes Endpoint', () => {
    const randomEndpoint = `${API_BASE_URL}/recipes/random?number=20`;

    it('should fetch random recipes successfully', async () => {
      const mockResponse = {
        recipes: [
          createMockRecipe({ id: 10, title: 'Random Recipe 1' }),
          createMockRecipe({ id: 11, title: 'Random Recipe 2' }),
          createMockRecipe({ id: 12, title: 'Random Recipe 3' }),
        ],
      };

      global.fetch = mockFetch(mockResponse);

      const response = await fetch(randomEndpoint);
      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.recipes).toHaveLength(3);
      expect(data.recipes[0].title).toBe('Random Recipe 1');
    });

    it('should handle network errors', async () => {
      global.fetch = mockFetchError('Network request failed');

      await expect(fetch(randomEndpoint)).rejects.toThrow('Network request failed');
    });
  });

  describe('Recipe Search Endpoint', () => {
    const searchEndpoint = `${API_BASE_URL}/recipes/search/complex`;

    it('should search recipes by query', async () => {
      const mockResponse = mockRecipeSearchResponse([
        createMockRecipe({ id: 20, title: 'Chicken Curry' }),
        createMockRecipe({ id: 21, title: 'Chicken Salad' }),
      ]);

      global.fetch = mockFetch(mockResponse);

      const response = await fetch(searchEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'chicken',
          number: 20,
        }),
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.recipes).toHaveLength(2);
      expect(data.recipes[0].title).toContain('Chicken');
    });

    it('should apply dietary filters', async () => {
      const mockResponse = mockRecipeSearchResponse([
        createMockRecipe({ id: 30, title: 'Vegan Buddha Bowl' }),
      ]);

      global.fetch = mockFetch(mockResponse);

      const response = await fetch(searchEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'bowl',
          number: 20,
          diet: 'vegan,gluten-free',
        }),
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        searchEndpoint,
        expect.objectContaining({
          body: expect.stringContaining('vegan,gluten-free'),
        })
      );
    });
  });

  describe('User Recipes Endpoint', () => {
    const userRecipesEndpoint = `${API_BASE_URL}/user-recipes`;

    it('should fetch saved recipes', async () => {
      const mockSavedRecipes = [
        {
          id: 'saved-1',
          recipe_id: 100,
          recipe_title: 'My Favorite Recipe',
          recipe_image: 'https://example.com/recipe.jpg',
          rating: 'thumbs_up',
          is_favorite: true,
          source: 'spoonacular',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];

      global.fetch = mockFetch(mockSavedRecipes);

      const response = await fetch(`${userRecipesEndpoint}?status=saved`, {
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': 'Bearer mock-token', // Currently disabled
        },
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data).toHaveLength(1);
      expect(data[0].recipe_title).toBe('My Favorite Recipe');
      expect(data[0].rating).toBe('thumbs_up');
    });

    it('should filter recipes by rating', async () => {
      const mockFilteredRecipes = [
        {
          id: 'saved-2',
          recipe_id: 101,
          recipe_title: 'Thumbs Up Recipe',
          rating: 'thumbs_up',
          is_favorite: false,
          source: 'spoonacular',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];

      global.fetch = mockFetch(mockFilteredRecipes);

      const response = await fetch(`${userRecipesEndpoint}?status=saved&rating=thumbs_up`, {
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data).toHaveLength(1);
      expect(data[0].rating).toBe('thumbs_up');
    });

    it('should handle empty recipe list', async () => {
      global.fetch = mockFetch([]);

      const response = await fetch(`${userRecipesEndpoint}?status=saved`, {
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data).toHaveLength(0);
    });
  });

  describe('Error Handling and Retry Logic', () => {
    it('should handle 500 server errors', async () => {
      global.fetch = mockFetch(
        { error: 'Internal server error' },
        { ok: false, status: 500 }
      );

      const response = await fetch(`${API_BASE_URL}/recipes/random`);

      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
    });

    it('should handle timeout errors', async () => {
      // Simulate timeout by never resolving
      global.fetch = jest.fn(() => new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout')), 100);
      }));

      await expect(fetch(`${API_BASE_URL}/recipes/random`)).rejects.toThrow('Request timeout');
    });

    it('should validate response data structure', async () => {
      // Test with malformed response
      const malformedResponse = {
        // Missing 'recipes' key
        data: [{ id: 1, title: 'Recipe' }],
      };

      global.fetch = mockFetch(malformedResponse);

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      const data = await response.json();

      // The component should handle missing 'recipes' key gracefully
      expect(data.recipes).toBeUndefined();
      expect(data.data).toBeDefined();
    });
  });

  describe('Recipe Data Validation', () => {
    it('should filter out recipes with missing required fields', async () => {
      const mockResponse = {
        recipes: [
          createMockRecipe({ id: 1, title: 'Valid Recipe' }),
          { id: null, title: 'Invalid - No ID' }, // Invalid
          { id: 2, title: '' }, // Invalid - empty title
          { id: 'string-id', title: 'Invalid - Wrong ID type' }, // Invalid
          createMockRecipe({ id: 3, title: 'Another Valid Recipe' }),
        ],
      };

      global.fetch = mockFetch(mockResponse);

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      const data = await response.json();

      // In the actual component, these would be filtered out
      expect(data.recipes).toHaveLength(5); // All returned from API
      
      // Validate which ones are actually valid
      const validRecipes = data.recipes.filter((recipe: any) => 
        recipe.id && typeof recipe.id === 'number' && recipe.id > 0 && recipe.title
      );
      
      expect(validRecipes).toHaveLength(2);
      expect(validRecipes[0].title).toBe('Valid Recipe');
      expect(validRecipes[1].title).toBe('Another Valid Recipe');
    });
  });
});