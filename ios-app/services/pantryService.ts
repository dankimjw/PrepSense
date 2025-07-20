// services/pantryService.ts - Pantry management service

import { apiClient } from './apiClient';
import { Config } from '../config';
import { PantryItem } from './api';

export interface PantryItemCreate {
  item_name: string;
  quantity_amount: number;
  quantity_unit: string;
  expected_expiration: string;
  category?: string;
  user_id: number;
}

export interface PantryItemUpdate {
  quantity_amount?: number;
  quantity_unit?: string;
  expected_expiration?: string;
  category?: string;
}

export interface PantryStats {
  total_items: number;
  expiring_soon: number;
  expired: number;
  categories: { [key: string]: number };
}

export interface PantryIngredientMatch {
  pantry_item: PantryItem;
  ingredient_name: string;
  similarity_score: number;
  is_exact_match: boolean;
}

class PantryService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = Config.API_BASE_URL;
  }

  /**
   * Get all pantry items for a user
   */
  async getPantryItems(userId: number): Promise<PantryItem[]> {
    try {
      const response = await apiClient.get(`/pantry/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching pantry items:', error);
      throw error;
    }
  }

  /**
   * Add a new item to the pantry
   */
  async addPantryItem(item: PantryItemCreate): Promise<PantryItem> {
    try {
      const response = await apiClient.post(`/pantry`, item);
      return response.data;
    } catch (error) {
      console.error('Error adding pantry item:', error);
      throw error;
    }
  }

  /**
   * Update an existing pantry item
   */
  async updatePantryItem(itemId: string, updates: PantryItemUpdate): Promise<PantryItem> {
    try {
      const response = await apiClient.put(`/pantry/${itemId}`, updates);
      return response.data;
    } catch (error) {
      console.error('Error updating pantry item:', error);
      throw error;
    }
  }

  /**
   * Delete a pantry item
   */
  async deletePantryItem(itemId: string): Promise<void> {
    try {
      await apiClient.delete(`/pantry/${itemId}`);
    } catch (error) {
      console.error('Error deleting pantry item:', error);
      throw error;
    }
  }

  /**
   * Get pantry statistics
   */
  async getPantryStats(userId: number): Promise<PantryStats> {
    try {
      const response = await apiClient.get(`/pantry/${userId}/stats`);
      return response.data;
    } catch (error) {
      console.error('Error fetching pantry stats:', error);
      throw error;
    }
  }

  /**
   * Check which ingredients from a list are available in the pantry
   */
  async checkIngredientsAvailability(userId: number, ingredients: string[]): Promise<PantryIngredientMatch[]> {
    try {
      const response = await apiClient.post(`/pantry/${userId}/check-ingredients`, {
        ingredients
      });
      return response.data;
    } catch (error) {
      console.error('Error checking ingredients availability:', error);
      throw error;
    }
  }

  /**
   * Use ingredients from pantry (reduce quantities)
   */
  async useIngredients(userId: number, ingredients: { item_id: string; amount: number }[]): Promise<void> {
    try {
      await apiClient.post(`/pantry/${userId}/use-ingredients`, {
        ingredients
      });
    } catch (error) {
      console.error('Error using ingredients:', error);
      throw error;
    }
  }

  /**
   * Get expiring items (within specified days)
   */
  async getExpiringItems(userId: number, daysAhead: number = 7): Promise<PantryItem[]> {
    try {
      const response = await apiClient.get(`/pantry/${userId}/expiring`, {
        params: { days_ahead: daysAhead }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching expiring items:', error);
      throw error;
    }
  }

  /**
   * Get expired items
   */
  async getExpiredItems(userId: number): Promise<PantryItem[]> {
    try {
      const response = await apiClient.get(`/pantry/${userId}/expired`);
      return response.data;
    } catch (error) {
      console.error('Error fetching expired items:', error);
      throw error;
    }
  }

  /**
   * Bulk add items to pantry
   */
  async bulkAddItems(userId: number, items: Omit<PantryItemCreate, 'user_id'>[]): Promise<PantryItem[]> {
    try {
      const itemsWithUserId = items.map(item => ({ ...item, user_id: userId }));
      const response = await apiClient.post(`/pantry/bulk`, {
        items: itemsWithUserId
      });
      return response.data;
    } catch (error) {
      console.error('Error bulk adding items:', error);
      throw error;
    }
  }

  /**
   * Search pantry items
   */
  async searchPantryItems(userId: number, query: string): Promise<PantryItem[]> {
    try {
      const response = await apiClient.get(`/pantry/${userId}/search`, {
        params: { q: query }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching pantry items:', error);
      throw error;
    }
  }

  /**
   * Get pantry items by category
   */
  async getItemsByCategory(userId: number, category: string): Promise<PantryItem[]> {
    try {
      const response = await apiClient.get(`/pantry/${userId}/category/${category}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching items by category:', error);
      throw error;
    }
  }

  /**
   * Get low stock items (based on typical usage patterns)
   */
  async getLowStockItems(userId: number): Promise<PantryItem[]> {
    try {
      const response = await apiClient.get(`/pantry/${userId}/low-stock`);
      return response.data;
    } catch (error) {
      console.error('Error fetching low stock items:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const pantryService = new PantryService();