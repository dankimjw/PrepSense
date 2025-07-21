import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { useRouter } from 'expo-router';
import RecipeDetailCardV2 from '../components/recipes/RecipeDetailCardV2';
import { apiClient } from '../services/apiClient';

// Mock dependencies
jest.mock('expo-router');
jest.mock('../services/apiClient');
jest.mock('../services/recipeService');
jest.mock('../services/pantryService');
jest.mock('../services/shoppingListService');
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

const mockRouter = {
  push: jest.fn(),
  back: jest.fn(),
};

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
mockUseRouter.mockReturnValue(mockRouter as any);

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('RecipeDetailCardV2 - Quick Complete Feature', () => {
  const mockRecipe = {
    id: 123,
    title: 'Test Recipe',
    image: 'https://example.com/image.jpg',
    readyInMinutes: 30,
    servings: 4,
    extendedIngredients: [
      {
        id: 1,
        name: 'chicken',
        original: '2 chicken breasts',
        amount: 2,
        unit: 'pieces',
      },
      {
        id: 2,
        name: 'rice',
        original: '1 cup rice',
        amount: 1,
        unit: 'cup',
      },
    ],
    analyzedInstructions: [
      {
        steps: [
          { number: 1, step: 'Cook the chicken' },
          { number: 2, step: 'Cook the rice' },
        ],
      },
    ],
    nutrition: {
      calories: 350,
      protein: 25,
      carbs: 40,
      fat: 10,
    },
    available_ingredients: ['chicken'],
    pantry_item_matches: {
      chicken: [{ pantry_item_id: 101 }],
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Quick Complete Button Rendering', () => {
    it('should render Quick Complete button alongside Cook Now button', () => {
      const { getByText } = render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(getByText('Cook Now')).toBeTruthy();
      expect(getByText('Quick Complete')).toBeTruthy();
    });

    it('should not show Quick Complete button when recipe is already being cooked', () => {
      const { getByText, queryByText, rerender } = render(
        <RecipeDetailCardV2 recipe={mockRecipe} />
      );

      // Initially both buttons should be visible
      expect(getByText('Cook Now')).toBeTruthy();
      expect(getByText('Quick Complete')).toBeTruthy();

      // Simulate cooking state
      fireEvent.press(getByText('Cook Now'));
      
      // After navigation, the component would typically update state
      // For this test, we'll manually trigger a re-render with cooking state
      const cookingRecipe = { ...mockRecipe, is_cooking: true };
      rerender(<RecipeDetailCardV2 recipe={cookingRecipe} />);

      // Quick Complete should not be visible during cooking
      expect(queryByText('Quick Complete')).toBeNull();
    });
  });

  describe('Quick Complete Modal Integration', () => {
    it('should open Quick Complete modal when button is pressed', async () => {
      const { getByText, getByTestId } = render(
        <RecipeDetailCardV2 recipe={mockRecipe} />
      );

      const quickCompleteButton = getByText('Quick Complete');
      fireEvent.press(quickCompleteButton);

      await waitFor(() => {
        expect(getByText('Quick Complete Recipe')).toBeTruthy();
      });
    });

    it('should pass correct props to Quick Complete modal', async () => {
      const { getByText, getByTestId } = render(
        <RecipeDetailCardV2 recipe={mockRecipe} />
      );

      fireEvent.press(getByText('Quick Complete'));

      await waitFor(() => {
        // Modal should be visible with correct recipe info
        expect(getByTestId('quick-complete-modal')).toBeTruthy();
        expect(getByTestId('quick-complete-modal').props.recipeId).toBe(123);
        expect(getByTestId('quick-complete-modal').props.userId).toBe(111);
      });
    });
  });

  describe('Quick Complete Success Flow', () => {
    beforeEach(() => {
      // Mock successful ingredient check
      const mockSummaryResponse = {
        data: {
          recipe_id: 123,
          available_ingredients: ['chicken', 'rice'],
          partial_ingredients: [],
          missing_ingredients: [],
          total_ingredients: 2,
          available_count: 2,
          partial_count: 0,
          missing_count: 0,
          availability_percentage: 100,
        },
        status: 200,
      };

      // Mock successful quick complete
      const mockCompleteResponse = {
        data: {
          success: true,
          message: 'Recipe completed successfully!',
          summary: {
            fully_consumed: [
              { ingredient: 'chicken', consumed_from: [] },
              { ingredient: 'rice', consumed_from: [] },
            ],
            partially_consumed: [],
            missing_ingredients: [],
          },
        },
        status: 200,
      };

      mockApiClient.post
        .mockResolvedValueOnce(mockSummaryResponse)
        .mockResolvedValueOnce(mockCompleteResponse);
    });

    it('should show success alert and navigate back after quick complete', async () => {
      const onBackMock = jest.fn();
      const { getByText } = render(
        <RecipeDetailCardV2 recipe={mockRecipe} onBack={onBackMock} />
      );

      // Open Quick Complete modal
      fireEvent.press(getByText('Quick Complete'));

      await waitFor(() => {
        expect(getByText('Complete Recipe')).toBeTruthy();
      });

      // Confirm quick complete
      fireEvent.press(getByText('Complete Recipe'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Recipe Completed!',
          'Recipe completed successfully!',
          expect.any(Array)
        );
      });

      // Simulate OK button press in success alert
      const alertCalls = (Alert.alert as jest.Mock).mock.calls;
      const successAlert = alertCalls.find(call => call[0] === 'Recipe Completed!');
      const okButton = successAlert[2][0];
      okButton.onPress();

      // Should navigate back
      expect(onBackMock).toHaveBeenCalled();
    });

    it('should use router.back() if no onBack prop provided', async () => {
      const { getByText } = render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Open Quick Complete modal
      fireEvent.press(getByText('Quick Complete'));

      await waitFor(() => {
        expect(getByText('Complete Recipe')).toBeTruthy();
      });

      // Confirm quick complete
      fireEvent.press(getByText('Complete Recipe'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalled();
      });

      // Simulate OK button press
      const alertCall = (Alert.alert as jest.Mock).mock.calls[0];
      const okButton = alertCall[2][0];
      okButton.onPress();

      // Should use router.back()
      expect(mockRouter.back).toHaveBeenCalled();
    });
  });

  describe('Quick Complete Button Styling', () => {
    it('should have correct styling and icon', () => {
      const { getByText, getByTestId } = render(
        <RecipeDetailCardV2 recipe={mockRecipe} />
      );

      const quickCompleteButton = getByText('Quick Complete').parent;
      
      // Check for flash icon
      const flashIcon = quickCompleteButton?.findByProps({ name: 'flash' });
      expect(flashIcon).toBeTruthy();
      expect(flashIcon.props.size).toBe(20);
      expect(flashIcon.props.color).toBe('#6366F1');

      // Check button styles
      expect(quickCompleteButton?.props.style).toMatchObject({
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#F3F4F6',
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle Quick Complete modal close without completion', async () => {
      const { getByText, queryByText } = render(
        <RecipeDetailCardV2 recipe={mockRecipe} />
      );

      // Open modal
      fireEvent.press(getByText('Quick Complete'));

      await waitFor(() => {
        expect(getByText('Cancel')).toBeTruthy();
      });

      // Close modal without completing
      fireEvent.press(getByText('Cancel'));

      await waitFor(() => {
        expect(queryByText('Quick Complete Recipe')).toBeNull();
      });

      // Should still be on the same screen
      expect(mockRouter.back).not.toHaveBeenCalled();
    });
  });

  describe('Integration with Cook Now Flow', () => {
    it('should allow switching between Cook Now and Quick Complete', () => {
      const { getByText } = render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Both buttons should be available
      const cookNowButton = getByText('Cook Now');
      const quickCompleteButton = getByText('Quick Complete');

      expect(cookNowButton).toBeTruthy();
      expect(quickCompleteButton).toBeTruthy();

      // Clicking Cook Now should navigate to cooking mode
      fireEvent.press(cookNowButton);
      expect(mockRouter.push).toHaveBeenCalledWith({
        pathname: '/cooking-mode',
        params: {
          recipeId: 123,
          recipeData: JSON.stringify(mockRecipe),
        },
      });

      // Quick Complete should open modal instead
      fireEvent.press(quickCompleteButton);
      expect(mockRouter.push).toHaveBeenCalledTimes(1); // Still only once from Cook Now
    });
  });
});
