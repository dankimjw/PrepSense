import { Recipe, SavedRecipe } from '../../types';

// Test utilities for recipe components
export const createMockRecipe = (overrides: Partial<Recipe> = {}): Recipe => ({
  id: 1,
  title: 'Mock Recipe',
  image: 'https://example.com/image.jpg',
  imageType: 'jpg',
  usedIngredientCount: 3,
  missedIngredientCount: 2,
  usedIngredients: [
    { id: 1, name: 'ingredient 1', amount: 1, unit: 'cup', image: '' },
    { id: 2, name: 'ingredient 2', amount: 2, unit: 'tsp', image: '' },
    { id: 3, name: 'ingredient 3', amount: 100, unit: 'g', image: '' }
  ],
  missedIngredients: [
    { id: 4, name: 'missing 1', amount: 1, unit: 'tbsp', image: '' },
    { id: 5, name: 'missing 2', amount: 200, unit: 'ml', image: '' }
  ],
  likes: 50,
  readyInMinutes: 30,
  servings: 4,
  nutrition: {
    calories: 400,
    protein: 20,
    carbs: 30,
    fat: 15,
    fiber: 5,
    sugar: 10
  },
  extendedIngredients: [
    { id: 1, name: 'ingredient 1', original: 'ingredient 1 (1 cup)', amount: 1, unit: 'cup' },
    { id: 2, name: 'ingredient 2', original: 'ingredient 2 (2 tsp)', amount: 2, unit: 'tsp' },
    { id: 3, name: 'ingredient 3', original: 'ingredient 3 (100g)', amount: 100, unit: 'g' },
    { id: 4, name: 'missing 1', original: 'missing 1 (1 tbsp)', amount: 1, unit: 'tbsp' },
    { id: 5, name: 'missing 2', original: 'missing 2 (200ml)', amount: 200, unit: 'ml' }
  ],
  available_ingredients: [
    'ingredient 1 (1 cup)',
    'ingredient 2 (2 tsp)',
    'ingredient 3 (100g)'
  ],
  pantry_item_matches: {
    'ingredient 1 (1 cup)': [{ pantry_item_id: 1 }],
    'ingredient 2 (2 tsp)': [{ pantry_item_id: 2 }],
    'ingredient 3 (100g)': [{ pantry_item_id: 3 }]
  },
  analyzedInstructions: [
    {
      steps: [
        { number: 1, step: 'First step of the recipe.' },
        { number: 2, step: 'Second step of the recipe.' },
        { number: 3, step: 'Final step of the recipe.' }
      ]
    }
  ],
  is_favorite: false,
  ...overrides
});

export const createMockSavedRecipe = (overrides: Partial<SavedRecipe> = {}): SavedRecipe => ({
  id: 'saved-1',
  recipe_id: 100,
  recipe_title: 'Saved Mock Recipe',
  recipe_image: 'https://example.com/saved-recipe.jpg',
  recipe_data: createMockRecipe({ id: 100, title: 'Saved Mock Recipe' }),
  rating: 'neutral',
  is_favorite: false,
  source: 'spoonacular',
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T10:00:00Z',
  ...overrides
});

// Mock fetch responses for different endpoints
export const createMockFetchResponse = (data: any, ok: boolean = true, status: number = 200) => {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data)
  } as Response);
};

// Common mock responses
export const mockApiResponses = {
  pantryRecipes: {
    recipes: [
      createMockRecipe({ id: 1, title: 'Pantry Recipe 1', usedIngredientCount: 4, missedIngredientCount: 1 }),
      createMockRecipe({ id: 2, title: 'Pantry Recipe 2', usedIngredientCount: 3, missedIngredientCount: 2 })
    ],
    pantry_ingredients: [
      { name: 'ingredient 1' },
      { name: 'ingredient 2' },
      { name: 'ingredient 3' }
    ]
  },
  savedRecipes: [
    createMockSavedRecipe({ id: 'saved-1', recipe_title: 'Saved Recipe 1', rating: 'thumbs_up' }),
    createMockSavedRecipe({ id: 'saved-2', recipe_title: 'Saved Recipe 2', rating: 'thumbs_down', is_favorite: true })
  ],
  randomRecipes: {
    recipes: [
      createMockRecipe({ id: 10, title: 'Random Recipe 1' }),
      createMockRecipe({ id: 11, title: 'Random Recipe 2' })
    ]
  },
  searchRecipes: {
    results: [
      createMockRecipe({ id: 20, title: 'Search Result 1' }),
      createMockRecipe({ id: 21, title: 'Search Result 2' })
    ]
  },
  saveRecipeSuccess: { success: true, message: 'Recipe saved successfully' },
  ratingUpdateSuccess: { success: true, message: 'Rating updated successfully' },
  favoriteToggleSuccess: { success: true, message: 'Favorite status updated' },
  deleteRecipeSuccess: { success: true, message: 'Recipe deleted successfully' },
  recipeCompleteSuccess: {
    success: true,
    summary: 'Recipe completed successfully!',
    insufficient_items: [],
    errors: []
  },
  pantryItems: [
    {
      id: 1,
      pantry_item_id: 1,
      product_name: 'ingredient 1',
      quantity: 2,
      unit_of_measurement: 'cup',
      expiration_date: '2024-12-31',
      food_category: 'Test Category'
    },
    {
      id: 2,
      pantry_item_id: 2,
      product_name: 'ingredient 2',
      quantity: 10,
      unit_of_measurement: 'tsp',
      expiration_date: '2024-12-31',
      food_category: 'Test Category'
    }
  ]
};

// Error responses
export const mockErrorResponses = {
  apiKeyError: {
    ok: false,
    status: 400,
    json: () => Promise.resolve({ detail: 'API key required for Spoonacular access' })
  },
  networkError: Promise.reject(new Error('Network error')),
  serverError: {
    ok: false,
    status: 500,
    json: () => Promise.resolve({ detail: 'Internal server error' })
  },
  notFoundError: {
    ok: false,
    status: 404,
    json: () => Promise.resolve({ detail: 'Recipe not found' })
  }
};

// Test data for different states
export const testStates = {
  emptyPantry: {
    recipes: [],
    pantry_ingredients: []
  },
  noMatchingRecipes: {
    recipes: [],
    pantry_ingredients: mockApiResponses.pantryRecipes.pantry_ingredients
  },
  allIngredientsAvailable: createMockRecipe({
    available_ingredients: [
      'ingredient 1 (1 cup)',
      'ingredient 2 (2 tsp)',
      'ingredient 3 (100g)',
      'missing 1 (1 tbsp)',
      'missing 2 (200ml)'
    ],
    missedIngredientCount: 0,
    usedIngredientCount: 5
  }),
  noIngredientsAvailable: createMockRecipe({
    available_ingredients: [],
    pantry_item_matches: {},
    missedIngredientCount: 5,
    usedIngredientCount: 0
  }),
  recipeWithoutImage: createMockRecipe({
    image: undefined
  }),
  recipeWithoutNutrition: createMockRecipe({
    nutrition: undefined
  }),
  recipeWithoutInstructions: createMockRecipe({
    analyzedInstructions: []
  }),
  longCookingTime: createMockRecipe({
    readyInMinutes: 150 // 2.5 hours
  }),
  shortCookingTime: createMockRecipe({
    readyInMinutes: 15
  }),
  manyIngredients: createMockRecipe({
    extendedIngredients: Array.from({ length: 10 }, (_, i) => ({
      id: i + 1,
      name: `ingredient ${i + 1}`,
      original: `ingredient ${i + 1} (${i + 1} units)`,
      amount: i + 1,
      unit: 'units'
    }))
  })
};

// Utility functions for testing
export const getRecipeCardTestId = (recipeId: number | string) => `recipe-card-${recipeId}`;
export const getBookmarkButtonTestId = (recipeId: number | string) => `bookmark-button-${recipeId}`;
export const getFavoriteButtonTestId = (recipeId: number | string) => `favorite-button-${recipeId}`;
export const getDeleteButtonTestId = (recipeId: number | string) => `delete-button-${recipeId}`;
export const getRatingButtonTestId = (recipeId: number | string, rating: string) => `${rating}-button-${recipeId}`;

// Mock navigation functions
export const createMockNavigation = () => ({
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
  canGoBack: jest.fn(),
  setParams: jest.fn(),
  pathname: '/test'
});

// Mock context providers
export const createMockAuthContext = (overrides = {}) => ({
  user: { id: 111, email: 'test@example.com' },
  token: 'mock-token',
  isAuthenticated: true,
  signIn: jest.fn(),
  signOut: jest.fn(),
  isLoading: false,
  ...overrides
});

export const createMockItemsContext = (overrides = {}) => ({
  items: [
    { product_name: 'ingredient 1' },
    { product_name: 'ingredient 2' },
    { product_name: 'ingredient 3' }
  ],
  addItem: jest.fn(),
  updateItem: jest.fn(),
  removeItem: jest.fn(),
  isLoading: false,
  error: null,
  refreshItems: jest.fn(),
  ...overrides
});

// Helper to wait for async operations in tests
export const waitForAsyncOperation = () => new Promise(resolve => setTimeout(resolve, 0));

// Matcher for checking if an element contains specific test IDs
export const expectElementToContainTestId = (element: any, testId: string) => {
  const found = element.findByProps ? element.findByProps({ testID: testId }) : null;
  expect(found).toBeTruthy();
};

// Helper to simulate network delays in tests
export const createDelayedMockResponse = (data: any, delay: number = 100) => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({
        ok: true,
        json: () => Promise.resolve(data)
      });
    }, delay);
  });
};