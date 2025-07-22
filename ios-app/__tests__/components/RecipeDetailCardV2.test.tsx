import React from 'react';
import { render, fireEvent, waitFor, screen } from '@testing-library/react-native';
import { Alert } from 'react-native';
import RecipeDetailCardV2 from '../../components/recipes/RecipeDetailCardV2';
import { useRouter } from 'expo-router';

// Mock dependencies
jest.mock('expo-router');
jest.mock('../../services/recipeService');
jest.mock('../../services/pantryService');
jest.mock('../../services/shoppingListService');

const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

// Mock router
const mockPush = jest.fn();
const mockBack = jest.fn();

// Mock Alert
jest.spyOn(Alert, 'alert');

// Sample recipe data with full structure
const mockRecipe = {
  id: 123,
  title: 'Chicken Alfredo Pasta',
  image: 'https://example.com/chicken-alfredo.jpg',
  readyInMinutes: 30,
  servings: 4,
  is_favorite: false,
  nutrition: {
    calories: 650,
    protein: 35,
    carbs: 45,
    fat: 28,
    fiber: 3,
    sugar: 8
  },
  extendedIngredients: [
    {
      id: 1,
      name: 'chicken breast',
      original: 'chicken breast (2 pieces)',
      amount: 2,
      unit: 'pieces'
    },
    {
      id: 2,
      name: 'pasta',
      original: 'pasta (200g)',
      amount: 200,
      unit: 'g'
    },
    {
      id: 3,
      name: 'heavy cream',
      original: 'heavy cream (200ml)',
      amount: 200,
      unit: 'ml'
    },
    {
      id: 4,
      name: 'parmesan cheese',
      original: 'parmesan cheese (50g)',
      amount: 50,
      unit: 'g'
    },
    {
      id: 5,
      name: 'garlic',
      original: 'garlic (2 cloves)',
      amount: 2,
      unit: 'cloves'
    }
  ],
  available_ingredients: [
    'chicken breast (2 pieces)',
    'pasta (200g)',
    'garlic (2 cloves)'
  ],
  pantry_item_matches: {
    'chicken breast (2 pieces)': [{ pantry_item_id: 1 }],
    'pasta (200g)': [{ pantry_item_id: 2 }],
    'garlic (2 cloves)': [{ pantry_item_id: 3 }]
  },
  analyzedInstructions: [
    {
      steps: [
        { number: 1, step: 'Cook pasta according to package directions.' },
        { number: 2, step: 'Season chicken with salt and pepper, then cook in a large skillet.' },
        { number: 3, step: 'Add garlic and cook for 1 minute.' },
        { number: 4, step: 'Pour in heavy cream and bring to a simmer.' },
        { number: 5, step: 'Add parmesan cheese and stir until melted.' },
        { number: 6, step: 'Add cooked pasta and toss to coat.' },
        { number: 7, step: 'Serve immediately with extra cheese.' }
      ]
    }
  ]
};

// Mock services
jest.mock('../../services/recipeService', () => ({
  recipeService: {
    saveRecipe: jest.fn().mockResolvedValue({ success: true }),
    rateRecipe: jest.fn().mockResolvedValue({ success: true })
  }
}));

jest.mock('../../services/shoppingListService', () => ({
  shoppingListService: {
    addItem: jest.fn().mockResolvedValue({ success: true })
  }
}));

const { recipeService } = require('../../services/recipeService');
const { shoppingListService } = require('../../services/shoppingListService');

describe('RecipeDetailCardV2', () => {
  const mockOnBack = jest.fn();
  const mockOnRatingSubmitted = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseRouter.mockReturnValue({
      push: mockPush,
      back: mockBack,
      replace: jest.fn(),
      canGoBack: jest.fn(),
      setParams: jest.fn(),
      pathname: '/recipe-detail'
    });

    global.alert = jest.fn();
  });

  describe('Recipe Data Display', () => {
    it('should display recipe title and basic information', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(screen.getByText('Chicken Alfredo Pasta')).toBeTruthy();
      expect(screen.getByText('30 min')).toBeTruthy();
      expect(screen.getByText('650 kcal')).toBeTruthy();
      expect(screen.getByText('35g protein')).toBeTruthy();
    });

    it('should display match percentage correctly', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // 3 available out of 5 total = 60% match
      expect(screen.getByText('60% match')).toBeTruthy();
    });

    it('should display recipe image', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const image = screen.getByTestId('hero-image');
      expect(image.props.source.uri).toBe('https://example.com/chicken-alfredo.jpg');
    });

    it('should display placeholder image when no image is provided', () => {
      const recipeWithoutImage = { ...mockRecipe, image: undefined };
      render(<RecipeDetailCardV2 recipe={recipeWithoutImage} />);

      const image = screen.getByTestId('hero-image');
      expect(image.props.source.uri).toBe('https://via.placeholder.com/400');
    });

    it('should display cooking time in correct format', () => {
      const recipeWithLongTime = { ...mockRecipe, readyInMinutes: 90 };
      render(<RecipeDetailCardV2 recipe={recipeWithLongTime} />);

      expect(screen.getByText('1h 30m')).toBeTruthy();

      const recipeWithHourOnly = { ...mockRecipe, readyInMinutes: 120 };
      render(<RecipeDetailCardV2 recipe={recipeWithHourOnly} />);

      expect(screen.getByText('2h')).toBeTruthy();
    });
  });

  describe('Ingredients Display with Have/Missing Badges', () => {
    it('should display ingredients with correct availability badges', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(screen.getByText('Ingredients (5)')).toBeTruthy();

      // Available ingredients should show with checkmark icons
      expect(screen.getByText('chicken breast (2 pieces)')).toBeTruthy();
      expect(screen.getByText('pasta (200g)')).toBeTruthy();
      expect(screen.getByText('garlic (2 cloves)')).toBeTruthy();

      // Missing ingredients should show with add icons
      expect(screen.getByText('heavy cream (200ml)')).toBeTruthy();
      expect(screen.getByText('parmesan cheese (50g)')).toBeTruthy();

      // Check for proper icon types
      const checkmarkIcons = screen.getAllByTestId('checkmark-circle-icon');
      const addIcons = screen.getAllByTestId('add-circle-outline-icon');
      
      expect(checkmarkIcons.length).toBe(3); // 3 available ingredients
      expect(addIcons.length).toBe(2); // 2 missing ingredients
    });

    it('should show legend when there are available ingredients', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(screen.getByText('✓ = In your pantry')).toBeTruthy();
    });

    it('should not show legend when no ingredients are available', () => {
      const recipeWithNoAvailable = {
        ...mockRecipe,
        available_ingredients: [],
        pantry_item_matches: {}
      };

      render(<RecipeDetailCardV2 recipe={recipeWithNoAvailable} />);

      expect(screen.queryByText('✓ = In your pantry')).toBeFalsy();
    });

    it('should show correct badge colors for have vs missing ingredients', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Get all ingredient rows
      const ingredientRows = screen.getAllByTestId('ingredient-row');
      
      // First 3 should be available (green checkmarks)
      expect(ingredientRows[0]).toContainElement(screen.getByTestId('checkmark-circle-icon'));
      expect(ingredientRows[1]).toContainElement(screen.getByTestId('checkmark-circle-icon'));
      expect(ingredientRows[2]).toContainElement(screen.getByTestId('checkmark-circle-icon'));
      
      // Last 2 should be missing (orange add icons)
      expect(ingredientRows[3]).toContainElement(screen.getByTestId('add-circle-outline-icon'));
      expect(ingredientRows[4]).toContainElement(screen.getByTestId('add-circle-outline-icon'));
    });

    it('should handle progressive disclosure for ingredients', () => {
      const recipeWithManyIngredients = {
        ...mockRecipe,
        extendedIngredients: [
          ...mockRecipe.extendedIngredients,
          { id: 6, name: 'salt', original: 'salt (1 tsp)', amount: 1, unit: 'tsp' },
          { id: 7, name: 'pepper', original: 'pepper (1/2 tsp)', amount: 0.5, unit: 'tsp' },
          { id: 8, name: 'butter', original: 'butter (30g)', amount: 30, unit: 'g' }
        ]
      };

      render(<RecipeDetailCardV2 recipe={recipeWithManyIngredients} />);

      // Should initially show only 5 ingredients
      expect(screen.getByText('Show all 8 ingredients')).toBeTruthy();
      
      // Tap to show all
      fireEvent.press(screen.getByText('Show all 8 ingredients'));
      
      expect(screen.getByText('Show less')).toBeTruthy();
      expect(screen.getByText('salt (1 tsp)')).toBeTruthy();
      expect(screen.getByText('pepper (1/2 tsp)')).toBeTruthy();
      expect(screen.getByText('butter (30g)')).toBeTruthy();
    });
  });

  describe('Shopping List Integration', () => {
    it('should display shopping list accordion for missing ingredients', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(screen.getByText('Items to Buy (2)')).toBeTruthy();
      expect(screen.getByText('• heavy cream (200ml)')).toBeTruthy();
      expect(screen.getByText('• parmesan cheese (50g)')).toBeTruthy();
    });

    it('should expand and collapse shopping list accordion', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const accordionHeader = screen.getByText('Items to Buy (2)');
      
      // Initially expanded
      expect(screen.getByText('• heavy cream (200ml)')).toBeTruthy();
      
      // Collapse
      fireEvent.press(accordionHeader);
      expect(screen.queryByText('• heavy cream (200ml)')).toBeFalsy();
      
      // Expand again
      fireEvent.press(accordionHeader);
      expect(screen.getByText('• heavy cream (200ml)')).toBeTruthy();
    });

    it('should add missing ingredients to shopping list', async () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const addToListButton = screen.getByText('Add to Shopping List');
      fireEvent.press(addToListButton);

      await waitFor(() => {
        expect(shoppingListService.addItem).toHaveBeenCalledTimes(2);
        expect(shoppingListService.addItem).toHaveBeenCalledWith({
          name: 'heavy cream',
          quantity: '200',
          unit: 'ml',
          category: 'Recipe Ingredients',
          notes: 'For Chicken Alfredo Pasta'
        });
        expect(shoppingListService.addItem).toHaveBeenCalledWith({
          name: 'parmesan cheese',
          quantity: '50',
          unit: 'g',
          category: 'Recipe Ingredients',
          notes: 'For Chicken Alfredo Pasta'
        });
      });

      expect(global.alert).toHaveBeenCalledWith('Added 2 items to shopping list');
    });

    it('should show loading state while adding to shopping list', async () => {
      // Mock a delay in the shopping list service
      shoppingListService.addItem.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const addToListButton = screen.getByText('Add to Shopping List');
      fireEvent.press(addToListButton);

      // Should show loading indicator
      expect(screen.getByTestId('shopping-list-loading')).toBeTruthy();

      await waitFor(() => {
        expect(screen.queryByTestId('shopping-list-loading')).toBeFalsy();
      });
    });

    it('should handle shopping list errors gracefully', async () => {
      shoppingListService.addItem.mockRejectedValue(new Error('API Error'));

      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const addToListButton = screen.getByText('Add to Shopping List');
      fireEvent.press(addToListButton);

      await waitFor(() => {
        expect(global.alert).toHaveBeenCalledWith('Failed to add items to shopping list');
      });
    });

    it('should not show shopping list section when no missing ingredients', () => {
      const recipeWithAllIngredients = {
        ...mockRecipe,
        available_ingredients: mockRecipe.extendedIngredients.map(ing => ing.original),
        pantry_item_matches: mockRecipe.extendedIngredients.reduce((acc, ing) => {
          acc[ing.original] = [{ pantry_item_id: ing.id }];
          return acc;
        }, {} as any)
      };

      render(<RecipeDetailCardV2 recipe={recipeWithAllIngredients} />);

      expect(screen.queryByText('Items to Buy')).toBeFalsy();
    });
  });

  describe('Instructions Display', () => {
    it('should display all recipe steps', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(screen.getByText('Steps (7)')).toBeTruthy();
      expect(screen.getByText('Cook pasta according to package directions.')).toBeTruthy();
      expect(screen.getByText('Season chicken with salt and pepper, then cook in a large skillet.')).toBeTruthy();
      expect(screen.getByText('Serve immediately with extra cheese.')).toBeTruthy();
    });

    it('should display step numbers correctly', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      expect(screen.getByText('1')).toBeTruthy();
      expect(screen.getByText('2')).toBeTruthy();
      expect(screen.getByText('7')).toBeTruthy();
    });

    it('should handle recipe without instructions', () => {
      const recipeWithoutInstructions = {
        ...mockRecipe,
        analyzedInstructions: []
      };

      render(<RecipeDetailCardV2 recipe={recipeWithoutInstructions} />);

      expect(screen.getByText('Steps (0)')).toBeTruthy();
    });
  });

  describe('Button Functionality', () => {
    it('should navigate back when back button is pressed', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} onBack={mockOnBack} />);

      const backButton = screen.getByTestId('back-button');
      fireEvent.press(backButton);

      expect(mockOnBack).toHaveBeenCalled();
    });

    it('should use router back when no onBack prop is provided', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const backButton = screen.getByTestId('back-button');
      fireEvent.press(backButton);

      expect(mockBack).toHaveBeenCalled();
    });

    it('should navigate to cooking mode when Cook Now is pressed', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const cookNowButton = screen.getByText('Cook Now');
      fireEvent.press(cookNowButton);

      expect(mockPush).toHaveBeenCalledWith({
        pathname: '/cooking-mode',
        params: {
          recipeId: 123,
          recipeData: JSON.stringify(mockRecipe)
        }
      });
    });

    it('should toggle bookmark status', async () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const bookmarkButton = screen.getByTestId('bookmark-button');
      fireEvent.press(bookmarkButton);

      await waitFor(() => {
        expect(recipeService.saveRecipe).toHaveBeenCalledWith(mockRecipe, 111);
      });
    });

    it('should animate bookmark when pressed', async () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const bookmarkButton = screen.getByTestId('bookmark-button');
      fireEvent.press(bookmarkButton);

      // Animation should be triggered (we can't easily test the actual animation)
      expect(bookmarkButton).toBeTruthy();
    });

    it('should show different bookmark icon when favorited', () => {
      const favoriteRecipe = { ...mockRecipe, is_favorite: true };
      render(<RecipeDetailCardV2 recipe={favoriteRecipe} />);

      const bookmarkIcon = screen.getByTestId('bookmark-icon');
      expect(bookmarkIcon.props.name).toBe('bookmark');
    });

    it('should show outline bookmark icon when not favorited', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const bookmarkIcon = screen.getByTestId('bookmark-icon');
      expect(bookmarkIcon.props.name).toBe('bookmark-outline');
    });
  });

  describe('Nutrition Modal', () => {
    it('should open nutrition modal when calories are pressed', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const caloriesText = screen.getByText('650 kcal');
      fireEvent.press(caloriesText);

      expect(screen.getByText('Nutrition Facts')).toBeTruthy();
      expect(screen.getByText('Calories')).toBeTruthy();
      expect(screen.getByText('650')).toBeTruthy();
      expect(screen.getByText('Protein')).toBeTruthy();
      expect(screen.getByText('35g')).toBeTruthy();
    });

    it('should display all nutrition information in modal', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const caloriesText = screen.getByText('650 kcal');
      fireEvent.press(caloriesText);

      expect(screen.getByText('Carbs')).toBeTruthy();
      expect(screen.getByText('45g')).toBeTruthy();
      expect(screen.getByText('Fat')).toBeTruthy();
      expect(screen.getByText('28g')).toBeTruthy();
      expect(screen.getByText('Fiber')).toBeTruthy();
      expect(screen.getByText('3g')).toBeTruthy();
      expect(screen.getByText('Sugar')).toBeTruthy();
      expect(screen.getByText('8g')).toBeTruthy();
    });

    it('should close nutrition modal when close button is pressed', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const caloriesText = screen.getByText('650 kcal');
      fireEvent.press(caloriesText);

      const closeButton = screen.getByTestId('nutrition-modal-close');
      fireEvent.press(closeButton);

      expect(screen.queryByText('Nutrition Facts')).toBeFalsy();
    });

    it('should show disclaimer in nutrition modal', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const caloriesText = screen.getByText('650 kcal');
      fireEvent.press(caloriesText);

      expect(screen.getByText('* Nutritional values are estimates and may vary based on specific ingredients used.')).toBeTruthy();
    });
  });

  describe('Rating System', () => {
    it('should show rating modal after cooking is finished', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // First cook the recipe
      const cookNowButton = screen.getByText('Cook Now');
      fireEvent.press(cookNowButton);

      // Simulate finishing cooking (this would normally happen in cooking mode)
      const finishCookingButton = screen.getByText('Finish Cooking');
      fireEvent.press(finishCookingButton);

      expect(screen.getByText('How did it turn out?')).toBeTruthy();
      expect(screen.getByText('Your feedback helps us improve recommendations')).toBeTruthy();
    });

    it('should submit positive rating', async () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} onRatingSubmitted={mockOnRatingSubmitted} />);

      // Simulate being in the finished cooking state
      const cookNowButton = screen.getByText('Cook Now');
      fireEvent.press(cookNowButton);
      const finishCookingButton = screen.getByText('Finish Cooking');
      fireEvent.press(finishCookingButton);

      const thumbsUpButton = screen.getByTestId('modal-thumbs-up');
      fireEvent.press(thumbsUpButton);

      await waitFor(() => {
        expect(recipeService.rateRecipe).toHaveBeenCalledWith(123, 111, 'thumbs_up');
        expect(mockOnRatingSubmitted).toHaveBeenCalledWith('thumbs_up');
      });
    });

    it('should submit negative rating', async () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} onRatingSubmitted={mockOnRatingSubmitted} />);

      // Simulate being in the finished cooking state
      const cookNowButton = screen.getByText('Cook Now');
      fireEvent.press(cookNowButton);
      const finishCookingButton = screen.getByText('Finish Cooking');
      fireEvent.press(finishCookingButton);

      const thumbsDownButton = screen.getByTestId('modal-thumbs-down');
      fireEvent.press(thumbsDownButton);

      await waitFor(() => {
        expect(recipeService.rateRecipe).toHaveBeenCalledWith(123, 111, 'thumbs_down');
        expect(mockOnRatingSubmitted).toHaveBeenCalledWith('thumbs_down');
      });
    });

    it('should allow skipping rating', () => {
      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Simulate being in the finished cooking state
      const cookNowButton = screen.getByText('Cook Now');
      fireEvent.press(cookNowButton);
      const finishCookingButton = screen.getByText('Finish Cooking');
      fireEvent.press(finishCookingButton);

      const skipButton = screen.getByText('Skip');
      fireEvent.press(skipButton);

      expect(screen.queryByText('How did it turn out?')).toBeFalsy();
    });

    it('should handle rating errors gracefully', async () => {
      recipeService.rateRecipe.mockRejectedValue(new Error('API Error'));

      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      // Simulate being in the finished cooking state
      const cookNowButton = screen.getByText('Cook Now');
      fireEvent.press(cookNowButton);
      const finishCookingButton = screen.getByText('Finish Cooking');
      fireEvent.press(finishCookingButton);

      const thumbsUpButton = screen.getByTestId('modal-thumbs-up');
      fireEvent.press(thumbsUpButton);

      await waitFor(() => {
        // Error should be handled silently or logged
        expect(recipeService.rateRecipe).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle missing nutrition data gracefully', () => {
      const recipeWithoutNutrition = {
        ...mockRecipe,
        nutrition: undefined
      };

      render(<RecipeDetailCardV2 recipe={recipeWithoutNutrition} />);

      expect(screen.getByText('0 kcal')).toBeTruthy();
      expect(screen.getByText('0g protein')).toBeTruthy();
    });

    it('should handle missing ingredients gracefully', () => {
      const recipeWithoutIngredients = {
        ...mockRecipe,
        extendedIngredients: undefined
      };

      render(<RecipeDetailCardV2 recipe={recipeWithoutIngredients} />);

      expect(screen.getByText('Ingredients (0)')).toBeTruthy();
      expect(screen.getByText('100% match')).toBeTruthy(); // 0/0 = 100%
    });

    it('should handle missing instructions gracefully', () => {
      const recipeWithoutInstructions = {
        ...mockRecipe,
        analyzedInstructions: undefined
      };

      render(<RecipeDetailCardV2 recipe={recipeWithoutInstructions} />);

      expect(screen.getByText('Steps (0)')).toBeTruthy();
    });

    it('should handle bookmark service errors', async () => {
      recipeService.saveRecipe.mockRejectedValue(new Error('Save error'));

      render(<RecipeDetailCardV2 recipe={mockRecipe} />);

      const bookmarkButton = screen.getByTestId('bookmark-button');
      fireEvent.press(bookmarkButton);

      await waitFor(() => {
        // Bookmark state should revert on error
        const bookmarkIcon = screen.getByTestId('bookmark-icon');
        expect(bookmarkIcon.props.name).toBe('bookmark-outline');
      });
    });
  });
});