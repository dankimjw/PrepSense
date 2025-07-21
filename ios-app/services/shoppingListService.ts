// services/shoppingListService.ts - Shopping list management service

import { apiClient } from './apiClient';
import { Config } from '../config';

export interface ShoppingListItem {
  id: string;
  name: string;
  quantity?: number;
  unit?: string;
  category?: string;
  checked: boolean;
  user_id: number;
  created_at: string;
  updated_at: string;
  recipe_id?: number;
  recipe_name?: string;
}

export interface ShoppingListItemCreate {
  name: string;
  quantity?: number;
  unit?: string;
  category?: string;
  user_id: number;
  recipe_id?: number;
  recipe_name?: string;
}

export interface ShoppingListStats {
  total_items: number;
  checked_items: number;
  unchecked_items: number;
  categories: { [key: string]: number };
}

class ShoppingListService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = Config.API_BASE_URL;
  }

  /**
   * Get all shopping list items for a user
   */
  async getShoppingList(userId: number): Promise<ShoppingListItem[]> {
    try {
      const response = await apiClient.get(`/shopping-list/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching shopping list:', error);
      throw error;
    }
  }

  /**
   * Add an item to the shopping list
   */
  async addItem(item: ShoppingListItemCreate): Promise<ShoppingListItem> {
    try {
      const response = await apiClient.post(`/shopping-list`, item);
      return response.data;
    } catch (error) {
      console.error('Error adding shopping list item:', error);
      throw error;
    }
  }

  /**
   * Add multiple items to the shopping list
   */
  async addMultipleItems(items: ShoppingListItemCreate[]): Promise<ShoppingListItem[]> {
    try {
      const response = await apiClient.post(`/shopping-list/bulk`, { items });
      return response.data;
    } catch (error) {
      console.error('Error adding multiple shopping list items:', error);
      throw error;
    }
  }

  /**
   * Update a shopping list item
   */
  async updateItem(itemId: string, updates: Partial<ShoppingListItem>): Promise<ShoppingListItem> {
    try {
      const response = await apiClient.put(`/shopping-list/${itemId}`, updates);
      return response.data;
    } catch (error) {
      console.error('Error updating shopping list item:', error);
      throw error;
    }
  }

  /**
   * Delete a shopping list item
   */
  async deleteItem(itemId: string): Promise<void> {
    try {
      await apiClient.delete(`/shopping-list/${itemId}`);
    } catch (error) {
      console.error('Error deleting shopping list item:', error);
      throw error;
    }
  }

  /**
   * Toggle the checked status of an item
   */
  async toggleItemChecked(itemId: string): Promise<ShoppingListItem> {
    try {
      const response = await apiClient.post(`/shopping-list/${itemId}/toggle`);
      return response.data;
    } catch (error) {
      console.error('Error toggling shopping list item:', error);
      throw error;
    }
  }

  /**
   * Clear all checked items from the list
   */
  async clearCheckedItems(userId: number): Promise<void> {
    try {
      await apiClient.delete(`/shopping-list/${userId}/checked`);
    } catch (error) {
      console.error('Error clearing checked items:', error);
      throw error;
    }
  }

  /**
   * Clear all items from the list
   */
  async clearAllItems(userId: number): Promise<void> {
    try {
      await apiClient.delete(`/shopping-list/${userId}/all`);
    } catch (error) {
      console.error('Error clearing all items:', error);
      throw error;
    }
  }

  /**
   * Get shopping list statistics
   */
  async getStats(userId: number): Promise<ShoppingListStats> {
    try {
      const response = await apiClient.get(`/shopping-list/${userId}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error fetching shopping list stats:', error);
      throw error;
    }
  }

  /**
   * Add missing ingredients from a recipe to the shopping list
   */
  async addMissingIngredients(userId: number, recipeId: number, ingredients: string[]): Promise<ShoppingListItem[]> {
    try {
      const response = await apiClient.post(`/shopping-list/${userId}/recipe-ingredients`, {
        recipe_id: recipeId,
        ingredients
      });
      return response.data;
    } catch (error) {
      console.error('Error adding recipe ingredients to shopping list:', error);
      throw error;
    }
  }

  /**
   * Move checked items to pantry
   */
  async moveCheckedToPantry(userId: number): Promise<{ moved_count: number }> {
    try {
      const response = await apiClient.post(`/shopping-list/${userId}/move-to-pantry`);
      return response.data;
    } catch (error) {
      console.error('Error moving items to pantry:', error);
      throw error;
    }
  }

  /**
   * Get items by category
   */
  async getItemsByCategory(userId: number, category: string): Promise<ShoppingListItem[]> {
    try {
      const response = await apiClient.get(`/shopping-list/${userId}/category/${category}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching items by category:', error);
      throw error;
    }
  }

  /**
   * Search shopping list items
   */
  async searchItems(userId: number, query: string): Promise<ShoppingListItem[]> {
    try {
      const response = await apiClient.get(`/shopping-list/${userId}/search`, {
        params: { q: query }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching shopping list:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const shoppingListService = new ShoppingListService();