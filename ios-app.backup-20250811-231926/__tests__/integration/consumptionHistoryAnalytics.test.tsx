// consumptionHistoryAnalytics.test.tsx
// Test suite for verifying consumption history tracking and analytics data flows

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import HomeScreen from '../../screens/HomeScreen';
import StatsScreen from '../../screens/StatsScreen';
import { apiClient } from '../../services/apiClient';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock the services
jest.mock('../../services/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }
}));

jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn()
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('Consumption History & Analytics Data Flows', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Historical Data Collection', () => {
    it('should track recipe completion events with timestamp and ingredients', async () => {
      const recipeCompletionData = {
        recipe_id: 123,
        recipe_title: 'Spaghetti Carbonara',
        completed_at: new Date().toISOString(),
        servings_made: 4,
        ingredients_consumed: [
          { item_id: 1, name: 'Pasta', quantity: 400, unit: 'g' },
          { item_id: 2, name: 'Eggs', quantity: 4, unit: 'units' },
          { item_id: 3, name: 'Bacon', quantity: 200, unit: 'g' }
        ],
        cooking_duration: 25, // minutes
        user_rating: null, // To be added post-cooking
        waste_prevented: 150 // grams of soon-to-expire bacon used
      };

      // Mock Quick Complete endpoint to verify it sends analytics data
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/recipe-consumption/quick-complete')) {
          // Verify analytics payload is included
          expect(data).toMatchObject({
            recipe_id: 123,
            analytics: {
              completed_at: expect.any(String),
              servings_made: 4,
              cooking_duration: expect.any(Number)
            }
          });
          
          return Promise.resolve({
            data: {
              success: true,
              history_id: 'hist_123456' // ID for later updates
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Simulate recipe completion
      await act(async () => {
        await mockApiClient.post('/recipe-consumption/quick-complete', {
          recipe_id: 123,
          servings_made: 4,
          ingredients: recipeCompletionData.ingredients_consumed,
          analytics: {
            completed_at: recipeCompletionData.completed_at,
            servings_made: 4,
            cooking_duration: 25
          }
        });
      });

      // Verify history entry was created
      expect(mockApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('quick-complete'),
        expect.objectContaining({
          analytics: expect.any(Object)
        })
      );
    });

    it('should aggregate consumption patterns for dashboard display', async () => {
      // Mock stats endpoint with historical data
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/stats/comprehensive')) {
          return Promise.resolve({
            data: {
              consumption_history: {
                total_recipes_made: 47,
                recipes_this_week: 12,
                most_cooked: [
                  { recipe: 'Pasta Primavera', count: 8 },
                  { recipe: 'Chicken Stir Fry', count: 6 },
                  { recipe: 'Greek Salad', count: 5 }
                ],
                cooking_frequency: {
                  monday: 2,
                  tuesday: 1,
                  wednesday: 3,
                  thursday: 2,
                  friday: 3,
                  saturday: 1,
                  sunday: 0
                },
                peak_cooking_time: '18:00-20:00',
                average_cooking_duration: 35 // minutes
              },
              ingredient_usage: {
                most_used: [
                  { name: 'Olive Oil', total_quantity: '2.5L' },
                  { name: 'Garlic', total_quantity: '45 cloves' },
                  { name: 'Onions', total_quantity: '3.2kg' }
                ],
                depletion_rate: {
                  'Olive Oil': '250ml/week',
                  'Eggs': '12/week',
                  'Milk': '2L/week'
                }
              },
              waste_metrics: {
                total_prevented: '12.3kg',
                saved_this_month: '3.1kg',
                expiry_prevention_rate: 78 // percentage
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <StatsScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Verify dashboard shows historical metrics
        expect(getByText('47 Recipes Cooked')).toBeTruthy();
        expect(getByText('12 This Week')).toBeTruthy();
        expect(getByText('Top Recipe: Pasta Primavera (8x)')).toBeTruthy();
        expect(getByText('Peak Time: 6-8 PM')).toBeTruthy();
        expect(getByText('12.3kg Food Saved')).toBeTruthy();
      });

      // Verify chart rendering with historical data
      const cookingChart = getByTestId('cooking-frequency-chart');
      expect(cookingChart).toBeTruthy();
    });

    it('should track ingredient substitutions and modifications', async () => {
      const modificationData = {
        history_id: 'hist_123456',
        modifications: [
          {
            original_ingredient: 'Heavy Cream',
            substituted_with: 'Greek Yogurt',
            reason: 'healthier_option'
          },
          {
            original_ingredient: 'Bacon',
            substituted_with: 'Turkey Bacon',
            reason: 'dietary_preference'
          }
        ],
        notes: 'Used less oil than recipe suggested'
      };

      mockApiClient.put.mockResolvedValueOnce({
        data: { success: true }
      });

      // User makes modifications post-cooking
      await act(async () => {
        await mockApiClient.put('/consumption-history/hist_123456', {
          modifications: modificationData.modifications,
          user_notes: modificationData.notes
        });
      });

      // Verify modification tracking
      expect(mockApiClient.put).toHaveBeenCalledWith(
        expect.stringContaining('consumption-history'),
        expect.objectContaining({
          modifications: expect.arrayContaining([
            expect.objectContaining({
              substituted_with: 'Greek Yogurt'
            })
          ])
        })
      );
    });
  });

  describe('AI Training Data Generation', () => {
    it('should generate training data from consumption patterns', async () => {
      // Mock endpoint that prepares data for AI
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/ai/training-data')) {
          return Promise.resolve({
            data: {
              user_preferences: {
                favorite_cuisines: ['Italian', 'Asian', 'Mediterranean'],
                cooking_skill_level: 'intermediate',
                typical_cooking_time: 30,
                dietary_patterns: {
                  low_carb_tendency: 0.3,
                  vegetarian_meals: 0.4,
                  quick_meals: 0.6
                }
              },
              ingredient_preferences: {
                frequently_used: ['olive oil', 'garlic', 'tomatoes'],
                never_used: ['blue cheese', 'anchovies'],
                substitution_patterns: {
                  'heavy cream': ['greek yogurt', 'coconut milk'],
                  'white sugar': ['honey', 'maple syrup']
                }
              },
              cooking_patterns: {
                meal_prep_sunday: true,
                batch_cooking: 0.7,
                leftover_usage: 0.8,
                experimental_cooking: 0.4
              },
              success_metrics: {
                completion_rate: 0.92,
                recipe_abandonment: 0.08,
                average_rating: 4.3,
                repeat_recipe_rate: 0.65
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Verify AI can access historical patterns
      const trainingData = await mockApiClient.get('/ai/training-data');
      
      expect(trainingData.data.user_preferences).toBeDefined();
      expect(trainingData.data.cooking_patterns.meal_prep_sunday).toBe(true);
      expect(trainingData.data.success_metrics.completion_rate).toBe(0.92);
    });

    it('should update AI recommendations based on historical success', async () => {
      // Mock CrewAI using historical data
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/recommendations')) {
          // AI should consider historical preferences
          expect(data.context).toMatchObject({
            historical_preferences: expect.any(Object),
            recent_recipes: expect.any(Array),
            ingredient_usage_patterns: expect.any(Object)
          });

          return Promise.resolve({
            data: {
              recommendations: [
                {
                  recipe_id: 789,
                  title: 'Quick Veggie Stir Fry',
                  score: 0.95,
                  reasoning: [
                    'Matches 30-minute cooking preference',
                    'Uses frequently used ingredients',
                    'Similar to previously enjoyed Asian dishes',
                    'High vegetarian meal compatibility'
                  ]
                }
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Request recommendations
      const response = await mockApiClient.post('/ai/recommendations', {
        context: {
          historical_preferences: { cooking_time: 30 },
          recent_recipes: ['Pad Thai', 'Veggie Curry'],
          ingredient_usage_patterns: { 'soy sauce': 'frequent' }
        }
      });

      // Verify AI uses historical context
      expect(response.data.recommendations[0].reasoning).toContain(
        'Matches 30-minute cooking preference'
      );
    });

    it('should track failed recipes for negative training data', async () => {
      const failureData = {
        recipe_id: 456,
        reason: 'too_complex',
        abandoned_at_step: 3,
        total_steps: 8,
        time_spent: 15,
        user_feedback: 'Instructions were unclear, ingredients not readily available'
      };

      mockApiClient.post.mockResolvedValueOnce({
        data: { success: true }
      });

      // Track recipe abandonment
      await act(async () => {
        await mockApiClient.post('/consumption-history/abandonment', failureData);
      });

      // Verify negative feedback is tracked
      expect(mockApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('abandonment'),
        expect.objectContaining({
          reason: 'too_complex',
          abandoned_at_step: 3
        })
      );
    });
  });

  describe('Predictive Analytics', () => {
    it('should predict ingredient depletion based on usage patterns', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/analytics/predictions')) {
          return Promise.resolve({
            data: {
              depletion_predictions: [
                {
                  item: 'Olive Oil',
                  current_quantity: '500ml',
                  predicted_depletion: '2024-02-15',
                  days_remaining: 7,
                  confidence: 0.85,
                  usage_trend: 'increasing'
                },
                {
                  item: 'Eggs',
                  current_quantity: '6',
                  predicted_depletion: '2024-02-12',
                  days_remaining: 4,
                  confidence: 0.92,
                  usage_trend: 'steady'
                }
              ],
              restock_recommendations: [
                {
                  item: 'Olive Oil',
                  suggested_quantity: '1L',
                  optimal_purchase_date: '2024-02-13'
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
        // Home screen should show predictions
        const alertSection = getByTestId('depletion-alerts');
        expect(alertSection).toHaveTextContent('Olive Oil running low (7 days)');
        expect(alertSection).toHaveTextContent('Eggs running low (4 days)');
      });
    });

    it('should suggest recipes based on consumption history and current pantry', async () => {
      mockApiClient.post.mockImplementation((url) => {
        if (url.includes('/ai/contextual-suggestions')) {
          return Promise.resolve({
            data: {
              suggestions: [
                {
                  recipe_id: 321,
                  title: 'Pasta Aglio e Olio',
                  reason: 'You have all ingredients and often cook pasta on Wednesdays',
                  historical_context: {
                    similar_recipes_enjoyed: 5,
                    last_cooked_similar: '3 weeks ago',
                    success_rate: 0.9
                  }
                },
                {
                  recipe_id: 654,
                  title: 'Veggie Frittata',
                  reason: 'Uses eggs before expiration, matches breakfast preference',
                  historical_context: {
                    breakfast_frequency: 0.7,
                    egg_usage_pattern: 'high'
                  }
                }
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
        // Contextual suggestions based on history
        expect(getByText('Suggested for Today')).toBeTruthy();
        expect(getByText('Pasta Aglio e Olio')).toBeTruthy();
        expect(getByText('You often cook pasta on Wednesdays')).toBeTruthy();
      });
    });
  });

  describe('Dashboard Visualization', () => {
    it('should display cooking trends over time', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/stats/trends')) {
          return Promise.resolve({
            data: {
              monthly_trends: [
                { month: 'Jan', recipes_cooked: 35, waste_prevented: 8.2 },
                { month: 'Feb', recipes_cooked: 42, waste_prevented: 9.1 },
                { month: 'Mar', recipes_cooked: 38, waste_prevented: 7.8 }
              ],
              cuisine_distribution: {
                Italian: 35,
                Asian: 25,
                Mexican: 20,
                American: 15,
                Other: 5
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByTestId } = render(
        <NavigationContainer>
          <StatsScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Verify trend charts
        const trendChart = getByTestId('monthly-trend-chart');
        expect(trendChart).toBeTruthy();
        
        const cuisineChart = getByTestId('cuisine-pie-chart');
        expect(cuisineChart).toBeTruthy();
      });
    });

    it('should show milestone achievements based on history', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/stats/milestones')) {
          return Promise.resolve({
            data: {
              achievements: [
                {
                  id: 'waste_warrior',
                  title: 'Waste Warrior',
                  description: 'Prevented 10kg of food waste',
                  unlocked_at: '2024-02-01',
                  progress: 100
                },
                {
                  id: 'cuisine_explorer',
                  title: 'Cuisine Explorer',
                  description: 'Cooked recipes from 5 different cuisines',
                  progress: 80,
                  next_milestone: 'Cook 1 more cuisine type'
                }
              ],
              streaks: {
                current_cooking_streak: 5,
                longest_streak: 12,
                meal_prep_streak: 3
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <StatsScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // Display achievements
        expect(getByText('Waste Warrior')).toBeTruthy();
        expect(getByText('Prevented 10kg of food waste')).toBeTruthy();
        
        // Show streaks
        const streakBadge = getByTestId('cooking-streak');
        expect(streakBadge).toHaveTextContent('5 day streak!');
      });
    });
  });

  describe('Data Export and Insights', () => {
    it('should allow exporting consumption history for analysis', async () => {
      mockApiClient.get.mockResolvedValueOnce({
        data: {
          export_url: 'https://api.prepsense.com/exports/history_123.csv',
          format: 'csv',
          included_data: [
            'recipe_completions',
            'ingredient_usage',
            'waste_metrics',
            'substitutions'
          ]
        }
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <StatsScreen />
        </NavigationContainer>
      );

      // Request export
      fireEvent.press(getByTestId('export-data-button'));

      await waitFor(() => {
        expect(getByText('Data export ready')).toBeTruthy();
        expect(mockApiClient.get).toHaveBeenCalledWith(
          expect.stringContaining('/analytics/export')
        );
      });
    });

    it('should generate personalized insights from historical data', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/analytics/insights')) {
          return Promise.resolve({
            data: {
              insights: [
                {
                  type: 'cost_saving',
                  message: 'You saved ~$127 this month by cooking at home',
                  calculation: 'Based on 42 home-cooked meals vs restaurant average'
                },
                {
                  type: 'health_improvement',
                  message: 'Your veggie intake increased 23% over last month',
                  supporting_data: 'More salads and stir-fries in history'
                },
                {
                  type: 'efficiency_gain',
                  message: 'Average cooking time decreased from 45 to 35 minutes',
                  trend: 'improving'
                }
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
        // Show personalized insights
        expect(getByText('You saved ~$127 this month')).toBeTruthy();
        expect(getByText('Veggie intake +23%')).toBeTruthy();
      });
    });
  });
});