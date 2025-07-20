import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import RecipesScreen from '@/app/(tabs)/recipes';
import { useItems } from '@/context/ItemsContext';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'expo-router';
import { mockFetch, mockFetchError, createMockRecipe, createMockPantryItem } from '../helpers/apiMocks';

// Mock dependencies
// These mocks are already in jest.setup.js
jest.spyOn(Alert, 'alert');

const mockUseItems = jest.mocked(useItems);
const mockUseAuth = jest.mocked(useAuth);
const mockUseRouter = jest.mocked(useRouter);

describe('Recipe Tabs Display Tests', () => {
  const mockRouter = { push: jest.fn() };
  const mockItems = [
    createMockPantryItem({ id: '1', product_name: 'Milk', quantity_amount: 2 }),
    createMockPantryItem({ id: '2', product_name: 'Flour', quantity_amount: 3 }),
    createMockPantryItem({ id: '3', product_name: 'Eggs', quantity_amount: 12 }),
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRouter.mockReturnValue(mockRouter as any);
    mockUseItems.mockReturnValue({ items: mockItems } as any);
    mockUseAuth.mockReturnValue({
      user: { id: 111 },
      token: 'mock-token',
      isAuthenticated: true,
    } as any);
  });

  describe('From Pantry Tab', () => {
    it('should display recipes based on pantry items when API returns data', async () => {
      const mockRecipesResponse = {
        recipes: [
          createMockRecipe({
            id: 1,
            title: 'Pasta Carbonara',
            usedIngredientCount: 3,
            missedIngredientCount: 1,
            usedIngredients: [
              { id: 1, name: 'eggs', amount: 3, unit: '' },
              { id: 2, name: 'flour', amount: 2, unit: 'cups' },
            ],
            missedIngredients: [
              { id: 3, name: 'bacon', amount: 200, unit: 'g' },
            ],
          }),
          createMockRecipe({
            id: 2,
            title: 'French Toast',
            usedIngredientCount: 2,
            missedIngredientCount: 0,
          }),
        ],
        pantry_ingredients: mockItems.map(item => ({
          name: item.product_name.toLowerCase(),
          quantity: item.quantity_amount,
        })),
      };

      global.fetch = mockFetch(mockRecipesResponse);

      const { getByText, getAllByTestId, queryByText } = render(<RecipesScreen />);

      // Wait for recipes to load
      await waitFor(() => {
        expect(getByText('Pasta Carbonara')).toBeTruthy();
        expect(getByText('French Toast')).toBeTruthy();
      });

      // Verify ingredient counts are displayed
      expect(getByText('✓ 3 | ✗ 1')).toBeTruthy(); // Pasta Carbonara
      expect(getByText('✓ 2 | ✗ 0')).toBeTruthy(); // French Toast

      // Verify API was called correctly
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/recipes/findByIngredients/complex'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ingredients: ['milk', 'flour', 'eggs'],
            ranking: 2,
            ignorePantry: false,
            number: 20,
          }),
        })
      );
    });

    it('should show empty state when no pantry items exist', async () => {
      mockUseItems.mockReturnValue({ items: [] } as any);
      
      const { getByText } = render(<RecipesScreen />);

      await waitFor(() => {
        expect(getByText("Your pantry is empty! Add some items to see recipe suggestions.")).toBeTruthy();
      });

      // Should not make API call with empty pantry
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should handle API errors gracefully', async () => {
      global.fetch = mockFetchError('Network error');

      const { queryByText } = render(<RecipesScreen />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to load recipes. Please try again.'
        );
      });

      // Should not display any recipes
      expect(queryByText('Pasta Carbonara')).toBeNull();
    });

    it('should handle missing API key error', async () => {
      global.fetch = mockFetch(
        { detail: 'Spoonacular API key not configured' },
        { ok: false, status: 400 }
      );

      render(<RecipesScreen />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Spoonacular API Key Required',
          expect.stringContaining('To use recipe features'),
          [{ text: 'OK' }]
        );
      });
    });
  });

  describe('Discover Tab', () => {
    it('should fetch random recipes when switching to discover tab', async () => {
      const mockRandomRecipes = {
        recipes: [
          createMockRecipe({ id: 10, title: 'Random Recipe 1' }),
          createMockRecipe({ id: 11, title: 'Random Recipe 2' }),
        ],
      };

      global.fetch = mockFetch(mockRandomRecipes);

      const { getByText, queryByText } = render(<RecipesScreen />);

      // Click on Discover tab
      fireEvent.press(getByText('Discover'));

      await waitFor(() => {
        expect(getByText('Random Recipe 1')).toBeTruthy();
        expect(getByText('Random Recipe 2')).toBeTruthy();
      });

      // Verify random endpoint was called
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/recipes/random?number=20')
      );
    });

    it('should search recipes when query is entered', async () => {
      const mockSearchResults = {
        results: [
          createMockRecipe({ id: 20, title: 'Chicken Curry' }),
          createMockRecipe({ id: 21, title: 'Chicken Salad' }),
        ],
      };

      global.fetch = jest.fn()
        .mockResolvedValueOnce({ // First call for random recipes
          ok: true,
          json: async () => ({ recipes: [] }),
        })
        .mockResolvedValueOnce({ // Second call for search
          ok: true,
          json: async () => mockSearchResults,
        });

      const { getByText, getByPlaceholderText } = render(<RecipesScreen />);

      // Switch to Discover tab
      fireEvent.press(getByText('Discover'));

      // Enter search query
      const searchInput = getByPlaceholderText('Search recipes...');
      fireEvent.changeText(searchInput, 'chicken');
      
      // Trigger search
      fireEvent(searchInput, 'submitEditing');

      await waitFor(() => {
        expect(getByText('Chicken Curry')).toBeTruthy();
        expect(getByText('Chicken Salad')).toBeTruthy();
      });

      // Verify search endpoint was called
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/recipes/search/complex'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            query: 'chicken',
            number: 20,
            diet: undefined,
          }),
        })
      );
    });

    it('should apply dietary filters', async () => {
      const mockFilteredRecipes = {
        results: [
          createMockRecipe({ id: 30, title: 'Vegan Buddha Bowl' }),
        ],
      };

      global.fetch = jest.fn()
        .mockResolvedValueOnce({ // First call for random recipes
          ok: true,
          json: async () => ({ recipes: [] }),
        })
        .mockResolvedValueOnce({ // Second call with filters
          ok: true,
          json: async () => mockFilteredRecipes,
        });

      const { getByText, getByPlaceholderText } = render(<RecipesScreen />);

      // Switch to Discover tab
      fireEvent.press(getByText('Discover'));

      // Select vegan filter
      fireEvent.press(getByText('🌱'));

      // Enter search and submit
      const searchInput = getByPlaceholderText('Search recipes...');
      fireEvent.changeText(searchInput, 'bowl');
      fireEvent(searchInput, 'submitEditing');

      await waitFor(() => {
        expect(getByText('Vegan Buddha Bowl')).toBeTruthy();
      });

      // Verify filter was included in search
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/recipes/search/complex'),
        expect.objectContaining({
          body: expect.stringContaining('"diet":"vegan"'),
        })
      );
    });
  });

  describe('My Recipes Tab', () => {
    it('should fetch and display saved recipes', async () => {
      const mockSavedRecipes = [
        {
          id: 'saved-1',
          recipe_id: 40,
          recipe_title: 'My Favorite Pasta',
          recipe_image: 'https://example.com/pasta.jpg',
          rating: 'thumbs_up',
          is_favorite: true,
          source: 'spoonacular',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'saved-2',
          recipe_id: 41,
          recipe_title: 'Quick Salad',
          recipe_image: 'https://example.com/salad.jpg',
          rating: 'neutral',
          is_favorite: false,
          source: 'spoonacular',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];

      global.fetch = mockFetch(mockSavedRecipes);

      const { getByText } = render(<RecipesScreen />);

      // Switch to My Recipes tab
      fireEvent.press(getByText('My Recipes'));

      await waitFor(() => {
        expect(getByText('My Favorite Pasta')).toBeTruthy();
        expect(getByText('Quick Salad')).toBeTruthy();
      });

      // Verify saved recipes endpoint was called
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/user-recipes?status=saved'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('should filter saved recipes by rating', async () => {
      const mockThumbsUpRecipes = [
        {
          id: 'saved-1',
          recipe_id: 50,
          recipe_title: 'Loved Recipe',
          recipe_image: 'https://example.com/loved.jpg',
          rating: 'thumbs_up',
          is_favorite: false,
          source: 'spoonacular',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];

      global.fetch = jest.fn()
        .mockResolvedValueOnce({ // First call for all saved
          ok: true,
          json: async () => [],
        })
        .mockResolvedValueOnce({ // Second call for thumbs up filter
          ok: true,
          json: async () => mockThumbsUpRecipes,
        });

      const { getByText } = render(<RecipesScreen />);

      // Switch to My Recipes tab
      fireEvent.press(getByText('My Recipes'));

      // Select thumbs up filter
      await waitFor(() => {
        fireEvent.press(getByText('👍'));
      });

      await waitFor(() => {
        expect(getByText('Loved Recipe')).toBeTruthy();
      });

      // Verify filter was applied
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/user-recipes?status=saved&rating=thumbs_up'),
        expect.any(Object)
      );
    });

    it('should switch between saved and cooked tabs', async () => {
      const mockCookedRecipes = [
        {
          id: 'cooked-1',
          recipe_id: 60,
          recipe_title: 'Already Cooked Recipe',
          recipe_image: 'https://example.com/cooked.jpg',
          rating: 'thumbs_up',
          is_favorite: false,
          source: 'spoonacular',
          status: 'cooked',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ];

      global.fetch = jest.fn()
        .mockResolvedValueOnce({ // First call for saved
          ok: true,
          json: async () => [],
        })
        .mockResolvedValueOnce({ // Second call for cooked
          ok: true,
          json: async () => mockCookedRecipes,
        });

      const { getByText } = render(<RecipesScreen />);

      // Switch to My Recipes tab
      fireEvent.press(getByText('My Recipes'));

      // Switch to Cooked sub-tab
      await waitFor(() => {
        fireEvent.press(getByText('Cooked'));
      });

      await waitFor(() => {
        expect(getByText('Already Cooked Recipe')).toBeTruthy();
      });

      // Verify cooked status filter was applied
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/user-recipes?status=cooked'),
        expect.any(Object)
      );
    });

    it('should show empty state for my recipes', async () => {
      global.fetch = mockFetch([]);

      const { getByText } = render(<RecipesScreen />);

      // Switch to My Recipes tab
      fireEvent.press(getByText('My Recipes'));

      await waitFor(() => {
        expect(getByText(/no saved recipes/i)).toBeTruthy();
      });
    });
  });

  describe('Recipe Card Interactions', () => {
    it('should navigate to recipe details when card is pressed', async () => {
      const mockRecipe = createMockRecipe({
        id: 123,
        title: 'Test Recipe',
      });

      global.fetch = mockFetch({
        recipes: [mockRecipe],
        pantry_ingredients: [],
      });

      const { getByText } = render(<RecipesScreen />);

      await waitFor(() => {
        expect(getByText('Test Recipe')).toBeTruthy();
      });

      // Press recipe card
      fireEvent.press(getByText('Test Recipe'));

      // Verify navigation
      expect(mockRouter.push).toHaveBeenCalledWith({
        pathname: '/recipe-details',
        params: expect.objectContaining({
          id: 123,
          recipe: JSON.stringify(mockRecipe),
        }),
      });
    });
  });

  describe('Pull to Refresh', () => {
    it('should refresh recipes when pulled down', async () => {
      const initialRecipes = {
        recipes: [createMockRecipe({ id: 1, title: 'Initial Recipe' })],
        pantry_ingredients: [],
      };

      const refreshedRecipes = {
        recipes: [createMockRecipe({ id: 2, title: 'Refreshed Recipe' })],
        pantry_ingredients: [],
      };

      global.fetch = jest.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => initialRecipes,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => refreshedRecipes,
        });

      const { getByText, getByTestId, queryByText } = render(<RecipesScreen />);

      // Wait for initial load
      await waitFor(() => {
        expect(getByText('Initial Recipe')).toBeTruthy();
      });

      // Trigger refresh
      const scrollView = getByTestId('recipe-scroll-view');
      fireEvent(scrollView, 'refresh');

      // Wait for refresh to complete
      await waitFor(() => {
        expect(queryByText('Initial Recipe')).toBeNull();
        expect(getByText('Refreshed Recipe')).toBeTruthy();
      });

      // Verify API was called twice
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });
});