// recipeAvailabilityCascade.test.tsx
// Test suite for verifying recipe availability percentage updates when ingredients are consumed

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import RecipesScreen from '../../screens/RecipesScreen';
import { apiClient } from '../../services/apiClient';
import { recipeService } from '../../services/recipeService';
import { pantryService } from '../../services/pantryService';

// Mock the services
jest.mock('../../services/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }
}));

jest.mock('../../services/recipeService');
jest.mock('../../services/pantryService');

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
const mockRecipeService = recipeService as jest.Mocked<typeof recipeService>;
const mockPantryService = pantryService as jest.Mocked<typeof pantryService>;

describe('Recipe Availability Cascade Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Mock data
  const mockPantryBefore = [
    { id: 1, name: 'Flour', quantity: 500, unit: 'g', category: 'Baking' },
    { id: 2, name: 'Eggs', quantity: 12, unit: 'units', category: 'Dairy' },
    { id: 3, name: 'Milk', quantity: 1000, unit: 'ml', category: 'Dairy' },
    { id: 4, name: 'Sugar', quantity: 300, unit: 'g', category: 'Baking' }
  ];

  const mockPantryAfter = [
    { id: 1, name: 'Flour', quantity: 200, unit: 'g', category: 'Baking' }, // 300g consumed
    { id: 2, name: 'Eggs', quantity: 10, unit: 'units', category: 'Dairy' }, // 2 eggs consumed
    { id: 3, name: 'Milk', quantity: 750, unit: 'ml', category: 'Dairy' }, // 250ml consumed
    { id: 4, name: 'Sugar', quantity: 300, unit: 'g', category: 'Baking' } // unchanged
  ];

  const mockRecipesBefore = [
    {
      id: 1,
      title: 'Pancakes',
      available_count: 4,
      missing_count: 0,
      match_score: 100,
      extendedIngredients: [
        { name: 'flour', amount: 200, unit: 'g' },
        { name: 'eggs', amount: 2, unit: '' },
        { name: 'milk', amount: 300, unit: 'ml' },
        { name: 'sugar', amount: 50, unit: 'g' }
      ]
    },
    {
      id: 2,
      title: 'Cake',
      available_count: 4,
      missing_count: 0,
      match_score: 100,
      extendedIngredients: [
        { name: 'flour', amount: 400, unit: 'g' },
        { name: 'eggs', amount: 4, unit: '' },
        { name: 'sugar', amount: 200, unit: 'g' }
      ]
    },
    {
      id: 3,
      title: 'French Toast',
      available_count: 3,
      missing_count: 0,
      match_score: 100,
      extendedIngredients: [
        { name: 'eggs', amount: 3, unit: '' },
        { name: 'milk', amount: 100, unit: 'ml' },
        { name: 'bread', amount: 6, unit: 'slices' } // Not in pantry
      ]
    }
  ];

  const mockRecipesAfter = [
    {
      ...mockRecipesBefore[0],
      match_score: 100 // Still 100% - has enough of everything
    },
    {
      ...mockRecipesBefore[1],
      available_count: 2,
      missing_count: 1,
      match_score: 67, // Now missing flour (only 200g left, needs 400g)
      missing_ingredients: ['flour']
    },
    {
      ...mockRecipesBefore[2],
      available_count: 2,
      missing_count: 1,
      match_score: 67 // Still missing bread
    }
  ];

  describe('Real-time Recipe Percentage Updates', () => {
    it('should update all recipe match scores when ingredients are consumed', async () => {
      // Setup initial state
      mockPantryService.getPantryItems.mockResolvedValue(mockPantryBefore);
      mockRecipeService.getRecipesWithAvailability.mockResolvedValue(mockRecipesBefore);

      const { getByText, getAllByText } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(getByText('Pancakes')).toBeTruthy();
        expect(getByText('100% available')).toBeTruthy();
      });

      // Simulate ingredient consumption (via Quick Complete)
      await act(async () => {
        // Mock the consumption event
        mockApiClient.post.mockResolvedValueOnce({
          data: { success: true, consumed_items: [
            { pantry_item_id: 1, quantity_consumed: 300 },
            { pantry_item_id: 2, quantity_consumed: 2 },
            { pantry_item_id: 3, quantity_consumed: 250 }
          ]}
        });

        // Trigger pantry update
        mockPantryService.getPantryItems.mockResolvedValue(mockPantryAfter);
        mockRecipeService.getRecipesWithAvailability.mockResolvedValue(mockRecipesAfter);
      });

      // Verify cascade updates
      await waitFor(() => {
        // Pancakes still 100%
        const pancakeCard = getByText('Pancakes').parent?.parent;
        expect(pancakeCard).toHaveTextContent('100% available');

        // Cake dropped to 67%
        const cakeCard = getByText('Cake').parent?.parent;
        expect(cakeCard).toHaveTextContent('67% available');
        expect(cakeCard).toHaveTextContent('Missing: flour');

        // French Toast remains 67%
        const frenchToastCard = getByText('French Toast').parent?.parent;
        expect(frenchToastCard).toHaveTextContent('67% available');
      });
    });

    it('should show visual indication of availability changes', async () => {
      mockPantryService.getPantryItems.mockResolvedValue(mockPantryBefore);
      mockRecipeService.getRecipesWithAvailability.mockResolvedValue(mockRecipesBefore);

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(getByText('Cake')).toBeTruthy();
      });

      // Check initial state - green indicator
      const cakeCard = getByTestId('recipe-card-2');
      expect(cakeCard).toHaveStyle({ borderColor: '#4CAF50' }); // Green for 100%

      // Simulate consumption
      await act(async () => {
        mockPantryService.getPantryItems.mockResolvedValue(mockPantryAfter);
        mockRecipeService.getRecipesWithAvailability.mockResolvedValue(mockRecipesAfter);
      });

      // Check updated state - yellow indicator
      await waitFor(() => {
        expect(cakeCard).toHaveStyle({ borderColor: '#FFC107' }); // Yellow for partial
      });
    });

    it('should update recipe ordering based on new availability', async () => {
      const mockRecipesReordered = [
        mockRecipesAfter[0], // Pancakes 100%
        mockRecipesAfter[1], // Cake 67%
        mockRecipesAfter[2], // French Toast 67%
        { ...mockRecipesBefore[0], id: 4, title: 'Omelette', match_score: 0, available_count: 0, missing_count: 3 }
      ];

      mockRecipeService.getRecipesWithAvailability
        .mockResolvedValueOnce(mockRecipesBefore)
        .mockResolvedValueOnce(mockRecipesReordered);

      const { getByText, getAllByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        const recipeCards = getAllByTestId(/recipe-card-/);
        expect(recipeCards[0]).toHaveTextContent('Pancakes');
        expect(recipeCards[1]).toHaveTextContent('Cake');
      });

      // After consumption, verify reordering
      await act(async () => {
        mockPantryService.getPantryItems.mockResolvedValue(mockPantryAfter);
      });

      await waitFor(() => {
        const recipeCards = getAllByTestId(/recipe-card-/);
        expect(recipeCards[0]).toHaveTextContent('Pancakes'); // Still first (100%)
        expect(recipeCards[1]).toHaveTextContent('Cake'); // Now 67%
        expect(recipeCards[3]).toHaveTextContent('Omelette'); // Last (0%)
      });
    });
  });

  describe('Complex Cascade Scenarios', () => {
    it('should handle complete depletion of ingredients', async () => {
      const pantryDepleted = [
        { id: 1, name: 'Flour', quantity: 0, unit: 'g', category: 'Baking' }, // Completely gone
        { id: 2, name: 'Eggs', quantity: 1, unit: 'units', category: 'Dairy' }
      ];

      const recipesAfterDepletion = mockRecipesBefore.map(recipe => ({
        ...recipe,
        available_count: recipe.extendedIngredients.filter(ing => ing.name !== 'flour').length,
        missing_count: recipe.extendedIngredients.filter(ing => ing.name === 'flour').length,
        match_score: recipe.extendedIngredients.some(ing => ing.name === 'flour') ? 0 : 100,
        missing_ingredients: recipe.extendedIngredients.some(ing => ing.name === 'flour') ? ['flour'] : []
      }));

      mockPantryService.getPantryItems
        .mockResolvedValueOnce(mockPantryBefore)
        .mockResolvedValueOnce(pantryDepleted);
      
      mockRecipeService.getRecipesWithAvailability
        .mockResolvedValueOnce(mockRecipesBefore)
        .mockResolvedValueOnce(recipesAfterDepletion);

      const { getByText, queryByText } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(getByText('Pancakes')).toBeTruthy();
      });

      // Deplete flour
      await act(async () => {
        // Trigger update
      });

      await waitFor(() => {
        // All recipes needing flour should show 0% or very low
        expect(queryByText('100% available')).toBeFalsy();
        expect(getByText('Missing: flour')).toBeTruthy();
      });
    });

    it('should update CrewAI recommendations based on availability changes', async () => {
      // Mock CrewAI endpoint
      mockApiClient.post.mockImplementation((url) => {
        if (url.includes('/ai/recommendations')) {
          // Should prioritize recipes with available ingredients
          return Promise.resolve({
            data: {
              recommendations: [
                { recipe_id: 1, reason: 'All ingredients available' },
                { recipe_id: 3, reason: 'Only missing bread' }
                // Cake (id: 2) not recommended due to insufficient flour
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      // Trigger AI recommendations
      await act(async () => {
        fireEvent.press(getByTestId('ai-recommendations-button'));
      });

      await waitFor(() => {
        // Verify AI prioritizes available recipes
        expect(mockApiClient.post).toHaveBeenCalledWith(
          expect.stringContaining('/ai/recommendations'),
          expect.objectContaining({
            pantry_state: expect.any(Array),
            availability_threshold: expect.any(Number)
          })
        );
      });
    });

    it('should show animation when percentages change', async () => {
      mockPantryService.getPantryItems.mockResolvedValue(mockPantryBefore);
      mockRecipeService.getRecipesWithAvailability.mockResolvedValue(mockRecipesBefore);

      const { getByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        const percentageText = getByTestId('percentage-text-2');
        expect(percentageText).toHaveTextContent('100%');
      });

      // Update to lower availability
      await act(async () => {
        mockRecipeService.getRecipesWithAvailability.mockResolvedValue(mockRecipesAfter);
      });

      // Check for animation class/style
      await waitFor(() => {
        const percentageText = getByTestId('percentage-text-2');
        expect(percentageText).toHaveAnimatedStyle({ opacity: 0.5 }); // Pulsing animation
        expect(percentageText).toHaveTextContent('67%');
      });
    });
  });

  describe('Performance and Optimization', () => {
    it('should batch updates for multiple recipe changes', async () => {
      // Mock 50 recipes
      const manyRecipes = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        title: `Recipe ${i + 1}`,
        match_score: 100,
        available_count: 4,
        missing_count: 0
      }));

      mockRecipeService.getRecipesWithAvailability.mockResolvedValue(manyRecipes);

      const { getByText } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(getByText('Recipe 1')).toBeTruthy();
      });

      const updateStartTime = Date.now();

      // Update all recipes
      await act(async () => {
        const updatedRecipes = manyRecipes.map(r => ({ ...r, match_score: 50 }));
        mockRecipeService.getRecipesWithAvailability.mockResolvedValue(updatedRecipes);
      });

      const updateEndTime = Date.now();
      const updateDuration = updateEndTime - updateStartTime;

      // Should complete within 500ms even with 50 recipes
      expect(updateDuration).toBeLessThan(500);
    });

    it('should not re-render unchanged recipes', async () => {
      const renderSpy = jest.fn();
      
      // Mock recipe card to track renders
      jest.mock('../../components/RecipeCard', () => ({
        __esModule: true,
        default: (props: any) => {
          renderSpy(props.recipe.id);
          return null;
        }
      }));

      mockRecipeService.getRecipesWithAvailability
        .mockResolvedValueOnce(mockRecipesBefore)
        .mockResolvedValueOnce([
          mockRecipesBefore[0], // Unchanged
          mockRecipesAfter[1], // Changed
          mockRecipesBefore[2] // Unchanged
        ]);

      render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(renderSpy).toHaveBeenCalledTimes(3); // Initial render
      });

      renderSpy.mockClear();

      // Update with partial changes
      await act(async () => {
        // Trigger update
      });

      await waitFor(() => {
        // Only changed recipe should re-render
        expect(renderSpy).toHaveBeenCalledWith(2); // Only Cake
        expect(renderSpy).not.toHaveBeenCalledWith(1); // Not Pancakes
        expect(renderSpy).not.toHaveBeenCalledWith(3); // Not French Toast
      });
    });
  });
});