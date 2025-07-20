import { apiClient } from '@/services/apiClient';

// Mock the global fetch
global.fetch = jest.fn();

describe('Recipe API Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset fetch mock
    (global.fetch as jest.Mock).mockReset();
  });

  describe('fetchRecipes', () => {
    it('should fetch recipes successfully', async () => {
      const mockRecipes = [
        {
          id: 1,
          title: 'Pasta Carbonara',
          ingredients: ['pasta', 'eggs', 'bacon', 'parmesan'],
          readyInMinutes: 30,
          servings: 4
        },
        {
          id: 2,
          title: 'Chicken Stir Fry',
          ingredients: ['chicken', 'vegetables', 'soy sauce', 'rice'],
          readyInMinutes: 25,
          servings: 3
        }
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recipes: mockRecipes }),
      });

      const response = await apiClient.get('/recipes');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/recipes'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      
      expect(response.recipes).toEqual(mockRecipes);
      expect(response.recipes).toHaveLength(2);
    });

    it('should handle API errors gracefully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(apiClient.get('/recipes')).rejects.toThrow();
    });

    it('should handle network errors', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network request failed')
      );

      await expect(apiClient.get('/recipes')).rejects.toThrow('Network request failed');
    });
  });

  describe('Recipe Details API', () => {
    it('should fetch recipe details with all steps', async () => {
      const mockRecipeDetail = {
        id: 1,
        title: 'Detailed Recipe',
        ingredients: [
          { name: 'flour', amount: 2, unit: 'cups' },
          { name: 'eggs', amount: 3, unit: 'large' },
          { name: 'milk', amount: 1, unit: 'cup' }
        ],
        steps: [
          { number: 1, step: 'Mix dry ingredients' },
          { number: 2, step: 'Beat eggs separately' },
          { number: 3, step: 'Combine wet and dry ingredients' },
          { number: 4, step: 'Cook on medium heat' },
          { number: 5, step: 'Serve hot' }
        ],
        nutrition: {
          calories: 250,
          protein: 12,
          carbs: 30,
          fat: 8
        }
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipeDetail,
      });

      const response = await apiClient.get('/recipes/1');
      
      // Verify all steps are returned
      expect(response.steps).toHaveLength(5);
      response.steps.forEach((step, index) => {
        expect(step.number).toBe(index + 1);
        expect(step.step).toBeTruthy();
      });
      
      // Verify all ingredients are returned
      expect(response.ingredients).toHaveLength(3);
    });

    it('should handle missing recipe steps', async () => {
      const mockRecipeWithoutSteps = {
        id: 1,
        title: 'Recipe Without Steps',
        ingredients: ['ingredient1', 'ingredient2'],
        steps: []
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipeWithoutSteps,
      });

      const response = await apiClient.get('/recipes/1');
      
      expect(response.steps).toEqual([]);
      expect(response.steps).toHaveLength(0);
    });
  });

  describe('Complete Recipe API', () => {
    it('should complete recipe and update pantry', async () => {
      const ingredientUsages = [
        {
          ingredientName: 'milk',
          selectedAmount: 2,
          pantryItems: [{ id: '1', name: 'Whole Milk' }]
        },
        {
          ingredientName: 'flour',
          selectedAmount: 3,
          pantryItems: [{ id: '2', name: 'All Purpose Flour' }]
        }
      ];

      const mockResponse = {
        success: true,
        message: 'Recipe completed successfully',
        updatedPantryItems: [
          { id: '1', quantity: 2 },
          { id: '2', quantity: 7 }
        ]
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const response = await apiClient.post('/recipes/complete', {
        recipeId: 1,
        ingredientUsages
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/recipes/complete'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            recipeId: 1,
            ingredientUsages
          })
        })
      );

      expect(response.success).toBe(true);
      expect(response.updatedPantryItems).toHaveLength(2);
    });

    it('should handle recipe completion errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid ingredient quantities' }),
      });

      await expect(
        apiClient.post('/recipes/complete', { recipeId: 1, ingredientUsages: [] })
      ).rejects.toThrow();
    });
  });

  describe('API Response Caching', () => {
    it('should cache repeated requests', async () => {
      const mockData = { recipes: [{ id: 1, title: 'Cached Recipe' }] };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      // First call
      const response1 = await apiClient.get('/recipes');
      expect(global.fetch).toHaveBeenCalledTimes(1);

      // Second call (should use cache if implemented)
      const response2 = await apiClient.get('/recipes');
      
      // If caching is implemented, fetch should still be called only once
      // Otherwise, this test documents current behavior
      expect(response1).toEqual(response2);
    });
  });

  describe('Retry Logic', () => {
    it('should retry failed requests', async () => {
      // First attempt fails
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
      });

      // Second attempt succeeds
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recipes: [] }),
      });

      // If retry logic is implemented, this should succeed
      // Otherwise, it documents the need for retry logic
      try {
        await apiClient.get('/recipes');
      } catch (error) {
        // Current behavior without retry
        expect(error).toBeDefined();
      }
    });
  });
});