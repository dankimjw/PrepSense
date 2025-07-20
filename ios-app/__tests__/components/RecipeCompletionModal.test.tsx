import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { RecipeCompletionModal } from '@/components/modals/RecipeCompletionModal';
import { Alert } from 'react-native';

// Mock Alert
jest.spyOn(Alert, 'alert');

// Mock parseIngredientsList
jest.mock('@/utils/ingredientParser', () => ({
  parseIngredientsList: jest.fn(() => [
    { name: 'milk', quantity: 2, unit: 'cups' },
    { name: 'flour', quantity: 3, unit: 'cups' },
    { name: 'eggs', quantity: 2, unit: 'units' }
  ])
}));

// Mock formatQuantity
jest.mock('@/utils/numberFormatting', () => ({
  formatQuantity: jest.fn((num) => num.toString())
}));

describe('RecipeCompletionModal', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();
  
  const mockRecipe = {
    name: 'Test Recipe',
    ingredients: ['2 cups milk', '3 cups flour', '2 eggs'],
    pantry_item_matches: {
      '2 cups milk': [
        { pantry_item_id: 1, product_name: 'Whole Milk', quantity: 4, unit: 'cups' }
      ],
      '3 cups flour': [
        { pantry_item_id: 2, product_name: 'All Purpose Flour', quantity: 5, unit: 'cups' }
      ]
    }
  };
  
  const mockPantryItems = [
    {
      id: '1',
      pantry_item_id: 1,
      item_name: 'Whole Milk',
      quantity_amount: 4,
      quantity_unit: 'cups',
      expiration_date: '2024-12-31'
    },
    {
      id: '2',
      pantry_item_id: 2,
      item_name: 'All Purpose Flour',
      quantity_amount: 5,
      quantity_unit: 'cups',
      expiration_date: '2025-06-30'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Modal Visibility', () => {
    it('should be visible when visible prop is true', () => {
      const { getByTestId } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
          testID="recipe-completion-modal"
        />
      );

      const modal = getByTestId('recipe-completion-modal');
      expect(modal).toHaveProp('visible', true);
    });

    it('should not be visible when visible prop is false', () => {
      const { getByTestId } = render(
        <RecipeCompletionModal
          visible={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
          testID="recipe-completion-modal"
        />
      );

      const modal = getByTestId('recipe-completion-modal');
      expect(modal).toHaveProp('visible', false);
    });

    it('should show modal content when visible', () => {
      const { getByText, queryByText } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
        />
      );

      expect(getByText('Complete Recipe')).toBeTruthy();
      expect(getByText('Test Recipe')).toBeTruthy();
    });

    it('should hide modal content when not visible', () => {
      const { queryByText } = render(
        <RecipeCompletionModal
          visible={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
        />
      );

      expect(queryByText('Complete Recipe')).toBeNull();
      expect(queryByText('Test Recipe')).toBeNull();
    });

    it('should call onClose when close button is pressed', () => {
      const { getByTestId } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
        />
      );

      // Find close button by looking for the close icon
      const closeButton = getByTestId('close-button');
      fireEvent.press(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should become visible when prop changes from false to true', () => {
      const { getByTestId, rerender } = render(
        <RecipeCompletionModal
          visible={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
          testID="recipe-completion-modal"
        />
      );

      expect(getByTestId('recipe-completion-modal')).toHaveProp('visible', false);

      rerender(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
          testID="recipe-completion-modal"
        />
      );

      expect(getByTestId('recipe-completion-modal')).toHaveProp('visible', true);
    });
  });

  describe('Modal Interactions', () => {
    it('should display loading state when loading prop is true', () => {
      const { getByTestId } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
          loading={true}
        />
      );

      // Confirm button should show loading indicator
      const confirmButton = getByTestId('confirm-button');
      expect(confirmButton).toHaveProperty('props.disabled', true);
    });

    it('should display ingredient statistics correctly', async () => {
      const { getByText } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
        />
      );

      // Wait for ingredient calculations to complete
      await waitFor(() => {
        expect(getByText('3')).toBeTruthy(); // Total ingredients
        expect(getByText('2')).toBeTruthy(); // Available ingredients
        expect(getByText('1')).toBeTruthy(); // Missing ingredients (eggs)
      });
    });

    it('should call onConfirm when Complete Recipe button is pressed', async () => {
      const { getByText } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={mockPantryItems}
        />
      );

      await waitFor(() => {
        const confirmButton = getByText('Complete Recipe');
        fireEvent.press(confirmButton);
      });

      expect(mockOnConfirm).toHaveBeenCalled();
    });

    it('should show alert when no ingredients are available', async () => {
      const emptyPantry = [];
      
      const { getByText } = render(
        <RecipeCompletionModal
          visible={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
          recipe={mockRecipe}
          pantryItems={emptyPantry}
        />
      );

      await waitFor(() => {
        const confirmButton = getByText('Complete Recipe');
        fireEvent.press(confirmButton);
      });

      expect(Alert.alert).toHaveBeenCalledWith(
        'No Ingredients Available',
        expect.any(String),
        expect.any(Array)
      );
    });
  });
});