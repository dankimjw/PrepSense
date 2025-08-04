import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert } from 'react-native';
import RecipesContainer from '../../../components/recipes/RecipesContainer';
import { useAuth } from '../../../context/AuthContext';
import { useItems } from '../../../context/ItemsContext';
import { useTabData } from '../../../context/TabDataProvider';
import { useRouter } from 'expo-router';
import {
  createMockRecipe,
  createMockSavedRecipe,
  mockApiResponses,
  mockErrorResponses,
  createMockAuthContext,
  createMockItemsContext,
  createMockNavigation
} from '../../helpers/recipeTestUtils';

// Mock all dependencies
jest.mock('../../../context/AuthContext');
jest.mock('../../../context/ItemsContext');
jest.mock('../../../context/TabDataProvider');
jest.mock('expo-router');
jest.mock('../../../config', () => ({
  Config: { API_BASE_URL: 'http://localhost:8000' }
}));
jest.mock('../../../utils/ingredientMatcher', () => ({
  calculateIngredientAvailability: jest.fn((ingredients, pantryItems) => ({
    availableCount: 3,
    missingCount: 2,
    totalCount: 5
  })),
  validateIngredientCounts: jest.fn(() => true)
}));
jest.mock('../../../utils/contentValidation', () => ({
  isValidRecipe: jest.fn(() => true)
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseItems = useItems as jest.MockedFunction<typeof useItems>;
const mockUseTabData = useTabData as jest.MockedFunction<typeof useTabData>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('RecipesContainer', () => {
  let mockNavigation: ReturnType<typeof createMockNavigation>;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockNavigation = createMockNavigation();
    
    mockUseAuth.mockReturnValue(createMockAuthContext());
    mockUseItems.mockReturnValue(createMockItemsContext());
    mockUseRouter.mockReturnValue(mockNavigation);
    mockUseTabData.mockReturnValue({
      recipesData: {
        pantryRecipes: mockApiResponses.pantryRecipes.recipes,
        myRecipes: mockApiResponses.savedRecipes,
        lastUpdated: Date.now()
      }
    });

    // Default successful fetch responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/recipes/search/from-pantry')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.pantryRecipes)
        } as Response);
      }
      if (url.includes('/user-recipes')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.savedRecipes)
        } as Response);
      }
      if (url.includes('/recipes/random')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.randomRecipes)
        } as Response);
      }
      if (url.includes('/recipes/search/complex')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.searchRecipes)
        } as Response);
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      } as Response);
    });
  });

  describe('State Management', () => {
    it('should initialize with correct default state', async () => {
      render(<RecipesContainer />);

      // Should start with pantry tab active
      expect(screen.getByTestId('pantry-tab')).toHaveStyle({ borderBottomColor: '#297A56' });
      
      // Should show search input with correct placeholder
      expect(screen.getByPlaceholderText('Search pantry recipes...')).toBeTruthy();
      
      // Should load pantry recipes on mount
      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });
    });

    it('should handle useReducer actions correctly', async () => {
      render(<RecipesContainer />);

      // Test tab change action
      fireEvent.press(screen.getByTestId('discover-tab'));
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search all recipes...')).toBeTruthy();
      });

      // Test search query change action
      const searchInput = screen.getByTestId('search-input');
      fireEvent.changeText(searchInput, 'pasta');
      expect(searchInput.props.value).toBe('pasta');

      // Test sort modal toggle action
      fireEvent.press(screen.getByTestId('sort-button'));
      expect(screen.getByTestId('sort-modal')).toHaveProp('visible', true);

      // Test sort option change action
      fireEvent.press(screen.getByTestId('sort-option-name'));
      await waitFor(() => {
        expect(screen.getByTestId('sort-modal')).toHaveProp('visible', false);
      });
    });

    it('should handle filter changes correctly', async () => {
      render(<RecipesContainer />);

      // Switch to discover tab to access filters
      fireEvent.press(screen.getByTestId('discover-tab'));
      
      await waitFor(() => {
        expect(screen.getByTestId('dietary-filter-vegetarian')).toBeTruthy();
      });

      // Test dietary filter selection
      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      fireEvent.press(screen.getByTestId('cuisine-filter-italian'));
      fireEvent.press(screen.getByTestId('meal-type-filter-dinner'));

      // Filters should be visually active
      expect(screen.getByTestId('dietary-filter-vegetarian')).toHaveStyle({
        backgroundColor: '#E6F7F0',
        borderWidth: 1,
        borderColor: '#297A56'
      });
    });

    it('should handle my recipes filter changes', async () => {
      render(<RecipesContainer />);

      // Switch to my recipes tab
      fireEvent.press(screen.getByTestId('my-recipes-tab'));
      
      await waitFor(() => {
        expect(screen.getByTestId('my-recipes-tabs')).toBeTruthy();
      });

      // Test cooked tab switch
      fireEvent.press(screen.getByTestId('cooked-tab'));
      
      await waitFor(() => {
        expect(screen.getByTestId('filter-thumbs-up')).toBeTruthy();
      });

      // Test rating filter selection
      fireEvent.press(screen.getByTestId('filter-thumbs-up'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes?status=cooked&rating=thumbs_up'),
          expect.any(Object)
        );
      });
    });
  });

  describe('API Integration', () => {
    it('should fetch pantry recipes on mount', async () => {
      render(<RecipesContainer />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/from-pantry'),
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('111')
          })
        );
      });

      expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
    });

    it('should search recipes in discover tab', async () => {
      render(<RecipesContainer />);

      // Switch to discover tab
      fireEvent.press(screen.getByTestId('discover-tab'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/random'),
          expect.any(Object)
        );
      });

      // Perform search
      const searchInput = screen.getByTestId('search-input');
      fireEvent.changeText(searchInput, 'pasta');
      fireEvent.press(screen.getByTestId('search-submit-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/complex'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('pasta')
          })
        );
      });
    });

    it('should fetch my recipes with filters', async () => {
      render(<RecipesContainer />);

      // Switch to my recipes tab
      fireEvent.press(screen.getByTestId('my-recipes-tab'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes?status=saved'),
          expect.any(Object)
        );
      });

      // Switch to cooked tab
      fireEvent.press(screen.getByTestId('cooked-tab'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes?status=cooked'),
          expect.any(Object)
        );
      });
    });

    it('should use preloaded data when available', async () => {
      // Mock tab data with fresh preloaded data
      mockUseTabData.mockReturnValue({
        recipesData: {
          pantryRecipes: mockApiResponses.pantryRecipes.recipes,
          myRecipes: mockApiResponses.savedRecipes,
          lastUpdated: Date.now()
        }
      });

      render(<RecipesContainer />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Should not make API call if using preloaded data
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should handle API errors gracefully', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<RecipesContainer />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to load recipes. Please try again.'
        );
      });
    });

    it('should handle Spoonacular API key errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'API key required for Spoonacular access' })
      } as Response);

      render(<RecipesContainer />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Spoonacular API Key Required',
          expect.stringContaining('Get your free API key'),
          [{ text: 'OK' }]
        );
      });
    });
  });

  describe('Data Processing', () => {
    it('should recalculate ingredient counts correctly', async () => {
      const { calculateIngredientAvailability } = require('../../../utils/ingredientMatcher');
      
      render(<RecipesContainer />);

      await waitFor(() => {
        expect(calculateIngredientAvailability).toHaveBeenCalled();
      });

      // Should display recalculated counts
      expect(screen.getByText('3 have')).toBeTruthy();
      expect(screen.getByText('2 missing')).toBeTruthy();
    });

    it('should filter Spoonacular recipes only', async () => {
      const mixedRecipes = [
        createMockRecipe({ id: 1, title: 'Valid Recipe' }),
        createMockRecipe({ id: 0, title: 'Invalid Recipe' }), // Invalid ID
        createMockRecipe({ id: -1, title: 'Negative ID Recipe' }), // Invalid ID
      ];

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          recipes: mixedRecipes,
          pantry_ingredients: mockApiResponses.pantryRecipes.pantry_ingredients
        })
      } as Response);

      render(<RecipesContainer />);

      await waitFor(() => {
        expect(screen.getByText('Valid Recipe')).toBeTruthy();
        expect(screen.queryByText('Invalid Recipe')).toBeFalsy();
        expect(screen.queryByText('Negative ID Recipe')).toBeFalsy();
      });
    });

    it('should validate recipes using content validation', async () => {
      const { isValidRecipe } = require('../../../utils/contentValidation');
      
      render(<RecipesContainer />);

      // Switch to discover tab to trigger search recipe validation
      fireEvent.press(screen.getByTestId('discover-tab'));
      
      await waitFor(() => {
        expect(isValidRecipe).toHaveBeenCalled();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading indicator during data fetch', async () => {
      // Create a promise that doesn't resolve immediately
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      
      mockFetch.mockReturnValue(pendingPromise);

      render(<RecipesContainer />);

      // Should show loading state
      expect(screen.getByText('Finding delicious recipes...')).toBeTruthy();
      expect(screen.getByTestId('loading-indicator')).toBeTruthy();

      // Resolve the promise
      resolvePromise!({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.pantryRecipes)
      });

      await waitFor(() => {
        expect(screen.queryByText('Finding delicious recipes...')).toBeFalsy();
      });
    });

    it('should handle refresh state correctly', async () => {
      render(<RecipesContainer />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Trigger pull-to-refresh
      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent(scrollView, 'refresh');

      // Should make fresh API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2); // Initial + refresh
      });
    });
  });

  describe('Component Integration', () => {
    it('should pass correct props to RecipesTabs', async () => {
      render(<RecipesContainer />);

      // Verify RecipesTabs receives correct props
      expect(screen.getByTestId('header-title')).toBeTruthy();
      expect(screen.getByTestId('search-container')).toBeTruthy();
      expect(screen.getByTestId('tab-container')).toBeTruthy();
    });

    it('should pass correct props to RecipesFilters', async () => {
      render(<RecipesContainer />);

      // Switch to discover tab to see filters
      fireEvent.press(screen.getByTestId('discover-tab'));
      
      await waitFor(() => {
        expect(screen.getByTestId('dietary-filter-vegetarian')).toBeTruthy();
      });
    });

    it('should pass correct props to RecipesList', async () => {
      render(<RecipesContainer />);

      await waitFor(() => {
        expect(screen.getByTestId('recipes-scroll-view')).toBeTruthy();
        expect(screen.getByTestId('recipes-grid')).toBeTruthy();
      });
    });

    it('should handle recipe save through RecipesList', async () => {
      render(<RecipesContainer />);

      await waitFor(() => {
        expect(screen.getByTestId('bookmark-button-1')).toBeTruthy();
      });

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockApiResponses.saveRecipeSuccess)
      } as Response);

      fireEvent.press(screen.getByTestId('bookmark-button-1'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Pantry Recipe 1')
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle network failures gracefully', async () => {
      mockFetch.mockRejectedValue(new Error('Failed to fetch'));

      render(<RecipesContainer />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to load recipes. Please try again.'
        );
      });
    });

    it('should handle malformed API responses', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(null) // Malformed response
      } as Response);

      render(<RecipesContainer />);

      await waitFor(() => {
        // Should handle gracefully without crashing
        expect(screen.getByTestId('empty-recipes')).toBeTruthy();
      });
    });

    it('should validate ingredient counts and warn on failure', async () => {
      const { validateIngredientCounts } = require('../../../utils/ingredientMatcher');
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      validateIngredientCounts.mockReturnValue(false); // Simulate validation failure

      render(<RecipesContainer />);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          expect.stringContaining('Ingredient count validation failed')
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Search Functionality', () => {
    it('should handle empty search queries correctly', async () => {
      render(<RecipesContainer />);

      // Switch to discover tab
      fireEvent.press(screen.getByTestId('discover-tab'));
      
      // Empty search should fetch random recipes
      const searchInput = screen.getByTestId('search-input');
      fireEvent.changeText(searchInput, '');
      fireEvent.press(screen.getByTestId('search-submit-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/random'),
          expect.any(Object)
        );
      });
    });

    it('should include filters in search requests', async () => {
      render(<RecipesContainer />);

      // Switch to discover tab
      fireEvent.press(screen.getByTestId('discover-tab'));
      
      await waitFor(() => {
        expect(screen.getByTestId('dietary-filter-vegetarian')).toBeTruthy();
      });

      // Select filters
      fireEvent.press(screen.getByTestId('dietary-filter-vegetarian'));
      fireEvent.press(screen.getByTestId('dietary-filter-vegan'));

      // Perform search
      const searchInput = screen.getByTestId('search-input');
      fireEvent.changeText(searchInput, 'pasta');
      fireEvent.press(screen.getByTestId('search-submit-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/complex'),
          expect.objectContaining({
            body: expect.stringContaining('vegetarian,vegan')
          })
        );
      });
    });

    it('should filter pantry recipes locally', async () => {
      render(<RecipesContainer />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
        expect(screen.getByText('Pantry Recipe 2')).toBeTruthy();
      });

      // Search should filter locally in pantry tab
      const searchInput = screen.getByTestId('search-input');
      fireEvent.changeText(searchInput, 'Recipe 1');

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
        expect(screen.queryByText('Pantry Recipe 2')).toBeFalsy();
      });
    });
  });
});