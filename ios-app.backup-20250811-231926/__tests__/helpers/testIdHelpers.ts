// Helper functions for consistent testID generation across components

// Recipe screen test IDs
export const recipeScreenTestIds = {
  loadingIndicator: 'loading-indicator',
  recipesScrollView: 'recipes-scroll-view',
  sortButton: 'sort-button',
  chatButton: 'chat-button',
  clearSearchButton: 'clear-search-button',
  recipeTitle: 'recipe-title',
  
  // Tab test IDs
  pantryTab: 'pantry-tab',
  discoverTab: 'discover-tab',
  myRecipesTab: 'my-recipes-tab',
  
  // Filter test IDs
  filterButton: (filterId: string) => `filter-button-${filterId}`,
  
  // Recipe card test IDs
  recipeCard: (recipeId: string | number) => `recipe-card-${recipeId}`,
  bookmarkButton: (recipeId: string | number) => `bookmark-button-${recipeId}`,
  favoriteButton: (recipeId: string | number) => `favorite-button-${recipeId}`,
  deleteButton: (recipeId: string | number) => `delete-button-${recipeId}`,
  thumbsUpButton: (recipeId: string | number) => `thumbs-up-button-${recipeId}`,
  thumbsDownButton: (recipeId: string | number) => `thumbs-down-button-${recipeId}`,
  
  // Badge test IDs
  checkCircleIcon: 'check-circle-icon',
  closeCircleIcon: 'close-circle-icon',
};

// Recipe details screen test IDs
export const recipeDetailsTestIds = {
  backButton: 'back-button',
  closeButton: 'close-button',
  favoriteButton: 'favorite-button',
  thumbsUpButton: 'thumbs-up-button',
  thumbsDownButton: 'thumbs-down-button',
  recipeImage: 'recipe-image',
  imageLoadingIndicator: 'image-loading-indicator',
  loadingIndicator: 'loading-indicator',
  
  // Ingredient test IDs
  checkmarkCircleIcon: 'checkmark-circle-icon',
  addCircleOutlineIcon: 'add-circle-outline-icon',
  
  // Step test IDs
  stepNumber: (stepNum: number) => `step-number-${stepNum}`,
  
  // Modal test IDs
  recipeCompletionModal: 'recipe-completion-modal',
  completionConfirmButton: 'completion-confirm-button',
};

// Recipe detail card V2 test IDs
export const recipeCardV2TestIds = {
  backButton: 'back-button',
  heroImage: 'hero-image',
  bookmarkButton: 'bookmark-button',
  bookmarkIcon: 'bookmark-icon',
  nutritionModalClose: 'nutrition-modal-close',
  
  // Ingredient test IDs
  ingredientRow: 'ingredient-row',
  checkmarkCircleIcon: 'checkmark-circle-icon',
  addCircleOutlineIcon: 'add-circle-outline-icon',
  
  // Shopping list test IDs
  shoppingListLoading: 'shopping-list-loading',
  
  // Rating test IDs
  modalThumbsUp: 'modal-thumbs-up',
  modalThumbsDown: 'modal-thumbs-down',
};

// Common icon test IDs
export const iconTestIds = {
  checkmarkCircle: 'checkmark-circle-icon',
  addCircleOutline: 'add-circle-outline-icon',
  closeCircle: 'close-circle-icon',
  bookmark: 'bookmark-icon',
  bookmarkOutline: 'bookmark-outline-icon',
  thumbsUp: 'thumbs-up-icon',
  thumbsDown: 'thumbs-down-icon',
  heart: 'heart-icon',
  heartOutline: 'heart-outline-icon',
  trash: 'trash-icon',
};

// Helper functions to generate test IDs consistently
export const generateTestId = {
  recipeCard: (id: string | number) => `recipe-card-${id}`,
  bookmarkButton: (id: string | number) => `bookmark-button-${id}`,
  favoriteButton: (id: string | number) => `favorite-button-${id}`,
  deleteButton: (id: string | number) => `delete-button-${id}`,
  ratingButton: (id: string | number, rating: 'thumbs_up' | 'thumbs_down') => `${rating}-button-${id}`,
  filterButton: (filterId: string) => `filter-button-${filterId}`,
  stepNumber: (stepNum: number) => `step-number-${stepNum}`,
  ingredientRow: (index: number) => `ingredient-row-${index}`,
};

// Test ID validation helpers
export const validateTestId = (testId: string): boolean => {
  return typeof testId === 'string' && testId.length > 0;
};

export const createAccessibilityProps = (label: string, hint?: string) => ({
  accessibilityLabel: label,
  accessibilityHint: hint,
  accessibilityRole: 'button' as const,
});

// Common test selectors
export const testSelectors = {
  byTestId: (testId: string) => ({ testID: testId }),
  byText: (text: string) => text,
  byRole: (role: string) => ({ accessibilityRole: role }),
  byLabel: (label: string) => ({ accessibilityLabel: label }),
};

// Test data generators for consistent test data
export const generateTestData = {
  recipe: (overrides = {}) => ({
    id: 1,
    title: 'Test Recipe',
    image: 'https://example.com/image.jpg',
    usedIngredientCount: 3,
    missedIngredientCount: 2,
    likes: 50,
    ...overrides
  }),
  
  savedRecipe: (overrides = {}) => ({
    id: 'saved-1',
    recipe_id: 100,
    recipe_title: 'Saved Test Recipe',
    recipe_image: 'https://example.com/saved.jpg',
    rating: 'neutral' as const,
    is_favorite: false,
    source: 'spoonacular',
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:00:00Z',
    ...overrides
  }),
  
  ingredient: (overrides = {}) => ({
    id: 1,
    name: 'test ingredient',
    amount: 1,
    unit: 'cup',
    image: '',
    ...overrides
  }),
  
  pantryItem: (overrides = {}) => ({
    product_name: 'test item',
    quantity: 1,
    unit_of_measurement: 'unit',
    expiration_date: '2024-12-31',
    food_category: 'Test',
    ...overrides
  })
};

// Common assertions for tests
export const commonAssertions = {
  elementExists: (element: any) => expect(element).toBeTruthy(),
  elementNotExists: (element: any) => expect(element).toBeFalsy(),
  textMatches: (element: any, text: string) => expect(element.props.children).toBe(text),
  hasTestId: (element: any, testId: string) => expect(element.props.testID).toBe(testId),
  isDisabled: (element: any) => expect(element.props.disabled).toBe(true),
  isEnabled: (element: any) => expect(element.props.disabled).not.toBe(true),
};

// Mock response generators
export const mockResponses = {
  success: (data = {}) => Promise.resolve({
    ok: true,
    json: () => Promise.resolve(data)
  } as Response),
  
  error: (status = 400, message = 'Error') => Promise.resolve({
    ok: false,
    status,
    json: () => Promise.resolve({ detail: message })
  } as Response),
  
  networkError: () => Promise.reject(new Error('Network error')),
};

export default {
  recipeScreenTestIds,
  recipeDetailsTestIds,
  recipeCardV2TestIds,
  iconTestIds,
  generateTestId,
  validateTestId,
  createAccessibilityProps,
  testSelectors,
  generateTestData,
  commonAssertions,
  mockResponses
};