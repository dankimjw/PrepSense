/**
 * Recipe Data Service
 * Handles background preloading, caching, and data management for all recipe tabs
 */

import { Config } from '../config';

export interface Recipe {
  id: number;
  title: string;
  image: string;
  imageType: string;
  usedIngredientCount: number;
  missedIngredientCount: number;
  available_count?: number;
  missing_count?: number;
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

export interface UserPreferences {
  dietary_preference: string[];
  allergens: string[];
  cuisine_preference: string[];
  household_size: number;
}

export interface RecipeDataCache {
  pantry: Recipe[];
  discover: Recipe[];
  myRecipes: SavedRecipe[];
  userPreferences: UserPreferences | null;
  lastUpdated: number;
  ttl: number; // Time to live in milliseconds
}

export class RecipeDataService {
  private cache: RecipeDataCache = {
    pantry: [],
    discover: [],
    myRecipes: [],
    userPreferences: null,
    lastUpdated: 0,
    ttl: 5 * 60 * 1000, // 5 minutes
  };

  private readonly DEFAULT_USER_ID = 111; // Demo user ID

  /**
   * Check if cached data is still valid
   */
  private isCacheValid(): boolean {
    const now = Date.now();
    return (now - this.cache.lastUpdated) < this.cache.ttl;
  }

  /**
   * Map frontend filter IDs to backend parameters
   */
  private mapFiltersToBackendParams(filters: string[]): Record<string, string> {
    const params: Record<string, string> = {};
    
    // Meal type filters
    const mealTypeMap: Record<string, string> = {
      'breakfast': 'breakfast',
      'lunch': 'lunch', 
      'dinner': 'main course',
      'snack': 'snack',
      'dessert': 'dessert',
      'appetizer': 'appetizer',
      'soup': 'soup',
      'salad': 'salad'
    };

    // Dietary filters
    const dietaryMap: Record<string, string> = {
      'vegetarian': 'vegetarian',
      'vegan': 'vegan',
      'gluten-free': 'gluten free',
      'dairy-free': 'dairy free',
      'low-carb': 'low carb',
      'keto': 'ketogenic',
      'paleo': 'paleo',
      'mediterranean': 'mediterranean'
    };

    // Cuisine filters
    const cuisineMap: Record<string, string> = {
      'italian': 'italian',
      'mexican': 'mexican',
      'asian': 'asian',
      'american': 'american',
      'indian': 'indian',
      'french': 'french',
      'japanese': 'japanese',
      'thai': 'thai'
    };

    // Apply meal type filters
    const mealTypes = filters.filter(f => mealTypeMap[f]).map(f => mealTypeMap[f]);
    if (mealTypes.length > 0) {
      params.type = mealTypes.join(',');
    }

    // Apply dietary filters
    const dietaryFilters = filters.filter(f => dietaryMap[f]).map(f => dietaryMap[f]);
    if (dietaryFilters.length > 0) {
      params.diet = dietaryFilters.join(',');
    }

    // Apply cuisine filters
    const cuisineFilters = filters.filter(f => cuisineMap[f]).map(f => cuisineMap[f]);
    if (cuisineFilters.length > 0) {
      params.cuisine = cuisineFilters.join(',');
    }

    return params;
  }

  /**
   * Fetch user preferences from backend
   */
  async fetchUserPreferences(userId: number = this.DEFAULT_USER_ID): Promise<UserPreferences> {
    try {
      const response = await fetch(`${Config.API_BASE_URL}/user-preferences/${userId}`);
      
      if (!response.ok) {
        console.warn('Failed to fetch user preferences, using defaults');
        return {
          dietary_preference: [],
          allergens: [],
          cuisine_preference: [],
          household_size: 2
        };
      }

      const data = await response.json();
      return {
        dietary_preference: data.dietary_preference || [],
        allergens: data.allergens || [],
        cuisine_preference: data.cuisine_preference || [],
        household_size: data.household_size || 2
      };
    } catch (error) {
      console.error('Error fetching user preferences:', error);
      return {
        dietary_preference: [],
        allergens: [],
        cuisine_preference: [],
        household_size: 2
      };
    }
  }

  /**
   * Fetch recipes from pantry with user preferences and filters
   */
  async fetchPantryRecipes(
    userId: number = this.DEFAULT_USER_ID,
    filters: string[] = [],
    userPreferences?: UserPreferences
  ): Promise<Recipe[]> {
    try {
      // Get user preferences if not provided
      const preferences = userPreferences || await this.fetchUserPreferences(userId);
      
      // Map filters to backend parameters
      const filterParams = this.mapFiltersToBackendParams(filters);

      const requestBody = {
        user_id: userId,
        max_missing_ingredients: 10,
        use_expiring_first: true,
        user_preferences: preferences,
        ...filterParams
      };

      const response = await fetch(`${Config.API_BASE_URL}/recipes/search/from-pantry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch pantry recipes: ${response.status}`);
      }

      const data = await response.json();
      
      // Filter and validate recipes
      const recipes = (data.recipes || []).filter((recipe: Recipe) => {
        return recipe.id && typeof recipe.id === 'number' && recipe.id > 0 && 
               recipe.title && recipe.title.trim().length > 0;
      });

      return recipes;
    } catch (error) {
      console.error('Error fetching pantry recipes:', error);
      return [];
    }
  }

  /**
   * Fetch discover/random recipes with filters
   */
  async fetchDiscoverRecipes(
    filters: string[] = [],
    searchQuery?: string
  ): Promise<Recipe[]> {
    try {
      if (searchQuery && searchQuery.trim()) {
        // Search for specific recipes
        const filterParams = this.mapFiltersToBackendParams(filters);
        
        const response = await fetch(`${Config.API_BASE_URL}/recipes/search/complex`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: searchQuery,
            number: 20,
            ...filterParams
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to search recipes: ${response.status}`);
        }

        const data = await response.json();
        return (data.results || []).filter((recipe: Recipe) => {
          return recipe.id && typeof recipe.id === 'number' && recipe.id > 0;
        });
      } else {
        // Get random recipes
        const filterParams = this.mapFiltersToBackendParams(filters);
        const url = new URL(`${Config.API_BASE_URL}/recipes/random`);
        url.searchParams.append('number', '20');
        url.searchParams.append('user_id', this.DEFAULT_USER_ID.toString());
        
        // Add filter parameters to URL
        Object.entries(filterParams).forEach(([key, value]) => {
          url.searchParams.append(key, value);
        });

        const response = await fetch(url.toString());

        if (!response.ok) {
          throw new Error(`Failed to fetch random recipes: ${response.status}`);
        }

        const data = await response.json();
        return (data.recipes || []).filter((recipe: Recipe) => {
          return recipe.id && typeof recipe.id === 'number' && recipe.id > 0;
        });
      }
    } catch (error) {
      console.error('Error fetching discover recipes:', error);
      return [];
    }
  }

  /**
   * Fetch user's saved recipes
   */
  async fetchMyRecipes(
    userId: number = this.DEFAULT_USER_ID,
    status?: 'saved' | 'cooked',
    rating?: 'all' | 'thumbs_up' | 'thumbs_down' | 'favorites'
  ): Promise<SavedRecipe[]> {
    try {
      let filterParam = '';
      
      // Add status filter
      if (status) {
        filterParam = `?status=${status}`;
      }

      // Add rating filters
      if (rating === 'favorites') {
        filterParam += filterParam ? '&is_favorite=true' : '?is_favorite=true';
      } else if (rating && rating !== 'all') {
        filterParam += filterParam ? `&rating=${rating}` : `?rating=${rating}`;
      }

      // Always include external recipes to show saved Spoonacular recipes
      const includeExternalParam = filterParam ? '&include_external=true' : '?include_external=true';
      const response = await fetch(`${Config.API_BASE_URL}/user-recipes${filterParam}${includeExternalParam}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch saved recipes: ${response.status}`);
      }

      const data = await response.json();
      return data || [];
    } catch (error) {
      console.error('Error fetching saved recipes:', error);
      return [];
    }
  }

  /**
   * Preload all recipe data in parallel
   */
  async preloadAllRecipeData(
    userId: number = this.DEFAULT_USER_ID,
    filters: string[] = []
  ): Promise<void> {
    try {
      console.log('🔄 Starting background recipe data preload...');
      
      // Fetch user preferences first
      const userPreferences = await this.fetchUserPreferences(userId);
      
      // Fetch all recipe data in parallel
      const [pantryRecipes, discoverRecipes, myRecipes] = await Promise.all([
        this.fetchPantryRecipes(userId, filters, userPreferences),
        this.fetchDiscoverRecipes(filters),
        this.fetchMyRecipes(userId, 'saved', 'all')
      ]);

      // Update cache
      this.cache = {
        pantry: pantryRecipes,
        discover: discoverRecipes,
        myRecipes: myRecipes,
        userPreferences: userPreferences,
        lastUpdated: Date.now(),
        ttl: this.cache.ttl
      };

      console.log(`✅ Recipe data preloaded: ${pantryRecipes.length} pantry, ${discoverRecipes.length} discover, ${myRecipes.length} saved`);
    } catch (error) {
      console.error('Error preloading recipe data:', error);
    }
  }

  /**
   * Get cached data for a specific tab
   */
  getCachedData(tab: 'pantry' | 'discover' | 'my-recipes'): Recipe[] | SavedRecipe[] {
    if (!this.isCacheValid()) {
      return [];
    }

    switch (tab) {
      case 'pantry':
        return this.cache.pantry;
      case 'discover':
        return this.cache.discover;
      case 'my-recipes':
        return this.cache.myRecipes;
      default:
        return [];
    }
  }

  /**
   * Get cached user preferences
   */
  getCachedUserPreferences(): UserPreferences | null {
    if (!this.isCacheValid()) {
      return null;
    }
    return this.cache.userPreferences;
  }

  /**
   * Check if data is currently cached and valid
   */
  hasCachedData(tab: 'pantry' | 'discover' | 'my-recipes'): boolean {
    return this.isCacheValid() && this.getCachedData(tab).length > 0;
  }

  /**
   * Clear cache (useful when user preferences change)
   */
  clearCache(): void {
    this.cache = {
      pantry: [],
      discover: [],
      myRecipes: [],
      userPreferences: null,
      lastUpdated: 0,
      ttl: this.cache.ttl
    };
  }

  /**
   * Update cache for specific tab
   */
  updateCacheForTab(tab: 'pantry' | 'discover' | 'my-recipes', data: Recipe[] | SavedRecipe[]): void {
    if (tab === 'pantry') {
      this.cache.pantry = data as Recipe[];
    } else if (tab === 'discover') {
      this.cache.discover = data as Recipe[];
    } else if (tab === 'my-recipes') {
      this.cache.myRecipes = data as SavedRecipe[];
    }
    this.cache.lastUpdated = Date.now();
  }
}

// Export singleton instance
export const recipeDataService = new RecipeDataService();
