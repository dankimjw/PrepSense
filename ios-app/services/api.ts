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
  id?: number; // Added required ID field for recipe navigation and images
  name: string;
  title?: string; // Support both name and title fields for compatibility
  image?: string; // Added image field for recipe images
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
  // Spoonacular compatibility fields
  usedIngredientCount?: number;
  missedIngredientCount?: number;
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  spoonacularSourceUrl?: string;
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

/**
 * Enhanced recipe ID extraction with comprehensive fallback strategies
 */
function extractRecipeId(recipe: any): number | null {
  // Priority order for ID extraction
  const idFields = ['id', 'recipe_id', 'spoonacularId', 'external_id', 'recipeId'];
  
  for (const field of idFields) {
    const value = recipe[field];
    if (value !== null && value !== undefined && value !== '') {
      // Handle numeric values
      if (typeof value === 'number') {
        if (value > 0 && Number.isInteger(value)) {
          return value;
        }
      }
      // Handle string values
      else if (typeof value === 'string') {
        const numericValue = parseInt(value, 10);
        if (!isNaN(numericValue) && numericValue > 0) {
          return numericValue;
        }
      }
    }
  }
  
  // Fallback: Generate ID from title hash if available
  if (recipe.title || recipe.name) {
    const title = recipe.title || recipe.name;
    let hash = 0;
    for (let i = 0; i < title.length; i++) {
      const char = title.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    const fallbackId = Math.abs(hash);
    console.log(`🔄 Generated fallback ID ${fallbackId} for recipe: ${title}`);
    return fallbackId;
  }
  
  return null;
}

/**
 * Enhanced image URL generation for Spoonacular recipes
 */
function enhanceRecipeImage(recipe: any): string {
  const recipeId = recipe.id;
  let imageUrl = recipe.image || '';
  
  // If we have a valid recipe ID, ensure proper Spoonacular image URL
  if (recipeId && typeof recipeId === 'number' && recipeId > 0) {
    // Generate proper Spoonacular image URL if missing or invalid
    if (!imageUrl || !imageUrl.startsWith('http')) {
      imageUrl = `https://img.spoonacular.com/recipes/${recipeId}-312x231.jpg`;
      console.log(`🖼️ Generated Spoonacular image URL: ${imageUrl}`);
    }
    // Fix malformed Spoonacular URLs
    else if (imageUrl.includes('spoonacular.com') && !imageUrl.includes(`${recipeId}-`)) {
      imageUrl = `https://img.spoonacular.com/recipes/${recipeId}-312x231.jpg`;
      console.log(`🔧 Fixed Spoonacular image URL: ${imageUrl}`);
    }
  }
  // Use working placeholder for recipes without valid IDs
  else if (!imageUrl || imageUrl === 'https://img.spoonacular.com/recipes/default-312x231.jpg') {
    imageUrl = 'https://via.placeholder.com/312x231/E5E5E5/666666?text=Recipe+Image';
    console.log('🖼️ Using placeholder image for recipe without valid ID');
  }
  
  return imageUrl;
}

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
    
    // Enhanced transformation that ensures proper recipe IDs and images
    const recipes: Recipe[] = data.recipes ? data.recipes.map((recipe: any) => {
      // Extract and validate recipe ID using enhanced extraction
      const recipeId = extractRecipeId(recipe);
      
      // Log ID extraction results
      if (recipeId) {
        console.log('✅ Recipe ID extracted successfully:', {
          recipe_id: recipeId,
          title: recipe.title || recipe.name,
          original_id_field: recipe.id,
          original_type: typeof recipe.id
        });
      } else {
        console.warn('⚠️ Recipe ID extraction failed:', {
          title: recipe.title || recipe.name,
          available_fields: Object.keys(recipe).filter(key => 
            key.toLowerCase().includes('id')),
          recipe_data_sample: JSON.stringify(recipe, null, 2).slice(0, 200) + '...'
        });
      }

      // Enhance image URL based on extracted ID
      recipe.id = recipeId; // Ensure the ID is set for image enhancement
      const enhancedImageUrl = enhanceRecipeImage(recipe);

      return {
        // Essential identification fields
        id: recipeId,
        name: recipe.title || recipe.name || 'Unknown Recipe',
        title: recipe.title, // Keep original title for compatibility
        image: enhancedImageUrl, // Use enhanced image URL
        
        // Recipe content
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
        
        // Timing and serving info
        time: recipe.readyInMinutes || recipe.time || 30,
        readyInMinutes: recipe.readyInMinutes, // Keep original for Spoonacular compatibility
        servings: recipe.servings,
        
        // Pantry matching information
        available_ingredients: recipe.available_ingredients || [],
        missing_ingredients: recipe.missing_ingredients || [],
        missing_count: recipe.missing_count || recipe.missedIngredientCount || 0,
        available_count: recipe.available_count || recipe.usedIngredientCount || 0,
        match_score: recipe.match_score || 0,
        
        // Spoonacular compatibility fields
        usedIngredientCount: recipe.usedIngredientCount,
        missedIngredientCount: recipe.missedIngredientCount,
        sourceUrl: recipe.sourceUrl,
        spoonacularSourceUrl: recipe.spoonacularSourceUrl,
        
        // Classification and preferences
        cuisine_type: recipe.cuisines?.[0] || recipe.cuisine_type || 'international',
        dietary_tags: recipe.diets || recipe.dietary_tags || [],
        allergens_present: recipe.allergens_present || [],
        matched_preferences: recipe.matched_preferences || []
      };
    }) : [];

    // Log transformation results with detailed ID analysis
    const recipesWithIds = recipes.filter(r => r.id);
    const recipesMissingIds = recipes.filter(r => !r.id);
    
    console.log(`✅ Recipe transformation completed:`, {
      total_recipes: recipes.length,
      recipes_with_valid_ids: recipesWithIds.length,
      recipes_missing_ids: recipesMissingIds.length,
      success_rate: `${((recipesWithIds.length / recipes.length) * 100).toFixed(1)}%`
    });

    if (recipesMissingIds.length > 0) {
      console.warn('⚠️ Recipes without valid IDs:', recipesMissingIds.map(r => ({
        title: r.name || r.title,
        id_value: r.id
      })));
    }

    // Sample recipe for verification
    if (recipes.length > 0) {
      console.log(`🔍 Sample processed recipe:`, {
        id: recipes[0].id,
        id_type: typeof recipes[0].id,
        name: recipes[0].name,
        image: recipes[0].image,
        has_valid_id: recipes[0].id !== null && recipes[0].id !== undefined && recipes[0].id > 0
      });
    }

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
    
    const recipe = await response.json();
    
    // Ensure the recipe has proper ID and image
    if (recipe) {
      const extractedId = extractRecipeId(recipe);
      recipe.id = extractedId || recipeId; // Use provided ID as fallback
      recipe.image = enhanceRecipeImage(recipe);
      
      console.log(`📋 Recipe details enhanced:`, {
        recipe_id: recipe.id,
        title: recipe.title,
        image: recipe.image,
        has_valid_id: recipe.id !== null && recipe.id > 0
      });
    }
    
    return recipe;
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