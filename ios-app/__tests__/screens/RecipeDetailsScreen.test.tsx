import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert } from 'react-native';
import RecipeDetailsScreen from '../../app/recipe-details';
import { useAuth } from '../../context/AuthContext';
import { useRouter, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock dependencies
jest.mock('../../context/AuthContext');
jest.mock('expo-router');
jest.mock('@react-native-async-storage/async-storage');
jest.mock('../../config', () => ({
  Config: {
    API_BASE_URL: 'http://localhost:8000'
  }
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
const mockUseLocalSearchParams = useLocalSearchParams as jest.MockedFunction<typeof useLocalSearchParams>;
const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock router
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockBack = jest.fn();

// Sample recipe data
const mockRecipe = {
  name: 'Chicken Alfredo Pasta',
  time: 30,
  nutrition: {
    calories: 650,
    protein: 35,
    carbs: 45,
    fat: 28
  },
  match_score: 0.75,
  ingredients: [
    'chicken breast (2 pieces)',
    'pasta (200g)',
    'heavy cream (200ml)',
    'parmesan cheese (50g)',
    'garlic (2 cloves)',
    'butter (30g)'
  ],
  available_ingredients: [
    'chicken breast (2 pieces)',
    'pasta (200g)',
    'garlic (2 cloves)'
  ],
  missing_ingredients: [
    'heavy cream (200ml)',
    'parmesan cheese (50g)',
    'butter (30g)'
  ],
  instructions: [
    'Cook pasta according to package directions.',
    'Season chicken with salt and pepper, then cook in a large skillet.',
    'Add garlic and cook for 1 minute.',
    'Pour in heavy cream and bring to a simmer.',
    'Add parmesan cheese and stir until melted.',
    'Add cooked pasta and toss to coat.',
    'Serve immediately with extra cheese.'
  ],
  image: 'https://example.com/chicken-alfredo.jpg'
};

const mockPantryItems = [
  {
    id: 1,
    pantry_item_id: 1,
    product_name: 'chicken breast',
    quantity: 3,
    unit_of_measurement: 'pieces',
    expiration_date: '2024-12-31',
    food_category: 'Meat'
  },
  {
    id: 2,
    pantry_item_id: 2,
    product_name: 'pasta',
    quantity: 500,
    unit_of_measurement: 'g',
    expiration_date: '2025-06-01',
    food_category: 'Grains'
  }
];

describe('RecipeDetailsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseAuth.mockReturnValue({
      user: { id: 111, email: 'test@example.com' },
      token: 'mock-token',
      isAuthenticated: true,
      signIn: jest.fn(),
      signOut: jest.fn(),
      isLoading: false
    });

    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: mockReplace,
      back: mockBack,
      canGoBack: jest.fn(),
      setParams: jest.fn(),
      pathname: '/recipe-details'
    });

    mockUseLocalSearchParams.mockReturnValue({
      recipe: JSON.stringify(mockRecipe)
    });

    // Mock successful fetch responses
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/pantry/items')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockPantryItems)
        } as Response);
      }
      
      if (url.includes('/user-recipes')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true })
        } as Response);
      }
      
      if (url.includes('/recipes/complete')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            summary: 'Recipe completed successfully!',
            insufficient_items: [],
            errors: []
          })
        } as Response);
      }

      if (url.includes('/recipes/image/generate')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            image_url: 'https://example.com/generated-image.jpg'
          })
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      } as Response);
    });

    // Mock AsyncStorage
    mockAsyncStorage.getItem.mockResolvedValue('[]');
    mockAsyncStorage.setItem.mockResolvedValue();
  });

  describe('Recipe Data Display', () => {
    it('should display recipe title and basic information', () => {
      render(<RecipeDetailsScreen />);

      expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      expect(screen.getByText('30 min')).toBeTruthy();
      expect(screen.getByText('650 cal')).toBeTruthy();
      expect(screen.getByText('35g protein')).toBeTruthy();
      expect(screen.getByText('75% match')).toBeTruthy();
    });

    it('should display all ingredients with correct availability status', () => {
      render(<RecipeDetailsScreen />);

      // Available ingredients should show with checkmarks
      expect(screen.getByText('chicken breast (2 pieces)')).toBeTruthy();
      expect(screen.getByText('pasta (200g)')).toBeTruthy();
      expect(screen.getByText('garlic (2 cloves)')).toBeTruthy();

      // Missing ingredients should show with add icons
      expect(screen.getByText('heavy cream (200ml)')).toBeTruthy();
      expect(screen.getByText('parmesan cheese (50g)')).toBeTruthy();
      expect(screen.getByText('butter (30g)')).toBeTruthy();

      // Check that ingredient items are rendered with proper testIDs
      expect(screen.getByTestId('ingredient-item-0')).toBeTruthy();
      expect(screen.getByTestId('ingredient-item-1')).toBeTruthy();
      expect(screen.getByTestId('ingredient-item-2')).toBeTruthy();
      expect(screen.getByTestId('ingredient-item-3')).toBeTruthy();
      expect(screen.getByTestId('ingredient-item-4')).toBeTruthy();
      expect(screen.getByTestId('ingredient-item-5')).toBeTruthy();
    });

    it('should display shopping list summary for missing ingredients', () => {
      render(<RecipeDetailsScreen />);

      expect(screen.getByText('🛒 Shopping list (3 items):')).toBeTruthy();
      expect(screen.getByText('• heavy cream (200ml)')).toBeTruthy();
      expect(screen.getByText('• parmesan cheese (50g)')).toBeTruthy();
      expect(screen.getByText('• butter (30g)')).toBeTruthy();
    });

    it('should display recipe instructions with step numbers', () => {
      render(<RecipeDetailsScreen />);

      expect(screen.getByText('Instructions')).toBeTruthy();
      
      // Check for step numbers
      expect(screen.getByTestId('step-number-1')).toBeTruthy();
      expect(screen.getByTestId('step-number-2')).toBeTruthy();
      expect(screen.getByTestId('step-number-7')).toBeTruthy();

      // Check for instruction text
      expect(screen.getByText('Cook pasta according to package directions.')).toBeTruthy();
      expect(screen.getByText('Season chicken with salt and pepper, then cook in a large skillet.')).toBeTruthy();
      expect(screen.getByText('Serve immediately with extra cheese.')).toBeTruthy();
    });

    it('should generate and display recipe image', async () => {
      // Use a recipe without an image to trigger generation
      const recipeWithoutImage = { ...mockRecipe };
      delete recipeWithoutImage.image;
      
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithoutImage)
      });
      
      render(<RecipeDetailsScreen />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/image/generate'),
          expect.any(Object)
        );
      });

      await waitFor(() => {
        const image = screen.getByTestId('recipe-image');
        expect(image.props.source.uri).toBe('https://example.com/generated-image.jpg');
      });
    });

    it('should handle recipe with no missing ingredients', () => {
      const recipeWithAllIngredients = {
        ...mockRecipe,
        missing_ingredients: [],
        available_ingredients: mockRecipe.ingredients
      };

      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithAllIngredients)
      });

      render(<RecipeDetailsScreen />);

      expect(screen.queryByText('🛒 Shopping list')).toBeFalsy();
      expect(screen.getByText('Start Cooking')).toBeTruthy();
    });

    it('should handle recipe with no available ingredients', () => {
      const recipeWithNoIngredients = {
        ...mockRecipe,
        available_ingredients: [],
        missing_ingredients: mockRecipe.ingredients
      };

      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithNoIngredients)
      });

      render(<RecipeDetailsScreen />);

      expect(screen.getByText('No ingredients available')).toBeTruthy();
      expect(screen.getByText('You\'ll need to shop for all 6 ingredients first')).toBeTruthy();
      expect(screen.getByText('Add to Shopping List')).toBeTruthy();
    });
  });

  describe('Button Functionality', () => {
    it('should navigate back when back button is pressed', () => {
      render(<RecipeDetailsScreen />);

      const backButton = screen.getByTestId('back-button');
      fireEvent.press(backButton);

      expect(mockBack).toHaveBeenCalled();
    });

    it('should close screen when close button is pressed', () => {
      render(<RecipeDetailsScreen />);

      const closeButton = screen.getByTestId('close-button');
      fireEvent.press(closeButton);

      expect(mockReplace).toHaveBeenCalledWith('/(tabs)');
    });

    it('should start cooking when Start Cooking button is pressed with all ingredients', () => {
      // Create a recipe with no missing ingredients
      const recipeWithAllIngredients = {
        ...mockRecipe,
        missing_ingredients: []
      };
      
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithAllIngredients)
      });
      
      render(<RecipeDetailsScreen />);

      const startCookingButton = screen.getByText('Start Cooking');
      fireEvent.press(startCookingButton);

      expect(mockPush).toHaveBeenCalledWith({
        pathname: '/cooking-mode',
        params: {
          recipe: JSON.stringify(recipeWithAllIngredients)
        }
      });
    });

    it('should show missing ingredients alert when Start Cooking is pressed with missing ingredients', () => {
      render(<RecipeDetailsScreen />);

      const startCookingButton = screen.getByText('Start Cooking');
      fireEvent.press(startCookingButton);

      expect(Alert.alert).toHaveBeenCalledWith(
        'Missing Ingredients',
        expect.stringContaining('You are missing 3 ingredient'),
        expect.arrayContaining([
          expect.objectContaining({ text: 'Cancel' }),
          expect.objectContaining({ text: 'Add to Shopping List' }),
          expect.objectContaining({ text: 'Continue' })
        ])
      );
    });

    it('should navigate to cooking mode when Cook Without Tracking is pressed', () => {
      render(<RecipeDetailsScreen />);

      const cookWithoutTrackingButton = screen.getByText('Cook Without Tracking Ingredients');
      fireEvent.press(cookWithoutTrackingButton);

      expect(mockPush).toHaveBeenCalledWith({
        pathname: '/cooking-mode',
        params: {
          recipe: JSON.stringify(mockRecipe)
        }
      });
    });

    it('should navigate to select ingredients screen when add to shopping list is pressed', async () => {
      render(<RecipeDetailsScreen />);

      const addToShoppingListButton = screen.getByText('Add to Shopping List');
      fireEvent.press(addToShoppingListButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith({
          pathname: '/select-ingredients',
          params: expect.objectContaining({
            ingredients: expect.any(String),
            recipeName: 'Chicken Alfredo Pasta'
          })
        });
      });
    });

    it('should toggle favorite status when bookmark button is pressed', async () => {
      render(<RecipeDetailsScreen />);

      const favoriteButton = screen.getByTestId('favorite-button');
      fireEvent.press(favoriteButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('Chicken Alfredo Pasta')
          })
        );
      });
    });

    it('should handle rating submission', async () => {
      render(<RecipeDetailsScreen />);

      const thumbsUpButton = screen.getByTestId('thumbs-up-button');
      fireEvent.press(thumbsUpButton);

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
        expect.arrayContaining([
          expect.objectContaining({ text: 'OK' })
        ])
      );
    });

    it('should toggle rating when same rating button is pressed twice', async () => {
      render(<RecipeDetailsScreen />);

      const thumbsUpButton = screen.getByTestId('thumbs-up-button');
      
      // First press - set to thumbs up
      fireEvent.press(thumbsUpButton);
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            body: expect.stringContaining('thumbs_up')
          })
        );
      });

      // Second press - should set to neutral
      fireEvent.press(thumbsUpButton);
      
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/user-recipes'),
          expect.objectContaining({
            body: expect.stringContaining('neutral')
          })
        );
      });
    });
  });

  describe('Quick Complete Functionality', () => {
    it('should open completion modal when Quick Complete is pressed', async () => {
      render(<RecipeDetailsScreen />);

      const quickCompleteButton = screen.getByText('Quick Complete');
      fireEvent.press(quickCompleteButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/pantry/items/111'),
          expect.any(Object)
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId('recipe-completion-modal')).toBeTruthy();
      });
    });

    it('should complete recipe with selected ingredients', async () => {
      render(<RecipeDetailsScreen />);

      const quickCompleteButton = screen.getByText('Quick Complete');
      fireEvent.press(quickCompleteButton);

      await waitFor(() => {
        expect(screen.getByTestId('recipe-completion-modal')).toBeTruthy();
      });

      // Mock the completion modal confirming with ingredient usage
      const mockIngredientUsages = [
        {
          ingredientName: 'chicken breast',
          selectedAmount: 2,
          requestedUnit: 'pieces'
        },
        {
          ingredientName: 'pasta',
          selectedAmount: 200,
          requestedUnit: 'g'
        }
      ];

      // Simulate modal confirmation
      const confirmButton = screen.getByTestId('completion-confirm-button');
      fireEvent.press(confirmButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/recipes/complete'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('chicken breast')
          })
        );
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'Recipe Completed! ✅',
        'Recipe completed successfully!',
        expect.arrayContaining([
          expect.objectContaining({ text: 'OK' })
        ])
      );
    });

    it('should handle completion with insufficient ingredients warning', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/recipes/complete')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              success: true,
              summary: 'Recipe completed with warnings.',
              insufficient_items: [
                {
                  ingredient: 'chicken breast',
                  needed: 2,
                  needed_unit: 'pieces',
                  consumed: 1
                }
              ],
              errors: []
            })
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });

      render(<RecipeDetailsScreen />);

      const quickCompleteButton = screen.getByText('Quick Complete');
      fireEvent.press(quickCompleteButton);

      await waitFor(() => {
        expect(screen.getByTestId('recipe-completion-modal')).toBeTruthy();
      });

      const confirmButton = screen.getByTestId('completion-confirm-button');
      fireEvent.press(confirmButton);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Recipe Completed with Warnings ⚠️',
          expect.stringContaining('Insufficient quantities'),
          expect.any(Array)
        );
      });
    });
  });

  describe('Image Generation', () => {
    it('should show loading state while generating image', () => {
      // Use a recipe without an image to trigger generation
      const recipeWithoutImage = { ...mockRecipe };
      delete recipeWithoutImage.image;
      
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithoutImage)
      });
      
      // Mock delayed image generation
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/recipes/image/generate')) {
          return new Promise(() => {}); // Never resolves
        }
        if (url.includes('/pantry/items')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockPantryItems)
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });

      render(<RecipeDetailsScreen />);

      expect(screen.getByText('Generating recipe image...')).toBeTruthy();
      expect(screen.getByTestId('image-loading-indicator')).toBeTruthy();
    });

    it('should show error state when image generation fails', async () => {
      // Use a recipe without an image to trigger generation
      const recipeWithoutImage = { ...mockRecipe };
      delete recipeWithoutImage.image;
      
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithoutImage)
      });
      
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/recipes/image/generate')) {
          return Promise.reject(new Error('Image generation failed'));
        }
        if (url.includes('/pantry/items')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockPantryItems)
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });

      render(<RecipeDetailsScreen />);

      await waitFor(() => {
        expect(screen.getByText('Image generation failed')).toBeTruthy();
        expect(screen.getByText('Retry')).toBeTruthy();
      });
    });

    it('should retry image generation when retry button is pressed', async () => {
      // Use a recipe without an image to trigger generation
      const recipeWithoutImage = { ...mockRecipe };
      delete recipeWithoutImage.image;
      
      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithoutImage)
      });
      
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/recipes/image/generate')) {
          return Promise.reject(new Error('Image generation failed'));
        }
        if (url.includes('/pantry/items')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockPantryItems)
          } as Response);
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

      const retryButton = screen.getByText('Retry');
      fireEvent.press(retryButton);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/recipes/image/generate'),
        expect.any(Object)
      );
    });

    it('should use Spoonacular image when available', () => {
      const recipeWithSpoonacularImage = {
        ...mockRecipe,
        image: 'https://spoonacular.com/recipe-image.jpg'
      };

      mockUseLocalSearchParams.mockReturnValue({
        recipe: JSON.stringify(recipeWithSpoonacularImage)
      });

      render(<RecipeDetailsScreen />);

      const image = screen.getByTestId('recipe-image');
      expect(image.props.source.uri).toBe('https://spoonacular.com/recipe-image.jpg');
    });
  });

  describe('Error Handling', () => {
    it('should handle missing recipe data gracefully', () => {
      mockUseLocalSearchParams.mockReturnValue({});

      render(<RecipeDetailsScreen />);

      expect(screen.getByText('Loading recipe...')).toBeTruthy();
      // ActivityIndicator doesn't have testID in the actual implementation
      expect(screen.getByText('Loading recipe...')).toBeTruthy();
    });

    it('should handle malformed recipe JSON', () => {
      mockUseLocalSearchParams.mockReturnValue({
        recipe: 'invalid-json'
      });

      render(<RecipeDetailsScreen />);

      expect(screen.getByText('Loading recipe...')).toBeTruthy();
    });

    it('should handle navigation errors gracefully', async () => {
      // Mock router.push to throw an error
      mockPush.mockImplementation(() => {
        throw new Error('Navigation error');
      });

      render(<RecipeDetailsScreen />);

      const addToShoppingListButton = screen.getByText('Add to Shopping List');
      
      // Should not crash when navigation fails
      expect(() => {
        fireEvent.press(addToShoppingListButton);
      }).not.toThrow();
    });

    it('should handle recipe completion errors', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/recipes/complete')) {
          return Promise.reject(new Error('API error'));
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });

      render(<RecipeDetailsScreen />);

      const quickCompleteButton = screen.getByText('Quick Complete');
      fireEvent.press(quickCompleteButton);

      await waitFor(() => {
        expect(screen.getByTestId('recipe-completion-modal')).toBeTruthy();
      });

      const confirmButton = screen.getByTestId('completion-confirm-button');
      fireEvent.press(confirmButton);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to update pantry. Please try again.'
        );
      });
    });

    it('should handle favorite toggle errors', async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes('/user-recipes')) {
          return Promise.reject(new Error('API error'));
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        } as Response);
      });

      render(<RecipeDetailsScreen />);

      const favoriteButton = screen.getByTestId('favorite-button');
      fireEvent.press(favoriteButton);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to update favorite status. Please try again.'
        );
      });
    });
  });

  describe('Navigation Integration', () => {
    it('should navigate to select ingredients screen from missing ingredients alert', () => {
      render(<RecipeDetailsScreen />);

      const startCookingButton = screen.getByText('Start Cooking');
      fireEvent.press(startCookingButton);

      // Get the alert and press "Add to Shopping List"
      const alertCalls = (Alert.alert as jest.Mock).mock.calls;
      const lastCall = alertCalls[alertCalls.length - 1];
      const buttons = lastCall[2];
      const addToShoppingListButton = buttons.find((btn: any) => btn.text === 'Add to Shopping List');
      
      addToShoppingListButton.onPress();

      expect(mockPush).toHaveBeenCalledWith({
        pathname: '/select-ingredients',
        params: {
          ingredients: JSON.stringify(mockRecipe.missing_ingredients),
          recipeName: 'Chicken Alfredo Pasta'
        }
      });
    });

    it('should navigate to select ingredients screen when add to shopping list is pressed', async () => {
      render(<RecipeDetailsScreen />);

      const addToShoppingListButton = screen.getByText('Add to Shopping List');
      fireEvent.press(addToShoppingListButton);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith({
          pathname: '/select-ingredients',
          params: expect.objectContaining({
            ingredients: expect.any(String),
            recipeName: 'Chicken Alfredo Pasta'
          })
        });
      });
    });
  });
});