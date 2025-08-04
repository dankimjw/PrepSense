// API Mock helpers for testing
export interface MockRecipe {
  id: number;
  title: string;
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  image?: string;
  usedIngredientCount?: number;
  missedIngredientCount?: number;
  missedIngredients?: Array<{
    id: number;
    name: string;
    original: string;
    originalName: string;
    amount: number;
    unit: string;
  }>;
  usedIngredients?: Array<{
    id: number;
    name: string;
    original: string;
    originalName: string;
    amount: number;
    unit: string;
  }>;
}

export function createMockRecipe(overrides: Partial<MockRecipe> = {}): MockRecipe {
  return {
    id: 1,
    title: 'Test Recipe',
    readyInMinutes: 30,
    servings: 4,
    sourceUrl: 'https://example.com',
    image: 'https://example.com/image.jpg',
    usedIngredientCount: 2,
    missedIngredientCount: 1,
    missedIngredients: [],
    usedIngredients: [],
    ...overrides,
  };
}

export interface MockRecipeSearchResponse {
  results: MockRecipe[];
  totalResults: number;
  offset: number;
  number: number;
}

export function mockRecipeSearchResponse(recipes: MockRecipe[] = []): MockRecipeSearchResponse {
  return {
    results: recipes,
    totalResults: recipes.length,
    offset: 0,
    number: recipes.length,
  };
}

export function mockFetch(responseData: any, status: number = 200): jest.MockedFunction<typeof fetch> {
  return jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(responseData),
    text: jest.fn().mockResolvedValue(JSON.stringify(responseData)),
  } as Response);
}

export function mockFetchError(message: string = 'Network error', status: number = 500): jest.MockedFunction<typeof fetch> {
  return jest.fn().mockRejectedValue(new Error(message));
}

export function mockFetchSequence(...responses: Array<{ data: any; status?: number }>): jest.MockedFunction<typeof fetch> {
  const mockResponses = responses.map(({ data, status = 200 }) => ({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(data),
    text: jest.fn().mockResolvedValue(JSON.stringify(data)),
  }));

  const mockedFetch = jest.fn();
  
  responses.forEach((_, index) => {
    mockedFetch.mockResolvedValueOnce(mockResponses[index]);
  });

  return mockedFetch as jest.MockedFunction<typeof fetch>;
}