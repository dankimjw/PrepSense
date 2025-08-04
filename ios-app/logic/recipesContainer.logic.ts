/**
 * Business logic for RecipesContainer component
 * Extracted for comprehensive testing without StyleSheet issues
 */

export type SortOption = 'name' | 'date' | 'rating' | 'missing';
export type ActiveTab = 'pantry' | 'discover' | 'my-recipes';
export type MyRecipesFilter = 'all' | 'thumbs_up' | 'thumbs_down' | 'favorites';
export type MyRecipesTab = 'saved' | 'cooked';

export interface Recipe {
  id: number;
  title: string;
  image: string;
  imageType: string;
  usedIngredientCount: number;
  missedIngredientCount: number;
  missedIngredients: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  usedIngredients: Array<{
    id: number;
    amount: number;
    unit: string;
    name: string;
    image: string;
  }>;
  likes: number;
}

export interface SavedRecipe {
  id: string;
  recipe_id: number;
  recipe_title: string;
  recipe_image: string;
  recipe_data: any;
  rating: 'thumbs_up' | 'thumbs_down' | 'neutral';
  is_favorite?: boolean;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface RecipesState {
  recipes: Recipe[];
  savedRecipes: SavedRecipe[];
  loading: boolean;
  refreshing: boolean;
  searchQuery: string;
  activeTab: ActiveTab;
  selectedFilters: string[];
  myRecipesFilter: MyRecipesFilter;
  myRecipesTab: MyRecipesTab;
  sortBy: SortOption;
  showSortModal: boolean;
  searchFocused: boolean;
  filtersCollapsed: boolean;
  scrollOffset: number;
  pantryIngredients: string[];
}

export type RecipesAction =
  | { type: 'SET_RECIPES'; payload: Recipe[] }
  | { type: 'SET_SAVED_RECIPES'; payload: SavedRecipe[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_REFRESHING'; payload: boolean }
  | { type: 'SET_SEARCH_QUERY'; payload: string }
  | { type: 'SET_ACTIVE_TAB'; payload: ActiveTab }
  | { type: 'SET_SELECTED_FILTERS'; payload: string[] }
  | { type: 'SET_MY_RECIPES_FILTER'; payload: MyRecipesFilter }
  | { type: 'SET_MY_RECIPES_TAB'; payload: MyRecipesTab }
  | { type: 'SET_SORT_BY'; payload: SortOption }
  | { type: 'SET_SHOW_SORT_MODAL'; payload: boolean }
  | { type: 'SET_SEARCH_FOCUSED'; payload: boolean }
  | { type: 'SET_FILTERS_COLLAPSED'; payload: boolean }
  | { type: 'SET_SCROLL_OFFSET'; payload: number }
  | { type: 'SET_PANTRY_INGREDIENTS'; payload: string[] }
  | { type: 'UPDATE_SAVED_RECIPE'; payload: { id: string; updates: Partial<SavedRecipe> } };

/**
 * Initial state for recipes reducer
 */
export const getInitialState = (): RecipesState => ({
  recipes: [],
  savedRecipes: [],
  loading: false,
  refreshing: false,
  searchQuery: '',
  activeTab: 'pantry',
  selectedFilters: [],
  myRecipesFilter: 'all',
  myRecipesTab: 'saved',
  sortBy: 'name',
  showSortModal: false,
  searchFocused: false,
  filtersCollapsed: false,
  scrollOffset: 0,
  pantryIngredients: [],
});

/**
 * Reducer for managing recipes state
 */
export function recipesReducer(state: RecipesState, action: RecipesAction): RecipesState {
  switch (action.type) {
    case 'SET_RECIPES':
      return { ...state, recipes: action.payload };
    case 'SET_SAVED_RECIPES':
      return { ...state, savedRecipes: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_REFRESHING':
      return { ...state, refreshing: action.payload };
    case 'SET_SEARCH_QUERY':
      return { ...state, searchQuery: action.payload };
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'SET_SELECTED_FILTERS':
      return { ...state, selectedFilters: action.payload };
    case 'SET_MY_RECIPES_FILTER':
      return { ...state, myRecipesFilter: action.payload };
    case 'SET_MY_RECIPES_TAB':
      return { ...state, myRecipesTab: action.payload };
    case 'SET_SORT_BY':
      return { ...state, sortBy: action.payload };
    case 'SET_SHOW_SORT_MODAL':
      return { ...state, showSortModal: action.payload };
    case 'SET_SEARCH_FOCUSED':
      return { ...state, searchFocused: action.payload };
    case 'SET_FILTERS_COLLAPSED':
      return { ...state, filtersCollapsed: action.payload };
    case 'SET_SCROLL_OFFSET':
      return { ...state, scrollOffset: action.payload };
    case 'SET_PANTRY_INGREDIENTS':
      return { ...state, pantryIngredients: action.payload };
    case 'UPDATE_SAVED_RECIPE':
      return {
        ...state,
        savedRecipes: state.savedRecipes.map(recipe => 
          recipe.id === action.payload.id 
            ? { ...recipe, ...action.payload.updates }
            : recipe
        )
      };
    default:
      return state;
  }
}

/**
 * Logic for recalculating ingredient counts based on pantry items
 */
export interface IngredientCountResult {
  usedCount: number;
  missedCount: number;
}

export function recalculateIngredientCounts(
  recipe: Recipe, 
  pantryItems: string[],
  calculateAvailability: (ingredients: any[], pantryItems: any[]) => any
): IngredientCountResult {
  // Convert pantry items to the expected format
  const pantryItemObjects = pantryItems.map(item => ({ product_name: item }));
  
  // Combine all ingredients into a single array with the expected format
  const allIngredients = [
    ...(recipe.usedIngredients || []),
    ...(recipe.missedIngredients || [])
  ].map((ingredient, index) => ({
    id: ingredient.id || index,
    name: ingredient.name,
    original: ingredient.name // Use name as fallback for original
  }));

  // Use the standardized ingredient matching utility
  const result = calculateAvailability(allIngredients, pantryItemObjects);
  
  return { 
    usedCount: result.availableCount, 
    missedCount: result.missingCount 
  };
}

/**
 * Logic for filtering saved recipes by various criteria
 */
export function filterSavedRecipes(
  recipes: SavedRecipe[], 
  filter: MyRecipesFilter,
  tab: MyRecipesTab
): SavedRecipe[] {
  // First filter by tab status if needed
  let filteredRecipes = recipes;
  
  // Note: Status filtering is typically done at API level,
  // but we can add client-side filtering if needed
  
  // Then apply the filter
  switch (filter) {
    case 'thumbs_up':
      return filteredRecipes.filter(r => r.rating === 'thumbs_up');
    case 'thumbs_down':
      return filteredRecipes.filter(r => r.rating === 'thumbs_down');
    case 'favorites':
      return filteredRecipes.filter(r => r.is_favorite);
    case 'all':
    default:
      return filteredRecipes;
  }
}

/**
 * Logic for filtering spoonacular recipes with validation
 */
export function filterValidRecipes(
  recipes: Recipe[],
  isValidRecipe?: (recipe: Recipe) => boolean
): Recipe[] {
  return recipes.filter((recipe: Recipe) => {
    // Basic validation
    if (!recipe.id || typeof recipe.id !== 'number' || recipe.id <= 0) {
      return false;
    }
    
    // Apply additional validation if provided
    if (isValidRecipe && !isValidRecipe(recipe)) {
      return false;
    }
    
    return true;
  });
}

/**
 * Logic for sorting recipes based on different criteria
 */
export function sortRecipes(recipes: Recipe[], sortBy: SortOption): Recipe[] {
  const sortedRecipes = [...recipes];
  
  switch (sortBy) {
    case 'name':
      return sortedRecipes.sort((a, b) => a.title.localeCompare(b.title));
    case 'missing':
      return sortedRecipes.sort((a, b) => a.missedIngredientCount - b.missedIngredientCount);
    case 'rating':
      return sortedRecipes.sort((a, b) => (b.likes || 0) - (a.likes || 0));
    case 'date':
      // For regular recipes, we don't have a date field, so maintain original order
      return sortedRecipes;
    default:
      return sortedRecipes;
  }
}

/**
 * Logic for sorting saved recipes
 */
export function sortSavedRecipes(recipes: SavedRecipe[], sortBy: SortOption): SavedRecipe[] {
  const sortedRecipes = [...recipes];
  
  switch (sortBy) {
    case 'name':
      return sortedRecipes.sort((a, b) => a.recipe_title.localeCompare(b.recipe_title));
    case 'date':
      return sortedRecipes.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    case 'rating':
      return sortedRecipes.sort((a, b) => {
        const ratingOrder = { 'thumbs_up': 3, 'neutral': 2, 'thumbs_down': 1 };
        return (ratingOrder[b.rating] || 0) - (ratingOrder[a.rating] || 0);
      });
    case 'missing':
      // For saved recipes, we don't have missing ingredient count
      return sortedRecipes;
    default:
      return sortedRecipes;
  }
}

/**
 * Logic for building API filter parameters
 */
export interface ApiFilterParams {
  statusFilter: string;
  additionalFilters: string;
  fullPath: string;
}

export function buildApiFilterParams(
  myRecipesTab: MyRecipesTab,
  myRecipesFilter: MyRecipesFilter
): ApiFilterParams {
  let statusFilter = '';
  let additionalFilters = '';
  
  // Add status filter based on current tab
  if (myRecipesTab === 'saved') {
    statusFilter = '?status=saved';
  } else if (myRecipesTab === 'cooked') {
    statusFilter = '?status=cooked';
  }
  
  // Add additional filters
  if (myRecipesFilter === 'favorites') {
    additionalFilters = statusFilter ? '&is_favorite=true' : '?is_favorite=true';
  } else if (myRecipesFilter !== 'all') {
    additionalFilters = statusFilter ? `&rating=${myRecipesFilter}` : `?rating=${myRecipesFilter}`;
  }
  
  const fullPath = `${statusFilter}${additionalFilters}`;
  
  return {
    statusFilter,
    additionalFilters, 
    fullPath
  };
}

/**
 * Logic for determining which data source to use
 */
export function shouldUsePreloadedData(
  preloadedData: any,
  isRefreshing: boolean
): boolean {
  return Boolean(preloadedData) && !isRefreshing;
}

/**
 * Logic for processing API error responses
 */
export interface ApiErrorInfo {
  isApiKeyError: boolean;
  shouldShowApiKeyAlert: boolean;
  errorMessage: string;
}

export function processApiError(response: Response, errorData: any): ApiErrorInfo {
  const isApiKeyError = response.status === 400 && errorData.detail?.includes('API key');
  
  return {
    isApiKeyError,
    shouldShowApiKeyAlert: isApiKeyError,
    errorMessage: isApiKeyError ? 'Spoonacular API key not configured' : 'API request failed'
  };
}

/**
 * Logic for updating recipes with recalculated counts
 */
export function updateRecipesWithCounts(
  recipes: Recipe[],
  pantryIngredients: string[],
  calculateAvailability: (ingredients: any[], pantryItems: any[]) => any
): Recipe[] {
  return recipes.map((recipe: Recipe) => {
    const { usedCount, missedCount } = recalculateIngredientCounts(
      recipe, 
      pantryIngredients, 
      calculateAvailability
    );
    return {
      ...recipe,
      usedIngredientCount: usedCount,
      missedIngredientCount: missedCount
    };
  });
}