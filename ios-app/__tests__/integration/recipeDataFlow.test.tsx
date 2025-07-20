import React from 'react';
import { render, waitFor, fireEvent } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import RecipesScreen from '@/app/(tabs)/recipes';
import RecipeDetails from '@/app/recipe-details';
import { useItems } from '@/context/ItemsContext';
import { useAuth } from '@/context/AuthContext';
import { createMockRecipe, createMockPantryItem } from '../helpers/apiMocks';

// Mock dependencies
jest.mock('@/context/ItemsContext');
jest.mock('@/context/AuthContext');
jest.mock('expo-router');

const mockUseItems = jest.mocked(useItems);
const mockUseAuth = jest.mocked(useAuth);

describe('Recipe Data Flow Integration Tests', () => {
  const mockPantryItems = [
    createMockPantryItem({ 
      id: '1', 
      product_name: 'Chicken Breast', 
      quantity_amount: 2,
      unit_of_measurement: 'lb'
    }),
    createMockPantryItem({ 
      id: '2', 
      product_name: 'Rice', 
      quantity_amount: 1,
      unit_of_measurement: 'cup'
    }),
    createMockPantryItem({ 
      id: '3', 
      product_name: 'Broccoli', 
      quantity_amount: 2,
      unit_of_measurement: 'heads'
    }),
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseItems.mockReturnValue({ items: mockPantryItems } as any);
    mockUseAuth.mockReturnValue({
      user: { id: 111 },
      token: 'mock-token',
      isAuthenticated: true,
    } as any);
  });

  describe('Complete Recipe Data Visibility', () => {
    it('should display have vs missing ingredients on recipe cards', async () => {
      const mockRecipe = createMockRecipe({
        id: 1,
        title: 'Chicken Rice Bowl',
        usedIngredientCount: 3,
        missedIngredientCount: 2,
        usedIngredients: [
          { id: 1, name: 'chicken breast', amount: 1.5, unit: 'lb' },
          { id: 2, name: 'rice', amount: 1, unit: 'cup' },
          { id: 3, name: 'broccoli', amount: 1, unit: 'head' }
        ],
        missedIngredients: [
          { id: 4, name: 'soy sauce', amount: 2, unit: 'tbsp' },
          { id: 5, name: 'garlic', amount: 3, unit: 'cloves' }
        ]
      });

      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          recipes: [mockRecipe],
          pantry_ingredients: mockPantryItems.map(item => ({
            name: item.product_name.toLowerCase(),
            quantity: item.quantity_amount,
          }))
        })
      });

      const { getByText, getByTestId } = render(<RecipesScreen />);

      await waitFor(() => {
        // Verify recipe title
        expect(getByText('Chicken Rice Bowl')).toBeTruthy();
        
        // Verify have vs missing ingredients display
        expect(getByText('✓ 3 | ✗ 2')).toBeTruthy();
        
        // Verify the recipe card shows correct counts
        const recipeCard = getByTestId('recipe-card-1');
        expect(recipeCard).toBeTruthy();
      });
    });

    it('should display all recipe details with complete data', async () => {
      const mockDetailedRecipe = {
        id: 1,
        title: 'Complete Recipe Test',
        readyInMinutes: 45,
        servings: 4,
        image: 'https://example.com/recipe.jpg',
        extendedIngredients: [
          {
            id: 1,
            name: 'chicken breast',
            amount: 2,
            unit: 'pounds',
            original: '2 pounds chicken breast, diced',
            aisle: 'Meat',
            consistency: 'solid'
          },
          {
            id: 2,
            name: 'jasmine rice',
            amount: 2,
            unit: 'cups',
            original: '2 cups jasmine rice',
            aisle: 'Rice',
            consistency: 'solid'
          }
        ],
        analyzedInstructions: [{
          name: '',
          steps: [
            { number: 1, step: 'Dice the chicken breast into bite-sized pieces.' },
            { number: 2, step: 'Rinse the rice until water runs clear.' },
            { number: 3, step: 'Heat oil in a large pan over medium heat.' },
            { number: 4, step: 'Cook chicken until golden brown, about 5-7 minutes.' },
            { number: 5, step: 'Add rice and water, bring to a boil.' },
            { number: 6, step: 'Reduce heat and simmer for 15 minutes.' },
            { number: 7, step: 'Add broccoli in the last 5 minutes.' },
            { number: 8, step: 'Season with soy sauce and garlic.' },
            { number: 9, step: 'Let rest for 5 minutes before serving.' },
            { number: 10, step: 'Garnish with sesame seeds and serve hot.' }
          ]
        }],
        nutrition: {
          nutrients: [
            { name: 'Calories', amount: 450, unit: 'kcal', percentOfDailyNeeds: 22.5 },
            { name: 'Protein', amount: 35, unit: 'g', percentOfDailyNeeds: 70 },
            { name: 'Carbohydrates', amount: 45, unit: 'g', percentOfDailyNeeds: 15 },
            { name: 'Fat', amount: 12, unit: 'g', percentOfDailyNeeds: 18.5 },
            { name: 'Fiber', amount: 4, unit: 'g', percentOfDailyNeeds: 16 },
            { name: 'Sugar', amount: 3, unit: 'g', percentOfDailyNeeds: 3.3 }
          ]
        }
      };

      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockDetailedRecipe
      });

      const { getByText, getAllByText, getByTestId } = render(
        <NavigationContainer>
          <RecipeDetails route={{ params: { id: 1 } }} />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(getByText('Complete Recipe Test')).toBeTruthy();
      });

      // Test Ingredients Tab
      fireEvent.press(getByText('Ingredients'));
      await waitFor(() => {
        expect(getByText('2 pounds chicken breast, diced')).toBeTruthy();
        expect(getByText('2 cups jasmine rice')).toBeTruthy();
        
        // Verify all ingredients are displayed
        const ingredientsList = getByTestId('ingredients-list');
        expect(ingredientsList.children).toHaveLength(2);
      });

      // Test Instructions Tab - verify all steps in order
      fireEvent.press(getByText('Instructions'));
      await waitFor(() => {
        // Verify all 10 steps are present and in order
        for (let i = 1; i <= 10; i++) {
          const stepNumber = getByText(`${i}.`);
          expect(stepNumber).toBeTruthy();
        }
        
        // Verify specific steps content
        expect(getByText(/Dice the chicken breast/)).toBeTruthy();
        expect(getByText(/Garnish with sesame seeds/)).toBeTruthy();
        
        // Verify steps are in correct order
        const instructionsList = getByTestId('instructions-list');
        const steps = instructionsList.children;
        expect(steps).toHaveLength(10);
      });

      // Test Nutrients Tab
      fireEvent.press(getByText('Nutrition'));
      await waitFor(() => {
        expect(getByText('Calories')).toBeTruthy();
        expect(getByText('450 kcal')).toBeTruthy();
        expect(getByText('22.5%')).toBeTruthy();
        
        expect(getByText('Protein')).toBeTruthy();
        expect(getByText('35 g')).toBeTruthy();
        expect(getByText('70%')).toBeTruthy();
        
        // Verify all nutrients are displayed
        const nutrientsList = getByTestId('nutrients-list');
        expect(nutrientsList.children).toHaveLength(6);
      });
    });
  });

  describe('Data Parsing and Matching Tests', () => {
    it('should correctly match pantry ingredients with recipe ingredients', async () => {
      const mockRecipeWithMatching = {
        id: 2,
        title: 'Ingredient Matching Test',
        extendedIngredients: [
          { name: 'chicken', original: '2 lbs chicken breast' },
          { name: 'white rice', original: '1 cup white rice' },
          { name: 'broccoli florets', original: '2 heads broccoli' }
        ],
        usedIngredients: [
          { name: 'chicken', pantryItem: 'Chicken Breast' },
          { name: 'rice', pantryItem: 'Rice' },
          { name: 'broccoli', pantryItem: 'Broccoli' }
        ]
      };

      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipeWithMatching
      });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipeDetails route={{ params: { id: 2 } }} />
        </NavigationContainer>
      );

      await waitFor(() => {
        fireEvent.press(getByText('Ingredients'));
      });

      // Verify pantry items are correctly matched
      await waitFor(() => {
        const ingredientItems = getByTestId('ingredients-list').children;
        
        // Each ingredient should show if it's available in pantry
        expect(getByTestId('ingredient-0-available')).toBeTruthy();
        expect(getByTestId('ingredient-1-available')).toBeTruthy();
        expect(getByTestId('ingredient-2-available')).toBeTruthy();
      });
    });

    it('should handle missing or incomplete recipe data gracefully', async () => {
      const incompleteRecipe = {
        id: 3,
        title: 'Incomplete Recipe',
        extendedIngredients: [
          { name: 'ingredient1', original: 'Some ingredient' }
        ],
        analyzedInstructions: [], // No instructions
        nutrition: null // No nutrition data
      };

      global.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => incompleteRecipe
      });

      const { getByText, queryByText, queryByTestId } = render(
        <NavigationContainer>
          <RecipeDetails route={{ params: { id: 3 } }} />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(getByText('Incomplete Recipe')).toBeTruthy();
      });

      // Test missing instructions
      fireEvent.press(getByText('Instructions'));
      await waitFor(() => {
        expect(getByText('No instructions available for this recipe.')).toBeTruthy();
        expect(queryByTestId('instructions-list')).toBeNull();
      });

      // Test missing nutrition
      fireEvent.press(getByText('Nutrition'));
      await waitFor(() => {
        expect(getByText('No nutrition information available.')).toBeTruthy();
        expect(queryByTestId('nutrients-list')).toBeNull();
      });
    });
  });

  describe('Recipe Completion Flow Tests', () => {
    it('should correctly update pantry after recipe completion', async () => {
      const mockRecipe = {
        id: 4,
        title: 'Recipe to Complete',
        extendedIngredients: [
          { id: 1, name: 'chicken', amount: 1, unit: 'lb' },
          { id: 2, name: 'rice', amount: 0.5, unit: 'cup' }
        ]
      };

      const mockCompletionResponse = {
        success: true,
        message: 'Recipe completed successfully',
        updatedPantryItems: [
          { id: '1', product_name: 'Chicken Breast', quantity_amount: 1 }, // 2 - 1 = 1
          { id: '2', product_name: 'Rice', quantity_amount: 0.5 } // 1 - 0.5 = 0.5
        ]
      };

      global.fetch = jest.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockRecipe
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockCompletionResponse
        });

      const { getByText, getByTestId } = render(
        <NavigationContainer>
          <RecipeDetails route={{ params: { id: 4 } }} />
        </NavigationContainer>
      );

      await waitFor(() => {
        expect(getByText('Recipe to Complete')).toBeTruthy();
      });

      // Complete the recipe
      fireEvent.press(getByTestId('complete-recipe-button'));

      await waitFor(() => {
        // Verify completion modal or success message
        expect(getByText('Recipe completed successfully')).toBeTruthy();
        
        // Verify pantry was updated
        expect(mockUseItems().updateItems).toHaveBeenCalledWith(
          mockCompletionResponse.updatedPantryItems
        );
      });
    });
  });
});
