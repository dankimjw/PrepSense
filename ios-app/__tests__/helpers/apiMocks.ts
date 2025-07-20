// API Mock Helpers for testing

export const mockFetch = (response: any, options: { ok?: boolean; status?: number } = {}) => {
  const { ok = true, status = 200 } = options;
  
  return jest.fn().mockResolvedValueOnce({
    ok,
    status,
    json: async () => response,
    text: async () => JSON.stringify(response),
    headers: new Headers({
      'content-type': 'application/json',
    }),
  });
};

export const mockFetchError = (error: string) => {
  return jest.fn().mockRejectedValueOnce(new Error(error));
};

export const mockFetchSequence = (responses: Array<{ data: any; ok?: boolean; status?: number }>) => {
  const mock = jest.fn();
  
  responses.forEach(({ data, ok = true, status = 200 }) => {
    mock.mockResolvedValueOnce({
      ok,
      status,
      json: async () => data,
      text: async () => JSON.stringify(data),
    });
  });
  
  return mock;
};

// Common mock data factories
export const createMockRecipe = (overrides = {}) => ({
  id: 1,
  title: 'Test Recipe',
  readyInMinutes: 30,
  servings: 4,
  ingredients: ['ingredient1', 'ingredient2'],
  instructions: 'Test instructions',
  nutrition: {
    calories: 300,
    protein: 20,
    carbs: 40,
    fat: 10,
  },
  ...overrides,
});

export const createMockPantryItem = (overrides = {}) => ({
  id: '1',
  product_name: 'Test Item',
  quantity_amount: 10,
  quantity_unit: 'units',
  expiration_date: '2024-12-31',
  category: 'dairy',
  ...overrides,
});

export const createMockIngredientMatch = (overrides = {}) => ({
  pantry_item_id: 1,
  product_name: 'Matched Item',
  quantity: 5,
  unit: 'cups',
  ...overrides,
});

// API response mocks
export const mockRecipeSearchResponse = (recipes = []) => ({
  recipes: recipes.length > 0 ? recipes : [
    createMockRecipe({ id: 1, title: 'Recipe 1' }),
    createMockRecipe({ id: 2, title: 'Recipe 2' }),
  ],
  totalResults: recipes.length || 2,
});

export const mockRecipeDetailsResponse = (recipe = {}) => ({
  ...createMockRecipe(),
  analyzedInstructions: [{
    steps: [
      { number: 1, step: 'Step 1' },
      { number: 2, step: 'Step 2' },
      { number: 3, step: 'Step 3' },
    ],
  }],
  extendedIngredients: [
    { id: 1, original: '2 cups milk', name: 'milk', amount: 2, unit: 'cups' },
    { id: 2, original: '3 cups flour', name: 'flour', amount: 3, unit: 'cups' },
  ],
  ...recipe,
});

export const mockPantryResponse = (items = []) => ({
  pantry_items: items.length > 0 ? items : [
    createMockPantryItem({ id: '1', product_name: 'Milk' }),
    createMockPantryItem({ id: '2', product_name: 'Flour' }),
  ],
  total: items.length || 2,
});

// Setup API mocks for tests
export const setupApiMocks = () => {
  global.fetch = jest.fn();
  
  // Default mock implementations
  const mockHandlers = {
    '/api/v1/recipes': mockFetch(mockRecipeSearchResponse()),
    '/api/v1/pantry': mockFetch(mockPantryResponse()),
  };
  
  (global.fetch as jest.Mock).mockImplementation((url: string) => {
    const handler = Object.entries(mockHandlers).find(([pattern]) => 
      url.includes(pattern)
    );
    
    if (handler) {
      return handler[1]();
    }
    
    // Default 404 response
    return Promise.resolve({
      ok: false,
      status: 404,
      json: async () => ({ error: 'Not found' }),
    });
  });
  
  return global.fetch as jest.Mock;
};

// Cleanup helper
export const cleanupApiMocks = () => {
  (global.fetch as jest.Mock).mockReset();
};