// services/api.ts - API service for PrepSense

import { apiClient, ApiError } from './apiClient';
import { Config } from '../config';

const API_BASE_URL = Config.API_BASE_URL;

export interface PantryItem {
  id: string;
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  addedDate?: string;
  category?: string;
  [key: string]: any; // Allow additional properties from the API
}

export interface ChatMessage {
  message: string;
  user_id: number;
  use_preferences?: boolean;
}

export interface Recipe {
  name: string;
  ingredients: string[];
  instructions?: string[];
  nutrition: {
    calories: number;
    protein: number;
  };
  time: number;
  available_ingredients: string[];
  missing_ingredients: string[];
  missing_count: number;
  available_count: number;
  match_score: number;
  cuisine_type?: string;
  dietary_tags?: string[];
  allergens_present?: string[];
  matched_preferences?: string[];
}

export interface UserPreferences {
  dietary_preference: string[];
  allergens: string[];
  cuisine_preference: string[];
}

export interface ChatResponse {
  response: string;
  recipes: Recipe[];
  pantry_items: PantryItem[];
  user_preferences?: UserPreferences;
  show_preference_choice?: boolean;
}

export interface ImageGenerationResponse {
  image_url: string;
  recipe_name: string;
}

export const savePantryItem = async (userId: number, item: Omit<PantryItem, 'id'> & { id?: string }): Promise<any> => {
  try {
    const endpoint = item.id 
      ? `/pantry/items/${item.id}`
      : `/pantry/user/${userId}/items`;
    
    const requestBody = {
      product_name: item.item_name,
      quantity: item.quantity_amount,
      unit_of_measurement: item.quantity_unit,
      expiration_date: item.expected_expiration ? item.expected_expiration.split('T')[0] : null, // Convert ISO string to date-only format
      category: item.category || 'Uncategorized',
    };
    
    const response = item.id 
      ? await apiClient.put(endpoint, requestBody, 30000) // 30 second timeout for updates
      : await apiClient.post(endpoint, requestBody, 15000); // 15 second timeout for creates
      
    return response.data;
  } catch (error: any) {
    if (error instanceof ApiError && error.isTimeout) {
      throw new Error('Request timed out - server is taking too long to respond');
    }
    console.error('Error saving pantry item:', error);
    throw error;
  }
};

export const updatePantryItem = async (itemId: string, data: any): Promise<any> => {
  try {
    const response = await apiClient.put(`/pantry/items/${itemId}`, data, 30000); // 30 second timeout for database updates
    return response.data;
  } catch (error: any) {
    if (error instanceof ApiError && error.isTimeout) {
      throw new Error('Update timed out - server is taking too long to respond');
    }
    console.error('Error updating pantry item:', error);
    throw error;
  }
};

export const deletePantryItem = async (itemId: string): Promise<void> => {
  try {
    await apiClient.delete(`/pantry/items/${itemId}`, 4000); // 4 second timeout for delete
  } catch (error: any) {
    if (error instanceof ApiError && error.isTimeout) {
      throw new Error('Delete timed out - please try again');
    }
    console.error('Error deleting pantry item:', error);
    throw error;
  }
};

export const fetchPantryItems = async (userId: number): Promise<PantryItem[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/pantry/user/${userId}/items`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error fetching pantry items: ${response.statusText}`);
    }
    
    const rawData = await response.json();
    
    // Transform the API response to match the PantryItem interface
    return rawData.map((item: any) => ({
      id: item.pantry_item_id?.toString() || '',
      item_name: item.product_name || '',
      quantity_amount: item.quantity || 0,
      quantity_unit: item.unit_of_measurement || '',
      expected_expiration: item.expiration_date || '',
      addedDate: item.pantry_item_created_at || '',
      category: item.food_category || 'Uncategorized',
      // Include all original fields for compatibility
      ...item
    }));
  } catch (error) {
    console.error('Error fetching pantry items:', error);
    throw error;
  }
};

export const sendChatMessage = async (message: string, userId: number = 111, usePreferences: boolean = true): Promise<ChatResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: userId,
        use_preferences: usePreferences,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error sending chat message: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
};

export const generateRecipeImage = async (
  recipeName: string, 
  style: string = "professional food photography",
  useGenerated: boolean = false
): Promise<ImageGenerationResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/generate-recipe-image`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        recipe_name: recipeName,
        style: style,
        use_generated: useGenerated
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error generating recipe image: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error generating recipe image:', error);
    throw error;
  }
};

// Spoonacular Recipe APIs
export const searchRecipesByIngredients = async (ingredients: string[]): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/search/by-ingredients`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ingredients,
        number: 20,
        ranking: 1,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error searching recipes: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error searching recipes by ingredients:', error);
    throw error;
  }
};

export const searchRecipesFromPantry = async (
  userId: number = 111,
  maxMissingIngredients: number = 5,
  useExpiringFirst: boolean = true
): Promise<{ recipes: Recipe[] }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/search/from-pantry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        max_missing_ingredients: maxMissingIngredients,
        use_expiring_first: useExpiringFirst
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Transform the response to match the expected Recipe interface
    const recipes: Recipe[] = data.recipes ? data.recipes.map((recipe: any) => ({
      name: recipe.title || recipe.name || 'Unknown Recipe',
      ingredients: recipe.extendedIngredients ? 
        recipe.extendedIngredients.map((ing: any) => ing.original || ing.name) : 
        (recipe.ingredients || []),
      instructions: recipe.analyzedInstructions ? 
        recipe.analyzedInstructions[0]?.steps?.map((step: any) => step.step) : 
        (recipe.instructions || []),
      nutrition: {
        calories: recipe.nutrition?.nutrients?.find((n: any) => n.name === 'Calories')?.amount || 0,
        protein: recipe.nutrition?.nutrients?.find((n: any) => n.name === 'Protein')?.amount || 0,
      },
      time: recipe.readyInMinutes || recipe.time || 30,
      available_ingredients: recipe.available_ingredients || [],
      missing_ingredients: recipe.missing_ingredients || [],
      missing_count: recipe.missing_count || 0,
      available_count: recipe.available_count || 0,
      match_score: recipe.match_score || 0,
      cuisine_type: recipe.cuisines?.[0] || recipe.cuisine_type || 'international',
      dietary_tags: recipe.diets || recipe.dietary_tags || [],
      allergens_present: recipe.allergens_present || [],
      matched_preferences: recipe.matched_preferences || []
    })) : [];

    return { recipes };
  } catch (error) {
    console.error('Error searching recipes from pantry:', error);
    throw error;
  }
};

export const getRecipeDetails = async (recipeId: number): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/recipe/${recipeId}?include_nutrition=true`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error fetching recipe details: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching recipe details:', error);
    throw error;
  }
};

export interface RecipeIngredient {
  ingredient_name: string;
  quantity?: number;
  unit?: string;
}

export interface RecipeCompletionRequest {
  user_id: number;
  recipe_name: string;
  ingredients: RecipeIngredient[];
}

export const completeRecipe = async (request: RecipeCompletionRequest): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/pantry/recipe/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error completing recipe: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error completing recipe:', error);
    throw error;
  }
};

// Shopping List APIs
export interface ShoppingListItem {
  item_name: string;
  quantity?: number;
  unit?: string;
  category?: string;
  recipe_name?: string;
  added_date?: string;
}

export const addToShoppingList = async (userId: number, items: ShoppingListItem[]): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/shopping-list/add-items`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        items: items,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error adding to shopping list: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error adding to shopping list:', error);
    throw error;
  }
};

export const getShoppingList = async (userId: number): Promise<ShoppingListItem[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/shopping-list/user/${userId}/items`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error fetching shopping list: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching shopping list:', error);
    throw error;
  }
};

export interface AIBulkEditRequest {
  item_ids: string[];
  options: {
    correct_units: boolean;
    update_categories: boolean;
    estimate_expirations: boolean;
    enable_recurring: boolean;
    recurring_options?: {
      add_to_shopping_list: boolean;
      days_before_expiry: number;
    };
  };
  user_id: number;
}

export const applyAIBulkCorrections = async (request: AIBulkEditRequest): Promise<any> => {
  try {
    const response = await apiClient.post('/ai/bulk-correct-items', request, 30000); // 30 second timeout
    return response.data;
  } catch (error: any) {
    console.error('Error applying AI bulk corrections:', error);
    throw error;
  }
};

// User Recipe Management APIs
export const deleteRecipe = async (recipeId: number): Promise<void> => {
  try {
    const userId = 111; // Default user ID - should be passed from context in production
    const response = await fetch(`${API_BASE_URL}/user-recipes/${recipeId}?user_id=${userId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error deleting recipe: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Error deleting recipe:', error);
    throw error;
  }
};

export const getUserRecipes = async (userId: number = 111): Promise<any> => {
  try {
    const response = await fetch(`${API_BASE_URL}/user-recipes?user_id=${userId}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error fetching user recipes: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching user recipes:', error);
    throw error;
  }
};