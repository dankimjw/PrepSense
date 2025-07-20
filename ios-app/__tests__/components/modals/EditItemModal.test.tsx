import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import EditItemModal from '../../../components/modals/EditItemModal';
import { useItems } from '../../../context/ItemsContext';
import { apiClient } from '../../../services/apiClient';
import { useToast } from '../../../hooks/useToast';

// Mock dependencies
jest.mock('../../../context/ItemsContext');
jest.mock('../../../services/apiClient');
jest.mock('../../../hooks/useToast');
jest.mock('@react-native-community/datetimepicker', () => 'DateTimePicker');
jest.mock('@react-native-picker/picker', () => ({
  Picker: 'Picker',
}));

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('EditItemModal', () => {
  const mockOnClose = jest.fn();
  const mockOnUpdate = jest.fn();
  const mockUpdateItem = jest.fn();
  const mockShowToast = jest.fn();

  const mockItem = {
    id: '1',
    pantry_item_id: 1,
    item_name: 'Milk',
    quantity_amount: 2,
    quantity_unit: 'litres',
    expected_expiration: '2024-12-31',
    category: 'Dairy',
    product_id: 101,
    pantry_id: 1,
  };

  const defaultProps = {
    visible: true,
    item: mockItem,
    onClose: mockOnClose,
    onUpdate: mockOnUpdate,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useItems as jest.Mock).mockReturnValue({
      updateItem: mockUpdateItem,
    });
    (useToast as jest.Mock).mockReturnValue({
      showToast: mockShowToast,
    });
    mockUpdateItem.mockResolvedValue({ success: true });
  });

  describe('Modal Visibility and Initialization', () => {
    it('should render when visible is true', () => {
      const { getByText } = render(<EditItemModal {...defaultProps} />);
      expect(getByText('Edit Item')).toBeTruthy();
    });

    it('should not render when visible is false', () => {
      const { queryByText } = render(
        <EditItemModal {...defaultProps} visible={false} />
      );
      expect(queryByText('Edit Item')).toBeNull();
    });

    it('should initialize form with item data', () => {
      const { getByDisplayValue } = render(<EditItemModal {...defaultProps} />);
      
      expect(getByDisplayValue('Milk')).toBeTruthy();
      expect(getByDisplayValue('2')).toBeTruthy();
      expect(getByDisplayValue('litres')).toBeTruthy();
      expect(getByDisplayValue('Dairy')).toBeTruthy();
    });

    it('should handle null item gracefully', () => {
      const { queryByText } = render(
        <EditItemModal {...defaultProps} item={null} />
      );
      expect(queryByText('Edit Item')).toBeTruthy();
    });
  });

  describe('Form Field Updates', () => {
    it('should update item name', () => {
      const { getByDisplayValue } = render(<EditItemModal {...defaultProps} />);
      const nameInput = getByDisplayValue('Milk');

      fireEvent.changeText(nameInput, 'Whole Milk');
      expect(nameInput.props.value).toBe('Whole Milk');
    });

    it('should update quantity with validation', () => {
      const { getByDisplayValue } = render(<EditItemModal {...defaultProps} />);
      const quantityInput = getByDisplayValue('2');

      // Valid quantity
      fireEvent.changeText(quantityInput, '3.5');
      expect(quantityInput.props.value).toBe('3.5');

      // Invalid quantity (non-numeric)
      fireEvent.changeText(quantityInput, 'abc');
      expect(quantityInput.props.value).toBe('');
    });

    it('should handle quantity focus and blur', () => {
      const { getByDisplayValue } = render(<EditItemModal {...defaultProps} />);
      const quantityInput = getByDisplayValue('2');

      // Focus
      fireEvent(quantityInput, 'focus');
      expect(quantityInput.props.value).toBe('2');

      // Blur with empty value should reset to 1
      fireEvent.changeText(quantityInput, '');
      fireEvent(quantityInput, 'blur');
      expect(quantityInput.props.value).toBe('1');
    });
  });

  describe('Unit Selection', () => {
    it('should render UnitSelector component', () => {
      const { getByTestId } = render(<EditItemModal {...defaultProps} />);
      expect(getByTestId('unit-selector')).toBeTruthy();
    });

    it('should update unit when changed', () => {
      const { getByTestId } = render(<EditItemModal {...defaultProps} />);
      const unitSelector = getByTestId('unit-selector');

      fireEvent(unitSelector, 'onUnitChange', 'gallons');
      
      // The form should be updated with new unit
      expect(unitSelector.props.selectedUnit).toBe('gallons');
    });
  });

  describe('Category Selection', () => {
    it('should show category picker when category field is pressed', () => {
      const { getByDisplayValue, getByTestId } = render(
        <EditItemModal {...defaultProps} />
      );
      
      const categoryField = getByDisplayValue('Dairy').parent;
      fireEvent.press(categoryField);

      // Category picker should be visible
      expect(getByTestId('category-picker')).toBeTruthy();
    });

    it('should update category when selected from picker', () => {
      const { getByDisplayValue, getByTestId } = render(
        <EditItemModal {...defaultProps} />
      );
      
      // Open picker
      const categoryField = getByDisplayValue('Dairy').parent;
      fireEvent.press(categoryField);

      // Select new category
      const picker = getByTestId('category-picker');
      fireEvent(picker, 'onValueChange', 'Produce');

      expect(getByDisplayValue('Produce')).toBeTruthy();
    });

    it('should close category picker when done is pressed', () => {
      const { getByDisplayValue, getByText, queryByTestId } = render(
        <EditItemModal {...defaultProps} />
      );
      
      // Open picker
      const categoryField = getByDisplayValue('Dairy').parent;
      fireEvent.press(categoryField);

      // Press Done
      fireEvent.press(getByText('Done'));

      // Picker should be closed
      expect(queryByTestId('category-picker')).toBeNull();
    });
  });

  describe('Date Selection', () => {
    it('should show date picker when date field is pressed', () => {
      const { getByText, getByTestId } = render(<EditItemModal {...defaultProps} />);
      
      // Find and press the date field
      const dateField = getByText('12/31/2024').parent;
      fireEvent.press(dateField);

      // Date picker should be visible
      expect(getByTestId('date-picker')).toBeTruthy();
    });

    it('should update date when changed in picker', () => {
      const { getByText, getByTestId } = render(<EditItemModal {...defaultProps} />);
      
      // Open date picker
      const dateField = getByText('12/31/2024').parent;
      fireEvent.press(dateField);

      // Change date
      const datePicker = getByTestId('date-picker');
      const newDate = new Date('2025-01-15');
      fireEvent(datePicker, 'onChange', { 
        type: 'set', 
        nativeEvent: { timestamp: newDate.getTime() } 
      });

      // Date should be updated
      expect(getByText('1/15/2025')).toBeTruthy();
    });

    it('should close date picker when dismissed', () => {
      const { getByText, getByTestId, queryByTestId } = render(
        <EditItemModal {...defaultProps} />
      );
      
      // Open date picker
      const dateField = getByText('12/31/2024').parent;
      fireEvent.press(dateField);

      // Dismiss picker
      const datePicker = getByTestId('date-picker');
      fireEvent(datePicker, 'onChange', { type: 'dismissed' });

      // Picker should be closed
      expect(queryByTestId('date-picker')).toBeNull();
    });
  });

  describe('Save Functionality', () => {
    it('should validate required fields before saving', async () => {
      const { getByDisplayValue, getByText } = render(<EditItemModal {...defaultProps} />);
      
      // Clear item name
      fireEvent.changeText(getByDisplayValue('Milk'), '');
      
      // Try to save
      fireEvent.press(getByText('Save Changes'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Validation Error',
          'Item name is required'
        );
      });

      expect(mockUpdateItem).not.toHaveBeenCalled();
    });

    it('should validate quantity is greater than 0', async () => {
      const { getByDisplayValue, getByText } = render(<EditItemModal {...defaultProps} />);
      
      // Set quantity to 0
      fireEvent.changeText(getByDisplayValue('2'), '0');
      
      // Try to save
      fireEvent.press(getByText('Save Changes'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Validation Error',
          'Quantity must be greater than 0'
        );
      });
    });

    it('should save with valid data', async () => {
      const { getByDisplayValue, getByText } = render(<EditItemModal {...defaultProps} />);
      
      // Update fields
      fireEvent.changeText(getByDisplayValue('Milk'), 'Whole Milk');
      fireEvent.changeText(getByDisplayValue('2'), '3');
      
      // Save
      fireEvent.press(getByText('Save Changes'));

      await waitFor(() => {
        expect(mockUpdateItem).toHaveBeenCalledWith({
          pantry_item_id: 1,
          item_name: 'Whole Milk',
          quantity_amount: 3,
          quantity_unit: 'litres',
          expected_expiration: '2024-12-31',
          category: 'Dairy',
        });
      });

      expect(mockShowToast).toHaveBeenCalledWith({
        message: 'Item updated successfully',
        type: 'success',
      });
      expect(mockOnUpdate).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should show loading state while saving', async () => {
      const { getByText, getByTestId } = render(<EditItemModal {...defaultProps} />);
      
      // Mock slow save
      mockUpdateItem.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      // Save
      fireEvent.press(getByText('Save Changes'));

      // Should show loading indicator
      await waitFor(() => {
        expect(getByTestId('loading-indicator')).toBeTruthy();
      });
    });

    it('should handle save errors', async () => {
      const { getByText } = render(<EditItemModal {...defaultProps} />);
      
      // Mock save failure
      const error = new Error('Network error');
      (error as any).response = { data: { detail: 'Server error' } };
      mockUpdateItem.mockRejectedValue(error);

      // Save
      fireEvent.press(getByText('Save Changes'));

      await waitFor(() => {
        expect(mockShowToast).toHaveBeenCalledWith({
          message: 'Server error',
          type: 'error',
        });
      });

      expect(mockOnUpdate).not.toHaveBeenCalled();
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should handle API errors without detail', async () => {
      const { getByText } = render(<EditItemModal {...defaultProps} />);
      
      // Mock save failure without detail
      mockUpdateItem.mockRejectedValue(new Error('Network error'));

      // Save
      fireEvent.press(getByText('Save Changes'));

      await waitFor(() => {
        expect(mockShowToast).toHaveBeenCalledWith({
          message: 'Failed to update item',
          type: 'error',
        });
      });
    });
  });

  describe('Cancel Functionality', () => {
    it('should close modal when cancel is pressed', () => {
      const { getByText } = render(<EditItemModal {...defaultProps} />);
      
      fireEvent.press(getByText('Cancel'));
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should not save changes when cancelled', () => {
      const { getByDisplayValue, getByText } = render(<EditItemModal {...defaultProps} />);
      
      // Make changes
      fireEvent.changeText(getByDisplayValue('Milk'), 'Changed Milk');
      
      // Cancel
      fireEvent.press(getByText('Cancel'));
      
      expect(mockUpdateItem).not.toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Form Reset', () => {
    it('should reset form when item changes', () => {
      const { getByDisplayValue, rerender } = render(<EditItemModal {...defaultProps} />);
      
      // Initial item
      expect(getByDisplayValue('Milk')).toBeTruthy();
      
      // Change to new item
      const newItem = {
        ...mockItem,
        id: '2',
        item_name: 'Bread',
        quantity_amount: 1,
        quantity_unit: 'loaf',
        category: 'Bakery',
      };
      
      rerender(<EditItemModal {...defaultProps} item={newItem} />);
      
      // Should show new item data
      expect(getByDisplayValue('Bread')).toBeTruthy();
      expect(getByDisplayValue('1')).toBeTruthy();
      expect(getByDisplayValue('loaf')).toBeTruthy();
      expect(getByDisplayValue('Bakery')).toBeTruthy();
    });

    it('should reset form when modal closes and reopens', () => {
      const { getByDisplayValue, rerender } = render(<EditItemModal {...defaultProps} />);
      
      // Make changes
      fireEvent.changeText(getByDisplayValue('Milk'), 'Changed');
      
      // Close and reopen
      rerender(<EditItemModal {...defaultProps} visible={false} />);
      rerender(<EditItemModal {...defaultProps} visible={true} />);
      
      // Should reset to original values
      expect(getByDisplayValue('Milk')).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have proper accessibility labels', () => {
      const { getByLabelText } = render(<EditItemModal {...defaultProps} />);
      
      expect(getByLabelText('Item name')).toBeTruthy();
      expect(getByLabelText('Quantity')).toBeTruthy();
      expect(getByLabelText('Expiration date')).toBeTruthy();
      expect(getByLabelText('Category')).toBeTruthy();
    });
  });
});