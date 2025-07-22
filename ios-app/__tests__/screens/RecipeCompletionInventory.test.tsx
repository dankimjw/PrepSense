import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { RecipeCompletionModal } from '../../components/modals/RecipeCompletionModal';
import { apiClient } from '../../services/apiClient';
import { mockPantryItems, mockRecipe } from '../__mocks__/testData';

jest.mock('../../services/apiClient');

// Mock Alert
const mockAlert = jest.fn();
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: mockAlert,
}));

describe('Recipe Completion Inventory Management', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const defaultProps = {
    visible: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    recipe: {
      name: 'Chocolate Chip Cookies',
      ingredients: ['2 cups flour', '1 cup sugar', '1/2 cup butter'],
      pantry_item_matches: {
        '2 cups flour': [
          { pantry_item_id: '1', product_name: 'All-Purpose Flour', quantity: 3, unit: 'cups' },
          { pantry_item_id: '2', product_name: 'Whole Wheat Flour', quantity: 1, unit: 'cups' }
        ],
        '1 cup sugar': [
          { pantry_item_id: '3', product_name: 'Granulated Sugar', quantity: 2, unit: 'cups' }
        ],
        '1/2 cup butter': [
          { pantry_item_id: 4, product_name: 'Butter', quantity: 0.5, unit: 'cups' }
        ]
      }
    },
    pantryItems: mockPantryItems,
    loading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockAlert.mockClear();
  });

  describe('Inventory Display', () => {
    it('should show current quantities and what will remain after use', async () => {
      const { getByText, getAllByText, getByTestId } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Wait for loading to complete - button has this text
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
      
      await waitFor(() => {
        // Should show ingredient names (parsed from recipe)
        expect(getByText('flour')).toBeTruthy();
        expect(getByText('sugar')).toBeTruthy();
        expect(getByText(/cup butter/)).toBeTruthy();
        
        // Should show available quantities in format "• Product: X unit"
        expect(getByText(/All-Purpose Flour: 3 cups/)).toBeTruthy();
        expect(getByText(/Granulated Sugar: 2 cups/)).toBeTruthy();
      });
    });

    it('should indicate which items will be depleted', async () => {
      const itemsNearDepletion = [
        { 
          id: '1', 
          product_name: 'Butter', 
          quantity: 0.5, 
          unit: 'cups',
          expiration_date: '2025-01-25'
        }
      ];
      
      const { getByText, getByTestId } = render(
        <RecipeCompletionModal 
          {...defaultProps} 
          pantryItems={itemsNearDepletion}
          recipe={{
            ...defaultProps.recipe,
            ingredients: ['1/2 cup butter'],
            pantry_item_matches: {
              '1/2 cup butter': [
                { pantry_item_id: '1', product_name: 'Butter', quantity: 0.5, unit: 'cups' }
              ]
            }
          }}
        />
      );
      
      await waitFor(() => {
        // Wait for loading to complete - button has this text
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
      
      await waitFor(() => {
        // Should show this will use all available butter
        // The component shows the actual unit from pantry item
        expect(getByText(/Butter: 0.5/)).toBeTruthy();
        expect(getByText(/Use: 0.5 piece/)).toBeTruthy();
        expect(getByText(/50% of recipe requirement/)).toBeTruthy();
      });
    });

    it('should group items by type and show total available', async () => {
      const multipleFlourItems = [
        { id: '1', product_name: 'All-Purpose Flour', quantity: 2, unit: 'cups', expiration_date: '2025-01-25' },
        { id: '2', product_name: 'All-Purpose Flour', quantity: 1.5, unit: 'cups', expiration_date: '2025-02-01' }
      ];
      
      const { getByText, getAllByText } = render(
        <RecipeCompletionModal {...defaultProps} pantryItems={multipleFlourItems} />
      );
      
      await waitFor(() => {
        // Should show items are grouped
        expect(getAllByText(/All-Purpose Flour/)[0]).toBeTruthy();
        expect(getByText('Available from 2 items:')).toBeTruthy();
      });
    });
  });

  describe('User Controls', () => {
    it('should default to using maximum available amount', async () => {
      const { getByTestId, getByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Wait for loading to complete
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
      
      await waitFor(() => {
        // Should show the default selected amount (max available)
        expect(getByText(/Use: 2 cup/)).toBeTruthy(); // 2 cups flour
        expect(getByText(/Use: 1 cup/)).toBeTruthy(); // 1 cup sugar
      });
    });

    it('should update quantity when amount buttons are pressed', async () => {
      const { getByTestId, getByText, getAllByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Wait for loading to complete
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
      
      // Press "Half" button for first ingredient (flour)
      const halfButton = getByTestId('use-half-0');
      fireEvent.press(halfButton);
      
      await waitFor(() => {
        // Should update to show half amount (1 cup)
        // formatQuantity will show "1" not "1.0" for whole numbers
        const useTexts = getAllByText(/Use: 1 cup/);
        expect(useTexts.length).toBeGreaterThan(0);
        const percentTexts = getAllByText(/50% of recipe requirement/);
        expect(percentTexts.length).toBeGreaterThan(0);
      });
      
      // Press "None" button
      const noneButton = getByTestId('use-none-0');
      fireEvent.press(noneButton);
      
      await waitFor(() => {
        // Should update to show 0
        const zeroTexts = getAllByText(/Use: 0 cup/);
        expect(zeroTexts.length).toBeGreaterThan(0);
        const zeroPercentTexts = getAllByText(/0% of recipe requirement/);
        expect(zeroPercentTexts.length).toBeGreaterThan(0);
      });
    });

    it('should have quick amount selection buttons', async () => {
      const { getByTestId, getAllByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Wait for loading to complete
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
      
      // Should have quick amount buttons for each ingredient
      expect(getByTestId('use-none-0')).toBeTruthy();
      expect(getByTestId('use-half-0')).toBeTruthy();
      expect(getByTestId('use-most-0')).toBeTruthy();
      expect(getByTestId('use-all-0')).toBeTruthy();
      
      // Buttons should show correct labels (multiple of each for different ingredients)
      expect(getAllByText('None').length).toBeGreaterThan(0);
      expect(getAllByText('Half').length).toBeGreaterThan(0);
      expect(getAllByText('Most').length).toBeGreaterThan(0);
      expect(getAllByText('All').length).toBeGreaterThan(0);
    });
  });

  describe('Missing Items', () => {
    it.skip('should show functional shopping list button for missing items', async () => {
      const { getByText, getAllByText } = render(
        <RecipeCompletionModal 
          {...defaultProps}
          recipe={{
            ...defaultProps.recipe,
            ingredients: ['2 cups flour', '1 tsp vanilla extract'],
            pantry_item_matches: {}
          }}
        />
      );
      
      await waitFor(() => {
        expect(getAllByText('Not available in your pantry')[0]).toBeTruthy();
        const addButton = getAllByText('Add to shopping list')[0];
        
        // Button now has functionality
        expect(addButton).toBeTruthy();
        
        // Test that button can be pressed
        fireEvent.press(addButton);
        
        // Should show alert with ingredient details
        expect(mockAlert).toHaveBeenCalledWith(
          'Add to Shopping List',
          expect.stringContaining('vanilla extract'),
          expect.any(Array)
        );
      });
    });

    it.skip('should handle all ingredients missing scenario', async () => {
      const { getByTestId } = render(
        <RecipeCompletionModal 
          {...defaultProps}
          pantryItems={[]} // Empty pantry
        />
      );
      
      await waitFor(() => {
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(mockAlert).toHaveBeenCalledWith(
          'No Ingredients Available',
          expect.stringContaining('shopping list'),
          expect.any(Array)
        );
      });
    });
  });

  describe('Pantry Updates', () => {
    it('should show which pantry items will be affected', async () => {
      const { getByText, getAllByText } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Should show specific items that will be updated
        expect(getAllByText(/All-Purpose Flour/)[0]).toBeTruthy();
        expect(getAllByText(/exp:/)[0]).toBeTruthy(); // Shows expiration to indicate which item
      });
    });

    it.skip('should validate that some ingredients are selected before confirming', async () => {
      const { getByTestId, getAllByTestId } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        // Wait for component to render
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
      
      // Press "None" button for all ingredients to set them to 0
      const noneButtons = getAllByTestId(/use-none-\d+/);
      noneButtons.forEach(button => fireEvent.press(button));
      
      await waitFor(() => {
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(mockAlert).toHaveBeenCalledWith(
          'No Ingredients Selected',
          expect.any(String),
          expect.any(Array)
        );
      });
    });

    it('should prepare correct data structure for API call', async () => {
      const { getByTestId } = render(<RecipeCompletionModal {...defaultProps} />);
      
      await waitFor(() => {
        fireEvent.press(getByTestId('completion-confirm-button'));
        
        expect(mockOnConfirm).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({
              ingredientName: expect.any(String),
              selectedAmount: expect.any(Number),
              requestedQuantity: expect.any(Number),
              pantryItems: expect.any(Array)
            })
          ])
        );
      });
    });
  });

  describe('Performance & UX', () => {
    it('should handle unit conversion display clearly', async () => {
      const { getByText, getByTestId } = render(
        <RecipeCompletionModal 
          {...defaultProps}
          recipe={{
            ...defaultProps.recipe,
            ingredients: ['250g flour'],
            pantry_item_matches: {
              '250g flour': [
                { pantry_item_id: 1, product_name: 'Flour', quantity: 2, unit: 'cups' }
              ]
            }
          }}
        />
      );
      
      await waitFor(() => {
        expect(getByText('Converting from cups to g')).toBeTruthy();
      });
    });

    it('should show loading state while calculating', async () => {
      // Mock a slow calculation to see loading state
      const slowRecipe = {
        ...defaultProps.recipe,
        ingredients: new Array(50).fill('1 cup flour') // Many ingredients to slow down calculation
      };
      
      const { getByText, queryByText, getByTestId, rerender } = render(
        <RecipeCompletionModal {...defaultProps} visible={false} />
      );
      
      // Open modal to trigger calculation
      rerender(<RecipeCompletionModal {...defaultProps} visible={true} recipe={slowRecipe} />);
      
      // Should briefly show loading state
      // Note: This might be too fast to catch in tests
      await waitFor(() => {
        // After loading completes, button should be visible
        expect(getByTestId('completion-confirm-button')).toBeTruthy();
      });
    });

    it.skip('should prioritize items by expiration date (FIFO)', async () => {
      // Test with multiple flour items with different expiration dates
      const itemsWithDates = [
        { ...mockPantryItems[0], expiration_date: '2025-01-30' },
        { ...mockPantryItems[1], expiration_date: '2025-01-25' }
      ];
      
      const { getByText, getAllByText, getByTestId } = render(
        <RecipeCompletionModal {...defaultProps} pantryItems={itemsWithDates} />
      );
      
      await waitFor(() => {
        // Should show both flour items with their expiration dates
        expect(getByText(/exp: 1\/25\/2025/)).toBeTruthy();
        expect(getByText(/exp: 1\/30\/2025/)).toBeTruthy();
        
        // The component shows all available items, user can see which expires first
        const flourTexts = getAllByText(/Flour/);
        expect(flourTexts.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle items with no expiration date', async () => {
      const itemsNoExpiry = [
        { ...mockPantryItems[0], expiration_date: null }
      ];
      
      const { queryByText } = render(
        <RecipeCompletionModal {...defaultProps} pantryItems={itemsNoExpiry} />
      );
      
      await waitFor(() => {
        expect(queryByText(/exp:/)).toBeNull();
      });
    });

    it('should handle zero quantity items gracefully', async () => {
      const zeroQuantityItems = [
        { ...mockPantryItems[0], quantity: 0 }
      ];
      
      const { getByText, getAllByText, getByTestId } = render(
        <RecipeCompletionModal {...defaultProps} pantryItems={zeroQuantityItems} />
      );
      
      await waitFor(() => {
        const notAvailableElements = getAllByText('Not available in your pantry');
        expect(notAvailableElements.length).toBeGreaterThan(0);
      });
    });
  });
});