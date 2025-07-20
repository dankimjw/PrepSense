// services/recipeService.ts - Recipe management service

import { apiClient } from './apiClient';
import { Config } from '../config';

// Extended Recipe interface to match Spoonacular API and component requirements
export interface Recipe {
  id: number;
  title: string;
  image?: string;
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  summary?: string;
  cuisines?: string[];
  dishTypes?: string[];
  diets?: string[];
  occasions?: string[];
  instructions?: string;
  extendedIngredients?: ExtendedIngredient[];
  analyzedInstructions?: AnalyzedInstruction[];
  nutrition?: Nutrition;
  is_favorite?: boolean;
  available_ingredients?: string[];
  missing_ingredients?: string[];
  pantry_item_matches?: { [key: string]: PantryItemMatch[] };
  match_score?: number;
  available_count?: number;
  missing_count?: number;
}

export interface ExtendedIngredient {
  id?: number;
  aisle?: string;
  image?: string;
  consistency?: string;
  name: string;
  nameClean?: string;
  original: string;
  originalString?: string;
  originalName?: string;
  amount?: number;
  unit?: string;
  meta?: string[];
  metaInformation?: string[];
  measures?: {
    us: Measure;
    metric: Measure;
  };
}

export interface Measure {
  amount: number;
  unitShort: string;
  unitLong: string;
}

export interface AnalyzedInstruction {
  name?: string;
  steps: Step[];
}

export interface Step {
  number: number;
  step: string;
  ingredients?: Ingredient[];
  equipment?: Equipment[];
  length?: {
    number: number;
    unit: string;
  };
}

export interface Ingredient {
  id: number;
  name: string;
  localizedName?: string;
  image?: string;
}

export interface Equipment {
  id: number;
  name: string;
  localizedName?: string;
  image?: string;
}

export interface Nutrition {
  nutrients?: Nutrient[];
  properties?: Property[];
  flavonoids?: Flavonoid[];
  ingredients?: IngredientNutrition[];
  caloricBreakdown?: CaloricBreakdown;
  weightPerServing?: WeightPerServing;
  // Convenience properties for common nutrients
  calories?: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  fiber?: number;
  sugar?: number;
}

export interface Nutrient {
  name: string;
  amount: number;
  unit: string;
  percentOfDailyNeeds?: number;
}

export interface Property {
  name: string;
  amount: number;
  unit: string;
}

export interface Flavonoid {
  name: string;
  amount: number;
  unit: string;
}

export interface IngredientNutrition {
  id: number;
  name: string;
  amount: number;
  unit: string;
  nutrients: Nutrient[];
}

export interface CaloricBreakdown {
  percentProtein: number;
  percentFat: number;
  percentCarbs: number;
}

export interface WeightPerServing {
  amount: number;
  unit: string;
}

export interface PantryItemMatch {
  pantry_item_id: number;
  item_name: string;
  similarity_score: number;
}

export interface SavedRecipe {
  id: number;
  user_id: number;
  recipe_id: number;
  recipe_data: Recipe;
  saved_at: string;
  is_favorite: boolean;
  tags?: string[];
  notes?: string;
}

export interface RecipeRating {
  recipe_id: number;
  user_id: number;
  rating: 'thumbs_up' | 'thumbs_down';
  created_at: string;
}

class RecipeService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = Config.API_BASE_URL;
  }

  /**
   * Save a recipe to user's collection
   */
  async saveRecipe(recipe: Recipe, userId: number): Promise<SavedRecipe> {
    try {
      const response = await apiClient.post(`/recipes/save`, {
        user_id: userId,
        recipe_id: recipe.id,
        recipe_data: recipe
      });
      return response.data;
    } catch (error) {
      console.error('Error saving recipe:', error);
      throw error;
    }
  }

  /**
   * Remove a recipe from user's saved collection
   */
  async removeRecipe(recipeId: number, userId: number): Promise<void> {
    try {
      await apiClient.delete(`/recipes/saved/${recipeId}`, {
        params: { user_id: userId }
      });
    } catch (error) {
      console.error('Error removing recipe:', error);
      throw error;
    }
  }

  /**
   * Get all saved recipes for a user
   */
  async getSavedRecipes(userId: number): Promise<SavedRecipe[]> {
    try {
      const response = await apiClient.get(`/recipes/saved`, {
        params: { user_id: userId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching saved recipes:', error);
      throw error;
    }
  }

  /**
   * Rate a recipe
   */
  async rateRecipe(recipeId: number, userId: number, rating: 'thumbs_up' | 'thumbs_down'): Promise<RecipeRating> {
    try {
      const response = await apiClient.post(`/recipes/${recipeId}/rate`, {
        user_id: userId,
        rating
      });
      return response.data;
    } catch (error) {
      console.error('Error rating recipe:', error);
      throw error;
    }
  }

  /**
   * Get recipe details by ID
   */
  async getRecipeDetails(recipeId: number): Promise<Recipe> {
    try {
      const response = await apiClient.get(`/recipes/${recipeId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching recipe details:', error);
      throw error;
    }
  }

  /**
   * Search recipes by ingredients
   */
  async searchByIngredients(ingredients: string[], userId?: number): Promise<Recipe[]> {
    try {
      const response = await apiClient.post(`/recipes/search/ingredients`, {
        ingredients,
        user_id: userId
      });
      return response.data;
    } catch (error) {
      console.error('Error searching recipes:', error);
      throw error;
    }
  }

  /**
   * Search recipes from user's pantry
   */
  async searchFromPantry(userId: number): Promise<Recipe[]> {
    try {
      const response = await apiClient.get(`/recipes/search/pantry`, {
        params: { user_id: userId }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching from pantry:', error);
      throw error;
    }
  }

  /**
   * Toggle favorite status for a recipe
   */
  async toggleFavorite(recipeId: number, userId: number): Promise<boolean> {
    try {
      const response = await apiClient.post(`/recipes/${recipeId}/favorite`, {
        user_id: userId
      });
      return response.data.is_favorite;
    } catch (error) {
      console.error('Error toggling favorite:', error);
      throw error;
    }
  }

  /**
   * Get personalized recipe recommendations
   */
  async getRecommendations(userId: number, limit: number = 10): Promise<Recipe[]> {
    try {
      const response = await apiClient.get(`/recipes/recommendations`, {
        params: { user_id: userId, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      throw error;
    }
  }

  /**
   * Complete a recipe (mark as cooked)
   */
  async completeRecipe(recipeId: number, userId: number, ingredientsUsed: string[]): Promise<void> {
    try {
      await apiClient.post(`/recipes/${recipeId}/complete`, {
        user_id: userId,
        ingredients_used: ingredientsUsed
      });
    } catch (error) {
      console.error('Error completing recipe:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const recipeService = new RecipeService();