// expirationPreventionIntelligence.test.tsx
// Test suite for verifying expiration prevention features and waste reduction intelligence

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import HomeScreen from '../../screens/HomeScreen';
import RecipesScreen from '../../screens/RecipesScreen';
import QuickCompleteModal from '../../components/modals/QuickCompleteModal';
import { apiClient } from '../../services/apiClient';
import * as Notifications from 'expo-notifications';

// Mock the services
jest.mock('../../services/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }
}));

jest.mock('expo-notifications', () => ({
  scheduleNotificationAsync: jest.fn(),
  cancelScheduledNotificationAsync: jest.fn(),
  getAllScheduledNotificationsAsync: jest.fn(),
  setNotificationHandler: jest.fn()
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Expiration Prevention Intelligence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Mock data for expiring items
  const mockExpiringItems = [
    {
      id: 1,
      name: 'Spinach',
      quantity: 200,
      unit: 'g',
      expiration_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days
      days_until_expiry: 2,
      category: 'Produce',
      priority: 'high'
    },
    {
      id: 2,
      name: 'Greek Yogurt',
      quantity: 500,
      unit: 'g',
      expiration_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days
      days_until_expiry: 3,
      category: 'Dairy',
      priority: 'high'
    },
    {
      id: 3,
      name: 'Chicken Breast',
      quantity: 400,
      unit: 'g',
      expiration_date: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
      days_until_expiry: 1,
      category: 'Protein',
      priority: 'critical'
    }
  ];

  describe('Expiration Alerts and Notifications', () => {
    it('should display expiring items prominently on home screen', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/pantry/expiring')) {
          return Promise.resolve({
            data: {
              expiring_soon: mockExpiringItems,
              total_at_risk_value: 25.50,
              potential_waste_kg: 1.1
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Alert banner should be visible
        const alertBanner = getByTestId('expiration-alert-banner');
        expect(alertBanner).toBeTruthy();
        expect(alertBanner).toHaveStyle({ backgroundColor: '#FF5252' }); // Red for critical
        
        // Show items expiring soon
        expect(getByText('3 items expiring soon')).toBeTruthy();
        expect(getByText('Chicken Breast expires tomorrow!')).toBeTruthy();
        expect(getByText('$25.50 worth of food at risk')).toBeTruthy();
      });
    });

    it('should schedule smart notifications based on expiration patterns', async () => {
      // Mock notification permission
      Notifications.scheduleNotificationAsync.mockResolvedValue('notification-id-123');

      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/notifications/schedule')) {
          // Verify intelligent scheduling
          expect(data.notifications).toEqual(
            expect.arrayContaining([
              expect.objectContaining({
                item: 'Chicken Breast',
                trigger_time: 'morning', // Morning of expiry day
                message: expect.stringContaining('expires today')
              }),
              expect.objectContaining({
                item: 'Spinach',
                trigger_time: 'evening_before', // Evening before expiry
                message: expect.stringContaining('Use soon')
              })
            ])
          );
          
          return Promise.resolve({
            data: { scheduled: data.notifications.length }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Enable notifications
      await act(async () => {
        await mockApiClient.post('/notifications/schedule', {
          notifications: [
            {
              item: 'Chicken Breast',
              trigger_time: 'morning',
              message: 'Chicken Breast expires today! Use it or lose it.'
            },
            {
              item: 'Spinach',
              trigger_time: 'evening_before',
              message: 'Spinach expires tomorrow. Use soon!'
            }
          ]
        });
      });

      // Verify notifications were scheduled
      expect(Notifications.scheduleNotificationAsync).toHaveBeenCalledTimes(2);
    });

    it('should prioritize notifications based on item value and quantity', async () => {
      const itemsWithValue = [
        { ...mockExpiringItems[2], estimated_value: 12.00 }, // Chicken - high value
        { ...mockExpiringItems[0], estimated_value: 3.00 }, // Spinach - low value
        { ...mockExpiringItems[1], estimated_value: 5.00 } // Yogurt - medium value
      ];

      mockApiClient.get.mockResolvedValueOnce({
        data: {
          notification_priority: [
            {
              item: 'Chicken Breast',
              priority_score: 95, // High value + expires tomorrow
              notification_strategy: 'aggressive'
            },
            {
              item: 'Greek Yogurt',
              priority_score: 60,
              notification_strategy: 'moderate'
            },
            {
              item: 'Spinach',
              priority_score: 40,
              notification_strategy: 'gentle'
            }
          ]
        }
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // High priority items shown first
        const priorityList = getByTestId('expiration-priority-list');
        const items = priorityList.children;
        
        expect(items[0]).toHaveTextContent('Chicken Breast');
        expect(items[0]).toHaveTextContent('$12.00 at risk');
      });
    });
  });

  describe('Smart Recipe Suggestions for Expiring Items', () => {
    it('should suggest recipes that use expiring ingredients', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/expiration-recipes')) {
          // AI should prioritize expiring items
          expect(data.expiring_items).toEqual(
            expect.arrayContaining([
              expect.objectContaining({ name: 'Chicken Breast' }),
              expect.objectContaining({ name: 'Spinach' })
            ])
          );

          return Promise.resolve({
            data: {
              suggested_recipes: [
                {
                  recipe_id: 101,
                  title: 'Chicken Spinach Alfredo',
                  uses_expiring: ['Chicken Breast', 'Spinach'],
                  waste_prevented: '600g',
                  expiration_score: 0.95,
                  ready_in_minutes: 25
                },
                {
                  recipe_id: 102,
                  title: 'Greek Chicken Bowl',
                  uses_expiring: ['Chicken Breast', 'Greek Yogurt'],
                  waste_prevented: '500g',
                  expiration_score: 0.88,
                  ready_in_minutes: 20
                }
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      // Trigger expiration-based suggestions
      fireEvent.press(getByTestId('use-expiring-button'));

      await waitFor(() => {
        // Should show special section
        expect(getByText('Save Expiring Items')).toBeTruthy();
        expect(getByText('Chicken Spinach Alfredo')).toBeTruthy();
        expect(getByText('Uses: Chicken, Spinach')).toBeTruthy();
        expect(getByText('Saves 600g from waste')).toBeTruthy();
      });
    });

    it('should show expiration badges on recipe cards', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/recipes')) {
          return Promise.resolve({
            data: [
              {
                id: 101,
                title: 'Chicken Spinach Alfredo',
                expiration_prevention: {
                  saves_items: ['Chicken Breast', 'Spinach'],
                  urgency: 'high',
                  days_until_expiry: 1
                }
              }
            ]
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        const recipeCard = getByTestId('recipe-card-101');
        
        // Expiration prevention badge
        const badge = recipeCard.querySelector('[testID="expiration-badge"]');
        expect(badge).toBeTruthy();
        expect(badge).toHaveStyle({ backgroundColor: '#FF5252' }); // Red urgency
        expect(badge).toHaveTextContent('Saves expiring items');
      });
    });

    it('should track when users cook expiration-preventing recipes', async () => {
      const recipe = {
        id: 101,
        title: 'Chicken Spinach Alfredo',
        uses_expiring: ['Chicken Breast', 'Spinach']
      };

      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/recipe-consumption/quick-complete')) {
          // Should include waste prevention metrics
          expect(data.waste_prevention).toEqual({
            items_saved: ['Chicken Breast', 'Spinach'],
            weight_saved: 600,
            value_saved: 15.00,
            days_before_expiry_used: {
              'Chicken Breast': 1,
              'Spinach': 2
            }
          });

          return Promise.resolve({
            data: {
              success: true,
              waste_prevented: {
                total_kg: 0.6,
                total_value: 15.00,
                environmental_impact: 'Saved 2.4kg CO2 equivalent'
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <QuickCompleteModal
          visible={true}
          recipe={recipe}
          onClose={jest.fn()}
        />
      );

      // Complete recipe
      fireEvent.press(getByTestId('complete-button'));

      await waitFor(() => {
        // Show waste prevention success
        expect(getByText('Great job! You saved 600g from waste')).toBeTruthy();
        expect(getByText('Environmental impact: 2.4kg CO2 saved')).toBeTruthy();
      });
    });
  });

  describe('Waste Prevention Analytics', () => {
    it('should display waste prevention metrics on dashboard', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/stats/waste-prevention')) {
          return Promise.resolve({
            data: {
              lifetime_stats: {
                total_prevented_kg: 45.7,
                total_value_saved: 342.50,
                items_saved_count: 128,
                co2_equivalent_saved: 182.8
              },
              monthly_trend: [
                { month: 'Jan', prevented_kg: 12.3, value: 89.50 },
                { month: 'Feb', prevented_kg: 15.7, value: 118.00 },
                { month: 'Mar', prevented_kg: 17.7, value: 135.00 }
              ],
              prevention_rate: 78, // percentage
              most_saved_categories: [
                { category: 'Produce', percentage: 45 },
                { category: 'Dairy', percentage: 30 },
                { category: 'Protein', percentage: 25 }
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Waste prevention widget
        const wasteWidget = getByTestId('waste-prevention-widget');
        expect(wasteWidget).toHaveTextContent('45.7kg Food Saved');
        expect(wasteWidget).toHaveTextContent('$342.50 Value');
        expect(wasteWidget).toHaveTextContent('78% Prevention Rate');
        
        // Environmental impact
        expect(getByText('🌍 182.8kg CO2 Saved')).toBeTruthy();
      });
    });

    it('should show achievement unlocks for waste prevention milestones', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/achievements/check')) {
          return Promise.resolve({
            data: {
              unlocked: [
                {
                  id: 'waste_warrior_bronze',
                  title: 'Waste Warrior - Bronze',
                  description: 'Prevented 10kg of food waste',
                  unlocked_at: new Date().toISOString(),
                  reward: 'New recipe filter: Zero Waste Meals'
                }
              ],
              progress: {
                next_milestone: 'waste_warrior_silver',
                current: 10.2,
                target: 25,
                percentage: 41
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Simulate reaching milestone
      await act(async () => {
        await mockApiClient.post('/achievements/check', {
          type: 'waste_prevention',
          amount: 10.2
        });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Achievement notification
        const achievementModal = getByTestId('achievement-modal');
        expect(achievementModal).toBeTruthy();
        expect(getByText('Waste Warrior - Bronze')).toBeTruthy();
        expect(getByText('New filter unlocked!')).toBeTruthy();
      });
    });

    it('should provide insights on best waste prevention practices', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/analytics/waste-insights')) {
          return Promise.resolve({
            data: {
              insights: [
                {
                  type: 'timing_pattern',
                  message: 'You save 40% more food when meal planning on Sundays',
                  recommendation: 'Continue Sunday planning routine'
                },
                {
                  type: 'category_success',
                  message: 'Your produce waste dropped 60% using FIFO method',
                  recommendation: 'Apply same method to dairy items'
                },
                {
                  type: 'recipe_impact',
                  message: 'Stir-fries prevent 3x more waste than salads',
                  recommendation: 'Prioritize stir-fries for expiring vegetables'
                }
              ],
              personalized_tips: [
                'Set reminders 2 days before dairy expires',
                'Freeze herbs in ice cubes before they spoil',
                'Your spinach lasts longer in paper towels'
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Insights section
        expect(getByText('Waste Prevention Insights')).toBeTruthy();
        expect(getByText('Sunday planning saves 40% more')).toBeTruthy();
        expect(getByText('Stir-fries prevent 3x more waste')).toBeTruthy();
      });
    });
  });

  describe('Proactive Prevention Features', () => {
    it('should auto-adjust shopping quantities based on waste patterns', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/shopping/smart-quantities')) {
          return Promise.resolve({
            data: {
              adjusted_quantities: [
                {
                  item: 'Spinach',
                  original_quantity: '500g',
                  suggested_quantity: '300g',
                  reason: 'You typically use only 60% before expiry',
                  waste_history: {
                    average_unused: '200g',
                    frequency: 'monthly'
                  }
                }
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Shopping suggestions
        const suggestion = getByTestId('quantity-suggestion-spinach');
        expect(suggestion).toHaveTextContent('Buy 300g instead of 500g');
        expect(suggestion).toHaveTextContent('Based on your usage patterns');
      });
    });

    it('should suggest preservation methods for at-risk items', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/preservation/suggestions')) {
          return Promise.resolve({
            data: {
              preservation_tips: [
                {
                  item: 'Spinach',
                  days_until_expiry: 2,
                  methods: [
                    {
                      method: 'Blanch and freeze',
                      extends_life: '3 months',
                      difficulty: 'easy',
                      time_required: '10 minutes'
                    },
                    {
                      method: 'Make pesto',
                      extends_life: '2 weeks',
                      difficulty: 'medium',
                      creates: 'Spinach pesto sauce'
                    }
                  ]
                },
                {
                  item: 'Greek Yogurt',
                  days_until_expiry: 3,
                  methods: [
                    {
                      method: 'Freeze in ice cube trays',
                      extends_life: '2 months',
                      use_case: 'Perfect for smoothies'
                    }
                  ]
                }
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      fireEvent.press(getByTestId('preservation-tips-button'));

      await waitFor(() => {
        expect(getByText('Preservation Options')).toBeTruthy();
        expect(getByText('Blanch and freeze Spinach')).toBeTruthy();
        expect(getByText('Extends life by 3 months')).toBeTruthy();
        expect(getByText('10 minutes • Easy')).toBeTruthy();
      });
    });

    it('should integrate with meal planning to minimize waste', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/meal-plan/optimize')) {
          return Promise.resolve({
            data: {
              optimized_plan: {
                monday: {
                  recipe: 'Chicken Stir Fry',
                  uses_expiring: ['Chicken Breast'],
                  prevents_waste: '400g'
                },
                tuesday: {
                  recipe: 'Green Smoothie',
                  uses_expiring: ['Spinach', 'Greek Yogurt'],
                  prevents_waste: '300g'
                },
                waste_prevention_total: '700g',
                items_saved: 3
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <HomeScreen />
        </NavigationContainer>
      );

      fireEvent.press(getByTestId('optimize-meal-plan'));

      await waitFor(() => {
        expect(getByText('Meal Plan Optimized')).toBeTruthy();
        expect(getByText('Saves 700g from waste')).toBeTruthy();
        expect(getByText('Monday: Chicken Stir Fry')).toBeTruthy();
        expect(getByText('Uses expiring chicken')).toBeTruthy();
      });
    });

    it('should learn from user behavior to improve predictions', async () => {
      // Track when user marks items as used/wasted
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/items/update-status')) {
          expect(data).toEqual({
            item_id: 1,
            status: 'used',
            used_percentage: 100,
            used_in_recipe: 'Chicken Spinach Alfredo',
            days_before_expiry: 2
          });

          return Promise.resolve({
            data: {
              learning_update: {
                pattern_detected: 'User consistently uses spinach 2 days before expiry',
                prediction_accuracy_improved: true,
                new_notification_timing: 'day_minus_3'
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // User marks item as used
      await act(async () => {
        await mockApiClient.post('/items/update-status', {
          item_id: 1,
          status: 'used',
          used_percentage: 100,
          used_in_recipe: 'Chicken Spinach Alfredo',
          days_before_expiry: 2
        });
      });

      // System should learn and adjust
      expect(mockApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('update-status'),
        expect.objectContaining({
          days_before_expiry: 2
        })
      );
    });
  });
});