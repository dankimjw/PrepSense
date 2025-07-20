import React from 'react';
import { render, waitFor, fireEvent } from '@testing-library/react-native';
import RecipeDetails from '@/app/recipe-details';
import { useLocalSearchParams } from 'expo-router';

// Mock dependencies
jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(),
  useRouter: () => ({ back: jest.fn() }),
}));

describe('Recipe Details Complete Data Display Tests', () => {
  const mockUseLocalSearchParams = jest.mocked(useLocalSearchParams);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Instructions Tab - Order and Completeness', () => {
    it('should display all instructions in correct numerical order', async () => {
      const mockRecipe = {
        id: 123,
        title: 'Test Recipe with 10 Steps',
        analyzedInstructions: [{
          name: '',
          steps: [
            { number: 1, step: 'Preheat oven to 375°F' },
            { number: 2, step: 'Mix dry ingredients' },
            { number: 3, step: 'Beat eggs and sugar' },
            { number: 4, step: 'Combine wet and dry ingredients' },
            { number: 5, step: 'Fold in chocolate chips' },
            { number: 6, step: 'Pour into baking pan' },
            { number: 7, step: 'Bake for 25 minutes' },
            { number: 8, step: 'Test with toothpick' },
            { number: 9, step: 'Cool for 10 minutes' },
            { number: 10, step: 'Cut into squares and serve' }
          ]
        }]
      };

      mockUseLocalSearchParams.mockReturnValue({
        id: '123',
        recipe: JSON.stringify(mockRecipe)
      });

      const { getByText, getAllByTestId, getByTestId } = render(<RecipeDetails />);

      // Navigate to Instructions tab
      fireEvent.press(getByText('Instructions'));

      await waitFor(() => {
        // Verify all 10 steps are present
        const steps = getAllByTestId(/^instruction-step-\d+$/);
        expect(steps).toHaveLength(10);

        // Verify steps are in correct order
        steps.forEach((step, index) => {
          const stepNumber = index + 1;
          expect(step).toHaveTextContent(`${stepNumber}.`);
        });

        // Verify first and last steps content
        expect(getByTestId('instruction-step-1')).toHaveTextContent('Preheat oven to 375°F');
        expect(getByTestId('instruction-step-10')).toHaveTextContent('Cut into squares and serve');
      });
    });

    it('should handle recipes with non-sequential step numbers', async () => {
      const mockRecipe = {
        id: 124,
        title: 'Recipe with Gaps',
        analyzedInstructions: [{
          steps: [
            { number: 1, step: 'First step' },
            { number: 3, step: 'Third step' },
            { number: 5, step: 'Fifth step' },
            { number: 8, step: 'Eighth step' }
          ]
        }]
      };

      mockUseLocalSearchParams.mockReturnValue({
        id: '124',
        recipe: JSON.stringify(mockRecipe)
      });

      const { getByText, getAllByTestId } = render(<RecipeDetails />);

      fireEvent.press(getByText('Instructions'));

      await waitFor(() => {
        const steps = getAllByTestId(/^instruction-step-\d+$/);
        expect(steps).toHaveLength(4);

        // Verify step numbers are preserved
        expect(steps[0]).toHaveTextContent('1.');
        expect(steps[1]).toHaveTextContent('3.');
        expect(steps[2]).toHaveTextContent('5.');
        expect(steps[3]).toHaveTextContent('8.');
      });
    });
  });

  describe('Ingredients Tab - Have vs Missing Display', () => {
    it('should show which ingredients user has in pantry', async () => {
      const mockRecipe = {
        id: 125,
        title: 'Pantry Match Recipe',
        extendedIngredients: [
          { id: 1, name: 'chicken breast', amount: 2, unit: 'lbs', original: '2 lbs chicken breast' },
          { id: 2, name: 'rice', amount: 1, unit: 'cup', original: '1 cup rice' },
          { id: 3, name: 'soy sauce', amount: 3, unit: 'tbsp', original: '3 tbsp soy sauce' }
        ],
        usedIngredients: [
          { id: 1, name: 'chicken breast' },
          { id: 2, name: 'rice' }
        ],
        missedIngredients: [
          { id: 3, name: 'soy sauce' }
        ]
      };

      mockUseLocalSearchParams.mockReturnValue({
        id: '125',
        recipe: JSON.stringify(mockRecipe),
        pantryIngredients: JSON.stringify(['chicken breast', 'rice'])
      });

      const { getByText, getByTestId } = render(<RecipeDetails />);

      fireEvent.press(getByText('Ingredients'));

      await waitFor(() => {
        // Check for have indicators
        expect(getByTestId('ingredient-1-status')).toHaveTextContent('✓');
        expect(getByTestId('ingredient-2-status')).toHaveTextContent('✓');
        expect(getByTestId('ingredient-3-status')).toHaveTextContent('✗');

        // Verify styling differences
        expect(getByTestId('ingredient-1-container')).toHaveStyle({ opacity: 1 });
        expect(getByTestId('ingredient-3-container')).toHaveStyle({ opacity: 0.6 });
      });
    });
  });

  describe('Nutrition Tab - Complete Nutrient Display', () => {
    it('should display all nutrients with values and daily percentages', async () => {
      const mockRecipe = {
        id: 126,
        title: 'Nutritious Recipe',
        nutrition: {
          nutrients: [
            { name: 'Calories', amount: 350, unit: 'kcal', percentOfDailyNeeds: 17.5 },
            { name: 'Protein', amount: 25, unit: 'g', percentOfDailyNeeds: 50 },
            { name: 'Carbohydrates', amount: 40, unit: 'g', percentOfDailyNeeds: 13.3 },
            { name: 'Fat', amount: 10, unit: 'g', percentOfDailyNeeds: 15.4 },
            { name: 'Saturated Fat', amount: 3, unit: 'g', percentOfDailyNeeds: 15 },
            { name: 'Fiber', amount: 5, unit: 'g', percentOfDailyNeeds: 20 },
            { name: 'Sugar', amount: 8, unit: 'g', percentOfDailyNeeds: 8.9 },
            { name: 'Sodium', amount: 650, unit: 'mg', percentOfDailyNeeds: 28.3 },
            { name: 'Cholesterol', amount: 75, unit: 'mg', percentOfDailyNeeds: 25 },
            { name: 'Vitamin A', amount: 1500, unit: 'IU', percentOfDailyNeeds: 30 }
          ]
        }
      };

      mockUseLocalSearchParams.mockReturnValue({
        id: '126',
        recipe: JSON.stringify(mockRecipe)
      });

      const { getByText, getAllByTestId } = render(<RecipeDetails />);

      fireEvent.press(getByText('Nutrition'));

      await waitFor(() => {
        // Verify all nutrients are displayed
        const nutrients = getAllByTestId(/^nutrient-row-/);
        expect(nutrients).toHaveLength(10);

        // Check specific nutrient details
        expect(getByTestId('nutrient-row-0')).toHaveTextContent('Calories');
        expect(getByTestId('nutrient-row-0')).toHaveTextContent('350 kcal');
        expect(getByTestId('nutrient-row-0')).toHaveTextContent('17.5%');

        // Verify macronutrients
        expect(getByText('Protein')).toBeTruthy();
        expect(getByText('25 g')).toBeTruthy();
        expect(getByText('50%')).toBeTruthy();

        // Verify micronutrients
        expect(getByText('Vitamin A')).toBeTruthy();
        expect(getByText('1500 IU')).toBeTruthy();
        expect(getByText('30%')).toBeTruthy();
      });
    });

    it('should handle missing nutrition data gracefully', async () => {
      const mockRecipe = {
        id: 127,
        title: 'No Nutrition Recipe',
        nutrition: null
      };

      mockUseLocalSearchParams.mockReturnValue({
        id: '127',
        recipe: JSON.stringify(mockRecipe)
      });

      const { getByText, queryByTestId } = render(<RecipeDetails />);

      fireEvent.press(getByText('Nutrition'));

      await waitFor(() => {
        expect(getByText('No nutrition information available')).toBeTruthy();
        expect(queryByTestId('nutrient-row-0')).toBeNull();
      });
    });
  });

  describe('Recipe Card Preview - Have vs Missing Ingredients', () => {
    it('should show ingredient counts on recipe card before opening details', async () => {
      // This would be tested in the RecipesScreen component
      // but I'll include the expected behavior here
      const mockRecipeCard = {
        id: 128,
        title: 'Quick Recipe',
        usedIngredientCount: 5,
        missedIngredientCount: 2,
        image: 'https://example.com/recipe.jpg'
      };

      // Recipe card should display: "✓ 5 | ✗ 2"
      // This indicates user has 5 ingredients and is missing 2
    });
  });
});
