// StatsScreen.test.tsx
// Test suite for StatsScreen timeout functionality and error handling

import React from 'react';
import { render, waitFor, act } from '@testing-library/react-native';
import StatsScreen from '../../app/(tabs)/stats';
import { AuthProvider } from '../../context/AuthContext';
import { TabDataProvider } from '../../context/TabDataProvider';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock other dependencies
jest.mock('../../services/api', () => ({
  fetchPantryItems: jest.fn().mockResolvedValue([])
}));

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn().mockResolvedValue(null),
  setItem: jest.fn(),
  removeItem: jest.fn()
}));

jest.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    token: 'test-token',
    isAuthenticated: true
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

jest.mock('../../context/TabDataProvider', () => ({
  useTabData: () => ({
    statsData: null,
    isLoadingStats: false,
    refreshStatsData: jest.fn()
  }),
  TabDataProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

jest.mock('react-native-chart-kit', () => ({
  LineChart: 'LineChart',
  BarChart: 'BarChart'
}));

jest.mock('expo-linear-gradient', () => ({
  LinearGradient: 'LinearGradient'
}));

const MockedWrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>
    <TabDataProvider>
      {children}
    </TabDataProvider>
  </AuthProvider>
);

describe('StatsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  describe('API Request Timeout Handling', () => {
    it('should handle fetch timeout correctly', async () => {
      // Mock a delayed response that should timeout
      mockFetch.mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: () => Promise.resolve({
              pantry: { summary: { total_items: 0, expired_items: 0, expiring_soon: 0, recently_added: 0 }, top_products: [] },
              recipes: { cooking_history: { cooked_this_week: 0, cooked_this_month: 0, current_streak: 0 }, total_recipes: 0, favorite_recipes: [] },
              sustainability: { food_saved_kg: 0, co2_saved_kg: 0 }
            })
          }), 15000) // 15 second delay - longer than 10 second timeout
        )
      );

      const { getByText } = render(
        <MockedWrapper>
          <StatsScreen />
        </MockedWrapper>
      );

      // Should show loading initially
      expect(getByText('Loading your stats...')).toBeTruthy();

      // Wait for timeout to occur and error to be displayed
      await waitFor(() => {
        expect(getByText('Failed to load stats')).toBeTruthy();
      }, { timeout: 12000 }); // Give enough time for our timeout to trigger
    });

    it('should successfully load stats within timeout period', async () => {
      // Mock a quick successful response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          pantry: { 
            summary: { total_items: 5, expired_items: 1, expiring_soon: 2, recently_added: 3 }, 
            top_products: [{ product_name: 'Eggs', purchase_count: 3 }] 
          },
          recipes: { 
            cooking_history: { cooked_this_week: 2, cooked_this_month: 8, current_streak: 3 }, 
            total_recipes: 15, 
            favorite_recipes: [{ name: 'Pasta', count: 5 }] 
          },
          sustainability: { food_saved_kg: 2.5, co2_saved_kg: 6.25 }
        })
      });

      const { getByText, queryByText } = render(
        <MockedWrapper>
          <StatsScreen />
        </MockedWrapper>
      );

      // Should show loading initially
      expect(getByText('Loading your stats...')).toBeTruthy();

      // Should successfully load and display stats
      await waitFor(() => {
        expect(queryByText('Loading your stats...')).toBeNull();
        expect(getByText('🏪 Pantry Analytics')).toBeTruthy();
      });
    });

    it('should handle network errors gracefully', async () => {
      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network request failed'));

      const { getByText } = render(
        <MockedWrapper>
          <StatsScreen />
        </MockedWrapper>
      );

      // Should show loading initially
      expect(getByText('Loading your stats...')).toBeTruthy();

      // Should show error message
      await waitFor(() => {
        expect(getByText('Failed to load stats')).toBeTruthy();
        expect(getByText('Network request failed')).toBeTruthy();
      });
    });

    it('should have retry functionality after error', async () => {
      // First call fails
      mockFetch.mockRejectedValueOnce(new Error('Timeout error'));
      
      // Second call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          pantry: { summary: { total_items: 3, expired_items: 0, expiring_soon: 1, recently_added: 2 }, top_products: [] },
          recipes: { cooking_history: { cooked_this_week: 1, cooked_this_month: 4, current_streak: 1 }, total_recipes: 10, favorite_recipes: [] },
          sustainability: { food_saved_kg: 1.5, co2_saved_kg: 3.75 }
        })
      });

      const { getByText, getByRole, queryByText } = render(
        <MockedWrapper>
          <StatsScreen />
        </MockedWrapper>
      );

      // Wait for error state
      await waitFor(() => {
        expect(getByText('Failed to load stats')).toBeTruthy();
        expect(getByText('Retry')).toBeTruthy();
      });

      // Tap retry button
      const retryButton = getByText('Retry');
      act(() => {
        retryButton.props.onPress();
      });

      // Should load successfully after retry
      await waitFor(() => {
        expect(queryByText('Failed to load stats')).toBeNull();
        expect(getByText('🏪 Pantry Analytics')).toBeTruthy();
      });
    });
  });

  describe('AbortController Implementation', () => {
    it('should create AbortController for requests', async () => {
      const mockAbortController = {
        signal: { aborted: false },
        abort: jest.fn()
      };
      
      // Mock AbortController constructor
      const originalAbortController = global.AbortController;
      global.AbortController = jest.fn(() => mockAbortController) as any;

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          pantry: { summary: { total_items: 0, expired_items: 0, expiring_soon: 0, recently_added: 0 }, top_products: [] },
          recipes: { cooking_history: { cooked_this_week: 0, cooked_this_month: 0, current_streak: 0 }, total_recipes: 0, favorite_recipes: [] },
          sustainability: { food_saved_kg: 0, co2_saved_kg: 0 }
        })
      });

      render(
        <MockedWrapper>
          <StatsScreen />
        </MockedWrapper>
      );

      await waitFor(() => {
        // Verify AbortController was created
        expect(global.AbortController).toHaveBeenCalled();
        
        // Verify fetch was called with signal
        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            signal: mockAbortController.signal
          })
        );
      });

      // Restore original AbortController
      global.AbortController = originalAbortController;
    });
  });
});