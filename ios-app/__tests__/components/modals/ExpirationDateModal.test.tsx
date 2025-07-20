import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import ExpirationDateModal from '../../../components/modals/ExpirationDateModal';
import { updatePantryItemExpiration } from '../../../services/api';

// Mock dependencies
jest.mock('../../../services/api');
jest.mock('@react-native-community/datetimepicker', () => 'DateTimePicker');

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('ExpirationDateModal', () => {
  const mockOnClose = jest.fn();
  const mockOnUpdate = jest.fn();

  const mockItem = {
    pantry_item_id: 1,
    product_name: 'Milk',
    expiration_date: '2024-12-31',
    quantity: 2,
    unit_of_measurement: 'litres',
  };

  const defaultProps = {
    visible: true,
    item: mockItem,
    onClose: mockOnClose,
    onUpdate: mockOnUpdate,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (updatePantryItemExpiration as jest.Mock).mockResolvedValue({ success: true });
  });

  describe('Modal Visibility', () => {
    it('should render when visible is true', () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      expect(getByText('Update Expiration Date')).toBeTruthy();
    });

    it('should not render when visible is false', () => {
      const { queryByText } = render(
        <ExpirationDateModal {...defaultProps} visible={false} />
      );
      expect(queryByText('Update Expiration Date')).toBeNull();
    });

    it('should return null when item is null', () => {
      const { container } = render(
        <ExpirationDateModal {...defaultProps} item={null} />
      );
      expect(container.children.length).toBe(0);
    });
  });

  describe('Item Information Display', () => {
    it('should display item name and quantity', () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      expect(getByText('Milk')).toBeTruthy();
      expect(getByText('2 litres')).toBeTruthy();
    });

    it('should display current expiration date', () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Date should be formatted
      expect(getByText(/12\/31\/2024/)).toBeTruthy();
    });

    it('should handle missing expiration date', () => {
      const itemWithoutDate = {
        ...mockItem,
        expiration_date: null,
      };
      
      const { getByText } = render(
        <ExpirationDateModal {...defaultProps} item={itemWithoutDate} />
      );
      
      // Should show today's date as default
      const today = new Date();
      const formattedDate = `${today.getMonth() + 1}/${today.getDate()}/${today.getFullYear()}`;
      expect(getByText(new RegExp(formattedDate))).toBeTruthy();
    });
  });

  describe('Date Picker Functionality', () => {
    it('should render date picker', () => {
      const { getByTestId } = render(<ExpirationDateModal {...defaultProps} />);
      expect(getByTestId('expiration-date-picker')).toBeTruthy();
    });

    it('should update selected date when picker changes', () => {
      const { getByTestId, getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      const datePicker = getByTestId('expiration-date-picker');
      const newDate = new Date('2025-01-15');
      
      fireEvent(datePicker, 'onChange', { 
        type: 'set', 
        nativeEvent: { timestamp: newDate.getTime() } 
      });

      // Should show new date
      expect(getByText(/1\/15\/2025/)).toBeTruthy();
    });

    it('should not update date when picker is dismissed', () => {
      const { getByTestId, getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      const datePicker = getByTestId('expiration-date-picker');
      
      fireEvent(datePicker, 'onChange', { 
        type: 'dismissed',
        nativeEvent: { timestamp: new Date().getTime() } 
      });

      // Should still show original date
      expect(getByText(/12\/31\/2024/)).toBeTruthy();
    });

    it('should have minimum date set to today', () => {
      const { getByTestId } = render(<ExpirationDateModal {...defaultProps} />);
      
      const datePicker = getByTestId('expiration-date-picker');
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      expect(datePicker.props.minimumDate.getTime()).toBe(today.getTime());
    });
  });

  describe('Update Functionality', () => {
    it('should call API and callbacks on successful update', async () => {
      const { getByTestId, getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Change date
      const datePicker = getByTestId('expiration-date-picker');
      const newDate = new Date('2025-01-15');
      fireEvent(datePicker, 'onChange', { 
        type: 'set', 
        nativeEvent: { timestamp: newDate.getTime() } 
      });

      // Press Update button
      fireEvent.press(getByText('Update'));

      await waitFor(() => {
        expect(updatePantryItemExpiration).toHaveBeenCalledWith(
          1, // pantry_item_id
          '2025-01-15' // formatted date
        );
      });

      expect(mockOnUpdate).toHaveBeenCalledWith({
        ...mockItem,
        expiration_date: '2025-01-15',
      });
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should show loading state while updating', async () => {
      const { getByText, getByTestId } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Mock slow API call
      (updatePantryItemExpiration as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      // Press Update
      fireEvent.press(getByText('Update'));

      // Should show loading indicator
      await waitFor(() => {
        expect(getByTestId('loading-indicator')).toBeTruthy();
      });
      
      // Button should be disabled
      const updateButton = getByText('Update').parent;
      expect(updateButton.props.disabled).toBe(true);
    });

    it('should handle API errors', async () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Mock API failure
      (updatePantryItemExpiration as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      // Press Update
      fireEvent.press(getByText('Update'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to update expiration date'
        );
      });

      expect(mockOnUpdate).not.toHaveBeenCalled();
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should not update if date unchanged', async () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Press Update without changing date
      fireEvent.press(getByText('Update'));

      // Should still call API (backend might have validation)
      await waitFor(() => {
        expect(updatePantryItemExpiration).toHaveBeenCalledWith(
          1,
          '2024-12-31'
        );
      });
    });
  });

  describe('Cancel Functionality', () => {
    it('should close modal when Cancel is pressed', () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      fireEvent.press(getByText('Cancel'));
      
      expect(mockOnClose).toHaveBeenCalled();
      expect(updatePantryItemExpiration).not.toHaveBeenCalled();
    });

    it('should reset date when cancelled', () => {
      const { getByTestId, getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Change date
      const datePicker = getByTestId('expiration-date-picker');
      const newDate = new Date('2025-01-15');
      fireEvent(datePicker, 'onChange', { 
        type: 'set', 
        nativeEvent: { timestamp: newDate.getTime() } 
      });

      // Cancel
      fireEvent.press(getByText('Cancel'));

      // Close and reopen modal
      const { rerender } = render(
        <ExpirationDateModal {...defaultProps} visible={false} />
      );
      rerender(<ExpirationDateModal {...defaultProps} visible={true} />);

      // Should show original date
      expect(getByText(/12\/31\/2024/)).toBeTruthy();
    });
  });

  describe('Date Formatting', () => {
    it('should format date correctly for display', () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Should show MM/DD/YYYY format
      expect(getByText('Current: 12/31/2024')).toBeTruthy();
    });

    it('should format date correctly for API', async () => {
      const { getByTestId, getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Set a specific date
      const datePicker = getByTestId('expiration-date-picker');
      const newDate = new Date('2025-03-05');
      fireEvent(datePicker, 'onChange', { 
        type: 'set', 
        nativeEvent: { timestamp: newDate.getTime() } 
      });

      // Update
      fireEvent.press(getByText('Update'));

      await waitFor(() => {
        expect(updatePantryItemExpiration).toHaveBeenCalledWith(
          1,
          '2025-03-05' // YYYY-MM-DD format
        );
      });
    });
  });

  describe('Visual States', () => {
    it('should show header with item icon', () => {
      const { getByText, getByTestId } = render(<ExpirationDateModal {...defaultProps} />);
      
      expect(getByText('Update Expiration Date')).toBeTruthy();
      expect(getByTestId('calendar-icon')).toBeTruthy();
    });

    it('should show item info section', () => {
      const { getByText, getByTestId } = render(<ExpirationDateModal {...defaultProps} />);
      
      expect(getByTestId('item-info-section')).toBeTruthy();
      expect(getByText('Item:')).toBeTruthy();
      expect(getByText('Quantity:')).toBeTruthy();
    });

    it('should show date section with proper styling', () => {
      const { getByTestId } = render(<ExpirationDateModal {...defaultProps} />);
      
      expect(getByTestId('date-section')).toBeTruthy();
      expect(getByTestId('date-picker-container')).toBeTruthy();
    });

    it('should disable Update button when loading', async () => {
      const { getByText } = render(<ExpirationDateModal {...defaultProps} />);
      
      // Mock slow API
      (updatePantryItemExpiration as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      const updateButton = getByText('Update').parent;
      
      // Initially enabled
      expect(updateButton.props.disabled).toBeFalsy();
      
      // Press update
      fireEvent.press(getByText('Update'));
      
      // Should be disabled while loading
      await waitFor(() => {
        expect(updateButton.props.disabled).toBe(true);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle item with very long name', () => {
      const longNameItem = {
        ...mockItem,
        product_name: 'Very Long Product Name That Should Be Truncated In The Display',
      };
      
      const { getByText } = render(
        <ExpirationDateModal {...defaultProps} item={longNameItem} />
      );
      
      // Should still render without breaking
      expect(getByText(longNameItem.product_name)).toBeTruthy();
    });

    it('should handle decimal quantities', () => {
      const decimalItem = {
        ...mockItem,
        quantity: 2.5,
      };
      
      const { getByText } = render(
        <ExpirationDateModal {...defaultProps} item={decimalItem} />
      );
      
      expect(getByText('2.5 litres')).toBeTruthy();
    });

    it('should handle missing unit of measurement', () => {
      const noUnitItem = {
        ...mockItem,
        unit_of_measurement: null,
      };
      
      const { getByText } = render(
        <ExpirationDateModal {...defaultProps} item={noUnitItem} />
      );
      
      // Should show quantity without unit
      expect(getByText('2')).toBeTruthy();
    });
  });
});