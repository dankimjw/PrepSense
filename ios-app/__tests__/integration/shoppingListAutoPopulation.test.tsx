// shoppingListAutoPopulation.test.tsx
// Test suite for verifying shopping list auto-population with user confirmation flow

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import QuickCompleteModal from '../../components/modals/QuickCompleteModal';
import ShoppingListConfirmationModal from '../../components/modals/ShoppingListConfirmationModal';
import { apiClient } from '../../services/apiClient';
import { shoppingListService } from '../../services/shoppingListService';

// Mock the services
jest.mock('../../services/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }
}));

jest.mock('../../services/shoppingListService');

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
const mockShoppingListService = shoppingListService as jest.Mocked<typeof shoppingListService>;

describe('Shopping List Auto-Population with User Confirmation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Mock data
  const mockRecipe = {
    id: 1,
    title: 'Chocolate Cake',
    extendedIngredients: [
      { id: 1, name: 'flour', amount: 3, unit: 'cups', original: '3 cups flour' },
      { id: 2, name: 'eggs', amount: 4, unit: '', original: '4 large eggs' },
      { id: 3, name: 'cocoa powder', amount: 0.5, unit: 'cup', original: '1/2 cup cocoa powder' },
      { id: 4, name: 'sugar', amount: 2, unit: 'cups', original: '2 cups sugar' }
    ]
  };

  const mockPantryItems = [
    { id: 1, name: 'Flour', quantity: 1, unit: 'cup', category: 'Baking' },
    { id: 2, name: 'Eggs', quantity: 2, unit: 'units', category: 'Dairy' },
    // No cocoa powder in pantry
    { id: 3, name: 'Sugar', quantity: 3, unit: 'cups', category: 'Baking' }
  ];

  const mockMissingItems = [
    { 
      ingredient: 'flour', 
      needed: 3, 
      available: 1, 
      missing: 2, 
      unit: 'cups',
      category: 'Baking',
      original: '2 cups flour'
    },
    { 
      ingredient: 'eggs', 
      needed: 4, 
      available: 2, 
      missing: 2, 
      unit: 'large',
      category: 'Dairy',
      original: '2 large eggs'
    },
    { 
      ingredient: 'cocoa powder', 
      needed: 0.5, 
      available: 0, 
      missing: 0.5, 
      unit: 'cup',
      category: 'Baking',
      original: '1/2 cup cocoa powder'
    }
  ];

  describe('Confirmation Modal Flow', () => {
    it('should show confirmation modal after Quick Complete with missing items', async () => {
      // Mock Quick Complete response with missing items
      mockApiClient.post.mockResolvedValueOnce({
        data: {
          success: true,
          consumed_items: [
            { pantry_item_id: 1, quantity_consumed: 1 },
            { pantry_item_id: 2, quantity_consumed: 2 }
          ],
          missing_items: mockMissingItems
        }
      });

      const onClose = jest.fn();
      const onShoppingListUpdate = jest.fn();

      const { getByText, getByTestId, queryByText } = render(
        <NavigationContainer>
          <QuickCompleteModal
            visible={true}
            recipe={mockRecipe}
            onClose={onClose}
            onShoppingListUpdate={onShoppingListUpdate}
          />
        </NavigationContainer>
      );

      // Complete the recipe
      await act(async () => {
        fireEvent.press(getByTestId('complete-button'));
      });

      // Should show shopping list confirmation
      await waitFor(() => {
        expect(getByText('Add Missing Items to Shopping List?')).toBeTruthy();
        expect(getByText('2 cups flour')).toBeTruthy();
        expect(getByText('2 large eggs')).toBeTruthy();
        expect(getByText('1/2 cup cocoa powder')).toBeTruthy();
      });

      // Should NOT auto-add without confirmation
      expect(mockShoppingListService.addItems).not.toHaveBeenCalled();
    });

    it('should allow user to modify quantities before adding', async () => {
      const { getByText, getByTestId, getAllByTestId } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      // Find quantity inputs
      const quantityInputs = getAllByTestId(/quantity-input-/);
      expect(quantityInputs).toHaveLength(3);

      // Modify flour quantity (maybe user has some at home)
      fireEvent.changeText(quantityInputs[0], '1.5');

      // Verify the change
      await waitFor(() => {
        expect(quantityInputs[0].props.value).toBe('1.5');
      });

      // Confirm button should be enabled
      const confirmButton = getByTestId('confirm-all-button');
      expect(confirmButton).not.toBeDisabled();
    });

    it('should allow user to skip individual items', async () => {
      const onConfirm = jest.fn();
      
      const { getByText, getAllByTestId } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={onConfirm}
          onCancel={jest.fn()}
        />
      );

      // Skip eggs (maybe user will get from neighbor)
      const skipButtons = getAllByTestId(/skip-item-/);
      fireEvent.press(skipButtons[1]); // Skip eggs

      // Confirm remaining items
      fireEvent.press(getByText('Add Selected Items'));

      await waitFor(() => {
        expect(onConfirm).toHaveBeenCalledWith([
          expect.objectContaining({ ingredient: 'flour' }),
          expect.objectContaining({ ingredient: 'cocoa powder' })
          // eggs should be excluded
        ]);
      });
    });

    it('should categorize items properly in shopping list', async () => {
      mockShoppingListService.addItems.mockResolvedValueOnce({
        data: { success: true, added_items: mockMissingItems }
      });

      const onConfirm = jest.fn();
      
      const { getByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={onConfirm}
          onCancel={jest.fn()}
        />
      );

      // Check category display
      expect(getByText('Baking')).toBeTruthy(); // flour and cocoa powder
      expect(getByText('Dairy')).toBeTruthy(); // eggs

      // Confirm all
      fireEvent.press(getByText('Add All Items'));

      await waitFor(() => {
        expect(onConfirm).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({ category: 'Baking' }),
            expect.objectContaining({ category: 'Dairy' })
          ])
        );
      });
    });
  });

  describe('Smart Quantity Handling', () => {
    it('should handle unit conversions when adding to shopping list', async () => {
      const itemsWithConversions = [
        {
          ingredient: 'butter',
          needed: 250, // grams in recipe
          available: 0.5, // sticks in pantry
          missing: 125, // grams needed
          unit: 'g',
          displayUnit: 'sticks', // Common shopping unit
          displayQuantity: 1, // 1 stick ≈ 125g
          original: '1 stick butter'
        }
      ];

      const { getByText, getByTestId } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={itemsWithConversions}
          onConfirm={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      // Should show shopping-friendly units
      expect(getByText('1 stick butter')).toBeTruthy();
      
      // Tooltip shows conversion
      fireEvent.press(getByTestId('unit-info-butter'));
      await waitFor(() => {
        expect(getByText('(125g)')).toBeTruthy();
      });
    });

    it('should round quantities to shopping-friendly amounts', async () => {
      const itemsWithOddQuantities = [
        {
          ingredient: 'milk',
          needed: 473, // ml (2 cups)
          available: 100, // ml
          missing: 373, // ml
          unit: 'ml',
          shoppingUnit: 'pint',
          shoppingQuantity: 1, // Round up to 1 pint (473ml)
          original: '1 pint milk'
        }
      ];

      const { getByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={itemsWithOddQuantities}
          onConfirm={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      // Should round to common shopping sizes
      expect(getByText('1 pint milk')).toBeTruthy();
      expect(getByText('Rounded up from 373ml')).toBeTruthy();
    });

    it('should suggest alternative products when available', async () => {
      const itemsWithAlternatives = [
        {
          ingredient: 'heavy cream',
          missing: 1,
          unit: 'cup',
          alternatives: [
            { name: 'Half and Half', ratio: '1.5 cups' },
            { name: 'Whole Milk + Butter', ratio: '3/4 cup + 1/3 cup' }
          ],
          original: '1 cup heavy cream'
        }
      ];

      const { getByText, getByTestId } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={itemsWithAlternatives}
          onConfirm={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      // Show alternatives dropdown
      fireEvent.press(getByTestId('show-alternatives-heavy cream'));

      await waitFor(() => {
        expect(getByText('Or substitute with:')).toBeTruthy();
        expect(getByText('Half and Half (1.5 cups)')).toBeTruthy();
        expect(getByText('Whole Milk + Butter')).toBeTruthy();
      });

      // Select alternative
      fireEvent.press(getByText('Half and Half (1.5 cups)'));
      
      // Item should update
      expect(getByText('1.5 cups Half and Half')).toBeTruthy();
    });
  });

  describe('Batch Operations', () => {
    it('should support "Add All" and "Skip All" actions', async () => {
      const onConfirm = jest.fn();
      const onCancel = jest.fn();

      const { getByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={onConfirm}
          onCancel={onCancel}
        />
      );

      // Test Add All
      fireEvent.press(getByText('Add All Items'));
      
      await waitFor(() => {
        expect(onConfirm).toHaveBeenCalledWith(mockMissingItems);
      });

      // Reset
      onConfirm.mockClear();

      // Test Skip All
      fireEvent.press(getByText('Skip All'));
      
      await waitFor(() => {
        expect(onCancel).toHaveBeenCalled();
        expect(onConfirm).not.toHaveBeenCalled();
      });
    });

    it('should show item count and total summary', async () => {
      const { getByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      // Summary at top
      expect(getByText('3 items needed for Chocolate Cake')).toBeTruthy();
      
      // Category counts
      expect(getByText('Baking (2 items)')).toBeTruthy();
      expect(getByText('Dairy (1 item)')).toBeTruthy();
    });

    it('should update count when items are skipped', async () => {
      const { getByText, getAllByTestId } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={jest.fn()}
          onCancel={jest.fn()}
        />
      );

      // Initial count
      expect(getByText('3 items selected')).toBeTruthy();

      // Skip one item
      const skipButtons = getAllByTestId(/skip-item-/);
      fireEvent.press(skipButtons[0]);

      await waitFor(() => {
        expect(getByText('2 items selected')).toBeTruthy();
      });
    });
  });

  describe('Integration with Shopping List', () => {
    it('should prevent duplicate items in shopping list', async () => {
      // Mock existing shopping list
      mockShoppingListService.getShoppingList.mockResolvedValue([
        { id: 1, name: 'Flour', quantity: 1, unit: 'cup', category: 'Baking' }
      ]);

      const onConfirm = jest.fn();
      
      const { getByText, getByTestId } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={onConfirm}
          onCancel={jest.fn()}
        />
      );

      // Should show warning for existing item
      await waitFor(() => {
        const flourItem = getByTestId('item-flour');
        expect(flourItem).toHaveTextContent('Already in list: 1 cup');
        expect(flourItem).toHaveTextContent('Will add: 2 cups');
      });

      // Confirm should merge quantities
      fireEvent.press(getByText('Add Selected Items'));

      await waitFor(() => {
        expect(onConfirm).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({
              ingredient: 'flour',
              missing: 2,
              mergeWithExisting: true,
              existingId: 1
            })
          ])
        );
      });
    });

    it('should navigate to shopping list after confirmation', async () => {
      const navigation = { navigate: jest.fn() };
      const onShoppingListUpdate = jest.fn();

      mockShoppingListService.addItems.mockResolvedValueOnce({
        data: { success: true }
      });

      const { getByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={async (items) => {
            await mockShoppingListService.addItems(items);
            onShoppingListUpdate();
            navigation.navigate('ShoppingList');
          }}
          onCancel={jest.fn()}
        />
      );

      fireEvent.press(getByText('Add All Items'));

      await waitFor(() => {
        expect(mockShoppingListService.addItems).toHaveBeenCalled();
        expect(onShoppingListUpdate).toHaveBeenCalled();
        expect(navigation.navigate).toHaveBeenCalledWith('ShoppingList');
      });
    });
  });

  describe('Error Handling', () => {
    it('should show error if shopping list addition fails', async () => {
      mockShoppingListService.addItems.mockRejectedValueOnce(
        new Error('Network error')
      );

      const onConfirm = jest.fn(async (items) => {
        await mockShoppingListService.addItems(items);
      });

      const { getByText, queryByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={onConfirm}
          onCancel={jest.fn()}
        />
      );

      fireEvent.press(getByText('Add All Items'));

      await waitFor(() => {
        expect(getByText('Failed to add items to shopping list')).toBeTruthy();
        expect(getByText('Please try again')).toBeTruthy();
      });

      // Modal should stay open for retry
      expect(queryByText('Add Missing Items to Shopping List?')).toBeTruthy();
    });

    it('should handle partial success gracefully', async () => {
      mockShoppingListService.addItems.mockResolvedValueOnce({
        data: {
          success: false,
          added: ['flour', 'eggs'],
          failed: ['cocoa powder'],
          error: 'Some items could not be added'
        }
      });

      const onConfirm = jest.fn(async (items) => {
        return await mockShoppingListService.addItems(items);
      });

      const { getByText } = render(
        <ShoppingListConfirmationModal
          visible={true}
          missingItems={mockMissingItems}
          onConfirm={onConfirm}
          onCancel={jest.fn()}
        />
      );

      fireEvent.press(getByText('Add All Items'));

      await waitFor(() => {
        expect(getByText('Partially added to shopping list')).toBeTruthy();
        expect(getByText('Added: flour, eggs')).toBeTruthy();
        expect(getByText('Failed: cocoa powder')).toBeTruthy();
      });
    });
  });
});