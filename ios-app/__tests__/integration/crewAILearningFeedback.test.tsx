// crewAILearningFeedback.test.tsx
// Test suite for verifying CrewAI learning from user consumption patterns and feedback

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import RecipesScreen from '../../screens/RecipesScreen';
import RecipeCompletionModal from '../../components/modals/RecipeCompletionModal';
import { apiClient } from '../../services/apiClient';

// Mock the services
jest.mock('../../services/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn()
  }
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('CrewAI Learning Feedback Loop', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Recipe Recommendation Feedback Collection', () => {
    it('should track which AI-recommended recipes were actually cooked', async () => {
      const aiRecommendations = [
        {
          recipe_id: 101,
          title: 'Veggie Stir Fry',
          ai_score: 0.92,
          recommendation_id: 'rec_abc123',
          reasoning: ['Uses expiring vegetables', 'Matches quick meal preference']
        },
        {
          recipe_id: 102,
          title: 'Pasta Primavera',
          ai_score: 0.88,
          recommendation_id: 'rec_def456',
          reasoning: ['Italian cuisine preference', 'All ingredients available']
        }
      ];

      // User cooks the AI-recommended recipe
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/feedback/recipe-selected')) {
          expect(data).toEqual({
            recommendation_id: 'rec_abc123',
            recipe_id: 101,
            action: 'cooked',
            time_to_selection: expect.any(Number), // milliseconds since recommendation
            context: {
              time_of_day: 'evening',
              day_of_week: 'wednesday',
              pantry_match_score: 0.95
            }
          });

          return Promise.resolve({
            data: {
              feedback_recorded: true,
              learning_impact: {
                factor_weights_updated: [
                  'expiring_items_priority: +0.05',
                  'evening_quick_meals: +0.03'
                ]
              }
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

      // Show AI recommendations
      await waitFor(() => {
        expect(getByTestId('ai-badge-101')).toBeTruthy();
        expect(getByText('AI Recommended')).toBeTruthy();
      });

      // User selects AI-recommended recipe
      fireEvent.press(getByText('Veggie Stir Fry'));

      // Track the selection
      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith(
          expect.stringContaining('/ai/feedback/recipe-selected'),
          expect.objectContaining({
            recommendation_id: 'rec_abc123',
            action: 'cooked'
          })
        );
      });
    });

    it('should collect detailed feedback after recipe completion', async () => {
      const completedRecipe = {
        id: 101,
        title: 'Veggie Stir Fry',
        recommendation_id: 'rec_abc123'
      };

      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/feedback/recipe-completed')) {
          expect(data).toEqual({
            recommendation_id: 'rec_abc123',
            recipe_id: 101,
            feedback: {
              rating: 4,
              difficulty_actual_vs_expected: 'easier',
              time_actual_vs_expected: 'longer',
              would_make_again: true,
              modifications: [
                {
                  type: 'ingredient_substitution',
                  original: 'soy sauce',
                  substituted: 'tamari',
                  reason: 'gluten_free'
                }
              ],
              taste_profile: {
                sweetness: 3,
                saltiness: 4,
                spiciness: 2,
                satisfaction: 4
              }
            },
            context: {
              cooking_duration_actual: 25,
              cooking_duration_expected: 20,
              servings_made: 4,
              leftovers: true
            }
          });

          return Promise.resolve({
            data: {
              learning_updates: {
                user_preferences_refined: [
                  'gluten_free_preference: detected',
                  'cooking_time_tolerance: +5min acceptable',
                  'prefers_easier_recipes: true'
                ],
                recommendation_accuracy: 0.85
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const onClose = jest.fn();
      const { getByText, getByTestId, getAllByTestId } = render(
        <RecipeCompletionModal
          visible={true}
          recipe={completedRecipe}
          onClose={onClose}
        />
      );

      // User provides feedback
      // Rate the recipe
      const stars = getAllByTestId(/star-/);
      fireEvent.press(stars[3]); // 4 stars

      // Difficulty feedback
      fireEvent.press(getByText('Easier than expected'));

      // Time feedback
      fireEvent.press(getByText('Took longer'));

      // Would make again
      fireEvent.press(getByTestId('would-make-again-yes'));

      // Submit feedback
      fireEvent.press(getByText('Submit Feedback'));

      await waitFor(() => {
        expect(mockApiClient.post).toHaveBeenCalledWith(
          expect.stringContaining('/ai/feedback/recipe-completed'),
          expect.objectContaining({
            feedback: expect.objectContaining({
              rating: 4,
              would_make_again: true
            })
          })
        );
      });
    });

    it('should track recipe abandonment for negative training', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/feedback/recipe-abandoned')) {
          expect(data).toEqual({
            recipe_id: 103,
            recommendation_id: 'rec_ghi789',
            abandonment_reason: 'too_complex',
            abandoned_at_step: 3,
            total_steps: 12,
            time_spent_minutes: 15,
            specific_issues: [
              'missing_equipment',
              'unclear_instructions'
            ],
            user_comment: 'Need a food processor for step 3'
          });

          return Promise.resolve({
            data: {
              learning_impact: {
                complexity_threshold_adjusted: true,
                equipment_requirements_noted: ['food_processor'],
                instruction_clarity_flag: true
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // User abandons recipe
      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      // Simulate abandonment flow
      await act(async () => {
        await mockApiClient.post('/ai/feedback/recipe-abandoned', {
          recipe_id: 103,
          recommendation_id: 'rec_ghi789',
          abandonment_reason: 'too_complex',
          abandoned_at_step: 3,
          total_steps: 12,
          time_spent_minutes: 15,
          specific_issues: ['missing_equipment', 'unclear_instructions'],
          user_comment: 'Need a food processor for step 3'
        });
      });

      // Verify negative feedback was recorded
      expect(mockApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('recipe-abandoned'),
        expect.objectContaining({
          abandonment_reason: 'too_complex'
        })
      );
    });
  });

  describe('Preference Learning and Model Updates', () => {
    it('should detect and learn cuisine preferences from patterns', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/ai/learning/patterns')) {
          return Promise.resolve({
            data: {
              detected_patterns: [
                {
                  pattern_type: 'cuisine_preference',
                  confidence: 0.87,
                  insight: 'Strong preference for Asian cuisine on weekdays',
                  data_points: 24,
                  recommendations: [
                    'Increase Asian recipe weight by 20% on weekdays',
                    'Suggest meal prep Asian dishes on Sundays'
                  ]
                },
                {
                  pattern_type: 'ingredient_avoidance',
                  confidence: 0.92,
                  insight: 'Consistently avoids mushrooms',
                  data_points: 15,
                  recommendations: [
                    'Exclude mushroom recipes from recommendations',
                    'Suggest mushroom substitutes when applicable'
                  ]
                }
              ],
              model_updates_pending: 2
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      await waitFor(() => {
        // AI should show it's learning
        const learningIndicator = getByText('AI is learning your preferences');
        expect(learningIndicator).toBeTruthy();
      });

      // Check pattern detection
      const patterns = await mockApiClient.get('/ai/learning/patterns');
      expect(patterns.data.detected_patterns).toHaveLength(2);
      expect(patterns.data.detected_patterns[0].confidence).toBe(0.87);
    });

    it('should adapt recommendations based on time and context patterns', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/contextual-recommendations')) {
          // AI should use learned context
          expect(data.context).toEqual({
            time_of_day: 'evening',
            day_of_week: 'wednesday',
            weather: 'rainy',
            recent_meals: expect.any(Array),
            energy_level: 'low', // inferred from quick meal selections
            learned_patterns: {
              wednesday_evening: 'prefers_quick_asian',
              rainy_day: 'comfort_food_preference'
            }
          });

          return Promise.resolve({
            data: {
              recommendations: [
                {
                  recipe_id: 201,
                  title: 'Quick Ramen Bowl',
                  confidence: 0.94,
                  reasoning: [
                    'Wednesday evening quick Asian preference',
                    'Comfort food for rainy weather',
                    'Low energy = minimal prep time'
                  ]
                }
              ]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Request context-aware recommendations
      await act(async () => {
        await mockApiClient.post('/ai/contextual-recommendations', {
          context: {
            time_of_day: 'evening',
            day_of_week: 'wednesday',
            weather: 'rainy',
            recent_meals: ['Sandwich', 'Salad'],
            energy_level: 'low',
            learned_patterns: {
              wednesday_evening: 'prefers_quick_asian',
              rainy_day: 'comfort_food_preference'
            }
          }
        });
      });

      // Verify context was considered
      expect(mockApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('contextual-recommendations'),
        expect.objectContaining({
          context: expect.objectContaining({
            learned_patterns: expect.any(Object)
          })
        })
      );
    });

    it('should improve portion size predictions based on leftovers data', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/learning/portions')) {
          expect(data).toEqual({
            recipe_id: 101,
            servings_made: 4,
            servings_consumed: 2.5,
            leftovers: true,
            household_size: 2,
            meal_type: 'dinner'
          });

          return Promise.resolve({
            data: {
              learning_update: {
                portion_adjustment: {
                  recipe_101: 'reduce_by_25_percent',
                  general_dinner: 'household_typically_needs_3_servings'
                },
                confidence: 0.78,
                data_points: 12
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Track leftover patterns
      await act(async () => {
        await mockApiClient.post('/ai/learning/portions', {
          recipe_id: 101,
          servings_made: 4,
          servings_consumed: 2.5,
          leftovers: true,
          household_size: 2,
          meal_type: 'dinner'
        });
      });

      // Future recommendations should adjust portions
      mockApiClient.post.mockImplementation((url) => {
        if (url.includes('/ai/recommendations')) {
          return Promise.resolve({
            data: {
              recommendations: [{
                recipe_id: 101,
                adjusted_servings: 3, // Down from default 4
                adjustment_reason: 'Based on your typical consumption'
              }]
            }
          });
        }
        return Promise.resolve({ data: {} });
      });
    });
  });

  describe('Continuous Improvement Metrics', () => {
    it('should track AI recommendation accuracy over time', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/ai/metrics/accuracy')) {
          return Promise.resolve({
            data: {
              accuracy_trend: [
                { week: 1, accuracy: 0.65, recommendations: 20 },
                { week: 2, accuracy: 0.72, recommendations: 25 },
                { week: 3, accuracy: 0.78, recommendations: 22 },
                { week: 4, accuracy: 0.83, recommendations: 28 }
              ],
              current_accuracy: 0.83,
              improvement: '+27.7%',
              factors_improved: [
                'cuisine_matching: +15%',
                'cooking_time_prediction: +20%',
                'ingredient_preference: +35%'
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

      // Show AI performance
      fireEvent.press(getByTestId('ai-insights-button'));

      await waitFor(() => {
        expect(getByText('AI Performance')).toBeTruthy();
        expect(getByText('83% Recommendation Accuracy')).toBeTruthy();
        expect(getByText('+27.7% improvement')).toBeTruthy();
      });
    });

    it('should identify and correct recommendation biases', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/ai/bias-detection')) {
          return Promise.resolve({
            data: {
              detected_biases: [
                {
                  bias_type: 'cuisine_overrepresentation',
                  description: 'Italian recipes recommended 40% more than user selection rate',
                  correction_applied: true,
                  adjustment: 'Reduced Italian recipe weight by 15%'
                },
                {
                  bias_type: 'complexity_mismatch',
                  description: 'Complex recipes recommended despite 80% quick meal preference',
                  correction_applied: true,
                  adjustment: 'Increased quick meal weight to 0.8'
                }
              ],
              bias_correction_impact: {
                before_correction_accuracy: 0.71,
                after_correction_accuracy: 0.83,
                user_satisfaction_increase: '+22%'
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const biasReport = await mockApiClient.get('/ai/bias-detection');
      
      expect(biasReport.data.detected_biases).toHaveLength(2);
      expect(biasReport.data.bias_correction_impact.user_satisfaction_increase).toBe('+22%');
    });

    it('should learn from cross-user patterns while maintaining privacy', async () => {
      mockApiClient.get.mockImplementation((url) => {
        if (url.includes('/ai/collective-learning')) {
          return Promise.resolve({
            data: {
              collective_insights: [
                {
                  insight: 'Users who like Recipe A also enjoy Recipe B 73% of the time',
                  applicable_to_user: true,
                  confidence: 0.73,
                  based_on_users: 156 // anonymized count
                },
                {
                  insight: 'Sunday meal prep reduces weekly food waste by 32%',
                  pattern_strength: 0.84,
                  recommendation: 'Suggest meal prep recipes on Saturdays'
                }
              ],
              privacy_preserved: true,
              learning_method: 'federated_aggregation'
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const insights = await mockApiClient.get('/ai/collective-learning');
      
      expect(insights.data.privacy_preserved).toBe(true);
      expect(insights.data.collective_insights[0].confidence).toBe(0.73);
    });
  });

  describe('Real-time Adaptation', () => {
    it('should immediately adjust recommendations based on feedback', async () => {
      // User gives negative feedback
      mockApiClient.post.mockImplementationOnce((url, data) => {
        if (url.includes('/ai/feedback/immediate')) {
          expect(data).toEqual({
            recipe_id: 301,
            feedback_type: 'dislike',
            reason: 'too_spicy',
            intensity: 'strong'
          });

          return Promise.resolve({
            data: {
              immediate_adjustments: {
                spice_preference: 'reduced to mild',
                similar_recipes_removed: 3,
                filter_applied: 'spice_level <= 2'
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      const { getByText, queryByText } = render(
        <NavigationContainer>
          <RecipesScreen />
        </NavigationContainer>
      );

      // User indicates dislike
      await act(async () => {
        await mockApiClient.post('/ai/feedback/immediate', {
          recipe_id: 301,
          feedback_type: 'dislike',
          reason: 'too_spicy',
          intensity: 'strong'
        });
      });

      // Recommendations should update immediately
      mockApiClient.get.mockImplementationOnce((url) => {
        if (url.includes('/recipes')) {
          return Promise.resolve({
            data: [
              { id: 401, title: 'Mild Curry', spice_level: 1 },
              { id: 402, title: 'Creamy Pasta', spice_level: 0 }
              // No spicy recipes
            ]
          });
        }
        return Promise.resolve({ data: {} });
      });

      // Refresh recipes
      fireEvent.press(getByText('Refresh'));

      await waitFor(() => {
        expect(queryByText('Spicy')).toBeFalsy();
        expect(getByText('Mild Curry')).toBeTruthy();
      });
    });

    it('should personalize explanation style based on user interaction', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/interaction-learning')) {
          expect(data).toEqual({
            interaction_type: 'expanded_reasoning',
            recipe_id: 201,
            user_action: 'read_full_explanation',
            time_spent: 15 // seconds
          });

          return Promise.resolve({
            data: {
              preference_noted: 'user_prefers_detailed_explanations',
              future_behavior: 'provide_comprehensive_reasoning'
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

      // User expands AI reasoning
      fireEvent.press(getByTestId('expand-reasoning-201'));

      // Track interaction
      await act(async () => {
        await mockApiClient.post('/ai/interaction-learning', {
          interaction_type: 'expanded_reasoning',
          recipe_id: 201,
          user_action: 'read_full_explanation',
          time_spent: 15
        });
      });

      // Future recommendations should have detailed explanations
      expect(mockApiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('interaction-learning'),
        expect.objectContaining({
          user_action: 'read_full_explanation'
        })
      );
    });

    it('should create personalized recipe variations based on modifications', async () => {
      mockApiClient.post.mockImplementation((url, data) => {
        if (url.includes('/ai/recipe-variations')) {
          expect(data.modification_history).toEqual([
            {
              recipe_id: 101,
              modifications: [
                { type: 'reduce_oil', amount: '50%' },
                { type: 'add_vegetable', item: 'bell peppers' }
              ]
            },
            {
              recipe_id: 102,
              modifications: [
                { type: 'reduce_oil', amount: '30%' }
              ]
            }
          ]);

          return Promise.resolve({
            data: {
              personalized_variation: {
                base_recipe_id: 103,
                title: 'Stir Fry (Your Way)',
                auto_modifications: [
                  'Oil reduced by 40%',
                  'Added bell peppers',
                  'Adjusted cooking time'
                ],
                confidence: 0.85
              }
            }
          });
        }
        return Promise.resolve({ data: {} });
      });

      // AI creates personalized version
      const variation = await mockApiClient.post('/ai/recipe-variations', {
        modification_history: [
          {
            recipe_id: 101,
            modifications: [
              { type: 'reduce_oil', amount: '50%' },
              { type: 'add_vegetable', item: 'bell peppers' }
            ]
          },
          {
            recipe_id: 102,
            modifications: [
              { type: 'reduce_oil', amount: '30%' }
            ]
          }
        ]
      });

      expect(variation.data.personalized_variation.auto_modifications).toContain(
        'Oil reduced by 40%'
      );
    });
  });
});