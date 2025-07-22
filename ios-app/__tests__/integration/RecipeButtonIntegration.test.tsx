import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert } from 'react-native';
import RecipesScreen from '../../app/(tabs)/recipes';
import RecipeDetailsScreen from '../../app/recipe-details';
import RecipeDetailCardV2 from '../../components/recipes/RecipeDetailCardV2';
import { useAuth } from '../../context/AuthContext';
import { useItems } from '../../context/ItemsContext';
import { useRouter, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  createMockRecipe,
  createMockSavedRecipe,
  mockApiResponses,
  mockErrorResponses,
  testStates,
  createMockAuthContext,
  createMockItemsContext,
  createMockNavigation
} from '../helpers/recipeTestUtils';

// Mock all dependencies
jest.mock('../../context/AuthContext');
jest.mock('../../context/ItemsContext');
jest.mock('expo-router');
jest.mock('@react-native-async-storage/async-storage');
jest.mock('../../config', () => ({
  Config: { API_BASE_URL: 'http://localhost:8000' }
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseItems = useItems as jest.MockedFunction<typeof useItems>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockUseLocalSearchParams = useLocalSearchParams as jest.MockedFunction<typeof useLocalSearchParams>;
const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('Recipe Button Integration Tests', () => {
  let mockNavigation: ReturnType<typeof createMockNavigation>;

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockNavigation = createMockNavigation();
    
    mockUseAuth.mockReturnValue(createMockAuthContext());
    mockUseItems.mockReturnValue(createMockItemsContext());
    mockUseRouter.mockReturnValue(mockNavigation);
    mockUseLocalSearchParams.mockReturnValue({});

    // Default successful fetch responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/recipes/search/from-pantry')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.pantryRecipes)
        } as Response);
      }
      if (url.includes('/user-recipes') && !url.includes('/rating') && !url.includes('/favorite')) {
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
        json: () => Promise.resolve(mockApiResponses.saveRecipeSuccess)
      } as Response);
    });

    mockAsyncStorage.getItem.mockResolvedValue('[]');
    mockAsyncStorage.setItem.mockResolvedValue();
  });

  describe('Recipes Screen Button Functionality', () => {
    it('should handle all tab navigation buttons correctly', async () => {
      render(<RecipesScreen />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Test Discover tab
      fireEvent.press(screen.getByText('Discover'));
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/random'),
          expect.any(Object)
        );
      });

      // Test My Recipes tab
      fireEvent.press(screen.getByText('My Recipes'));
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.any(Object)
        );
      });

      // Back to From Pantry tab
      fireEvent.press(screen.getByText('From Pantry'));
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/from-pantry'),
          expect.any(Object)
        );
      });
    });

    it('should handle search functionality across tabs', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Test search in pantry tab (local filter)
      const searchInput = screen.getByPlaceholderText('Search pantry recipes...');
      fireEvent.changeText(searchInput, 'Recipe 1');

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
        expect(screen.queryByText('Pantry Recipe 2')).toBeFalsy();
      });

      // Clear search
      fireEvent.press(screen.getByTestId('clear-search-button'));
      expect(searchInput.props.value).toBe('');

      // Test search in discover tab (API search)
      fireEvent.press(screen.getByText('Discover'));
      
      const discoverSearchInput = screen.getByPlaceholderText('Search all recipes...');
      fireEvent.changeText(discoverSearchInput, 'pasta');
      fireEvent.press(screen.getByText('Search'));

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

    it('should handle filter buttons in discover tab', async () => {
      render(<RecipesScreen />);

      // Switch to discover tab
      fireEvent.press(screen.getByText('Discover'));

      await waitFor(() => {
        expect(screen.getByText('Vegetarian')).toBeTruthy();
      });

      // Test dietary filters
      fireEvent.press(screen.getByText('Vegetarian'));
      fireEvent.press(screen.getByText('Vegan'));
      fireEvent.press(screen.getByText('Gluten-Free'));

      // Test cuisine filters
      fireEvent.press(screen.getByText('Italian'));
      fireEvent.press(screen.getByText('Mexican'));

      // Test meal type filters
      fireEvent.press(screen.getByText('Breakfast'));
      fireEvent.press(screen.getByText('Dinner'));

      // Verify filters are visually active
      expect(screen.getByText('Vegetarian').props.style).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ color: '#297A56' })
        ])
      );
    });

    it('should handle sort modal and sorting options', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Open sort modal
      fireEvent.press(screen.getByTestId('sort-button'));

      expect(screen.getByText('Sort By')).toBeTruthy();
      expect(screen.getByText('Name (A-Z)')).toBeTruthy();
      expect(screen.getByText('Recently Added')).toBeTruthy();
      expect(screen.getByText('Highest Rated')).toBeTruthy();
      expect(screen.getByText('Fewest Missing')).toBeTruthy();

      // Test sorting by name
      fireEvent.press(screen.getByText('Name (A-Z)'));

      const recipeTexts = screen.getAllByTestId('recipe-title');
      expect(recipeTexts[0].props.children).toBe('Pantry Recipe 1');
      expect(recipeTexts[1].props.children).toBe('Pantry Recipe 2');

      // Test sorting by missing ingredients
      fireEvent.press(screen.getByTestId('sort-button'));
      fireEvent.press(screen.getByText('Fewest Missing'));

      // Should sort by missing count (recipe 1 has 1 missing, recipe 2 has 2)
      const sortedRecipeTexts = screen.getAllByTestId('recipe-title');
      expect(sortedRecipeTexts[0].props.children).toBe('Pantry Recipe 1');
    });

    it('should handle recipe card interactions', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Test recipe card navigation
      fireEvent.press(screen.getByText('Pantry Recipe 1'));
      expect(mockNavigation.push).toHaveBeenCalledWith({
        pathname: '/recipe-spoonacular-detail',
        params: { recipeId: '1' }
      });

      // Test bookmark button
      const bookmarkButton = screen.getByTestId('bookmark-button-1');
      fireEvent.press(bookmarkButton);

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

    it('should handle My Recipes tab functionality', async () => {
      render(<RecipesScreen />);

      // Switch to My Recipes tab
      fireEvent.press(screen.getByText('My Recipes'));

      await waitFor(() => {
        expect(screen.getByText('Saved Recipe 1')).toBeTruthy();
      });

      // Test saved/cooked sub-tabs
      fireEvent.press(screen.getByText('🍳 Cooked'));
      
      // Should show rating filters in cooked tab
      expect(screen.getByText('All')).toBeTruthy();
      expect(screen.getByText('Liked')).toBeTruthy();
      expect(screen.getByText('Disliked')).toBeTruthy();

      // Test rating filter
      fireEvent.press(screen.getByText('Liked'));
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes?status=cooked&rating=thumbs_up'),
          expect.any(Object)
        );
      });

      // Test rating buttons on recipes
      const thumbsUpButton = screen.getByTestId('thumbs-up-button-saved-1');
      fireEvent.press(thumbsUpButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes/saved-1/rating'),
          expect.objectContaining({
            method: 'PUT',
            body: expect.stringContaining('thumbs_up')
          })
        );
      });

      // Test favorite button
      const favoriteButton = screen.getByTestId('favorite-button-saved-1');
      fireEvent.press(favoriteButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes/saved-1/favorite'),
          expect.objectContaining({
            method: 'PUT'
          })
        );
      });

      // Test delete button
      const deleteButton = screen.getByTestId('delete-button-saved-1');
      fireEvent.press(deleteButton);

      expect(Alert.alert).toHaveBeenCalledWith(
        'Delete Recipe',
        'Are you sure you want to remove this recipe from your collection?',
        expect.arrayContaining([
          expect.objectContaining({ text: 'Cancel' }),
          expect.objectContaining({ text: 'Delete' })
        ])
      );
    });

    it('should handle header action buttons', async () => {
      render(<RecipesScreen />);

      // Test chat button
      fireEvent.press(screen.getByTestId('chat-button'));
      expect(mockNavigation.push).toHaveBeenCalledWith('/chat');

      // Test sort button
      fireEvent.press(screen.getByTestId('sort-button'));
      expect(screen.getByText('Sort By')).toBeTruthy();
    });

    it('should handle pull-to-refresh functionality', async () => {
      render(<RecipesScreen />);

      await waitFor(() => {
        expect(screen.getByText('Pantry Recipe 1')).toBeTruthy();
      });

      // Simulate pull to refresh
      const scrollView = screen.getByTestId('recipes-scroll-view');
      fireEvent(scrollView, 'refresh');

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/search/from-pantry'),
          expect.any(Object)
        );
      });
    });
  });

  describe('Recipe Details Screen Button Functionality', () => {
    beforeEach(() => {
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(createMockRecipe({ 
          name: 'Test Recipe',
          missing_ingredients: ['salt', 'pepper'],
          available_ingredients: ['chicken', 'pasta']
        }))
      });

      // Mock additional endpoints for recipe details
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/pantry/items')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.pantryItems)
          } as Response);
        }
        if (url.includes('/recipes/complete')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockApiResponses.recipeCompleteSuccess)
          } as Response);
        }
        if (url.includes('/recipes/image/generate')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ image_url: 'https://example.com/generated.jpg' })
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.saveRecipeSuccess)
        } as Response);
      });
    });

    it('should handle navigation buttons', () => {
      render(<RecipeDetailsScreen />);

      // Test back button
      fireEvent.press(screen.getByTestId('back-button'));
      expect(mockNavigation.back).toHaveBeenCalled();

      // Test close button
      fireEvent.press(screen.getByTestId('close-button'));
      expect(mockNavigation.replace).toHaveBeenCalledWith('/(tabs)');
    });

    it('should handle rating buttons', async () => {
      render(<RecipeDetailsScreen />);

      // Test thumbs up
      fireEvent.press(screen.getByTestId('thumbs-up-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('thumbs_up')
          })
        );
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'Rating Saved',
        'Your positive feedback helps improve future recommendations!',
        expect.any(Array)
      );

      // Test thumbs down
      fireEvent.press(screen.getByTestId('thumbs-down-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            body: expect.stringContaining('thumbs_down')
          })
        );
      });
    });

    it('should handle favorite button', async () => {
      render(<RecipeDetailsScreen />);

      fireEvent.press(screen.getByTestId('favorite-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Test Recipe')
          })
        );
      });
    });

    it('should handle cooking action buttons', () => {
      render(<RecipeDetailsScreen />);

      // Test Start Cooking button (with missing ingredients)
      fireEvent.press(screen.getByText('Start Cooking'));

      expect(Alert.alert).toHaveBeenCalledWith(
        'Missing Ingredients',
        expect.stringContaining('You are missing 2 ingredient'),
        expect.arrayContaining([
          expect.objectContaining({ text: 'Cancel' }),
          expect.objectContaining({ text: 'Add to Shopping List' }),
          expect.objectContaining({ text: 'Continue' })
        ])
      );

      // Test Cook Without Tracking button
      fireEvent.press(screen.getByText('Cook Without Tracking Ingredients'));

      expect(mockNavigation.push).toHaveBeenCalledWith({
        pathname: '/cooking-mode',
        params: {
          recipe: expect.any(String)
        }
      });
    });

    it('should handle Quick Complete button and modal', async () => {
      render(<RecipeDetailsScreen />);

      fireEvent.press(screen.getByText('Quick Complete'));

      // Should load pantry items
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/pantry/items'),
          expect.any(Object)
        );
      });

      // Should show completion modal
      await waitFor(() => {
        expect(screen.getByTestId('recipe-completion-modal')).toBeTruthy();
      });

      // Test modal confirmation
      fireEvent.press(screen.getByTestId('completion-confirm-button'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/complete'),
          expect.objectContaining({
            method: 'POST'
          })
        );
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'Recipe Completed! ✅',
        'Recipe completed successfully!',
        expect.any(Array)
      );
    });

    it('should handle shopping list button', async () => {
      render(<RecipeDetailsScreen />);

      fireEvent.press(screen.getByText('Add to Shopping List'));

      await waitFor(() => {
        expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
          '@PrepSense_ShoppingList',
          expect.stringContaining('salt')
        );
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'Added to Shopping List',
        '2 items added to your shopping list.',
        expect.arrayContaining([
          expect.objectContaining({ text: 'View List' }),
          expect.objectContaining({ text: 'OK' })
        ])
      );
    });

    it('should handle image retry button', async () => {
      // Mock image generation failure
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/recipes/image/generate')) {
          return Promise.reject(new Error('Image generation failed'));
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });

      render(<RecipeDetailsScreen />);

      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeTruthy();
      });

      fireEvent.press(screen.getByText('Retry'));

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/recipes/image/generate'),
        expect.any(Object)
      );
    });
  });

  describe('Recipe Detail Card V2 Button Functionality', () => {
    const mockRecipe = createMockRecipe({
      title: 'Card Test Recipe',
      available_ingredients: ['ingredient 1', 'ingredient 2'],
      pantry_item_matches: {
        'ingredient 1': [{ pantry_item_id: 1 }],
        'ingredient 2': [{ pantry_item_id: 2 }]
      }
    });

    it('should handle navigation and action buttons', () => {
      const onBack = jest.fn();
      render(<RecipeDetailCardV2 recipe={mockRecipe} onBack={onBack} />);

      // Test back button
      fireEvent.press(screen.getByTestId('back-button'));
      expect(onBack).toHaveBeenCalled();

      // Test Cook Now button
      fireEvent.press(screen.getByText('Cook Now'));
      expect(mockNavigation.push).toHaveBeenCalledWith({
        pathname: '/cooking-mode',
        params: {
          recipeId: mockRecipe.id,
          recipeData: JSON.stringify(mockRecipe)
        }
      });
    });

    it('should handle bookmark button with animation', async () => {
      // Mock recipe service
      const recipeService = require('../../services/recipeService');
      recipeService.recipeService.saveRecipe = jest.fn().mockResolvedValue({ success: true });

      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const bookmarkButton = screen.getByTestId('bookmark-button');
      fireEvent.press(bookmarkButton);

      await waitFor(() => {
        expect(recipeService.recipeService.saveRecipe).toHaveBeenCalledWith(mockRecipe, 111);
      });
    });

    it('should handle ingredient disclosure buttons', () => {
      const recipeWithManyIngredients = createMockRecipe({
        extendedIngredients: Array.from({ length: 8 }, (_, i) => ({
          id: i + 1,
          name: `ingredient ${i + 1}`,
          original: `ingredient ${i + 1} (${i + 1} units)`,
          amount: i + 1,
          unit: 'units'
        }))
      });

      render(<RecipeDetailCardV2 recipe={recipeWithManyIngredients} />);

      // Should show "Show all" button
      expect(screen.getByText('Show all 8 ingredients')).toBeTruthy();

      fireEvent.press(screen.getByText('Show all 8 ingredients'));

      expect(screen.getByText('Show less')).toBeTruthy();
      expect(screen.getByText('ingredient 6 (6 units)')).toBeTruthy();
    });

    it('should handle shopping list accordion', async () => {
      const shoppingListService = require('../../services/shoppingListService');
      shoppingListService.shoppingListService.addItem = jest.fn().mockResolvedValue({ success: true });

      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Test accordion toggle
      const accordionHeader = screen.getByText('Items to Buy (2)');
      fireEvent.press(accordionHeader);

      // Should collapse
      expect(screen.queryByText('• missing 1 (1 tbsp)')).toBeFalsy();

      // Expand again
      fireEvent.press(accordionHeader);
      expect(screen.getByText('• missing 1 (1 tbsp)')).toBeTruthy();

      // Test add to shopping list
      fireEvent.press(screen.getByText('Add to Shopping List'));

      await waitFor(() => {
        expect(shoppingListService.shoppingListService.addItem).toHaveBeenCalledTimes(2);
      });
    });

    it('should handle nutrition modal', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Open nutrition modal
      fireEvent.press(screen.getByText('400 kcal'));

      expect(screen.getByText('Nutrition Facts')).toBeTruthy();
      expect(screen.getByText('Calories')).toBeTruthy();
      expect(screen.getByText('400')).toBeTruthy();

      // Close modal
      fireEvent.press(screen.getByTestId('nutrition-modal-close'));
      expect(screen.queryByText('Nutrition Facts')).toBeFalsy();
    });

    it('should handle rating flow after cooking', async () => {
      const onRatingSubmitted = jest.fn();
      const recipeService = require('../../services/recipeService');
      recipeService.recipeService.rateRecipe = jest.fn().mockResolvedValue({ success: true });

      render(<RecipeDetailCardV2 recipe={mockRecipe} onRatingSubmitted={onRatingSubmitted} />);

      // Start cooking
      fireEvent.press(screen.getByText('Cook Now'));

      // Simulate finishing cooking
      fireEvent.press(screen.getByText('Finish Cooking'));

      expect(screen.getByText('How did it turn out?')).toBeTruthy();

      // Submit positive rating
      fireEvent.press(screen.getByTestId('modal-thumbs-up'));

      await waitFor(() => {
        expect(recipeService.recipeService.rateRecipe).toHaveBeenCalledWith(mockRecipe.id, 111, 'thumbs_up');
        expect(onRatingSubmitted).toHaveBeenCalledWith('thumbs_up');
      });
    });
  });

  describe('Error Handling for Button Actions', () => {
    it('should handle API errors gracefully', async () => {
      // Mock API failure
      mockFetch.mockRejectedValue(new Error('API Error'));

      render(<RecipesScreen />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to load recipes. Please try again.'
        );
      });
    });

    it('should handle shopping list save errors', async () => {
      mockAsyncStorage.setItem.mockRejectedValue(new Error('Storage error'));
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(createMockRecipe())
      });

      render(<RecipeDetailsScreen />);

      fireEvent.press(screen.getByText('Add to Shopping List'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to add items to shopping list. Please try again.'
        );
      });
    });

    it('should handle network connectivity issues', async () => {
      mockFetch.mockImplementation(() => Promise.reject(new Error('Network error')));

      render(<RecipesScreen />);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to load recipes. Please try again.'
        );
      });
    });
  });

  describe('Button State Management', () => {
    it('should disable buttons during loading states', async () => {
      // Mock delayed response
      mockFetch.mockImplementation(() => new Promise(() => {}));

      render(<RecipesScreen />);

      // Loading state should be shown
      expect(screen.getByText('Finding delicious recipes...')).toBeTruthy();
      expect(screen.getByTestId('loading-indicator')).toBeTruthy();
    });

    it('should show proper button states based on recipe data', () => {
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(testStates.allIngredientsAvailable)
      });

      render(<RecipeDetailsScreen />);

      // Should show enabled Start Cooking button
      const startCookingButton = screen.getByText('Start Cooking');
      expect(startCookingButton).toBeTruthy();
      // Button should not be disabled
      expect(startCookingButton.props.style).not.toEqual(
        expect.arrayContaining([
          expect.objectContaining({ backgroundColor: '#A0A0A0' })
        ])
      );
    });

    it('should show appropriate buttons for recipes with no available ingredients', () => {
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(testStates.noIngredientsAvailable)
      });

      render(<RecipeDetailsScreen />);

      expect(screen.getByText('No ingredients available')).toBeTruthy();
      expect(screen.getByText('Add to Shopping List')).toBeTruthy();
      expect(screen.getByText('Cook Without Tracking')).toBeTruthy();
    });
  });
});