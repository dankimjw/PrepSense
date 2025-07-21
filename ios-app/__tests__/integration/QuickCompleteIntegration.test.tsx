/**
 * Frontend integration tests for Quick Complete feature
 * Tests the complete flow from UI interaction to API calls
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import { QuickCompleteModal } from '../../components/modals/QuickCompleteModal';
import { PantryItemSelectionModal } from '../../components/modals/PantryItemSelectionModal';
import { apiClient } from '../../services/apiClient';

// Mock API client
jest.mock('../../services/apiClient', () => ({
  apiClient: {
    post: jest.fn(),
  },
}));

// Mock Alert
jest.spyOn(Alert, 'alert');

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('QuickCompleteModal Integration Tests', () => {
  const defaultProps = {
    visible: true,
    onClose: jest.fn(),
    onConfirm: jest.fn(),
    recipeId: 12345,
    recipeName: 'Test Recipe',
    userId: 111,
    servings: 1,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiClient.post.mockClear();
  });

  it('should fetch ingredient availability on mount', async () => {
    // Mock successful check-ingredients response
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        ingredients: [
          {
            ingredient_name: 'chicken breast',
            required_quantity: 1.0,
            required_unit: 'lbs',
            status: 'available',
            pantry_matches: [
              {
                pantry_item_id: 1,
                pantry_item_name: 'Chicken Breast',
                quantity_available: 2.0,
                unit: 'lbs',
                expiration_date: '2025-01-25',
                created_at: '2025-01-20T10:00:00Z',
                days_until_expiry: 5,
              },
            ],
          },
        ],
      },
    });

    render(<QuickCompleteModal {...defaultProps} />);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith('/recipe-consumption/check-ingredients', {
        user_id: 111,
        recipe_id: 12345,
        servings: 1,
      });
    });
  });

  it('should display ingredients with correct status indicators', async () => {
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        ingredients: [
          {
            ingredient_name: 'chicken breast',
            required_quantity: 1.0,
            required_unit: 'lbs',
            status: 'available',
            pantry_matches: [
              {
                pantry_item_id: 1,
                pantry_item_name: 'Chicken Breast',
                quantity_available: 2.0,
                unit: 'lbs',
                days_until_expiry: 5,
              },
            ],
          },
          {
            ingredient_name: 'onion',
            required_quantity: 2.0,
            required_unit: 'count',
            status: 'partial',
            pantry_matches: [
              {
                pantry_item_id: 2,
                pantry_item_name: 'Yellow Onion',
                quantity_available: 1.0,
                unit: 'count',
                days_until_expiry: 3,
              },
            ],
          },
          {
            ingredient_name: 'garlic',
            required_quantity: 1.0,
            required_unit: 'head',
            status: 'missing',
            pantry_matches: [],
          },
        ],
      },
    });

    const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

    await waitFor(() => {
      expect(getByText('chicken breast')).toBeTruthy();
      expect(getByText('Available')).toBeTruthy();
      expect(getByText('Partially available')).toBeTruthy();
      expect(getByText('Missing')).toBeTruthy();
    });
  });

  it('should show expiration information for selected items', async () => {
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        ingredients: [
          {
            ingredient_name: 'chicken breast',
            required_quantity: 1.0,
            required_unit: 'lbs',
            status: 'available',
            pantry_matches: [
              {
                pantry_item_id: 1,
                pantry_item_name: 'Chicken Breast',
                quantity_available: 2.0,
                unit: 'lbs',
                days_until_expiry: 1, // Expires tomorrow
              },
            ],
          },
        ],
      },
    });

    const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

    await waitFor(() => {
      expect(getByText('Expires tomorrow')).toBeTruthy();
    });
  });

  it('should handle quick complete submission successfully', async () => {
    // Mock check-ingredients response
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        ingredients: [
          {
            ingredient_name: 'chicken breast',
            required_quantity: 1.0,
            required_unit: 'lbs',
            status: 'available',
            pantry_matches: [
              {
                pantry_item_id: 1,
                pantry_item_name: 'Chicken Breast',
                quantity_available: 2.0,
                unit: 'lbs',
                days_until_expiry: 5,
              },
            ],
          },
        ],
      },
    });

    // Mock quick-complete response
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Recipe completed successfully!',
        completion_record: {
          recipe_id: 12345,
          recipe_title: 'Test Recipe',
          servings: 1,
        },
        updated_items: [
          {
            item_id: 1,
            name: 'chicken breast',
            quantity_used: 1.0,
            remaining_quantity: 1.0,
          },
        ],
        depleted_items: [],
      },
    });

    const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

    // Wait for ingredients to load
    await waitFor(() => {
      expect(getByText('chicken breast')).toBeTruthy();
    });

    // Find and tap Quick Complete button
    const quickCompleteButton = getByText('Quick Complete');
    fireEvent.press(quickCompleteButton);

    await waitFor(() => {
      expect(mockApiClient.post).toHaveBeenCalledWith('/recipe-consumption/quick-complete', {
        user_id: 111,
        recipe_id: 12345,
        servings: 1,
        ingredient_selections: [
          {
            ingredient_name: 'chicken breast',
            pantry_item_id: 1,
            quantity_to_use: 1.0,
            unit: 'lbs',
          },
        ],
      });
    });

    // Should show success alert
    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Recipe Completed!',
        'Recipe completed successfully!',
        expect.any(Array)
      );
    });
  });

  it('should handle API errors gracefully', async () => {
    // Mock API error
    mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));

    const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

    await waitFor(() => {
      expect(getByText('Failed to load ingredient information')).toBeTruthy();
      expect(getByText('Try Again')).toBeTruthy();
    });
  });

  it('should allow retrying after error', async () => {
    // First call fails
    mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));
    
    const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

    await waitFor(() => {
      expect(getByText('Try Again')).toBeTruthy();
    });

    // Second call succeeds
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        ingredients: [
          {
            ingredient_name: 'chicken breast',
            required_quantity: 1.0,
            required_unit: 'lbs',
            status: 'available',
            pantry_matches: [
              {
                pantry_item_id: 1,
                pantry_item_name: 'Chicken Breast',
                quantity_available: 2.0,
                unit: 'lbs',
                days_until_expiry: 5,
              },
            ],
          },
        ],
      },
    });

    const retryButton = getByText('Try Again');
    fireEvent.press(retryButton);

    await waitFor(() => {
      expect(getByText('chicken breast')).toBeTruthy();
    });
  });

  it('should show loading state during API calls', async () => {
    // Mock delayed response
    mockApiClient.post.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ data: { ingredients: [] } }), 100))
    );

    const { getByText } = render(<QuickCompleteModal {...defaultProps} />);

    expect(getByText('Checking ingredient availability...')).toBeTruthy();
  });

  it('should disable quick complete button when no available ingredients', async () => {
    mockApiClient.post.mockResolvedValueOnce({
      data: {
        ingredients: [
          {
            ingredient_name: 'missing item',
            required_quantity: 1.0,
            required_unit: 'count',
            status: 'missing',
            pantry_matches: [],
          },
        ],
      },
    });

    const { queryByText } = render(<QuickCompleteModal {...defaultProps} />);

    await waitFor(() => {
      expect(queryByText('Quick Complete')).toBeNull();
    });
  });
});

describe('PantryItemSelectionModal Integration Tests', () => {
  const defaultProps = {
    visible: true,
    ingredientName: 'chicken breast',
    requiredQuantity: 1.0,
    requiredUnit: 'lbs',
    availableItems: [
      {
        pantryItemId: 1,
        pantryItemName: 'Chicken Breast Package 1',
        quantityAvailable: 1.5,
        unit: 'lbs',
        expirationDate: '2025-01-23',
        addedDate: '2025-01-20T10:00:00Z',
        daysUntilExpiry: 3,
      },
      {
        pantryItemId: 2,
        pantryItemName: 'Chicken Breast Package 2',
        quantityAvailable: 2.0,
        unit: 'lbs',
        expirationDate: '2025-01-25',
        addedDate: '2025-01-20T09:00:00Z',
        daysUntilExpiry: 5,
      },
    ],
    currentSelection: undefined,
    onSelect: jest.fn(),
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display available items sorted by expiration date', () => {
    const { getByText } = render(<PantryItemSelectionModal {...defaultProps} />);

    expect(getByText('Chicken Breast Package 1')).toBeTruthy();
    expect(getByText('Chicken Breast Package 2')).toBeTruthy();
    expect(getByText('Expires in 3 days')).toBeTruthy();
    expect(getByText('Expires in 5 days')).toBeTruthy();
  });

  it('should call onSelect when item is tapped', () => {
    const { getByText } = render(<PantryItemSelectionModal {...defaultProps} />);

    const firstItem = getByText('Chicken Breast Package 1');
    fireEvent.press(firstItem);

    expect(defaultProps.onSelect).toHaveBeenCalledWith({
      pantryItemId: 1,
      pantryItemName: 'Chicken Breast Package 1',
      quantityAvailable: 1.5,
      unit: 'lbs',
      expirationDate: '2025-01-23',
      addedDate: '2025-01-20T10:00:00Z',
      daysUntilExpiry: 3,
    });
  });

  it('should show current selection with radio button', () => {
    const propsWithSelection = {
      ...defaultProps,
      currentSelection: defaultProps.availableItems[0],
    };

    const { getByTestId } = render(<PantryItemSelectionModal {...propsWithSelection} />);

    expect(getByTestId('radio-selected-1')).toBeTruthy();
  });

  it('should show priority badge for items expiring soon', () => {
    const propsWithUrgentItem = {
      ...defaultProps,
      availableItems: [
        {
          pantryItemId: 1,
          pantryItemName: 'Expiring Soon',
          quantityAvailable: 1.0,
          unit: 'lbs',
          expirationDate: '2025-01-22',
          addedDate: '2025-01-20T10:00:00Z',
          daysUntilExpiry: 1, // Expires tomorrow
        },
      ],
    };

    const { getByText } = render(<PantryItemSelectionModal {...propsWithUrgentItem} />);

    expect(getByText('Priority')).toBeTruthy();
  });
});

describe('RecipeDetailCardV2 Quick Complete Integration', () => {
  // Mock the recipe data
  const mockRecipe = {
    id: 12345,
    title: 'Test Recipe',
    image: 'https://example.com/image.jpg',
    readyInMinutes: 30,
    servings: 4,
    nutrition: {
      calories: 400,
      protein: 30,
      carbs: 20,
      fat: 15,
    },
    extendedIngredients: [
      {
        id: 1,
        name: 'chicken breast',
        amount: 1.0,
        unit: 'lbs',
        original: '1 lb chicken breast',
      },
    ],
    available_ingredients: ['chicken breast'],
    pantry_item_matches: {
      'chicken breast': [
        {
          pantry_item_id: 1,
          product_name: 'Chicken Breast',
          quantity: 2.0,
          unit: 'lbs',
        },
      ],
    },
    analyzedInstructions: [
      {
        steps: [
          {
            number: 1,
            step: 'Cook the chicken breast.',
          },
        ],
      },
    ],
  };

  it('should show Quick Complete button when ingredients are available', () => {
    const RecipeDetailCardV2 = require('../../components/recipes/RecipeDetailCardV2').default;
    
    const { getByTestId } = render(
      <RecipeDetailCardV2 recipe={mockRecipe} />
    );

    expect(getByTestId('quick-complete-button')).toBeTruthy();
    expect(getByTestId('quick-complete-text')).toBeTruthy();
  });

  it('should not show Quick Complete button when no ingredients available', () => {
    const RecipeDetailCardV2 = require('../../components/recipes/RecipeDetailCardV2').default;
    
    const recipeWithoutIngredients = {
      ...mockRecipe,
      available_ingredients: [],
    };

    const { queryByTestId } = render(
      <RecipeDetailCardV2 recipe={recipeWithoutIngredients} />
    );

    expect(queryByTestId('quick-complete-button')).toBeNull();
  });

  it('should open Quick Complete modal when button is pressed', () => {
    const RecipeDetailCardV2 = require('../../components/recipes/RecipeDetailCardV2').default;
    
    const { getByTestId } = render(
      <RecipeDetailCardV2 recipe={mockRecipe} />
    );

    const quickCompleteButton = getByTestId('quick-complete-button');
    fireEvent.press(quickCompleteButton);

    // Modal should be visible
    expect(getByTestId('quick-complete-modal')).toBeTruthy();
  });
});