import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import RecipeCard from '@/components/RecipeCard';

describe('RecipeCard Component Tests', () => {
  const mockOnPress = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Have vs Missing Ingredients Display', () => {
    it('should display ingredient counts correctly on recipe card', () => {
      const recipe = {
        id: 1,
        title: 'Chicken Stir Fry',
        image: 'https://example.com/recipe.jpg',
        readyInMinutes: 30,
        servings: 4,
        usedIngredientCount: 5,
        missedIngredientCount: 2
      };

      const { getByText, getByTestId } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      // Verify recipe title
      expect(getByText('Chicken Stir Fry')).toBeTruthy();

      // Verify ingredient counts display
      expect(getByText('✓ 5 | ✗ 2')).toBeTruthy();

      // Verify the counts are styled correctly
      const ingredientCounts = getByTestId('ingredient-counts');
      expect(ingredientCounts).toBeTruthy();
    });

    it('should display zero counts correctly', () => {
      const recipe = {
        id: 2,
        title: 'Simple Salad',
        usedIngredientCount: 0,
        missedIngredientCount: 5
      };

      const { getByText } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      expect(getByText('✓ 0 | ✗ 5')).toBeTruthy();
    });

    it('should display when all ingredients are available', () => {
      const recipe = {
        id: 3,
        title: 'Perfect Match Recipe',
        usedIngredientCount: 8,
        missedIngredientCount: 0
      };

      const { getByText, getByTestId } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      expect(getByText('✓ 8 | ✗ 0')).toBeTruthy();

      // Could have special styling for perfect matches
      const card = getByTestId('recipe-card-3');
      expect(card).toHaveStyle({ borderColor: '#4CAF50' }); // Green border for perfect match
    });

    it('should handle missing ingredient count data', () => {
      const recipe = {
        id: 4,
        title: 'No Count Recipe',
        // Missing usedIngredientCount and missedIngredientCount
      };

      const { queryByText, getByText } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      // Should not crash and display title
      expect(getByText('No Count Recipe')).toBeTruthy();
      
      // Should not display counts if data is missing
      expect(queryByText(/✓.*✗/)).toBeNull();
    });
  });

  describe('Visual Indicators', () => {
    it('should show visual indicator for high match percentage', () => {
      const recipe = {
        id: 5,
        title: 'High Match Recipe',
        usedIngredientCount: 9,
        missedIngredientCount: 1,
        matchPercentage: 90
      };

      const { getByTestId } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      // Check for match percentage badge
      const matchBadge = getByTestId('match-percentage-badge');
      expect(matchBadge).toBeTruthy();
      expect(matchBadge).toHaveTextContent('90%');
      expect(matchBadge).toHaveStyle({ backgroundColor: '#4CAF50' }); // Green for high match
    });

    it('should show different color for low match percentage', () => {
      const recipe = {
        id: 6,
        title: 'Low Match Recipe',
        usedIngredientCount: 2,
        missedIngredientCount: 8,
        matchPercentage: 20
      };

      const { getByTestId } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      const matchBadge = getByTestId('match-percentage-badge');
      expect(matchBadge).toHaveStyle({ backgroundColor: '#FF9800' }); // Orange for low match
    });
  });

  describe('Recipe Metadata Display', () => {
    it('should display cooking time and servings', () => {
      const recipe = {
        id: 7,
        title: 'Quick Dinner',
        readyInMinutes: 25,
        servings: 4,
        usedIngredientCount: 5,
        missedIngredientCount: 1
      };

      const { getByText } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      expect(getByText('25 min')).toBeTruthy();
      expect(getByText('4 servings')).toBeTruthy();
    });

    it('should handle missing metadata gracefully', () => {
      const recipe = {
        id: 8,
        title: 'Minimal Recipe',
        usedIngredientCount: 3,
        missedIngredientCount: 2
      };

      const { queryByText } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      // Should not display missing data
      expect(queryByText(/min/)).toBeNull();
      expect(queryByText(/servings/)).toBeNull();
    });
  });

  describe('Interaction Tests', () => {
    it('should call onPress with recipe data when tapped', () => {
      const recipe = {
        id: 9,
        title: 'Tappable Recipe',
        usedIngredientCount: 4,
        missedIngredientCount: 2
      };

      const { getByTestId } = render(
        <RecipeCard recipe={recipe} onPress={mockOnPress} />
      );

      const card = getByTestId('recipe-card-9');
      fireEvent.press(card);

      expect(mockOnPress).toHaveBeenCalledTimes(1);
      expect(mockOnPress).toHaveBeenCalledWith(recipe);
    });
  });
});
