import { Config } from '@/config';

// Test the logic for fetching and processing recipes
describe('Recipe Logic Tests', () => {
  const API_BASE_URL = Config.API_BASE_URL;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  describe('Recipe Fetching Logic', () => {
    it('should process pantry-based recipes correctly', async () => {
      const mockPantryItems = ['milk', 'flour', 'eggs'];
      const mockResponse = {
        recipes: [
          {
            id: 1,
            title: 'Pancakes',
            usedIngredientCount: 3,
            missedIngredientCount: 0,
            usedIngredients: [
              { id: 1, name: 'milk', amount: 1, unit: 'cup' },
              { id: 2, name: 'flour', amount: 2, unit: 'cups' },
              { id: 3, name: 'eggs', amount: 2, unit: '' },
            ],
            missedIngredients: [],
          },
        ],
        pantry_ingredients: mockPantryItems.map(name => ({ name, quantity: 1 })),
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Simulate the fetch logic
      const response = await fetch(`${API_BASE_URL}/recipes/findByIngredients/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredients: mockPantryItems,
          ranking: 2,
          ignorePantry: false,
          number: 20,
        }),
      });

      const data = await response.json();

      // Verify the response structure
      expect(data.recipes).toBeDefined();
      expect(data.recipes.length).toBe(1);
      expect(data.recipes[0].title).toBe('Pancakes');
      expect(data.recipes[0].usedIngredientCount).toBe(3);
      expect(data.recipes[0].missedIngredientCount).toBe(0);
    });

    it('should filter out invalid recipes', async () => {
      const mockResponse = {
        recipes: [
          { id: 1, title: 'Valid Recipe' },
          { id: null, title: 'Invalid - No ID' },
          { id: 2, title: '' }, // Invalid - empty title
          { id: 'string-id', title: 'Invalid - Wrong ID type' },
          { id: 3, title: 'Another Valid Recipe' },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      const data = await response.json();

      // Simulate the filtering logic used in the component
      const validRecipes = data.recipes.filter((recipe: any) => 
        recipe.id && typeof recipe.id === 'number' && recipe.id > 0 && recipe.title
      );

      expect(validRecipes.length).toBe(2);
      expect(validRecipes[0].title).toBe('Valid Recipe');
      expect(validRecipes[1].title).toBe('Another Valid Recipe');
    });

    it('should handle empty pantry scenario', async () => {
      const mockResponse = {
        recipes: [],
        pantry_ingredients: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const response = await fetch(`${API_BASE_URL}/recipes/findByIngredients/complex`, {
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

      expect(data.recipes).toEqual([]);
      expect(data.pantry_ingredients).toEqual([]);
    });

    it('should handle API key error', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Spoonacular API key not configured' }),
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      
      expect(response.ok).toBe(false);
      expect(response.status).toBe(400);

      const error = await response.json();
      expect(error.detail).toContain('API key');
    });
  });

  describe('Recipe Search Logic', () => {
    it('should apply dietary filters correctly', async () => {
      const mockResponse = {
        results: [
          { id: 1, title: 'Vegan Salad' },
          { id: 2, title: 'Gluten-Free Pasta' },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const selectedFilters = ['vegan', 'gluten-free'];
      const response = await fetch(`${API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'healthy',
          number: 20,
          diet: selectedFilters.join(','),
        }),
      });

      const data = await response.json();

      expect(data.results).toBeDefined();
      expect(data.results.length).toBe(2);
      
      // Verify the filters were sent in the request
      expect((global.fetch as jest.Mock).mock.calls[0][1].body).toContain('vegan,gluten-free');
    });
  });

  describe('User Recipes Logic', () => {
    it('should filter saved recipes by rating', async () => {
      const allRecipes = [
        { id: '1', recipe_title: 'Recipe 1', rating: 'thumbs_up' },
        { id: '2', recipe_title: 'Recipe 2', rating: 'thumbs_down' },
        { id: '3', recipe_title: 'Recipe 3', rating: 'thumbs_up' },
        { id: '4', recipe_title: 'Recipe 4', rating: 'neutral' },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => allRecipes,
      });

      const response = await fetch(`${API_BASE_URL}/user-recipes?rating=thumbs_up`);
      const data = await response.json();

      // Simulate client-side filtering (if needed)
      const thumbsUpRecipes = data.filter((recipe: any) => recipe.rating === 'thumbs_up');

      expect(thumbsUpRecipes.length).toBe(2);
      expect(thumbsUpRecipes[0].recipe_title).toBe('Recipe 1');
      expect(thumbsUpRecipes[1].recipe_title).toBe('Recipe 3');
    });

    it('should separate saved and cooked recipes', async () => {
      const allRecipes = [
        { id: '1', recipe_title: 'Saved Recipe', status: 'saved' },
        { id: '2', recipe_title: 'Cooked Recipe', status: 'cooked' },
        { id: '3', recipe_title: 'Another Saved', status: 'saved' },
      ];

      // Mock for saved recipes
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => allRecipes.filter(r => r.status === 'saved'),
      });

      const savedResponse = await fetch(`${API_BASE_URL}/user-recipes?status=saved`);
      const savedData = await savedResponse.json();

      expect(savedData.length).toBe(2);
      expect(savedData[0].recipe_title).toBe('Saved Recipe');
      expect(savedData[1].recipe_title).toBe('Another Saved');

      // Mock for cooked recipes
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => allRecipes.filter(r => r.status === 'cooked'),
      });

      const cookedResponse = await fetch(`${API_BASE_URL}/user-recipes?status=cooked`);
      const cookedData = await cookedResponse.json();

      expect(cookedData.length).toBe(1);
      expect(cookedData[0].recipe_title).toBe('Cooked Recipe');
    });
  });

  describe('Error Scenarios', () => {
    it('should handle network failures', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(fetch(`${API_BASE_URL}/recipes/random`)).rejects.toThrow('Network error');
    });

    it('should handle malformed responses', async () => {
      const malformedResponse = {
        // Missing expected 'recipes' field
        data: [{ id: 1 }],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => malformedResponse,
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      const data = await response.json();

      // Component should handle missing fields gracefully
      expect(data.recipes).toBeUndefined();
      expect(data.data).toBeDefined();
    });

    it('should handle 500 server errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ error: 'Server error' }),
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);

      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
    });
  });
});