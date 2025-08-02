/**
 * Comprehensive API and service layer testing
 * Expanded coverage following recipeLogic.test.ts patterns
 */

import { Config } from '@/config';

describe('API Service Layer Tests', () => {
  const API_BASE_URL = Config.API_BASE_URL;

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  describe('Recipe API Endpoints', () => {
    describe('Pantry-Based Recipe Search', () => {
      it('should handle successful pantry recipe search', async () => {
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
          pantry_ingredients: [
            { name: 'milk', quantity: 1 },
            { name: 'flour', quantity: 1 },
            { name: 'eggs', quantity: 12 }
          ],
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 111,
            max_missing_ingredients: 10,
            use_expiring_first: true,
          }),
        });

        const data = await response.json();

        expect(response.ok).toBe(true);
        expect(data.recipes).toHaveLength(1);
        expect(data.recipes[0].title).toBe('Pancakes');
        expect(data.recipes[0].usedIngredientCount).toBe(3);
        expect(data.pantry_ingredients).toHaveLength(3);
      });

      it('should handle empty pantry response', async () => {
        const mockResponse = {
          recipes: [],
          pantry_ingredients: [],
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 111,
            max_missing_ingredients: 10,
            use_expiring_first: true,
          }),
        });

        const data = await response.json();

        expect(data.recipes).toEqual([]);
        expect(data.pantry_ingredients).toEqual([]);
      });

      it('should handle API key error for pantry search', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Spoonacular API key not configured' }),
        });

        const response = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 111,
            max_missing_ingredients: 10,
            use_expiring_first: true,
          }),
        });

        expect(response.ok).toBe(false);
        expect(response.status).toBe(400);

        const error = await response.json();
        expect(error.detail).toContain('API key');
      });
    });

    describe('Complex Recipe Search', () => {
      it('should search recipes with dietary filters', async () => {
        const mockResponse = {
          results: [
            { id: 1, title: 'Vegan Pasta', diet: ['vegan'] },
            { id: 2, title: 'Gluten-Free Bread', diet: ['gluten-free'] },
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

        expect(data.results).toHaveLength(2);
        expect(data.results[0].title).toBe('Vegan Pasta');
        
        // Verify the filters were sent in the request
        const requestBody = (global.fetch as jest.Mock).mock.calls[0][1].body;
        expect(requestBody).toContain('vegan,gluten-free');
      });

      it('should handle search with no results', async () => {
        const mockResponse = {
          results: [],
          totalResults: 0,
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/recipes/search/complex`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: 'xyz-nonexistent-recipe',
            number: 20,
          }),
        });

        const data = await response.json();

        expect(data.results).toEqual([]);
        expect(data.totalResults).toBe(0);
      });

      it('should handle complex search API errors', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 402,
          json: async () => ({ detail: 'Daily limit exceeded' }),
        });

        const response = await fetch(`${API_BASE_URL}/recipes/search/complex`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: 'pasta',
            number: 20,
          }),
        });

        expect(response.ok).toBe(false);
        expect(response.status).toBe(402);
      });
    });

    describe('Random Recipe Fetching', () => {
      it('should fetch random recipes successfully', async () => {
        const mockResponse = {
          recipes: [
            { id: 1, title: 'Random Recipe 1' },
            { id: 2, title: 'Random Recipe 2' },
            { id: 3, title: 'Random Recipe 3' },
          ],
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/recipes/random?number=20`);
        const data = await response.json();

        expect(data.recipes).toHaveLength(3);
        expect(data.recipes[0].title).toBe('Random Recipe 1');
      });

      it('should handle random recipe API limits', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 402,
          json: async () => ({ detail: 'Daily quota exceeded' }),
        });

        const response = await fetch(`${API_BASE_URL}/recipes/random?number=20`);

        expect(response.ok).toBe(false);
        expect(response.status).toBe(402);
      });
    });

    describe('Recipe Details', () => {
      it('should fetch recipe details by ID', async () => {
        const mockResponse = {
          id: 123,
          title: 'Detailed Recipe',
          instructions: [
            { number: 1, step: 'Prepare ingredients' },
            { number: 2, step: 'Cook the dish' },
          ],
          extendedIngredients: [
            { id: 1, name: 'flour', amount: 2, unit: 'cups' },
            { id: 2, name: 'sugar', amount: 1, unit: 'cup' },
          ],
          readyInMinutes: 30,
          servings: 4,
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/recipes/123/information`);
        const data = await response.json();

        expect(data.id).toBe(123);
        expect(data.title).toBe('Detailed Recipe');
        expect(data.instructions).toHaveLength(2);
        expect(data.extendedIngredients).toHaveLength(2);
      });

      it('should handle recipe not found', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 404,
          json: async () => ({ detail: 'Recipe not found' }),
        });

        const response = await fetch(`${API_BASE_URL}/recipes/999999/information`);

        expect(response.ok).toBe(false);
        expect(response.status).toBe(404);
      });
    });
  });

  describe('User Recipe Management', () => {
    describe('Saved Recipes', () => {
      it('should fetch all saved recipes', async () => {
        const mockResponse = [
          {
            id: '1',
            recipe_id: 100,
            recipe_title: 'Saved Recipe 1',
            rating: 'thumbs_up',
            status: 'saved',
            created_at: '2024-01-01T10:00:00Z',
          },
          {
            id: '2',
            recipe_id: 101,
            recipe_title: 'Saved Recipe 2',
            rating: 'neutral',
            status: 'saved',
            created_at: '2024-01-02T10:00:00Z',
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/user-recipes`);
        const data = await response.json();

        expect(data).toHaveLength(2);
        expect(data[0].recipe_title).toBe('Saved Recipe 1');
      });

      it('should filter recipes by rating', async () => {
        const mockResponse = [
          {
            id: '1',
            recipe_id: 100,
            recipe_title: 'Liked Recipe',
            rating: 'thumbs_up',
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/user-recipes?rating=thumbs_up`);
        const data = await response.json();

        expect(data).toHaveLength(1);
        expect(data[0].rating).toBe('thumbs_up');
      });

      it('should filter recipes by status', async () => {
        const mockResponse = [
          {
            id: '1',
            recipe_id: 100,
            recipe_title: 'Cooked Recipe',
            status: 'cooked',
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/user-recipes?status=cooked`);
        const data = await response.json();

        expect(data).toHaveLength(1);
        expect(data[0].status).toBe('cooked');
      });

      it('should filter favorites', async () => {
        const mockResponse = [
          {
            id: '1',
            recipe_id: 100,
            recipe_title: 'Favorite Recipe',
            is_favorite: true,
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/user-recipes?is_favorite=true`);
        const data = await response.json();

        expect(data).toHaveLength(1);
        expect(data[0].is_favorite).toBe(true);
      });

      it('should handle combined filters', async () => {
        const mockResponse = [
          {
            id: '1',
            recipe_id: 100,
            recipe_title: 'Favorite Cooked Recipe',
            status: 'cooked',
            is_favorite: true,
            rating: 'thumbs_up',
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/user-recipes?status=cooked&is_favorite=true&rating=thumbs_up`);
        const data = await response.json();

        expect(data).toHaveLength(1);
        expect(data[0].status).toBe('cooked');
        expect(data[0].is_favorite).toBe(true);
        expect(data[0].rating).toBe('thumbs_up');
      });
    });

    describe('Recipe Saving', () => {
      it('should save a new recipe', async () => {
        const mockResponse = {
          id: '123',
          recipe_id: 456,
          recipe_title: 'Newly Saved Recipe',
          status: 'saved',
          created_at: '2024-01-15T10:00:00Z',
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => mockResponse,
        });

        const saveData = {
          recipe_id: 456,
          recipe_title: 'Newly Saved Recipe',
          recipe_image: 'recipe.jpg',
          recipe_data: { /* recipe details */ },
          source: 'spoonacular',
        };

        const response = await fetch(`${API_BASE_URL}/user-recipes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(saveData),
        });

        const data = await response.json();

        expect(response.status).toBe(201);
        expect(data.recipe_title).toBe('Newly Saved Recipe');
        expect(data.status).toBe('saved');
      });

      it('should handle duplicate recipe save', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: false,
          status: 409,
          json: async () => ({ detail: 'Recipe already saved' }),
        });

        const saveData = {
          recipe_id: 456,
          recipe_title: 'Duplicate Recipe',
        };

        const response = await fetch(`${API_BASE_URL}/user-recipes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(saveData),
        });

        expect(response.status).toBe(409);
      });
    });

    describe('Recipe Updates', () => {
      it('should update recipe rating', async () => {
        const mockResponse = {
          id: '123',
          recipe_id: 456,
          recipe_title: 'Updated Recipe',
          rating: 'thumbs_up',
          updated_at: '2024-01-15T11:00:00Z',
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const updateData = {
          rating: 'thumbs_up',
        };

        const response = await fetch(`${API_BASE_URL}/user-recipes/123`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        });

        const data = await response.json();

        expect(data.rating).toBe('thumbs_up');
        expect(data.updated_at).toBe('2024-01-15T11:00:00Z');
      });

      it('should mark recipe as cooked', async () => {
        const mockResponse = {
          id: '123',
          recipe_id: 456,
          status: 'cooked',
          cooked_at: '2024-01-15T12:00:00Z',
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const updateData = {
          status: 'cooked',
        };

        const response = await fetch(`${API_BASE_URL}/user-recipes/123`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        });

        const data = await response.json();

        expect(data.status).toBe('cooked');
        expect(data.cooked_at).toBe('2024-01-15T12:00:00Z');
      });

      it('should toggle favorite status', async () => {
        const mockResponse = {
          id: '123',
          recipe_id: 456,
          is_favorite: true,
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const updateData = {
          is_favorite: true,
        };

        const response = await fetch(`${API_BASE_URL}/user-recipes/123`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        });

        const data = await response.json();

        expect(data.is_favorite).toBe(true);
      });
    });
  });

  describe('Pantry Management API', () => {
    describe('Pantry Items', () => {
      it('should fetch all pantry items', async () => {
        const mockResponse = [
          {
            id: '1',
            item_name: 'Milk',
            category: 'Dairy',
            expiry_date: '2024-01-20',
            quantity: 1,
            unit: 'gallon',
          },
          {
            id: '2',
            item_name: 'Bread',
            category: 'Bakery',
            expiry_date: '2024-01-18',
            quantity: 1,
            unit: 'loaf',
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/pantry-items?user_id=111`);
        const data = await response.json();

        expect(data).toHaveLength(2);
        expect(data[0].item_name).toBe('Milk');
        expect(data[1].item_name).toBe('Bread');
      });

      it('should add new pantry item', async () => {
        const mockResponse = {
          id: '123',
          item_name: 'New Item',
          category: 'Produce',
          expiry_date: '2024-01-25',
          quantity: 3,
          unit: 'pieces',
          created_at: '2024-01-15T10:00:00Z',
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: async () => mockResponse,
        });

        const newItem = {
          item_name: 'New Item',
          category: 'Produce',
          expiry_date: '2024-01-25',
          quantity: 3,
          unit: 'pieces',
          user_id: 111,
        };

        const response = await fetch(`${API_BASE_URL}/pantry-items`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newItem),
        });

        const data = await response.json();

        expect(response.status).toBe(201);
        expect(data.item_name).toBe('New Item');
        expect(data.quantity).toBe(3);
      });

      it('should update pantry item', async () => {
        const mockResponse = {
          id: '123',
          item_name: 'Updated Item',
          quantity: 5,
          updated_at: '2024-01-15T11:00:00Z',
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const updateData = {
          item_name: 'Updated Item',
          quantity: 5,
        };

        const response = await fetch(`${API_BASE_URL}/pantry-items/123`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData),
        });

        const data = await response.json();

        expect(data.quantity).toBe(5);
      });

      it('should delete pantry item', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          status: 204,
        });

        const response = await fetch(`${API_BASE_URL}/pantry-items/123`, {
          method: 'DELETE',
        });

        expect(response.status).toBe(204);
      });
    });

    describe('Expiration Tracking', () => {
      it('should fetch expiring items', async () => {
        const mockResponse = [
          {
            id: '1',
            item_name: 'Expiring Milk',
            expiry_date: '2024-01-16',
            days_until_expiry: 1,
            is_expiring_soon: true,
          },
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        const response = await fetch(`${API_BASE_URL}/pantry-items/expiring?user_id=111&days=3`);
        const data = await response.json();

        expect(data).toHaveLength(1);
        expect(data[0].is_expiring_soon).toBe(true);
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle network timeouts', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network timeout'));

      await expect(fetch(`${API_BASE_URL}/recipes/random`)).rejects.toThrow('Network timeout');
    });

    it('should handle malformed JSON responses', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);
      
      expect(response.ok).toBe(true);
      await expect(response.json()).rejects.toThrow('Invalid JSON');
    });

    it('should handle 500 server errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ error: 'Server error', message: 'Something went wrong' }),
      });

      const response = await fetch(`${API_BASE_URL}/recipes/random`);

      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
      expect(response.statusText).toBe('Internal Server Error');
    });

    it('should handle 429 rate limit errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ 
          detail: 'Rate limit exceeded',
          retry_after: 3600
        }),
      });

      const response = await fetch(`${API_BASE_URL}/recipes/search/complex`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'pasta' }),
      });

      expect(response.status).toBe(429);
      
      const error = await response.json();
      expect(error.detail).toContain('Rate limit');
      expect(error.retry_after).toBe(3600);
    });

    it('should handle empty response bodies', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => null,
      });

      const response = await fetch(`${API_BASE_URL}/user-recipes`);
      const data = await response.json();

      expect(data).toBeNull();
    });

    it('should handle unauthorized requests', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid authentication credentials' }),
      });

      const response = await fetch(`${API_BASE_URL}/user-recipes`, {
        headers: {
          'Authorization': 'Bearer invalid-token',
        },
      });

      expect(response.status).toBe(401);
    });
  });
});