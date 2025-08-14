import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { RecipeCompletionModal } from '../../components/modals/RecipeCompletionModal';
import { apiClient } from '../../services/apiClient';
import { mockPantryItems, mockRecipe } from '../__mocks__/testData';

// Mock dependencies
jest.mock('../../services/apiClient');
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

describe('Cooking Mode Completion Screen', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const defaultProps = {
    visible: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    recipe: mockRecipe,
    pantryItems: mockPantryItems,
    loading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Modal Display', () => {
    it('should display recipe name and ingredient statistics', () => {
      const { getByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      expect(getByText(mockRecipe.name)).toBeTruthy();
      expect(getByText('Total')).toBeTruthy();
      expect(getByText('Available')).toBeTruthy();
      expect(getByText('Missing')).toBeTruthy();
    });

    it('should show loading state while calculating ingredients', async () => {
      const { getByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        expect(getByText(/Calculating ingredient usage/)).toBeTruthy();
      });
    });
  });

  describe('Ingredient Matching', () => {
    it('should match pantry items to recipe ingredients', async () => {
      const { getAllByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Should show matched ingredients
        expect(getAllByText(/Available from/)[0]).toBeTruthy();
      });
    });

    it('should prioritize items expiring soon', async () => {
      const itemsWithExpiration = [
        { ...mockPantryItems[0], expiration_date: '2025-01-25' },
        { ...mockPantryItems[1], expiration_date: '2025-02-01' },
      ];
      
      const { getByText } = render(
        <RecipeCompletionModal {...defaultProps} pantryItems={itemsWithExpiration} />
      );
      
      await waitFor(() => {
        // Earlier expiration should appear first
        expect(getByText(/exp: 1\/25\/2025/)).toBeTruthy();
      });
    });

    it('should handle unit conversions', async () => {
      const { getByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Should show conversion notes when units differ
        expect(getByText(/Converting from/)).toBeTruthy();
      });
    });
  });

  describe('Slider Interactions', () => {
    it('should allow adjusting ingredient usage amounts', async () => {
      const { getAllByRole } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        const sliders = getAllByRole('slider');
        expect(sliders.length).toBeGreaterThan(0);
        
        // Simulate slider value change
        fireEvent.valueChange(sliders[0], 0.5);
      });
    });

    it('should show shortage warning when using less than required', async () => {
      const { getByText, getAllByRole } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        const sliders = getAllByRole('slider');
        fireEvent.valueChange(sliders[0], 0);
        
        expect(getByText(/Short by/)).toBeTruthy();
      });
    });
  });

  describe('Completion Actions', () => {
    it('should validate at least one ingredient is selected', async () => {
      const { getByTestId } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(Alert.alert).toHaveBeenCalledWith(
          'No Ingredients Selected',
          expect.any(String),
          expect.any(Array)
        );
      });
    });

    it('should call onConfirm with selected ingredients', async () => {
      const { getByTestId, getAllByRole } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        const sliders = getAllByRole('slider');
        fireEvent.valueChange(sliders[0], 2);
        
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(mockOnConfirm).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({
              selectedAmount: expect.any(Number),
              ingredientName: expect.any(String),
            })
          ])
        );
      });
    });

    it('should handle API errors gracefully', async () => {
      const error = new Error('Network error');
      (apiClient.post as jest.Mock).mockRejectedValueOnce(error);
      
      const { getByTestId } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          expect.stringContaining('Failed'),
          expect.any(Array)
        );
      });
    });
  });

  describe('Missing Ingredients', () => {
    it('should show add to shopping list option for missing items', async () => {
      const recipeWithMissingItems = {
        ...mockRecipe,
        ingredients: ['2 cups unicorn tears', '1 dragon scale'],
      };
      
      const { getAllByText } = render(
        <RecipeCompletionModal {...defaultProps} recipe={recipeWithMissingItems} />
      );
      
      await waitFor(() => {
        expect(getAllByText('Add to shopping list')[0]).toBeTruthy();
        expect(getAllByText('Not available in your pantry')[0]).toBeTruthy();
      });
    });

    it('should prompt to add all to shopping list when nothing available', async () => {
      const { getByTestId } = render(
        <RecipeCompletionModal {...defaultProps} pantryItems={[]} />
      );
      
      await waitFor(() => {
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(Alert.alert).toHaveBeenCalledWith(
          'No Ingredients Available',
          expect.stringContaining('shopping list'),
          expect.arrayContaining([
            expect.objectContaining({ text: 'Add to Shopping List' })
          ])
        );
      });
    });
  });

  describe('Performance', () => {
    it('should render large ingredient lists efficiently', async () => {
      const manyIngredients = Array(50).fill(null).map((_, i) => `Ingredient ${i}`);
      const largeRecipe = { ...mockRecipe, ingredients: manyIngredients };
      
      const startTime = Date.now();
      const { getByText } = render(
        <RecipeCompletionModal {...defaultProps} recipe={largeRecipe} />
      );
      const renderTime = Date.now() - startTime;
      
      expect(renderTime).toBeLessThan(1000); // Should render in under 1 second
      
      await waitFor(() => {
        expect(getByText('Complete Recipe')).toBeTruthy();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', async () => {
      const { getByTestId, getByLabelText } = render(
        <RecipeCompletionModal {...defaultProps} />
      );
      
      expect(getByTestId('recipe-completion-modal')).toBeTruthy();
      expect(getByTestId('close-button')).toBeTruthy();
      expect(getByTestId('completion-confirm-button')).toBeTruthy();
    });
  });
});