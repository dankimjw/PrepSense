import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { QuickCompleteModal } from '../components/modals/QuickCompleteModal';
import { apiClient } from '../services/apiClient';

// Mock dependencies
jest.mock('../services/apiClient');
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('QuickCompleteModal', () => {
  const defaultProps = {
    visible: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    recipeId: 123,
    userId: 111,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render modal when visible is true', () => {
      const { getByText } = render(<QuickCompleteModal {...defaultProps} />);
      
      expect(getByText('Quick Complete Recipe')).toBeTruthy();
      expect(getByText('Cancel')).toBeTruthy();
      expect(getByText('Complete Recipe')).toBeTruthy();
    });

    it('should not render modal when visible is false', () => {
      const { queryByText } = render(
        <QuickCompleteModal {...defaultProps} visible={false} />
      );
      
      expect(queryByText('Quick Complete Recipe')).toBeNull();
    });
  });

  describe('Ingredient Summary Loading', () => {
    it('should show loading state initially', () => {
      mockApiClient.post.mockImplementation(() => new Promise(() => {})); // Never resolves
      
      const { getByTestId } = render(<QuickCompleteModal {...defaultProps} />);
      
      expect(getByTestId('loading-indicator')).toBeTruthy();
    });

    it('should fetch and display ingredient summary on mount', async () => {
      const mockSummaryResponse = {
        data: {
          recipe_id: 123,
          available_ingredients: ['Chicken', 'Rice'],
          partial_ingredients: ['Olive Oil'],
          missing_ingredients: ['Garlic'],
          total_ingredients: 4,
          available_count: 2,
          partial_count: 1,
          missing_count: 1,
          availability_percentage: 75,
        },
        status: 200,
      };

      mockApiClient.post.mockResolvedValueOnce(mockSummaryResponse);

      const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

      await waitFor(() => {
        expect(getByText('Available (2)')).toBeTruthy();
        expect(getByText('Partial (1)')).toBeTruthy();
        expect(getByText('Missing (1)')).toBeTruthy();
      });

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/recipe-consumption/check-ingredients',
        {
          recipe_id: 123,
          user_id: 111,
          servings: 1,
        }
      );
    });

    it('should handle API errors gracefully', async () => {
      mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));
      
      const alertSpy = jest.spyOn(Alert, 'alert');
      
      render(<QuickCompleteModal {...defaultProps} />);

      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith(
          'Error',
          'Failed to check ingredients availability'
        );
      });
    });
  });

  describe('Quick Complete Functionality', () => {
    beforeEach(async () => {
      // Setup successful summary fetch
      const mockSummaryResponse = {
        data: {
          recipe_id: 123,
          available_ingredients: ['Chicken', 'Rice'],
          partial_ingredients: [],
          missing_ingredients: [],
          total_ingredients: 2,
          available_count: 2,
          partial_count: 0,
          missing_count: 0,
          availability_percentage: 100,
        },
        status: 200,
      };

      mockApiClient.post.mockResolvedValueOnce(mockSummaryResponse);
    });

    it('should handle successful quick complete', async () => {
      const mockCompleteResponse = {
        data: {
          success: true,
          message: 'Recipe completed successfully!',
          summary: {
            fully_consumed: [
              {
                ingredient: 'Chicken',
                consumed_from: [
                  {
                    pantry_item_name: 'Chicken Breast',
                    quantity_consumed: 2,
                    unit: 'pieces',
                  },
                ],
              },
            ],
            partially_consumed: [],
            missing_ingredients: [],
          },
        },
        status: 200,
      };

      const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

      // Wait for summary to load
      await waitFor(() => {
        expect(getByText('Available (2)')).toBeTruthy();
      });

      // Mock the complete response
      mockApiClient.post.mockResolvedValueOnce(mockCompleteResponse);

      // Click Complete Recipe button
      const completeButton = getByText('Complete Recipe');
      fireEvent.press(completeButton);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Recipe Completed!',
          'Recipe completed successfully!',
          expect.any(Array)
        );
      });

      // Simulate OK button press in alert
      const alertCall = (Alert.alert as jest.Mock).mock.calls[0];
      const okButton = alertCall[2][0];
      okButton.onPress();

      expect(defaultProps.onConfirm).toHaveBeenCalled();
      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('should handle quick complete API error', async () => {
      const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

      // Wait for summary to load
      await waitFor(() => {
        expect(getByText('Complete Recipe')).toBeTruthy();
      });

      // Mock error response
      mockApiClient.post.mockRejectedValueOnce(new Error('Server error'));

      // Click Complete Recipe button
      const completeButton = getByText('Complete Recipe');
      fireEvent.press(completeButton);

      await waitFor(() => {
        expect(Alert.alert).toHaveBeenCalledWith(
          'Error',
          'Failed to complete recipe. Please try again.'
        );
      });

      expect(defaultProps.onConfirm).not.toHaveBeenCalled();
    });

    it('should disable complete button when confirming', async () => {
      const { getByText, getByTestId } = render(<QuickCompleteModal {...defaultProps} />);

      // Wait for summary to load
      await waitFor(() => {
        expect(getByText('Complete Recipe')).toBeTruthy();
      });

      // Mock a slow response
      mockApiClient.post.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      // Click Complete Recipe button
      const completeButton = getByText('Complete Recipe');
      fireEvent.press(completeButton);

      // Button should be disabled
      expect(completeButton.props.disabled).toBe(true);
      expect(getByTestId('confirming-indicator')).toBeTruthy();
    });
  });

  describe('User Interactions', () => {
    it('should call onClose when Cancel button is pressed', async () => {
      const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

      const cancelButton = getByText('Cancel');
      fireEvent.press(cancelButton);

      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it('should call onClose when modal backdrop is pressed', () => {
      const { getByTestId } = render(<QuickCompleteModal {...defaultProps} />);

      const backdrop = getByTestId('modal-backdrop');
      fireEvent.press(backdrop);

      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe('Ingredient Display', () => {
    it('should display ingredients in correct categories', async () => {
      const mockSummaryResponse = {
        data: {
          recipe_id: 123,
          available_ingredients: ['Chicken', 'Rice', 'Salt'],
          partial_ingredients: ['Olive Oil'],
          missing_ingredients: ['Garlic', 'Basil'],
          total_ingredients: 6,
          available_count: 3,
          partial_count: 1,
          missing_count: 2,
          availability_percentage: 66.7,
        },
        status: 200,
      };

      mockApiClient.post.mockResolvedValueOnce(mockSummaryResponse);

      const { getByText, getAllByText } = render(<QuickCompleteModal {...defaultProps} />);

      await waitFor(() => {
        // Check section headers
        expect(getByText('Available (3)')).toBeTruthy();
        expect(getByText('Partial (1)')).toBeTruthy();
        expect(getByText('Missing (2)')).toBeTruthy();

        // Check ingredients are displayed
        expect(getByText('✓ Chicken')).toBeTruthy();
        expect(getByText('✓ Rice')).toBeTruthy();
        expect(getByText('✓ Salt')).toBeTruthy();
        expect(getByText('◐ Olive Oil')).toBeTruthy();
        expect(getByText('✗ Garlic')).toBeTruthy();
        expect(getByText('✗ Basil')).toBeTruthy();
      });
    });

    it('should show empty state when no ingredients', async () => {
      const mockSummaryResponse = {
        data: {
          recipe_id: 123,
          available_ingredients: [],
          partial_ingredients: [],
          missing_ingredients: [],
          total_ingredients: 0,
          available_count: 0,
          partial_count: 0,
          missing_count: 0,
          availability_percentage: 0,
        },
        status: 200,
      };

      mockApiClient.post.mockResolvedValueOnce(mockSummaryResponse);

      const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

      await waitFor(() => {
        expect(getByText('No ingredients found for this recipe')).toBeTruthy();
      });
    });
  });

  describe('Servings Adjustment', () => {
    it('should update servings when changed', async () => {
      const mockSummaryResponse = {
        data: {
          recipe_id: 123,
          available_ingredients: ['Chicken'],
          partial_ingredients: [],
          missing_ingredients: [],
          total_ingredients: 1,
          available_count: 1,
          partial_count: 0,
          missing_count: 0,
          availability_percentage: 100,
        },
        status: 200,
      };

      mockApiClient.post.mockResolvedValueOnce(mockSummaryResponse);

      const { getByTestId, getByText } = render(<QuickCompleteModal {...defaultProps} />);

      await waitFor(() => {
        expect(getByText('Available (1)')).toBeTruthy();
      });

      // Change servings
      const servingsInput = getByTestId('servings-input');
      fireEvent.changeText(servingsInput, '2');

      // Should refetch with new servings
      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith(
          '/recipe-consumption/check-ingredients',
          {
            recipe_id: 123,
            user_id: 111,
            servings: 2,
          }
        );
      });
    });
  });
});
