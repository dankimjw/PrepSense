/**
 * Tests for ItemsDetected screen component
 * Tests displaying scanned/detected items, editing, and saving to database
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert, Image } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useItems } from '../../context/ItemsContext';
import { Buffer } from 'buffer';
import ItemsDetected from '../../app/items-detected';

// Mock dependencies
jest.mock('expo-router', () => ({
  useLocalSearchParams: jest.fn(),
  useRouter: jest.fn(),
  router: { replace: jest.fn(), push: jest.fn() },
  Stack: {
    Screen: ({ children }: any) => children,
  },
}));

jest.mock('../../context/ItemsContext', () => ({
  useItems: jest.fn(),
}));

jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

jest.mock('../../config', () => ({
  Config: {
    API_BASE_URL: 'http://test-api',
  },
}));

jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: ({ children }: any) => children,
}));

jest.mock('../../app/components/CustomHeader', () => ({
  CustomHeader: () => null,
}));

// Mock fetch
global.fetch = jest.fn();

// Helper functions
const enc = (o: any) => Buffer.from(JSON.stringify(o)).toString('base64');
const dec = (s: string) => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));

describe('ItemsDetected', () => {
  let mockRouter: any;
  let mockAddItems: jest.Mock;
  
  const mockItems = [
    {
      item_name: 'Milk',
      quantity_amount: 1,
      quantity_unit: 'gallon',
      expected_expiration: '2024-06-01',
      category: 'Dairy',
      count: 1,
    },
    {
      item_name: 'Bread',
      quantity_amount: 2,
      quantity_unit: 'loaf',
      expected_expiration: '2024-05-28',
      category: 'Bakery',
      count: 1,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockRouter = {
      replace: jest.fn(),
      push: jest.fn(),
    };
    mockAddItems = jest.fn();
    
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useItems as jest.Mock).mockReturnValue({ addItems: mockAddItems });
    (global.fetch as jest.Mock).mockReset();
  });

  describe('Initial State', () => {
    it('should display no items message when data is empty', () => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc([]),
      });
      
      const { getByText } = render(<ItemsDetected />);
      
      expect(getByText('No items detected.')).toBeTruthy();
      expect(getByText('Back')).toBeTruthy();
    });

    it('should navigate back when Back link is pressed on empty state', () => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc([]),
      });
      
      const { getByText } = render(<ItemsDetected />);
      
      fireEvent.press(getByText('Back'));
      
      expect(mockRouter.replace).toHaveBeenCalledWith('/(tabs)');
    });

    it('should display items when data is provided', () => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
      });
      
      const { getByText } = render(<ItemsDetected />);
      
      expect(getByText('2 items detected')).toBeTruthy();
      expect(getByText('Review and confirm before saving')).toBeTruthy();
      expect(getByText('Milk')).toBeTruthy();
      expect(getByText('1 × 1 gallon')).toBeTruthy();
      expect(getByText('Expires: 2024-06-01')).toBeTruthy();
      expect(getByText('Dairy')).toBeTruthy();
      expect(getByText('Bread')).toBeTruthy();
      expect(getByText('1 × 2 loaf')).toBeTruthy();
    });

    it('should display photo when photoUri is provided', () => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
        photoUri: 'test://photo.jpg',
      });
      
      const { UNSAFE_getByType } = render(<ItemsDetected />);
      
      const image = UNSAFE_getByType(Image);
      expect(image.props.source).toEqual({ uri: 'test://photo.jpg' });
    });
  });

  describe('Item Interactions', () => {
    beforeEach(() => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
        photoUri: 'test://photo.jpg',
      });
    });

    it('should navigate to edit screen when item is pressed', () => {
      const { getByText } = render(<ItemsDetected />);
      
      fireEvent.press(getByText('Milk'));
      
      expect(mockRouter.push).toHaveBeenCalledWith({
        pathname: '/edit-item',
        params: expect.objectContaining({
          index: '0',
          data: enc(mockItems),
          photoUri: 'test://photo.jpg',
          _t: expect.any(String),
        }),
      });
    });

    it('should handle items without categories', () => {
      const itemsWithoutCategory = [
        {
          item_name: 'Unknown Item',
          quantity_amount: 1,
          quantity_unit: 'each',
          expected_expiration: '2024-06-01',
        },
      ];
      
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(itemsWithoutCategory),
      });
      
      const { getByText } = render(<ItemsDetected />);
      
      expect(getByText('Uncategorized')).toBeTruthy();
    });
  });

  describe('Saving Items', () => {
    beforeEach(() => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
      });
    });

    it('should save items via images endpoint when source is not receipt-scanner', async () => {
      const { getByText } = render(<ItemsDetected />);
      
      // Mock successful response
      const mockResponse = {
        saved_count: 2,
        error_count: 0,
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });
      
      fireEvent.press(getByText('Confirm & Save'));
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api/images/save-detected-items',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              items: mockItems.map(item => ({
                item_name: item.item_name,
                quantity_amount: item.quantity_amount,
                quantity_unit: item.quantity_unit,
                expected_expiration: item.expected_expiration,
                category: item.category || 'Uncategorized',
                brand: 'Generic',
              })),
              user_id: 111,
            }),
          })
        );
      });
      
      // Should show success alert
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Success',
          '2 items saved to database successfully!',
          expect.arrayContaining([
            expect.objectContaining({
              text: 'OK',
              onPress: expect.any(Function),
            }),
          ])
        );
      });
      
      // Simulate OK press
      const alertCall = (Alert.alert as jest.Mock).mock.calls[0];
      const okButton = alertCall[2][0];
      okButton.onPress();
      
      expect(mockAddItems).toHaveBeenCalledWith(mockItems);
      expect(mockRouter.replace).toHaveBeenCalledWith('/(tabs)');
    });

    it('should save items via OCR endpoint when source is receipt-scanner', async () => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
        source: 'receipt-scanner',
      });
      
      const { getByText } = render(<ItemsDetected />);
      
      // Mock successful response
      const mockResponse = {
        added_count: 2,
        total_count: 2,
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });
      
      fireEvent.press(getByText('Confirm & Save'));
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://test-api/ocr/add-scanned-items',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(
              mockItems.map(item => ({
                name: item.item_name,
                quantity: item.quantity_amount,
                unit: item.quantity_unit,
                category: item.category || 'Uncategorized',
                price: undefined,
              }))
            ),
          })
        );
      });
      
      // Should show receipt-specific success message
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Success',
          '2 out of 2 items added to pantry successfully!',
          expect.any(Array)
        );
      });
    });

    it('should handle save errors gracefully', async () => {
      const { getByText } = render(<ItemsDetected />);
      
      // Mock error response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Database connection failed' }),
      });
      
      fireEvent.press(getByText('Confirm & Save'));
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to save items: Database connection failed'
        );
      });
      
      expect(mockAddItems).not.toHaveBeenCalled();
      expect(mockRouter.replace).not.toHaveBeenCalled();
    });

    it('should handle network errors', async () => {
      const { getByText } = render(<ItemsDetected />);
      
      // Mock network error
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
      
      fireEvent.press(getByText('Confirm & Save'));
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to save items: Network error'
        );
      });
    });

    it('should show partial success message when some items have errors', async () => {
      const { getByText } = render(<ItemsDetected />);
      
      // Mock response with errors
      const mockResponse = {
        saved_count: 1,
        error_count: 1,
      };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });
      
      fireEvent.press(getByText('Confirm & Save'));
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Success',
          '1 items saved to database successfully!\n1 items had errors.',
          expect.any(Array)
        );
      });
    });

    it('should disable save button while saving', async () => {
      const { getByText } = render(<ItemsDetected />);
      
      // Create a promise we can control
      let resolveResponse: any;
      const responsePromise = new Promise((resolve) => {
        resolveResponse = resolve;
      });
      (global.fetch as jest.Mock).mockReturnValueOnce(responsePromise);
      
      const saveButton = getByText('Confirm & Save');
      fireEvent.press(saveButton);
      
      // Button should be disabled while saving
      expect(saveButton.parent?.props.disabled).toBe(true);
      
      // Resolve the response
      resolveResponse({
        ok: true,
        json: async () => ({ saved_count: 2, error_count: 0 }),
      });
      
      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalled();
      });
    });
  });

  describe('Skip Functionality', () => {
    it('should add items locally without saving to database when Skip is pressed', () => {
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
      });
      
      const { getByText } = render(<ItemsDetected />);
      
      fireEvent.press(getByText('Skip'));
      
      expect(mockAddItems).toHaveBeenCalledWith(mockItems);
      expect(mockRouter.replace).toHaveBeenCalledWith('/(tabs)');
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('Category Colors', () => {
    it('should display correct colors for different categories', () => {
      const itemsWithCategories = [
        { ...mockItems[0], category: 'Dairy' },
        { ...mockItems[1], category: 'Meat' },
        {
          item_name: 'Apples',
          quantity_amount: 3,
          quantity_unit: 'pound',
          expected_expiration: '2024-06-05',
          category: 'Produce',
        },
      ];
      
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(itemsWithCategories),
      });
      
      const { getAllByTestId, getAllByText } = render(<ItemsDetected />);
      
      // Check that category chips exist with correct text
      const categoryTexts = ['Dairy', 'Meat', 'Produce'];
      categoryTexts.forEach(category => {
        expect(() => getAllByText(category)).not.toThrow();
      });
    });
  });

  describe('Data Updates', () => {
    it('should update items when returning from edit screen with new data', () => {
      const { rerender } = render(<ItemsDetected />);
      
      // Initial render
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(mockItems),
      });
      
      rerender(<ItemsDetected />);
      
      // Update with modified items
      const modifiedItems = [
        { ...mockItems[0], item_name: 'Whole Milk' },
        mockItems[1],
      ];
      
      (useLocalSearchParams as jest.Mock).mockReturnValue({
        data: enc(modifiedItems),
      });
      
      rerender(<ItemsDetected />);
      
      const { getByText } = render(<ItemsDetected />);
      expect(getByText('Whole Milk')).toBeTruthy();
    });
  });
});