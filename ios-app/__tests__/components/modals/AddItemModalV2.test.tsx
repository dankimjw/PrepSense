import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import AddItemModalV2 from '../../../components/modals/AddItemModalV2';
import { savePantryItem } from '../../../services/api';

// Mock dependencies
jest.mock('../../../services/api');
jest.mock('@react-native-community/datetimepicker', () => 'DateTimePicker');

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('AddItemModalV2', () => {
  const mockOnClose = jest.fn();
  const mockOnItemAdded = jest.fn();
  const defaultUserId = 111;

  const defaultProps = {
    visible: true,
    onClose: mockOnClose,
    onItemAdded: mockOnItemAdded,
    userId: defaultUserId,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (savePantryItem as jest.Mock).mockResolvedValue({ success: true });
  });

  describe('Modal Visibility', () => {
    it('should render when visible is true', () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);
      expect(getByText('Add New Item')).toBeTruthy();
    });

    it('should not render when visible is false', () => {
      const { queryByText } = render(
        <AddItemModalV2 {...defaultProps} visible={false} />
      );
      expect(queryByText('Add New Item')).toBeNull();
    });
  });

  describe('Form Fields', () => {
    it('should render all required form fields', () => {
      const { getByPlaceholderText, getByText } = render(
        <AddItemModalV2 {...defaultProps} />
      );

      expect(getByPlaceholderText('Item name')).toBeTruthy();
      expect(getByPlaceholderText('1')).toBeTruthy(); // Quantity field
      expect(getByText('Select Category')).toBeTruthy();
      expect(getByText('Select Unit')).toBeTruthy();
    });

    it('should update item name when typed', () => {
      const { getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);
      const nameInput = getByPlaceholderText('Item name');

      fireEvent.changeText(nameInput, 'Milk');
      expect(nameInput.props.value).toBe('Milk');
    });

    it('should update quantity when typed', () => {
      const { getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);
      const quantityInput = getByPlaceholderText('1');

      fireEvent.changeText(quantityInput, '2.5');
      expect(quantityInput.props.value).toBe('2.5');
    });

    it('should only allow numeric input for quantity', () => {
      const { getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);
      const quantityInput = getByPlaceholderText('1');

      fireEvent.changeText(quantityInput, 'abc');
      expect(quantityInput.props.value).toBe('');

      fireEvent.changeText(quantityInput, '123');
      expect(quantityInput.props.value).toBe('123');
    });
  });

  describe('Category Selection', () => {
    it('should show category picker when Select Category is pressed', () => {
      const { getByText, queryByText } = render(<AddItemModalV2 {...defaultProps} />);
      
      // Initially categories should not be visible
      expect(queryByText('🥬 Produce')).toBeNull();

      // Press Select Category
      fireEvent.press(getByText('Select Category'));

      // Categories should now be visible
      expect(getByText('🥬 Produce')).toBeTruthy();
      expect(getByText('🥛 Dairy')).toBeTruthy();
      expect(getByText('🥩 Meat')).toBeTruthy();
    });

    it('should select a category and update units accordingly', () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);

      // Open category picker
      fireEvent.press(getByText('Select Category'));

      // Select Dairy category
      fireEvent.press(getByText('🥛 Dairy'));

      // Should now show selected category
      expect(getByText('🥛 Dairy')).toBeTruthy();

      // Open unit picker - should show dairy-specific units
      fireEvent.press(getByText('Select Unit'));
      expect(getByText('millilitres')).toBeTruthy();
      expect(getByText('litres')).toBeTruthy();
    });

    it('should change available units when category changes', () => {
      const { getByText, queryByText } = render(<AddItemModalV2 {...defaultProps} />);

      // Select Produce category first
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥬 Produce'));

      // Check produce units
      fireEvent.press(getByText('Select Unit'));
      expect(getByText('each')).toBeTruthy();
      expect(queryByText('litres')).toBeNull(); // No volume units for produce

      // Change to Beverages category
      fireEvent.press(getByText('🥬 Produce')); // Current selection
      fireEvent.press(getByText('🥤 Beverages'));

      // Check beverage units
      fireEvent.press(getByText('Select Unit'));
      expect(getByText('litres')).toBeTruthy();
      expect(getByText('millilitres')).toBeTruthy();
    });
  });

  describe('Unit Selection', () => {
    it('should show unit types based on selected category', async () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);

      // Select Dairy category (has volume, mass, count)
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));

      // Open unit picker
      fireEvent.press(getByText('Select Unit'));

      // Should show unit type tabs
      expect(getByText('Volume')).toBeTruthy();
      expect(getByText('Mass')).toBeTruthy();
      expect(getByText('Count')).toBeTruthy();
    });

    it('should switch between unit types', () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);

      // Select Dairy and open units
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      fireEvent.press(getByText('Select Unit'));

      // Initially on Volume tab
      expect(getByText('millilitres')).toBeTruthy();

      // Switch to Mass tab
      fireEvent.press(getByText('Mass'));
      expect(getByText('grams')).toBeTruthy();
      expect(getByText('kilograms')).toBeTruthy();

      // Switch to Count tab
      fireEvent.press(getByText('Count'));
      expect(getByText('each')).toBeTruthy();
      expect(getByText('dozen')).toBeTruthy();
    });

    it('should select a unit and close picker', () => {
      const { getByText, queryByText } = render(<AddItemModalV2 {...defaultProps} />);

      // Select category and open units
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      fireEvent.press(getByText('Select Unit'));

      // Select litres
      fireEvent.press(getByText('litres'));

      // Unit picker should close and show selected unit
      expect(queryByText('millilitres')).toBeNull(); // Picker closed
      expect(getByText('litres')).toBeTruthy(); // Selected unit shown
    });
  });

  describe('Date Selection', () => {
    it('should show current date by default', () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);
      
      const today = new Date();
      const dateString = today.toLocaleDateString();
      
      // Look for the date in the expiration date section
      expect(getByText(new RegExp(dateString))).toBeTruthy();
    });

    it('should show date picker when date is pressed', () => {
      const { getByText, getByTestId } = render(<AddItemModalV2 {...defaultProps} />);
      
      const dateButton = getByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      fireEvent.press(dateButton);

      // DateTimePicker should be rendered
      expect(getByTestId('dateTimePicker')).toBeTruthy();
    });

    it('should update date when changed in picker', () => {
      const { getByText, getByTestId } = render(<AddItemModalV2 {...defaultProps} />);
      
      // Open date picker
      const dateButton = getByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      fireEvent.press(dateButton);

      // Simulate date change
      const datePicker = getByTestId('dateTimePicker');
      const newDate = new Date('2024-12-31');
      fireEvent(datePicker, 'onChange', { type: 'set', nativeEvent: { timestamp: newDate.getTime() } });

      // Check if date was updated
      expect(getByText('12/31/2024')).toBeTruthy();
    });
  });

  describe('Form Validation', () => {
    it('should show alert when trying to save without item name', async () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);

      // Try to save without entering name
      fireEvent.press(getByText('Add Item'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Missing Information',
          'Please enter an item name'
        );
      });
    });

    it('should show alert when trying to save without category', async () => {
      const { getByText, getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);

      // Enter name but no category
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Milk');
      fireEvent.press(getByText('Add Item'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Missing Information',
          'Please select a category'
        );
      });
    });

    it('should show alert when trying to save without unit', async () => {
      const { getByText, getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);

      // Enter name and category but no unit
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Milk');
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      fireEvent.press(getByText('Add Item'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Missing Information',
          'Please select a unit'
        );
      });
    });

    it('should validate quantity is greater than 0', async () => {
      const { getByText, getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);

      // Fill all fields but with 0 quantity
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Milk');
      fireEvent.changeText(getByPlaceholderText('1'), '0');
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      fireEvent.press(getByText('Select Unit'));
      fireEvent.press(getByText('litres'));

      fireEvent.press(getByText('Add Item'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Invalid Quantity',
          'Please enter a quantity greater than 0'
        );
      });
    });
  });

  describe('Save Functionality', () => {
    it('should save item with all valid data', async () => {
      const { getByText, getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);

      // Fill all fields
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Whole Milk');
      fireEvent.changeText(getByPlaceholderText('1'), '2');
      
      // Select category
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      
      // Select unit
      fireEvent.press(getByText('Select Unit'));
      fireEvent.press(getByText('litres'));

      // Save
      fireEvent.press(getByText('Add Item'));

      await waitFor(() => {
        expect(savePantryItem).toHaveBeenCalledWith(
          defaultUserId,
          expect.objectContaining({
            product_name: 'Whole Milk',
            quantity: 2,
            unit_of_measurement: 'litres',
            category: 'Dairy',
            expiration_date: expect.any(String),
          })
        );
      });

      expect(mockOnItemAdded).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should show loading state while saving', async () => {
      const { getByText, getByPlaceholderText, getByTestId } = render(
        <AddItemModalV2 {...defaultProps} />
      );

      // Mock slow save
      (savePantryItem as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      // Fill required fields
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Milk');
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      fireEvent.press(getByText('Select Unit'));
      fireEvent.press(getByText('litres'));

      // Save
      fireEvent.press(getByText('Add Item'));

      // Should show loading indicator
      await waitFor(() => {
        expect(getByTestId('loadingIndicator')).toBeTruthy();
      });
    });

    it('should handle save errors', async () => {
      const { getByText, getByPlaceholderText } = render(<AddItemModalV2 {...defaultProps} />);

      // Mock save failure
      (savePantryItem as jest.Mock).mockRejectedValue(new Error('Network error'));

      // Fill required fields
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Milk');
      fireEvent.press(getByText('Select Category'));
      fireEvent.press(getByText('🥛 Dairy'));
      fireEvent.press(getByText('Select Unit'));
      fireEvent.press(getByText('litres'));

      // Save
      fireEvent.press(getByText('Add Item'));

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to add item. Please try again.'
        );
      });

      expect(mockOnItemAdded).not.toHaveBeenCalled();
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Cancel Functionality', () => {
    it('should close modal when cancel is pressed', () => {
      const { getByText } = render(<AddItemModalV2 {...defaultProps} />);

      fireEvent.press(getByText('Cancel'));
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should reset form when modal is closed and reopened', () => {
      const { getByText, getByPlaceholderText, rerender } = render(
        <AddItemModalV2 {...defaultProps} />
      );

      // Fill some fields
      fireEvent.changeText(getByPlaceholderText('Item name'), 'Test Item');
      fireEvent.changeText(getByPlaceholderText('1'), '5');

      // Close modal
      fireEvent.press(getByText('Cancel'));

      // Reopen modal
      rerender(<AddItemModalV2 {...defaultProps} visible={false} />);
      rerender(<AddItemModalV2 {...defaultProps} visible={true} />);

      // Fields should be reset
      const nameInput = getByPlaceholderText('Item name');
      const quantityInput = getByPlaceholderText('1');
      
      expect(nameInput.props.value).toBe('');
      expect(quantityInput.props.value).toBe('1');
    });
  });

  describe('Keyboard Handling', () => {
    it('should use KeyboardAvoidingView for proper keyboard handling', () => {
      const { UNSAFE_getByType } = render(<AddItemModalV2 {...defaultProps} />);
      
      const keyboardAvoidingView = UNSAFE_getByType(
        require('react-native').KeyboardAvoidingView
      );
      
      expect(keyboardAvoidingView).toBeTruthy();
      expect(keyboardAvoidingView.props.behavior).toBe(
        Platform.OS === 'ios' ? 'padding' : 'height'
      );
    });
  });
});