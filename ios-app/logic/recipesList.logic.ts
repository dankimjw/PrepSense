/**
 * Business logic for RecipesList component
 * Extracted for comprehensive testing without StyleSheet issues
 */

import { Recipe, SavedRecipe, SortOption, ActiveTab, MyRecipesTab } from './recipesContainer.logic';

/**
 * Logic for determining when to show empty states
 */
export interface EmptyStateInfo {
  shouldShow: boolean;
  title: string;
  message: string;
  showSearchHint: boolean;
}

export function getEmptyStateInfo(
  recipes: Recipe[],
  savedRecipes: SavedRecipe[],
  activeTab: ActiveTab,
  searchQuery: string,
  loading: boolean
): EmptyStateInfo {
  if (loading) {
    return {
      shouldShow: false,
      title: '',
      message: '',
      showSearchHint: false
    };
  }

  const isEmpty = activeTab === 'my-recipes' ? savedRecipes.length === 0 : recipes.length === 0;
  
  if (!isEmpty) {
    return {
      shouldShow: false,
      title: '',
      message: '',
      showSearchHint: false
    };
  }

  // Determine empty state based on tab and search
  switch (activeTab) {
    case 'pantry':
      return {
        shouldShow: true,
        title: 'No Recipes Found',
        message: searchQuery 
          ? 'Try adjusting your search or filters'
          : 'Add items to your pantry to see recipe suggestions',
        showSearchHint: false
      };
    case 'discover':
      return {
        shouldShow: true,
        title: 'No Recipes Found',
        message: searchQuery
          ? 'Try a different search term or adjust your filters'
          : 'Search for recipes to discover new dishes',
        showSearchHint: !searchQuery
      };
    case 'my-recipes':
      return {
        shouldShow: true,
        title: 'No Saved Recipes',
        message: 'Save recipes from the Pantry or Discover tabs to see them here',
        showSearchHint: false
      };
    default:
      return {
        shouldShow: false,
        title: '',
        message: '',
        showSearchHint: false
      };
  }
}

/**
 * Logic for processing recipe data for display
 */
export interface ProcessedRecipeData {
  displayRecipes: Recipe[];
  displaySavedRecipes: SavedRecipe[];
  totalCount: number;
}

export function processRecipeDataForDisplay(
  recipes: Recipe[],
  savedRecipes: SavedRecipe[],
  activeTab: ActiveTab,
  sortBy: SortOption,
  searchQuery: string,
  sortRecipes: (recipes: Recipe[], sortBy: SortOption) => Recipe[],
  sortSavedRecipes: (recipes: SavedRecipe[], sortBy: SortOption) => SavedRecipe[]
): ProcessedRecipeData {
  let displayRecipes: Recipe[] = [];
  let displaySavedRecipes: SavedRecipe[] = [];
  
  if (activeTab === 'my-recipes') {
    // Filter by search query if provided
    let filteredSaved = savedRecipes;
    if (searchQuery.trim()) {
      filteredSaved = savedRecipes.filter(recipe =>
        recipe.recipe_title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    displaySavedRecipes = sortSavedRecipes(filteredSaved, sortBy);
  } else {
    // Filter by search query if provided
    let filteredRecipes = recipes;
    if (searchQuery.trim() && activeTab === 'discover') {
      filteredRecipes = recipes.filter(recipe =>
        recipe.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    displayRecipes = sortRecipes(filteredRecipes, sortBy);
  }
  
  const totalCount = activeTab === 'my-recipes' ? displaySavedRecipes.length : displayRecipes.length;
  
  return {
    displayRecipes,
    displaySavedRecipes,
    totalCount
  };
}

/**
 * Logic for calculating recipe compatibility scores
 */
export interface RecipeCompatibility {
  score: number;
  availableIngredients: number;
  totalIngredients: number;
  compatibilityLevel: 'high' | 'medium' | 'low';
}

export function calculateRecipeCompatibility(recipe: Recipe): RecipeCompatibility {
  const totalIngredients = recipe.usedIngredientCount + recipe.missedIngredientCount;
  const availableIngredients = recipe.usedIngredientCount;
  
  if (totalIngredients === 0) {
    return {
      score: 0,
      availableIngredients: 0,
      totalIngredients: 0,
      compatibilityLevel: 'low'
    };
  }
  
  const score = availableIngredients / totalIngredients;
  
  let compatibilityLevel: 'high' | 'medium' | 'low';
  if (score >= 0.8) {
    compatibilityLevel = 'high';
  } else if (score >= 0.5) {
    compatibilityLevel = 'medium';
  } else {
    compatibilityLevel = 'low';
  }
  
  return {
    score,
    availableIngredients,
    totalIngredients,
    compatibilityLevel
  };
}

/**
 * Logic for generating recipe action button states
 */
export interface RecipeActionState {
  canSave: boolean;
  canRate: boolean;
  canComplete: boolean;
  saveButtonText: string;
  saveButtonVariant: 'primary' | 'secondary' | 'outline';
}

export function getRecipeActionState(
  recipe: Recipe | SavedRecipe,
  activeTab: ActiveTab,
  myRecipesTab: MyRecipesTab,
  isAuthenticated: boolean
): RecipeActionState {
  if (activeTab === 'my-recipes') {
    const savedRecipe = recipe as SavedRecipe;
    return {
      canSave: false,
      canRate: true,
      canComplete: myRecipesTab === 'saved',
      saveButtonText: myRecipesTab === 'saved' ? 'Cook Recipe' : 'Cooked',
      saveButtonVariant: myRecipesTab === 'saved' ? 'primary' : 'outline'
    };
  }
  
  return {
    canSave: isAuthenticated,
    canRate: false,
    canComplete: false,
    saveButtonText: 'Save Recipe',
    saveButtonVariant: 'outline'
  };
}

/**
 * Logic for formatting ingredient display text
 */
export function formatIngredientSummary(
  usedCount: number,
  missedCount: number,
  maxDisplay: number = 3
): string {
  const totalCount = usedCount + missedCount;
  
  if (totalCount === 0) {
    return 'No ingredients listed';
  }
  
  if (missedCount === 0) {
    return `You have all ${totalCount} ingredients`;
  }
  
  if (usedCount === 0) {
    return `Need ${missedCount} ingredients`;
  }
  
  if (missedCount === 1) {
    return `Missing 1 ingredient (${usedCount}/${totalCount} available)`;
  }
  
  return `Missing ${missedCount} ingredients (${usedCount}/${totalCount} available)`;
}

/**
 * Logic for determining recipe card style based on compatibility
 */
export interface RecipeCardStyle {
  borderColor: string;
  backgroundColor: string;
  compatibilityIcon: string;
  compatibilityColor: string;
}

export function getRecipeCardStyle(compatibility: RecipeCompatibility): RecipeCardStyle {
  switch (compatibility.compatibilityLevel) {
    case 'high':
      return {
        borderColor: '#10B981',
        backgroundColor: '#F0FDF4',
        compatibilityIcon: 'checkmark-circle',
        compatibilityColor: '#10B981'
      };
    case 'medium':
      return {
        borderColor: '#F59E0B',
        backgroundColor: '#FFFBEB',
        compatibilityIcon: 'warning',
        compatibilityColor: '#F59E0B'
      };
    case 'low':
      return {
        borderColor: '#EF4444',
        backgroundColor: '#FEF2F2',
        compatibilityIcon: 'close-circle',
        compatibilityColor: '#EF4444'
      };
    default:
      return {
        borderColor: '#E5E7EB',
        backgroundColor: '#FFFFFF',
        compatibilityIcon: 'help-circle',
        compatibilityColor: '#6B7280'
      };
  }
}

/**
 * Logic for scroll behavior and filter collapse
 */
export interface ScrollBehavior {
  shouldCollapseFilters: boolean;
  isScrollingUp: boolean;
  isScrollingDown: boolean;
}

export function calculateScrollBehavior(
  currentOffset: number,
  previousOffset: number,
  threshold: number = 50
): ScrollBehavior {
  const scrollDelta = currentOffset - previousOffset;
  const isScrollingUp = scrollDelta < 0;
  const isScrollingDown = scrollDelta > 0;
  
  const shouldCollapseFilters = isScrollingDown && Math.abs(scrollDelta) > threshold;
  
  return {
    shouldCollapseFilters,
    isScrollingUp,
    isScrollingDown
  };
}

/**
 * Logic for refresh control behavior
 */
export interface RefreshBehavior {
  shouldShowRefreshControl: boolean;
  refreshThreshold: number;
  canRefresh: boolean;
}

export function getRefreshBehavior(
  activeTab: ActiveTab,
  loading: boolean,
  scrollOffset: number
): RefreshBehavior {
  const refreshThreshold = 100;
  const canRefresh = !loading && scrollOffset < refreshThreshold;
  
  return {
    shouldShowRefreshControl: true,
    refreshThreshold,
    canRefresh
  };
}

/**
 * Logic for generating navigation paths
 */
export interface NavigationPath {
  route: string;
  params?: Record<string, any>;
}

export function getRecipeNavigationPath(
  recipe: Recipe | SavedRecipe,
  activeTab: ActiveTab
): NavigationPath {
  if (activeTab === 'my-recipes') {
    const savedRecipe = recipe as SavedRecipe;
    return {
      route: '/recipe-details',
      params: {
        recipeId: savedRecipe.recipe_id,
        savedRecipeId: savedRecipe.id,
        source: 'saved'
      }
    };
  }
  
  const regularRecipe = recipe as Recipe;
  return {
    route: '/recipe-details',
    params: {
      recipeId: regularRecipe.id,
      source: 'spoonacular'
    }
  };
}

/**
 * Logic for recipe list performance optimization
 */
export interface ListOptimization {
  itemHeight: number;
  windowSize: number;
  initialNumToRender: number;
  maxToRenderPerBatch: number;
}

export function getListOptimizationSettings(
  itemCount: number,
  deviceHeight: number
): ListOptimization {
  const itemHeight = 200; // Estimated height per recipe card
  const windowSize = Math.ceil(deviceHeight / itemHeight) * 2;
  
  return {
    itemHeight,
    windowSize: Math.max(windowSize, 5),
    initialNumToRender: Math.min(10, itemCount),
    maxToRenderPerBatch: 5
  };
}